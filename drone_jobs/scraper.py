import argparse
import json
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus
from urllib.parse import urljoin

import feedparser
import requests

from classifier import classify_job, detect_type
from config import (
    DEFAULT_SOURCES,
    EXCLUDED_TITLE_PHRASES,
    GREENHOUSE_BOARDS,
    GREENHOUSE_JOBS_API,
    INDEED_RSS,
    JOBBANK_SEARCH,
    JOBS_BEAR_SEARCH,
    LEVER_POSTINGS_API,
    LEVER_SITES,
    QUERY_FAMILIES,
    REQUIRED_ROLE_TERMS_IN_TITLE,
    SIMPLYHIRED_SEARCH,
    TALENT_SEARCH,
)
from database import clear_jobs, init_db, insert_job
from normalization import normalize_date, normalize_text

DRONE_WEIGHTS = {
    "drone": 0.30,
    "uav": 0.30,
    "rpas": 0.30,
    "uas": 0.25,
    "aerial": 0.20,
    "photogrammetry": 0.25,
    "lidar": 0.20,
    "geospatial": 0.20,
}
CORE_DRONE_TERMS = [
    "drone",
    "uav",
    "rpas",
    "uas",
    "unmanned aerial",
    "remotely piloted",
]
DRONE_CONTEXT_PHRASES = [
    "drone pilot",
    "drone operator",
    "drone operations",
    "uav operator",
    "uav pilot",
    "rpas pilot",
    "remote pilot",
    "aerial survey",
    "drone inspection",
    "drone mapping",
]
JOB_WEIGHTS = {
    "pilot": 0.25,
    "operator": 0.20,
    "inspector": 0.20,
    "survey": 0.20,
    "surveyor": 0.20,
    "photographer": 0.20,
    "videographer": 0.20,
    "hiring": 0.15,
    "apply": 0.10,
    "career": 0.10,
    "job": 0.10,
}
NEGATIVE_TERMS = {
    "training": 0.25,
    "course": 0.25,
    "forum": 0.25,
    "wikipedia": 0.30,
    "wiki": 0.20,
    "overview": 0.20,
    "exam": 0.20,
    "community": 0.20,
}
SOURCE_WEIGHTS = {
    "indeed": 0.20,
    "jobbank": 0.30,
    "simplyhired": 0.25,
    "talent": 0.20,
    "jobs_bear": 0.22,
    "greenhouse": 0.28,
    "lever": 0.27,
}
FAMILY_SIGNAL_TERMS = {
    "operations": ["pilot", "operator", "flight", "uas", "uav", "rpas"],
    "mapping": ["survey", "mapping", "photogrammetry", "lidar", "gis", "geospatial"],
    "inspection": ["inspection", "inspector", "tower", "roof", "utility", "powerline"],
    "media": ["videographer", "photographer", "cinema", "media", "content"],
    "technical": ["maintenance", "assembly", "avionics", "repair"],
}
JOB_URL_TOKENS = ["jobposting", "/job/", "/jobs", "careers", "jobsearch"]
ARTICLE_RE = re.compile(r'<article[^>]*class="action-buttons"[^>]*>(.*?)</article>', re.S)
LDJSON_RE = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
SIMPLYHIRED_LINK_RE = re.compile(r'href="(/job/[^"]+)"')


def normalize_date_value(value):
    return normalize_date(value)


def iter_query_pairs():
    for family, terms in QUERY_FAMILIES.items():
        for query in terms:
            yield family, query


