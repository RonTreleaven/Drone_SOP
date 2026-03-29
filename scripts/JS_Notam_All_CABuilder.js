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

const LIVE_QCODE_ALLOWLIST = new Set(["QOBCE", "QOLAS"]);
const LIVE_Q_SUBJECT_ALLOWLIST = new Set(["OB", "OL"]);

function mapDmsToDecimal(token, isLat) {
  const clean = String(token || "").toUpperCase().trim();
  const dir = clean.slice(-1);
  const body = clean.slice(0, -1);
  if (isLat && !/[NS]/.test(dir)) return null;
  if (!isLat && !/[EW]/.test(dir)) return null;
  const degDigits = isLat ? 2 : 3;
  if (!/^\d+$/.test(body)) return null;
  if (body.length !== degDigits + 2 && body.length !== degDigits + 4) return null;
  const deg = Number(body.slice(0, degDigits));
  const min = Number(body.slice(degDigits, degDigits + 2));
  const sec = body.length === degDigits + 4 ? Number(body.slice(degDigits + 2, degDigits + 4)) : 0;
  if (min >= 60 || sec >= 60) return null;
  let dd = deg + (min / 60) + (sec / 3600);
  if (dir === "S" || dir === "W") dd = -dd;
  return dd;
}

function mapExtractCoordsFromText(text) {
  const value = String(text || "");
  const pairRegex = /(\d{4,6}[NS])\s*(\d{5,7}[EW])/gi;
  const found = [];
  let match;
  while ((match = pairRegex.exec(value)) !== null) {
    const lat = mapDmsToDecimal((match[1] || "").toUpperCase(), true);
    const lon = mapDmsToDecimal((match[2] || "").toUpperCase(), false);
    if (lat == null || lon == null) continue;
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) continue;
    found.push({ lat, lon });
  }
  return found;
}

function mapExtractPrimaryCoord(rawText) {
  const value = String(rawText || "");
  if (!value) return null;
  const eMatch = value.match(/E\)\s*([\s\S]*?)(?=(?:\n|\r\n?)[A-Z]\)|$)/);
  const eSection = eMatch ? String(eMatch[0] || "") : "";
  const eCoords = mapExtractCoordsFromText(eSection);
  if (eCoords.length > 0) return eCoords[0];
  const anyCoords = mapExtractCoordsFromText(value);
  return anyCoords.length > 0 ? anyCoords[0] : null;
}

function parseNotamText(textField) {
  if (typeof textField !== "string") return "";
  try {
    const parsed = JSON.parse(textField || "{}");
    if (parsed && typeof parsed === "object") {
      return String(parsed.raw || parsed.english || parsed.french || "");
    }
  } catch {
    return String(textField || "");
  }
  return "";
}

function extractQCode(rawText) {
  const match = String(rawText || "").match(/Q\)\s*[^/\s]+\/([A-Z]{5})\//i);
  return match ? String(match[1] || "").toUpperCase() : "";
}

function shouldKeepFiltered(rawText) {
  const qCode = extractQCode(rawText);
  if (!qCode) return false;
  if (LIVE_QCODE_ALLOWLIST.has(qCode)) return true;
  return LIVE_Q_SUBJECT_ALLOWLIST.has(qCode.slice(1, 3));
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
    const rawText = parseNotamText(item?.text);
    if (!rawText) continue;

    const primaryCoord = mapExtractPrimaryCoord(rawText);
    const coordsDd = primaryCoord
      ? [`${Number(primaryCoord.lat).toFixed(6)}, ${Number(primaryCoord.lon).toFixed(6)}`]
      : [];
    const qCode = extractQCode(rawText);

    const normalized = {
      raw: rawText,
      startValidity: item?.startValidity || null,
      endValidity: item?.endValidity || null,
      q_code: qCode || null,
      coordinates_dd: coordsDd,
    };

    // Keep a complete, unfiltered copy for search/reporting use-cases.
    rawNotamsList.push(normalized);

    if (!shouldKeepFiltered(rawText)) continue;

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
