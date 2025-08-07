"""
Report generation engine
"""

import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
from ..utils.stability_analytics import SystemStabilityAnalyzer, StabilityMetrics
from ..utils.pattern_recognition import TimePatternEngine

class ReportEngine:
    """Generates various stability reports from ticket data"""
    
    def __init__(self, settings):
        self.settings = settings
        self.critical_threshold = settings.get("reports.critical_threshold", 2)
        self.mttr_targets = settings.get("reports.mttr_targets", {})
        
        # Initialize analytics engines
        self.stability_analyzer = SystemStabilityAnalyzer(settings)
        self.pattern_engine = TimePatternEngine(settings)
    
    def generate_critical_hotspots_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Critical Incident Hotspot Report
        Shows sites with multiple critical incidents
        """
        if df.empty:
            return [], []
        
        # Filter for critical tickets only
        critical_df = df[df["Priority"] == "1 - Critical"].copy()
        
        if critical_df.empty:
            return [], ["Site", "Company", "Critical Count", "Latest Incident", "Days Since Last", "All Critical Tickets"]
        
        # Group by site and company
        grouped = critical_df.groupby(["Site", "Company"]).agg({
            "Created": ["count", "max"],
            "Number": "first"  # Just to get a ticket number reference
        }).reset_index()
        
        # Flatten column names
        grouped.columns = ["Site", "Company", "Critical_Count", "Latest_Incident", "Sample_Ticket"]
        
        # Filter sites with threshold or more critical incidents
        hotspots = grouped[grouped["Critical_Count"] >= self.critical_threshold].copy()
        
        if hotspots.empty:
            return [], ["Site", "Company", "Critical Count", "Latest Incident", "Days Since Last", "All Critical Tickets"]
        
        # Calculate days since last critical incident
        now = pd.Timestamp.now()
        hotspots["Days_Since_Last"] = (now - hotspots["Latest_Incident"]).dt.days
        
        # Sort by critical count (desc) then by latest incident (desc)
        hotspots = hotspots.sort_values(["Critical_Count", "Latest_Incident"], 
                                       ascending=[False, False])
        
        # Format for display with ALL critical tickets
        results = []
        for _, row in hotspots.iterrows():
            site_name = row["Site"]
            
            # Get ALL critical tickets for this site
            site_critical_tickets = critical_df[critical_df["Site"] == site_name]["Number"].dropna().tolist()
            all_tickets = ", ".join([str(t) for t in site_critical_tickets])
            if not all_tickets:
                all_tickets = "No ticket #s"
            
            results.append([
                row["Site"],
                row["Company"],
                int(row["Critical_Count"]),
                row["Latest_Incident"].strftime("%Y-%m-%d %H:%M") if pd.notna(row["Latest_Incident"]) else "N/A",
                int(row["Days_Since_Last"]) if pd.notna(row["Days_Since_Last"]) else "N/A",
                all_tickets
            ])
        
        columns = ["Site", "Company", "Critical Count", "Latest Incident", "Days Since Last", "All Critical Tickets"]
        return results, columns
    
    def generate_site_scorecard_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Site Stability Scorecard
        Shows performance metrics for all sites
        """
        if df.empty:
            return [], []
        
        # Group by site and company
        grouped = df.groupby(["Site", "Company"]).agg({
            "Number": "count",  # Total tickets
            "Is_Critical": "sum",  # Critical count
            "Resolution_Hours": ["mean", "count"],  # MTTR and resolved count
            "Is_Resolved": "sum",  # Total resolved
            "Days_Since_Created": "max"  # Longest open issue
        }).reset_index()
        
        # Flatten column names
        grouped.columns = ["Site", "Company", "Total_Tickets", "Critical_Count", 
                          "Avg_MTTR_Hours", "Resolved_Count", "Total_Resolved", "Longest_Open_Days"]
        
        # Calculate metrics
        grouped["Critical_Percentage"] = (grouped["Critical_Count"] / grouped["Total_Tickets"] * 100).round(1)
        grouped["Avg_MTTR_Hours"] = grouped["Avg_MTTR_Hours"].fillna(0).round(1)
        grouped["Longest_Open_Days"] = grouped["Longest_Open_Days"].fillna(0).astype(int)
        
        # Sort by critical percentage (desc) then by avg MTTR (desc)
        grouped = grouped.sort_values(["Critical_Percentage", "Avg_MTTR_Hours"], 
                                     ascending=[False, False])
        
        # Format for display
        results = []
        for _, row in grouped.iterrows():
            # Determine status color/indicator
            mttr_hours = row["Avg_MTTR_Hours"]
            if mttr_hours > 48:
                status = "🔴 High Risk"
            elif mttr_hours > 24:
                status = "🟡 Medium Risk"
            else:
                status = "🟢 Good"
            
            results.append([
                row["Site"],
                row["Company"],
                int(row["Total_Tickets"]),
                int(row["Critical_Count"]),
                f"{row['Critical_Percentage']:.1f}%",
                f"{row['Avg_MTTR_Hours']:.1f}h" if row["Avg_MTTR_Hours"] > 0 else "N/A",
                int(row["Longest_Open_Days"]) if row["Longest_Open_Days"] > 0 else "N/A",
                status
            ])
        
        columns = ["Site", "Company", "Total Tickets", "Critical Count", "Critical %", 
                  "Avg MTTR", "Longest Open (days)", "Status"]
        return results, columns
    
    def generate_green_list_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Green List - sites with no critical incidents
        """
        if df.empty:
            return [], []
        
        # Get all sites
        all_sites = df.groupby(["Site", "Company"]).agg({
            "Number": "count",
            "Is_Critical": "sum",
            "Created": "max",
            "Is_Resolved": "sum"
        }).reset_index()
        
        all_sites.columns = ["Site", "Company", "Total_Tickets", "Critical_Count", 
                           "Last_Issue_Date", "Resolved_Count"]
        
        # Filter sites with zero critical incidents
        green_sites = all_sites[all_sites["Critical_Count"] == 0].copy()
        
        if green_sites.empty:
            return [], ["Site", "Company", "Total Non-Critical", "Last Issue", "Uptime Days"]
        
        # Calculate uptime days (days since last issue)
        now = pd.Timestamp.now()
        green_sites["Uptime_Days"] = (now - green_sites["Last_Issue_Date"]).dt.days
        
        # Sort by total tickets (desc) to show most active stable sites first
        green_sites = green_sites.sort_values("Total_Tickets", ascending=False)
        
        # Format for display
        results = []
        for _, row in green_sites.iterrows():
            results.append([
                row["Site"],
                row["Company"],
                int(row["Total_Tickets"]),
                row["Last_Issue_Date"].strftime("%Y-%m-%d") if pd.notna(row["Last_Issue_Date"]) else "N/A",
                int(row["Uptime_Days"]) if pd.notna(row["Uptime_Days"]) else "N/A"
            ])
        
        columns = ["Site", "Company", "Total Non-Critical", "Last Issue", "Uptime Days"]
        return results, columns
    
    def generate_franchise_overview_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Franchise Performance Overview
        Company-level aggregation and comparison
        """
        if df.empty:
            return [], []
        
        # Group by company
        company_stats = df.groupby("Company").agg({
            "Site": "nunique",  # Number of sites
            "Number": "count",  # Total tickets
            "Is_Critical": "sum",  # Critical tickets
            "Resolution_Hours": "mean",  # Average MTTR
            "Is_Resolved": "sum"  # Resolved tickets
        }).reset_index()
        
        company_stats.columns = ["Company", "Sites_Count", "Total_Tickets", 
                               "Critical_Count", "Avg_MTTR_Hours", "Resolved_Count"]
        
        # Calculate derived metrics
        company_stats["Critical_Percentage"] = (
            company_stats["Critical_Count"] / company_stats["Total_Tickets"] * 100
        ).round(1)
        company_stats["Avg_MTTR_Hours"] = company_stats["Avg_MTTR_Hours"].fillna(0).round(1)
        company_stats["Tickets_Per_Site"] = (
            company_stats["Total_Tickets"] / company_stats["Sites_Count"]
        ).round(1)
        
        # Find best and worst performing sites for each company
        site_performance = df.groupby(["Company", "Site"]).agg({
            "Is_Critical": "sum",
            "Resolution_Hours": "mean"
        }).reset_index()
        
        best_worst = []
        for company in company_stats["Company"]:
            sites = site_performance[site_performance["Company"] == company]
            if not sites.empty and len(sites) > 0:
                try:
                    # Best site: lowest critical incidents, then lowest MTTR
                    best_site = sites.loc[sites["Is_Critical"].idxmin(), "Site"]
                    # Worst site: highest critical incidents, then highest MTTR
                    worst_site = sites.loc[sites["Is_Critical"].idxmax(), "Site"]
                    best_worst.append((company, best_site, worst_site))
                except (ValueError, KeyError, IndexError):
                    # Handle empty series or missing data gracefully
                    if len(sites) > 0:
                        first_site = sites.iloc[0]["Site"]
                        best_worst.append((company, first_site, first_site))
                    else:
                        best_worst.append((company, "N/A", "N/A"))
        
        best_worst_df = pd.DataFrame(best_worst, columns=["Company", "Best_Site", "Worst_Site"])
        
        # Merge with company stats
        company_stats = company_stats.merge(best_worst_df, on="Company", how="left")
        
        # Sort by performance score (lower critical % and MTTR is better)
        company_stats["Performance_Score"] = (
            company_stats["Critical_Percentage"] + company_stats["Avg_MTTR_Hours"] / 10
        )
        company_stats = company_stats.sort_values("Performance_Score")
        
        # Format for display
        results = []
        for _, row in company_stats.iterrows():
            results.append([
                row["Company"],
                int(row["Sites_Count"]),
                int(row["Total_Tickets"]),
                f"{row['Critical_Percentage']:.1f}%",
                f"{row['Avg_MTTR_Hours']:.1f}h" if row["Avg_MTTR_Hours"] > 0 else "N/A",
                f"{row['Tickets_Per_Site']:.1f}",
                row["Best_Site"] if pd.notna(row["Best_Site"]) else "N/A",
                row["Worst_Site"] if pd.notna(row["Worst_Site"]) else "N/A"
            ])
        
        columns = ["Company", "Sites", "Total Tickets", "Critical %", "Avg MTTR", 
                  "Tickets/Site", "Best Site", "Worst Site"]
        return results, columns
    
    def generate_equipment_analysis_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Equipment Category Breakdown Report
        """
        if df.empty or "Category" not in df.columns:
            return [], []
        
        # Group by category and subcategory
        equipment_stats = df.groupby(["Category", "Subcategory"]).agg({
            "Number": "count",
            "Is_Critical": "sum",
            "Resolution_Hours": "mean",
            "Site": lambda x: x.value_counts().index[0] if len(x) > 0 else "N/A"  # Most affected site
        }).reset_index()
        
        equipment_stats.columns = ["Category", "Subcategory", "Total_Count", 
                                 "Critical_Count", "Avg_MTTR_Hours", "Most_Affected_Site"]
        
        # Calculate percentage of total
        total_tickets = len(df)
        equipment_stats["Percentage"] = (equipment_stats["Total_Count"] / total_tickets * 100).round(1)
        equipment_stats["Critical_Rate"] = (
            equipment_stats["Critical_Count"] / equipment_stats["Total_Count"] * 100
        ).round(1)
        equipment_stats["Avg_MTTR_Hours"] = equipment_stats["Avg_MTTR_Hours"].fillna(0).round(1)
        
        # Sort by total count (desc)
        equipment_stats = equipment_stats.sort_values("Total_Count", ascending=False)
        
        # Format for display
        results = []
        for _, row in equipment_stats.iterrows():
            results.append([
                row["Category"],
                row["Subcategory"],
                int(row["Total_Count"]),
                f"{row['Percentage']:.1f}%",
                int(row["Critical_Count"]),
                f"{row['Critical_Rate']:.1f}%",
                f"{row['Avg_MTTR_Hours']:.1f}h" if row["Avg_MTTR_Hours"] > 0 else "N/A",
                row["Most_Affected_Site"]
            ])
        
        columns = ["Category", "Subcategory", "Count", "% of Total", "Critical", 
                  "Critical %", "Avg MTTR", "Most Affected Site"]
        return results, columns
    
    def get_report_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for the current dataset"""
        if df.empty:
            return {}
        
        total_tickets = len(df)
        critical_tickets = df["Is_Critical"].sum()
        resolved_tickets = df["Is_Resolved"].sum()
        
        # Date range
        if "Created" in df.columns:
            date_range = {
                "start": df["Created"].min(),
                "end": df["Created"].max()
            }
        else:
            date_range = {"start": None, "end": None}
        
        # Average MTTR
        avg_mttr = df["Resolution_Hours"].dropna().mean() if "Resolution_Hours" in df.columns else None
        
        summary = {
            "total_tickets": int(total_tickets),
            "critical_tickets": int(critical_tickets),
            "critical_percentage": round((critical_tickets / total_tickets * 100), 1) if total_tickets > 0 else 0,
            "resolved_tickets": int(resolved_tickets),
            "resolution_rate": round((resolved_tickets / total_tickets * 100), 1) if total_tickets > 0 else 0,
            "unique_sites": df["Site"].nunique(),
            "unique_companies": df["Company"].nunique(),
            "date_range": date_range,
            "avg_mttr_hours": round(avg_mttr, 1) if avg_mttr else None
        }
        
        return summary
    
    def generate_incident_details_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Incident Details Report
        Shows individual tickets matching current filters
        """
        if df.empty:
            return [], []
        
        # Sort by site, then by created date (most recent first)
        df_sorted = df.sort_values(["Site", "Created"], ascending=[True, False])
        
        results = []
        for _, row in df_sorted.iterrows():
            # Format created date
            created_str = row["Created"].strftime("%Y-%m-%d %H:%M") if pd.notna(row["Created"]) else "N/A"
            
            # Format resolved date and calculate resolution time
            if pd.notna(row.get("Resolved")):
                resolved_str = row["Resolved"].strftime("%Y-%m-%d %H:%M")
                status = "Resolved"
                resolution_hours = row.get("Resolution_Hours", 0)
                if resolution_hours and resolution_hours > 0:
                    if resolution_hours < 24:
                        resolution_time = f"{resolution_hours:.1f}h"
                    else:
                        days = resolution_hours / 24
                        resolution_time = f"{days:.1f}d"
                else:
                    resolution_time = "N/A"
            else:
                resolved_str = "Open"
                status = "Open"
                # Calculate days since created for open tickets
                if pd.notna(row["Created"]):
                    days_open = (pd.Timestamp.now() - row["Created"]).days
                    resolution_time = f"{days_open}d open"
                else:
                    resolution_time = "N/A"
            
            # Get ticket description (truncate if too long)
            description = str(row.get("Short description", "")).strip()
            if len(description) > 60:
                description = description[:57] + "..."
            if not description or description == "nan":
                description = "No description"
            
            # Get category and subcategory
            category = str(row.get("Category", "")).strip()
            subcategory = str(row.get("Subcategory", "")).strip()
            if category == "nan" or not category:
                category = "Other"
            if subcategory == "nan" or not subcategory:
                subcategory = ""
            
            category_full = f"{category}" + (f" - {subcategory}" if subcategory else "")
            
            results.append([
                row["Site"],
                str(row.get("Number", "N/A")),
                description,
                category_full,
                row["Priority"],
                created_str,
                resolved_str,
                resolution_time,
                status,
                row["Company"]
            ])
        
        columns = ["Site", "Ticket #", "Description", "Category", "Priority", 
                  "Created", "Resolved", "Resolution Time", "Status", "Company"]
        return results, columns
    
    def generate_site_drill_down_report(self, df: pd.DataFrame, site_name: str) -> Tuple[List[List], List[str]]:
        """
        Generate drill-down report for a specific site
        Shows all tickets for that site with full details
        """
        if df.empty:
            return [], []
        
        # Filter for specific site
        site_df = df[df["Site"] == site_name].copy()
        
        if site_df.empty:
            return [], []
        
        # Use the incident details report for this site
        return self.generate_incident_details_report(site_df)
    
    def enhance_existing_reports_with_sample_tickets(self, df: pd.DataFrame, report_results: List[List], 
                                                   report_type: str) -> List[List]:
        """
        Enhance existing report results with sample ticket numbers
        """
        if not report_results or df.empty:
            return report_results
        
        enhanced_results = []
        
        for row in report_results:
            site_name = row[0]  # Site is always first column
            
            # Get tickets for this site
            site_tickets = df[df["Site"] == site_name]
            
            if not site_tickets.empty:
                # Get sample ticket numbers (up to 3)
                sample_tickets = site_tickets["Number"].dropna().head(3).tolist()
                sample_str = ", ".join([str(t) for t in sample_tickets])
                if len(sample_tickets) == 3 and len(site_tickets) > 3:
                    sample_str += f" (+{len(site_tickets) - 3} more)"
                elif not sample_str:
                    sample_str = "No ticket #s"
                
                # Add sample tickets as last column
                enhanced_row = row + [sample_str]
            else:
                enhanced_row = row + ["No tickets"]
            
            enhanced_results.append(enhanced_row)
        
        return enhanced_results
    
    def generate_repeat_offenders_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Repeat Offenders Analysis Report
        Shows sites with recurring issues in same categories
        """
        if df.empty or "Category" not in df.columns:
            return [], []
        
        # Group by site, company, and category
        category_groups = df.groupby(["Site", "Company", "Category"]).agg({
            "Number": "count",
            "Created": ["min", "max"],
            "Is_Critical": "sum"
        }).reset_index()
        
        # Flatten column names
        category_groups.columns = ["Site", "Company", "Category", "Count", "First_Incident", "Last_Incident", "Critical_Count"]
        
        # Filter for sites with 3+ incidents in same category
        repeat_offenders = category_groups[category_groups["Count"] >= 3].copy()
        
        if repeat_offenders.empty:
            return [], ["Site", "Company", "Category", "Incident Count", "Time Span (days)", "Critical Count", "Pattern Score"]
        
        # Calculate time span and pattern score
        repeat_offenders["Time_Span_Days"] = (repeat_offenders["Last_Incident"] - repeat_offenders["First_Incident"]).dt.days
        repeat_offenders["Pattern_Score"] = (repeat_offenders["Count"] * 10) + repeat_offenders["Critical_Count"] * 5
        
        # Sort by pattern score (desc)
        repeat_offenders = repeat_offenders.sort_values("Pattern_Score", ascending=False)
        
        # Format for display
        results = []
        for _, row in repeat_offenders.iterrows():
            results.append([
                row["Site"],
                row["Company"], 
                row["Category"],
                int(row["Count"]),
                int(row["Time_Span_Days"]) if row["Time_Span_Days"] >= 0 else 0,
                int(row["Critical_Count"]),
                int(row["Pattern_Score"])
            ])
        
        columns = ["Site", "Company", "Category", "Incident Count", "Time Span (days)", "Critical Count", "Pattern Score"]
        return results, columns
    
    def generate_resolution_tracking_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Resolution Performance Tracking Report
        Shows tickets exceeding target resolution times
        """
        if df.empty or "Resolution_Hours" not in df.columns:
            return [], []
        
        # Filter for resolved tickets only
        resolved_df = df[df["Is_Resolved"] == True].copy()
        
        if resolved_df.empty:
            return [], ["Site", "Ticket #", "Priority", "Resolution Time", "Target", "SLA Status", "Days Overdue"]
        
        # Define SLA targets (in hours)
        sla_targets = self.mttr_targets
        
        results = []
        for _, row in resolved_df.iterrows():
            priority = row["Priority"]
            resolution_hours = row["Resolution_Hours"]
            
            if priority in sla_targets and resolution_hours is not None:
                target_hours = sla_targets[priority]
                
                if resolution_hours > target_hours:
                    # Calculate overdue time
                    overdue_hours = resolution_hours - target_hours
                    overdue_days = overdue_hours / 24
                    
                    # Format resolution time
                    if resolution_hours < 24:
                        resolution_str = f"{resolution_hours:.1f}h"
                    else:
                        resolution_str = f"{resolution_hours/24:.1f}d"
                    
                    # Format target time
                    if target_hours < 24:
                        target_str = f"{target_hours}h"
                    else:
                        target_str = f"{target_hours/24:.1f}d"
                    
                    results.append([
                        row["Site"],
                        str(row.get("Number", "N/A")),
                        priority,
                        resolution_str,
                        target_str,
                        "🔴 Missed SLA",
                        f"{overdue_days:.1f}d"
                    ])
        
        # Sort by overdue time (most overdue first)
        if results:
            results.sort(key=lambda x: float(x[6].replace('d', '')), reverse=True)
        
        columns = ["Site", "Ticket #", "Priority", "Resolution Time", "Target", "SLA Status", "Days Overdue"]
        return results, columns
    
    def generate_workload_trends_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Workload Distribution Trends Report
        Shows ticket volume patterns by time period
        """
        if df.empty or "Created" not in df.columns:
            return [], []
        
        # Create weekly groupings
        df_copy = df.copy()
        df_copy["Week_Start"] = df_copy["Created"].dt.to_period('W').dt.start_time
        
        # Group by week
        weekly_stats = df_copy.groupby("Week_Start").agg({
            "Number": "count",
            "Is_Critical": "sum",
            "Is_Resolved": "sum",
            "Created": lambda x: x.dt.dayofweek.mode()[0] if len(x) > 0 else 0  # Most common day of week
        }).reset_index()
        
        weekly_stats.columns = ["Week_Start", "New_Tickets", "Critical_Count", "Resolved_Count", "Peak_Day_Num"]
        
        # Calculate additional metrics
        weekly_stats["Resolution_Rate"] = (weekly_stats["Resolved_Count"] / weekly_stats["New_Tickets"] * 100).round(1)
        weekly_stats["Critical_Rate"] = (weekly_stats["Critical_Count"] / weekly_stats["New_Tickets"] * 100).round(1)
        
        # Convert peak day number to name
        day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
        weekly_stats["Peak_Day"] = weekly_stats["Peak_Day_Num"].map(day_names)
        
        # Calculate backlog change (simplified)
        weekly_stats["Backlog_Change"] = weekly_stats["New_Tickets"] - weekly_stats["Resolved_Count"]
        
        # Sort by week (most recent first)
        weekly_stats = weekly_stats.sort_values("Week_Start", ascending=False)
        
        # Format for display
        results = []
        for _, row in weekly_stats.iterrows():
            # Format week range
            week_start = row["Week_Start"]
            week_end = week_start + pd.Timedelta(days=6)
            week_range = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"
            
            backlog_change = int(row["Backlog_Change"])
            backlog_indicator = "📈" if backlog_change > 0 else "📉" if backlog_change < 0 else "➡️"
            
            results.append([
                week_range,
                int(row["New_Tickets"]),
                int(row["Critical_Count"]),
                f"{row['Critical_Rate']:.1f}%",
                int(row["Resolved_Count"]),
                f"{row['Resolution_Rate']:.1f}%",
                f"{backlog_indicator} {abs(backlog_change)}",
                row["Peak_Day"]
            ])
        
        columns = ["Week", "New Tickets", "Critical", "Critical %", "Resolved", "Resolution %", "Backlog Change", "Peak Day"]
        return results, columns
    
    def generate_data_quality_report(self, quality_report: Dict[str, Any], 
                                   duplicate_groups: List = None) -> Tuple[List[List], List[str]]:
        """
        Generate Data Quality Analysis Report
        Shows data quality metrics and duplicate detection results
        """
        if not quality_report:
            return [], ["Metric", "Value", "Status", "Recommendation"]
        
        results = []
        
        # Overall quality score
        quality_score = quality_report.get("data_quality_score", 0)
        status = "🟢 Excellent" if quality_score >= 90 else "🟡 Good" if quality_score >= 75 else "🔴 Needs Attention"
        results.append([
            "Overall Data Quality Score",
            f"{quality_score:.1f}%",
            status,
            "Monitor and maintain" if quality_score >= 90 else "Review quality issues"
        ])
        
        # Site filtering results
        site_filtering = quality_report.get("site_filtering", {})
        if site_filtering.get("removed_count", 0) > 0:
            results.append([
                "Site Filtering",
                f"{site_filtering['removed_count']} tickets filtered out",
                "🔵 Applied",
                f"Removed {site_filtering['sites_removed']} non-Wendy's sites"
            ])
        else:
            results.append([
                "Site Filtering",
                "No tickets filtered",
                "🔵 Applied",
                "All sites match filter criteria"
            ])
        
        # Duplicate analysis
        dup_analysis = quality_report.get("duplicate_analysis", {})
        dup_groups = dup_analysis.get("total_duplicate_groups", 0)
        
        if dup_groups > 0:
            status = "🟡 Review Required" if dup_analysis.get("manual_review_required", 0) > 0 else "🟢 Auto-handled"
            results.append([
                "Duplicate Detection",
                f"{dup_groups} duplicate groups found",
                status,
                f"Review {dup_analysis.get('manual_review_required', 0)} groups manually"
            ])
            
            # High confidence duplicates
            high_confidence = dup_analysis.get("high_confidence_groups", 0)
            if high_confidence > 0:
                results.append([
                    "High Confidence Duplicates",
                    f"{high_confidence} groups",
                    "🟢 Auto-mergeable",
                    "Can be automatically processed"
                ])
        else:
            results.append([
                "Duplicate Detection",
                "No duplicates detected",
                "🟢 Clean",
                "Data appears to have no duplicates"
            ])
        
        # Data completeness
        original_data = quality_report.get("original_dataset", {})
        results.append([
            "Dataset Size",
            f"{original_data.get('total_tickets', 0)} tickets",
            "🔵 Info",
            f"Spanning {original_data.get('unique_sites', 0)} unique sites"
        ])
        
        # Add recommendations summary
        recommendations = quality_report.get("recommendations", [])
        if recommendations:
            results.append([
                "Key Recommendations",
                f"{len(recommendations)} items",
                "🔵 Action Required",
                "; ".join(recommendations[:2])  # Show first 2 recommendations
            ])
        
        columns = ["Metric", "Value", "Status", "Recommendation"]
        return results, columns
    
    def generate_duplicate_review_report(self, duplicate_groups: List) -> Tuple[List[List], List[str]]:
        """
        Generate Duplicate Review Report for manual processing
        Shows detailed duplicate groups requiring review
        """
        if not duplicate_groups:
            return [], ["Group ID", "Primary Ticket", "Duplicate Tickets", "Confidence", "Site", "Created Date", "Action Required"]
        
        results = []
        
        for idx, group in enumerate(duplicate_groups):
            primary = group.primary_ticket
            duplicates = group.duplicates
            
            # Format ticket numbers
            primary_number = str(primary.get('Number', 'N/A'))
            duplicate_numbers = ', '.join([str(dup.get('Number', 'N/A')) for dup in duplicates])
            
            # Determine action required
            confidence = group.confidence_score
            if confidence >= 0.95:
                action = "🤖 Auto-merge recommended"
            elif confidence >= 0.7:
                action = "👁️ Manual review required"
            else:
                action = "❓ Low confidence - verify"
            
            # Format creation date
            created_date = primary.get('Created', pd.NaT)
            date_str = created_date.strftime("%Y-%m-%d") if pd.notna(created_date) else "N/A"
            
            results.append([
                f"Group {idx + 1}",
                primary_number,
                duplicate_numbers,
                f"{confidence:.1%}",
                primary.get('Site', 'N/A'),
                date_str,
                action
            ])
        
        columns = ["Group ID", "Primary Ticket", "Duplicate Tickets", "Confidence", "Site", "Created Date", "Action Required"]
        return results, columns
    
    def generate_system_stability_dashboard(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate System Stability Dashboard Report
        Shows overall system health metrics and benchmarks
        """
        if df.empty:
            return [], ["Metric", "Current Value", "Target/Benchmark", "Status", "Trend"]
        
        # Calculate stability metrics
        stability_metrics = self.stability_analyzer.calculate_system_stability(df)
        
        results = []
        
        # Overall Stability Percentage
        stability_status = "🟢 Excellent" if stability_metrics.overall_stability_percentage >= 95 else \
                          "🟡 Good" if stability_metrics.overall_stability_percentage >= 85 else \
                          "🔴 Needs Attention"
        
        results.append([
            "Overall System Stability",
            f"{stability_metrics.overall_stability_percentage:.1f}%",
            "≥95% (Excellent)",
            stability_status,
            "📈" if stability_metrics.stability_trend == "improving" else 
            "📉" if stability_metrics.stability_trend == "declining" else "➡️"
        ])
        
        # Weighted Stability Score
        weighted_status = "🟢 Excellent" if stability_metrics.weighted_stability_score >= 95 else \
                         "🟡 Good" if stability_metrics.weighted_stability_score >= 85 else \
                         "🔴 Needs Attention"
        
        results.append([
            "Volume-Weighted Stability",
            f"{stability_metrics.weighted_stability_score:.1f}%",
            "≥95% (Excellent)",
            weighted_status,
            "📊" if abs(stability_metrics.weighted_stability_score - stability_metrics.overall_stability_percentage) > 5 else "➡️"
        ])
        
        # Critical Incident Rate
        critical_target = 5.0  # Target: <5% critical incidents
        critical_status = "🟢 Excellent" if stability_metrics.critical_incident_rate <= critical_target else \
                         "🟡 Acceptable" if stability_metrics.critical_incident_rate <= critical_target * 2 else \
                         "🔴 High"
        
        results.append([
            "Critical Incident Rate",
            f"{stability_metrics.critical_incident_rate:.1f}%",
            f"≤{critical_target}% (Target)",
            critical_status,
            "⚠️" if stability_metrics.critical_incident_rate > critical_target else "✅"
        ])
        
        # Mean Time to Recovery
        if stability_metrics.mean_time_to_recovery > 0:
            mttr_target = 4.0  # Target: <4 hours
            mttr_status = "🟢 Excellent" if stability_metrics.mean_time_to_recovery <= mttr_target else \
                         "🟡 Acceptable" if stability_metrics.mean_time_to_recovery <= mttr_target * 2 else \
                         "🔴 Slow"
            
            results.append([
                "Mean Time to Recovery",
                f"{stability_metrics.mean_time_to_recovery:.1f} hours",
                f"≤{mttr_target}h (Target)",
                mttr_status,
                "⏱️" if stability_metrics.mean_time_to_recovery > mttr_target else "⚡"
            ])
        
        # System Availability
        availability_target = 99.5
        availability_status = "🟢 Excellent" if stability_metrics.system_availability >= availability_target else \
                             "🟡 Good" if stability_metrics.system_availability >= 99.0 else \
                             "🔴 Poor"
        
        results.append([
            "System Availability",
            f"{stability_metrics.system_availability:.2f}%",
            f"≥{availability_target}% (Target)",
            availability_status,
            "🎯" if stability_metrics.system_availability >= availability_target else "📉"
        ])
        
        # Benchmark Score
        benchmark_status = "🟢 Exceeds" if stability_metrics.benchmark_score >= 90 else \
                          "🟡 Meets" if stability_metrics.benchmark_score >= 70 else \
                          "🔴 Below"
        
        results.append([
            "Industry Benchmark Score",
            f"{stability_metrics.benchmark_score:.1f}/100",
            "≥70 (Industry Standard)",
            benchmark_status,
            "🏆" if stability_metrics.benchmark_score >= 90 else "📊"
        ])
        
        # Site Performance Distribution
        if stability_metrics.site_performance_distribution:
            dist = stability_metrics.site_performance_distribution.get("distribution", {})
            excellent_pct = dist.get("excellent", {}).get("percentage", 0)
            needs_attention_pct = dist.get("needs_attention", {}).get("percentage", 0)
            
            results.append([
                "High-Performing Sites",
                f"{excellent_pct:.1f}% (≥95% stable)",
                "≥80% of sites",
                "🟢 Good" if excellent_pct >= 80 else "🟡 Fair" if excellent_pct >= 60 else "🔴 Low",
                "📈" if excellent_pct >= 80 else "📊"
            ])
            
            if needs_attention_pct > 0:
                results.append([
                    "Sites Needing Attention", 
                    f"{needs_attention_pct:.1f}% (<70% stable)",
                    "≤10% of sites",
                    "🔴 High" if needs_attention_pct > 20 else "🟡 Medium" if needs_attention_pct > 10 else "🟢 Low",
                    "⚠️" if needs_attention_pct > 10 else "✅"
                ])
        
        columns = ["Metric", "Current Value", "Target/Benchmark", "Status", "Trend"]
        return results, columns
    
    def generate_time_pattern_analysis_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Time Pattern Analysis Report
        Shows temporal patterns, synchronized incidents, and correlations
        """
        if df.empty:
            return [], ["Pattern Type", "Description", "Confidence", "Sites Affected", "Timeframe", "Recommendation"]
        
        # Analyze temporal patterns
        pattern_results = self.pattern_engine.analyze_temporal_patterns(df)
        
        results = []
        
        # Synchronized Incidents
        sync_incidents = pattern_results.get("synchronized_incidents", [])
        for i, sync_event in enumerate(sync_incidents[:5]):  # Show top 5
            results.append([
                f"🔗 Synchronized Event {i+1}",
                f"{sync_event.likely_root_cause} - {len(sync_event.sites)} sites affected",
                f"{sync_event.correlation_score:.1%}",
                f"{len(sync_event.sites)} sites",
                sync_event.timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(sync_event.timestamp, 'strftime') else str(sync_event.timestamp),
                "Investigate common infrastructure"
            ])
        
        # Site Correlations
        correlations = pattern_results.get("time_correlation_matrix", {}).get("high_correlations", [])
        for i, corr in enumerate(correlations[:5]):  # Show top 5
            results.append([
                f"📊 Site Correlation {i+1}",
                f"{corr['site1']} ↔ {corr['site2']} ({corr['strength']} correlation)",
                f"{corr['correlation']:.1%}",
                "2 sites",
                "Ongoing pattern",
                "Review shared dependencies"
            ])
        
        # Recurring Patterns
        recurring_patterns = pattern_results.get("recurring_patterns", [])
        for i, pattern in enumerate(recurring_patterns[:3]):  # Show top 3
            results.append([
                "🔄 Recurring Pattern",
                pattern.description,
                f"{pattern.confidence:.1%}",
                f"{len(pattern.sites)} site{'s' if len(pattern.sites) > 1 else ''}",
                f"{pattern.time_window[0].strftime('%Y-%m-%d')} to {pattern.time_window[1].strftime('%Y-%m-%d')}",
                "Schedule preventive maintenance"
            ])
        
        # Peak Time Analysis
        peak_times = pattern_results.get("peak_incident_times", {})
        if peak_times:
            peak_hour = peak_times.get("peak_hour", {})
            peak_day = peak_times.get("peak_day", {})
            
            if peak_hour.get("percentage", 0) > 10:
                results.append([
                    "⏰ Peak Hour Pattern",
                    f"Most incidents at {peak_hour.get('hour', 0):02d}:00 ({peak_hour.get('percentage', 0):.1f}%)",
                    "High",
                    "All sites",
                    "Daily pattern",
                    "Review operations during peak hour"
                ])
            
            if peak_day.get("percentage", 0) > 20:
                results.append([
                    "📅 Peak Day Pattern", 
                    f"Most incidents on {peak_day.get('day', 'Unknown')}s ({peak_day.get('percentage', 0):.1f}%)",
                    "High",
                    "All sites", 
                    "Weekly pattern",
                    "Investigate day-specific factors"
                ])
        
        # Seasonal Patterns
        seasonal_patterns = pattern_results.get("seasonal_patterns", [])
        for pattern in seasonal_patterns[:2]:  # Show top 2
            results.append([
                "🌊 Seasonal Pattern",
                pattern.description,
                f"{pattern.confidence:.1%}",
                f"{len(pattern.sites)} sites",
                "Annual/Monthly cycle",
                "Plan seasonal capacity"
            ])
        
        # Anomalies
        anomalies = pattern_results.get("anomaly_detection", [])
        for i, anomaly in enumerate(anomalies[:3]):  # Show top 3
            if anomaly['type'] == 'volume_spike':
                results.append([
                    "📈 Volume Anomaly",
                    f"Unusual spike on {anomaly['date']} ({anomaly['incident_count']} incidents)",
                    "High",
                    f"{anomaly['affected_sites']} sites",
                    anomaly['date'],
                    "Investigate root cause of spike"
                ])
        
        if not results:
            results.append([
                "No Patterns Detected",
                "No significant temporal patterns found in current data",
                "N/A",
                "N/A",
                "N/A",
                "Continue monitoring for patterns"
            ])
        
        columns = ["Pattern Type", "Description", "Confidence", "Sites Affected", "Timeframe", "Recommendation"]
        return results, columns
    
    def generate_stability_insights_report(self, df: pd.DataFrame) -> Tuple[List[List], List[str]]:
        """
        Generate Stability Insights Report
        Combines stability metrics and pattern analysis for actionable insights
        """
        if df.empty:
            return [], ["Insight Category", "Finding", "Impact Level", "Action Required", "Priority"]
        
        results = []
        
        # Get stability metrics and pattern analysis
        stability_metrics = self.stability_analyzer.calculate_system_stability(df)
        pattern_results = self.pattern_engine.analyze_temporal_patterns(df)
        
        # Generate stability insights
        stability_insights = self.stability_analyzer.generate_stability_insights(stability_metrics)
        
        for insight in stability_insights[:5]:  # Top 5 stability insights
            # Extract priority and impact from insight text
            if "🔴" in insight or "critical" in insight.lower() or "immediate" in insight.lower():
                priority = "🔴 High"
                impact = "🔴 High"
                action = "Immediate investigation required"
            elif "🟡" in insight or "review" in insight.lower() or "attention" in insight.lower():
                priority = "🟡 Medium"
                impact = "🟡 Medium"
                action = "Review and plan improvements"
            else:
                priority = "🟢 Low"
                impact = "🟢 Low"  
                action = "Continue monitoring"
            
            # Clean up insight text (remove emojis for category)
            clean_insight = insight.replace("🟢", "").replace("🟡", "").replace("🔴", "").replace("⚠️", "").replace("✅", "").replace("📈", "").replace("📉", "").replace("➡️", "").replace("⏱️", "").replace("⚡", "").replace("🚨", "").replace("🎯", "").replace("🏆", "").replace("📊", "").strip()
            
            results.append([
                "📊 System Stability",
                clean_insight,
                impact,
                action,
                priority
            ])
        
        # Generate pattern insights
        pattern_insights = pattern_results.get("pattern_insights", [])
        
        for insight in pattern_insights[:3]:  # Top 3 pattern insights
            if "synchronized" in insight.lower() or "correlation" in insight.lower():
                priority = "🟡 Medium"
                impact = "🟡 Medium"
                action = "Investigate shared dependencies"
                category = "🔗 Pattern Analysis"
            elif "peak" in insight.lower() or "recurring" in insight.lower():
                priority = "🟢 Low"
                impact = "🟢 Low"
                action = "Optimize operations timing"
                category = "⏰ Temporal Patterns"
            else:
                priority = "🟢 Low"
                impact = "🟢 Low"
                action = "Continue pattern monitoring"
                category = "📈 Trend Analysis"
            
            # Clean up insight text
            clean_insight = insight.replace("🔗", "").replace("📊", "").replace("⏰", "").replace("📅", "").replace("🔄", "").replace("🌊", "").replace("📈", "").replace("🎯", "").strip()
            
            results.append([
                category,
                clean_insight,
                impact,
                action,
                priority
            ])
        
        # Add site performance insights
        if stability_metrics.site_performance_distribution:
            dist = stability_metrics.site_performance_distribution.get("distribution", {})
            needs_attention = dist.get("needs_attention", {}).get("count", 0)
            
            if needs_attention > 0:
                results.append([
                    "🏢 Site Performance",
                    f"{needs_attention} sites performing below 70% stability threshold",
                    "🟡 Medium",
                    "Focus improvement efforts on underperforming sites",
                    "🟡 Medium"
                ])
            
            top_performers = stability_metrics.site_performance_distribution.get("top_performers", [])
            if top_performers:
                results.append([
                    "🏆 Best Practices",
                    f"Top performing sites: {', '.join(top_performers[:3])}",
                    "🟢 Low",
                    "Share best practices from high-performing sites",
                    "🟢 Low"
                ])
        
        # Add benchmark insights
        if stability_metrics.benchmark_score < 70:
            results.append([
                "📊 Benchmark Performance",
                f"Overall benchmark score ({stability_metrics.benchmark_score:.1f}/100) below industry standards",
                "🔴 High",
                "Implement improvement plan to meet industry benchmarks",
                "🔴 High"
            ])
        elif stability_metrics.benchmark_score >= 90:
            results.append([
                "🏆 Performance Excellence",
                f"Benchmark score ({stability_metrics.benchmark_score:.1f}/100) exceeds industry standards",
                "🟢 Low",
                "Maintain current excellence and share best practices",
                "🟢 Low"
            ])
        
        if not results:
            results.append([
                "✅ System Health",
                "System appears to be operating normally with no major issues detected",
                "🟢 Low",
                "Continue regular monitoring",
                "🟢 Low"
            ])
        
        columns = ["Insight Category", "Finding", "Impact Level", "Action Required", "Priority"]
        return results, columns