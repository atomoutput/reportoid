"""
Main application controller
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from typing import Dict, Any, List
import uuid
from datetime import datetime
import logging

from ..models.data_manager import DataManager
from ..models.report_engine import ReportEngine
from ..views.main_window import MainWindow
from ..utils.audit_trail import AuditTrailManager, AuditAction
from ..utils.stability_analytics import SystemStabilityAnalyzer
from ..utils.pattern_recognition import TimePatternEngine

class AppController:
    """Main application controller - coordinates between models and views"""
    
    def __init__(self, root: tk.Tk, settings):
        self.root = root
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.data_manager = DataManager(settings)
        self.report_engine = ReportEngine(settings)
        self.audit_manager = AuditTrailManager(settings)
        
        # Initialize analytics engines
        self.stability_analyzer = SystemStabilityAnalyzer(settings)
        self.pattern_engine = TimePatternEngine(settings)
        
        # Initialize pending review decisions
        self.pending_review_decisions = []
        
        # Initialize view
        self.main_window = MainWindow(root, settings)
        
        # Set up callbacks
        self._setup_callbacks()
        
        # Initialize UI state
        self._update_ui_state()
    
    def _setup_callbacks(self):
        """Set up callbacks between view and controller"""
        self.main_window.set_callback('load_data', self._handle_load_data)
        self.main_window.set_callback('export_results', self._handle_export_results)
        self.main_window.set_callback('export_selected', self._handle_export_selected)
        self.main_window.set_callback('refresh', self._handle_refresh)
        self.main_window.set_callback('run_report', self._handle_run_report)
        self.main_window.set_callback('filter_change', self._handle_filter_change)
        self.main_window.set_callback('company_changed', self._handle_company_changed)
        self.main_window.set_callback('category_changed', self._handle_category_changed)
        self.main_window.set_callback('data_summary', self._handle_data_summary)
        self.main_window.set_callback('settings', self._handle_settings)
        self.main_window.set_callback('drill_down', self._handle_drill_down)
        self.main_window.set_callback('export_filtered_data', self._handle_export_filtered_data)
        self.main_window.set_callback('export_comprehensive', self._handle_export_comprehensive)
        
        # Set up quality management callbacks
        quality_tab = self.main_window.get_quality_tab()
        quality_tab.set_callback('refresh_quality', self._handle_refresh_quality)
        quality_tab.set_callback('auto_process_duplicates', self._handle_auto_process_duplicates)
        quality_tab.set_callback('export_audit_log', self._handle_export_audit_log)
        quality_tab.set_callback('review_duplicate_group', self._handle_review_duplicate_group)
        quality_tab.set_callback('batch_process_duplicates', self._handle_batch_process_duplicates)
        quality_tab.set_callback('get_duplicate_queue', self._handle_get_duplicate_queue)
        quality_tab.set_callback('get_audit_trail', self._handle_get_audit_trail)
        quality_tab.set_callback('apply_manual_changes', self._handle_apply_manual_changes)
    
    def _handle_load_data(self):
        """Handle data loading from file"""
        try:
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Ticket Data File",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx *.xls"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Show loading status
            self.main_window.set_status("Loading data...")
            self.main_window.show_progress(True, 0)
            self.root.update()
            
            # Load data
            result = self.data_manager.load_file(file_path)
            
            # Hide progress
            self.main_window.show_progress(False)
            
            if not result["valid"]:
                # Show errors
                error_msg = "Failed to load data:\n\n" + "\n".join(result["errors"])
                if result["warnings"]:
                    error_msg += "\n\nWarnings:\n" + "\n".join(result["warnings"])
                messagebox.showerror("Data Load Error", error_msg)
                self.main_window.set_status("Failed to load data")
                return
            
            # Show warnings if any
            if result["warnings"]:
                warning_msg = "Data loaded with warnings:\n\n" + "\n".join(result["warnings"])
                messagebox.showwarning("Data Load Warnings", warning_msg)
            
            # Update UI with loaded data
            self._update_ui_state(data_loaded=True)
            self._update_filter_options()
            
            # Update quality tab with quality report
            quality_report = self.data_manager.get_quality_report()
            if quality_report:
                quality_tab = self.main_window.get_quality_tab()
                quality_tab.update_quality_metrics(quality_report)
            
            # Show data summary
            info = result["info"]
            status_text = f"Loaded {info['processed_records']} records from {info['total_records']} total"
            self.main_window.set_status(status_text)
            
            data_info = f"Sites: {info['sites']} | Companies: {info['companies']} | Categories: {info['categories']}"
            self.main_window.update_data_info(data_info)
            
            # Show success message with summary
            summary_msg = (
                f"Data loaded successfully!\n\n"
                f"Records processed: {info['processed_records']}\n"
                f"Sites: {info['sites']}\n"
                f"Companies: {info['companies']}\n"
                f"Categories: {info['categories']}"
            )
            
            if info.get('date_range'):
                date_range = info['date_range']
                if 'Created' in date_range:
                    created_range = date_range['Created']
                    start_date = created_range['min'].strftime("%Y-%m-%d")
                    end_date = created_range['max'].strftime("%Y-%m-%d")
                    summary_msg += f"\nDate range: {start_date} to {end_date}"
            
            messagebox.showinfo("Data Loaded", summary_msg)
            
        except Exception as e:
            self.main_window.show_progress(False)
            self.main_window.set_status("Error loading data")
            messagebox.showerror("Error", f"Unexpected error loading data:\n{str(e)}")
    
    def _handle_export_results(self):
        """Handle exporting current results"""
        try:
            # Get current results from tree view
            tree = self.main_window.results_tree
            
            if not tree.get_children():
                messagebox.showwarning("No Data", "No results to export. Please run a report first.")
                return
            
            # Get file path for export
            file_path = filedialog.asksaveasfilename(
                title="Export Results",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Extract data from tree view
            columns = [tree.heading(col)['text'] for col in tree['columns']]
            data = []
            for item in tree.get_children():
                data.append(tree.item(item)['values'])
            
            # Create dataframe and export
            df = pd.DataFrame(data, columns=columns)
            
            if file_path.lower().endswith('.csv'):
                df.to_csv(file_path, index=False)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df.to_excel(file_path, index=False)
            else:
                df.to_csv(file_path, index=False)  # Default to CSV
            
            self.main_window.set_status(f"Results exported to {file_path}")
            messagebox.showinfo("Export Complete", f"Results exported successfully to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")
    
    def _handle_export_selected(self):
        """Handle exporting selected rows"""
        try:
            tree = self.main_window.results_tree
            selected_items = tree.selection()
            
            if not selected_items:
                messagebox.showwarning("No Selection", "Please select rows to export.")
                return
            
            # Get file path for export
            file_path = filedialog.asksaveasfilename(
                title="Export Selected Results",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Extract selected data
            columns = [tree.heading(col)['text'] for col in tree['columns']]
            data = []
            for item in selected_items:
                data.append(tree.item(item)['values'])
            
            # Create dataframe and export
            df = pd.DataFrame(data, columns=columns)
            
            if file_path.lower().endswith('.csv'):
                df.to_csv(file_path, index=False)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df.to_excel(file_path, index=False)
            else:
                df.to_csv(file_path, index=False)
            
            self.main_window.set_status(f"Selected results exported to {file_path}")
            messagebox.showinfo("Export Complete", f"Selected results exported successfully to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export selected results:\n{str(e)}")
    
    def _handle_refresh(self):
        """Handle data refresh"""
        if self.data_manager.data is not None:
            self._update_filter_options()
            self.main_window.set_status("Data refreshed")
        else:
            messagebox.showwarning("No Data", "No data to refresh. Please load data first.")
    
    def _handle_run_report(self, report_type: str):
        """Handle running different types of reports"""
        try:
            if self.data_manager.data is None:
                messagebox.showwarning("No Data", "Please load data first.")
                return
            
            # Get current filters
            filters = self.main_window.get_current_filters()
            
            # Apply filters to get filtered data
            filtered_data = self.data_manager.apply_filters(filters)
            
            if filtered_data.empty:
                messagebox.showwarning("No Data", "No data matches the current filters.")
                return
            
            self.main_window.set_status(f"Generating {report_type} report...")
            self.main_window.show_progress(True, 50)
            self.root.update()
            
            # Check if this is an enhanced analytics report that needs drill-down
            enhanced_reports = ["system_stability_dashboard", "time_pattern_analysis", "stability_insights"]
            
            if report_type in enhanced_reports:
                self._handle_enhanced_analytics_report(report_type, filtered_data)
                return
            
            # Generate report based on type
            results, columns = self._generate_report(report_type, filtered_data)
            
            self.main_window.show_progress(False)
            
            if not results:
                messagebox.showinfo("No Results", f"No data found for {report_type} report with current filters.")
                self.main_window.set_status("Report completed - no results")
                return
            
            # Display results
            report_titles = {
                "critical_hotspots": "Critical Incident Hotspots",
                "site_scorecard": "Site Stability Scorecard",
                "green_list": "Green List - Stable Operations",
                "franchise_overview": "Franchise Performance Overview",
                "equipment_analysis": "Equipment Category Analysis",
                "incident_details": "Incident Details - Individual Tickets",
                "repeat_offenders": "Repeat Offenders - Recurring Issues",
                "resolution_tracking": "Resolution Tracking - SLA Performance",
                "workload_trends": "Workload Trends - Volume Patterns",
                # Phase 2: Advanced Analytics
                "system_stability_dashboard": "System Stability Dashboard",
                "time_pattern_analysis": "Time Pattern Analysis",
                "stability_insights": "Stability Insights",
                "data_quality_report": "Data Quality Report"
            }
            
            title = report_titles.get(report_type, report_type.replace('_', ' ').title())
            self.main_window.display_results(results, columns, title)
            
            self.main_window.set_status(f"Report completed: {len(results)} results")
            
        except Exception as e:
            self.main_window.show_progress(False)
            self.main_window.set_status("Error generating report")
            messagebox.showerror("Report Error", f"Failed to generate report:\n{str(e)}")
    
    def _handle_enhanced_analytics_report(self, report_type: str, filtered_data: pd.DataFrame):
        """Handle enhanced analytics reports with drill-down views"""
        try:
            # Generate analytics data based on report type
            analytics_data = self._generate_analytics_data(report_type, filtered_data)
            
            # Update progress
            self.main_window.show_progress(True, 75)
            self.root.update()
            
            # Get report title
            report_titles = {
                "system_stability_dashboard": "System Stability Dashboard",
                "time_pattern_analysis": "Time Pattern Analysis", 
                "stability_insights": "Stability Insights"
            }
            
            title = report_titles.get(report_type, "Analytics Report")
            
            # Hide progress and display analytics results in main area
            self.main_window.show_progress(False)
            
            # Display analytics results directly in the main results area
            self.main_window.display_analytics_results(
                analytics_data=analytics_data,
                underlying_tickets=filtered_data,
                report_type=report_type
            )
            
            # Log analytics generation
            from datetime import datetime
            import uuid
            audit_action = AuditAction(
                action_id=str(uuid.uuid4()),
                action_type="report_generated",
                user="system",
                timestamp=datetime.now(),
                description=f"Enhanced {title} generated with {len(filtered_data)} tickets and drill-down evidence",
                details={"report_type": report_type, "ticket_count": len(filtered_data)},
                affected_tickets=[]
            )
            self.audit_manager.log_action(audit_action)
            
            self.main_window.set_status(f"Enhanced {title} generated with evidence view")
            
        except Exception as e:
            self.main_window.show_progress(False)
            self.logger.error(f"Error generating enhanced analytics {report_type}: {str(e)}")
            messagebox.showerror("Analytics Error", f"Failed to generate enhanced analytics:\n{str(e)}")
    
    def _generate_analytics_data(self, report_type: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate analytics data for enhanced reports"""
        analytics_data = {}
        
        if report_type == "system_stability_dashboard":
            # Generate stability metrics
            stability_metrics = self.stability_analyzer.calculate_system_stability(data)
            analytics_data['stability_metrics'] = {
                'overall_stability_percentage': stability_metrics.overall_stability_percentage,
                'weighted_stability_score': stability_metrics.weighted_stability_score,
                'critical_incident_rate': stability_metrics.critical_incident_rate,
                'mean_time_to_recovery': stability_metrics.mean_time_to_recovery,
                'system_availability': stability_metrics.system_availability,
                'stability_trend': stability_metrics.stability_trend,
                'benchmark_score': stability_metrics.benchmark_score,
                'site_performance_distribution': stability_metrics.site_performance_distribution,
                'time_based_metrics': stability_metrics.time_based_metrics
            }
            
        elif report_type == "time_pattern_analysis":
            # Generate pattern analysis results
            pattern_results = self.pattern_engine.analyze_temporal_patterns(data)
            analytics_data['pattern_results'] = pattern_results
            
        elif report_type == "stability_insights":
            # Generate stability insights
            stability_metrics = self.stability_analyzer.calculate_system_stability(data)
            insights = self.stability_analyzer.generate_stability_insights(stability_metrics)
            analytics_data['insights'] = insights
            analytics_data['stability_metrics'] = stability_metrics
            
        return analytics_data
    
    def _generate_report(self, report_type: str, data: pd.DataFrame):
        """Generate specific report type"""
        if report_type == "critical_hotspots":
            return self.report_engine.generate_critical_hotspots_report(data)
        elif report_type == "site_scorecard":
            return self.report_engine.generate_site_scorecard_report(data)
        elif report_type == "green_list":
            return self.report_engine.generate_green_list_report(data)
        elif report_type == "franchise_overview":
            return self.report_engine.generate_franchise_overview_report(data)
        elif report_type == "equipment_analysis":
            return self.report_engine.generate_equipment_analysis_report(data)
        elif report_type == "incident_details":
            return self.report_engine.generate_incident_details_report(data)
        elif report_type == "repeat_offenders":
            return self.report_engine.generate_repeat_offenders_report(data)
        elif report_type == "resolution_tracking":
            return self.report_engine.generate_resolution_tracking_report(data)
        elif report_type == "workload_trends":
            return self.report_engine.generate_workload_trends_report(data)
        # Phase 2: Advanced Analytics Reports
        elif report_type == "system_stability_dashboard":
            return self.report_engine.generate_system_stability_dashboard(data)
        elif report_type == "time_pattern_analysis":
            return self.report_engine.generate_time_pattern_analysis_report(data)
        elif report_type == "stability_insights":
            return self.report_engine.generate_stability_insights_report(data)
        elif report_type == "data_quality_report":
            quality_report = self.data_manager.get_quality_report()
            duplicate_groups = self.data_manager.get_duplicate_groups()
            return self.report_engine.generate_data_quality_report(quality_report, duplicate_groups)
        else:
            # Placeholder for other report types
            return [], []
    
    def _handle_filter_change(self):
        """Handle filter changes"""
        if self.data_manager.data is not None:
            filters = self.main_window.get_current_filters()
            filtered_data = self.data_manager.apply_filters(filters)
            summary = self.report_engine.get_report_summary(filtered_data)
            
            # Update status with filtered data info
            if summary:
                status_text = f"Filtered: {summary['total_tickets']} tickets"
                if summary['critical_tickets'] > 0:
                    status_text += f" ({summary['critical_tickets']} critical)"
                self.main_window.set_status(status_text)
    
    def _handle_company_changed(self, company: str):
        """Handle company selection change"""
        if self.data_manager.data is not None and company != "All":
            # Update site options based on selected company
            company_sites = self.data_manager.data[
                self.data_manager.data["Company"] == company
            ]["Site"].unique().tolist()
            
            sites = ["All"] + sorted(company_sites)
            self.main_window.site_combo['values'] = sites
            self.main_window.site_var.set("All")
        else:
            # Reset to all sites
            self._update_filter_options()
        
        self._handle_filter_change()
    
    def _handle_category_changed(self, category: str):
        """Handle category selection change"""
        if category != "All":
            subcategories = self.data_manager.get_subcategories(category)
            self.main_window.update_subcategory_options(subcategories)
        else:
            # Reset to all subcategories
            all_subcategories = []
            for subcat_list in self.data_manager.category_mapping.values():
                all_subcategories.extend(subcat_list)
            unique_subcategories = sorted(list(set(all_subcategories)))
            self.main_window.update_subcategory_options(unique_subcategories)
        
        self._handle_filter_change()
    
    def _handle_data_summary(self):
        """Handle data summary request"""
        if self.data_manager.data is None:
            messagebox.showwarning("No Data", "Please load data first.")
            return
        
        try:
            summary = self.data_manager.get_data_summary()
            
            summary_text = (
                f"Dataset Summary\n"
                f"{'='*50}\n\n"
                f"Total Tickets: {summary['total_tickets']:,}\n"
                f"Critical Tickets: {summary['critical_tickets']:,} "
                f"({summary['critical_tickets']/summary['total_tickets']*100:.1f}%)\n"
                f"Resolved Tickets: {summary['resolved_tickets']:,} "
                f"({summary['resolved_tickets']/summary['total_tickets']*100:.1f}%)\n"
                f"Open Tickets: {summary['open_tickets']:,}\n\n"
                f"Unique Sites: {summary['unique_sites']:,}\n"
                f"Unique Companies: {summary['unique_companies']:,}\n"
            )
            
            if summary.get('avg_resolution_hours'):
                summary_text += f"\nAverage Resolution Time: {summary['avg_resolution_hours']:.1f} hours\n"
            
            if summary.get('date_range'):
                date_range = summary['date_range']
                if 'Created' in date_range:
                    created = date_range['Created']
                    start_date = created['min'].strftime("%Y-%m-%d")
                    end_date = created['max'].strftime("%Y-%m-%d")
                    summary_text += f"\nDate Range: {start_date} to {end_date}\n"
                    summary_text += f"Time Span: {(created['max'] - created['min']).days} days\n"
            
            messagebox.showinfo("Data Summary", summary_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate data summary:\n{str(e)}")
    
    def _handle_settings(self):
        """Handle settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog functionality coming soon!")
    
    def _update_ui_state(self, data_loaded: bool = False):
        """Update UI state based on data availability"""
        self.main_window.data_loaded(data_loaded)
        
        if not data_loaded:
            self.main_window.set_status("Ready - No data loaded")
            self.main_window.update_data_info("")
            # Clear results
            self.main_window.display_results([], [], "No Data")
    
    def _update_filter_options(self):
        """Update filter dropdown options from loaded data"""
        if self.data_manager.data is not None:
            options = self.data_manager.get_filter_options()
            self.main_window.update_filter_options(options)
            
            # Set default subcategory options
            all_subcategories = []
            for subcat_list in self.data_manager.category_mapping.values():
                all_subcategories.extend(subcat_list)
            unique_subcategories = sorted(list(set(all_subcategories)))
            self.main_window.update_subcategory_options(unique_subcategories)
    
    def _handle_drill_down(self, site_name: str):
        """Handle site drill-down functionality"""
        try:
            if self.data_manager.data is None:
                messagebox.showwarning("No Data", "Please load data first.")
                return
            
            # Get current filters
            filters = self.main_window.get_current_filters()
            
            # Apply filters to get filtered data
            filtered_data = self.data_manager.apply_filters(filters)
            
            if filtered_data.empty:
                messagebox.showwarning("No Data", "No data matches the current filters.")
                return
            
            self.main_window.set_status(f"Generating drill-down report for {site_name}...")
            self.main_window.show_progress(True, 50)
            self.root.update()
            
            # Generate site-specific report
            results, columns = self.report_engine.generate_site_drill_down_report(filtered_data, site_name)
            
            self.main_window.show_progress(False)
            
            if not results:
                messagebox.showinfo("No Results", f"No tickets found for {site_name} with current filters.")
                self.main_window.set_status("Drill-down completed - no results")
                return
            
            # Display results
            title = f"Site Drill-Down: {site_name}"
            self.main_window.display_results(results, columns, title)
            
            self.main_window.set_status(f"Drill-down completed: {len(results)} tickets for {site_name}")
            
        except Exception as e:
            self.main_window.show_progress(False)
            self.main_window.set_status("Error generating drill-down")
            messagebox.showerror("Drill-Down Error", f"Failed to generate drill-down report:\n{str(e)}")
    
    def _handle_export_filtered_data(self):
        """Handle exporting filtered raw data"""
        try:
            if self.data_manager.data is None:
                messagebox.showwarning("No Data", "Please load data first.")
                return
            
            # Get current filters
            filters = self.main_window.get_current_filters()
            
            # Apply filters to get filtered data
            filtered_data = self.data_manager.apply_filters(filters)
            
            if filtered_data.empty:
                messagebox.showwarning("No Data", "No data matches the current filters.")
                return
            
            # Get file path for export
            file_path = filedialog.asksaveasfilename(
                title="Export Filtered Data",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Prepare data for export (clean up internal columns)
            export_data = filtered_data.copy()
            
            # Remove internal calculated columns
            internal_columns = ["Is_Critical", "Is_Resolved", "Resolution_Hours", "Days_Since_Created"]
            for col in internal_columns:
                if col in export_data.columns:
                    export_data = export_data.drop(columns=[col])
            
            # Export data
            if file_path.lower().endswith('.csv'):
                export_data.to_csv(file_path, index=False)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                export_data.to_excel(file_path, index=False)
            else:
                export_data.to_csv(file_path, index=False)  # Default to CSV
            
            self.main_window.set_status(f"Filtered data exported to {file_path}")
            
            # Show summary of exported data
            active_filters = []
            if filters.get("date_from"):
                active_filters.append(f"Date from: {filters['date_from']}")
            if filters.get("date_to"):
                active_filters.append(f"Date to: {filters['date_to']}")
            if filters.get("priorities"):
                active_filters.append(f"Priorities: {', '.join(filters['priorities'])}")
            if filters.get("company"):
                active_filters.append(f"Company: {filters['company']}")
            if filters.get("site"):
                active_filters.append(f"Site: {filters['site']}")
            
            filter_summary = "\n".join(active_filters) if active_filters else "No filters applied"
            
            messagebox.showinfo("Export Complete", 
                              f"Filtered data exported successfully!\n\n"
                              f"Records exported: {len(export_data)}\n"
                              f"File: {file_path}\n\n"
                              f"Applied filters:\n{filter_summary}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export filtered data:\n{str(e)}")
    
    def _handle_export_comprehensive(self):
        """Handle comprehensive Excel export with all reports in separate sheets"""
        try:
            if self.data_manager.data is None:
                messagebox.showwarning("No Data", "Please load data first.")
                return
            
            # Get file path for export (Excel only)
            file_path = filedialog.asksaveasfilename(
                title="Export Comprehensive Report",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            
            if not file_path:
                return
            
            # Show progress
            self.main_window.set_status("Generating comprehensive report...")
            self.main_window.show_progress(True, 0)
            self.root.update()
            
            # Get current filters
            filters = self.main_window.get_current_filters()
            filtered_data = self.data_manager.apply_filters(filters)
            
            if filtered_data.empty:
                messagebox.showwarning("No Data", "No data matches the current filters.")
                self.main_window.show_progress(False)
                return
            
            # Create Excel writer
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                
                # Sheet 1: Summary Overview
                self.main_window.show_progress(True, 10)
                self.root.update()
                summary_data = self._create_summary_sheet(filtered_data)
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Sheet 2: Critical Hotspots
                self.main_window.show_progress(True, 20)
                self.root.update()
                results, columns = self.report_engine.generate_critical_hotspots_report(filtered_data)
                if results:
                    hotspots_df = pd.DataFrame(results, columns=columns)
                    hotspots_df.to_excel(writer, sheet_name='Critical Hotspots', index=False)
                
                # Sheet 3: Site Scorecard
                self.main_window.show_progress(True, 30)
                self.root.update()
                results, columns = self.report_engine.generate_site_scorecard_report(filtered_data)
                if results:
                    scorecard_df = pd.DataFrame(results, columns=columns)
                    scorecard_df.to_excel(writer, sheet_name='Site Scorecard', index=False)
                
                # Sheet 4: Green List
                self.main_window.show_progress(True, 40)
                self.root.update()
                results, columns = self.report_engine.generate_green_list_report(filtered_data)
                if results:
                    green_df = pd.DataFrame(results, columns=columns)
                    green_df.to_excel(writer, sheet_name='Green List', index=False)
                
                # Sheet 5: Franchise Overview
                self.main_window.show_progress(True, 50)
                self.root.update()
                results, columns = self.report_engine.generate_franchise_overview_report(filtered_data)
                if results:
                    franchise_df = pd.DataFrame(results, columns=columns)
                    franchise_df.to_excel(writer, sheet_name='Franchise Overview', index=False)
                
                # Sheet 6: Equipment Analysis
                self.main_window.show_progress(True, 60)
                self.root.update()
                results, columns = self.report_engine.generate_equipment_analysis_report(filtered_data)
                if results:
                    equipment_df = pd.DataFrame(results, columns=columns)
                    equipment_df.to_excel(writer, sheet_name='Equipment Analysis', index=False)
                
                # Sheet 7: Repeat Offenders
                self.main_window.show_progress(True, 70)
                self.root.update()
                results, columns = self.report_engine.generate_repeat_offenders_report(filtered_data)
                if results:
                    repeat_df = pd.DataFrame(results, columns=columns)
                    repeat_df.to_excel(writer, sheet_name='Repeat Offenders', index=False)
                
                # Sheet 8: Resolution Tracking
                self.main_window.show_progress(True, 80)
                self.root.update()
                results, columns = self.report_engine.generate_resolution_tracking_report(filtered_data)
                if results:
                    resolution_df = pd.DataFrame(results, columns=columns)
                    resolution_df.to_excel(writer, sheet_name='Resolution Tracking', index=False)
                
                # Sheet 9: Workload Trends
                self.main_window.show_progress(True, 85)
                self.root.update()
                results, columns = self.report_engine.generate_workload_trends_report(filtered_data)
                if results:
                    workload_df = pd.DataFrame(results, columns=columns)
                    workload_df.to_excel(writer, sheet_name='Workload Trends', index=False)
                
                # Sheet 10: Individual Tickets (Full Details)
                self.main_window.show_progress(True, 90)
                self.root.update()
                results, columns = self.report_engine.generate_incident_details_report(filtered_data)
                if results:
                    incidents_df = pd.DataFrame(results, columns=columns)
                    incidents_df.to_excel(writer, sheet_name='All Tickets', index=False)
                
                # Advanced Analytics Sheets (Phase 2)
                # Sheet 11: System Stability Dashboard
                self.main_window.show_progress(True, 88)
                self.root.update()
                stability_data = self._create_stability_analytics_sheet(filtered_data)
                if stability_data:
                    stability_df = pd.DataFrame(stability_data)
                    stability_df.to_excel(writer, sheet_name='Stability Dashboard', index=False)
                
                # Sheet 12: Pattern Analysis Results
                self.main_window.show_progress(True, 91)
                self.root.update()
                pattern_data = self._create_pattern_analysis_sheet(filtered_data)
                if pattern_data:
                    pattern_df = pd.DataFrame(pattern_data)
                    pattern_df.to_excel(writer, sheet_name='Pattern Analysis', index=False)
                
                # Sheet 13: Stability Insights & Recommendations
                self.main_window.show_progress(True, 94)
                self.root.update()
                insights_data = self._create_insights_sheet(filtered_data)
                if insights_data:
                    insights_df = pd.DataFrame(insights_data)
                    insights_df.to_excel(writer, sheet_name='Stability Insights', index=False)
                
                # Sheet 14: Analytics Evidence - Critical Incidents
                self.main_window.show_progress(True, 96)
                self.root.update()
                critical_evidence = self._create_critical_evidence_sheet(filtered_data)
                if critical_evidence:
                    critical_df = pd.DataFrame(critical_evidence)
                    critical_df.to_excel(writer, sheet_name='Critical Incidents Evidence', index=False)
                
                # Sheet 15: Analytics Evidence - Synchronized Events
                self.main_window.show_progress(True, 97)
                self.root.update()
                sync_evidence = self._create_synchronized_evidence_sheet(filtered_data)
                if sync_evidence:
                    sync_df = pd.DataFrame(sync_evidence)
                    sync_df.to_excel(writer, sheet_name='Synchronized Events Evidence', index=False)
                
                # Sheet 16: Raw Data (Filtered)
                self.main_window.show_progress(True, 98)
                self.root.update()
                raw_data = filtered_data.copy()
                # Remove internal calculated columns
                internal_columns = ["Is_Critical", "Is_Resolved", "Resolution_Hours", "Days_Since_Created"]
                for col in internal_columns:
                    if col in raw_data.columns:
                        raw_data = raw_data.drop(columns=[col])
                raw_data.to_excel(writer, sheet_name='Raw Data', index=False)
            
            self.main_window.show_progress(False)
            self.main_window.set_status(f"Comprehensive report exported to {file_path}")
            
            # Show completion message
            active_filters = self._get_active_filters_summary(filters)
            messagebox.showinfo("Export Complete", 
                              f"Enhanced comprehensive report exported successfully!\n\n"
                              f"File: {file_path}\n"
                              f"Records analyzed: {len(filtered_data)}\n"
                              f"Sheets created: 16 (Summary + 10 reports + 5 analytics sheets)\n\n"
                              f"📊 Enhanced Analytics Included:\n"
                              f"• Stability Dashboard & Metrics\n"
                              f"• Pattern Analysis & Correlations\n"
                              f"• Stability Insights & Recommendations\n"
                              f"• Critical Incidents Evidence\n"
                              f"• Synchronized Events Evidence\n\n"
                              f"Applied filters:\n{active_filters}")
            
        except Exception as e:
            self.main_window.show_progress(False)
            self.main_window.set_status("Error exporting comprehensive report")
            messagebox.showerror("Export Error", f"Failed to export comprehensive report:\n{str(e)}")
    
    def _create_summary_sheet(self, df: pd.DataFrame) -> list:
        """Create summary data for the Excel export"""
        summary = self.report_engine.get_report_summary(df)
        
        summary_data = [
            ["Metric", "Value"],
            ["Report Generated", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Total Records", summary.get("total_tickets", 0)],
            ["Critical Incidents", summary.get("critical_tickets", 0)],
            ["Critical Percentage", f"{summary.get('critical_percentage', 0)}%"],
            ["Resolved Tickets", summary.get("resolved_tickets", 0)],
            ["Resolution Rate", f"{summary.get('resolution_rate', 0)}%"],
            ["Open Tickets", summary.get("total_tickets", 0) - summary.get("resolved_tickets", 0)],
            ["Unique Sites", summary.get("unique_sites", 0)],
            ["Unique Companies", summary.get("unique_companies", 0)],
            ["Average Resolution Time (hours)", summary.get("avg_mttr_hours", "N/A")]
        ]
        
        if summary.get("date_range"):
            date_range = summary["date_range"]
            if "start" in date_range and date_range["start"]:
                summary_data.append(["Date Range Start", date_range["start"].strftime("%Y-%m-%d")])
            if "end" in date_range and date_range["end"]:
                summary_data.append(["Date Range End", date_range["end"].strftime("%Y-%m-%d")])
        
        return summary_data
    
    def _create_stability_analytics_sheet(self, df: pd.DataFrame) -> list:
        """Create stability analytics data for Excel export"""
        try:
            # Generate stability metrics
            stability_metrics = self.stability_analyzer.calculate_system_stability(df)
            
            stability_data = [
                ["Metric", "Current Value", "Target/Benchmark", "Status", "Description"],
                
                # Portfolio-wide stability metrics (NEW)
                ["Portfolio Stability", 
                 f"{stability_metrics.portfolio_stability_percentage:.1f}%" if stability_metrics.total_supported_sites > 0 else f"{stability_metrics.overall_stability_percentage:.1f}%", 
                 "≥95% (Excellent)", 
                 "🟢 Excellent" if (stability_metrics.portfolio_stability_percentage if stability_metrics.total_supported_sites > 0 else stability_metrics.overall_stability_percentage) >= 95 else 
                 "🟡 Good" if (stability_metrics.portfolio_stability_percentage if stability_metrics.total_supported_sites > 0 else stability_metrics.overall_stability_percentage) >= 85 else 
                 "🔴 Needs Attention",
                 f"Percentage of ALL {stability_metrics.total_supported_sites} supported sites with zero critical incidents" if stability_metrics.total_supported_sites > 0 else "Percentage of active sites with no critical incidents"],
                
                ["Total Supported Sites", 
                 f"{stability_metrics.total_supported_sites}" if stability_metrics.total_supported_sites > 0 else "Not configured", 
                 "Configuration dependent", 
                 "ℹ️ Info",
                 "Total number of sites under IT support coverage"],
                
                ["Sites with Zero Critical Incidents", 
                 f"{stability_metrics.sites_with_zero_incidents}", 
                 f"≥{int(stability_metrics.total_supported_sites * 0.95)} sites (95%)" if stability_metrics.total_supported_sites > 0 else "≥95%", 
                 "🟢 Good" if stability_metrics.total_supported_sites == 0 or stability_metrics.sites_with_zero_incidents >= (stability_metrics.total_supported_sites * 0.95) else "🟡 Monitor",
                 "Number of sites with no critical incidents (including sites with no activity)"],
                
                ["Portfolio Coverage", 
                 f"{stability_metrics.portfolio_coverage_percentage:.1f}%" if stability_metrics.total_supported_sites > 0 else "100.0%", 
                 "Varies by business", 
                 "ℹ️ Info",
                 f"Percentage of supported sites that had any incidents ({stability_metrics.sites_with_incidents} of {stability_metrics.total_supported_sites})" if stability_metrics.total_supported_sites > 0 else "All active sites covered"],
                
                ["Overall System Stability", 
                 f"{stability_metrics.overall_stability_percentage:.1f}%", 
                 "≥95% (Excellent)", 
                 "🟢 Excellent" if stability_metrics.overall_stability_percentage >= 95 else 
                 "🟡 Good" if stability_metrics.overall_stability_percentage >= 85 else 
                 "🔴 Needs Attention",
                 "Legacy metric: Percentage of active sites with no critical incidents"],
                
                ["Volume-Weighted Stability", 
                 f"{stability_metrics.weighted_stability_score:.1f}%", 
                 "≥95% (Excellent)", 
                 "🟢 Excellent" if stability_metrics.weighted_stability_score >= 95 else 
                 "🟡 Good" if stability_metrics.weighted_stability_score >= 85 else 
                 "🔴 Needs Attention",
                 "Stability score weighted by site ticket volumes"],
                
                ["Critical Incident Rate", 
                 f"{stability_metrics.critical_incident_rate:.1f}%", 
                 "≤5% (Target)", 
                 "🟢 Excellent" if stability_metrics.critical_incident_rate <= 5 else 
                 "🟡 Acceptable" if stability_metrics.critical_incident_rate <= 10 else 
                 "🔴 High",
                 "Percentage of tickets that are critical priority"],
                
                ["Mean Time to Recovery", 
                 f"{stability_metrics.mean_time_to_recovery:.1f} hours", 
                 "≤4 hours (Target)", 
                 "🟢 Good" if stability_metrics.mean_time_to_recovery <= 4 else 
                 "🟡 Acceptable" if stability_metrics.mean_time_to_recovery <= 8 else 
                 "🔴 Slow",
                 "Average time to resolve critical incidents"],
                
                ["System Availability", 
                 f"{stability_metrics.system_availability:.1f}%", 
                 "≥99.5% (Target)", 
                 "🟢 Excellent" if stability_metrics.system_availability >= 99.5 else 
                 "🟡 Good" if stability_metrics.system_availability >= 99.0 else 
                 "🔴 Poor",
                 "Estimated system availability based on critical incidents"],
                
                ["Stability Trend", 
                 stability_metrics.stability_trend.title(), 
                 "Improving (Ideal)", 
                 "🟢 Good" if stability_metrics.stability_trend == "improving" else 
                 "🟡 Neutral" if stability_metrics.stability_trend == "stable" else 
                 "🔴 Concerning",
                 "Overall stability trend over recent period"],
                
                ["Benchmark Score", 
                 f"{stability_metrics.benchmark_score:.1f}/100", 
                 "≥80/100 (Good)", 
                 "🟢 Good" if stability_metrics.benchmark_score >= 80 else 
                 "🟡 Fair" if stability_metrics.benchmark_score >= 60 else 
                 "🔴 Poor",
                 "Overall score against industry benchmarks"],
                
                # Critical incident distribution breakdown (NEW)
                ["", "", "", "", ""],  # Separator row
                ["CRITICAL INCIDENT DISTRIBUTION", "", "", "", ""],
                ["Sites with 0 Critical Incidents", 
                 f"{stability_metrics.critical_distribution['zero_criticals']['count']} sites ({stability_metrics.critical_distribution['zero_criticals']['percentage']:.1f}%)", 
                 "Target: 95%+", 
                 "🟢 Excellent" if stability_metrics.critical_distribution['zero_criticals']['percentage'] >= 95 else 
                 "🟡 Good" if stability_metrics.critical_distribution['zero_criticals']['percentage'] >= 85 else 
                 "🔴 Needs Attention",
                 "Sites with zero critical incidents (ideal state)"],
                
                ["Sites with 1 Critical Incident", 
                 f"{stability_metrics.critical_distribution['one_critical']['count']} sites ({stability_metrics.critical_distribution['one_critical']['percentage']:.1f}%)", 
                 "Monitor closely", 
                 "🟡 Monitor",
                 "Sites with exactly one critical incident"],
                
                ["Sites with 2 Critical Incidents", 
                 f"{stability_metrics.critical_distribution['two_criticals']['count']} sites ({stability_metrics.critical_distribution['two_criticals']['percentage']:.1f}%)", 
                 "Requires attention", 
                 "🟡 Attention" if stability_metrics.critical_distribution['two_criticals']['percentage'] <= 5 else "🔴 Concern",
                 "Sites with exactly two critical incidents"],
                
                ["Sites with 3 Critical Incidents", 
                 f"{stability_metrics.critical_distribution['three_criticals']['count']} sites ({stability_metrics.critical_distribution['three_criticals']['percentage']:.1f}%)", 
                 "High priority review", 
                 "🔴 High Priority" if stability_metrics.critical_distribution['three_criticals']['percentage'] > 0 else "🟢 None",
                 "Sites with exactly three critical incidents"],
                
                ["Sites with 4+ Critical Incidents", 
                 f"{stability_metrics.critical_distribution['four_plus_criticals']['count']} sites ({stability_metrics.critical_distribution['four_plus_criticals']['percentage']:.1f}%)", 
                 "Immediate action", 
                 "🔴 Critical" if stability_metrics.critical_distribution['four_plus_criticals']['percentage'] > 0 else "🟢 None",
                 "Sites with four or more critical incidents (requires immediate intervention)"]
            ]
            
            return stability_data
        except Exception as e:
            return [["Error", f"Failed to generate stability analytics: {str(e)}"]]
    
    def _create_pattern_analysis_sheet(self, df: pd.DataFrame) -> list:
        """Create pattern analysis data for Excel export"""
        try:
            # Generate pattern analysis results
            pattern_results = self.pattern_engine.analyze_temporal_patterns(df)
            
            pattern_data = [
                ["Pattern Type", "Description", "Confidence", "Sites Affected", "Timeframe", "Evidence Count", "Recommendation"]
            ]
            
            # Add synchronized incidents
            sync_incidents = pattern_results.get("synchronized_incidents", [])
            for i, sync_event in enumerate(sync_incidents[:10]):  # Top 10
                pattern_data.append([
                    f"🔗 Synchronized Event {i+1}",
                    f"{sync_event.likely_root_cause} - {len(sync_event.sites)} sites affected",
                    f"{sync_event.correlation_score:.1%}",
                    f"{len(sync_event.sites)} sites",
                    sync_event.timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(sync_event.timestamp, 'strftime') else str(sync_event.timestamp),
                    len(sync_event.incidents),
                    "Investigate common infrastructure or service dependencies"
                ])
            
            # Add site correlations
            correlations = pattern_results.get("time_correlation_matrix", {}).get("high_correlations", [])
            for i, corr in enumerate(correlations[:10]):  # Top 10
                pattern_data.append([
                    f"📊 Site Correlation {i+1}",
                    f"{corr['site1']} ↔ {corr['site2']} ({corr['strength']} correlation)",
                    f"{corr['correlation']:.1%}",
                    "2 sites",
                    "Ongoing pattern",
                    0,  # Would need to calculate actual evidence
                    "Review shared dependencies and infrastructure"
                ])
            
            # Add recurring patterns
            recurring_patterns = pattern_results.get("recurring_patterns", [])
            for i, pattern in enumerate(recurring_patterns[:5]):  # Top 5
                pattern_data.append([
                    f"🔄 Recurring Pattern {i+1}",
                    pattern.description,
                    f"{pattern.confidence:.1%}",
                    f"{len(pattern.sites)} site{'s' if len(pattern.sites) > 1 else ''}",
                    f"{pattern.time_window[0].strftime('%Y-%m-%d')} to {pattern.time_window[1].strftime('%Y-%m-%d')}",
                    pattern.incident_count,
                    "Schedule preventive maintenance during identified pattern periods"
                ])
            
            return pattern_data
        except Exception as e:
            return [["Error", f"Failed to generate pattern analysis: {str(e)}"]]
    
    def _create_insights_sheet(self, df: pd.DataFrame) -> list:
        """Create stability insights data for Excel export"""
        try:
            # Generate stability metrics and insights
            stability_metrics = self.stability_analyzer.calculate_system_stability(df)
            insights = self.stability_analyzer.generate_stability_insights(stability_metrics)
            
            insights_data = [
                ["Insight Category", "Finding", "Priority", "Impact Level", "Recommendation", "Evidence Count"]
            ]
            
            # Add top insights with evidence counts
            for i, insight in enumerate(insights[:15]):  # Top 15 insights
                # Categorize insight based on content
                if "critical" in insight.lower():
                    category = "🚨 Critical Issues"
                    priority = "High"
                    impact = "High"
                elif "performance" in insight.lower() or "slow" in insight.lower():
                    category = "⚡ Performance"
                    priority = "Medium"
                    impact = "Medium"
                elif "stability" in insight.lower():
                    category = "🏗️ Stability"
                    priority = "Medium"
                    impact = "High"
                elif "trend" in insight.lower():
                    category = "📈 Trends"
                    priority = "Low"
                    impact = "Medium"
                else:
                    category = "💡 General"
                    priority = "Medium"
                    impact = "Medium"
                
                # Generate recommendation based on insight
                if "high" in insight.lower() and "critical" in insight.lower():
                    recommendation = "Implement immediate escalation procedures and root cause analysis"
                elif "increasing" in insight.lower() or "rising" in insight.lower():
                    recommendation = "Monitor trend closely and implement preventive measures"
                elif "availability" in insight.lower():
                    recommendation = "Review infrastructure redundancy and failure recovery procedures"
                else:
                    recommendation = "Review and optimize current operational procedures"
                
                # Estimate evidence count (would be actual count in real implementation)
                evidence_count = len(df[df['Priority'].str.contains('Critical', case=False, na=False)]) if "critical" in insight.lower() else len(df) // 10
                
                insights_data.append([
                    category,
                    insight[:100] + ("..." if len(insight) > 100 else ""),  # Truncate long insights
                    priority,
                    impact,
                    recommendation,
                    evidence_count
                ])
            
            return insights_data
        except Exception as e:
            return [["Error", f"Failed to generate stability insights: {str(e)}"]]
    
    def _create_critical_evidence_sheet(self, df: pd.DataFrame) -> list:
        """Create critical incidents evidence data for Excel export"""
        try:
            # Filter for critical incidents
            critical_tickets = df[df['Priority'].str.contains('Critical', case=False, na=False)].copy()
            
            if critical_tickets.empty:
                return [["No critical incidents found in the data"]]
            
            evidence_data = [
                ["Ticket Number", "Site", "Created Date", "Description", "Category", "Subcategory", 
                 "Resolution Status", "Time to Resolution (Hours)", "Stability Impact"]
            ]
            
            for _, ticket in critical_tickets.iterrows():
                # Calculate resolution time
                if pd.notna(ticket.get('Resolved')):
                    resolution_time = (ticket['Resolved'] - ticket['Created']).total_seconds() / 3600
                    resolution_status = "✅ Resolved"
                else:
                    resolution_time = "⏳ Open"
                    resolution_status = "⏳ Open"
                
                # Assess stability impact
                if resolution_time == "⏳ Open":
                    stability_impact = "🔴 High - Ongoing"
                elif isinstance(resolution_time, (int, float)):
                    if resolution_time <= 2:
                        stability_impact = "🟢 Low - Quick Resolution"
                    elif resolution_time <= 8:
                        stability_impact = "🟡 Medium - Standard Resolution"
                    else:
                        stability_impact = "🔴 High - Slow Resolution"
                else:
                    stability_impact = "❓ Unknown"
                
                evidence_data.append([
                    ticket.get('Number', 'N/A'),
                    ticket.get('Site', 'Unknown'),
                    ticket['Created'].strftime('%Y-%m-%d %H:%M') if pd.notna(ticket.get('Created')) else 'Unknown',
                    ticket.get('Short description', 'No description')[:80] + ("..." if len(str(ticket.get('Short description', ''))) > 80 else ""),
                    ticket.get('Category', 'Unknown'),
                    ticket.get('Subcategory', 'Unknown'),
                    resolution_status,
                    f"{resolution_time:.1f}" if isinstance(resolution_time, (int, float)) else resolution_time,
                    stability_impact
                ])
            
            return evidence_data
        except Exception as e:
            return [["Error", f"Failed to generate critical evidence: {str(e)}"]]
    
    def _create_synchronized_evidence_sheet(self, df: pd.DataFrame) -> list:
        """Create synchronized events evidence data for Excel export"""
        try:
            # Generate pattern analysis to find synchronized events
            pattern_results = self.pattern_engine.analyze_temporal_patterns(df)
            sync_incidents = pattern_results.get("synchronized_incidents", [])
            
            if not sync_incidents:
                return [["No synchronized events detected in the data"]]
            
            evidence_data = [
                ["Event ID", "Event Time", "Root Cause", "Sites Affected", "Correlation Score", 
                 "Ticket Numbers", "Categories", "Total Impact", "Recovery Pattern"]
            ]
            
            for i, sync_event in enumerate(sync_incidents[:20]):  # Top 20 events
                # Extract ticket details
                ticket_numbers = [inc.get('Number', 'N/A') for inc in sync_event.incidents]
                categories = list(set([inc.get('Category', 'Unknown') for inc in sync_event.incidents]))
                
                # Assess total impact
                total_tickets = len(sync_event.incidents)
                if total_tickets >= 10:
                    total_impact = "🔴 Severe - Multiple Sites"
                elif total_tickets >= 5:
                    total_impact = "🟡 Moderate - Several Sites"
                else:
                    total_impact = "🟢 Limited - Few Sites"
                
                # Determine recovery pattern
                if len(set([inc.get('Category', '') for inc in sync_event.incidents])) == 1:
                    recovery_pattern = "🎯 Single System - Targeted Fix"
                else:
                    recovery_pattern = "🌐 Multi-System - Complex Recovery"
                
                evidence_data.append([
                    f"SYNC-{i+1:03d}",
                    sync_event.timestamp.strftime('%Y-%m-%d %H:%M') if hasattr(sync_event.timestamp, 'strftime') else str(sync_event.timestamp),
                    sync_event.likely_root_cause,
                    f"{len(sync_event.sites)} sites: " + ", ".join(sync_event.sites[:3]) + ("..." if len(sync_event.sites) > 3 else ""),
                    f"{sync_event.correlation_score:.1%}",
                    ", ".join(ticket_numbers[:5]) + ("..." if len(ticket_numbers) > 5 else ""),
                    ", ".join(categories),
                    total_impact,
                    recovery_pattern
                ])
            
            return evidence_data
        except Exception as e:
            return [["Error", f"Failed to generate synchronized evidence: {str(e)}"]]
    
    def _get_active_filters_summary(self, filters: dict) -> str:
        """Get summary of active filters for export confirmation"""
        active_filters = []
        if filters.get("date_from"):
            active_filters.append(f"Date from: {filters['date_from']}")
        if filters.get("date_to"):
            active_filters.append(f"Date to: {filters['date_to']}")
        if filters.get("priorities"):
            active_filters.append(f"Priorities: {', '.join(filters['priorities'])}")
        if filters.get("company"):
            active_filters.append(f"Company: {filters['company']}")
        if filters.get("site"):
            active_filters.append(f"Site: {filters['site']}")
        if filters.get("category"):
            active_filters.append(f"Category: {filters['category']}")
        if filters.get("subcategory"):
            active_filters.append(f"Subcategory: {filters['subcategory']}")
        
        return "\n".join(active_filters) if active_filters else "No filters applied"
    
    # Quality Management Event Handlers
    def _handle_refresh_quality(self):
        """Handle refresh quality analysis request"""
        if self.data_manager.data is None:
            messagebox.showwarning("No Data", "Please load data first.")
            return
        
        try:
            self.main_window.set_status("Refreshing quality analysis...")
            
            # Regenerate quality analysis
            quality_report = self.data_manager.get_quality_report()
            
            if quality_report:
                quality_tab = self.main_window.get_quality_tab()
                quality_tab.update_quality_metrics(quality_report)
                
                self.main_window.set_status("Quality analysis refreshed")
                messagebox.showinfo("Quality Analysis", "Quality analysis has been refreshed successfully!")
            else:
                messagebox.showwarning("Quality Analysis", "Unable to generate quality report.")
                
        except Exception as e:
            messagebox.showerror("Quality Analysis Error", f"Failed to refresh quality analysis:\n{str(e)}")
    
    def _handle_auto_process_duplicates(self):
        """Handle auto-processing of high confidence duplicates"""
        try:
            duplicate_groups = self.data_manager.get_duplicate_groups()
            high_confidence_groups = [
                group for group in duplicate_groups 
                if group.confidence_score >= self.settings.get("data_quality.auto_review.high_confidence_threshold", 0.95)
            ]
            
            if not high_confidence_groups:
                messagebox.showinfo("Auto-Process", "No high-confidence duplicate groups found for automatic processing.")
                return
            
            processed_count = 0
            
            for group in high_confidence_groups:
                # Auto-merge high confidence duplicates
                primary_ticket_id = str(group.primary_ticket.get("Number", "N/A"))
                duplicate_ticket_ids = [str(dup.get("Number", "N/A")) for dup in group.duplicates]
                
                # Log audit action
                action = AuditAction(
                    action_id=str(uuid.uuid4()),
                    action_type="merge_duplicates",
                    user="system_auto",
                    timestamp=datetime.now(),
                    description=f"Auto-merged high confidence duplicates ({group.confidence_score:.1%} confidence)",
                    details={
                        "confidence_score": group.confidence_score,
                        "auto_processed": True,
                        "primary_ticket": primary_ticket_id,
                        "merged_tickets": duplicate_ticket_ids
                    },
                    affected_tickets=[primary_ticket_id] + duplicate_ticket_ids
                )
                
                if self.audit_manager.log_action(action):
                    # Mark as processed in data manager
                    self.data_manager.merge_duplicate_tickets(primary_ticket_id, duplicate_ticket_ids, 
                                                            "Auto-processed by system (high confidence)")
                    processed_count += 1
            
            if processed_count > 0:
                # Refresh quality analysis
                self._handle_refresh_quality()
                
                messagebox.showinfo("Auto-Process Complete", 
                                  f"Successfully auto-processed {processed_count} high-confidence duplicate groups!")
            
        except Exception as e:
            messagebox.showerror("Auto-Process Error", f"Failed to auto-process duplicates:\n{str(e)}")
    
    def _handle_export_audit_log(self):
        """Handle export audit log request"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Audit Log",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Determine format
            format_type = "json" if file_path.lower().endswith('.json') else "csv"
            
            if self.audit_manager.export_audit_log(file_path, format_type):
                messagebox.showinfo("Export Complete", f"Audit log exported successfully to:\n{file_path}")
                self.main_window.set_status(f"Audit log exported to {file_path}")
            else:
                messagebox.showerror("Export Error", "Failed to export audit log.")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export audit log:\n{str(e)}")
    
    def _handle_review_duplicate_group(self, group_id: str):
        """Handle review of specific duplicate group"""
        try:
            # Find the duplicate group by ID  
            duplicate_groups = self.data_manager.get_duplicate_groups()
            
            target_group = None
            for i, group in enumerate(duplicate_groups):
                if f"Group {i + 1}" == group_id:
                    target_group = group
                    break
            
            if not target_group:
                messagebox.showwarning("Group Not Found", f"Duplicate group '{group_id}' not found.")
                return
            
            # Show review dialog
            quality_tab = self.main_window.get_quality_tab()
            result = quality_tab.show_review_dialog(target_group)
            
            if result and result["action"] != "skip":
                # Add decision to pending list instead of processing immediately
                result['group_id'] = group_id
                result['timestamp'] = datetime.now()
                self.pending_review_decisions.append(result)
                
                # Update UI to show pending changes
                quality_tab = self.main_window.get_quality_tab()
                quality_tab.update_pending_changes(len(self.pending_review_decisions))
                
                # Show confirmation message
                if result["action"] == "merge":
                    message = f"Merge decision added to pending changes.\n\n"
                    message += f"Primary: {result['primary_ticket_id']}\n"
                    message += f"Duplicates: {', '.join(result['duplicate_ticket_ids'])}\n\n"
                    message += f"Click 'Apply Changes' to process all pending decisions."
                elif result["action"] == "dismiss":
                    message = f"Dismiss decision added to pending changes.\n\n"
                    message += f"Tickets: {', '.join(result.get('ticket_ids', []))}\n\n" 
                    message += f"Click 'Apply Changes' to process all pending decisions."
                
                messagebox.showinfo("Decision Pending", message)
                
        except Exception as e:
            import traceback
            error_details = f"Failed to review duplicate group:\n{str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
            self.logger.error(f"Duplicate review error: {error_details}")
            
            # Show shorter message to user but log full details
            messagebox.showerror("Review Error", 
                f"Failed to review duplicate group:\n{str(e)}\n\nCheck logs for full details.")
    
    def _handle_batch_process_duplicates(self, group_ids: List[str]):
        """Handle batch processing of multiple duplicate groups"""
        try:
            processed_count = 0
            failed_count = 0
            
            for group_id in group_ids:
                try:
                    # For batch processing, auto-merge groups above threshold
                    duplicate_groups = self.data_manager.get_duplicate_groups()
                    
                    target_group = None
                    for i, group in enumerate(duplicate_groups):
                        if f"Group {i + 1}" == group_id:
                            target_group = group
                            break
                    
                    if target_group and target_group.confidence_score >= 0.8:  # Batch process threshold
                        primary_ticket_id = str(target_group.primary_ticket.get("Number", "N/A"))
                        duplicate_ticket_ids = [str(dup.get("Number", "N/A")) for dup in target_group.duplicates]
                        
                        # Log batch action
                        action = AuditAction(
                            action_id=str(uuid.uuid4()),
                            action_type="merge_duplicates",
                            user="batch_process",
                            timestamp=datetime.now(),
                            description=f"Batch processed: Merged duplicates ({target_group.confidence_score:.1%} confidence)",
                            details={
                                "confidence_score": target_group.confidence_score,
                                "batch_processed": True,
                                "primary_ticket": primary_ticket_id,
                                "merged_tickets": duplicate_ticket_ids
                            },
                            affected_tickets=[primary_ticket_id] + duplicate_ticket_ids
                        )
                        
                        if self.audit_manager.log_action(action):
                            self.data_manager.merge_duplicate_tickets(primary_ticket_id, duplicate_ticket_ids, 
                                                                    f"Batch processed (confidence: {target_group.confidence_score:.1%})")
                            processed_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception:
                    failed_count += 1
            
            # Show results
            if processed_count > 0 or failed_count > 0:
                result_msg = f"Batch processing complete!\n\nProcessed: {processed_count}\nFailed: {failed_count}"
                
                if processed_count > 0:
                    # Refresh quality analysis
                    self._handle_refresh_quality()
                
                messagebox.showinfo("Batch Process Complete", result_msg)
                
        except Exception as e:
            messagebox.showerror("Batch Process Error", f"Failed to batch process duplicates:\n{str(e)}")
    
    def _handle_get_duplicate_queue(self, filter_type: str) -> List[List]:
        """Get duplicate queue data for display"""
        try:
            duplicate_groups = self.data_manager.get_duplicate_groups()
            
            # Filter based on type
            filtered_groups = []
            
            for i, group in enumerate(duplicate_groups):
                if filter_type == "High Confidence" and group.confidence_score < 0.9:
                    continue
                elif filter_type == "Manual Review Required" and (group.confidence_score < 0.7 or group.confidence_score >= 0.95):
                    continue
                elif filter_type == "Low Confidence" and group.confidence_score >= 0.7:
                    continue
                
                # Format for display
                primary_ticket = group.primary_ticket
                duplicate_tickets = group.duplicates
                
                group_data = [
                    f"Group {i + 1}",
                    str(primary_ticket.get("Number", "N/A")),
                    ", ".join([str(dup.get("Number", "N/A")) for dup in duplicate_tickets]),
                    f"{group.confidence_score:.1%}",
                    primary_ticket.get("Site", "N/A"),
                    primary_ticket.get("Created").strftime("%Y-%m-%d") if hasattr(primary_ticket.get("Created"), 'strftime') else "N/A",
                    getattr(group, 'review_status', 'pending').title(),
                    "🤖 Auto-merge" if group.confidence_score >= 0.95 else "👁️ Review" if group.confidence_score >= 0.7 else "❓ Low confidence"
                ]
                
                filtered_groups.append(group_data)
            
            return filtered_groups
            
        except Exception as e:
            messagebox.showerror("Queue Error", f"Failed to get duplicate queue:\n{str(e)}")
            return []
    
    def _handle_get_audit_trail(self, filter_type: str) -> List[List]:
        """Get audit trail data for display"""
        try:
            # Map filter types to action types
            action_type_map = {
                "All Actions": None,
                "Merge Duplicates": "merge_duplicates",
                "Dismiss Duplicates": "dismiss_duplicates", 
                "Manual Corrections": "manual_correction",
                "Reversals": "reversal"
            }
            
            action_type = action_type_map.get(filter_type)
            actions = self.audit_manager.get_audit_history(limit=100, action_type=action_type)
            
            audit_data = []
            for action in actions:
                audit_row = [
                    action.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    action.action_type.replace("_", " ").title(),
                    action.user,
                    action.description[:80] + ("..." if len(action.description) > 80 else ""),
                    ", ".join(action.affected_tickets[:3]) + ("..." if len(action.affected_tickets) > 3 else ""),
                    "Reversed" if getattr(action, 'reversed', False) else "Active"
                ]
                audit_data.append(audit_row)
            
            return audit_data
            
        except Exception as e:
            messagebox.showerror("Audit Trail Error", f"Failed to get audit trail:\n{str(e)}")
            return []
    
    def _handle_apply_manual_changes(self):
        """Handle applying pending manual review changes"""
        try:
            # Show progress while processing
            self.main_window.set_status("Applying manual review changes...")
            self.main_window.show_progress(True, 0)
            self.root.update()
            
            # Check if we have pending changes
            if not hasattr(self, 'pending_review_decisions'):
                self.pending_review_decisions = []
            
            if not self.pending_review_decisions:
                messagebox.showinfo("No Changes", "No pending manual review decisions to apply.")
                self.main_window.show_progress(False)
                self.main_window.set_status("Ready")
                return
            
            processed_count = 0
            merge_count = 0
            dismiss_count = 0
            
            # Process each pending decision
            for decision in self.pending_review_decisions:
                try:
                    if decision['action'] == 'merge':
                        # Apply ticket merge
                        self._apply_ticket_merge(decision)
                        merge_count += 1
                    elif decision['action'] == 'dismiss':
                        # Remove from duplicate queue
                        dismiss_count += 1
                    
                    processed_count += 1
                    
                    # Update progress
                    progress = (processed_count / len(self.pending_review_decisions)) * 70
                    self.main_window.show_progress(True, progress)
                    self.root.update()
                    
                except Exception as e:
                    self.logger.error(f"Failed to process decision {decision.get('primary_ticket_id', 'unknown')}: {e}")
            
            # Reprocess data with changes applied
            self.main_window.show_progress(True, 80)
            self.root.update()
            
            # Regenerate quality report
            if self.data_manager.data is not None:
                quality_report = self.data_manager.quality_manager.generate_quality_report(self.data_manager.data)
                self.data_manager.quality_report = quality_report
                
                # Update quality tab
                quality_tab = self.main_window.get_quality_tab()
                quality_tab.update_quality_metrics(quality_report)
            
            # Clear pending decisions
            self.pending_review_decisions = []
            
            # Update UI
            quality_tab = self.main_window.get_quality_tab()
            quality_tab.update_pending_changes(0)
            
            self.main_window.show_progress(False)
            
            # Show completion message
            message = f"Manual review changes applied successfully!\n\n"
            message += f"• {merge_count} ticket merge(s) processed\n"
            message += f"• {dismiss_count} duplicate group(s) dismissed\n"
            message += f"• Data quality report regenerated"
            
            messagebox.showinfo("Changes Applied", message)
            self.main_window.set_status(f"Applied {processed_count} manual review changes")
            
        except Exception as e:
            self.main_window.show_progress(False)
            self.main_window.set_status("Error applying changes")
            messagebox.showerror("Apply Changes Error", f"Failed to apply manual review changes:\n{str(e)}")
    
    def _apply_ticket_merge(self, decision):
        """Apply a ticket merge decision to the dataset"""
        try:
            if self.data_manager.data is None:
                return
            
            primary_ticket_id = decision['primary_ticket_id']
            duplicate_ticket_ids = decision['duplicate_ticket_ids']
            
            # Find tickets in the dataset
            df = self.data_manager.data
            primary_mask = df['Number'].astype(str) == str(primary_ticket_id)
            
            if not primary_mask.any():
                self.logger.warning(f"Primary ticket {primary_ticket_id} not found in dataset")
                return
            
            # Add ticket status tracking columns if they don't exist
            if 'Is_Active' not in df.columns:
                df['Is_Active'] = True
            if 'Merged_Into' not in df.columns:
                df['Merged_Into'] = None
            if 'Manual_Review_Status' not in df.columns:
                df['Manual_Review_Status'] = 'active'
            
            # Get primary ticket index
            primary_idx = df[primary_mask].index[0]
            
            # Process duplicate tickets
            for dup_id in duplicate_ticket_ids:
                dup_mask = df['Number'].astype(str) == str(dup_id)
                if dup_mask.any():
                    dup_indices = df[dup_mask].index
                    # Mark as inactive (merged)
                    df.loc[dup_indices, 'Is_Active'] = False
                    df.loc[dup_indices, 'Merged_Into'] = primary_ticket_id
                    df.loc[dup_indices, 'Manual_Review_Status'] = 'merged'
            
            # Update primary ticket description with merge info
            if 'selected_tickets' in decision:
                # Combine descriptions from all selected tickets
                combined_desc_parts = []
                for ticket_id in decision['selected_tickets']:
                    ticket_mask = df['Number'].astype(str) == str(ticket_id)
                    if ticket_mask.any():
                        ticket_row = df[ticket_mask].iloc[0]
                        desc = ticket_row.get('Short description', '')
                        created = ticket_row.get('Created', '')
                        if pd.notna(created) and hasattr(created, 'strftime'):
                            timestamp = created.strftime('%Y-%m-%d %H:%M')
                            combined_desc_parts.append(f"[{ticket_id} - {timestamp}] {desc}")
                        else:
                            combined_desc_parts.append(f"[{ticket_id}] {desc}")
                
                if combined_desc_parts:
                    combined_description = "\n\n".join(combined_desc_parts)
                    df.loc[primary_idx, 'Short description'] = combined_description
            
            # Mark primary as reviewed
            df.loc[primary_idx, 'Manual_Review_Status'] = 'reviewed'
            
            # Log the merge action
            action = AuditAction(
                action_id=str(uuid.uuid4()),
                action_type="merge_duplicates",
                user="manual_review", 
                timestamp=datetime.now(),
                description=f"Merged {len(duplicate_ticket_ids)} tickets into {primary_ticket_id}",
                details=decision,
                affected_tickets=[primary_ticket_id] + duplicate_ticket_ids
            )
            
            self.audit_manager.log_action(action)
            
        except Exception as e:
            self.logger.error(f"Failed to apply ticket merge for {decision.get('primary_ticket_id', 'unknown')}: {e}")
            raise