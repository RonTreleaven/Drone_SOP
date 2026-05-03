QUERY_FAMILIES = {
    "operations": [
        "drone pilot",
        "uav operator",
        "rpas pilot",
        "remote pilot",
        "uas operator",
    ],
    "mapping": [
        "drone survey",
        "photogrammetry drone",
        "lidar drone",
        "geospatial drone",
        "uav mapping",
    ],
    "inspection": [
        "drone inspection",
        "uav inspection",
        "powerline drone inspection",
        "infrastructure drone",
    ],
    "media": [
        "drone videographer",
        "aerial photographer",
        "drone photographer",
    ],
    "technical": [
        "uav operations coordinator",
        "rpas platform engineer",
        "drone field engineer",
        "uas field engineer",
    ],
}

# Hard title exclusions for recurring false positives.
EXCLUDED_TITLE_PHRASES = [
    "drone technician",
]

# Title must include one of these role terms to be considered a strong fit.
# Intentionally excludes generic "technician" to reduce off-target matches.
REQUIRED_ROLE_TERMS_IN_TITLE = [
    "pilot",
    "operator",
    "inspection",
    "inspector",
    "survey",
    "surveyor",
    "photographer",
    "videographer",
    "engineer",
    "specialist",
]

# Flattened list kept for compatibility with any existing imports.
QUERIES = [query for family in QUERY_FAMILIES.values() for query in family]

INDEED_RSS = "https://ca.indeed.com/rss?q={query}&l=Canada"
JOBBANK_SEARCH = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={query}&locationstring=Canada"
SIMPLYHIRED_SEARCH = "https://www.simplyhired.ca/search?q={query}"
TALENT_SEARCH = "https://ca.talent.com/jobs?k={query}&l=Canada"
JOBS_BEAR_SEARCH = "https://ca.jobs-bear.co/jobs?search={query}"

# Greenhouse ATS boards to ingest from. Update this list as needed.
GREENHOUSE_JOBS_API = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
GREENHOUSE_BOARDS = {
    "wing": "Wing",
    "zipline": "Zipline",
    "skydio": "Skydio",
}

# Lever ATS sites to ingest from. Keys are site IDs used by Lever API.
LEVER_POSTINGS_API = "https://api.lever.co/v0/postings/{site}?mode=json"
LEVER_SITES = {
    "shieldai": "Shield AI",
    "aero": "Aero",
}

# Workopolis is currently blocked by anti-bot protection for Python requests from this environment.
