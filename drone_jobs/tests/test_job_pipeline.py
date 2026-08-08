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
