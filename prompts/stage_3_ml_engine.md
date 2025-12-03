# Stage 3 - ML Engine
## Objective
- Deliver a reproducible ML training pipeline for signal models using XGBoost with evaluation and metadata.

## Current State
- DatasetBuilder loads tick CSVs from data/ticks and offline fallback, computes FEATURE_COLS and binary targets.
- train.py trains XGBClassifier with fixed params and saves models to storage/models and datasets to storage/datasets.
- SignalModel loads models; EnsembleSignalModel aggregates horizons; run_bot/offline_loop rely on presence of models and features.
- No validation split, metadata logging, cross-validation, or dataset quality checks; no CLI for evaluation beyond training.

## Missing Modules
- Evaluation script with train/val split, metrics (logloss, AUC, precision/recall) and saved manifest.
- Model registry capturing horizons, params, feature list, and training timestamp.
- Data quality checks (class balance, leakage), optional cross-validation and scaler persistence.
- Unit tests for dataset builder and model loading.

## Modules To Update
- bot/ml/signal_model/dataset_builder.py, train.py, model.py, ensemble.py.
- storage/models and storage/datasets manifests; config/settings.yaml for training params and horizons.
- test_features.py to add dataset assertions.

## Tasks
1) Create/update:
- Add CLI entrypoint for dataset profiling (`python -m bot.ml.signal_model.dataset_builder --profile`).
- Extend train.py to support train/val split, early stopping, and save metrics/manifest (JSON) per model.
- Add evaluation script (e.g., bot/ml/signal_model/eval.py) to compute metrics on hold-out set and load saved models.
- Update SignalModel to load calibration/metadata and fail clearly on FEATURE_COLS mismatch; allow Ensemble weights from config.
2) Implement logic:
- Loop over configured symbols/horizons; enforce min_rows; log class balance and dataset shape.
- Persist feature importance/shap summaries and dataset paths into manifest.
- Keep compatibility with OnlineFeatureBuilder/FeatureBuilder outputs and storage layout.
3) Config:
- settings.yaml: ml.horizons, ml.min_rows, ml.test_size, ml.seed, ensemble weights path if needed.

## Tests
Run:
```
python -m bot.sandbox.generate_synthetic_ticks
python -m bot.ml.signal_model.dataset_builder --symbol BTCUSDT --horizon 1 --profile
python -m bot.ml.signal_model.train --symbol BTCUSDT --horizon 1 --min-rows 200
python -m bot.ml.signal_model.train --symbol BTCUSDT --horizon 3 --min-rows 200
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
```

## Verification Tasks
- Models saved under storage/models/signal_xgb_<symbol>_h<h>.json with manifest/metrics.
- Dataset profiling outputs class balance and feature stats; no NaN in FEATURE_COLS.
- Ensemble loads trained models without warnings; offline_loop executes predictions.

## Expected Output
- Reproducible ML training pipeline with metrics and manifests per horizon/symbol.
- Saved datasets under storage/datasets for traceability.
- Command-line workflows for training and evaluating new horizons.

## Acceptance Criteria
- Training runs succeed with metrics reported; manifest includes features, params, data_path, metrics.
- SignalModel/Ensemble load successfully with calibrated outputs.
- run_bot and offline_loop pick up new models without code changes.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 3 completed"
git push origin main
```
