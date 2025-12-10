## Scope: Files to Inspect and Potentially Modify

You MUST inspect (and may modify / extend) at least:

- Core / Config:
  - bot/core/config_loader.py
  - bot/core/state.py (if present) and any shared state helpers
  - config/settings.yaml
  - config/pairs.yaml

- ML / Features:
  - bot/ml/signal_model/dataset_builder.py
  - bot/ml/signal_model/dataset.py
  - bot/ml/signal_model/train.py
  - bot/ml/signal_model/online_features.py
  - bot/ml/signal_model/model.py
  - bot/ml/ensemble.py

- Signals / Decision:
  - bot/engine/decision_engine.py
  - bot/ai/risk_moderator.py (may integrate as a light, local risk/signal filter)

- Risk / Money Management:
  - bot/trading/risk_engine.py
  - bot/trading/position_manager.py
  - bot/trading/order_manager.py

- Execution:
  - bot/trading/executor.py (demo/binance futures)
  - bot/trading/paper_trader.py
  - bot/run_bot.py and bot/main.py
  - bot/market_data/* (only as needed for spread/depth features, no heavy rewrites)

You may add new modules / packages where it improves clarity (e.g., `bot/risk/session_limits.py`, `bot/engine/regime_classifier.py`, `bot/execution/scalp_policy.py`).

## Tasks (grouped by layer)

### LAYER 1 — ML / Features

1. Extend training pipeline:
   - Update dataset builders and train.py to support multiple horizons: 1, 5, 30 (seconds or tick windows).
   - Store models under a clear naming scheme, e.g.:
     - storage/models/signal_xgb_{symbol}_h1.json
     - storage/models/signal_xgb_{symbol}_h5.json
     - storage/models/signal_xgb_{symbol}_h30.json
   - Ensure training script can train one or all horizons via CLI flags.

2. Add multi-timeframe features:
   - For the online & offline feature builders, compute features for 1s / 5s / 30s / 1m windows:
     - rolling volatility (std/ATR),
     - VWAP / short EMAs,
     - order-flow / imbalance,
     - simple volume spike flags.
   - Introduce a simple **market regime feature** (enum or encoded numeric):
     - flat / trending / high-vol / low-liq, derived from recent volatility and trend metrics.
   - Keep feature schema consistent between offline training and online inference; consider a small schema-hash helper to enforce this.

3. Warmup / context:
   - Implement minimal history checks:
     - before feeding features to the SignalModel and Ensemble,
     - before allowing any DecisionEngine trading actions (see LAYER 2).
   - Make warmup duration configurable in settings.yaml (e.g., warmup_seconds / warmup_bars).

### LAYER 2 — Decision & Signal Logic

4. Enhance EnsembleSignalModel or a new signal aggregator:
   - Aggregate outputs from horizons h1/h5/h30.
   - Provide a structured Signal object with:
     - per-horizon p_up/p_down/edge,
     - overall ensemble p_up/edge,
     - regime tag (from LAYER 1),
     - flags for conflicts between horizons.

5. Implement signal filters:
   - Only allow trade entries when:
     - horizon signals are consistent (configurable rule, e.g. h1 & h5 same direction, h30 not strongly opposite),
     - ensemble p_up (or p_down) exceeds a configurable confidence threshold.
   - Add a “loss streak” or “over-trading” filter:
     - track recent N trades and their PnL,
     - if there are ≥K losing trades within a short window, pause new entries for a cooling-off period.
   - Make these parameters configurable in settings.yaml under a new section (e.g., decision.filters).

6. Regime-aware behavior:
   - For flat regime:
     - smaller TP/SL, smaller sizes, more frequent trades allowed.
   - For trending regime:
     - allow positions to run longer; fewer flips; possibly trailing logic hooks (even if initial implementation is basic).
   - Encapsulate this in a **RegimePolicy** abstraction used by DecisionEngine.

### LAYER 3 — Money & Risk Management

7. Edge-based position sizing:
   - Implement a position sizing engine where:
     - position_size = base_size * f(edge),
       where f(edge) is a monotonic function (e.g. linear or capped curve).
   - Ensure:
     - min_position_size enforces meaningful minimum size,
     - max_position_size is capped by:
       - account equity,
       - leverage,
       - exchange constraints (min_notional, min_qty, step_size),
       - session risk limits.

8. Volatility-aware SL/TP:
   - Make SL/TP depend on recent volatility / ATR and regime:
     - high volatility → wider SL/TP, smaller size;
     - low volatility → tighter SL/TP, larger size within limits.
   - Keep parameters configurable in settings.yaml (e.g., risk.sl_multiplier, risk.tp_rr_ratio, per-regime overrides).

9. Session limits & governance:
   - Implement in risk_engine / position_manager (or separate module):
     - max_trades_per_hour,
     - max_daily_loss (absolute and % of starting equity),
     - optional max_daily_profit (lock-in / stop-trading after good day).
   - These limits should:
     - be checked before opening a new position,
     - optionally trigger a “pause trading” flag that DecisionEngine respects.
   - Provide a simple event or log that can later feed a higher-level Supervisor.

### LAYER 4 — Execution / Scalp-mode

10. Scalp-mode configuration:
    - In settings.yaml, add a structured section, e.g.:

      trading:
        mode: "normal" | "scalp"
        scalp:
          min_confidence: 0.6
          min_edge: 0.03
          max_hold_seconds: 30
          max_spread_bps: 5
          min_depth_quote: 500   # USDT or contracts
          ...

11. Implement scalp-mode logic:
    - Integrate into DecisionEngine and executor/order_manager:
      - Under trading.mode == "scalp", use:
        - stricter signal thresholds,
        - smaller TP/SL in price terms,
        - time-based exit (max_hold_seconds) in addition to price-based exits.
      - Check orderbook spread & depth before placing orders:
        - no trade if spread > max_spread_bps,
        - no trade if best-bid / best-ask depth < min_depth_quote.
    - Source orderbook data from existing market_data layer (ws_manager / data_manager).
      - If full depth is not yet available, start with a simplified best bid/ask spread approximation and design hooks for later depth extensions.

12. Order policy improvements:
    - Implement an execution policy that decides:
      - market vs limit, based on:
        - current spread,
        - expected slippage,
        - recent order fill stats (if available).
      - For market orders:
        - only when spread/depth ok and risk limits good.
      - For limit orders:
        - use price offsets near best bid/ask,
        - implement timeouts for cancellation or conversion to market.
    - Ensure:
      - quantities and prices respect exchange filters (stepSize, tickSize, minQty, minNotional).
      - this builds on top of the existing demo executor and its symbol metadata logic.

## Non-Goals / Constraints

- Do NOT introduce external heavy databases or new external services; stay within the existing filesystem-based storage for now.
- Do NOT change the basic project layout or break existing entrypoints:
  - root run_bot.py,
  - bot/run_bot.py (main async loop).
- Do NOT hard-code secrets or production keys; use config_loader / secrets as is.
- Keep all new parameters/configuration in YAML under existing or new sections; default values must be safe and conservative.

## Output Format

Your response MUST consist only of `===FILE: path===` blocks with full file contents.

- For each modified file, output the entire new version (not a diff).
- For each new file, create an appropriate path inside the project (e.g., `bot/engine/regime_policy.py`).
- Do NOT output explanations outside of file blocks.

Example:

===FILE: bot/engine/decision_engine.py===
<full updated code>

===FILE: config/settings.yaml===
<full updated YAML>

...

## Tests & Verification

Where reasonable, add or update small self-contained tests / sandbox scripts, for example:

- Extend `bot/sandbox/offline_loop.py` or add a similar script to:
  - run a short offline simulation with:
    - warmup,
    - multi-horizon signals,
    - new DecisionEngine logic,
    - risk limits & scalp-mode.
  - print summary stats: number of trades, win rate, max DD, basic PnL.

At minimum, ensure:

- `python -m py_compile` passes for all changed .py files.
- `python run_bot.py` in demo mode still starts successfully (even if there is no real feed), and logs show:
  - warmup period,
  - multi-horizon model loading (where available),
  - risk/session limits being loaded from config.

## Acceptance Criteria

- ML / feature code supports multiple horizons and adds basic market regime features with consistent schemas between training and live.
- DecisionEngine (and related layers) apply:
  - horizon agreement logic,
  - configurable confidence thresholds,
  - loss-streak / over-trading guards,
  - regime-aware behavior.
- Risk / money management:
  - position sizing is edge-based and respects min/max caps,
  - SL/TP depend on volatility/regime,
  - session limits (max trades per hour, max daily loss) are enforced.
- Execution:
  - scalp-mode is configurable and active, with spread/depth filters and time-based exits,
  - market/limit order decision is based on simple but clear policy,
  - quantities/prices are normalized to exchange requirements.

If in doubt between a “quick hack” and a “clean extensible design”, choose the clean design, but keep the implementation concise and focused.