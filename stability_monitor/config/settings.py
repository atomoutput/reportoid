"""
Application settings and configuration management
"""

import json
import os
from typing import Dict, Any

class Settings:
    """Manages application settings and configuration"""
    
    def __init__(self):
        self.config_file = "config/app_settings.json"
        self.settings = self._load_default_settings()
        self._load_user_settings()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default application settings"""
        return {
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "theme": "default"
            },
            "data": {
                "auto_detect_columns": True,
                "date_formats": [
                    "%m/%d/%Y %H:%M",
                    "%Y-%m-%d %H:%M:%S",
                    "%m/%d/%Y",
                    "%Y-%m-%d"
                ],
                "required_columns": ["Site", "Priority", "Created", "Company"],
                "optional_columns": ["Number", "Short description", "Category", "Subcategory", "Resolved"]
            },
            "reports": {
                "critical_threshold": 2,
                "mttr_targets": {
                    "1 - Critical": 4,  # hours
                    "2 - High": 24,
                    "3 - Medium": 72,
                    "4 - Low": 168
                },
                "date_presets": [
                    "Last 7 days",
                    "Last 30 days", 
                    "Last 90 days",
                    "Year to Date",
                    "Custom"
                ]
            },
            "export": {
                "default_format": "csv",
                "include_filters_in_export": True,
                "timestamp_exports": True
            }
        }
    
    def _load_user_settings(self):
        """Load user-specific settings from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_settings = json.load(f)
                self._merge_settings(user_settings)
            except Exception as e:
                print(f"Warning: Could not load user settings: {e}")
    
    def _merge_settings(self, user_settings: Dict[str, Any]):
        """Merge user settings with defaults"""
        for key, value in user_settings.items():
            if key in self.settings and isinstance(value, dict):
                self.settings[key].update(value)
            else:
                self.settings[key] = value
    
    def get(self, key_path: str, default=None):
        """Get setting value using dot notation (e.g., 'ui.window_width')"""
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set setting value using dot notation"""
        keys = key_path.split('.')
        target = self.settings
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
    
    def save(self):
        """Save current settings to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save settings: {e}")