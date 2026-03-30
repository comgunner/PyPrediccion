"""Config manager for Heat Predictor - Trading Prediction System — persists settings to ~/.pyprediccion/config.json."""

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any


class ConfigManager:
    """Persistent configuration manager for Heat Predictor - Trading Prediction System."""

    CONFIG_DIR = Path.home() / ".pyprediccion"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    DEFAULT_CONFIG = {
        "SYMBOL": "BTCUSDT,ETHUSDT,DOGEUSDT",
        "INTERVAL": "15",
        "PROBABILITY_THRESHOLD": 0.65,
        "DARK_MODE": True,
        "BYBIT_API_KEY": "",
        "BYBIT_API_SECRET": "",
    }

    def __init__(self):
        """Initialize the config manager and load or create configuration."""
        self.config_data = {}
        self._initialize()

    def _initialize(self):
        """Create config directory and file if they do not exist, then load."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not self.CONFIG_FILE.exists():
            self._save_default()
            print(f"\n{'=' * 60}")
            print(" FIRST RUN: configuration file created")
            print(f" Path: {self.CONFIG_FILE}")
            print(f"{'=' * 60}\n")
        self._load()

    def _build_first_run_config(self) -> dict:
        """Build initial config from config.json.example if available, else DEFAULT_CONFIG."""
        example_path = Path(__file__).parent.parent / "config.json.example"
        try:
            with open(example_path, encoding="utf-8") as f:
                example = json.load(f)
            config = self.DEFAULT_CONFIG.copy()
            for key, value in example.items():
                if key.startswith("_"):
                    continue
                if key in ("BYBIT_API_KEY", "BYBIT_API_SECRET"):
                    config[key] = ""
                else:
                    config[key] = value
            return config
        except (OSError, json.JSONDecodeError):
            return self.DEFAULT_CONFIG.copy()

    def _save_default(self):
        """Write first-run configuration to disk, seeding from config.json.example."""
        config = self._build_first_run_config()
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def _load(self):
        """Load configuration from JSON file, merging missing keys with defaults."""
        try:
            with open(self.CONFIG_FILE, encoding="utf-8") as f:
                self.config_data = json.load(f)
            for key, value in self.DEFAULT_CONFIG.items():
                if key not in self.config_data:
                    self.config_data[key] = value
        except json.JSONDecodeError as e:
            print(f"Warning: config.json unreadable ({e}), using defaults.")
            self.config_data = self.DEFAULT_CONFIG.copy()

    def save(self) -> bool:
        """Persist current configuration to disk."""
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            return True
        except OSError as e:
            print(f"Error saving configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Return configuration value for key, or default if not present."""
        return self.config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value for key."""
        self.config_data[key] = value

    def get_symbols_list(self) -> list:
        """Return SYMBOL field as a list, splitting on commas if needed."""
        symbols = self.get("SYMBOL", "BTCUSDT")
        if isinstance(symbols, str):
            return [
                s.strip() for s in symbols.replace("\n", ",").split(",") if s.strip()
            ]
        return symbols

    def is_configured(self) -> bool:
        """Return True if API key and secret are set and not placeholders."""
        key = self.get("BYBIT_API_KEY", "")
        secret = self.get("BYBIT_API_SECRET", "")
        if not key or not secret:
            return False
        return not (key.startswith("YOUR_") or secret.startswith("YOUR_"))

    @property
    def config_path(self) -> Path:
        """Return absolute path to the configuration file."""
        return self.CONFIG_FILE

    @property
    def models_dir(self) -> Path:
        """Return path to the directory where trained models are stored."""
        return self.CONFIG_DIR / "models"

    def open_config_file(self) -> None:
        """Open the configuration file with the system default editor."""
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(self.CONFIG_FILE)  # noqa: S606
            elif system == "Darwin":
                subprocess.run(["open", str(self.CONFIG_FILE)], check=False)
            else:
                subprocess.run(["xdg-open", str(self.CONFIG_FILE)], check=False)
        except OSError as e:
            print(f"Could not open config file: {e}\nPath: {self.CONFIG_FILE}")
