import re
import unicodedata
from datetime import datetime, timezone
from html import unescape

TAG_RE = re.compile(r"<[^>]+>")
MOJIBAKE_MARKERS = ("Ã", "â", "Â")


def strip_tags(value):
    return TAG_RE.sub(" ", value)


def _repair_mojibake(text):
    if not any(marker in text for marker in MOJIBAKE_MARKERS):
        return text

    try:
        repaired = text.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
        return repaired
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def normalize_text(value, strip_html=False):
    if value is None:
        return ""

    text = unescape(str(value))
    if strip_html:
        text = strip_tags(text)

    text = _repair_mojibake(text)
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\xa0", " ")
    text = " ".join(text.split())

    # Fold accented characters to ASCII for consistent matching/export formatting.
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.strip()


def parse_date_value(value):
    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        try:
            ts = float(value)
            if ts > 1_000_000_000_000:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None

    text = str(value).strip()
    if not text:
        return None

    if text.isdigit():
        try:
            ts = float(text)
            if ts > 1_000_000_000_000:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None

    iso_text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_text)
    except ValueError:
        pass

    for fmt in (
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%b %d, %Y",
        "%B %d, %Y",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def normalize_date(value):
    parsed = parse_date_value(value)
    if not parsed:
        return ""
    return parsed.strftime("%m/%d/%Y")
