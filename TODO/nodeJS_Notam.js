## Node.js script to fetch NOTAMS each morning from GitHub Pages...
## March 10, 2026 
## looking to make some minor changes...



// Node.js script to fetch NOTAMs for each FIR and write individual JSON files
// plus an aggregated "All_CA.json" containing every filtered NOTAM from the
// seven Canadian FIRS.  The original 1.1 script asked interactively for a
// single ICAO; the API doesn't accept a comma‑separated list, so the "All
// Canadian FIRS" entry had been failing.  Here we split that entry and
// iterate each code.

// called with Node "JS Notam Builder.js" to start to create .json by FIR and All_CA consolidated .json
// updated March 2, 2026 to run in GitHub with ACTION to run daily....



const fs = require("fs/promises");
const https = require("https");
const path = require("path");

const OUTPUT_DIR = path.resolve(__dirname, "..", "data", "notams");
const API_TIMEOUT_MS = 30000;

const FIRS = {
  "1": { name: "Edmonton", icao: "CZEG" },
  "2": { name: "Gander", icao: "CZQX" },
  "3": { name: "Moncton", icao: "CZQM" },
  "4": { name: "Montreal", icao: "CZUL" },
  "5": { name: "Toronto", icao: "CZYZ" },
  "6": { name: "Vancouver", icao: "CZVR" },
  "7": { name: "Winnipeg", icao: "CZWG" },
};

const KEYWORDS = [
  "PARAJUMP",
  "PARACHUTE",
  "ADVISORY",
  "CRANE",
  "GPS",
  "RESTRICTED",
  "OBST",
  "TFR",
  "DANGER",
  "RPAS",
  "UAS",
  "DRONE",
  "CYR",
  "AIRSHOW",
];

function extractDms(text) {
  const regex = /(\d{6}[NS])\s*(\d{7}[EW])/g;
  const matches = [];
  let m;
  while ((m = regex.exec(text)) !== null) {
    matches.push([m[1], m[2]]);
  }
  return matches;
}

function dmsToDd(dmsLat, dmsLon) {
  const latDeg = Number(dmsLat.slice(0, 2));
  const latMin = Number(dmsLat.slice(2, 4));
  const latSec = Number(dmsLat.slice(4, 6));
  const latDir = dmsLat.slice(-1);
  let latDd = latDeg + latMin / 60 + latSec / 3600;
  if (latDir === "S") latDd = -latDd;

  const lonDeg = Number(dmsLon.slice(0, 3));
  const lonMin = Number(dmsLon.slice(3, 5));
  const lonSec = Number(dmsLon.slice(5, 7));
  const lonDir = dmsLon.slice(-1);
  let lonDd = lonDeg + lonMin / 60 + lonSec / 3600;
  if (lonDir === "W") lonDd = -lonDd;

  return [Number(latDd.toFixed(6)), Number(lonDd.toFixed(6))];
}

function parseRawText(textField) {
  try {
    const parsed = JSON.parse(textField || "{}");
    return parsed.raw || "";
  } catch {
    return "";
  }
}

async function fetchNotams(icao) {
  const url = `https://plan.navcanada.ca/weather/api/alpha/?site=${encodeURIComponent(
    icao
  )}&alpha=notam&notam_choice=default`;

  return new Promise((resolve, reject) => {
    const req = https.get(
      url,
      {
        headers: {
          Accept: "application/json",
          "User-Agent": "drone-sop-notam-fetch/1.0",
        },
      },
      (res) => {
        const { statusCode } = res;
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          if (!statusCode || statusCode < 200 || statusCode >= 300) {
            reject(
              new Error(`Failed to fetch data for ICAO code '${icao}'. Response: ${body}`)
            );
            return;
          }
          try {
            resolve(JSON.parse(body));
          } catch (err) {
            reject(new Error(`Failed to parse API response JSON: ${err.message}`));
          }
        });
      }
    );

    req.setTimeout(API_TIMEOUT_MS, () => {
      req.destroy(new Error(`Request timed out after ${API_TIMEOUT_MS} ms for ${icao}`));
    });
    req.on("error", (err) => reject(new Error(`Request failed: ${err.message}`)));
  });
}

