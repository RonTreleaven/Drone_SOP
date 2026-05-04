QUERIES = [
    "drone pilot Ontario",
    "UAV operator Ontario",
    "RPAS pilot Canada",
    "drone photographer Toronto",
    "aerial photographer Ontario",
    "videographer drone Toronto freelance",
    "photogrammetry drone Ontario",
    "GIS drone technician Ontario",
    "survey technician UAV Ontario"
]

INDEED_RSS = "https://ca.indeed.com/rss?q={query}"


def classify_job(title, description):
    text = (title + " " + description).lower()

    if any(k in text for k in ["real estate", "photographer", "videographer", "media"]):
        return "media"

    if any(k in text for k in ["photogrammetry", "mapping", "gis", "survey"]):
        return "mapping"

    if any(k in text for k in ["inspection", "roof", "tower", "construction"]):
        return "inspection"

    # Keep film matching explicit; generic "production" causes engineering false positives.
    if any(k in text for k in ["film", "cinema", " tv ", "television", "movie", "documentary"]):
        return "film"

    return "general"


def detect_type(title, description):
    text = (title + " " + description).lower()

    if "contract" in text:
        return "contract"
    if "part-time" in text:
        return "part-time"
    if "freelance" in text:
        return "freelance"

    return "unknown"