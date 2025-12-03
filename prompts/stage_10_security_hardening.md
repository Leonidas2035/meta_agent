# Stage 10 - Security Hardening
## Objective
- Secure credentials, configs, and runtime safety for live deployment.

## Current State
- config/settings.yaml holds endpoints and flags; secrets are not loaded from env or masked; .gitignore minimal; installer scripts exist but not hardened.

## Missing Modules
- .env example and loader for API keys; secret masking in logs; permission checks on storage.
- Input validation for external data; dependency locking; security scan guidance.

## Modules To Update
- bot/core/config_loader.py to load env vars, validate required keys in live mode, and mask sensitive values.
- Update .gitignore and add .env.example/SECURITY.md if needed; ensure storage permissions.
- Apply guards across market_data/trading/ai modules for timeouts and retries.

## Tasks
1) Create/update:
- Enhance config_loader to merge env overrides, validate required keys when app.mode=live, and refuse unsafe start.
- Add secret redaction helpers for logging/alerts; avoid writing API keys to storage or stdout.
- Pin dependencies in requirements.txt and document security checks.
2) Implement logic:
- Add input validation for websocket/REST payloads and symbol whitelist; enforce request timeouts and recv_window limits.
- Provide operator checklist (e.g., SECURITY.md or README section) covering keys, permissions, and network settings.
3) Config:
- settings.yaml: security block (allowed_symbols, max_notional, request_timeout, signed_request_window) and env var names for keys.

## Tests
Run:
```
python -m bot.run_bot
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
```
Optional: run any available static/secret scan tools.

## Verification Tasks
- App fails fast if live mode without required API keys; secrets are not logged.
- Requests time out gracefully; invalid payloads rejected.
- git status shows no secret files tracked.

## Expected Output
- Hardened config loader and redaction utilities with documented security posture.
- Security defaults preventing accidental live trading or secret leakage.
- Guidance for operators before enabling live mode.

## Acceptance Criteria
- Live mode requires env keys; paper/mock unaffected.
- Logs/alerts contain no sensitive data; secrets masked consistently.
- Tests complete without security violations or leaks.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 10 completed"
git push origin main
```