function filterAndTransform(data) {
  const all = data?.data || [];
  const totalNotams = all.length;
  const rawNotamsList = [];
  const notamsList = [];

  for (const item of all) {
    const rawText = parseRawText(item?.text);
    if (!rawText) continue;

    const matches = extractDms(rawText);
    const coordsDd = matches.map(([lat, lon]) => {
      const [latDd, lonDd] = dmsToDd(lat, lon);
      return `${latDd.toFixed(6)}, ${lonDd.toFixed(6)}`;
    });

    const normalized = {
      raw: rawText,
      startValidity: item?.startValidity || null,
      endValidity: item?.endValidity || null,
      coordinates_dd: coordsDd,
    };

    // Keep a complete, unfiltered copy for search/reporting use-cases.
    rawNotamsList.push(normalized);

    const upper = rawText.toUpperCase();
    const hasKeyword = KEYWORDS.some((k) => upper.includes(k));
    if (!hasKeyword) continue;

    notamsList.push(normalized);
  }

  return { totalNotams, rawNotamsList, notamsList };
}

async function fetchAndSave(firKey, fir) {
  // split ICAO string; API doesn't accept more than one site at once
  const icaos = fir.icao.split(",").map((s) => s.trim()).filter(Boolean);
  let accumulatedRaw = [];
  let accumulated = [];

  for (const icao of icaos) {
    const data = await fetchNotams(icao);
    const { rawNotamsList, notamsList } = filterAndTransform(data);
    accumulatedRaw = accumulatedRaw.concat(rawNotamsList);
    accumulated = accumulated.concat(notamsList);
  }

  if (accumulatedRaw.length === 0) {
    throw new Error(`No NOTAM payload returned for ${fir.name} (${fir.icao})`);
  }

  const filename = `${fir.name.replace(/[^a-zA-Z0-9]/g, "_")}.json`;
  const outPath = path.join(OUTPUT_DIR, filename);
  await fs.writeFile(outPath, JSON.stringify(accumulated, null, 2), "utf8");
  console.log(
    `wrote ${accumulated.length} filtered entries to ${outPath} (raw count: ${accumulatedRaw.length})`
  );
  return { filtered: accumulated, raw: accumulatedRaw };
}

async function buildAll() {
  try {
    await fs.mkdir(OUTPUT_DIR, { recursive: true });

    let allCaRaw = [];
    let allCa = [];
    const generatedAt = new Date().toISOString();

    for (const [key, fir] of Object.entries(FIRS)) {
      const list = await fetchAndSave(key, fir);
      allCaRaw = allCaRaw.concat(list.raw);
      allCa = allCa.concat(list.filtered);
    }

    if (allCaRaw.length === 0) {
      throw new Error("No NOTAM data was fetched from any FIR; aborting write.");
    }

    const rawPath = path.join(OUTPUT_DIR, "All_CA_raw.json");
    const filteredPath = path.join(OUTPUT_DIR, "All_CA.json");
    const metaPath = path.join(OUTPUT_DIR, "All_CA.meta.json");

    await fs.writeFile(rawPath, JSON.stringify(allCaRaw, null, 2), "utf8");
    await fs.writeFile(filteredPath, JSON.stringify(allCa, null, 2), "utf8");
    await fs.writeFile(
      metaPath,
      JSON.stringify(
        {
          generatedAt,
          totalItems: allCa.length,
          filteredTotalItems: allCa.length,
          rawTotalItems: allCaRaw.length,
        },
        null,
        2
      ),
      "utf8"
    );
    console.log(`wrote aggregated ${rawPath} with ${allCaRaw.length} total raw items`);
    console.log(`wrote aggregated ${filteredPath} with ${allCa.length} total filtered items`);
    console.log(`wrote ${metaPath} generatedAt ${generatedAt}`);
  } catch (err) {
    console.error("Fatal error", err);
    process.exitCode = 1;
  }
}

// run when executed directly
if (require.main === module) {
  buildAll();
}
