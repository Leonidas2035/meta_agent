# Stage 2 - Feature Engine
## Objective
- Build deterministic feature generation that matches offline datasets and live streaming for ai_scalper_bot.

## Current State
- bot/indicators/feature_builder.py computes OHLCV, RSI, ATR, VWAP, orderflow, and orderbook imbalance from DataManager artifacts; contains minimal validation and mixed comments.
- Indicator helpers exist (ohlcv_indicators.py, orderflow.py, volatility.py); OnlineFeatureBuilder (bot/ml/signal_model/online_features.py) streams FEATURE_COLS; DatasetBuilder defines FEATURE_COLS and builds offline matrices from data/ticks CSVs.
- run_bot and offline_loop use OnlineFeatureBuilder; FeatureBuilder not wired into training; no shared schema contract.

## Missing Modules
- Central feature registry and schema validation between feature_builder, OnlineFeatureBuilder, and DatasetBuilder.
- Normalization/standardization artifacts persisted with datasets; feature caching for reuse.
- Tests/fixtures for feature edge cases and NaN handling.

## Modules To Update
- bot/indicators/feature_builder.py and indicator utilities for robustness.
- bot/ml/signal_model/online_features.py and dataset_builder.py to ensure identical ordering/scaling.
- config/settings.yaml feature toggles and windows; documentation for ws_manager/DataManager integration.

## Tasks
1) Create/update:
- Refactor feature_builder to return ordered dict/np.ndarray aligned with FEATURE_COLS; remove noise comments, add validation and fallback defaults.
- Update OnlineFeatureBuilder to guard against underflow, clip extremes, and expose feature names; ensure consistent shapes with DatasetBuilder.
- Extend DatasetBuilder to ingest precomputed features (from feature_builder) and persist scaler parameters; add CLI for profiling (`python -m bot.ml.signal_model.dataset_builder --profile`).
- Add lightweight feature tests (e.g., in test_features.py) to assert no NaN/inf and correct length.
2) Implement logic:
- Ensure compatibility with ws_manager/DataManager schema; handle side/buy-sell orientation consistently.
- Add optional normalization (z-score/min-max) with saved params under storage/datasets.
- Document feature mapping for SignalModel.predict_proba and EnsembleSignalModel.filter_blocks.
3) Config:
- settings.yaml: feature windows, normalization flag, minimum ticks per build.

## Tests
Run:
```
python -m bot.sandbox.generate_synthetic_ticks
python -m bot.ml.signal_model.dataset_builder --symbol BTCUSDT --horizon 1 --profile
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Verification Tasks
- FEATURE_COLS identical across dataset_builder and online_features; feature vector length matches model expectations.
- FeatureBuilder returns deterministic values for same input; NaN/inf replaced with safe defaults.
- offline_loop produces trades without feature-related exceptions.

## Expected Output
- Unified, documented feature schema for offline and online use.
- Persisted feature datasets/scalers under storage/datasets ready for ML training.
- Smoke tests demonstrating feature health on synthetic ticks.

## Acceptance Criteria
- Feature generation passes tests and delivers non-empty vectors when ticks exist.
- Models trained in later stages can consume both offline and streaming features without mismatches.
- run_bot and offline_loop operate with configured feature settings.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 2 completed"
git push origin main
```
