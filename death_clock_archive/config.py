"""Configuration persistence for Death Clock settings."""

import json
import os
from datetime import datetime

CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")

DEFAULT_CONFIG = {
    "date_of_birth": "1990-01-01",
    "sex": "male",
    "factors": {
        "current_smoker": False,
        "former_smoker": False,
        "obesity": False,
        "sedentary": False,
        "heavy_drinking": False,
        "diabetes": False,
        "regular_exercise": False,
        "mediterranean_diet": False,
        "college_degree": False,
        "married": False,
    },
    "window": {
        "x": 100,
        "y": 100,
        "width": 420,
        "height": 160,
    },
}


def load_config() -> dict:
    """Load configuration from disk, returning defaults if not found."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        # Merge with defaults to pick up any new keys
        merged = {**DEFAULT_CONFIG, **config}
        merged["factors"] = {**DEFAULT_CONFIG["factors"], **config.get("factors", {})}
        merged["window"] = {**DEFAULT_CONFIG["window"], **config.get("window", {})}
        return merged
    return {**DEFAULT_CONFIG, "factors": {**DEFAULT_CONFIG["factors"]}, "window": {**DEFAULT_CONFIG["window"]}}


def save_config(config: dict) -> None:
    """Save configuration to disk."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_dob(config: dict) -> datetime:
    """Parse date of birth from config string."""
    return datetime.strptime(config["date_of_birth"], "%Y-%m-%d")
