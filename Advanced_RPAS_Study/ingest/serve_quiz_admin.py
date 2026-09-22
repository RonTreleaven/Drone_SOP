#!/usr/bin/env python3
"""Serve the Advanced RPAS quiz with a local admin write API.

Run from Advanced_RPAS_Study:

    python ingest/serve_quiz_admin.py

Then open:

    http://127.0.0.1:8765/quiz.html

The API is intentionally bound to localhost only. It lets quiz.html clear review
flags immediately during an admin review session while creating a questions.json
backup before each write.
"""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
QPATH = ROOT / "data" / "questions.json"
BACKUP_DIR = ROOT / "ingest" / "backups"
HOST = "127.0.0.1"
PORT = 8765


def load_questions():
    return json.loads(QPATH.read_text(encoding="utf-8-sig"))


def write_json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


class QuizAdminHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            data = load_questions()
            write_json_response(self, 200, {
                "ok": True,
                "mode": "local-admin",
                "root": str(ROOT),
                "questionCount": len(data.get("questions", [])),
                "updated": data.get("updated"),
            })
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/approve-review":
            write_json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = approve_review(payload)
            write_json_response(self, 200, result)
        except Exception as exc:
            write_json_response(self, 500, {"ok": False, "error": str(exc)})


def approve_review(payload):
    qid = payload.get("id")
    if not qid:
        raise ValueError("Missing id")

    cleared_flags = set(payload.get("clearedFlags") or [])
    reviewed_sets = set(payload.get("reviewedSets") or [])
    data = load_questions()
    questions = data.get("questions", [])
    question = next((q for q in questions if q.get("id") == qid), None)
    if not question:
        raise ValueError(f"Question id not found: {qid}")

    before_flags = list(question.get("reviewFlags") or [])
    after_flags = [flag for flag in before_flags if flag not in cleared_flags]
    removed_flags = [flag for flag in before_flags if flag in cleared_flags]
    if after_flags:
        question["reviewFlags"] = after_flags
    else:
        question.pop("reviewFlags", None)

    before_sets = set(question.get("reviewedSets") or [])
    after_sets = sorted(before_sets | reviewed_sets)
    if after_sets:
        question["reviewedSets"] = after_sets

    if removed_flags or reviewed_sets:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup = BACKUP_DIR / f"questions_before_local_review_{qid}_{stamp}.json"
        shutil.copy2(QPATH, backup)

        data["updated"] = date.today().isoformat()
        data["lastUpdated"] = date.today().isoformat()
        note = (
            f"{date.today().isoformat()} LOCAL QUIZ REVIEW: approved {qid}; "
            f"cleared flags {sorted(removed_flags)}; reviewed sets {sorted(reviewed_sets)}."
        )
        if note not in data.setdefault("migrationNotes", []):
            data["migrationNotes"].append(note)

        QPATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        backup_path = str(backup)
    else:
        backup_path = None

    return {
        "ok": True,
        "id": qid,
        "clearedFlags": removed_flags,
        "reviewedSets": sorted(reviewed_sets),
        "question": question,
        "backup": backup_path,
    }


def main():
    server = ThreadingHTTPServer((HOST, PORT), QuizAdminHandler)
    print(f"Serving Advanced RPAS quiz admin at http://{HOST}:{PORT}/quiz.html")
    print(f"Repo root: {ROOT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
