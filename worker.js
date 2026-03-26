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

    const reqUrl = new URL(request.url);
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
