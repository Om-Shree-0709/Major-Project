import os
import json
from pathlib import Path


class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = {}

        if Path(config_path).exists():
            self.load_config()
        else:
            self.create_default_config()

    def create_default_config(self):
        self.config = {
            "server": {
                "host": "localhost",
                "port": 8000
            },
            "logging": {
                "level": "INFO"
            },
            "mcp": {
                "timeout": 30
            }
        }

        self.save_config()

    def load_config(self):
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config

        for k in keys:
            value = value.get(k, {})

        return value or default


config_manager = ConfigManager()