def fetch_url(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        print("Request failed:", exc)
        return None


def strip_tags(value):
    return re.sub(r"<[^>]+>", " ", value)


def clean_text(value):
    return normalize_text(value, strip_html=True)


def parse_entry(entry, source):
    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    summary = entry.get("summary", "")
    company = entry.get("author", "Unknown")
    location = entry.get("where", "Canada")

    return {
        "title": title,
        "company": company,
        "location": location,
        "link": link,
        "description": clean_text(summary),
        "date_posted": normalize_date_value(entry.get("published") or entry.get("updated")),
        "date_expires": "",
        "category": classify_job(title, summary),
        "type": detect_type(title, summary),
        "source": source,
    }


def normalize_jobbank_link(link):
    link = urljoin("https://www.jobbank.gc.ca", link)
    if ";jsessionid=" in link:
        link = link.split(";jsessionid=", 1)[0] + ("?" + link.split("?", 1)[1] if "?" in link else "")
    return link


def parse_jobbank_article(article):
    link_match = re.search(r'<a\s+href="([^"]*/jobsearch/jobposting/[^"]+)"[^>]*class="resultJobItem"', article)
    title_match = re.search(r'<span\s+class="noctitle">(.*?)</span>', article, re.S)
    company_match = re.search(r'<li\s+class="business">(.*?)</li>', article, re.S)
    location_match = re.search(r'<li\s+class="location">(.*?)</li>', article, re.S)

    if not link_match or not title_match:
        return None

    title = clean_text(title_match.group(1))
    company = clean_text(company_match.group(1)) if company_match else "Unknown"
    location = clean_text(location_match.group(1)).replace("Location", "").strip() if location_match else "Canada"
    if not location:
        location = "Canada"

    description = clean_text(article)
    return {
        "title": title,
        "company": company,
        "location": location,
        "link": normalize_jobbank_link(link_match.group(1)),
        "description": description,
        "date_posted": "",
        "date_expires": "",
        "category": classify_job(title, description),
        "type": detect_type(title, description),
        "source": "jobbank",
    }


def load_json_blocks(html):
    blocks = []
    for raw in LDJSON_RE.findall(html):
        text = raw.strip()
        if not text:
            continue
        try:
            blocks.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    return blocks


def extract_next_data(html):
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def find_jobposting_node(value):
    if isinstance(value, dict):
        node_type = value.get("@type", "")
        if isinstance(node_type, list):
            if "JobPosting" in node_type:
                return value
        elif node_type == "JobPosting":
            return value

        for child in value.values():
            found = find_jobposting_node(child)
            if found:
                return found

    if isinstance(value, list):
        for item in value:
            found = find_jobposting_node(item)
            if found:
                return found

    return None


def location_from_jobposting(node):
    location = node.get("jobLocation")
    if isinstance(location, list):
        location = location[0] if location else {}
    if isinstance(location, dict):
        address = location.get("address", location)
        if isinstance(address, dict):
            parts = [
                address.get("addressLocality", ""),
                address.get("addressRegion", ""),
                address.get("addressCountry", ""),
            ]
            cleaned = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
            if cleaned:
                return ", ".join(cleaned)
    return "Canada"


def parse_jobposting_page(html, source, fallback_link):
    node = None
    for block in load_json_blocks(html):
        node = find_jobposting_node(block)
        if node:
            break

    if not node:
        return None

    title = clean_text(node.get("title") or node.get("name") or "")
    if not title:
        return None

    org = node.get("hiringOrganization", {})
    if isinstance(org, list):
        org = org[0] if org else {}
    company = clean_text(org.get("name", "Unknown")) if isinstance(org, dict) else "Unknown"
    description = clean_text(node.get("description", ""))
    link = (node.get("url") or fallback_link or "").strip()
    location = location_from_jobposting(node)
    employment = node.get("employmentType", "")
    employment_text = " ".join(employment) if isinstance(employment, list) else str(employment)
    combined_description = f"{description} {employment_text}".strip()

    return {
        "title": title,
        "company": company,
        "location": location,
        "link": link,
        "description": combined_description,
        "date_posted": normalize_date_value(node.get("datePosted") or node.get("datePublished")),
        "date_expires": normalize_date_value(node.get("validThrough") or node.get("dateExpires")),
        "category": classify_job(title, combined_description),
        "type": detect_type(title, combined_description),
        "source": source,
    }


def parse_jobs_bear_jobs(html):
    payload = extract_next_data(html)
    page_props = (payload.get("props") or {}).get("pageProps") or {}
    items = page_props.get("jobs") or []
    parsed_jobs = []

    for item in items:
        if not isinstance(item, dict):
            continue

        title = clean_text(item.get("title", ""))
        if not title:
            continue

        company = clean_text(item.get("src", "Unknown")) or "Unknown"
        location = clean_text(item.get("location", "Canada")) or "Canada"
        description = clean_text(item.get("body", ""))
        link = str(item.get("url", "")).strip()

        parsed_jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "link": link,
            "description": description,
            "date_posted": normalize_date_value(item.get("date") or item.get("publishedAt") or item.get("createdAt")),
            "date_expires": normalize_date_value(item.get("validThrough") or item.get("expiresAt")),
            "category": classify_job(title, description),
            "type": detect_type(title, description),
            "source": "jobs_bear",
        })

    return parsed_jobs


