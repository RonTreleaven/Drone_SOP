// Coordinate utilities: parse various formats and format for map/KML/NOTAM
const CoordUtils = (() => {
  // Helpers
  const toFloat = s => (s === null || s === undefined ? null : Number(s));
  const clamp = (v,min,max) => Math.max(min, Math.min(max, v));

  // Parse one coordinate token (latitude or longitude)
  // Accepts: decimal with sign or trailing N/S/E/W, DM (DDMM or DDDMM) optionally with symbols,
  // DMS (D M S) with separators, compact NOTAM pieces (e.g., 4414N or 07938W)
  function parseSingle(token) {
    if (!token) return null;
    token = token.trim();
    // If contains comma or space-separated DMS parts handle below
    // Try detect trailing cardinal
    const cardMatch = token.match(/([NSWE])$/i);
    const card = cardMatch ? cardMatch[1].toUpperCase() : null;
    let core = card ? token.slice(0, -1) : token;

    // If token contains degrees symbol or separators: replace ° ' " with spaces
    core = core.replace(/[°º∘]/g, ' ')
               .replace(/[’‘′′′‘'`]/g, "'")
               .replace(/[“”″"]/g, '"')
               .replace(/[^\d.+-]/g, ' ')
               .trim();

    const parts = core.split(/\s+/).filter(Boolean);

    // Case 1: pure decimal (single numeric string, possibly with sign)
    if (parts.length === 1 && /^[-+]?(\d+(\.\d*)?|\.\d+)$/.test(parts[0])) {
      let v = Number(parts[0]);
      if (card) {
        if (card === 'S' || card === 'W') v = -Math.abs(v);
        else v = Math.abs(v);
      }
      return v;
    }

    // Case 2: compact DM like 4414 or 07938 (no separators) - interpret by length
    if (parts.length === 1 && /^\d+$/.test(parts[0])) {
      const s = parts[0];
      // latitude: expected DDMM (4) or DDMMSS(6) ; longitude: DDDMM (5) or DDDMMSS(7)
      if (s.length === 4 || s.length === 6) {
        // lat-ish
        const deg = Number(s.slice(0, s.length === 4 ? 2 : 2));
        const min = Number(s.slice(s.length === 4 ? 2 : 4, s.length === 4 ? 4 : 6)) || 0;
        const sec = s.length === 6 ? Number(s.slice(4,6)) : 0;
        let dd = deg + (min / 60) + (sec / 3600);
        if (card === 'S') dd = -dd;
        return dd;
      }
      if (s.length === 5 || s.length === 7) {
        // lon-ish
        const deg = Number(s.slice(0, s.length === 5 ? 3 : 3));
        const min = Number(s.slice(s.length === 5 ? 3 : 5, s.length === 5 ? 5 : 7)) || 0;
        const sec = s.length === 7 ? Number(s.slice(5,7)) : 0;
        let dd = deg + (min / 60) + (sec / 3600);
        if (card === 'W') dd = -dd;
        return dd;
      }
    }

    // Case 3: parts = [deg, min, sec?]
    if (parts.length >= 2) {
      const deg = Number(parts[0]);
      const min = Number(parts[1]) || 0;
      const sec = Number(parts[2]) || 0;
      let sign = 1;
      if (card) {
        if (card === 'S' || card === 'W') sign = -1;
      } else {
        // if degrees have sign
        if (String(parts[0]).startsWith('-')) sign = -1;
      }
      const dd = Math.abs(deg) + (min / 60) + (sec / 3600);
      return sign * dd;
    }

    return null;
  }

  // Parse an input that may be:
  // - NOTAM compact pair like "4414N07938W001" or "4414N07938W"
  // - two coords separated by comma/space "44.2333,-79.6333" or "44 14 N 079 38 W"
  function parseCoordinateString(input) {
    if (!input) return null;
    input = String(input).trim();

    // Detect NOTAM compact pair: lat(4-6)+N/S + lon(5-7)+E/W optionally followed by radius
    const notamPair = input.match(/^(\d{4,6}[NS])\s*(\d{5,7}[EW])(?:\d{3})?$/i);
    if (notamPair) {
      const lat = parseSingle(notamPair[1]);
      const lon = parseSingle(notamPair[2]);
      return lat !== null && lon !== null ? { lat, lon } : null;
    }

    // Try split by comma
    let parts = input.split(',');
    if (parts.length === 2) {
      const a = parseSingle(parts[0].trim());
      const b = parseSingle(parts[1].trim());
      // Determine which is lat/lon: heuristics -> latitude range [-90,90]
      if (Math.abs(a) <= 90 && Math.abs(b) <= 180) return { lat: a, lon: b };
      if (Math.abs(b) <= 90 && Math.abs(a) <= 180) return { lat: b, lon: a };
      return null;
    }

    // Otherwise split by whitespace and try to find two coord tokens (with cardinals)
    const tokens = input.split(/\s+/).filter(Boolean);
    // If tokens contain two tokens with N/S and E/W, take them
    const nsToken = tokens.find(t => /[NS]$/i.test(t));
    const ewToken = tokens.find(t => /[EW]$/i.test(t));
    if (nsToken && ewToken) {
      const lat = parseSingle(nsToken);
      const lon = parseSingle(ewToken);
      return lat !== null && lon !== null ? { lat, lon } : null;
    }

    // If exactly two numeric-like tokens, parse both and assign by range
    if (tokens.length === 2) {
      const a = parseSingle(tokens[0]);
      const b = parseSingle(tokens[1]);
      if (Math.abs(a) <= 90 && Math.abs(b) <= 180) return { lat: a, lon: b };
      if (Math.abs(b) <= 90 && Math.abs(a) <= 180) return { lat: b, lon: a };
    }

    // Fallback: attempt to find any lat-like and lon-like substrings using regex
    const coordRegex = /(-?\d+(?:\.\d+)?)[ ,]+(-?\d+(?:\.\d+)?)/;
    const m = input.match(coordRegex);
    if (m) return { lat: Number(m[1]), lon: Number(m[2]) };

    return null;
  }

  // Formatting
  function toMapString(lat, lon, decimals = 6) {
    return `${lat.toFixed(decimals)}, ${lon.toFixed(decimals)}`;
  }
  function toKmlString(lat, lon, decimals = 6) {
    // KML expects lon,lat[,alt]
    return `${lon.toFixed(decimals)},${lat.toFixed(decimals)}`;
  }

  // Format NOTAM compact DM: lat -> DDMMN/S , lon -> DDDMME/W
  function toNotamCompact(lat, lon) {
    const latSign = lat < 0 ? 'S' : 'N';
    const lonSign = lon < 0 ? 'W' : 'E';
    const a = Math.abs(lat);
    const b = Math.abs(lon);
    const latDeg = Math.floor(a); const latMin = Math.round((a - latDeg) * 60);
    const lonDeg = Math.floor(b); const lonMin = Math.round((b - lonDeg) * 60);
    const latStr = String(latDeg).padStart(2, '0') + String(latMin).padStart(2, '0') + latSign;
    const lonStr = String(lonDeg).padStart(3, '0') + String(lonMin).padStart(2, '0') + lonSign;
    return latStr + lonStr;
  }

  return {
    parseCoordinateString,
    parseSingle,
    toMapString,
    toKmlString,
    toNotamCompact
  };
})();

// Example usage:
// CoordUtils.parseCoordinateString("4414N07938W001") -> {lat:44.233333..., lon:-79.633333...}
// CoordUtils.toMapString(44.2333333, -79.6333333) -> "44.233333, -79.633333"
// CoordUtils.toKmlString(44.2333333, -79.6333333) -> "-79.633333,44.233333"
// CoordUtils.toNotamCompact(44.2333333, -79.6333333) -> "4414N07938W"
 