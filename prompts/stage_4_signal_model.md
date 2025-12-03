# Stage 4 - Signal Model and Decision Engine
## Objective
- Deliver robust inference combining XGBoost outputs, ensemble weighting, and deterministic decision logic.

## Current State
- SignalModel wraps XGBClassifier loading from storage/models; EnsembleSignalModel aggregates horizons with fixed weights and simple filter_blocks; OnlineFeatureBuilder feeds features; DecisionEngine applies min_confidence/min_edge thresholds; run_bot wires these with LLMRiskModerator and PaperTrader.
- Missing calibration, logging, and graceful fallback when models are absent; stop_loss/take_profit sizing not wired; limited error handling.

## Missing Modules
- Probability calibration/smoothing and model warmup checks; fallback to hold when models missing.
- Telemetry for per-horizon outputs and meta_edge; optional threshold auto-tuning.
- Unit tests for inference path and filter_blocks.

## Modules To Update
- bot/ml/signal_model/model.py, ensemble.py, online_features.py, dataset_builder.py (for calibration metadata).
- bot/engine/decision_engine.py to support sl/tp sizing; bot/run_bot.py and bot/sandbox/offline_loop.py for decision propagation.
- config/settings.yaml for thresholds/weights.

## Tasks
1) Create/update:
- Add calibration (Platt/temperature) saved in manifest and loaded in SignalModel.predict_proba.
- Expand EnsembleSignalModel to log horizon outputs, handle missing models gracefully, and read weights from config.
- Enhance DecisionEngine to support sl/tp, position sizing via RiskParams, and incorporate LLMRiskModerator verdict.
- Update run_bot/offline_loop to print meta_edge/stats and propagate decision fields to PaperTrader/executors.
2) Implement logic:
- Ensure filter_blocks uses FEATURE_COLS indices reliably; add tests.
- Provide fallback to hold when model or features invalid; avoid hard crashes.
- Keep integration with ws_manager/DataManager event schema intact.
3) Config:
- Add decision thresholds, ensemble weights, calibration flags in settings.yaml.

## Tests
Run:
```
python -m bot.ml.signal_model.train --symbol BTCUSDT --horizon 1 --min-rows 200
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Verification Tasks
- Ensemble prints horizon edges/meta_edge; DecisionEngine returns actions with size/sl/tp populated.
- No crashes when model file missing; logs show skip with warning.
- Offline loop reaches trading summary with non-zero trades.

## Expected Output
- Stable inference/decision layer with calibrated probabilities and configurable thresholds.
- Logging that exposes per-horizon contributions and approvals from LLMRiskModerator.
- Decisions consumable by PaperTrader and live executors.

## Acceptance Criteria
- SignalModel/Ensemble load successfully and return SignalOutput without shape errors.
- DecisionEngine respects min_edge/min_confidence and integrates LLM approvals.
- offline_loop and run_bot complete without inference exceptions.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 4 completed"
git push origin main
```
