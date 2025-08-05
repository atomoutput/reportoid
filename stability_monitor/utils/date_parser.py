"""
Date parsing utilities for flexible date format handling
"""

from datetime import datetime
from dateutil.parser import parse as dateutil_parse
from typing import Optional, List
import pandas as pd

class DateParser:
    """Handles parsing of various date formats"""
    
    def __init__(self, date_formats: List[str] = None):
        self.date_formats = date_formats or [
            "%m/%d/%Y %H:%M",
            "%Y-%m-%d %H:%M:%S", 
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M",
            "%m-%d-%Y %H:%M",
            "%m-%d-%Y"
        ]
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse a date string using multiple format attempts"""
        if pd.isna(date_str) or not str(date_str).strip():
            return None
            
        date_str = str(date_str).strip()
        
        # Try predefined formats first (faster)
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Fall back to dateutil parser (more flexible but slower)
        try:
            return dateutil_parse(date_str)
        except (ValueError, TypeError):
            return None
    
    def parse_series(self, series: pd.Series) -> pd.Series:
        """Parse a pandas Series of date strings"""
        return series.apply(self.parse_date)
    
    def detect_format(self, date_strings: List[str], sample_size: int = 100) -> Optional[str]:
        """Detect the most likely date format from a sample"""
        if not date_strings:
            return None
        
        # Take a sample for format detection
        sample = date_strings[:sample_size]
        format_scores = {}
        
        for fmt in self.date_formats:
            success_count = 0
            for date_str in sample:
                try:
                    datetime.strptime(str(date_str).strip(), fmt)
                    success_count += 1
                except (ValueError, TypeError):
                    continue
            
            if success_count > 0:
                format_scores[fmt] = success_count / len(sample)
        
        if format_scores:
            best_format = max(format_scores.items(), key=lambda x: x[1])
            if best_format[1] > 0.8:  # 80% success rate
                return best_format[0]
        
        return None