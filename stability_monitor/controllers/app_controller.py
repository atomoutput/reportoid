"""
Main application controller
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from typing import Dict, Any

from ..models.data_manager import DataManager
from ..models.report_engine import ReportEngine
from ..views.main_window import MainWindow

class AppController:
    """Main application controller - coordinates between models and views"""
    
    def __init__(self, root: tk.Tk, settings):
        self.root = root
        self.settings = settings
        
        # Initialize models
        self.data_manager = DataManager(settings)
        self.report_engine = ReportEngine(settings)
        
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
                "workload_trends": "Workload Trends - Volume Patterns"
            }
            
            title = report_titles.get(report_type, report_type.replace('_', ' ').title())
            self.main_window.display_results(results, columns, title)
            
            self.main_window.set_status(f"Report completed: {len(results)} results")
            
        except Exception as e:
            self.main_window.show_progress(False)
            self.main_window.set_status("Error generating report")
            messagebox.showerror("Report Error", f"Failed to generate report:\n{str(e)}")
    
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