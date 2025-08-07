"""
System Stability Analytics for comprehensive stability metrics and benchmarking
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import logging

class StabilityMetrics:
    """Container for stability metrics and calculations"""
    
    def __init__(self):
        self.overall_stability_percentage = 0.0
        self.weighted_stability_score = 0.0
        self.stability_trend = "stable"  # improving, stable, declining
        self.benchmark_score = 0.0
        self.critical_incident_rate = 0.0
        self.mean_time_to_recovery = 0.0
        self.system_availability = 0.0
        self.site_performance_distribution = {}
        self.time_based_metrics = {}
        
        # Portfolio-wide metrics (new)
        self.portfolio_stability_percentage = 0.0  # % of total supported sites with no criticals
        self.total_supported_sites = 0
        self.sites_with_incidents = 0
        self.sites_with_critical_incidents = 0
        self.sites_with_zero_incidents = 0
        self.portfolio_coverage_percentage = 0.0  # % of supported sites that had any activity
        
class SystemStabilityAnalyzer:
    """Analyzes system-wide stability metrics and performance trends"""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.stability_config = settings.get("stability_analysis", {
            "excellent_threshold": 95.0,
            "good_threshold": 85.0,
            "acceptable_threshold": 70.0,
            "benchmark_targets": {
                "critical_rate_threshold": 5.0,  # % of tickets that should be critical
                "mttr_target_hours": 4.0,        # Target mean time to recovery
                "availability_target": 99.5       # Target system availability %
            },
            "trend_analysis_days": 30,
            "weight_by_volume": True
        })
    
    def _ensure_critical_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure Is_Critical column exists, create from Priority if needed"""
        if df.empty:
            return df
        
        df = df.copy()
        if 'Is_Critical' not in df.columns and 'Priority' in df.columns:
            df['Is_Critical'] = df['Priority'].str.contains('Critical', case=False, na=False)
        elif 'Is_Critical' not in df.columns:
            # If no Priority column either, create default False column
            df['Is_Critical'] = False
        
        return df
    
    def calculate_system_stability(self, df: pd.DataFrame) -> StabilityMetrics:
        """
        Calculate comprehensive system stability metrics
        """
        if df.empty:
            return StabilityMetrics()
        
        # Ensure Is_Critical column exists
        df = self._ensure_critical_column(df)
        
        metrics = StabilityMetrics()
        
        # Overall stability percentage (sites with no critical incidents / total sites)
        metrics.overall_stability_percentage = self._calculate_overall_stability_percentage(df)
        
        # Portfolio-wide stability metrics (NEW)
        self._calculate_portfolio_metrics(df, metrics)
        
        # Weighted stability score (considers ticket volumes per site)
        metrics.weighted_stability_score = self._calculate_weighted_stability_score(df)
        
        # Critical incident rate
        metrics.critical_incident_rate = self._calculate_critical_incident_rate(df)
        
        # Mean Time to Recovery (MTTR)
        metrics.mean_time_to_recovery = self._calculate_system_mttr(df)
        
        # System availability estimation
        metrics.system_availability = self._calculate_system_availability(df)
        
        # Stability trend analysis
        metrics.stability_trend = self._analyze_stability_trend(df)
        
        # Benchmark score against targets
        metrics.benchmark_score = self._calculate_benchmark_score(metrics)
        
        # Site performance distribution
        metrics.site_performance_distribution = self._analyze_site_performance_distribution(df)
        
        # Time-based metrics for trend analysis
        metrics.time_based_metrics = self._calculate_time_based_metrics(df)
        
        return metrics
    
    def _calculate_overall_stability_percentage(self, df: pd.DataFrame) -> float:
        """
        Calculate percentage of total supported sites with no critical incidents
        This now uses the configured total sites count for accurate portfolio metrics
        """
        if df.empty:
            # If no data, all supported sites are stable (perfect score)
            return 100.0
        
        # Get total supported sites from configuration
        total_supported_sites = self.settings.get("stability_analysis.total_supported_sites.count", 0)
        
        if total_supported_sites <= 0:
            # Fall back to old method if total sites not configured
            site_critical_counts = df.groupby('Site')['Is_Critical'].sum()
            stable_sites = (site_critical_counts == 0).sum()
            total_sites = len(site_critical_counts)
            return (stable_sites / total_sites * 100.0) if total_sites > 0 else 100.0
        
        # Count sites with critical incidents
        site_critical_counts = df.groupby('Site')['Is_Critical'].sum()
        sites_with_criticals = (site_critical_counts > 0).sum()
        
        # Calculate sites with NO critical incidents
        # Total supported sites minus sites that appear in data with criticals
        sites_with_no_criticals = total_supported_sites - sites_with_criticals
        
        # Portfolio stability percentage
        portfolio_stability = (sites_with_no_criticals / total_supported_sites) * 100.0
        
        return max(0.0, min(100.0, portfolio_stability))
    
    def _calculate_portfolio_metrics(self, df: pd.DataFrame, metrics: StabilityMetrics) -> None:
        """
        Calculate comprehensive portfolio-wide stability metrics
        Populates portfolio metrics fields in the provided metrics object
        """
        if df.empty:
            # Set default values for empty dataset
            metrics.total_supported_sites = self.settings.get("stability_analysis.total_supported_sites.count", 0)
            metrics.sites_with_incidents = 0
            metrics.sites_with_critical_incidents = 0
            metrics.sites_with_zero_incidents = metrics.total_supported_sites
            metrics.portfolio_coverage_percentage = 0.0
            metrics.portfolio_stability_percentage = 100.0
            return
        
        # Get total supported sites from configuration
        total_supported_sites = self.settings.get("stability_analysis.total_supported_sites.count", 0)
        metrics.total_supported_sites = total_supported_sites
        
        # Calculate site-based metrics from actual data
        site_stats = df.groupby('Site').agg({
            'Number': 'count',        # Total tickets per site
            'Is_Critical': 'sum'      # Critical tickets per site
        })
        
        # Sites that appear in the data (have any activity)
        sites_with_any_activity = set(site_stats.index)
        metrics.sites_with_incidents = len(sites_with_any_activity)
        
        # Sites with critical incidents
        sites_with_criticals = site_stats[site_stats['Is_Critical'] > 0]
        metrics.sites_with_critical_incidents = len(sites_with_criticals)
        
        # Calculate portfolio metrics
        if total_supported_sites > 0:
            # Sites with zero incidents = total supported - sites with criticals
            # This assumes sites not in data have zero incidents
            metrics.sites_with_zero_incidents = total_supported_sites - metrics.sites_with_critical_incidents
            
            # Portfolio coverage: what percentage of supported sites had any activity
            metrics.portfolio_coverage_percentage = (metrics.sites_with_incidents / total_supported_sites) * 100.0
            
            # Portfolio stability: what percentage of ALL supported sites have no critical incidents
            metrics.portfolio_stability_percentage = (metrics.sites_with_zero_incidents / total_supported_sites) * 100.0
        else:
            # Fall back to data-only calculations
            sites_without_criticals = site_stats[site_stats['Is_Critical'] == 0]
            metrics.sites_with_zero_incidents = len(sites_without_criticals)
            metrics.portfolio_coverage_percentage = 100.0  # All data sites are covered
            metrics.portfolio_stability_percentage = (len(sites_without_criticals) / len(sites_with_any_activity)) * 100.0 if len(sites_with_any_activity) > 0 else 100.0
        
        # Ensure values are within valid ranges
        metrics.portfolio_coverage_percentage = max(0.0, min(100.0, metrics.portfolio_coverage_percentage))
        metrics.portfolio_stability_percentage = max(0.0, min(100.0, metrics.portfolio_stability_percentage))
    
    def _calculate_weighted_stability_score(self, df: pd.DataFrame) -> float:
        """
        Calculate stability score weighted by site ticket volumes
        Sites with more tickets have more impact on the score
        """
        if not self.stability_config.get("weight_by_volume", True):
            return self._calculate_overall_stability_percentage(df)
        
        df = self._ensure_critical_column(df)
        
        site_stats = df.groupby('Site').agg({
            'Number': 'count',        # Total tickets per site
            'Is_Critical': 'sum'      # Critical tickets per site
        }).rename(columns={'Number': 'Total_Tickets', 'Is_Critical': 'Critical_Tickets'})
        
        if site_stats.empty:
            return 100.0
        
        # Calculate stability score per site (0-100)
        site_stats['Site_Stability'] = ((site_stats['Total_Tickets'] - site_stats['Critical_Tickets']) / 
                                       site_stats['Total_Tickets']) * 100
        
        # Weight by ticket volume
        total_tickets = site_stats['Total_Tickets'].sum()
        site_stats['Weight'] = site_stats['Total_Tickets'] / total_tickets
        
        # Calculate weighted average
        weighted_score = (site_stats['Site_Stability'] * site_stats['Weight']).sum()
        
        return weighted_score
    
    def _calculate_critical_incident_rate(self, df: pd.DataFrame) -> float:
        """Calculate percentage of tickets that are critical"""
        if df.empty:
            return 0.0
        
        df = self._ensure_critical_column(df)
        return (df['Is_Critical'].sum() / len(df)) * 100.0
    
    def _calculate_system_mttr(self, df: pd.DataFrame) -> float:
        """Calculate system-wide Mean Time to Recovery"""
        if 'Resolution_Hours' not in df.columns:
            return 0.0
        
        resolved_tickets = df[df['Is_Resolved'] == True]
        if resolved_tickets.empty:
            return 0.0
        
        return resolved_tickets['Resolution_Hours'].mean()
    
    def _calculate_system_availability(self, df: pd.DataFrame) -> float:
        """
        Estimate system availability based on critical incident patterns
        Simplified calculation: assumes critical incidents indicate downtime
        """
        if df.empty:
            return 100.0
        
        # Get time span of data
        if 'Created' not in df.columns:
            return 100.0
        
        df = self._ensure_critical_column(df)
        
        date_range = df['Created'].max() - df['Created'].min()
        total_hours = date_range.total_seconds() / 3600 if date_range.total_seconds() > 0 else 1
        
        # Calculate downtime from critical incidents
        critical_incidents = df[df['Is_Critical'] == True]
        
        if critical_incidents.empty:
            return 100.0
        
        # Estimate downtime: assume each critical incident causes 1 hour downtime if not resolved
        # If resolved, use actual resolution time
        total_downtime_hours = 0
        
        for _, incident in critical_incidents.iterrows():
            if incident.get('Is_Resolved', False) and pd.notna(incident.get('Resolution_Hours')):
                downtime = min(incident['Resolution_Hours'], 24)  # Cap at 24 hours per incident
            else:
                downtime = 1.0  # Assume 1 hour for unresolved critical incidents
            
            total_downtime_hours += downtime
        
        # Calculate availability percentage
        uptime_hours = max(0, total_hours - total_downtime_hours)
        availability = (uptime_hours / total_hours) * 100 if total_hours > 0 else 100.0
        
        return min(100.0, max(0.0, availability))
    
    def _analyze_stability_trend(self, df: pd.DataFrame) -> str:
        """
        Analyze stability trend over time
        Returns: 'improving', 'stable', 'declining'
        """
        if df.empty or 'Created' not in df.columns:
            return 'stable'
        
        df = self._ensure_critical_column(df)
        
        trend_days = self.stability_config.get("trend_analysis_days", 30)
        
        # Get data from last trend_days period
        cutoff_date = df['Created'].max() - timedelta(days=trend_days)
        recent_data = df[df['Created'] >= cutoff_date]
        
        if recent_data.empty or len(recent_data) < 10:  # Need minimum data for trend
            return 'stable'
        
        # Split into two halves for comparison
        midpoint_date = cutoff_date + timedelta(days=trend_days/2)
        first_half = recent_data[recent_data['Created'] < midpoint_date]
        second_half = recent_data[recent_data['Created'] >= midpoint_date]
        
        if first_half.empty or second_half.empty:
            return 'stable'
        
        # Compare critical incident rates
        first_half_critical_rate = (first_half['Is_Critical'].sum() / len(first_half)) * 100
        second_half_critical_rate = (second_half['Is_Critical'].sum() / len(second_half)) * 100
        
        # Calculate improvement/degradation
        change = second_half_critical_rate - first_half_critical_rate
        
        if change < -2.0:  # Significant improvement (less critical incidents)
            return 'improving'
        elif change > 2.0:   # Significant degradation (more critical incidents) 
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_benchmark_score(self, metrics: StabilityMetrics) -> float:
        """
        Calculate benchmark score against industry targets
        Returns score from 0-100 based on how well metrics meet targets
        """
        targets = self.stability_config.get("benchmark_targets", {})
        
        scores = []
        
        # Critical rate score (lower is better)
        critical_target = targets.get("critical_rate_threshold", 5.0)
        if metrics.critical_incident_rate <= critical_target:
            critical_score = 100.0
        else:
            # Penalty for exceeding target
            excess = metrics.critical_incident_rate - critical_target
            critical_score = max(0, 100 - (excess * 5))  # 5 points per % over target
        scores.append(critical_score)
        
        # MTTR score (lower is better)  
        mttr_target = targets.get("mttr_target_hours", 4.0)
        if metrics.mean_time_to_recovery > 0:
            if metrics.mean_time_to_recovery <= mttr_target:
                mttr_score = 100.0
            else:
                # Penalty for exceeding target
                excess_ratio = metrics.mean_time_to_recovery / mttr_target
                mttr_score = max(0, 100 - ((excess_ratio - 1) * 50))
            scores.append(mttr_score)
        
        # Availability score (higher is better)
        availability_target = targets.get("availability_target", 99.5)
        if metrics.system_availability >= availability_target:
            availability_score = 100.0
        else:
            # Penalty for missing target
            shortfall = availability_target - metrics.system_availability
            availability_score = max(0, 100 - (shortfall * 20))  # 20 points per % below target
        scores.append(availability_score)
        
        # Overall stability score
        if metrics.weighted_stability_score >= 95:
            stability_score = 100.0
        elif metrics.weighted_stability_score >= 85:
            stability_score = 80.0
        elif metrics.weighted_stability_score >= 70:
            stability_score = 60.0
        else:
            stability_score = max(0, metrics.weighted_stability_score * 0.5)
        scores.append(stability_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _analyze_site_performance_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distribution of site performance levels"""
        df = self._ensure_critical_column(df)
        
        site_stats = df.groupby('Site').agg({
            'Number': 'count',
            'Is_Critical': 'sum'
        }).rename(columns={'Number': 'Total_Tickets', 'Is_Critical': 'Critical_Tickets'})
        
        if site_stats.empty:
            return {}
        
        # Calculate site stability percentages
        site_stats['Stability_Percent'] = ((site_stats['Total_Tickets'] - site_stats['Critical_Tickets']) / 
                                          site_stats['Total_Tickets']) * 100
        
        # Categorize sites
        excellent = (site_stats['Stability_Percent'] >= 95).sum()
        good = ((site_stats['Stability_Percent'] >= 85) & 
                (site_stats['Stability_Percent'] < 95)).sum()
        acceptable = ((site_stats['Stability_Percent'] >= 70) & 
                     (site_stats['Stability_Percent'] < 85)).sum()
        needs_attention = (site_stats['Stability_Percent'] < 70).sum()
        
        total_sites = len(site_stats)
        
        return {
            "total_sites": total_sites,
            "distribution": {
                "excellent": {"count": excellent, "percentage": (excellent/total_sites)*100 if total_sites > 0 else 0},
                "good": {"count": good, "percentage": (good/total_sites)*100 if total_sites > 0 else 0},
                "acceptable": {"count": acceptable, "percentage": (acceptable/total_sites)*100 if total_sites > 0 else 0},
                "needs_attention": {"count": needs_attention, "percentage": (needs_attention/total_sites)*100 if total_sites > 0 else 0}
            },
            "top_performers": site_stats.nlargest(5, 'Stability_Percent').index.tolist(),
            "needs_improvement": site_stats.nsmallest(5, 'Stability_Percent').index.tolist()
        }
    
    def _calculate_time_based_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate time-based metrics for trend visualization"""
        if df.empty or 'Created' not in df.columns:
            return {}
        
        df = self._ensure_critical_column(df)
        
        # Daily metrics for last 30 days
        df_copy = df.copy()
        df_copy['Date'] = df_copy['Created'].dt.date
        
        # Create Is_Resolved column if it doesn't exist
        if 'Is_Resolved' not in df_copy.columns:
            df_copy['Is_Resolved'] = df_copy['Resolved'].notna()
        
        daily_metrics = df_copy.groupby('Date').agg({
            'Number': 'count',
            'Is_Critical': 'sum',
            'Is_Resolved': 'sum'
        }).rename(columns={
            'Number': 'Total_Tickets',
            'Is_Critical': 'Critical_Tickets', 
            'Is_Resolved': 'Resolved_Tickets'
        })
        
        daily_metrics['Critical_Rate'] = (daily_metrics['Critical_Tickets'] / 
                                         daily_metrics['Total_Tickets'] * 100).fillna(0)
        
        # Weekly aggregation
        df_copy['Week'] = df_copy['Created'].dt.to_period('W').dt.start_time
        weekly_metrics = df_copy.groupby('Week').agg({
            'Number': 'count',
            'Is_Critical': 'sum',
            'Is_Resolved': 'sum'
        }).rename(columns={
            'Number': 'Total_Tickets',
            'Is_Critical': 'Critical_Tickets',
            'Is_Resolved': 'Resolved_Tickets'
        })
        
        weekly_metrics['Critical_Rate'] = (weekly_metrics['Critical_Tickets'] / 
                                          weekly_metrics['Total_Tickets'] * 100).fillna(0)
        
        return {
            "daily_trends": {
                "dates": [str(date) for date in daily_metrics.index.tolist()],
                "critical_rates": daily_metrics['Critical_Rate'].tolist(),
                "total_tickets": daily_metrics['Total_Tickets'].tolist()
            },
            "weekly_trends": {
                "weeks": [str(week) for week in weekly_metrics.index.tolist()],
                "critical_rates": weekly_metrics['Critical_Rate'].tolist(),
                "total_tickets": weekly_metrics['Total_Tickets'].tolist()
            }
        }
    
    def generate_stability_insights(self, metrics: StabilityMetrics) -> List[str]:
        """Generate actionable insights based on stability metrics"""
        insights = []
        
        # Portfolio-wide stability insights (NEW)
        if metrics.total_supported_sites > 0:
            if metrics.portfolio_stability_percentage >= 95:
                insights.append(f"🟢 Excellent portfolio stability: {metrics.portfolio_stability_percentage:.1f}% of all {metrics.total_supported_sites} supported sites have zero critical incidents")
            elif metrics.portfolio_stability_percentage >= 85:
                insights.append(f"🟡 Good portfolio stability: {metrics.portfolio_stability_percentage:.1f}% of {metrics.total_supported_sites} supported sites stable, but {metrics.sites_with_critical_incidents} sites need attention")
            else:
                insights.append(f"🔴 Portfolio stability needs immediate attention: Only {metrics.portfolio_stability_percentage:.1f}% of {metrics.total_supported_sites} supported sites are stable")
            
            # Coverage insights
            if metrics.portfolio_coverage_percentage < 50:
                insights.append(f"📊 Data coverage: Only {metrics.sites_with_incidents} of {metrics.total_supported_sites} sites ({metrics.portfolio_coverage_percentage:.1f}%) had activity - most sites stable with zero incidents")
            elif metrics.portfolio_coverage_percentage > 80:
                insights.append(f"⚠️ High activity portfolio: {metrics.sites_with_incidents} of {metrics.total_supported_sites} sites ({metrics.portfolio_coverage_percentage:.1f}%) had incidents - investigate underlying issues")
        else:
            # Fall back to original insights for backward compatibility
            if metrics.overall_stability_percentage >= 95:
                insights.append("🟢 Excellent system stability with 95%+ of sites running without critical incidents")
            elif metrics.overall_stability_percentage >= 85:
                insights.append("🟡 Good system stability, but some sites experiencing critical issues")
            else:
                insights.append("🔴 System stability needs attention with multiple sites having critical incidents")
        
        # Weighted score insights
        if abs(metrics.weighted_stability_score - metrics.overall_stability_percentage) > 10:
            if metrics.weighted_stability_score < metrics.overall_stability_percentage:
                insights.append("⚠️ High-volume sites are disproportionately affected by critical incidents")
            else:
                insights.append("✅ Critical incidents are concentrated in lower-volume sites")
        
        # Critical rate insights
        if metrics.critical_incident_rate > 10:
            insights.append(f"🚨 High critical incident rate ({metrics.critical_incident_rate:.1f}%) - investigate root causes")
        elif metrics.critical_incident_rate < 2:
            insights.append("✅ Very low critical incident rate indicates stable operations")
        
        # MTTR insights
        if metrics.mean_time_to_recovery > 8:
            insights.append(f"⏱️ Long resolution times ({metrics.mean_time_to_recovery:.1f}h) - review response processes")
        elif metrics.mean_time_to_recovery < 2:
            insights.append("⚡ Excellent response times for incident resolution")
        
        # Availability insights  
        if metrics.system_availability < 99:
            insights.append(f"📉 System availability ({metrics.system_availability:.1f}%) below industry standards")
        elif metrics.system_availability > 99.5:
            insights.append("🎯 Excellent system availability exceeding industry standards")
        
        # Trend insights
        if metrics.stability_trend == 'improving':
            insights.append("📈 Positive trend: System stability is improving over time")
        elif metrics.stability_trend == 'declining':
            insights.append("📉 Concerning trend: System stability is declining - immediate action needed")
        else:
            insights.append("➡️ Stable trend: System performance is consistent")
        
        # Benchmark insights
        if metrics.benchmark_score >= 90:
            insights.append("🏆 Performance exceeds industry benchmarks")
        elif metrics.benchmark_score < 60:
            insights.append("📊 Performance below industry benchmarks - review best practices")
        
        return insights[:8]  # Limit to top 8 insights