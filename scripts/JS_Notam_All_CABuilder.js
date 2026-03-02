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
    https
      .get(url, (res) => {
        const { statusCode } = res;
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          if (!statusCode || statusCode < 200 || statusCode >= 300) {
            reject(new Error(`Failed to fetch data for ICAO code '${icao}'. Response: ${body}`));
            return;
          }
          try {
            resolve(JSON.parse(body));
          } catch (err) {
            reject(new Error(`Failed to parse API response JSON: ${err.message}`));
          }
        });
      })
      .on("error", (err) => reject(new Error(`Request failed: ${err.message}`)));
  });
}

function filterAndTransform(data) {
  const all = data?.data || [];
  const totalNotams = all.length;
  const notamsList = [];

  for (const item of all) {
    const rawText = parseRawText(item?.text);
    if (!rawText) continue;

    const upper = rawText.toUpperCase();
    const hasKeyword = KEYWORDS.some((k) => upper.includes(k));
    if (!hasKeyword) continue;

    const matches = extractDms(rawText);
    const coordsDd = matches.map(([lat, lon]) => {
      const [latDd, lonDd] = dmsToDd(lat, lon);
      return `${latDd.toFixed(6)}, ${lonDd.toFixed(6)}`;
    });

    notamsList.push({
      raw: rawText,
      startValidity: item?.startValidity || null,
      endValidity: item?.endValidity || null,
      coordinates_dd: coordsDd,
    });
  }

  return { totalNotams, notamsList };
}

async function fetchAndSave(firKey, fir) {
  // split ICAO string; API doesn't accept more than one site at once
  const icaos = fir.icao.split(",").map((s) => s.trim()).filter(Boolean);
  let accumulated = [];

  for (const icao of icaos) {
    try {
      const data = await fetchNotams(icao);
      const { notamsList } = filterAndTransform(data);
      accumulated = accumulated.concat(notamsList);
    } catch (err) {
      console.error(`error fetching ${icao}:`, err.message || err);
    }
  }

  const filename = `${fir.name.replace(/[^a-zA-Z0-9]/g, "_")}.json`;
  await fs.writeFile(filename, JSON.stringify(accumulated, null, 2), "utf8");
  console.log(`wrote ${accumulated.length} entries to ${filename}`);
  return accumulated;
}

async function buildAll() {
  try {
    let allCa = [];

    for (const [key, fir] of Object.entries(FIRS)) {
      const list = await fetchAndSave(key, fir);
      // when building the "All CA" file, include every FIR except the
      // artificial aggregate entry (#8) to avoid duplicating the same
      // information twice.
      if (key !== "8") {
        allCa = allCa.concat(list);
      }
    }

    await fs.writeFile("All_CA.json", JSON.stringify(allCa, null, 2), "utf8");
    console.log(`wrote aggregated All_CA.json with ${allCa.length} total items`);
  } catch (err) {
    console.error("Fatal error", err);
    process.exitCode = 1;
  }
}

// run when executed directly
if (require.main === module) {
  buildAll();
}
