


def classify_job(title, description):
    text = (title + " " + description).lower()

    if any(k in text for k in ["real estate", "photographer", "videographer", "media"]):
        return "media"

    if any(k in text for k in ["photogrammetry", "mapping", "gis", "survey"]):
        return "mapping"

    if any(k in text for k in ["inspection", "roof", "tower", "construction"]):
        return "inspection"

    if any(k in text for k in ["film", "cinema", "tv", "production"]):
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