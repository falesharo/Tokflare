import json
import os
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)
SETTINGS_FILE = "admin_settings.json"

class AdminSettings:
    _instance = None
    _data = {
        "test_mode": False,
        "profit_margin": settings.PROFIT_MARGIN
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdminSettings, cls).__new__(cls)
            cls._instance.load()
            cls._instance.save() # Force initial save
        return cls._instance

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self._data.update(json.load(f))
                logger.info("Admin settings loaded from file.")
            except Exception as e:
                logger.error(f"Failed to load admin settings: {e}")

    def save(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self._data, f)
            logger.info("Admin settings saved to file.")
        except Exception as e:
            logger.error(f"Failed to save admin settings: {e}")

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    @property
    def test_mode(self) -> bool:
        return self.get("test_mode", False)

    @test_mode.setter
    def test_mode(self, value: bool):
        self.set("test_mode", value)

    @property
    def profit_margin(self) -> float:
        return self.get("profit_margin", settings.PROFIT_MARGIN)

    @profit_margin.setter
    def profit_margin(self, value: float):
        self.set("profit_margin", value)

admin_settings = AdminSettings()
