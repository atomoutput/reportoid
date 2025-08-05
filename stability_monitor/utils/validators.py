"""
Data validation utilities
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional

class DataValidator:
    """Validates and reports on data quality"""
    
    def __init__(self, required_columns: List[str] = None):
        self.required_columns = required_columns or ["Site", "Priority", "Created", "Company"]
        self.priority_values = ["1 - Critical", "2 - High", "3 - Medium", "4 - Low"]
    
    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, any]:
        """Comprehensive validation of the loaded dataframe"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {},
            "data_quality": {}
        }
        
        # Check required columns
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            results["valid"] = False
            results["errors"].append(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Check for empty dataframe
        if df.empty:
            results["valid"] = False
            results["errors"].append("No data found in file")
            return results
        
        # Data quality metrics
        total_rows = len(df)
        results["info"]["total_records"] = total_rows
        results["info"]["columns"] = list(df.columns)
        
        # Check data completeness
        for col in self.required_columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                null_pct = (null_count / total_rows) * 100
                results["data_quality"][col] = {
                    "null_count": int(null_count),
                    "null_percentage": round(null_pct, 1),
                    "completeness": round(100 - null_pct, 1)
                }
                
                if null_pct > 10:
                    results["warnings"].append(f"Column '{col}' has {null_pct:.1f}% missing values")
        
        # Validate priority values
        if "Priority" in df.columns:
            invalid_priorities = df[~df["Priority"].isin(self.priority_values + [None])]["Priority"].unique()
            if len(invalid_priorities) > 0:
                results["warnings"].append(f"Unexpected priority values found: {list(invalid_priorities)}")
        
        # Check for duplicate tickets
        if "Number" in df.columns:
            duplicates = df[df["Number"].duplicated()]["Number"].nunique()
            if duplicates > 0:
                results["warnings"].append(f"Found {duplicates} duplicate ticket numbers")
        
        # Date validation info
        for date_col in ["Created", "Resolved"]:
            if date_col in df.columns:
                valid_dates = pd.to_datetime(df[date_col], errors='coerce').notna().sum()
                invalid_dates = total_rows - valid_dates
                if invalid_dates > 0:
                    results["warnings"].append(f"Column '{date_col}' has {invalid_dates} invalid date formats")
        
        return results
    
    def get_column_mapping_suggestions(self, df_columns: List[str]) -> Dict[str, str]:
        """Suggest column mappings for non-standard column names"""
        mapping_suggestions = {}
        
        # Common alternative column names
        column_alternatives = {
            "Site": ["site", "location", "store", "branch", "facility"],
            "Priority": ["priority", "severity", "level", "urgency"],
            "Created": ["created", "opened", "start", "date_created", "created_date"],
            "Resolved": ["resolved", "closed", "completed", "end", "date_resolved"],
            "Company": ["company", "franchise", "owner", "organization"],
            "Category": ["category", "type", "issue_type", "problem_type"],
            "Subcategory": ["subcategory", "subtype", "sub_category", "detail_type"]
        }
        
        df_columns_lower = [col.lower() for col in df_columns]
        
        for standard_col, alternatives in column_alternatives.items():
            if standard_col not in df_columns:
                for alt in alternatives:
                    if alt in df_columns_lower:
                        actual_col = df_columns[df_columns_lower.index(alt)]
                        mapping_suggestions[actual_col] = standard_col
                        break
        
        return mapping_suggestions