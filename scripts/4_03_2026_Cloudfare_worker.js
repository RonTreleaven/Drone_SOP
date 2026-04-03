/**
 * Added a Cloudfare CORS proxy for NOTAM retrieval
 * and updates to allow additional Hosts.  March 26, 2026 NavCan worker. 
 * April 3, 2026 -ggcode and partial completions looksup
 * - Run "npm run dev" in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run "npm run deploy" to publish your worker
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */



const ALLOWED_HOSTS = new Set([
  "plan.navcanada.ca",
  "aviationweather.gov",
  "tgftp.nws.noaa.gov"
]);

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "86400"
  };
}

function withCors(upstreamHeaders) {
  const headers = new Headers(upstreamHeaders);
  const cors = corsHeaders();
  for (const [key, value] of Object.entries(cors)) {
    headers.set(key, value);
  }
  return headers;
}

export default {
  async fetch(request, env, ctx) {
    const reqUrl = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders()
      });
    }

    if (request.method !== "GET") {
      return new Response("Method not allowed", {
        status: 405,
        headers: corsHeaders()
      });
    }

    if (reqUrl.pathname === "/geocode") {
      const address = (reqUrl.searchParams.get("address") || "").trim();
      const components = (reqUrl.searchParams.get("components") || "").trim();

      if (!address) {
        return new Response(JSON.stringify({ status: "INVALID_REQUEST", error_message: "Missing address" }), {
          status: 400,
          headers: {
            ...corsHeaders(),
            "Content-Type": "application/json"
          }
        });
      }

      if (!env.GOOGLE_GEOCODING_API_KEY) {
        return new Response(JSON.stringify({ status: "ERROR", error_message: "Worker secret GOOGLE_GEOCODING_API_KEY is not configured" }), {
          status: 500,
          headers: {
            ...corsHeaders(),
            "Content-Type": "application/json"
          }
        });
      }

      const googleUrl = new URL("https://maps.googleapis.com/maps/api/geocode/json");
      googleUrl.searchParams.set("address", address);
      if (components) {
        googleUrl.searchParams.set("components", components);
      }
      googleUrl.searchParams.set("key", env.GOOGLE_GEOCODING_API_KEY);

      try {
        const upstream = await fetch(googleUrl.toString(), {
          method: "GET",
          redirect: "follow",
          headers: {
            "Accept": "application/json",
            "User-Agent": "Drone-SOP-Geocode-Worker"
          }
        });

        return new Response(upstream.body, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers: withCors(upstream.headers)
        });
      } catch (err) {
        return new Response(
          JSON.stringify({ status: "ERROR", error_message: `Geocode upstream fetch failed: ${err?.message || "unknown error"}` }),
          {
            status: 502,
            headers: {
              ...corsHeaders(),
              "Content-Type": "application/json"
            }
          }
        );
      }
    }

    if (reqUrl.pathname === "/places-autocomplete") {
      const input = (reqUrl.searchParams.get("input") || "").trim();
      const components = (reqUrl.searchParams.get("components") || "").trim();
      const requestedTypes = (reqUrl.searchParams.get("types") || "").trim();
      const requestedLanguage = (reqUrl.searchParams.get("language") || "").trim();

      if (!input) {
        return new Response(JSON.stringify({ status: "INVALID_REQUEST", error_message: "Missing input" }), {
          status: 400,
          headers: {
            ...corsHeaders(),
            "Content-Type": "application/json"
          }
        });
      }

      if (!env.GOOGLE_GEOCODING_API_KEY) {
        return new Response(JSON.stringify({ status: "ERROR", error_message: "Worker secret GOOGLE_GEOCODING_API_KEY is not configured" }), {
          status: 500,
          headers: {
            ...corsHeaders(),
            "Content-Type": "application/json"
          }
        });
      }

      const safeTypes = /^[a-z_]+$/i.test(requestedTypes) ? requestedTypes : "";
      const safeLanguage = /^[a-z-]+$/i.test(requestedLanguage) ? requestedLanguage : "";

      const googleUrl = new URL("https://maps.googleapis.com/maps/api/place/autocomplete/json");
      googleUrl.searchParams.set("input", input);
      if (components) {
        googleUrl.searchParams.set("components", components);
      }
      if (safeTypes) {
        googleUrl.searchParams.set("types", safeTypes);
      }
      if (safeLanguage) {
        googleUrl.searchParams.set("language", safeLanguage);
      }
      googleUrl.searchParams.set("key", env.GOOGLE_GEOCODING_API_KEY);

      try {
        const upstream = await fetch(googleUrl.toString(), {
          method: "GET",
          redirect: "follow",
          headers: {
            "Accept": "application/json",
            "User-Agent": "Drone-SOP-PlacesAutocomplete-Worker"
          }
        });

        return new Response(upstream.body, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers: withCors(upstream.headers)
        });
      } catch (err) {
        return new Response(
          JSON.stringify({ status: "ERROR", error_message: `Places autocomplete upstream fetch failed: ${err?.message || "unknown error"}` }),
          {
            status: 502,
            headers: {
              ...corsHeaders(),
              "Content-Type": "application/json"
            }
          }
        );
      }
    }

    if (reqUrl.pathname === "/maps-bootstrap") {
      const mapsApiKey = env.GOOGLE_GEOCODING_API_KEY;
      if (!mapsApiKey) {
        return new Response(JSON.stringify({ error: "Worker secret GOOGLE_GEOCODING_API_KEY is not configured" }), {
          status: 500,
          headers: {
            ...corsHeaders(),
            "Content-Type": "application/json"
          }
        });
      }

      const requestedLibraries = (reqUrl.searchParams.get("libraries") || "drawing,geometry").trim();
      const safeLibraries = /^[a-z,]+$/i.test(requestedLibraries) ? requestedLibraries : "drawing,geometry";

      const mapsUrl = new URL("https://maps.googleapis.com/maps/api/js");
      mapsUrl.searchParams.set("key", mapsApiKey);
      mapsUrl.searchParams.set("libraries", safeLibraries);

      return new Response(JSON.stringify({ scriptUrl: mapsUrl.toString() }), {
        status: 200,
        headers: {
          ...corsHeaders(),
          "Content-Type": "application/json",
          "Cache-Control": "no-store"
        }
      });
    }

    const target = reqUrl.searchParams.get("url");
    if (!target) {
      return new Response("Missing url= parameter", {
        status: 400,
        headers: corsHeaders()
      });
    }

    let targetUrl;
    try {
      targetUrl = new URL(target);
    } catch {
      return new Response("Invalid target URL", {
        status: 400,
        headers: corsHeaders()
      });
    }

    if (targetUrl.protocol !== "https:") {
      return new Response("Only https targets are allowed", {
        status: 400,
        headers: corsHeaders()
      });
    }

    if (!ALLOWED_HOSTS.has(targetUrl.hostname)) {
      return new Response("Host not allowed", {
        status: 403,
        headers: corsHeaders()
      });
    }

    try {
      const upstream = await fetch(targetUrl.toString(), {
        method: "GET",
        redirect: "follow",
        headers: {
          "Accept": "*/*",
          "User-Agent": "FetchNotams-Proxy"
        }
      });

      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: withCors(upstream.headers)
      });
    } catch (err) {
      return new Response(
        `Upstream fetch failed: ${err?.message || "unknown error"}`,
        {
          status: 502,
          headers: corsHeaders()
        }
      );
    }
  }
};