def enrich_jobbank_with_detail(base_job):
    detail = fetch_url(base_job["link"])
    if detail is None:
        return base_job

    detailed = parse_jobposting_page(detail.text, "jobbank", base_job["link"])
    if not detailed:
        return base_job

    merged = base_job.copy()
    for key, value in detailed.items():
        if value and value != "Unknown":
            merged[key] = value

    merged["category"] = classify_job(merged["title"], merged.get("description", ""))
    merged["type"] = detect_type(merged["title"], merged.get("description", ""))
    return merged


def talent_links_from_search(html):
    links = []
    for block in load_json_blocks(html):
        if not isinstance(block, dict):
            continue

        graph = block.get("@graph", [])
        if not isinstance(graph, list):
            continue

        for item in graph:
            if not isinstance(item, dict) or item.get("@type") != "ItemList":
                continue

            elements = item.get("itemListElement", [])
            for element in elements:
                if not isinstance(element, dict):
                    continue
                page = element.get("item", {})
                if isinstance(page, dict):
                    link = str(page.get("url", "")).strip()
                    if link.startswith("https://ca.talent.com/view?id="):
                        links.append(link)

    return list(dict.fromkeys(links))


def evaluate_job_match(job):
    title_text = str(job.get("title", "")).lower()
    company_text = str(job.get("company", "")).lower()
    desc_text = str(job.get("description", "")).lower()
    link = str(job.get("link", "")).lower()
    query_family = str(job.get("query_family", "")).lower()
    title_and_desc = f"{title_text} {desc_text}"
    has_uav_rpas_context = ("uav" in title_and_desc) or ("rpas" in title_and_desc)

    if any(phrase in title_text for phrase in EXCLUDED_TITLE_PHRASES) and not has_uav_rpas_context:
        return False, 0.0, "excluded title phrase"

    text = " ".join([
        title_text,
        company_text,
        str(job.get("location", "")).lower(),
        desc_text,
        link,
    ])

    # Use a short, high-signal window to avoid matching on unrelated sidebar/recommendation content.
    primary_signal_text = " ".join([
        title_text,
        company_text,
        desc_text[:450],
        link,
    ])

    score = 0.0
    reasons = []

    matched_drone = []
    for term, weight in DRONE_WEIGHTS.items():
        if term in text:
            score += weight
            matched_drone.append(term)

    matched_job = []
    for term, weight in JOB_WEIGHTS.items():
        if term in text:
            score += weight
            matched_job.append(term)

    for term, penalty in NEGATIVE_TERMS.items():
        if term in text:
            score -= penalty

    if any(token in link for token in JOB_URL_TOKENS):
        score += 0.15
        reasons.append("job-like URL")

    source = job.get("source", "")
    score += SOURCE_WEIGHTS.get(source, 0)

    family_terms = FAMILY_SIGNAL_TERMS.get(query_family, [])
    family_hits = [term for term in family_terms if term in text]
    if family_hits:
        score += 0.10
        reasons.append("family terms: " + ", ".join(sorted(set(family_hits))))
    elif family_terms:
        score -= 0.10

    if matched_drone:
        reasons.append("drone terms: " + ", ".join(sorted(set(matched_drone))))
    if matched_job:
        reasons.append("job terms: " + ", ".join(sorted(set(matched_job))))
    reasons.append(f"source={source}")
    reasons.append(f"query_family={query_family}")

    has_drone_in_title_or_company = any(term in (title_text + " " + company_text) for term in DRONE_WEIGHTS)
    has_core_drone_in_title = any(term in title_text for term in CORE_DRONE_TERMS)
    has_drone_context_phrase = any(phrase in desc_text for phrase in DRONE_CONTEXT_PHRASES)
    has_core_drone_signal = any(term in primary_signal_text for term in CORE_DRONE_TERMS)
    has_strong_drone_signal = has_core_drone_signal and (has_drone_in_title_or_company or has_drone_context_phrase or ("drone" in title_text))
    has_role_term_in_title = any(term in title_text for term in REQUIRED_ROLE_TERMS_IN_TITLE)
    has_technician_title = "technician" in title_text
    allow_technician_override = has_technician_title and has_uav_rpas_context
    has_job_in_title = has_role_term_in_title or allow_technician_override
    has_job_anywhere = bool(matched_job)

    score = min(score, 0.95)
    score = max(0.0, score)

    if has_drone_context_phrase:
        reasons.append("drone context phrase")
    if has_drone_in_title_or_company:
        reasons.append("drone term in title/company")
    if has_core_drone_in_title:
        reasons.append("core term in title")
    if has_core_drone_signal:
        reasons.append("core drone/uav signal")
    if has_role_term_in_title:
        reasons.append("required role term in title")
    if allow_technician_override:
        reasons.append("technician override via uav/rpas context")

    required_score = 0.55 if allow_technician_override else 0.62
    is_match = has_core_drone_in_title and has_job_in_title and has_strong_drone_signal and has_job_anywhere and score >= required_score
    if not has_job_in_title and source in {"simplyhired", "talent"}:
        is_match = is_match and score >= 0.72

    return is_match, round(score, 3), "; ".join(reasons)


