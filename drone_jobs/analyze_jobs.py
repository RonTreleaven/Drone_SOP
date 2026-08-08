import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'data' / 'jobs.db'
JSON_PATH = ROOT / 'data' / 'jobs.json'


def summarize():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        rows = conn.execute(
            'select title, company, location, source, query_family, matched_query, confidence, link from jobs order by created_at desc'
        ).fetchall()
    finally:
        conn.close()

    print(f'db_rows={len(rows)}')
    print('sources=' + json.dumps(Counter(r[3] for r in rows), sort_keys=True))
    print('query_families=' + json.dumps(Counter(r[4] for r in rows), sort_keys=True))
    print('confidence_min_max=' + json.dumps({'min': min((r[6] for r in rows), default=0), 'max': max((r[6] for r in rows), default=0)}))

    if JSON_PATH.exists():
        with JSON_PATH.open(encoding='utf-8') as handle:
            exported = json.load(handle)
        print(f'json_rows={len(exported)}')
        print('json_sources=' + json.dumps(Counter(j.get('source', '') for j in exported), sort_keys=True))

    if rows:
        print('sample=')
        for row in rows[:10]:
            print(' -', row[0], '|', row[1], '|', row[3], '|', row[6])


if __name__ == '__main__':
    summarize()
