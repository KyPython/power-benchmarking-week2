#!/usr/bin/env python3
"""
Configuration Management

Handles YAML/JSON configuration files, environment variables, and profile management.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict

CONFIG_DIR = Path.home() / ".power_benchmarking"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
PROFILES_DIR = CONFIG_DIR / "profiles"


@dataclass
class PowerMetricsConfig:
    """Power metrics configuration."""
    sample_interval: int = 500  # milliseconds
    samplers: list = None  # Will default to ['cpu_power', 'ane_power', 'gpu_power']
    
    def __post_init__(self):
        if self.samplers is None:
            self.samplers = ['cpu_power', 'ane_power', 'gpu_power']


@dataclass
class ArduinoConfig:
    """Arduino configuration."""
    enabled: bool = False
    port: str = "/dev/cu.usbmodem*"
    baud_rate: int = 115200


@dataclass
class AppConfig:
    """Application configuration."""
    powermetrics: PowerMetricsConfig = None
    arduino: ArduinoConfig = None
    default_profile: str = "default"
    
    def __post_init__(self):
        if self.powermetrics is None:
            self.powermetrics = PowerMetricsConfig()
        if self.arduino is None:
            self.arduino = ArduinoConfig()


class ConfigManager:
    """Configuration manager."""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or CONFIG_FILE
        self.config_dir = self.config_file.parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                if (self.config_file.suffix == '.yaml' or self.config_file.suffix == '.yml') and YAML_AVAILABLE:
                    with open(self.config_file, 'r') as f:
                        return yaml.safe_load(f) or {}
                else:
                    with open(self.config_file, 'r') as f:
                        return json.load(f) or {}
            except Exception as e:
                print(f"⚠️  Error loading config: {e}, using defaults")
                return self._default_config()
        else:
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "powermetrics": {
                "sample_interval": 500,
                "samplers": ["cpu_power", "ane_power", "gpu_power"]
            },
            "arduino": {
                "enabled": False,
                "port": "/dev/cu.usbmodem*",
                "baud_rate": 115200
            },
            "default_profile": "default"
        }
    
    def save_config(self, config: Optional[Dict] = None):
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        try:
            if (self.config_file.suffix == '.yaml' or self.config_file.suffix == '.yml') and YAML_AVAILABLE:
                with open(self.config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            else:
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def load_profile(self, profile_name: str) -> Dict:
        """Load a profile."""
        # Try YAML first, then JSON
        for ext in ['.yaml', '.yml', '.json']:
            profile_file = PROFILES_DIR / f"{profile_name}{ext}"
            if profile_file.exists():
                try:
                    with open(profile_file, 'r') as f:
                        if ext == '.json':
                            return json.load(f) or {}
                        elif YAML_AVAILABLE:
                            return yaml.safe_load(f) or {}
                except Exception:
                    continue
        return {}
    
    def save_profile(self, profile_name: str, profile_data: Dict):
        """Save a profile."""
        # Use JSON if YAML not available, otherwise YAML
        if YAML_AVAILABLE:
            profile_file = PROFILES_DIR / f"{profile_name}.yaml"
            try:
                with open(profile_file, 'w') as f:
                    yaml.dump(profile_data, f, default_flow_style=False, sort_keys=False)
            except Exception as e:
                print(f"⚠️  Error saving profile: {e}")
        else:
            profile_file = PROFILES_DIR / f"{profile_name}.json"
            try:
                with open(profile_file, 'w') as f:
                    json.dump(profile_data, f, indent=2)
            except Exception as e:
                print(f"⚠️  Error saving profile: {e}")
    
    def list_profiles(self) -> List[str]:
        """List available profiles."""
        profiles = []
        for ext in ['.yaml', '.yml', '.json']:
            for profile_file in PROFILES_DIR.glob(f"*{ext}"):
                profiles.append(profile_file.stem)
        return sorted(set(profiles))


def get_config_manager() -> ConfigManager:
    """Get configuration manager instance."""
    return ConfigManager()

