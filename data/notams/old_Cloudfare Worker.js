/**
 * Added a Cloudfare CORS proxy for NOTAM retrieval
 *
 * - Run "npm run dev" in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run "npm run deploy" to publish your worker
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const target = url.searchParams.get("url");
    if (!target) {
      return new Response("Missing url= parameter", { status: 400 });
    }

    // Only allow NAV CANADA endpoint (lock it down)
    const allowedHost = "plan.navcanada.ca";
    const targetUrl = new URL(target);
    if (targetUrl.hostname !== allowedHost) {
      return new Response("Host not allowed", { status: 403 });
    }

    const resp = await fetch(targetUrl.toString(), {
      method: "GET",
      headers: {
        "User-Agent": "FetchNotams-Proxy"
      }
    });

    // Pass-through with CORS headers
    const headers = new Headers(resp.headers);
    headers.set("Access-Control-Allow-Origin", "*");
    headers.set("Access-Control-Allow-Methods", "GET, OPTIONS");
    headers.set("Access-Control-Allow-Headers", "*");

    return new Response(resp.body, { status: resp.status, headers });
  }
};