# Stage 5 - Paper Trading
## Objective
- Provide realistic paper trading executor for strategy validation and plug into run_bot/offline_loop.

## Current State
- bot/trading/paper_trader.py simulates async latency/fees and tracks position/pnl; DecisionEngine drives it in run_bot/offline_loop.
- trading/executor.py, hedging.py, order_manager.py, position_manager.py, risk_engine.py are empty placeholders; no persistence of trades; no slippage model or risk controls beyond DecisionEngine.

## Missing Modules
- Central order routing abstraction for paper/live parity; slippage/latency controls; audit trail saving to storage.
- Risk checks per order (max position, daily loss) and PnL tracking per symbol.
- Reporting hooks for monitoring/alerts.

## Modules To Update
- bot/trading/paper_trader.py, executor.py, order_manager.py, position_manager.py, risk_engine.py, hedging.py.
- bot/engine/decision_engine.py (size fields) and bot/run_bot.py integration.
- Data persistence via DataManager/storage.

## Tasks
1) Create/update:
- Implement trading/executor.py to route decisions to PaperTrader in paper mode and stub live executor for later stages; include async queueing.
- Implement order_manager.py and position_manager.py for stateful tracking (positions, average price, realized/unrealized PnL).
- Extend paper_trader.py with slippage model, fee config, and ability to persist trades to data/trades or storage.
- Add risk_engine.py with guardrails (max_daily_loss, position caps) consistent with config.risk; integrate hedging stub if needed.
2) Implement logic:
- Ensure decisions carry size/sl/tp; executor honors close/open transitions and logs audit trail.
- Expose summary/report method used by monitoring; integrate with DataManager to store trades.
- Keep compatibility with offline_loop and run_bot event loop.
3) Config:
- settings.yaml: paper trading parameters (fees, slippage, max position, latency) and reporting toggles.

## Tests
Run:
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Verification Tasks
- Paper trading log shows opens/closes with fees and PnL; summary prints non-zero trades.
- RiskEngine prevents trades when limits breached and reports reason.
- Executor handles close -> open transitions without position drift.

## Expected Output
- Full paper execution stack mirroring live interfaces with persisted trade logs.
- Accurate PnL and position tracking ready for backtester and monitoring stages.

## Acceptance Criteria
- Decisions routed through executor/risk_engine before PaperTrader; violations are blocked.
- Trade history saved to storage or data/trades; summaries consistent with actions.
- offline_loop and run_bot run without executor errors.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 5 completed"
git push origin main
```