def finalize_job(job):
    is_match, score, reason = evaluate_job_match(job)
    if not is_match:
        return None

    description = job.get("description", "")
    job["summary"] = description[:500]
    job["confidence"] = score
    job["match_reason"] = reason
    job.pop("description", None)
    return job


def attach_query_metadata(job, query_family, matched_query):
    job["query_family"] = query_family
    job["matched_query"] = matched_query
    return job


def infer_query_metadata(title, description):
    text = f"{title} {description}".lower()

    for family, queries in QUERY_FAMILIES.items():
        for query in queries:
            if query.lower() in text:
                return family, query

    best_family = ""
    best_score = 0
    for family, terms in FAMILY_SIGNAL_TERMS.items():
        score = sum(1 for term in terms if term in text)
        if score > best_score:
            best_score = score
            best_family = family

    if best_family and best_score > 0:
        return best_family, QUERY_FAMILIES[best_family][0]

    return "", ""


def parse_greenhouse_job(item, company_name):
    if not isinstance(item, dict):
        return None

    title = clean_text(item.get("title", ""))
    if not title:
        return None

    location_obj = item.get("location") if isinstance(item.get("location"), dict) else {}
    location = clean_text(location_obj.get("name", "Canada")) or "Canada"
    description = clean_text(item.get("content", ""))
    link = str(item.get("absolute_url", "")).strip()

    if not link:
        return None

    return {
        "title": title,
        "company": company_name,
        "location": location,
        "link": link,
        "description": description,
        "date_posted": normalize_date_value(item.get("updated_at") or item.get("first_published")),
        "date_expires": "",
        "category": classify_job(title, description),
        "type": detect_type(title, description),
        "source": "greenhouse",
    }


def lever_millis_to_iso(value):
    if value in (None, ""):
        return ""

    if isinstance(value, (int, float)):
        try:
            return normalize_date_value(datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc))
        except (ValueError, OSError, OverflowError):
            return ""

    if isinstance(value, str) and value.isdigit():
        try:
            return normalize_date_value(datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc))
        except (ValueError, OSError, OverflowError):
            return ""

    return normalize_date_value(value)


def parse_lever_job(item, company_name):
    if not isinstance(item, dict):
        return None

    title = clean_text(item.get("text", ""))
    if not title:
        return None

    categories = item.get("categories") if isinstance(item.get("categories"), dict) else {}
    location = clean_text(categories.get("location", "Canada")) or "Canada"
    description = clean_text(item.get("descriptionPlain") or item.get("descriptionBodyPlain") or item.get("description", ""))
    link = str(item.get("hostedUrl", "")).strip()

    if not link:
        return None

    return {
        "title": title,
        "company": company_name,
        "location": location,
        "link": link,
        "description": description,
        "date_posted": lever_millis_to_iso(item.get("createdAt") or item.get("updatedAt")),
        "date_expires": "",
        "category": classify_job(title, description),
        "type": detect_type(title, description),
        "source": "lever",
    }


