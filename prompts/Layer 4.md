# STAGE: QuantumEdge v2 — LAYER 4 (Execution / Scalp-mode)

## ROLE

You are Codex working inside:
C:/ai_scalper_bot

Your task in THIS STAGE is to upgrade ONLY **Layer 4 — Execution / Scalp-mode** of the QuantumEdge (ai_scalper_bot) system to a v2 architecture with:

1) A dedicated **scalp-mode** in the decision/execution pipeline, switchable via config.
2) Stricter entry conditions for scalp trades (confidence + order-flow / microstructure checks).
3) Spread and local depth checks (no trades in bad microstructure conditions).
4) An order policy that:
   - uses MARKET only when spread & depth are acceptable and latency is low,
   - otherwise prefers near-touch LIMIT orders with small offsets and timeouts,
   - safely handles partial fills and cancellations.

Do NOT redesign ML (Layer 1), signal logic (Layer 2) or money/risk management (Layer 3).  
You may only **consume** their outputs and add the missing **execution / scalp** behavior on top.

---

## CONTEXT & DEPENDENCIES

Assume:

- **Layer 1 (ML / Features)**:
  - multi-horizon models, regime tag, volatility metrics available.

- **Layer 2 (Decision & Signal Logic)**:
  - produces a structured `Decision` object that includes:
    - direction (LONG / SHORT / NO_TRADE),
    - action_type (ENTER / EXIT / HOLD / NO_ACTION),
    - confidence, edge, regime,
    - possibly `trade_style` (SCALP vs TREND) or a flag suitable for scalp-mode.

- **Layer 3 (Money & Risk)**:
  - provides a `RiskCheckResult` / `RiskCheckedOrder` with:
    - approved: True/False,
    - symbol, direction,
    - qty (normalized),
    - notional,
    - SL/TP prices,
    - any risk events.

Your Layer 4 must take this **risk-approved** order intent and:

- decide **how** to send it (market vs limit),
- enforce microstructure constraints (spread, depth),
- manage order lifecycle (place / cancel / re-place / timeout),
- specialize behavior when **trading.mode == "scalp"**.

---

## FILES TO INSPECT (AND MOST LIKELY MODIFY)

You MUST inspect these first:

- Execution / orders:
  - bot/trading/executor.py        (Binance futures demo executor)
  - bot/trading/order_manager.py
  - bot/trading/position_manager.py
  - bot/trading/risk_engine.py     (ONLY for integration points, do not change risk logic)

- Decision / engine:
  - bot/engine/decision_engine.py
  - bot/engine/decision_types.py   (or equivalent)

