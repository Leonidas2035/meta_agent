# Stage 9 - Monitoring and Alerts
## Objective
- Add observability: structured logging, metrics, and alerts for pipeline health.

## Current State
- Logging is print-based; no metrics or alerting; config.log_level present; DataManager writes files but not monitored; no health checks.

## Missing Modules
- Central logging/metrics module; alert sinks (Slack/email/Telegram) with throttling.
- Health checks for websocket ingestion, model freshness, PnL/risk breaches.
- Dashboards or log files for offline analysis.

## Modules To Update
- New bot/monitoring/ module (logger.py, alerts.py, health.py).
- Integrations in ws_manager, DataManager, DecisionEngine, PaperTrader, LLMRiskModerator, backtester, run_bot.
- config/settings.yaml for alert endpoints and thresholds.

## Tasks
1) Create/update:
- Structured logger writing to storage/logs (JSONL) with context (symbol, stage, decision, latency).
- alerts.py to send notifications (or mock) with rate limiting; sinks configured via env/webhooks.
- health.py to compute liveness for websocket, data freshness, model timestamps, PnL drawdown.
- Wire run_bot/offline_loop/backtester to emit metrics and call alerts on thresholds.
2) Implement logic:
- Provide command to run health once: `python -m bot.monitoring.health --once` and optionally watch mode.
- Ensure monitoring uses safe defaults in offline/mock (no external calls unless configured).
- Expose hooks for GUI Launcher to display status.
3) Config:
- Add monitoring thresholds (max stale ms, max drawdown), alert webhooks, log rotation settings.

## Tests
Run:
```
python -m bot.run_bot
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.monitoring.health --once
```

## Verification Tasks
- Logs written to storage/logs with structured fields; alert mock prints when thresholds crossed.
- Health check reports OK for running components or actionable warnings.
- No unhandled exceptions when alert endpoints unset.

## Expected Output
- Observability layer with metrics/logs/alerts for bot lifecycle.
- Health check CLI for automation pipelines.
- Hooks for GUI launcher and monitoring dashboards.

## Acceptance Criteria
- Monitoring code runs in mock/paper modes without network calls unless configured.
- Alerts trigger on threshold violations during tests.
- run_bot/offline_loop complete while emitting logs.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 9 completed"
git push origin main
```
