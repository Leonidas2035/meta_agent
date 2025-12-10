# STAGE: QuantumEdge v2 — LAYER 3 (Money & Risk Management)

## ROLE

You are Codex working inside:
C:/ai_scalper_bot

Your task in THIS STAGE is to upgrade ONLY **Layer 3 — Money & Risk Management** of the QuantumEdge (ai_scalper_bot) system to a v2 architecture with:

1) Position sizing based on model edge (from Layer 2 / ML ensemble).
2) Volatility-aware SL/TP placement.
3) Session-level risk constraints (trades per hour, daily loss, etc.).
4) Simple hooks for an upper “Supervisor” layer (even if currently stubbed).

Do NOT modify ML/feature computations (Layer 1) or core decision logic (Layer 2) beyond what is necessary to pass structured information into the risk/money management layer.

---

## CONTEXT & DEPENDENCIES

Assume that:

- **Layer 1 (ML / Features)** provides:
  - multi-horizon predictions,
  - market regime tag,
  - volatility-related features (e.g., realized volatility, ATR, etc.),
  - warmup readiness flags.

- **Layer 2 (Decision & Signal Logic)** provides:
  - a structured `Decision` object (or equivalent) that includes:
    - direction (LONG / SHORT / FLAT / NO_TRADE),
    - action_type (ENTER / EXIT / HOLD / NO_ACTION),
    - confidence (0–1),
    - edge (≈ |p_up − 0.5|),
    - regime,
    - reasons / flags for why decision is allowed or blocked.

Your role is to take this Decision + current market/account state and:

- compute **how big** the position should be,
- compute **where** SL/TP should be,
- check **whether** we are allowed to open a new trade right now (session constraints),
- and pass a **RiskCheckedOrder** (or similar structure) to execution (Layer 4).

---

## FILES TO INSPECT (AND MOST LIKELY MODIFY)

You MUST inspect these files first:

- Trading / risk / state:
  - bot/trading/risk_engine.py
  - bot/trading/position_manager.py
  - bot/trading/order_manager.py
  - bot/trading/executor.py  (integration point; keep changes minimal)
  - any existing “risk” or “sizing” helpers.

- Decision layer:
  - bot/engine/decision_engine.py
  - bot/engine/decision_types.py  (or equivalent structured decision definitions)

- Core / config / state:
  - bot/core/config_loader.py
  - bot/core/state.py  (if present; may hold equity/balance info)
  - config/settings.yaml

- Any code that currently:
  - computes position size,
  - sets fixed SL/TP,
  - enforces basic risk limits (even if stubby).

Build a clear picture of how trades are currently created:
DecisionEngine → (maybe risk_engine) → order_manager → executor.

---

## TARGET FOR LAYER 3

### A. Position sizing based on edge

Goal: position size must depend on both **account equity** and **signal strength (edge)**.

Definitions:

- `edge` ≈ |p_up − 0.5| or |p_down − 0.5| from Layer 2.
- `equity` = current account equity in USDT (demo or live).
- base risk parameters configured in settings.yaml.

#### 1. Config design

In `config/settings.yaml`, add a dedicated risk section, for example:

