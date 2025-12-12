# Meta-Agent Runbook (multi-project + off-market)

- Configure projects in config/projects.yaml (default ai_scalper_bot, supervisor_agent, meta_agent).
- GUI: select project, enter task name & body, click Add; stage saved with project field.
- CLI helpers:
  - python meta_agent.py --list-projects
  - python meta_agent.py --project-id supervisor_agent (override project for stage run)

## Off-Market / Supervisor Maintenance
- Schedule config: config/offmarket_schedule.yaml (UTC window, day allow list, max_runs_per_day, require_bot_idle, backlog limits).
- State file: state/offmarket_state.json (last_run_utc, runs_today, last_run_result).
- Runner: offmarket_scheduler.py (one-shot) decides if maintenance should run, then calls supervisor_runner.run_supervisor_maintenance_once.
- Entry: python offmarket_runner.py (or call offmarket_scheduler.main from cron/Task Scheduler).
- Supervisor reports directory: eports/supervisor/ (used to build backlog). Logs: logs/offmarket_scheduler.log.
