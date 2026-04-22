"""Settings and configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, Field


class DataSettings(BaseModel):
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    output_dir: str = "data/outputs"


class AppSettings(BaseModel):
    name: str = "Payment Claim Detector"
    version: str = "0.1.0"


class ProcessingSettings(BaseModel):
    default_sheet_name: str = "Payment Register"
    date_column: str = "check_date"
    claim_column: str = "claim_number"
    payment_id_column: str = "payment_id"
    amount_column: str = "amount_issued"


class LoggingSettings(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Settings(BaseModel):
    app: AppSettings = Field(default_factory=AppSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    states: List[str] = Field(default_factory=lambda: ["NV", "CO", "AZ", "ID", "UT"])
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)


@lru_cache()
def get_settings() -> Settings:
    """Load settings from config files."""
    config_dir = Path(__file__).parent.parent.parent / "config"
    settings_file = config_dir / "settings.yaml"

    if settings_file.exists():
        with open(settings_file, "r") as f:
            data = yaml.safe_load(f)
        return Settings(**data)
    else:
        return Settings()


def load_column_aliases() -> Dict[str, List[str]]:
    """Load column aliases from config."""
    config_dir = Path(__file__).parent.parent.parent / "config"
    aliases_file = config_dir / "column_aliases.yaml"

    if aliases_file.exists():
        with open(aliases_file, "r") as f:
            return yaml.safe_load(f)
    else:
        return {}


def load_state_sheet_map() -> Dict[str, List[str]]:
    """Load state sheet mapping from config."""
    config_dir = Path(__file__).parent.parent.parent / "config"
    map_file = config_dir / "state_sheet_map.yaml"

    if map_file.exists():
        with open(map_file, "r") as f:
            return yaml.safe_load(f)
    else:
        return {}