def fetch_indeed():
    jobs = []
    blocked = False
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.9",
        "Referer": "https://ca.indeed.com/",
    }

    for query_family, query in iter_query_pairs():
        if blocked:
            break

        url = INDEED_RSS.format(query=quote_plus(query))
        try:
            response = requests.get(url, headers=headers, timeout=20)
        except requests.RequestException as exc:
            print(f"Indeed request failed for '{query}': {exc}")
            continue

        if response.status_code in (403, 429):
            print(
                "\nIndeed RSS appears blocked (HTTP "
                f"{response.status_code}). Skipping Indeed for this run."
            )
            blocked = True
            continue

        if response.status_code >= 400:
            print(f"Indeed RSS HTTP {response.status_code} for query '{query}', skipping query.")
            continue

        content_type = (response.headers.get("content-type") or "").lower()
        body_lower = response.text.lower()
        if ("xml" not in content_type) and ("<rss" not in body_lower and "<feed" not in body_lower):
            print("\nIndeed returned a non-RSS payload. Skipping Indeed for this run.")
            blocked = True
            continue

        if "security check" in body_lower or "captcha" in body_lower:
            print("\nIndeed security challenge detected. Skipping Indeed for this run.")
            blocked = True
            continue

        print("\nFetching:", url)
        print("HTTP Status:", response.status_code)

        feed = feedparser.parse(response.content)
        print("Entries found:", len(feed.entries))

        for entry in feed.entries:
            parsed = parse_entry(entry, "indeed")
            parsed = attach_query_metadata(parsed, query_family, query)
            job = finalize_job(parsed)
            if not job:
                continue
            print(" -", job["title"])
            jobs.append(job)

    return jobs


def fetch_jobbank():
    jobs = []

    for query_family, query in iter_query_pairs():
        url = JOBBANK_SEARCH.format(query=quote_plus(query))
        response = fetch_url(url)
        if response is None:
            continue

        html = response.text
        articles = ARTICLE_RE.findall(html)
        print("\nFetching:", url)
        print("HTTP Status:", response.status_code)
        print("Article cards found:", len(articles))

        for article in articles:
            parsed = parse_jobbank_article(article)
            if parsed is None:
                continue

            parsed = enrich_jobbank_with_detail(parsed)
            parsed = attach_query_metadata(parsed, query_family, query)
            job = finalize_job(parsed)
            if not job:
                continue

            print(" -", job["title"])
            jobs.append(job)

    return jobs


def fetch_simplyhired():
    jobs = []

    for query_family, query in iter_query_pairs():
        url = SIMPLYHIRED_SEARCH.format(query=quote_plus(query))
        response = fetch_url(url)
        if response is None:
            continue

        links = [urljoin("https://www.simplyhired.ca", link) for link in SIMPLYHIRED_LINK_RE.findall(response.text)]
        links = list(dict.fromkeys(links))[:20]

        print("\nFetching:", url)
        print("HTTP Status:", response.status_code)
        print("Detail links found:", len(links))

        for link in links:
            detail = fetch_url(link)
            if detail is None:
                continue

            parsed = parse_jobposting_page(detail.text, "simplyhired", link)
            if parsed is None:
                continue

            parsed = attach_query_metadata(parsed, query_family, query)
            job = finalize_job(parsed)
            if not job:
                continue

            print(" -", job["title"])
            jobs.append(job)

    return jobs


def fetch_talent():
    jobs = []

    for query_family, query in iter_query_pairs():
        url = TALENT_SEARCH.format(query=quote_plus(query))
        response = fetch_url(url)
        if response is None:
            continue

        links = talent_links_from_search(response.text)[:20]

        print("\nFetching:", url)
        print("HTTP Status:", response.status_code)
        print("Detail links found:", len(links))

        for link in links:
            detail = fetch_url(link)
            if detail is None:
                continue

            parsed = parse_jobposting_page(detail.text, "talent", link)
            if parsed is None:
                continue

            parsed = attach_query_metadata(parsed, query_family, query)
            job = finalize_job(parsed)
            if not job:
                continue

            print(" -", job["title"])
            jobs.append(job)

    return jobs


def fetch_jobs_bear():
    jobs = []

    for query_family, query in iter_query_pairs():
        url = JOBS_BEAR_SEARCH.format(query=quote_plus(query))
        response = fetch_url(url)
        if response is None:
            continue

        candidates = parse_jobs_bear_jobs(response.text)

        print("\nFetching:", url)
        print("HTTP Status:", response.status_code)
        print("Jobs found:", len(candidates))

        for parsed in candidates:
            parsed = attach_query_metadata(parsed, query_family, query)
            job = finalize_job(parsed)
            if not job:
                continue

            print(" -", job["title"])
            jobs.append(job)

    return jobs


