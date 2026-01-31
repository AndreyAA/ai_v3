"""Configuration loader for File Processor Service."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class DirectoriesConfig:
    """Directory paths configuration."""

    watch_dir: Path
    data_subdir: str
    processed_subdir: str

    @property
    def data_dir(self) -> Path:
        """Full path to data directory."""
        return self.watch_dir / self.data_subdir

    @property
    def processed_dir(self) -> Path:
        """Full path to processed directory."""
        return self.watch_dir / self.processed_subdir


@dataclass
class ServiceConfig:
    """Service behavior configuration."""

    poll_interval_sec: int


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str
    format: str


@dataclass
class Config:
    """Main configuration container."""

    directories: DirectoriesConfig
    service: ServiceConfig
    logging: LoggingConfig


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default path.

    Returns:
        Config object with all settings.
    """
    if config_path is None:
        config_path = os.environ.get(
            "FILE_PROCESSOR_CONFIG",
            Path(__file__).parent.parent / "config.yaml"
        )

    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    dirs_raw = raw_config["directories"]
    directories = DirectoriesConfig(
        watch_dir=Path(dirs_raw["watch_dir"]),
        data_subdir=dirs_raw["data_subdir"],
        processed_subdir=dirs_raw["processed_subdir"],
    )

    service = ServiceConfig(
        poll_interval_sec=raw_config["service"]["poll_interval_sec"],
    )

    logging_raw = raw_config["logging"]
    logging_config = LoggingConfig(
        level=logging_raw["level"],
        format=logging_raw["format"],
    )

    return Config(
        directories=directories,
        service=service,
        logging=logging_config,
    )
