import json
import os
from datetime import datetime, timedelta

from . import config


def load_state() -> dict:
    if os.path.exists(config.STATE_FILE):
        try:
            with open(config.STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    with open(config.STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def should_alert(state: dict, ticker: str, signal_type: str) -> bool:
    key = f"{ticker}:{signal_type}"
    last = state.get(key)
    if not last:
        return True
    last_time = datetime.fromisoformat(last)
    return datetime.utcnow() - last_time >= timedelta(minutes=config.COOLDOWN_MINUTES)


def mark_alerted(state: dict, ticker: str, signal_type: str) -> None:
    key = f"{ticker}:{signal_type}"
    state[key] = datetime.utcnow().isoformat()
