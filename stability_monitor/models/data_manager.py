"""
Data loading, validation, and management
"""

import pandas as pd
import os
from typing import Dict, List, Optional, Tuple, Any
from ..utils.date_parser import DateParser
from ..utils.validators import DataValidator

class DataManager:
    """Manages data loading, validation, and preprocessing"""
    
    def __init__(self, settings):
        self.settings = settings
        self.data = None
        self.original_data = None
        self.date_parser = DateParser(settings.get("data.date_formats"))
        self.validator = DataValidator(settings.get("data.required_columns"))
        self.category_mapping = {}
        self.metadata = {}
    
    def load_file(self, file_path: str, column_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Load data from CSV or Excel file"""
        try:
            # Determine file type and load
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Please use CSV or Excel files.")
            
            # Apply column mapping if provided
            if column_mapping:
                df = df.rename(columns=column_mapping)
            
            # Store original data
            self.original_data = df.copy()
            
            # Validate data
            validation_results = self.validator.validate_dataframe(df)
            
            if not validation_results["valid"]:
                return validation_results
            
            # Process and clean data
            df = self._preprocess_data(df)
            
            # Build category-subcategory mapping
            self._build_category_mapping(df)
            
            # Store processed data
            self.data = df
            
            # Update metadata
            self._update_metadata(df, file_path)
            
            # Add success info to validation results
            validation_results["info"]["processed_records"] = len(df)
            validation_results["info"]["date_range"] = self._get_date_range(df)
            validation_results["info"]["categories"] = len(self.category_mapping)
            validation_results["info"]["sites"] = df["Site"].nunique()
            validation_results["info"]["companies"] = df["Company"].nunique()
            
            return validation_results
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Failed to load file: {str(e)}"],
                "warnings": [],
                "info": {},
                "data_quality": {}
            }
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the data"""
        df = df.copy()
        
        # Parse date columns
        for date_col in ["Created", "Resolved"]:
            if date_col in df.columns:
                df[date_col] = self.date_parser.parse_series(df[date_col])
        
        # Standardize priority values
        if "Priority" in df.columns:
            df["Priority"] = df["Priority"].astype(str).str.strip()
        
        # Clean text columns
        text_columns = ["Site", "Company", "Category", "Subcategory", "Short description"]
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
        
        # Calculate resolution time in hours for resolved tickets
        if "Created" in df.columns and "Resolved" in df.columns:
            mask = df["Resolved"].notna() & df["Created"].notna()
            df.loc[mask, "Resolution_Hours"] = (
                df.loc[mask, "Resolved"] - df.loc[mask, "Created"]
            ).dt.total_seconds() / 3600
        
        # Add derived columns
        df["Is_Critical"] = df["Priority"] == "1 - Critical"
        df["Is_Resolved"] = df["Resolved"].notna()
        
        # Calculate days since created
        df["Days_Since_Created"] = (
            pd.Timestamp.now() - df["Created"]
        ).dt.days
        
        return df
    
    def _build_category_mapping(self, df: pd.DataFrame):
        """Build dynamic category-subcategory mapping from actual data"""
        self.category_mapping = {}
        
        if "Category" in df.columns and "Subcategory" in df.columns:
            # Group by category and collect unique subcategories
            grouped = df.groupby("Category")["Subcategory"].apply(
                lambda x: sorted(x.dropna().unique())
            ).to_dict()
            
            # Clean up empty categories
            self.category_mapping = {
                k: v for k, v in grouped.items() 
                if k and str(k).strip() and str(k) != 'nan'
            }
    
    def _update_metadata(self, df: pd.DataFrame, file_path: str):
        """Update dataset metadata"""
        self.metadata = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "load_timestamp": pd.Timestamp.now(),
            "total_records": len(df),
            "columns": list(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum(),
        }
    
    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get date range information from the dataset"""
        date_info = {}
        
        for date_col in ["Created", "Resolved"]:
            if date_col in df.columns:
                valid_dates = df[date_col].dropna()
                if not valid_dates.empty:
                    date_info[date_col] = {
                        "min": valid_dates.min(),
                        "max": valid_dates.max(),
                        "count": len(valid_dates)
                    }
        
        return date_info
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get available filter options from current data"""
        if self.data is None:
            return {}
        
        options = {}
        
        # Priority options
        if "Priority" in self.data.columns:
            options["Priority"] = sorted(self.data["Priority"].dropna().unique())
        
        # Company options
        if "Company" in self.data.columns:
            options["Company"] = sorted(self.data["Company"].dropna().unique())
        
        # Site options
        if "Site" in self.data.columns:
            options["Site"] = sorted(self.data["Site"].dropna().unique())
        
        # Category options
        options["Category"] = list(self.category_mapping.keys())
        
        return options
    
    def get_subcategories(self, category: str) -> List[str]:
        """Get subcategories for a specific category"""
        return self.category_mapping.get(category, [])
    
    def apply_filters(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to the data and return filtered dataframe"""
        if self.data is None:
            return pd.DataFrame()
        
        df = self.data.copy()
        
        # Date range filter
        if filters.get("date_from") and "Created" in df.columns:
            df = df[df["Created"] >= pd.to_datetime(filters["date_from"])]
        
        if filters.get("date_to") and "Created" in df.columns:
            df = df[df["Created"] <= pd.to_datetime(filters["date_to"])]
        
        # Priority filter
        if filters.get("priorities"):
            df = df[df["Priority"].isin(filters["priorities"])]
        
        # Company filter
        if filters.get("company") and filters["company"] != "All":
            df = df[df["Company"] == filters["company"]]
        
        # Site filter
        if filters.get("site") and filters["site"] != "All":
            df = df[df["Site"] == filters["site"]]
        
        # Category filter
        if filters.get("category") and filters["category"] != "All":
            df = df[df["Category"] == filters["category"]]
        
        # Subcategory filter
        if filters.get("subcategory") and filters["subcategory"] != "All":
            df = df[df["Subcategory"] == filters["subcategory"]]
        
        # Resolution status filter
        if filters.get("resolution_status"):
            if filters["resolution_status"] == "Open":
                df = df[df["Is_Resolved"] == False]
            elif filters["resolution_status"] == "Resolved":
                df = df[df["Is_Resolved"] == True]
        
        return df
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of current dataset"""
        if self.data is None:
            return {}
        
        df = self.data
        
        summary = {
            "total_tickets": len(df),
            "critical_tickets": df["Is_Critical"].sum(),
            "resolved_tickets": df["Is_Resolved"].sum(),
            "open_tickets": (~df["Is_Resolved"]).sum(),
            "unique_sites": df["Site"].nunique(),
            "unique_companies": df["Company"].nunique(),
            "date_range": self._get_date_range(df),
            "avg_resolution_hours": df["Resolution_Hours"].dropna().mean() if "Resolution_Hours" in df.columns else None
        }
        
        return summary