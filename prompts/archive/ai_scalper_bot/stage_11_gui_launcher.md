# Stage 11 - GUI Launcher
## Objective
- Provide a lightweight GUI/TUI to start/stop ai_scalper_bot modes and display status.

## Current State
- Launch happens via CLI scripts (run_bot.py, start_bot.cmd, run_bot.exe); no UI; monitoring data not exposed.

## Missing Modules
- GUI or TUI wrapping run_bot/offline_loop/backtester with mode selection and status panels.
- Integration with monitoring metrics and DataManager paths.

## Modules To Update
- New module bot/gui/launcher.py (or similar) plus assets; update build scripts if needed.
- Hooks to run_bot main entry, offline_loop, backtester, monitoring health checks.

## Tasks
1) Create/update:
- Build GUI/TUI with controls: select mode (offline/paper/live), pick symbol, set data path, start/stop process threads.
- Display stats (connection status, last tick, position, pnl) by reading monitoring/summary outputs.
- Provide buttons to open config/settings.yaml, run health checks, and view logs in storage/logs.
- Add confirmation prompts before live mode; default to mock websocket.
2) Implement logic:
- Use subprocess or asyncio to start run_bot/offline_loop/backtester; handle termination gracefully and prevent orphaned processes.
- Ensure GUI code reuses existing modules rather than duplicating trading logic; keep dependencies minimal.
- Connect monitoring hooks for status updates.
3) Config:
- Optional gui settings (theme, default paths) in settings.yaml.

## Tests
Run:
```
python -m bot.gui.launcher
```
Manual interactions: start offline_loop with synthetic ticks, view stats, stop cleanly.

## Verification Tasks
- GUI launches without missing asset errors; controls trigger correct commands.
- Starting/stopping bot does not orphan processes; logs visible from storage/logs.
- Mode switches update configuration or pass args accordingly.

## Expected Output
- Usable launcher for non-CLI operators to run offline/paper/live modes.
- Status visibility backed by monitoring layer.
- Safe guardrails around live actions.

## Acceptance Criteria
- GUI functions on Windows with current dependencies.
- Mock/offline runs start and stop cleanly through the UI.
- No additional runtime errors introduced to bot modules.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 11 completed"
git push origin main
```
