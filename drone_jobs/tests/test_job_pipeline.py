import json
import sqlite3
from pathlib import Path

from drone_jobs.scraper import write_daily_summary_report

ROOT = Path(__file__).resolve().parents[1]


def test_exports_match_database_count():
    db_path = ROOT.parent / 'data' / 'jobs.db'
    json_path = ROOT.parent / 'data' / 'jobs.json'

    if not db_path.exists() or not json_path.exists():
        raise AssertionError('Expected generated job artifacts to exist')

    conn = sqlite3.connect(str(db_path))
    try:
        db_count = conn.execute('select count(*) from jobs').fetchone()[0]
    finally:
        conn.close()

    with json_path.open(encoding='utf-8') as handle:
        jobs = json.load(handle)

    assert len(jobs) == db_count


def test_write_daily_summary_report(tmp_path):
    output_path = tmp_path / 'daily_summary.json'
    report = write_daily_summary_report({
        'timestamp': '2026-08-08T00:00:00+00:00',
        'mode': 'write',
        'selected_sources': ['simplyhired', 'greenhouse'],
        'total_jobs': 2,
        'collected_count': 4,
        'deduped_count': 2,
        'inserted_count': 2,
        'by_source': {'simplyhired': 1, 'greenhouse': 1},
        'by_query_family': {'operations': 2},
        'average_confidence': 0.9,
        'confidence_min': 0.8,
        'confidence_max': 0.95,
    }, output_path=output_path)

    assert output_path.exists()
    assert report['total_jobs'] == 2
    assert report['by_source']['simplyhired'] == 1
    assert report['by_query_family']['operations'] == 2


def _isolated_db(tmp_path, monkeypatch):
    from drone_jobs import database
    monkeypatch.setattr(database, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(database, 'JOBS_DB_PATH', tmp_path / 'jobs.db')
    database.init_db()
    return database


def _seed(database, source, link, age_days):
    conn = database._connect()
    conn.execute(
        "INSERT INTO jobs (title, company, location, link, category, type, source, last_seen) "
        "VALUES ('t', 'c', 'l', ?, 'g', 'u', ?, datetime('now', ?))",
        (link, source, f'-{age_days} days'),
    )
    conn.commit()
    conn.close()


def _count(database):
    conn = database._connect()
    try:
        return conn.execute('select count(*) from jobs').fetchone()[0]
    finally:
        conn.close()


def test_expire_only_touches_requested_sources(tmp_path, monkeypatch):
    database = _isolated_db(tmp_path, monkeypatch)
    _seed(database, 'simplyhired', 'a', 30)
    _seed(database, 'lever', 'b', 30)

    assert database.expire_stale_jobs(14, []) == 0
    assert database.expire_stale_jobs(14, ['lever']) == 1
    assert _count(database) == 1


def test_clear_jobs_scoped_to_sources(tmp_path, monkeypatch):
    database = _isolated_db(tmp_path, monkeypatch)
    _seed(database, 'simplyhired', 'a', 0)
    _seed(database, 'lever', 'b', 0)

    database.clear_jobs(['lever'])
    assert _count(database) == 1


def test_source_health_ignores_404_and_flags_blocked_hosts(monkeypatch):
    from drone_jobs import scraper
    monkeypatch.setattr(scraper, 'HOST_STATS', {
        'www.simplyhired.ca': {'ok': 0, 'failed': 21},
        'boards-api.greenhouse.io': {'ok': 1, 'failed': 0},
    })
    assert not scraper.source_is_healthy('simplyhired')
    assert scraper.source_is_healthy('greenhouse')
    assert not scraper.source_is_healthy('talent')


def test_fetch_url_retries_429_then_succeeds(monkeypatch):
    from drone_jobs import scraper

    class Resp:
        def __init__(self, status):
            self.status_code = status
            self.headers = {'Retry-After': '1'}

        def raise_for_status(self):
            if self.status_code >= 400:
                import requests
                raise requests.HTTPError(response=self)

    responses = iter([Resp(429), Resp(200)])
    monkeypatch.setattr(scraper.requests, 'get', lambda *a, **k: next(responses))
    monkeypatch.setattr(scraper.time, 'sleep', lambda s: None)
    monkeypatch.setattr(scraper, 'HOST_STATS', {})
    monkeypatch.setattr(scraper, '_response_cache', {})

    assert scraper.fetch_url('https://example.test/x').status_code == 200
