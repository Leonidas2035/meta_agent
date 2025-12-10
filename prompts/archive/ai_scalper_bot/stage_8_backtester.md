# Stage 8 - Backtester
## Objective
- Provide a reproducible backtesting harness over recorded ticks and generated signals.

## Current State
- bot/backtester/* files are empty; bot/sandbox/offline_loop.py runs a simple loop using Ensemble + PaperTrader; DataManager saves ticks; generate_synthetic_ticks provides sample CSVs.
- No metrics beyond PaperTrader.summary; no scenario configs or visualization.

## Missing Modules
- Backtest simulator with event replay, slippage models, and portfolio accounting.
- Metrics module (win rate, expectancy, drawdown, Sharpe) and report generation.
- Configurable strategy params (thresholds, horizons) for sweeps and experiments.

## Modules To Update
- bot/backtester/backtest_model.py, metrics.py, simulator.py, tick_replay.py.
- bot/sandbox/offline_loop.py to reuse backtester components.
- storage/backtests/ for outputs.

## Tasks
1) Create/update:
- tick_replay.py to stream events from CSVs (data/ticks or storage/datasets) with configurable speed.
- simulator.py/backtest_model.py to run Ensemble/DecisionEngine/PaperTrader over replayed ticks, tracking equity curve and trades.
- metrics.py to compute PnL stats, drawdown, Sharpe/SQN, and export to JSON/CSV.
- CLI `python -m bot.backtester.simulator --ticks-path ... --symbol ...` plus report writer to storage/backtests.
2) Implement logic:
- Reuse FeatureBuilder/OnlineFeatureBuilder for feature generation; ensure filter_blocks applied.
- Allow parameter sweeps (min_confidence, min_edge, fees, slippage) via config or CLI args.
- Integrate LLMRiskModerator mock approvals to evaluate impact.
3) Config:
- settings.yaml: backtester options (replay_speed, slippage, output_dir) and default paths.

## Tests
Run:
```
python -m bot.backtester.simulator --ticks-path data/ticks/BTCUSDT_synthetic.csv --symbol BTCUSDT
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
```

## Verification Tasks
- Backtester outputs report under storage/backtests with summary metrics and trade log.
- Results comparable to PaperTrader summary for same settings.
- No crashes when dataset missing columns; graceful error messages.

## Expected Output
- Full backtesting reports and trade logs suitable for iteration.
- CLI to run replay/sweeps quickly on stored ticks.
- Reusable metrics for monitoring.

## Acceptance Criteria
- Backtester runs end-to-end on synthetic ticks producing metrics file.
- Parameter sweeps execute without manual code changes.
- Reports include trades, PnL, drawdown, Sharpe.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 8 completed"
git push origin main
```
