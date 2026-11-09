import { heights, validPoint } from "./mission";

export async function fetchModelForecast(params: URLSearchParams) {
  const lat = Number(params.get("lat")), lon = Number(params.get("lon"));
  const altitude = Number(params.get("alt"));
  const time = params.get("time") ?? "";
  const millis = Date.parse(time), now = Date.now();
  if (!params.get("lat") || !params.get("lon") || !validPoint({ lat, lon }) || !Number.isFinite(altitude) || altitude < 10 || altitude > 180)
    throw new Error("Forecast requires valid coordinates and a height from 10 to 180 m AGL.");
  if (!Number.isFinite(millis) || millis < now - 3600000 || millis > now + 14 * 86400000)
    throw new Error("Select a UTC time from the current hour through the next 14 days.");
  const hour = new Date(Math.round(millis / 3600000) * 3600000).toISOString().slice(0, 13) + ":00";
  const day = hour.slice(0, 10);
  const lower = [...heights].reverse().find(h => h <= altitude)!;
  const upper = heights.find(h => h >= altitude)!;
  const layers = [...new Set([lower, upper])];
  const variables = [...layers.flatMap(h => [`wind_speed_${h}m`, `wind_direction_${h}m`]), "wind_gusts_10m", "visibility", "temperature_2m", "precipitation"];
  const url = new URL("https://api.open-meteo.com/v1/forecast");
  url.search = new URLSearchParams({ latitude: String(lat), longitude: String(lon), hourly: variables.join(","),
    wind_speed_unit: "kn", timezone: "GMT", start_date: day, end_date: day }).toString();
  try {
    const upstream = await fetch(url, { signal: AbortSignal.timeout(12000) });
    if (!upstream.ok) throw new Error("Upstream response error");
    const payload = await upstream.json() as { hourly?: Record<string, unknown[]> };
    const data = payload.hourly;
    const i = data?.time?.indexOf(hour) ?? -1;
    if (!data || i < 0) throw new Error("Missing forecast hour");
    const read = (name: string) => {
      const value = data[name]?.[i];
      return typeof value === "number" && Number.isFinite(value) ? value : null;
    };
    const vectors = layers.map(h => {
      const speed = read(`wind_speed_${h}m`), from = read(`wind_direction_${h}m`);
      if (speed === null || from === null) throw new Error("Missing forecast wind");
      const a = from * Math.PI / 180;
      return { x: speed * Math.sin(a), y: speed * Math.cos(a) };
    });
    const [a, b = a] = vectors, f = lower === upper ? 0 : (altitude - lower) / (upper - lower);
    const x = a.x + (b.x - a.x) * f, y = a.y + (b.y - a.y) * f;
    return { target: { lat, lon }, valid: hour + "Z", fetched: new Date().toISOString(), altitude, lower, upper,
      speed: Math.hypot(x, y), direction: (Math.atan2(x, y) * 180 / Math.PI + 360) % 360,
      gust: read("wind_gusts_10m"), visibility: read("visibility"), temperature: read("temperature_2m"), precipitation: read("precipitation"),
    };
  } catch {
    throw new Error("Open-Meteo forecast unavailable for this point and hour. Try again or enter manual weather.");
  }
}
