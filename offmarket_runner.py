import argparse
import logging
import os

from offmarket_config import DEFAULT_CONFIG_PATH, DEFAULT_STATE_PATH
from offmarket_scheduler import run_offmarket_maintenance_once


def _configure_logging() -> None:
    logs_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "offmarket_scheduler.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main():
    _configure_logging()
    parser = argparse.ArgumentParser(description="One-shot off-market maintenance runner for Meta-Agent.")
    parser.add_argument("--config", default=None, help="Path to offmarket_schedule.yaml (optional).")
    parser.add_argument("--state", default=None, help="Path to offmarket_state.json (optional).")
    args = parser.parse_args()

    result = run_offmarket_maintenance_once(
        config_path=args.config or DEFAULT_CONFIG_PATH,
        state_path=args.state or DEFAULT_STATE_PATH,
    )

    # Concise console output
    status = result.get("status")
    ran = result.get("ran_cycles") or []
    print(f"[OFFMARKET] status={status} ran={ran} reason={result.get('reason')}")
    for summary in result.get("results", []):
        print(
            f" - goal={summary.get('goal')} status={summary.get('status')} "
            f"tasks={len(summary.get('tasks', []))} summary_md={summary.get('supervisor_md_path')}"
        )


if __name__ == "__main__":
    main()
