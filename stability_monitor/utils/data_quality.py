"""
Data Quality Management utilities for duplicate detection and data filtering
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import logging

class DuplicateGroup:
    """Represents a group of potentially duplicate tickets"""
    
    def __init__(self, primary_ticket: pd.Series, duplicates: List[pd.Series], confidence_score: float):
        self.primary_ticket = primary_ticket
        self.duplicates = duplicates
        self.confidence_score = confidence_score
        self.review_status = "pending"  # pending, confirmed, dismissed
        self.manual_notes = ""
        
    def get_all_tickets(self) -> List[pd.Series]:
        """Get all tickets in this duplicate group"""
        return [self.primary_ticket] + self.duplicates
    
    def get_ticket_numbers(self) -> List[str]:
        """Get all ticket numbers in this group"""
        tickets = self.get_all_tickets()
        return [str(ticket.get('Number', 'N/A')) for ticket in tickets]

class DataQualityManager:
    """Manages data quality operations including filtering and duplicate detection"""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.site_filter_config = settings.get("data_quality.site_filter", {})
        self.duplicate_config = settings.get("data_quality.duplicate_detection", {})
        self.auto_review_config = settings.get("data_quality.auto_review", {})
    
    def apply_site_filter(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Apply site filtering to remove non-relevant sites
        Returns filtered dataframe and filter statistics
        """
        if not self.site_filter_config.get("enabled", False):
            return df, {"original_count": len(df), "filtered_count": len(df), "removed_count": 0}
        
        original_count = len(df)
        required_keywords = self.site_filter_config.get("required_keywords", ["wendy"])
        case_sensitive = self.site_filter_config.get("case_sensitive", False)
        
        # Create filter condition
        filter_mask = pd.Series([False] * len(df), index=df.index)
        
        for keyword in required_keywords:
            if case_sensitive:
                keyword_mask = df['Site'].str.contains(keyword, na=False)
            else:
                keyword_mask = df['Site'].str.contains(keyword, case=False, na=False)
            filter_mask |= keyword_mask
        
        # Apply filter
        filtered_df = df[filter_mask].copy()
        
        stats = {
            "original_count": original_count,
            "filtered_count": len(filtered_df),
            "removed_count": original_count - len(filtered_df),
            "filter_keywords": required_keywords,
            "sites_removed": df[~filter_mask]['Site'].nunique() if original_count > len(filtered_df) else 0
        }
        
        if stats["removed_count"] > 0:
            self.logger.info(f"Site filter removed {stats['removed_count']} tickets from {stats['sites_removed']} sites")
        
        return filtered_df, stats
    
    def detect_duplicates(self, df: pd.DataFrame) -> List[DuplicateGroup]:
        """
        Detect potential duplicate tickets using multi-factor analysis
        """
        if not self.duplicate_config.get("enabled", False):
            return []
        
        duplicate_groups = []
        priority_levels = self.duplicate_config.get("priority_levels", ["1 - Critical"])
        date_window_hours = self.duplicate_config.get("date_window_hours", 24)
        similarity_threshold = self.duplicate_config.get("similarity_threshold", 0.8)
        
        # Filter to only check specified priority levels
        target_df = df[df['Priority'].isin(priority_levels)].copy()
        
        if target_df.empty:
            return []
        
        # Sort by created date for efficient processing
        target_df = target_df.sort_values('Created')
        processed_indices = set()
        
        
        for idx, ticket in target_df.iterrows():
            if idx in processed_indices:
                continue
                
            # Find potential duplicates within time window
            potential_duplicates = self._find_potential_duplicates(ticket, target_df, date_window_hours)
            
            if potential_duplicates:
                # Calculate similarity scores
                scored_duplicates = []
                for dup_idx, dup_ticket in potential_duplicates:
                    if dup_idx not in processed_indices:
                        score = self._calculate_similarity_score(ticket, dup_ticket)
                        if score >= similarity_threshold:
                            scored_duplicates.append((dup_ticket, score))
                            processed_indices.add(dup_idx)
                
                if scored_duplicates:
                    # Create duplicate group
                    duplicates = [dup[0] for dup in scored_duplicates]
                    avg_confidence = np.mean([dup[1] for dup in scored_duplicates])
                    
                    duplicate_group = DuplicateGroup(
                        primary_ticket=ticket,
                        duplicates=duplicates,
                        confidence_score=avg_confidence
                    )
                    duplicate_groups.append(duplicate_group)
                    processed_indices.add(idx)
        
        self.logger.info(f"Detected {len(duplicate_groups)} potential duplicate groups")
        return duplicate_groups
    
    def _find_potential_duplicates(self, ticket: pd.Series, df: pd.DataFrame, 
                                 time_window_hours: int) -> List[Tuple[int, pd.Series]]:
        """Find tickets that could be duplicates based on basic criteria"""
        ticket_date = ticket['Created']
        ticket_site = ticket['Site']
        
        # Time window filter
        time_delta = timedelta(hours=time_window_hours)
        time_mask = (
            (df['Created'] >= ticket_date - time_delta) & 
            (df['Created'] <= ticket_date + time_delta)
        )
        
        # Site filter - duplicates are only detected within the same site
        # This ensures we only find true duplicates, not synchronized incidents across sites
        site_mask = df['Site'] == ticket_site
        
        # Exclude the ticket itself
        not_self_mask = df.index != ticket.name
        
        # Combine filters
        candidate_mask = time_mask & site_mask & not_self_mask
        candidates = df[candidate_mask]
        
        
        return [(idx, row) for idx, row in candidates.iterrows()]
    
    def _calculate_similarity_score(self, ticket1: pd.Series, ticket2: pd.Series) -> float:
        """
        Calculate similarity score between two tickets using weighted factors
        """
        weights = {
            'description': self.duplicate_config.get("description_weight", 0.6),  # Increased from 0.4
            'date': self.duplicate_config.get("date_weight", 0.3),                # Increased from 0.2
            'priority': self.duplicate_config.get("priority_weight", 0.1)          # Same
            # Note: Removed site weight as all duplicates are now same-site only
        }
        
        scores = {}
        
        # Description similarity (using sequence matching)
        desc1 = str(ticket1.get('Short description', '')).lower().strip()
        desc2 = str(ticket2.get('Short description', '')).lower().strip()
        if desc1 and desc2 and desc1 != 'nan' and desc2 != 'nan':
            scores['description'] = SequenceMatcher(None, desc1, desc2).ratio()
        else:
            scores['description'] = 0.0
        
        # Note: Site similarity removed - all duplicates are now same-site only
        
        # Date similarity (closer dates = higher score)
        date_diff = abs((ticket1['Created'] - ticket2['Created']).total_seconds())
        max_diff = self.duplicate_config.get("date_window_hours", 24) * 3600
        scores['date'] = max(0, 1 - (date_diff / max_diff))
        
        # Priority similarity (exact match)
        scores['priority'] = 1.0 if ticket1['Priority'] == ticket2['Priority'] else 0.0
        
        # Calculate weighted average (only for factors we actually computed)
        total_score = sum(scores[factor] * weights[factor] for factor in scores if factor in weights)
        final_score = min(1.0, max(0.0, total_score))
        
        
        return final_score
    
    def flag_potential_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add duplicate flags to the dataframe for visualization
        """
        df_flagged = df.copy()
        df_flagged['Duplicate_Flag'] = 'Clean'
        df_flagged['Duplicate_Confidence'] = 0.0
        df_flagged['Duplicate_Group_ID'] = None
        
        duplicate_groups = self.detect_duplicates(df)
        
        for group_id, group in enumerate(duplicate_groups):
            all_tickets = group.get_all_tickets()
            ticket_indices = [ticket.name for ticket in all_tickets]
            
            # Flag all tickets in the group
            for idx in ticket_indices:
                if idx in df_flagged.index:
                    if group.confidence_score >= self.auto_review_config.get("high_confidence_threshold", 0.95):
                        df_flagged.loc[idx, 'Duplicate_Flag'] = 'High Confidence Duplicate'
                    elif group.confidence_score >= self.auto_review_config.get("require_manual_review_threshold", 0.7):
                        df_flagged.loc[idx, 'Duplicate_Flag'] = 'Needs Manual Review'
                    else:
                        df_flagged.loc[idx, 'Duplicate_Flag'] = 'Low Confidence Duplicate'
                    
                    df_flagged.loc[idx, 'Duplicate_Confidence'] = group.confidence_score
                    df_flagged.loc[idx, 'Duplicate_Group_ID'] = group_id
        
        return df_flagged
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report
        """
        # Apply site filter
        filtered_df, filter_stats = self.apply_site_filter(df)
        
        # Detect duplicates
        duplicate_groups = self.detect_duplicates(filtered_df)
        
        # Calculate quality metrics
        total_tickets = len(filtered_df)
        duplicate_tickets = sum(len(group.get_all_tickets()) for group in duplicate_groups)
        
        quality_report = {
            "timestamp": datetime.now().isoformat(),
            "original_dataset": {
                "total_tickets": len(df),
                "unique_sites": df['Site'].nunique(),
                "date_range": {
                    "start": df['Created'].min().isoformat() if 'Created' in df.columns else None,
                    "end": df['Created'].max().isoformat() if 'Created' in df.columns else None
                }
            },
            "site_filtering": filter_stats,
            "duplicate_analysis": {
                "total_duplicate_groups": len(duplicate_groups),
                "tickets_affected": duplicate_tickets,
                "duplicate_percentage": (duplicate_tickets / total_tickets * 100) if total_tickets > 0 else 0,
                "high_confidence_groups": len([g for g in duplicate_groups 
                                             if g.confidence_score >= self.auto_review_config.get("high_confidence_threshold", 0.95)]),
                "manual_review_required": len([g for g in duplicate_groups 
                                             if g.confidence_score >= self.auto_review_config.get("require_manual_review_threshold", 0.7)])
            },
            "data_quality_score": self._calculate_quality_score(filtered_df, duplicate_groups),
            "recommendations": self._generate_recommendations(filtered_df, duplicate_groups, filter_stats)
        }
        
        return quality_report
    
    def _calculate_quality_score(self, df: pd.DataFrame, duplicate_groups: List[DuplicateGroup]) -> float:
        """
        Calculate overall data quality score (0-100)
        """
        if df.empty:
            return 0.0
        
        total_tickets = len(df)
        duplicate_tickets = sum(len(group.get_all_tickets()) for group in duplicate_groups)
        
        # Base score starts at 100
        quality_score = 100.0
        
        # Deduct points for duplicates
        duplicate_penalty = (duplicate_tickets / total_tickets) * 30  # Max 30 point penalty
        quality_score -= duplicate_penalty
        
        # Deduct points for missing critical data
        required_cols = ['Site', 'Priority', 'Created']
        for col in required_cols:
            if col in df.columns:
                null_percentage = (df[col].isna().sum() / total_tickets) * 100
                quality_score -= (null_percentage * 0.2)  # 0.2 points per % missing
        
        return max(0.0, min(100.0, quality_score))
    
    def _generate_recommendations(self, df: pd.DataFrame, duplicate_groups: List[DuplicateGroup], 
                                filter_stats: Dict[str, int]) -> List[str]:
        """
        Generate actionable recommendations based on data quality analysis
        """
        recommendations = []
        
        # Site filtering recommendations
        if filter_stats["removed_count"] > 0:
            recommendations.append(
                f"Site filter removed {filter_stats['removed_count']} tickets from "
                f"{filter_stats['sites_removed']} sites. Review filter criteria if needed."
            )
        
        # Duplicate recommendations
        if duplicate_groups:
            high_confidence = len([g for g in duplicate_groups 
                                 if g.confidence_score >= self.auto_review_config.get("high_confidence_threshold", 0.95)])
            
            if high_confidence > 0:
                recommendations.append(
                    f"{high_confidence} duplicate groups have high confidence scores and "
                    "can be automatically processed."
                )
            
            manual_review = len([g for g in duplicate_groups 
                               if g.confidence_score >= self.auto_review_config.get("require_manual_review_threshold", 0.7)])
            
            if manual_review > 0:
                recommendations.append(
                    f"{manual_review} duplicate groups require manual review. "
                    "Use the Data Quality tab to review and process these."
                )
        
        # Data completeness recommendations
        required_cols = ['Site', 'Priority', 'Created', 'Short description']
        for col in required_cols:
            if col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    percentage = (null_count / len(df)) * 100
                    recommendations.append(
                        f"Column '{col}' has {null_count} missing values ({percentage:.1f}%). "
                        "Consider data cleanup for better analysis accuracy."
                    )
        
        if not recommendations:
            recommendations.append("Data quality looks good! No major issues detected.")
        
        return recommendations