
import sqlite3

try:
    from .config import DATA_DIR, JOBS_DB_PATH
except ImportError:  # pragma: no cover - script execution fallback
    from config import DATA_DIR, JOBS_DB_PATH


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(JOBS_DB_PATH))


def _ensure_column(cursor, table_name, column_name, ddl):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing = {row[1] for row in cursor.fetchall()}
    if column_name not in existing:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")

def init_db():
    conn = _connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        link TEXT UNIQUE,
        description TEXT,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    _ensure_column(c, "jobs", "description", "description TEXT")
    _ensure_column(c, "jobs", "summary", "summary TEXT")
    _ensure_column(c, "jobs", "date_posted", "date_posted TEXT")
    _ensure_column(c, "jobs", "date_expires", "date_expires TEXT")
    _ensure_column(c, "jobs", "query_family", "query_family TEXT DEFAULT ''")
    _ensure_column(c, "jobs", "matched_query", "matched_query TEXT DEFAULT ''")
    _ensure_column(c, "jobs", "confidence", "confidence REAL DEFAULT 0")
    _ensure_column(c, "jobs", "match_reason", "match_reason TEXT DEFAULT ''")
    _ensure_column(c, "jobs", "last_seen", "last_seen TIMESTAMP")
    # Backfill so existing rows aren't immediately eligible for expiry.
    c.execute("UPDATE jobs SET last_seen = CURRENT_TIMESTAMP WHERE last_seen IS NULL")

    conn.commit()
    conn.close()


def clear_jobs():
    conn = _connect()
    c = conn.cursor()
    c.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()


def expire_stale_jobs(days: int) -> int:
    conn = _connect()
    c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE last_seen < datetime('now', ?)", (f"-{days} days",))
    count = c.rowcount
    conn.commit()
    conn.close()
    return count


def insert_job(job):
    conn = _connect()
    c = conn.cursor()

    c.execute("""
    INSERT OR IGNORE INTO jobs
    (title, company, location, link, description, summary, date_posted, date_expires,
     category, type, source, query_family, matched_query, confidence, match_reason)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job["title"],
        job["company"],
        job["location"],
        job["link"],
        job.get("description", ""),
        job.get("summary", ""),
        job.get("date_posted", ""),
        job.get("date_expires", ""),
        job["category"],
        job["type"],
        job["source"],
        job.get("query_family", ""),
        job.get("matched_query", ""),
        job.get("confidence", 0),
        job.get("match_reason", ""),
    ))
    was_inserted = c.rowcount

    # Refresh last_seen on re-encounter; promote score/summary if confidence improved.
    new_conf = job.get("confidence", 0)
    c.execute("""
    UPDATE jobs SET
        last_seen = CURRENT_TIMESTAMP,
        confidence = CASE WHEN ? > confidence THEN ? ELSE confidence END,
        summary = CASE WHEN ? > confidence THEN ? ELSE summary END,
        match_reason = CASE WHEN ? > confidence THEN ? ELSE match_reason END
    WHERE link = ?
    """, (new_conf, new_conf, new_conf, job.get("summary", ""), new_conf, job.get("match_reason", ""), job["link"]))

    conn.commit()
    conn.close()
    return was_inserted