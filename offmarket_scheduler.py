import datetime
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from offmarket_config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_STATE_PATH,
    OffMarketConfig,
    OffMarketScheduleItem,
    OffMarketState,
    is_bot_idle,
    load_offmarket_config,
    load_offmarket_state,
    save_offmarket_state,
)
from supervisor_runner import run_supervisor_cycle

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

logger = logging.getLogger(__name__)


@dataclass
class DueCycle:
    goal: str
    mode: str
    schedule: OffMarketScheduleItem


def _now_in_tz(tz_name: str, now: Optional[datetime.datetime] = None) -> datetime.datetime:
    naive_now = now or datetime.datetime.utcnow()
    if ZoneInfo is None:
        return naive_now
    try:
        tz = ZoneInfo(tz_name)
        return naive_now.replace(tzinfo=datetime.timezone.utc).astimezone(tz)
    except Exception:
        return naive_now


def _day_name(dt: datetime.datetime) -> str:
    return dt.strftime("%a")  # Mon, Tue, ...


def _parse_time_str(time_str: str) -> tuple[int, int]:
    try:
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 3, 0


def _reset_runs_if_new_day(state: OffMarketState, current_date: str) -> None:
    if state.runs_date != current_date:
        state.runs_today = {}
        state.runs_date = current_date


def compute_due_cycles(
    config: OffMarketConfig,
    state: OffMarketState,
    now: Optional[datetime.datetime] = None,
) -> List[DueCycle]:
    """
    Determines which supervisor cycles should run based on schedule, cooldown, and per-day limits.
    """
    current = _now_in_tz(config.timezone, now)
    _reset_runs_if_new_day(state, current.strftime("%Y-%m-%d"))

    due: List[DueCycle] = []
    for sched in config.schedules:
        if not sched.enabled:
            continue

        today_name = _day_name(current)
        if sched.days != ["*"] and today_name not in sched.days:
            continue

        hour, minute = _parse_time_str(sched.time)
        scheduled_dt = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
        window_end = scheduled_dt + datetime.timedelta(minutes=sched.window_minutes)
        if current < scheduled_dt or current > window_end:
            continue

        last_run_str = state.last_runs.get(sched.goal)
        if last_run_str:
            try:
                last_run_dt = datetime.datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
                delta_minutes = (current - last_run_dt).total_seconds() / 60
                if delta_minutes < config.cooldown_minutes:
                    continue
            except Exception:
                pass

        runs_today = state.runs_today.get(sched.goal, 0)
        if runs_today >= config.max_runs_per_day:
            continue

        due.append(DueCycle(goal=sched.goal, mode=sched.mode, schedule=sched))

    return due


def run_offmarket_maintenance_once(
    config_path: str = DEFAULT_CONFIG_PATH,
    state_path: str = DEFAULT_STATE_PATH,
    now: Optional[datetime.datetime] = None,
) -> Dict[str, Any]:
    """
    One-shot runner that evaluates off-market schedules and triggers supervisor cycles if due.
    """
    logger.info("Loading off-market config from %s", config_path)
    config = load_offmarket_config(config_path)
    state = load_offmarket_state(state_path)

    current = _now_in_tz(config.timezone, now)
    logger.info("Current time in %s: %s", config.timezone, current.isoformat())

    if config.require_bot_idle:
        idle = is_bot_idle(config)
        if not idle:
            logger.warning("Bot is not idle; skipping maintenance.")
            return {
                "status": "skipped",
                "reason": "bot_not_idle",
                "now": current.isoformat(),
                "ran_cycles": [],
                "results": [],
                "config_path": config_path,
                "state_path": state_path,
            }

    due_cycles = compute_due_cycles(config, state, current)
    if not due_cycles:
        logger.info("No due cycles at this time.")
        return {
            "status": "no_due_cycles",
            "reason": "no_due_cycles",
            "now": current.isoformat(),
            "ran_cycles": [],
            "results": [],
            "config_path": config_path,
            "state_path": state_path,
        }

    results = []
    ran_cycles = []
    for cycle in due_cycles:
        logger.info("Running supervisor cycle: goal=%s mode=%s", cycle.goal, cycle.mode)
        summary = run_supervisor_cycle(goal=cycle.goal, mode=cycle.mode, project=config.project)
        results.append(summary)
        ran_cycles.append(cycle.goal)
        state.last_runs[cycle.goal] = current.isoformat()
        state.runs_today[cycle.goal] = state.runs_today.get(cycle.goal, 0) + 1
        logger.info("Supervisor cycle completed: goal=%s status=%s", cycle.goal, summary.get("status"))

    save_offmarket_state(state, state_path)
    logger.info("Saved off-market state to %s", state_path)

    return {
        "status": "ok",
        "reason": None,
        "now": current.isoformat(),
        "ran_cycles": ran_cycles,
        "results": results,
        "config_path": config_path,
        "state_path": state_path,
    }
