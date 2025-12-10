# Stage 1 - Data Pipeline
## Objective
- Build reliable market data ingestion and persistence for ai_scalper_bot using websocket sources, mocks, and offline simulators.

## Current State
- bot/market_data/ws_manager.py builds Binance trade/depth streams and sends payloads to DataManager; DataManager writes JSON/CSV ticks under ./data with schema timestamp,price,qty,side; settings.yaml defaults to websocket mock and symbols ["BTCUSDT","ETHUSDT"].
- bot/market_data/mock_ws_manager.py and bot/market_data/offline_simulator.py stream synthetic events; sandbox/generate_synthetic_ticks.py builds CSV fixtures; run_bot currently consumes MockWSManager via _event_stream.
- binance_ws.py and bingx_ws.py are empty placeholders; no reconnection/backfill logic; no validation of incoming payloads; storage rotation and checksum missing.

## Missing Modules
- Exchange-specific websocket clients with auth/reconnect/backoff (binance_ws.py, bingx_ws.py) and schema validation.
- File rotation/retention for ticks/orderbooks plus lightweight quality checks.
- CLI entrypoints for starting capture (live/mock), progress logging, and fallback to offline replay.

## Modules To Update
- bot/market_data/ws_manager.py, binance_ws.py, bingx_ws.py, offline_simulator.py, mock_ws_manager.py, data_manager.py.
- config/settings.yaml to hold websocket selection, retention, and storage toggles.
- Integration touchpoints: ws_manager output -> DataManager; offline_loop/run_bot event streams.

## Tasks
1) Create/update the following files:
- Implement binance_ws.py and bingx_ws.py async clients that normalize trades/orderbooks to {s,p,q,m,E/T,...} and expose async generators.
- Harden ws_manager.py to choose backend (mock/binance/bingx) per config.app.websocket, include reconnect/backoff, heartbeat, and graceful shutdown.
- Enhance data_manager.py with schema enforcement, rotation (max rows/size), optional parquet output, and clear logging of write errors.
- Refresh offline_simulator.py and mock_ws_manager.py to reuse DataManager schema and allow configurable replay speed and jitter.
2) Implement logic:
- Validate and drop malformed events; attach source/latency metadata for monitoring.
- Keep integration compatible with FeatureBuilder, OnlineFeatureBuilder, DatasetBuilder (timestamp,price,qty,side).
- Provide CLI docs in module docstrings for running captures: `python -m bot.market_data.ws_manager` (live) and offline simulator options.
3) Config:
- settings.yaml: add websocket choices, backoff timers, retention limits, data paths; keep defaults safe (mock, no keys).

## Tests
Run:
```
python -m bot.sandbox.generate_synthetic_ticks
python -m bot.market_data.offline_simulator --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.market_data.ws_manager
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
```

## Verification Tasks
- data/ticks/*_stream.csv grows with header timestamp,price,qty,side and no malformed rows.
- WSManager reconnects after forced disconnect without crashing; mock/offline paths keep working.
- offline_loop and run_bot can iterate over events emitted by WSManager without schema errors.

## Expected Output
- Reliable ingestion pipeline with live/mock/offline sources writing normalized tick/orderbook data.
- Clear CLI usage and logs for capture jobs.
- Data artifacts ready for FeatureBuilder, DatasetBuilder, and XGBoost training.

## Acceptance Criteria
- Websocket ingestion survives reconnects and preserves schema for all configured symbols.
- DataManager writes JSON/CSV (and optional parquet) atomically with rotation and respects storage toggles.
- offline_loop and run_bot execute end-to-end on mock data without ingestion exceptions.

## Post-patch Commands
```
python -m bot.sandbox.offline_loop --ticks-path data/ticks/BTCUSDT_synthetic.csv
python -m bot.run_bot
```

## Commit
```
git add .
git commit -m "Stage 1 completed"
git push origin main
```