```yaml
risk:
  # fraction of equity risked per trade (base)
  base_risk_fraction: 0.005      # 0.5% per trade

  # min/max caps on position notional (in USDT)
  min_notional: 10
  max_notional: 500

  # how edge scales size (example linear/capped scaling)
  edge_sizing:
    min_edge: 0.01
    max_edge: 0.10
    min_multiplier: 0.5          # 50% of base size when edge is just above min_edge
    max_multiplier: 2.0          # 200% of base size when edge >= max_edge

  # hard supervisor-like caps (per symbol or global)
  max_leverage: 10
  max_exposure_fraction: 0.2     # max 20% of equity in one symbol
You may refine structure but keep it config-driven and easy to read.

2. Sizing logic (in risk_engine or a new module)
Implement a position sizing helper, e.g. in bot/trading/position_sizing.py or inside risk_engine.py:

Input:

Decision (direction, edge),

current price,

current equity,

existing exposure for the symbol (if any),

exchange constraints (min_qty, step_size, min_notional, leverage caps).

Steps:

Compute base notional:

python
Копіювати код
base_notional = risk.base_risk_fraction * equity
Compute edge-based multiplier:

If edge <= min_edge: either:

return 0 (no trade), OR

use min_multiplier.

If edge >= max_edge: use max_multiplier.

Otherwise: scale linearly between min_multiplier and max_multiplier.

Example:

python
Копіювати код
m = clamp(
    risk.edge_sizing.min_multiplier +
    (edge - min_edge) / (max_edge - min_edge)
    * (risk.edge_sizing.max_multiplier - risk.edge_sizing.min_multiplier),
    risk.edge_sizing.min_multiplier,
    risk.edge_sizing.max_multiplier,
)
target_notional = base_notional * m
Enforce global caps:

target_notional = clamp(target_notional, risk.min_notional, risk.max_notional)

Also respect max_exposure_fraction * equity:

if current exposure for symbol + target_notional > allowed max:

reduce target_notional or block new trade.

Convert notional to quantity:

raw_qty = target_notional / price

Pass through existing symbol normalization:

min_qty,

step_size,

min_notional,

rounding.

This must reuse symbol metadata logic introduced earlier in the executor (LotSize, tickSize).

If normalized qty is 0 or below exchange min:

block the trade (NO_TRADE / return None),

log reason: "SIZE_TOO_SMALL".

Output:

a SizedOrder / RiskCheckedOrder structure that includes:

symbol,

direction,

quantity,

target_notional,

leverage (if applicable),

meta info (edge, base_risk_fraction, multipliers applied).

B. Volatility-aware SL/TP
Goal: adapt SL/TP distances and possibly size scaling to current volatility.

Assumptions:

Layer 1 provides volatility metrics:

e.g. ATR, rolling std of returns, etc.

accessible directly or via a “market state” helper.

1. Config design
Extend risk section in settings.yaml, for example:

yaml
Копіювати код
risk:
  ...
  sltp:
    # base R-multiple for SL/TP
    base_rr: 1.5          # TP = 1.5 * SL

    # volatility-based distance factors (in % of price or multiples of ATR)
    mode: "atr"           # "atr" or "percent"

    atr:
      sl_mult_low_vol: 1.0
      sl_mult_high_vol: 0.5
      tp_mult_low_vol: 1.5
      tp_mult_high_vol: 1.0
      vol_threshold: 1.5   # threshold between low/high volatility regimes in ATR units

    percent:
      sl_percent_low_vol: 0.2
      sl_percent_high_vol: 0.4
      tp_rr_low_vol: 2.0
      tp_rr_high_vol: 1.0
Any clear and coherent scheme is acceptable, as long as it is config-driven.

2. Volatility classification
Implement a simple volatility band classification in risk_engine or a small helper module:

Input:

current volatility metric (e.g., ATR / price or std of returns),

vol_threshold.

Output:

VOL_LOW / VOL_HIGH (and optionally MEDIUM if needed).

This classification can re-use or complement the regime tag from Layer 1.

3. SL/TP distance computation
Based on:

direction (LONG / SHORT),

price,

volatility band,

config.

Example for ATR mode:

If VOL_LOW:

sl_distance = atr * sl_mult_low_vol

tp_distance = atr * tp_mult_low_vol

If VOL_HIGH:

sl_distance = atr * sl_mult_high_vol

tp_distance = atr * tp_mult_high_vol

Then:

For LONG:

sl_price = entry_price - sl_distance

tp_price = entry_price + tp_distance

For SHORT:

sl_price = entry_price + sl_distance

tp_price = entry_price - tp_distance

Enforce:

min SL/TP distances so they are not below tickSize / min price movement allowed by the exchange.

Optionally (not required in this stage): you can further adjust size based on volatility band (e.g., half size in high volatility), but keep the logic simple and clearly documented.

C. Session constraints (risk limits over time)
Goal: enforce session-level risk constraints:

max trades per hour,

max daily loss (absolute and % of equity),

optional hooks for max daily profit, pause after big win, etc.

1. Config design
Extend risk section further, e.g.:

yaml
Копіювати код
risk:
  ...
  session:
    max_trades_per_hour: 100

    max_daily_loss_abs: 200       # USDT
    max_daily_loss_pct: 0.05      # 5% of starting equity for the day

    # optional safety
    max_daily_profit_abs: null    # can be used to "lock in" a good day
    max_daily_profit_pct: null

    # what to do when limit hit:
    on_violation: "halt"          # "halt" or "cooldown"
    cooldown_minutes: 60
2. Session tracking
In risk_engine.py or a new session_limits.py:

Track per day (UTC or exchange timezone):

starting_equity,

realized PnL (closed trades only),

max drawdown (optional),

number of trades opened,

last trade timestamps.

Use position_manager / order_manager data:

when a trade closes, update realized PnL,

each time a trade is opened, update counts/metrics.

You may persist these in memory plus optional simple on-disk logs (JSON/CSV) if helpful, but avoid heavy database dependencies.

3. Enforcement
Before approving a new entry trade:

Check trades_last_hour <= max_trades_per_hour.

If violated:

block entry,

set a flag:

session_state.overtrading = True,

return a decision to caller:

NO_TRADE / “session_limit”,

reason: "MAX_TRADES_PER_HOUR_REACHED".

Compute current daily loss:

daily_pnl = realized_pnl_today.

If:

daily_pnl <= -max_daily_loss_abs, or

daily_pnl <= -max_daily_loss_pct * starting_equity:

set session_state.halted = True OR cooldown_until depending on config,

block entries:

reason: "MAX_DAILY_LOSS_REACHED".

If settings specify profit-based stop:

similar logic for max_daily_profit_abs / max_daily_profit_pct.

Important:

All session checks happen after DecisionEngine says “ENTER” but before order is sent to executor.

The result must be communicated back as a structured answer (e.g., RiskCheckResult) so that DecisionEngine / upper Supervisor can log or react.

D. Hooks for an upper Supervisor
Goal: provide simple, explicit hooks for a future “Supervisor agent” without implementing it now.

Implement in risk_engine.py or a small helper:

A thin layer that generates risk events, e.g.:

RISK_EVENT_MAX_DAILY_LOSS_HIT

RISK_EVENT_MAX_TRADES_PER_HOUR_HIT

RISK_EVENT_POSITION_TOO_LARGE

etc.

These events can be:

logged in a structured way, and/or

pushed into a simple event queue object.

Design a basic interface:

python
Копіювати код
class RiskEvent:
    def __init__(self, type: str, symbol: str, details: dict): ...

def publish_risk_event(event: RiskEvent) -> None:
    # for now: log it
    # later: Supervisor will subscribe here
No complex infra is needed now; just make a clear single point where such events are emitted.

INTEGRATION POINTS
DecisionEngine → RiskEngine:

DecisionEngine builds a Decision with direction/action/edge/regime.

It calls RiskEngine with:

Decision,

symbol,

latest price,

maybe volatility snapshot (or RiskEngine reads it from a shared state).

RiskEngine returns:

RiskCheckResult (or similar), which may contain:

approved: True/False,

sized quantity / notional,

SL/TP levels,

reasons for rejection if not approved,

any risk events generated.

RiskEngine → OrderManager / Executor:

When approved, OrderManager receives a fully specified order:

symbol,

direction,

qty,

price (if limit),

SL/TP levels.

Execution details (market vs limit, scalp-mode) remain under Layer 4 and must not be implemented here beyond minimal compatibility.

Logging:

All rejections due to risk/session constraints must be logged clearly with:

symbol, decision, edge, notional, reason.

IMPLEMENTATION GUIDELINES
Do NOT:

change how ML computes predictions (Layer 1),

change horizon agreement / confidence logic (Layer 2),

implement scalp-mode / microstructure logic (Layer 4).

Do:

centralize position sizing logic in RiskEngine or a dedicated sizing module,

make it config-driven and dependent on edge & equity,

centralize SL/TP computation in the same layer,

centralize session limits enforcement in risk_engine/session_limits.

Backwards compatibility:

If some code still expects a simple “qty + fixed SL/TP”, keep an adapter:

default to using new risk engine but preserve old interfaces where needed.

Safety:

If any error occurs when computing risk (e.g., missing equity or volatility data):

fail safe: do NOT trade,

log an ERROR with context.

ACCEPTANCE CRITERIA FOR LAYER 3
Layer 3 is considered successfully upgraded if:

Position sizing:

depends on equity and edge as configured,

respects min_notional, max_notional, max_exposure_fraction,

respects exchange filters (min_qty, step_size, min_notional) by reusing existing metadata logic.

SL/TP:

SL/TP distances depend on volatility (ATR or %),

SL/TP are directionally correct and normalized to tickSize,

configuration of volatility bands and multipliers is read from settings.yaml.

Session constraints:

max_trades_per_hour is enforced,

max_daily_loss_abs AND/OR max_daily_loss_pct is enforced,

when limits are hit, new entries are blocked and logged.

Hooks:

risk events are emitted using a simple, centralized mechanism,

events are logged in a way that a Supervisor can later consume.

Runtime:

python run_bot.py in demo mode still runs,

logs show:

computed sizes (notionals and qty),

SL/TP values,

session stats,

reasons when trades are blocked by risk.

OUTPUT FORMAT
Follow the Meta-Agent / Codex file-block convention.

Only output updated/created files as:

===FILE: path/to/file.py===
<full file content>

Examples of files you may update/create:

bot/trading/risk_engine.py

bot/trading/position_sizing.py (if created)

bot/trading/session_limits.py (if created)

bot/trading/position_manager.py (extensions)

bot/trading/order_manager.py (integration)

bot/engine/decision_engine.py (minimal wiring only)

config/settings.yaml (risk & session config)

Do NOT implement Layer 4 (execution / scalp-mode) in this stage.
That will be handled in the next stage.