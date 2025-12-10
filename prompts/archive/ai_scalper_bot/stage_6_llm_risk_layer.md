# Stage 6 - LLM Risk Layer
## Objective
- Integrate LLM-based risk moderation with deterministic fallbacks for live and paper trading.

## Current State
- bot/ai/risk_moderator.py implements heuristic caching and prompt template; config settings include llm options but disabled; run_bot calls evaluate when llm_enabled; ai_llm/*.py placeholders empty.
- No actual LLM client/prompt builder/cache persistence; no unit tests or observability.

## Missing Modules
- ai_llm.llm_client.py to call config.ai.api_url/model/key with timeouts/retries.
- ai_llm.llm_prompt_builder.py to assemble market context + signal + feature tail.
- ai_llm.llm_cache.py for persistent memoization and offline mode.
- Telemetry and safety filters for responses.

## Modules To Update
- bot/ai/risk_moderator.py to call new client with fallback heuristics and structured validation.
- bot/run_bot.py to surface risk decisions; config/settings.yaml for llm tuning and cache settings.
- Add tests/mocks for offline use.

## Tasks
1) Create/update:
- Implement ai_llm/llm_client.py with async HTTP calls, api key from env/config, timeout/retry, and mock mode.
- Implement ai_llm/llm_prompt_builder.py assembling prompt from features, SignalOutput, market context aligned with LLMRiskModerator.
- Implement ai_llm/llm_cache.py for TTL cache on disk (storage/llm_cache.json) plus in-memory.
- Extend risk_moderator.py to select between heuristic and LLM, validate JSON, and cap latency.
2) Implement logic:
- Provide deterministic mock response when llm_enabled=false or network absent; default to hold on errors.
- Add structured logging of approve/risk_score/reason and how it affects DecisionEngine/PaperTrader.
- Keep integration with ws_manager/DataManager event schema intact.
3) Config:
- settings.yaml: llm_enabled, llm_model, temperature, max_tokens, timeout, cache_ttl, mock_mode flags.

## Tests
Run:
```
python -m bot.run_bot
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
```
(Enable llm_enabled true or mock mode for smoke test.)

## Verification Tasks
- risk_moderator.evaluate returns JSON with approve/risk_score/reason consistently.
- run_bot logs LLM approvals/blocks and continues trading loop.
- Errors/timeouts fall back to heuristic without crashing event loop.

## Expected Output
- Functional LLM risk layer with mock and live modes plus cached responses.
- Clear interface for DecisionEngine to consume approvals.
- Configurable and observable risk moderation.

## Acceptance Criteria
- No unhandled exceptions when LLM unavailable; approvals deterministic in mock mode.
- Config toggles switch between heuristic and live LLM.
- run_bot/offline_loop complete with LLM checks engaged.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 6 completed"
git push origin main
```
