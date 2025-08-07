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
            "data_quality": {
                "site_filter": {
                    "enabled": True,
                    "required_keywords": ["wendy"],
                    "case_sensitive": False,
                    "filter_stats": True
                },
                "duplicate_detection": {
                    "enabled": True,
                    "similarity_threshold": 0.7,      # Lowered from 0.8 due to better focus
                    "date_window_hours": 24,
                    "priority_levels": ["1 - Critical", "2 - High"],  # Expanded scope
                    "description_weight": 0.6,        # Increased from 0.4
                    "date_weight": 0.3,               # Increased from 0.2  
                    "priority_weight": 0.1            # Same
                    # Note: Removed site_weight - duplicates are site-specific only
                },
                "auto_review": {
                    "high_confidence_threshold": 0.95,
                    "require_manual_review_threshold": 0.7
                }
            },
            "stability_analysis": {
                "excellent_threshold": 95.0,
                "good_threshold": 85.0,
                "acceptable_threshold": 70.0,
                "benchmark_targets": {
                    "critical_rate_threshold": 5.0,
                    "mttr_target_hours": 4.0,
                    "availability_target": 99.5
                },
                "trend_analysis_days": 30,
                "weight_by_volume": True,
                "total_supported_sites": {
                    "enabled": True,
                    "count": 250,  # Default: 250 total sites under support
                    "last_updated": None,
                    "notes": "Total number of sites under IT support coverage"
                }
            },
            "pattern_analysis": {
                "sync_time_window_minutes": 30,
                "min_sites_for_sync": 2,
                "correlation_threshold": 0.6,
                "recurring_pattern_days": 7,
                "seasonal_analysis_weeks": 12,
                "cluster_epsilon": 0.5,
                "min_incidents_for_pattern": 3
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