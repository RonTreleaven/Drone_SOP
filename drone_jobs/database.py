
import sqlite3


def _ensure_column(cursor, table_name, column_name, ddl):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing = {row[1] for row in cursor.fetchall()}
    if column_name not in existing:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")

def init_db():
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        link TEXT UNIQUE,
        summary TEXT,
        date_posted TEXT,
        date_expires TEXT,
        category TEXT,
        type TEXT,
        source TEXT,
        query_family TEXT DEFAULT '',
        matched_query TEXT DEFAULT '',
        confidence REAL DEFAULT 0,
        match_reason TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    _ensure_column(c, "jobs", "summary", "summary TEXT")
    _ensure_column(c, "jobs", "date_posted", "date_posted TEXT")
    _ensure_column(c, "jobs", "date_expires", "date_expires TEXT")
    _ensure_column(c, "jobs", "query_family", "query_family TEXT DEFAULT ''")
    _ensure_column(c, "jobs", "matched_query", "matched_query TEXT DEFAULT ''")
    _ensure_column(c, "jobs", "confidence", "confidence REAL DEFAULT 0")
    _ensure_column(c, "jobs", "match_reason", "match_reason TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def clear_jobs():
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()


def insert_job(job):
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO jobs (title, company, location, link, summary, date_posted, date_expires, category, type, source, query_family, matched_query, confidence, match_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job["title"],
            job["company"],
            job["location"],
            job["link"],
            job.get("summary", ""),
            job.get("date_posted", ""),
            job.get("date_expires", ""),
            job["category"],
            job["type"],
            job["source"],
            job.get("query_family", ""),
            job.get("matched_query", ""),
            job.get("confidence", 0),
            job.get("match_reason", "")
        ))
        conn.commit()
        return 1
    except sqlite3.IntegrityError:
        # Duplicate link, skip without failing the run.
        return 0
    finally:
        conn.close()

    return 0