def fetch_greenhouse():
    jobs = []

    for board, company_name in GREENHOUSE_BOARDS.items():
        url = GREENHOUSE_JOBS_API.format(board=quote_plus(board))
        response = fetch_url(url)
        if response is None:
            continue

        try:
            payload = response.json()
        except ValueError:
            print("Invalid Greenhouse payload for:", board)
            continue

        candidates = payload.get("jobs", []) if isinstance(payload, dict) else []

        print("\nFetching:", url)
        print("HTTP Status:", response.status_code)
        print("Jobs found:", len(candidates))

        for item in candidates:
            parsed = parse_greenhouse_job(item, company_name)
            if parsed is None:
                continue

            family, query = infer_query_metadata(parsed["title"], parsed.get("description", ""))
            parsed = attach_query_metadata(parsed, family, query)

            job = finalize_job(parsed)
            if not job:
                continue

            print(" -", job["title"])
            jobs.append(job)

    return jobs


def fetch_lever():
    jobs = []

    for site, company_name in LEVER_SITES.items():
        url = LEVER_POSTINGS_API.format(site=quote_plus(site))
        response = fetch_url(url)
        if response is None:
            continue

        try:
            candidates = response.json()
        except ValueError:
            print("Invalid Lever payload for:", site)
            continue

        if not isinstance(candidates, list):
            print("Unexpected Lever payload shape for:", site)
            continue

        print("\nFetching:", url)
        print("HTTP Status:", response.status_code)
        print("Jobs found:", len(candidates))

        for item in candidates:
            parsed = parse_lever_job(item, company_name)
            if parsed is None:
                continue

            family, query = infer_query_metadata(parsed["title"], parsed.get("description", ""))
            parsed = attach_query_metadata(parsed, family, query)

            job = finalize_job(parsed)
            if not job:
                continue

            print(" -", job["title"])
            jobs.append(job)

    return jobs


def dedupe_jobs(jobs):
    best_by_link = {}
    for job in jobs:
        link = job.get("link", "").strip()
        if not link:
            continue

        existing = best_by_link.get(link)
        if not existing:
            best_by_link[link] = job
            continue

        if job.get("confidence", 0) > existing.get("confidence", 0):
            best_by_link[link] = job

    return list(best_by_link.values())


def parse_sources(value):
    if not value:
        return None
    sources = [item.strip().lower() for item in value.split(",") if item.strip()]
    return list(dict.fromkeys(sources))


def run(reset=False, sources=None, no_write=False):
    init_db()
    if reset and not no_write:
        clear_jobs()
        print("Cleared existing jobs table")
    elif reset and no_write:
        print("Ignoring --reset because --no-write was provided")

    source_fetchers = {
        "indeed": fetch_indeed,
        "jobbank": fetch_jobbank,
        "simplyhired": fetch_simplyhired,
        "talent": fetch_talent,
        "jobs_bear": fetch_jobs_bear,
        "greenhouse": fetch_greenhouse,
        "lever": fetch_lever,
    }

    selected_sources = sources or list(DEFAULT_SOURCES)
    unknown_sources = [source for source in selected_sources if source not in source_fetchers]
    if unknown_sources:
        valid = ", ".join(sorted(source_fetchers.keys()))
        raise ValueError(f"Unknown source(s): {', '.join(unknown_sources)}. Valid sources: {valid}")

    print("Selected sources:", ", ".join(selected_sources))

    collected = []
    for source in selected_sources:
        collected.extend(source_fetchers[source]())

    jobs = dedupe_jobs(collected)
    inserted = 0
    if no_write:
        print("Preview mode enabled: not writing to jobs.db")
    else:
        for job in jobs:
            inserted += insert_job(job)

    by_source = {}
    for job in jobs:
        by_source[job["source"]] = by_source.get(job["source"], 0) + 1

    by_family = {}
    for job in jobs:
        family = job.get("query_family", "unknown")
        by_family[family] = by_family.get(family, 0) + 1

    avg_conf = round(sum(job.get("confidence", 0) for job in jobs) / len(jobs), 3) if jobs else 0

    print(f"\nCollected {len(collected)} matched jobs")
    print(f"Deduped to {len(jobs)} unique jobs")
    print(f"Inserted {inserted} new jobs")
    print("By source:", by_source)
    print("By query family:", by_family)
    print(f"Average confidence: {avg_conf}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape and catalog drone/UAV jobs")
    parser.add_argument("--reset", action="store_true", help="Clear existing jobs before scraping")
    parser.add_argument(
        "--sources",
        type=str,
        default="",
        help="Comma-separated source list (e.g. greenhouse,jobbank)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Run scraper and print summaries without inserting into the database",
    )
    args = parser.parse_args()
    run(reset=args.reset, sources=parse_sources(args.sources), no_write=args.no_write)
