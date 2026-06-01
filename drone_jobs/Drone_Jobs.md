# Drone Jobs Scraper Operations

Objective: refresh the drone jobs dataset consumed by JobBoard.html.



## Pipeline Overview

The refresh flow is:

1. drone_jobs/scraper.py collects and classifies jobs into data/jobs.db.
2. drone_jobs/export.py exports data/jobs.json and review CSV files.
3. JobBoard.html fetches data/jobs.json and displays the most recent listing set.

Primary run command already available at repository root:

- UpdateJobsBoard.cmd

This command runs scraper.py, then export.py, and refreshes:

- data/jobs.db
- data/jobs.json
- data/jobs_review.csv

Scrape run summary log (append-only):

- assets/logs/jobs_scraper_runs.log
  - Each run appends timestamp, mode, sources, collected, deduped, duplicates_removed, duplicate_ratio, inserted, avg_conf, by_source, and by_family.

## Manual Refresh

From repository root:

```powershell
.\UpdateJobsBoard.cmd --reset
```

Useful options:

- Preview scrape only (no database writes):

```powershell
python .\drone_jobs\scraper.py --no-write
```

- Source-limited run:

```powershell
python .\drone_jobs\scraper.py --reset --sources jobbank,greenhouse,lever
python .\drone_jobs\export.py
```

## Daily Schedule (Windows Task Scheduler)

### Files added for scheduling

- drone_jobs/run_jobs_refresh_daily.cmd
  - Executes UpdateJobsBoard.cmd and writes logs to assets/logs/jobs_refresh_daily.log.
- drone_jobs/register_daily_jobs_task.ps1
  - Registers/updates a daily task for the current user.
- drone_jobs/unregister_daily_jobs_task.ps1
  - Removes the scheduled task.

### Register daily run

Default schedule is 06:15 local time.

```powershell
powershell -ExecutionPolicy Bypass -File .\drone_jobs\register_daily_jobs_task.ps1
```

Set a custom time and task name:

```powershell
powershell -ExecutionPolicy Bypass -File .\drone_jobs\register_daily_jobs_task.ps1 -TaskName "DroneSOP-DailyJobsRefresh" -Time "07:30"
```

Remove the schedule:

```powershell
powershell -ExecutionPolicy Bypass -File .\drone_jobs\unregister_daily_jobs_task.ps1 -TaskName "DroneSOP-DailyJobsRefresh"
```

## Integration Notes (JobBoard)

JobBoard.html reads data/jobs.json with cache bypass:

- fetch("data/jobs.json", { cache: "no-store" })

The refresh stamp shown on the page is based on the Last-Modified response header for data/jobs.json.

After a scheduled run, open JobBoard.html and verify:

1. Job count updates.
2. Refresh stamp date changes.
3. Source counts and filters still behave as expected.

## Version Control Workflow

Recommended lightweight workflow:

1. Create a branch for pipeline or scoring changes.
2. Run UpdateJobsBoard.cmd --reset.
3. Review data changes in:
   - data/jobs.json
   - data/jobs_review.csv
4. Spot-check JobBoard.html rendering.
5. Commit code and data updates together when intended.

Suggested commit split:

- Commit A: scraper/config/export code changes.
- Commit B: regenerated data outputs (if you want deterministic review of data delta).

## Troubleshooting

- Python runtime not found:
  - UpdateJobsBoard.cmd checks .venv first, then py launcher, then python in PATH.
- jobs_review.csv locked by another program:
  - export.py writes fallback output to data/jobs_review_latest.csv.
- No jobs on board:
  - Run a source-limited scrape to verify availability.
  - Check scraper output for HTTP blocks (for example anti-bot responses).