- Market data / orderbook:
  - bot/market_data/* (especially any module that provides:
      - best bid/ask,
      - orderbook snapshots / depth,
      - spread,
      - latency info if available)

- Core / config:
  - bot/core/config_loader.py
  - config/settings.yaml

You must understand how:

DecisionEngine → RiskEngine → OrderManager → Executor  
currently flows, and insert **scalp-mode logic** at the right place.

---

## TARGET FOR LAYER 4

### A. Config-driven trading mode & scalp config

Goal: control execution behavior via config, **without hard-coding** values.

In `config/settings.yaml`, define or align with an existing structure similar to:

```yaml
trading:
  mode: "normal"       # "normal" | "scalp"

  scalp:
    enabled: true

    # Entry conditions
    min_conf_long: 0.60
    min_conf_short: 0.60
    min_edge: 0.03

    # Order-flow / microstructure filters
    max_spread_bps: 5           # no trades if spread > 5 bps
    min_top_depth_usdt: 1000    # required depth on best bid/ask
    min_book_levels: 5          # minimum number of valid levels to consider "OK" depth

    # TP/SL tuning for micro-moves
    max_hold_seconds: 30
    sl_distance_bps: 10         # override for scalp stops, in bps if configured
    tp_distance_bps: 20
    use_risk_sl_tp: true        # if true, start from risk-engine SL/TP and then clamp for scalp

    # Order policy
    prefer_limit: true
    passive_offset_bps: 2       # how far from best bid/ask for passive orders
    order_timeout_seconds: 2    # cancel or adjust if not filled within this time
    partial_fill_min_ratio: 0.5 # if filled less than 50% by timeout, handle accordingly

    # Safety
    cancel_on_spread_widening: true
    spread_widen_bps: 10        # if spread jumps above this, cancel scalp order
You may adjust names and exact fields, but the config must:

distinguish trading.mode == "normal" vs "scalp",

contain thresholds for:

confidence/edge,

spread and depth,

micro TP/SL / max_hold_seconds,

passive order behavior (offset, timeout).

The executor/manager must read ONLY from config via config_loader.

B. Stricter scalp entry conditions at execution gate
Goal: even if DecisionEngine & RiskEngine say “ENTER LONG/SHORT”, scalp-mode must re-check conditions at execution time:

microstructure (spread, depth),

scalp-specific confidence thresholds.

Implement in an appropriate place:

either in order_manager.py before constructing the actual order,

or in executor.py with a dedicated “scalp validator” helper.

Steps:

Read current spread and depth from market data:

Use existing market_data components to get:

best_bid_price, best_ask_price,

top-of-book bid/ask sizes (converted to USDT if necessary),

optionally aggregated depth over first N levels.

Compute:

spread = ask - bid

mid = (bid + ask) / 2

spread_bps = (spread / mid) * 1e4

Check microstructure:

If spread_bps > trading.scalp.max_spread_bps → block the trade:

log: "[SCALP] Blocked: spread too wide for {symbol}: {spread_bps:.2f} bps"

If top_depth_usdt < trading.scalp.min_top_depth_usdt → block:

log: "[SCALP] Blocked: insufficient depth for {symbol}: {depth}"

Check scalp confidence:

Use Decision’s confidence and edge fields:

if confidence < trading.scalp.min_conf_long for LONG, or min_conf_short for SHORT:

block,

reason: "SCALP_LOW_CONFIDENCE".

if edge < trading.scalp.min_edge:

block,

reason: "SCALP_LOW_EDGE".

Only proceed to actually creating orders if all scalp checks pass.

These checks must only apply when:

trading.mode == "scalp"

and (optionally) Decision indicates trade_style == "SCALP".

In normal mode, execution should behave like before, with minimal modifications.

C. Scalp-mode TP/SL & max holding time
Goal: specialize TP/SL and holding behavior for scalp trades:

small TP/SL tuned for micro-moves,

time-based exit if price doesn’t move.

Assume Layer 3 already computes a base SL/TP using volatility and risk config.
Scalp-mode may override or clamp those values.

Implementation:

After RiskEngine provides SL/TP and before sending the order:

If trading.mode == "scalp":

Option A: start from risk SL/TP, then enforce that:

scalp_sl_distance_bps and scalp_tp_distance_bps are upper limits for distance.

Option B: compute scalp SL/TP directly from:

mid price,

sl_distance_bps, tp_distance_bps config.

Normalize price levels to tickSize (reuse existing symbol metadata logic).

Add max_hold_seconds to the order metadata:

Store this in an internal order-tracking structure, e.g. in order_manager:

open_orders[order_id].max_hold_until = timestamp + max_hold_seconds

In the main loop / async tasks:

Periodically check open scalp orders and positions:

If position is open and now >= entry_time + max_hold_seconds:

trigger a market exit or best-available exit,

log: "[SCALP] Time-based exit triggered for {symbol}".

This is especially relevant for scalp positions that don’t hit SL/TP quickly.

D. Order policy: market vs limit, partial fills, cancellations
Goal: create a simple but robust order policy for scalp-mode while keeping normal mode intact.

1. Market vs limit choice
By default:

If trading.mode == "normal":

use the current behavior (whatever OrderManager / Executor already does).

If trading.mode == "scalp":

and spread & depth are GOOD:

we may allow MARKET orders (fast entry).

but if user prefers prefer_limit = true:

we prefer LIMIT orders placed very close to top-of-book.

Implement logic:

For scalp entry:

Compute bid/ask as above.

If using MARKET:

ensure that:

spread_bps <= max_spread_bps,

top_depth_usdt >= min_top_depth_usdt.

Else, fallback to LIMIT.

For scalp LIMIT:

LONG:

place limit at bid + passive_offset or near-mid (depending on passive_offset_bps).

SHORT:

place limit at ask - passive_offset.

Normalize limit prices to tickSize.

2. Timeouts and partial fills
Extend order_manager.py (or another central order-tracking file):

For each open LIMIT order in scalp-mode, store:

created_at,

timeout_at = created_at + order_timeout_seconds,

min_fill_qty = qty * partial_fill_min_ratio.

On periodic checks:

If now >= timeout_at:

Query fill status (filled_qty, remaining_qty).

If filled_qty >= min_fill_qty:

Decide:

either keep position as is,

or optionally adjust SL/TP for smaller size.

If filled_qty < min_fill_qty:

Cancel the order.

Optionally:

re-place a new order (limit or market) based on updated spread/depth,

OR just give up and log "[SCALP] Cancelled due to poor fill".

Handling of partial fills must be safe:

never assume full size when only 30% filled,

maintain accurate position size via position_manager.

3. Spread widening safety
If cancel_on_spread_widening = true:

For open scalp orders:

if current spread_bps > trading.scalp.spread_widen_bps:

cancel the limit order,

log: "[SCALP] Cancelled order due to spread widening".

This may share code with the periodic order check.

E. Integration with existing loop & multi-pair support
Your changes must:

work with existing async main loop (with await asyncio.sleep(0.02) etc.),

support multiple symbols (already introduced in Layer 2/3 upgrades),

avoid blocking I/O (use async Binance client calls as already implemented).

Where to hook periodic checks:

in the main bot loop (e.g., bot/run_bot.py), or

via async tasks spawned from executor/order_manager, such as:

python
Копіювати код
async def monitor_open_orders():
    while True:
        await order_manager.check_open_orders()
        await asyncio.sleep(0.1)
You may add such a task if it does not break existing architecture.

IMPLEMENTATION GUIDELINES
Do NOT:

rewrite ML or DecisionEngine logic from scratch,

modify risk sizing formulas (Layer 3),

bypass RiskEngine (all trades must still go through risk checks).

Do:

add a thin “execution policy” layer that:

reads trading.mode and trading.scalp config,

checks spread/depth,

picks MARKET vs LIMIT,

manages timeouts and partial fills,

handles scalp-specific SL/TP & max-hold.

Backwards compatibility:

In normal mode, the system should behave almost exactly as before,

In scalp mode, new behavior is active only when configured:

trading.mode: "scalp"

trading.scalp.enabled: true.

Logging:

All blocks / decisions in scalp path must be logged with clear tags:

"[SCALP]" prefix is recommended,

reasons for block, cancel, or forced exit.

ACCEPTANCE CRITERIA FOR LAYER 4
Layer 4 is considered successfully upgraded if:

Config:

trading.mode and trading.scalp section exist and are used.

Changing trading.mode from "normal" to "scalp" clearly changes execution behavior.

Scalp entry conditions:

Spread/depth/edge/confidence thresholds are enforced.

Trades are blocked when microstructure conditions are bad, with clear logs.

TP/SL & max-hold:

Scalp trades have smaller TP/SL tuned via config (or clamped from Layer 3 values),

Max holding time is respected via time-based exits.

Order policy:

In scalp-mode:

MARKET is used only when spread/depth allow it,

LIMIT orders are used near-touch when configured,

partial fills & timeouts are handled safely.

Safety:

Orders are cancelled when spread widens too much if configured.

No infinite loops / blocking behavior; CPU usage stays under control.

Runtime:

python run_bot.py (demo) still runs without exceptions,

When trading.mode: "scalp", logs show:

"[SCALP]" decisions,

blocked entries due to microstructure,

time-based exits or order cancellations.

OUTPUT FORMAT
Follow the Meta-Agent / Codex file-block convention.

Only output updated/created files as:

===FILE: path/to/file.py===
<full file content>

Likely candidates:

bot/trading/executor.py

bot/trading/order_manager.py

bot/trading/position_manager.py (if needed)

bot/trading/execution_policy.py or similar (if you create a dedicated policy layer)

bot/market_data/* (only if needed to expose spread/depth as a clean API)

bot/run_bot.py (for wiring / periodic checks)

config/settings.yaml (trading.mode + trading.scalp config)

Do NOT modify other layers (ML, Decision, Risk) beyond what is necessary to pass structured decisions/order intents into the execution layer.