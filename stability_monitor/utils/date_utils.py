"""
Date formatting utilities
Provides consistent and safe date formatting across the application
"""

import pandas as pd
from datetime import datetime
from typing import Union, Optional


def safe_strftime(date_value: Union[datetime, pd.Timestamp, str, None], 
                  format_str: str = "%Y-%m-%d %H:%M",
                  fallback: str = "N/A") -> str:
    """
    Safely format datetime objects with proper null/NaT handling
    
    Args:
        date_value: The date value to format (can be datetime, pd.Timestamp, str, or None)
        format_str: The format string to use (default: "%Y-%m-%d %H:%M")
        fallback: The fallback string for invalid/null values (default: "N/A")
        
    Returns:
        Formatted date string or fallback value
    """
    # Handle None and NaT cases
    if date_value is None or (hasattr(date_value, 'isna') and date_value.isna()):
        return fallback
    
    # Handle pandas NaT specifically
    if pd.isna(date_value) or str(date_value) == 'NaT':
        return fallback
    
    # Try to format if it has strftime method
    if hasattr(date_value, 'strftime'):
        try:
            return date_value.strftime(format_str)
        except (ValueError, AttributeError, TypeError):
            return fallback
    
    # If it's a string, try to parse it first
    if isinstance(date_value, str):
        try:
            # Try common date parsing
            parsed_date = pd.to_datetime(date_value)
            if pd.isna(parsed_date):
                return fallback
            return parsed_date.strftime(format_str)
        except (ValueError, TypeError):
            return fallback
    
    # Last resort: convert to string
    return str(date_value) if date_value is not None else fallback


def safe_date_display(date_value: Union[datetime, pd.Timestamp, str, None]) -> str:
    """
    Format date for display in UI components
    Uses standard display format: YYYY-MM-DD HH:MM
    """
    return safe_strftime(date_value, "%Y-%m-%d %H:%M", "N/A")


def safe_date_export(date_value: Union[datetime, pd.Timestamp, str, None]) -> str:
    """
    Format date for export to Excel/CSV
    Uses export-friendly format: YYYY-MM-DD HH:MM:SS
    """
    return safe_strftime(date_value, "%Y-%m-%d %H:%M:%S", "")


def safe_date_compact(date_value: Union[datetime, pd.Timestamp, str, None]) -> str:
    """
    Format date in compact format for space-constrained displays
    Uses compact format: MM/DD/YY HH:MM
    """
    return safe_strftime(date_value, "%m/%d/%y %H:%M", "N/A")


def validate_date_column(df: pd.DataFrame, column_name: str) -> dict:
    """
    Validate a date column and provide statistics
    
    Args:
        df: The DataFrame to check
        column_name: The name of the date column
        
    Returns:
        Dictionary with validation results and statistics
    """
    if column_name not in df.columns:
        return {
            "valid": False,
            "error": f"Column '{column_name}' not found",
            "null_count": 0,
            "valid_count": 0,
            "invalid_count": 0
        }
    
    column = df[column_name]
    null_count = column.isna().sum()
    total_count = len(column)
    
    valid_dates = 0
    invalid_dates = 0
    
    for value in column.dropna():
        try:
            if hasattr(value, 'strftime'):
                valid_dates += 1
            elif isinstance(value, str) and value.strip():
                pd.to_datetime(value)  # Try to parse
                valid_dates += 1
            else:
                invalid_dates += 1
        except (ValueError, TypeError):
            invalid_dates += 1
    
    return {
        "valid": True,
        "null_count": null_count,
        "valid_count": valid_dates,
        "invalid_count": invalid_dates,
        "total_count": total_count,
        "null_percentage": (null_count / total_count) * 100 if total_count > 0 else 0,
        "valid_percentage": (valid_dates / total_count) * 100 if total_count > 0 else 0
    }