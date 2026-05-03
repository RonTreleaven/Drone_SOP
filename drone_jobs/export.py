import sqlite3
import json
import csv
from datetime import datetime, timedelta, timezone

from normalization import normalize_date, normalize_text, parse_date_value


def parse_iso_date(value):
    return parse_date_value(value)


def is_possibly_stale(date_posted, date_expires):
    now = datetime.now(timezone.utc)
    posted = parse_iso_date(date_posted)
    expires = parse_iso_date(date_expires)

    if posted and posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires and expires < now:
        return "expired"
    if posted and posted < (now - timedelta(days=45)):
        return "old"
    return ""


def fetch_jobs():
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    c.execute(
        """
         SELECT title, company, location, link, summary, date_posted, date_expires,
             category, type, source, query_family, matched_query, confidence, match_reason
        FROM jobs
        ORDER BY confidence DESC, created_at DESC
        """
    )
    rows = c.fetchall()
    conn.close()

    jobs = []
    for r in rows:
        jobs.append({
            "title": normalize_text(r[0]),
            "company": normalize_text(r[1]),
            "location": normalize_text(r[2]),
            "link": r[3],
            "summary": normalize_text(r[4]),
            "date_posted": normalize_date(r[5]),
            "date_expires": normalize_date(r[6]),
            "category": normalize_text(r[7]),
            "type": normalize_text(r[8]),
            "source": normalize_text(r[9]),
            "query_family": normalize_text(r[10]),
            "matched_query": normalize_text(r[11]),
            "confidence": r[12],
            "match_reason": normalize_text(r[13]),
        })

    return jobs

def export_json():
    jobs = fetch_jobs()

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def load_existing_reviews(path):
    existing = {}
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                link = row.get("link", "").strip()
                if link:
                    existing[link] = row
    except FileNotFoundError:
        pass
    return existing


def export_review_csv():
    jobs = fetch_jobs()
    output = "jobs_review.csv"
    existing = load_existing_reviews(output)

    review_fields = [
        "qualification",
        "interest_level",
        "review_rank",
        "review_comments",
        "next_action",
        "last_reviewed",
    ]
    headers = [
        "title",
        "company",
        "location",
        "source",
        "query_family",
        "matched_query",
        "date_posted",
        "date_expires",
        "stale_hint",
        "category",
        "type",
        "confidence",
        "match_reason",
        "summary",
        "link",
    ] + review_fields

    defaults = {
        "qualification": "unreviewed",
        "interest_level": "unknown",
        "review_rank": "",
        "review_comments": "",
        "next_action": "",
        "last_reviewed": "",
    }

    rows = []
    for job in jobs:
        row = {k: job.get(k, "") for k in headers if k not in review_fields}
        row["stale_hint"] = is_possibly_stale(job.get("date_posted", ""), job.get("date_expires", ""))
        prior = existing.get(job.get("link", ""), {})
        for field in review_fields:
            row[field] = prior.get(field, defaults[field])
        rows.append(row)

    try:
        with open(output, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
    except PermissionError:
        fallback_output = "jobs_review_latest.csv"
        with open(fallback_output, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Could not write {output} (file may be open). Wrote {fallback_output} instead.")


def run_exports():
    export_json()
    export_review_csv()


if __name__ == "__main__":
    run_exports()
    