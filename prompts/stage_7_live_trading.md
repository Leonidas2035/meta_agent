# Stage 7 - Live Trading
## Objective
- Enable live trading mode with real exchange connectivity while preserving safety and compatibility with paper/backtesting flows.

## Current State
- ws_manager streams Binance data; binance_ws/bingx_ws empty; trading executor/order_manager/position_manager/risk_engine placeholders; config.app.mode defaults to paper; run_bot uses MockWSManager and PaperTrader.
- No REST client, auth, order placement, or futures handling; storage lacks live fills; offline_loop covers only paper.

## Missing Modules
- Exchange client wrappers (REST + authenticated WS) with signatures, rate limits, and testnet support.
- Live mode configuration and dry-run switches; safety guardrails and kill-switch.
- State persistence for open orders/positions and reconciliation with fills.

## Modules To Update
- bot/market_data/binance_ws.py/bingx_ws.py for authenticated streams and order/fill events.
- bot/trading/executor.py, order_manager.py, position_manager.py, risk_engine.py for live execution pipeline.
- bot/run_bot.py to branch on app.mode (paper/live) and select appropriate managers; config/settings.yaml for api keys and testnet flags.

## Tasks
1) Create/update:
- Build exchange REST client (new module e.g., bot/trading/exchange_client.py) supporting place/cancel/query for spot/futures with signatures and timeouts.
- Extend executor/order_manager/position_manager to maintain live state, reconcile with fills, and log to DataManager/storage.
- Add kill-switch and dry-run flags; integrate LLMRiskModerator and DecisionEngine before order placement.
- Update ws_manager/binance_ws to subscribe to user data streams when available and route fills to position manager.
2) Implement logic:
- Ensure live and paper share interface so run_bot/offline_loop codepaths align.
- Avoid real orders in test environments; require explicit config flag to send trades.
- Persist all live events (orders/fills/positions) to storage for monitoring and backtesting.
3) Config:
- settings.yaml: api keys, secret env var names, testnet flag, dry_run, max slippage per order.

## Tests
Run (dry-run/mock endpoints):
```
python -m bot.run_bot
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
```
If exchange sandbox keys available, add smoke test placing/cancelling 0-size test orders.

## Verification Tasks
- run_bot in live mode initializes executor and position manager without errors; logs show readiness but no real orders when dry-run.
- OrderManager updates positions and PnL when mock fills received.
- Kill-switch stops trading and closes positions when triggered.

## Expected Output
- Live-capable trading pipeline sharing interfaces with paper mode.
- Safe dry-run defaults with clear separation between mock and real orders.
- Persisted state for orders/fills/positions.

## Acceptance Criteria
- Live mode can start and run event loop without hitting NotImplemented paths.
- Order submissions are gated by risk checks and config flags.
- State sync (orders/positions) is consistent across restarts.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 7 completed"
git push origin main
```
