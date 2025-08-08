"""
Time Pattern Recognition Engine for detecting synchronized incidents and temporal patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import logging

class TemporalPattern:
    """Represents a temporal pattern in incident data"""
    
    def __init__(self, pattern_type: str, sites: List[str], confidence: float, 
                 time_window: Tuple[datetime, datetime], description: str):
        self.pattern_type = pattern_type  # 'synchronized', 'recurring', 'seasonal'
        self.sites = sites
        self.confidence = confidence
        self.time_window = time_window
        self.description = description
        self.incident_count = 0
        self.affected_categories = []
        self.severity_distribution = {}

class SynchronizedIncident:
    """Represents incidents that occurred across multiple sites simultaneously"""
    
    def __init__(self, timestamp: datetime, sites: List[str], incidents: List[Dict], 
                 correlation_score: float, time_window_minutes: int):
        self.timestamp = timestamp
        self.sites = sites
        self.incidents = incidents
        self.correlation_score = correlation_score
        self.time_window_minutes = time_window_minutes
        self.incident_categories = list(set([inc.get('Category', 'Unknown') for inc in incidents]))
        self.likely_root_cause = self._determine_likely_root_cause()
    
    def _determine_likely_root_cause(self) -> str:
        """Analyze incidents to suggest likely root cause"""
        categories = [inc.get('Category', '').lower() for inc in self.incidents]
        
        # Network/connectivity issues
        if any('network' in cat or 'connectivity' in cat or 'internet' in cat for cat in categories):
            return "Network/Connectivity Issue"
        
        # Server/infrastructure issues
        if any('server' in cat or 'system' in cat or 'infrastructure' in cat for cat in categories):
            return "Infrastructure/Server Issue"
        
        # POS system issues
        if any('pos' in cat or 'terminal' in cat or 'payment' in cat for cat in categories):
            return "POS System Issue"
        
        # Power/facility issues
        if any('power' in cat or 'electrical' in cat or 'facility' in cat for cat in categories):
            return "Power/Facility Issue"
        
        return "Unknown - Requires Investigation"

class TimePatternEngine:
    """Analyzes temporal patterns and synchronized incidents in ticket data"""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.pattern_config = settings.get("pattern_analysis", {
            "sync_time_window_minutes": 5,       # Default tight window
            "min_sites_for_sync": 2,             # Minimum sites for synchronized pattern
            "correlation_threshold": 0.6,        # Minimum correlation for pattern detection
            "recurring_pattern_days": 7,         # Look for weekly recurring patterns
            "seasonal_analysis_weeks": 12,       # Weeks to analyze for seasonal patterns
            "cluster_epsilon": 0.5,              # Clustering parameter (unused without sklearn)
            "min_incidents_for_pattern": 3       # Minimum incidents to establish pattern
        })
        
        # Enhanced multi-window configuration
        self.sync_windows = self.pattern_config.get("sync_time_windows", {})
        self.enable_multi_window = self.pattern_config.get("enable_multi_window_analysis", True)
        self.advanced_correlation = self.pattern_config.get("advanced_correlation_scoring", True)
    
    def analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive temporal pattern analysis
        Returns dictionary with various pattern types and insights
        """
        if df.empty or 'Created' not in df.columns:
            return {}
        
        results = {
            "synchronized_incidents": self._detect_synchronized_incidents(df),
            "recurring_patterns": self._detect_recurring_patterns(df),
            "time_correlation_matrix": self._calculate_site_correlation_matrix(df),
            "peak_incident_times": self._analyze_peak_incident_times(df),
            "seasonal_patterns": self._detect_seasonal_patterns(df),
            "anomaly_detection": self._detect_temporal_anomalies(df),
            "pattern_insights": []
        }
        
        # Generate insights based on patterns found
        results["pattern_insights"] = self._generate_pattern_insights(results)
        
        return results
    
    def _detect_synchronized_incidents(self, df: pd.DataFrame) -> List[SynchronizedIncident]:
        """
        Enhanced synchronized incident detection with configurable time windows
        """
        sync_incidents = []
        
        if df.empty:
            return []
        
        # If multi-window analysis is enabled, use enhanced detection
        if self.enable_multi_window and self.sync_windows:
            return self._detect_synchronized_incidents_multi_window(df)
        
        # Fallback to legacy single-window detection
        return self._detect_synchronized_incidents_legacy(df)
    
    def _detect_synchronized_incidents_multi_window(self, df: pd.DataFrame) -> List[SynchronizedIncident]:
        """
        Enhanced multi-window synchronized incident detection
        """
        all_sync_incidents = []
        processed_global = set()
        
        # Analyze each configured time window
        for window_name, window_config in self.sync_windows.items():
            if not window_config.get("enabled", True):
                continue
            
            self.logger.info(f"Analyzing synchronized incidents with {window_name} ({window_config.get('window_minutes', 0)} minutes)")
            
            # Filter incidents by priority scope
            priority_scope = window_config.get("priority_scope", ["1 - Critical"])
            filtered_df = df[df['Priority'].isin(priority_scope)].copy()
            
            if filtered_df.empty:
                continue
            
            # Sort by creation time
            filtered_df = filtered_df.sort_values('Created')
            
            window_sync_incidents = self._analyze_time_window(
                filtered_df, 
                window_name,
                window_config,
                processed_global
            )
            
            all_sync_incidents.extend(window_sync_incidents)
        
        # Sort by timestamp and remove duplicates
        unique_incidents = self._deduplicate_sync_incidents(all_sync_incidents)
        
        return sorted(unique_incidents, key=lambda x: x.timestamp)
    
    def _analyze_time_window(self, df: pd.DataFrame, window_name: str, config: dict, processed_global: set) -> List[SynchronizedIncident]:
        """
        Analyze a specific time window configuration
        """
        sync_incidents = []
        window_minutes = config.get("window_minutes", 5)
        tolerance_seconds = config.get("tolerance_seconds", 0)
        min_sites = config.get("min_sites", 2)
        correlation_threshold = config.get("correlation_threshold", 0.6)
        
        processed_indices = set()
        
        for idx, incident in df.iterrows():
            if idx in processed_indices or idx in processed_global:
                continue
            
            incident_time = incident['Created']
            
            # Handle exact minute analysis with tolerance
            if window_minutes == 0:  # Exact minute mode
                # Find incidents in same minute with tolerance
                minute_start = incident_time.replace(second=0, microsecond=0)
                minute_end = minute_start + timedelta(minutes=1)
                
                # Apply tolerance within the minute
                if tolerance_seconds > 0:
                    tolerance_delta = timedelta(seconds=tolerance_seconds)
                    window_start = max(minute_start, incident_time - tolerance_delta)
                    window_end = min(minute_end, incident_time + tolerance_delta)
                else:
                    window_start = minute_start
                    window_end = minute_end
            else:
                # Regular time window
                time_window = timedelta(minutes=window_minutes)
                window_start = incident_time - time_window
                window_end = incident_time + time_window
            
            # Find incidents within time window at different sites
            window_mask = (
                (df['Created'] >= window_start) &
                (df['Created'] <= window_end) &
                (df['Site'] != incident['Site']) &  # Different sites
                (df.index != idx)  # Not the same incident
            )
            
            window_incidents = df[window_mask]
            
            # Check if we have enough sites
            unique_sites = set([incident['Site']] + list(window_incidents['Site'].unique()))
            
            if len(unique_sites) >= min_sites:
                # Create list of all incidents in this sync event
                all_incidents = [incident.to_dict()] + [inc.to_dict() for _, inc in window_incidents.iterrows()]
                
                # Calculate enhanced correlation score
                if self.advanced_correlation:
                    correlation_score = self._calculate_enhanced_correlation_score(all_incidents, window_name)
                else:
                    correlation_score = self._calculate_sync_correlation_score(all_incidents)
                
                if correlation_score >= correlation_threshold:
                    # Calculate precise time span for this group
                    timestamps = [inc['Created'] for inc in all_incidents]
                    time_span_seconds = (max(timestamps) - min(timestamps)).total_seconds()
                    
                    sync_incident = SynchronizedIncident(
                        timestamp=incident_time,
                        sites=list(unique_sites),
                        incidents=all_incidents,
                        correlation_score=correlation_score,
                        time_window_minutes=window_minutes if window_minutes > 0 else time_span_seconds/60
                    )
                    
                    # Add window analysis metadata
                    sync_incident.window_type = window_name
                    sync_incident.actual_time_span_seconds = time_span_seconds
                    sync_incident.priority_scope = config.get("priority_scope", [])
                    
                    sync_incidents.append(sync_incident)
                    
                    # Mark as processed
                    processed_indices.add(idx)
                    processed_indices.update(window_incidents.index)
                    processed_global.update([idx] + list(window_incidents.index))
        
        return sync_incidents
    
    def _detect_synchronized_incidents_legacy(self, df: pd.DataFrame) -> List[SynchronizedIncident]:
        """
        Legacy single-window synchronized incident detection (backward compatibility)
        """
        sync_incidents = []
        time_window_minutes = self.pattern_config.get("sync_time_window_minutes", 5)
        min_sites = self.pattern_config.get("min_sites_for_sync", 2)
        
        # Focus on critical incidents for synchronization analysis
        critical_df = df[df['Priority'] == '1 - Critical'].copy()
        
        if critical_df.empty:
            return []
        
        # Sort by creation time
        critical_df = critical_df.sort_values('Created')
        processed_indices = set()
        
        for idx, incident in critical_df.iterrows():
            if idx in processed_indices:
                continue
            
            incident_time = incident['Created']
            time_window = timedelta(minutes=time_window_minutes)
            
            # Find incidents within time window
            window_start = incident_time - time_window
            window_end = incident_time + time_window
            
            window_mask = (
                (critical_df['Created'] >= window_start) &
                (critical_df['Created'] <= window_end) &
                (critical_df['Site'] != incident['Site'])  # Different sites
            )
            
            window_incidents = critical_df[window_mask]
            
            if len(window_incidents) >= min_sites - 1:  # -1 because we already have the primary incident
                # Create list of all incidents in this sync event
                all_incidents = [incident.to_dict()] + [inc.to_dict() for _, inc in window_incidents.iterrows()]
                all_sites = [inc['Site'] for inc in all_incidents]
                
                # Calculate correlation score based on description similarity and timing
                correlation_score = self._calculate_sync_correlation_score(all_incidents)
                
                if correlation_score >= self.pattern_config.get("correlation_threshold", 0.6):
                    sync_incident = SynchronizedIncident(
                        timestamp=incident_time,
                        sites=all_sites,
                        incidents=all_incidents,
                        correlation_score=correlation_score,
                        time_window_minutes=time_window_minutes
                    )
                    sync_incidents.append(sync_incident)
                    
                    # Mark as processed
                    processed_indices.add(idx)
                    processed_indices.update(window_incidents.index)
        
        return sync_incidents
    
    def _calculate_sync_correlation_score(self, incidents: List[Dict]) -> float:
        """Calculate correlation score for synchronized incidents"""
        if len(incidents) < 2:
            return 0.0
        
        scores = []
        
        # Category similarity
        categories = [inc.get('Category', '').lower() for inc in incidents]
        unique_categories = set(categories)
        if len(unique_categories) == 1:  # All same category
            scores.append(1.0)
        elif len(unique_categories) <= len(categories) / 2:  # Most are same category
            scores.append(0.7)
        else:
            scores.append(0.3)
        
        # Description similarity (simplified)
        descriptions = [inc.get('Short description', '').lower() for inc in incidents]
        common_words = self._find_common_words(descriptions)
        if len(common_words) >= 2:
            scores.append(0.8)
        elif len(common_words) >= 1:
            scores.append(0.5)
        else:
            scores.append(0.2)
        
        # Time clustering (tighter timing = higher score)
        timestamps = [inc.get('Created') for inc in incidents if inc.get('Created')]
        if len(timestamps) >= 2:
            time_span = max(timestamps) - min(timestamps)
            time_span_minutes = time_span.total_seconds() / 60
            
            if time_span_minutes <= 10:
                scores.append(1.0)
            elif time_span_minutes <= 30:
                scores.append(0.7)
            else:
                scores.append(0.4)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_enhanced_correlation_score(self, incidents: List[Dict], window_type: str) -> float:
        """Calculate enhanced correlation score with window-specific logic"""
        if len(incidents) < 2:
            return 0.0
        
        scores = []
        
        # Base correlation score
        base_score = self._calculate_sync_correlation_score(incidents)
        scores.append(base_score)
        
        # Time precision bonus for exact minute windows
        if window_type == "exact_minute":
            timestamps = [inc.get('Created') for inc in incidents if inc.get('Created')]
            if len(timestamps) >= 2:
                time_span = max(timestamps) - min(timestamps)
                time_span_seconds = time_span.total_seconds()
                
                # Bonus for very tight timing (within 60 seconds)
                if time_span_seconds <= 60:
                    precision_bonus = 1.0 - (time_span_seconds / 60)
                    scores.append(precision_bonus * 0.3)  # Up to 30% bonus
        
        # Site diversity bonus
        unique_sites = set(inc.get('Site', '') for inc in incidents)
        if len(unique_sites) >= 3:
            diversity_bonus = min(0.2, (len(unique_sites) - 2) * 0.05)  # Up to 20% bonus
            scores.append(diversity_bonus)
        
        # Priority consistency bonus
        priorities = [inc.get('Priority', '').lower() for inc in incidents]
        unique_priorities = set(priorities)
        if len(unique_priorities) == 1 and 'critical' in unique_priorities:
            scores.append(0.1)  # 10% bonus for all critical
        
        # Description keyword clustering
        descriptions = [inc.get('Short description', '').lower() for inc in incidents]
        common_keywords = self._find_technical_keywords(descriptions)
        if len(common_keywords) >= 2:
            keyword_bonus = min(0.25, len(common_keywords) * 0.05)  # Up to 25% bonus
            scores.append(keyword_bonus)
        
        return min(1.0, sum(scores) / len(scores))
    
    def _find_technical_keywords(self, descriptions: List[str]) -> Set[str]:
        """Find common technical keywords that suggest related issues"""
        technical_terms = {
            'network', 'server', 'connection', 'timeout', 'database', 'system',
            'power', 'internet', 'wifi', 'router', 'switch', 'firewall',
            'pos', 'terminal', 'payment', 'credit', 'card', 'receipt',
            'backup', 'restore', 'update', 'patch', 'reboot', 'restart',
            'error', 'failure', 'crash', 'hang', 'freeze', 'slow', 'down'
        }
        
        word_sets = []
        for desc in descriptions:
            if desc and desc != 'nan':
                words = set(desc.lower().split())
                # Find intersection with technical terms
                technical_words = words.intersection(technical_terms)
                if technical_words:
                    word_sets.append(technical_words)
        
        if len(word_sets) < 2:
            return set()
        
        # Find common technical terms across descriptions
        common = word_sets[0]
        for word_set in word_sets[1:]:
            common = common.intersection(word_set)
        
        return common
    
    def _deduplicate_sync_incidents(self, sync_incidents: List[SynchronizedIncident]) -> List[SynchronizedIncident]:
        """Remove duplicate synchronized incidents found in multiple windows"""
        if not sync_incidents:
            return []
        
        unique_incidents = []
        processed_incident_sets = set()
        
        for sync_incident in sync_incidents:
            # Create a signature for this incident group based on involved sites and time
            sites_signature = tuple(sorted(sync_incident.sites))
            time_signature = sync_incident.timestamp.replace(second=0, microsecond=0)
            incident_signature = (sites_signature, time_signature)
            
            if incident_signature not in processed_incident_sets:
                unique_incidents.append(sync_incident)
                processed_incident_sets.add(incident_signature)
            else:
                # If we have a duplicate, keep the one with higher correlation score
                existing_idx = None
                for i, existing in enumerate(unique_incidents):
                    existing_sig = (tuple(sorted(existing.sites)), existing.timestamp.replace(second=0, microsecond=0))
                    if existing_sig == incident_signature:
                        existing_idx = i
                        break
                
                if existing_idx is not None and sync_incident.correlation_score > unique_incidents[existing_idx].correlation_score:
                    unique_incidents[existing_idx] = sync_incident
        
        return unique_incidents
    
    def _find_common_words(self, descriptions: List[str]) -> Set[str]:
        """Find common words across descriptions (ignoring common stopwords)"""
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        
        word_sets = []
        for desc in descriptions:
            if desc and desc != 'nan':
                words = set(desc.lower().split()) - stopwords
                if words:  # Only add non-empty word sets
                    word_sets.append(words)
        
        if len(word_sets) < 2:
            return set()
        
        # Find intersection of all word sets
        common = word_sets[0]
        for word_set in word_sets[1:]:
            common = common.intersection(word_set)
        
        return common
    
    def _detect_recurring_patterns(self, df: pd.DataFrame) -> List[TemporalPattern]:
        """Detect recurring patterns (daily, weekly, monthly)"""
        if df.empty:
            return []
        
        patterns = []
        
        # Weekly patterns (e.g., every Monday)
        df_copy = df.copy()
        df_copy['DayOfWeek'] = df_copy['Created'].dt.dayofweek
        df_copy['Hour'] = df_copy['Created'].dt.hour
        
        # Analyze by site and day of week
        weekly_patterns = df_copy.groupby(['Site', 'DayOfWeek']).size().reset_index(name='Count')
        
        # Look for sites with consistently high incident counts on specific days
        for site in df['Site'].unique():
            site_weekly = weekly_patterns[weekly_patterns['Site'] == site]
            
            if len(site_weekly) > 0:
                max_day_count = site_weekly['Count'].max()
                avg_day_count = site_weekly['Count'].mean()
                
                # If one day has significantly more incidents than average
                if max_day_count > avg_day_count * 2 and max_day_count >= 3:
                    matching_days = site_weekly[site_weekly['Count'] == max_day_count]['DayOfWeek']
                    peak_day = matching_days.iloc[0] if len(matching_days) > 0 else 0
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    
                    pattern = TemporalPattern(
                        pattern_type='recurring',
                        sites=[site],
                        confidence=min(0.9, (max_day_count - avg_day_count) / max_day_count),
                        time_window=(df['Created'].min(), df['Created'].max()),
                        description=f"High incident rate on {day_names[peak_day]}s ({max_day_count} incidents)"
                    )
                    pattern.incident_count = max_day_count
                    patterns.append(pattern)
        
        return patterns
    
    def _calculate_site_correlation_matrix(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate temporal correlation between sites"""
        if df.empty:
            return {}
        
        # Create daily incident counts per site
        df_copy = df.copy()
        df_copy['Date'] = df_copy['Created'].dt.date
        
        # Pivot to get site incident counts by date
        daily_counts = df_copy.groupby(['Date', 'Site']).size().unstack(fill_value=0)
        
        if daily_counts.empty or len(daily_counts.columns) < 2:
            return {}
        
        # Calculate correlation matrix
        correlation_matrix = daily_counts.corr()
        
        # Find highly correlated site pairs
        high_correlations = []
        
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                site1 = correlation_matrix.columns[i]
                site2 = correlation_matrix.columns[j]
                correlation = correlation_matrix.iloc[i, j]
                
                if not pd.isna(correlation) and correlation > self.pattern_config.get("correlation_threshold", 0.6):
                    high_correlations.append({
                        'site1': site1,
                        'site2': site2,
                        'correlation': correlation,
                        'strength': 'Strong' if correlation > 0.8 else 'Moderate'
                    })
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'high_correlations': high_correlations,
            'total_site_pairs': len(high_correlations)
        }
    
    def _analyze_peak_incident_times(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze when incidents most commonly occur"""
        if df.empty:
            return {}
        
        df_copy = df.copy()
        df_copy['Hour'] = df_copy['Created'].dt.hour
        df_copy['DayOfWeek'] = df_copy['Created'].dt.dayofweek
        df_copy['Month'] = df_copy['Created'].dt.month
        
        # Hourly distribution - safe empty series handling
        hourly_counts = df_copy['Hour'].value_counts().sort_index()
        peak_hour = hourly_counts.idxmax() if len(hourly_counts) > 0 else 0
        
        # Daily distribution - safe empty series handling
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_counts = df_copy['DayOfWeek'].value_counts().sort_index()
        peak_day_idx = daily_counts.idxmax() if len(daily_counts) > 0 else 0
        peak_day = day_names[peak_day_idx] if peak_day_idx < len(day_names) else 'Monday'
        
        # Monthly distribution - safe empty series handling
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_counts = df_copy['Month'].value_counts().sort_index()
        if len(monthly_counts) > 0:
            peak_month_idx = monthly_counts.idxmax() - 1
            peak_month = month_names[peak_month_idx] if 0 <= peak_month_idx < len(month_names) else 'Jan'
        else:
            peak_month = 'Jan'
        
        return {
            'peak_hour': {
                'hour': peak_hour,
                'count': hourly_counts.loc[peak_hour] if peak_hour in hourly_counts.index else 0,
                'percentage': ((hourly_counts.loc[peak_hour] if peak_hour in hourly_counts.index else 0) / len(df_copy)) * 100 if len(df_copy) > 0 else 0
            },
            'peak_day': {
                'day': peak_day,
                'count': daily_counts.max() if len(daily_counts) > 0 else 0,
                'percentage': ((daily_counts.max() if len(daily_counts) > 0 else 0) / len(df_copy)) * 100 if len(df_copy) > 0 else 0
            },
            'peak_month': {
                'month': peak_month,
                'count': monthly_counts.max() if len(monthly_counts) > 0 else 0,
                'percentage': ((monthly_counts.max() if len(monthly_counts) > 0 else 0) / len(df_copy)) * 100 if len(df_copy) > 0 else 0
            },
            'hourly_distribution': hourly_counts.to_dict(),
            'daily_distribution': daily_counts.to_dict(),
            'monthly_distribution': monthly_counts.to_dict()
        }
    
    def _detect_seasonal_patterns(self, df: pd.DataFrame) -> List[TemporalPattern]:
        """Detect seasonal patterns in incident data"""
        if df.empty or len(df) < 30:  # Need sufficient data for seasonal analysis
            return []
        
        patterns = []
        
        df_copy = df.copy()
        df_copy['Week'] = df_copy['Created'].dt.isocalendar().week
        df_copy['Month'] = df_copy['Created'].dt.month
        
        # Monthly seasonal patterns
        monthly_counts = df_copy.groupby('Month').size()
        
        if len(monthly_counts) >= 3:  # Need at least 3 months of data
            max_month = monthly_counts.idxmax()
            min_month = monthly_counts.idxmin()
            
            # If difference is significant, it's a seasonal pattern
            if monthly_counts.max() > monthly_counts.mean() * 1.5:
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                pattern = TemporalPattern(
                    pattern_type='seasonal',
                    sites=df['Site'].unique().tolist(),
                    confidence=0.7,
                    time_window=(df['Created'].min(), df['Created'].max()),
                    description=f"Peak incidents in {month_names[max_month-1]} ({monthly_counts.max()} incidents)"
                )
                pattern.incident_count = monthly_counts.max()
                patterns.append(pattern)
        
        return patterns
    
    def _detect_temporal_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect unusual spikes or patterns in incident timing"""
        if df.empty:
            return []
        
        anomalies = []
        
        # Daily incident count analysis
        df_copy = df.copy()
        df_copy['Date'] = df_copy['Created'].dt.date
        daily_counts = df_copy.groupby('Date').size()
        
        if len(daily_counts) >= 7:  # Need at least a week of data
            mean_daily = daily_counts.mean()
            std_daily = daily_counts.std()
            threshold = mean_daily + (2 * std_daily)  # 2 standard deviations
            
            # Find anomalous days
            anomalous_days = daily_counts[daily_counts > threshold]
            
            for date, count in anomalous_days.items():
                anomaly_data = df_copy[df_copy['Date'] == date]
                
                anomalies.append({
                    'type': 'volume_spike',
                    'date': date.strftime('%Y-%m-%d'),
                    'incident_count': count,
                    'normal_range': f"{mean_daily:.1f} ± {std_daily:.1f}",
                    'affected_sites': anomaly_data['Site'].nunique(),
                    'categories': anomaly_data['Category'].value_counts().to_dict() if 'Category' in anomaly_data.columns else {}
                })
        
        return anomalies
    
    def _generate_pattern_insights(self, pattern_results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from pattern analysis"""
        insights = []
        
        # Synchronized incidents insights
        sync_incidents = pattern_results.get("synchronized_incidents", [])
        if len(sync_incidents) > 0:
            insights.append(f"🔗 {len(sync_incidents)} synchronized incident events detected - investigate common root causes")
            
            # Most common root cause
            root_causes = [inc.likely_root_cause for inc in sync_incidents]
            if root_causes:
                most_common = max(set(root_causes), key=root_causes.count)
                insights.append(f"🎯 Most likely synchronized issue cause: {most_common}")
        
        # Site correlation insights  
        correlations = pattern_results.get("time_correlation_matrix", {}).get("high_correlations", [])
        if len(correlations) > 0:
            insights.append(f"📊 {len(correlations)} site pairs show correlated incident patterns")
            
            strongest = max(correlations, key=lambda x: x['correlation'])
            insights.append(f"🔗 Strongest correlation: {strongest['site1']} ↔ {strongest['site2']} ({strongest['correlation']:.1%})")
        
        # Peak time insights
        peak_times = pattern_results.get("peak_incident_times", {})
        if peak_times:
            if 'peak_hour' in peak_times and peak_times['peak_hour']['percentage'] > 15:
                hour = peak_times['peak_hour']['hour']
                pct = peak_times['peak_hour']['percentage']
                insights.append(f"⏰ {pct:.1f}% of incidents occur at {hour:02d}:00 - review operations during this time")
            
            if 'peak_day' in peak_times and peak_times['peak_day']['percentage'] > 20:
                day = peak_times['peak_day']['day']
                pct = peak_times['peak_day']['percentage']
                insights.append(f"📅 {pct:.1f}% of incidents occur on {day}s - investigate day-specific factors")
        
        # Recurring patterns insights
        recurring = pattern_results.get("recurring_patterns", [])
        if len(recurring) > 0:
            insights.append(f"🔄 {len(recurring)} sites show recurring incident patterns")
            
            high_confidence = [p for p in recurring if p.confidence > 0.8]
            if high_confidence:
                insights.append(f"⚠️ {len(high_confidence)} sites have highly predictable recurring issues")
        
        # Seasonal patterns insights
        seasonal = pattern_results.get("seasonal_patterns", [])
        if len(seasonal) > 0:
            for pattern in seasonal:
                insights.append(f"🌊 Seasonal pattern detected: {pattern.description}")
        
        # Anomaly insights
        anomalies = pattern_results.get("anomaly_detection", [])
        if len(anomalies) > 0:
            volume_spikes = [a for a in anomalies if a['type'] == 'volume_spike']
            if volume_spikes:
                insights.append(f"📈 {len(volume_spikes)} unusual incident volume spikes detected")
        
        return insights[:10]  # Limit to top 10 insights