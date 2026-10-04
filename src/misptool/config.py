from pathlib import Path
from typing import Any, Dict

import yaml

class Config:

    def __init__(self, config_path: str):
        self.config_path = config_path

        self.data = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        path = Path(self.config_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise ValueError("Config file must contain a YAML dictionary at the top level.")

        return config

    def get(self, key, default=None):
        return self.data.get(key, default)