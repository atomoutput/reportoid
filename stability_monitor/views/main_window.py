"""
Main application window
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Callable
import pandas as pd
from .quality_management import DataQualityTab

class MainWindow:
    """Main application window with all UI components"""
    
    def __init__(self, root: tk.Tk, settings):
        self.root = root
        self.settings = settings
        self.callbacks = {}
        
        # Configure main window
        self._setup_window()
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        # Initialize component states
        self._update_ui_state(data_loaded=False)
    
    def _setup_window(self):
        """Configure main window properties"""
        self.root.title("IT Stability & Operations Health Monitor")
        
        # Set window icon if available
        try:
            # You can add an icon file later
            pass
        except:
            pass
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def _create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Data...", command=self._on_load_data, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Export Results...", command=self._on_export_results, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Critical Hotspots", command=lambda: self._on_run_report("critical_hotspots"))
        reports_menu.add_command(label="Site Scorecard", command=lambda: self._on_run_report("site_scorecard"))
        reports_menu.add_command(label="Green List", command=lambda: self._on_run_report("green_list"))
        reports_menu.add_command(label="Franchise Overview", command=lambda: self._on_run_report("franchise_overview"))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Data Summary", command=self._on_data_summary)
        tools_menu.add_command(label="Settings...", command=self._on_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self._on_help)
        help_menu.add_command(label="About", command=self._on_about)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self._on_load_data())
        self.root.bind('<Control-e>', lambda e: self._on_export_results())
        self.root.bind('<F5>', lambda e: self._on_refresh())
    
    def _create_main_layout(self):
        """Create the main layout with toolbar, filters, reports, and results"""
        
        # Toolbar frame
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Toolbar buttons
        self.load_btn = ttk.Button(toolbar_frame, text="📁 Load Data", command=self._on_load_data)
        self.load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_btn = ttk.Button(toolbar_frame, text="💾 Export Current", command=self._on_export_results, state="disabled")
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_comprehensive_btn = ttk.Button(toolbar_frame, text="📊 Export All Reports", command=self._on_export_comprehensive, state="disabled")
        self.export_comprehensive_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_btn = ttk.Button(toolbar_frame, text="🔄 Refresh", command=self._on_refresh, state="disabled")
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Total Sites Configuration (Dynamic)
        sites_frame = ttk.Frame(toolbar_frame)
        sites_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(sites_frame, text="Total Sites:").pack(side=tk.LEFT, padx=(0, 2))
        
        self.total_sites_var = tk.StringVar()
        self.total_sites_entry = ttk.Entry(sites_frame, textvariable=self.total_sites_var, width=5)
        self.total_sites_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.total_sites_entry.bind('<Return>', self._on_total_sites_changed)
        self.total_sites_entry.bind('<FocusOut>', self._on_total_sites_changed)
        
        self.update_sites_btn = ttk.Button(sites_frame, text="Update", command=self._on_total_sites_changed, width=6)
        self.update_sites_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Initialize with current setting
        current_total = self.settings.get("stability_analysis.total_supported_sites.count", 250)
        self.total_sites_var.set(str(current_total))
        
        # Settings button
        settings_btn = ttk.Button(toolbar_frame, text="⚙️ Settings", command=self._on_settings)
        settings_btn.pack(side=tk.RIGHT)
        
        # Main content frame with notebook for organized layout
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Analysis tab
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Analysis & Reports")
        
        # Configure analysis frame grid
        self.analysis_frame.grid_rowconfigure(2, weight=1)
        self.analysis_frame.grid_columnconfigure(0, weight=1)
        
        # Create filter panel
        self._create_filter_panel()
        
        # Create reports panel
        self._create_reports_panel()
        
        # Create results panel
        self._create_results_panel()
        
        # Data Quality tab
        self.quality_tab = DataQualityTab(self.notebook, self.settings)
        self.notebook.add(self.quality_tab, text="Data Quality")
    
    def _create_filter_panel(self):
        """Create the filters panel"""
        # Filters frame
        filters_frame = ttk.LabelFrame(self.analysis_frame, text="📊 Filters", padding=10)
        filters_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Configure grid for filters
        filters_frame.grid_columnconfigure(1, weight=1)
        filters_frame.grid_columnconfigure(3, weight=1)
        
        # Date range filters with elegant presets
        ttk.Label(filters_frame, text="Date Range:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        date_container = ttk.Frame(filters_frame)
        date_container.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        
        # Date preset buttons (top row)
        preset_frame = ttk.Frame(date_container)
        preset_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.date_presets = [
            ("Last 7 Days", 7),
            ("Last 30 Days", 30), 
            ("Last 90 Days", 90),
            ("This Year", "YTD"),
            ("All Time", "ALL")
        ]
        
        for preset_name, preset_value in self.date_presets:
            btn = ttk.Button(preset_frame, text=preset_name, 
                           command=lambda v=preset_value: self._apply_date_preset(v),
                           width=10)
            btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Custom date entry (bottom row)
        custom_frame = ttk.Frame(date_container)
        custom_frame.pack(fill=tk.X)
        
        ttk.Label(custom_frame, text="From:").pack(side=tk.LEFT)
        self.date_from_var = tk.StringVar()
        self.date_from_entry = ttk.Entry(custom_frame, textvariable=self.date_from_var, width=12)
        self.date_from_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.date_from_entry.bind('<KeyRelease>', self._on_filter_change)
        
        ttk.Label(custom_frame, text="To:").pack(side=tk.LEFT)
        self.date_to_var = tk.StringVar()
        self.date_to_entry = ttk.Entry(custom_frame, textvariable=self.date_to_var, width=12)
        self.date_to_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.date_to_entry.bind('<KeyRelease>', self._on_filter_change)
        
        # Clear button
        clear_dates_btn = ttk.Button(custom_frame, text="Clear", command=self._clear_dates, width=6)
        clear_dates_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Priority filters
        ttk.Label(filters_frame, text="Priority:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        
        priority_frame = ttk.Frame(filters_frame)
        priority_frame.grid(row=0, column=3, sticky="ew")
        
        self.priority_vars = {}
        priorities = ["Critical", "High", "Medium", "Low"]
        for i, priority in enumerate(priorities):
            var = tk.BooleanVar(value=True)
            self.priority_vars[priority] = var
            cb = ttk.Checkbutton(priority_frame, text=priority[0], variable=var, command=self._on_filter_change)
            cb.pack(side=tk.LEFT, padx=5)
        
        # Company and Site filters with search
        ttk.Label(filters_frame, text="Company:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(10, 0))
        
        company_frame = ttk.Frame(filters_frame)
        company_frame.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=(10, 0))
        
        self.company_var = tk.StringVar(value="All")
        self.company_combo = ttk.Combobox(company_frame, textvariable=self.company_var, width=25)
        self.company_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.company_combo.bind('<<ComboboxSelected>>', self._on_company_changed)
        self.company_combo.bind('<KeyRelease>', self._on_company_search)
        
        ttk.Button(company_frame, text="🔍", width=3, command=self._focus_company).pack(side=tk.RIGHT, padx=(2, 0))
        
        ttk.Label(filters_frame, text="Site:").grid(row=1, column=2, sticky="w", padx=(0, 5), pady=(10, 0))
        
        site_frame = ttk.Frame(filters_frame)
        site_frame.grid(row=1, column=3, sticky="ew", pady=(10, 0))
        
        self.site_var = tk.StringVar(value="All")
        self.site_combo = ttk.Combobox(site_frame, textvariable=self.site_var, width=25)
        self.site_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.site_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        self.site_combo.bind('<KeyRelease>', self._on_site_search)
        
        ttk.Button(site_frame, text="🔍", width=3, command=self._focus_site).pack(side=tk.RIGHT, padx=(2, 0))
        
        # Advanced filters (collapsible)
        self.advanced_visible = tk.BooleanVar(value=False)
        self.advanced_btn = ttk.Button(filters_frame, text="▼ Advanced Filters", 
                                     command=self._toggle_advanced_filters)
        self.advanced_btn.grid(row=2, column=0, sticky="w", pady=(10, 0))
        
        # Advanced filters frame (initially hidden)
        self.advanced_frame = ttk.Frame(filters_frame)
        
        # Category and Subcategory with search
        ttk.Label(self.advanced_frame, text="Category:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=(10, 0))
        
        category_frame = ttk.Frame(self.advanced_frame)
        category_frame.grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=(10, 0))
        
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, width=16)
        self.category_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_changed)
        self.category_combo.bind('<KeyRelease>', self._on_category_search)
        
        ttk.Button(category_frame, text="🔍", width=3, command=self._focus_category).pack(side=tk.RIGHT, padx=(2, 0))
        
        ttk.Label(self.advanced_frame, text="Subcategory:").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=(10, 0))
        
        subcategory_frame = ttk.Frame(self.advanced_frame)
        subcategory_frame.grid(row=0, column=3, sticky="ew", pady=(10, 0))
        
        self.subcategory_var = tk.StringVar(value="All")
        self.subcategory_combo = ttk.Combobox(subcategory_frame, textvariable=self.subcategory_var, width=16)
        self.subcategory_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.subcategory_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        self.subcategory_combo.bind('<KeyRelease>', self._on_subcategory_search)
        
        ttk.Button(subcategory_frame, text="🔍", width=3, command=self._focus_subcategory).pack(side=tk.RIGHT, padx=(2, 0))
        
        # Filter controls
        filter_controls = ttk.Frame(filters_frame)
        filter_controls.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        
        ttk.Button(filter_controls, text="Clear All", command=self._clear_filters).pack(side=tk.LEFT)
        ttk.Button(filter_controls, text="Apply Filters", command=self._on_filter_change).pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_reports_panel(self):
        """Create the reports selection panel"""
        reports_frame = ttk.LabelFrame(self.analysis_frame, text="📈 Reports", padding=10)
        reports_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Core reports (top row)
        core_frame = ttk.Frame(reports_frame)
        core_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.hotspots_btn = ttk.Button(core_frame, text="🚨 Critical Hotspots", 
                                     command=lambda: self._on_run_report("critical_hotspots"),
                                     state="disabled")
        self.hotspots_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.scorecard_btn = ttk.Button(core_frame, text="📊 Site Scorecard",
                                      command=lambda: self._on_run_report("site_scorecard"),
                                      state="disabled")
        self.scorecard_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.green_btn = ttk.Button(core_frame, text="✅ Green List",
                                  command=lambda: self._on_run_report("green_list"),
                                  state="disabled")
        self.green_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.franchise_btn = ttk.Button(core_frame, text="🏢 Franchise Overview",
                                      command=lambda: self._on_run_report("franchise_overview"),
                                      state="disabled")
        self.franchise_btn.pack(side=tk.LEFT)
        
        # Enhanced reports (bottom row)
        enhanced_frame = ttk.Frame(reports_frame)
        enhanced_frame.pack(fill=tk.X)
        
        self.equipment_btn = ttk.Button(enhanced_frame, text="🔧 Equipment Analysis",
                                      command=lambda: self._on_run_report("equipment_analysis"),
                                      state="disabled")
        self.equipment_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.repeat_btn = ttk.Button(enhanced_frame, text="🔄 Repeat Offenders",
                                   command=lambda: self._on_run_report("repeat_offenders"),
                                   state="disabled")
        self.repeat_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.resolution_btn = ttk.Button(enhanced_frame, text="⏱️ Resolution Tracking",
                                       command=lambda: self._on_run_report("resolution_tracking"),
                                       state="disabled")
        self.resolution_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.workload_btn = ttk.Button(enhanced_frame, text="📈 Workload Trends",
                                     command=lambda: self._on_run_report("workload_trends"),
                                     state="disabled")
        self.workload_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Detail reports (third row)
        detail_frame = ttk.Frame(reports_frame)
        detail_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.incident_details_btn = ttk.Button(detail_frame, text="📋 Incident Details",
                                             command=lambda: self._on_run_report("incident_details"),
                                             state="disabled")
        self.incident_details_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.drill_down_btn = ttk.Button(detail_frame, text="🔍 Site Drill-Down",
                                       command=self._on_drill_down,
                                       state="disabled")
        self.drill_down_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_filtered_btn = ttk.Button(detail_frame, text="📤 Export Filtered Data",
                                            command=self._on_export_filtered_data,
                                            state="disabled")
        self.export_filtered_btn.pack(side=tk.LEFT)
        
        # Phase 2: Advanced Analytics Reports (fourth row)
        analytics_frame = ttk.Frame(reports_frame)
        analytics_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.stability_dashboard_btn = ttk.Button(analytics_frame, text="🏗️ Stability Dashboard",
                                                command=lambda: self._on_run_report("system_stability_dashboard"),
                                                state="disabled")
        self.stability_dashboard_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pattern_analysis_btn = ttk.Button(analytics_frame, text="🔍 Pattern Analysis",
                                             command=lambda: self._on_run_report("time_pattern_analysis"),
                                             state="disabled")
        self.pattern_analysis_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stability_insights_btn = ttk.Button(analytics_frame, text="💡 Stability Insights",
                                               command=lambda: self._on_run_report("stability_insights"),
                                               state="disabled")
        self.stability_insights_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.data_quality_report_btn = ttk.Button(analytics_frame, text="📊 Quality Report",
                                                command=lambda: self._on_run_report("data_quality_report"),
                                                state="disabled")
        self.data_quality_report_btn.pack(side=tk.LEFT)
    
    def _create_results_panel(self):
        """Create the results display panel"""
        results_frame = ttk.LabelFrame(self.analysis_frame, text="📋 Results", padding=5)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configure grid for results frame
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(results_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview
        self.results_tree = ttk.Treeview(tree_frame)
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.results_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Results info frame
        results_info_frame = ttk.Frame(results_frame)
        results_info_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        self.results_info_label = ttk.Label(results_info_frame, text="No data loaded")
        self.results_info_label.pack(side=tk.LEFT)
        
        # Export selected button
        self.export_selected_btn = ttk.Button(results_info_frame, text="Export Selected", 
                                            command=self._on_export_selected, state="disabled")
        self.export_selected_btn.pack(side=tk.RIGHT)
    
    def _create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Progress bar (initially hidden)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_bar, variable=self.progress_var, 
                                          mode='determinate', length=200)
        
        # Data info labels
        self.data_info_label = ttk.Label(self.status_bar, text="")
        self.data_info_label.pack(side=tk.RIGHT)
    
    # Event handlers
    def _on_load_data(self):
        """Handle load data button click"""
        if 'load_data' in self.callbacks:
            self.callbacks['load_data']()
    
    def _on_export_results(self):
        """Handle export results button click"""
        if 'export_results' in self.callbacks:
            self.callbacks['export_results']()
    
    def _on_export_comprehensive(self):
        """Handle comprehensive export button click"""
        if 'export_comprehensive' in self.callbacks:
            self.callbacks['export_comprehensive']()
    
    def _on_export_selected(self):
        """Handle export selected button click"""
        if 'export_selected' in self.callbacks:
            self.callbacks['export_selected']()
    
    def _on_refresh(self):
        """Handle refresh button click"""
        if 'refresh' in self.callbacks:
            self.callbacks['refresh']()
    
    def _on_run_report(self, report_type: str):
        """Handle report button clicks"""
        if 'run_report' in self.callbacks:
            self.callbacks['run_report'](report_type)
    
    def _on_filter_change(self, event=None):
        """Handle filter changes"""
        if 'filter_change' in self.callbacks:
            self.callbacks['filter_change']()
    
    def _on_company_changed(self, event=None):
        """Handle company selection change"""
        if 'company_changed' in self.callbacks:
            self.callbacks['company_changed'](self.company_var.get())
    
    def _on_category_changed(self, event=None):
        """Handle category selection change"""
        if 'category_changed' in self.callbacks:
            self.callbacks['category_changed'](self.category_var.get())
    
    def _on_drill_down(self):
        """Handle site drill-down button click"""
        # Get selected site from results tree
        tree = self.results_tree
        selected_items = tree.selection()
        
        if not selected_items:
            from tkinter import messagebox
            messagebox.showwarning("No Selection", "Please select a site from the results to drill down.")
            return
        
        # Get the site name from the selected row (first column)
        selected_item = selected_items[0]
        site_name = tree.item(selected_item)['values'][0]
        
        if 'drill_down' in self.callbacks:
            self.callbacks['drill_down'](site_name)
    
    def _on_export_filtered_data(self):
        """Handle export filtered data button click"""
        if 'export_filtered_data' in self.callbacks:
            self.callbacks['export_filtered_data']()
    
    def _toggle_advanced_filters(self):
        """Toggle visibility of advanced filters"""
        if self.advanced_visible.get():
            self.advanced_frame.grid_remove()
            self.advanced_btn.config(text="▼ Advanced Filters")
            self.advanced_visible.set(False)
        else:
            self.advanced_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))
            self.advanced_btn.config(text="▲ Advanced Filters")
            self.advanced_visible.set(True)
    
    def _clear_filters(self):
        """Clear all filters"""
        self.date_from_var.set("")
        self.date_to_var.set("")
        for var in self.priority_vars.values():
            var.set(True)
        self.company_var.set("All")
        self.site_var.set("All")
        self.category_var.set("All")
        self.subcategory_var.set("All")
        self._on_filter_change()
    
    def _apply_date_preset(self, preset_value):
        """Apply a date preset"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        if preset_value == "ALL":
            self.date_from_var.set("")
            self.date_to_var.set("")
        elif preset_value == "YTD":
            year_start = datetime(now.year, 1, 1)
            self.date_from_var.set(year_start.strftime("%Y-%m-%d"))
            self.date_to_var.set(now.strftime("%Y-%m-%d"))
        else:  # numeric days
            start_date = now - timedelta(days=preset_value)
            self.date_from_var.set(start_date.strftime("%Y-%m-%d"))
            self.date_to_var.set(now.strftime("%Y-%m-%d"))
        
        self._on_filter_change()
    
    def _on_total_sites_changed(self, event=None):
        """Handle total sites count change"""
        try:
            total_sites_str = self.total_sites_var.get().strip()
            if not total_sites_str:
                raise ValueError("Total sites cannot be empty")
                
            new_total = int(total_sites_str)
            if new_total < 0:
                raise ValueError("Total sites cannot be negative")
            elif new_total > 10000:
                raise ValueError("Total sites cannot exceed 10,000")
                
            # Update settings
            self.settings.set("stability_analysis.total_supported_sites.count", new_total)
            from datetime import datetime
            self.settings.set("stability_analysis.total_supported_sites.last_updated", datetime.now().isoformat())
            self.settings.save()
            
            # Trigger callback to update analytics
            if 'total_sites_changed' in self.callbacks:
                self.callbacks['total_sites_changed'](new_total)
                
            self.set_status(f"Total supported sites updated to {new_total}")
            
        except ValueError as e:
            # Reset to previous valid value
            current_total = self.settings.get("stability_analysis.total_supported_sites.count", 250)
            self.total_sites_var.set(str(current_total))
            self.set_status(f"Invalid total sites value - using {current_total}")
    
    def get_total_supported_sites(self) -> int:
        """Get current total supported sites count"""
        return int(self.total_sites_var.get())
    
    def _clear_dates(self):
        """Clear date range"""
        self.date_from_var.set("")
        self.date_to_var.set("")
        self._on_filter_change()
    
    def _focus_company(self):
        """Focus on company search"""
        self.company_combo.focus()
        self.company_combo.event_generate('<Button-1>')
    
    def _focus_site(self):
        """Focus on site search"""
        self.site_combo.focus()
        self.site_combo.event_generate('<Button-1>')
    
    def _focus_category(self):
        """Focus on category search"""
        self.category_combo.focus()
        self.category_combo.event_generate('<Button-1>')
    
    def _focus_subcategory(self):
        """Focus on subcategory search"""
        self.subcategory_combo.focus()
        self.subcategory_combo.event_generate('<Button-1>')
    
    def _on_company_search(self, event=None):
        """Handle company search as user types"""
        search_text = self.company_var.get().lower()
        if search_text and search_text != "all":
            # Filter the company options based on search
            all_companies = list(self.company_combo['values'])
            filtered = [comp for comp in all_companies if search_text in comp.lower()]
            self.company_combo['values'] = filtered
            self.company_combo.event_generate('<Down>')
    
    def _on_site_search(self, event=None):
        """Handle site search as user types"""
        search_text = self.site_var.get().lower()
        if search_text and search_text != "all":
            # Filter the site options based on search
            all_sites = list(self.site_combo['values'])
            filtered = [site for site in all_sites if search_text in site.lower()]
            self.site_combo['values'] = filtered
            self.site_combo.event_generate('<Down>')
    
    def _on_category_search(self, event=None):
        """Handle category search as user types"""
        search_text = self.category_var.get().lower()
        if search_text and search_text != "all":
            all_categories = list(self.category_combo['values'])
            filtered = [cat for cat in all_categories if search_text in cat.lower()]
            self.category_combo['values'] = filtered
            self.category_combo.event_generate('<Down>')
    
    def _on_subcategory_search(self, event=None):
        """Handle subcategory search as user types"""
        search_text = self.subcategory_var.get().lower()
        if search_text and search_text != "all":
            all_subcategories = list(self.subcategory_combo['values'])
            filtered = [subcat for subcat in all_subcategories if search_text in subcat.lower()]
            self.subcategory_combo['values'] = filtered
            self.subcategory_combo.event_generate('<Down>')
    
    def _on_data_summary(self):
        """Handle data summary menu item"""
        if 'data_summary' in self.callbacks:
            self.callbacks['data_summary']()
    
    def _on_settings(self):
        """Handle settings menu item"""
        if 'settings' in self.callbacks:
            self.callbacks['settings']()
    
    def _on_help(self):
        """Handle help menu item"""
        messagebox.showinfo("Help", "User guide functionality coming soon!")
    
    def _on_about(self):
        """Handle about menu item"""
        messagebox.showinfo("About", 
                          "IT Stability & Operations Health Monitor\n\n"
                          "A tool for analyzing IT support ticket data\n"
                          "and generating stability reports.\n\n"
                          "Version 1.0")
    
    # Public methods for controller interaction
    def set_callback(self, event_name: str, callback: Callable):
        """Set callback function for UI events"""
        self.callbacks[event_name] = callback
    
    def update_filter_options(self, options: Dict[str, list]):
        """Update filter dropdown options"""
        # Update company options
        if "Company" in options:
            companies = ["All"] + options["Company"]
            self.company_combo['values'] = companies
        
        # Update site options
        if "Site" in options:
            sites = ["All"] + options["Site"]
            self.site_combo['values'] = sites
        
        # Update category options
        if "Category" in options:
            categories = ["All"] + options["Category"]
            self.category_combo['values'] = categories
    
    def update_subcategory_options(self, subcategories: list):
        """Update subcategory options based on selected category"""
        subcats = ["All"] + subcategories
        self.subcategory_combo['values'] = subcats
        self.subcategory_var.set("All")
    
    def get_current_filters(self) -> Dict[str, Any]:
        """Get current filter values"""
        filters = {
            "date_from": self.date_from_var.get() or None,
            "date_to": self.date_to_var.get() or None,
            "priorities": [f"{i+1} - {name}" for i, name in enumerate(["Critical", "High", "Medium", "Low"]) 
                          if self.priority_vars[name].get()],
            "company": self.company_var.get() if self.company_var.get() != "All" else None,
            "site": self.site_var.get() if self.site_var.get() != "All" else None,
            "category": self.category_var.get() if self.category_var.get() != "All" else None,
            "subcategory": self.subcategory_var.get() if self.subcategory_var.get() != "All" else None
        }
        return filters
    
    def display_results(self, data: list, columns: list, title: str = "Results"):
        """Display results in the treeview"""
        # Clear existing data
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Configure columns
        self.results_tree['columns'] = columns
        self.results_tree['show'] = 'headings'
        
        # Set column headings and widths
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120, minwidth=80)
        
        # Insert data
        for row in data:
            self.results_tree.insert('', 'end', values=row)
        
        # Update results info
        self.results_info_label.config(text=f"{title}: {len(data)} records")
    
    def display_analytics_results(self, analytics_data: dict, underlying_tickets, report_type: str):
        """Display analytics results directly in the main results area"""
        # Clear existing data
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Create analytics display data
        analytics_display_data = []
        columns = ["Metric", "Value", "Details"]
        
        # Configure columns for analytics display
        self.results_tree['columns'] = columns
        self.results_tree['show'] = 'headings'
        
        # Set column headings and widths
        self.results_tree.heading("Metric", text="Analytics Metric")
        self.results_tree.heading("Value", text="Value")
        self.results_tree.heading("Details", text="Details/Description")
        
        self.results_tree.column("Metric", width=200, minwidth=150)
        self.results_tree.column("Value", width=120, minwidth=80)
        self.results_tree.column("Details", width=400, minwidth=200)
        
        # Build display data based on report type
        if report_type == "system_stability_dashboard":
            self._build_stability_dashboard_data(analytics_data, analytics_display_data)
        elif report_type == "time_pattern_analysis":
            self._build_pattern_analysis_data(analytics_data, analytics_display_data)
        elif report_type == "stability_insights":
            self._build_stability_insights_data(analytics_data, analytics_display_data)
        
        # Insert analytics data
        for row in analytics_display_data:
            self.results_tree.insert('', 'end', values=row)
        
        # Add separator
        self.results_tree.insert('', 'end', values=("", "", ""))
        self.results_tree.insert('', 'end', values=("--- UNDERLYING EVIDENCE ---", f"{len(underlying_tickets)} tickets", "Tickets used for this analysis"))
        
        # Add sample of underlying tickets
        ticket_columns = ["Number", "Site", "Priority", "Created", "Description", "Status"]
        sample_size = min(10, len(underlying_tickets))  # Show max 10 sample tickets
        
        for i, (_, ticket) in enumerate(underlying_tickets.head(sample_size).iterrows()):
            from ..utils.date_utils import safe_date_display
            created_str = safe_date_display(ticket.get('Created'))
            status = "Resolved" if pd.notna(ticket.get('Resolved')) else "Open"
            desc = str(ticket.get('Short description', ''))[:50] + ("..." if len(str(ticket.get('Short description', ''))) > 50 else "")
            
            self.results_tree.insert('', 'end', values=(
                ticket.get('Number', 'N/A'),
                f"{ticket.get('Site', 'Unknown')} | {ticket.get('Priority', 'Unknown')}",
                f"{created_str} | {desc} | {status}"
            ))
        
        # Update results info with analytics title
        report_titles = {
            "system_stability_dashboard": "System Stability Dashboard",
            "time_pattern_analysis": "Time Pattern Analysis",
            "stability_insights": "Stability Insights"
        }
        title = report_titles.get(report_type, "Analytics Report")
        
        total_items = len(analytics_display_data) + sample_size + 2  # analytics + sample + separators
        self.results_info_label.config(text=f"{title}: {len(analytics_display_data)} metrics, {len(underlying_tickets)} evidence tickets (showing {sample_size} samples)")
    
    def _build_stability_dashboard_data(self, analytics_data: dict, display_data: list):
        """Build display data for stability dashboard"""
        stability_metrics = analytics_data.get('stability_metrics', {})
        
        # Core stability metrics
        display_data.append(["Overall Stability", f"{stability_metrics.get('overall_stability_percentage', 0):.1f}%", "Percentage of sites with zero critical incidents"])
        display_data.append(["Weighted Stability Score", f"{stability_metrics.get('weighted_stability_score', 0):.1f}%", "Weighted stability considering incident severity"])
        display_data.append(["Critical Incident Rate", f"{stability_metrics.get('critical_incident_rate', 0):.1f}%", "Percentage of total incidents that are critical"])
        display_data.append(["Mean Time to Recovery", f"{stability_metrics.get('mean_time_to_recovery', 0):.1f} hours", "Average time to resolve critical incidents"])
        display_data.append(["System Availability", f"{stability_metrics.get('system_availability', 0):.1f}%", "Overall system uptime percentage"])
        display_data.append(["Stability Trend", stability_metrics.get('stability_trend', 'Unknown').title(), "Current stability trend direction"])
        display_data.append(["Benchmark Score", f"{stability_metrics.get('benchmark_score', 0):.1f}/100", "Industry benchmark comparison score"])
        
        # Portfolio metrics if available
        portfolio_metrics = stability_metrics.get('portfolio_metrics', {})
        if portfolio_metrics:
            display_data.append(["--- PORTFOLIO STABILITY ---", "", ""])
            display_data.append(["Total Supported Sites", str(portfolio_metrics.get('total_supported_sites', 0)), "Total number of sites under IT support"])
            display_data.append(["Sites with Zero Critical", f"{portfolio_metrics.get('sites_with_zero_critical', 0)} ({portfolio_metrics.get('zero_critical_percentage', 0):.1f}%)", "Sites with no critical incidents"])
            
            # Critical distribution
            critical_dist = stability_metrics.get('critical_distribution', {})
            if critical_dist:
                display_data.append(["Sites with 1 Critical", f"{critical_dist.get('one_critical', {}).get('count', 0)} ({critical_dist.get('one_critical', {}).get('percentage', 0):.1f}%)", "Sites with exactly one critical incident"])
                display_data.append(["Sites with 2 Criticals", f"{critical_dist.get('two_criticals', {}).get('count', 0)} ({critical_dist.get('two_criticals', {}).get('percentage', 0):.1f}%)", "Sites with exactly two critical incidents"])
                display_data.append(["Sites with 3 Criticals", f"{critical_dist.get('three_criticals', {}).get('count', 0)} ({critical_dist.get('three_criticals', {}).get('percentage', 0):.1f}%)", "Sites with exactly three critical incidents"])
                display_data.append(["Sites with 4+ Criticals", f"{critical_dist.get('four_plus_criticals', {}).get('count', 0)} ({critical_dist.get('four_plus_criticals', {}).get('percentage', 0):.1f}%)", "Sites with four or more critical incidents"])
        
        # Site performance distribution
        distribution = stability_metrics.get('site_performance_distribution', {})
        if distribution:
            display_data.append(["--- SITE PERFORMANCE ---", "", ""])
            dist_data = distribution.get('distribution', {})
            for category, data in dist_data.items():
                display_data.append([f"{category.title()} Sites", f"{data.get('count', 0)} ({data.get('percentage', 0):.1f}%)", f"Sites categorized as {category.lower()} performance"])
    
    def _build_pattern_analysis_data(self, analytics_data: dict, display_data: list):
        """Build display data for pattern analysis"""
        pattern_results = analytics_data.get('pattern_results', {})
        
        # Synchronized incidents
        sync_incidents = pattern_results.get('synchronized_incidents', [])
        if sync_incidents:
            display_data.append(["Synchronized Incident Groups", str(len(sync_incidents)), "Number of incident groups that occurred simultaneously"])
            for i, incident in enumerate(sync_incidents[:5], 1):  # Show top 5
                display_data.append([f"Sync Group {i}", f"{len(incident.sites)} sites, {incident.correlation_score:.1%} correlation", incident.likely_root_cause])
        
        # Correlations summary
        correlations = pattern_results.get('time_correlation_matrix', {})
        if correlations:
            display_data.append(["Site Correlations Detected", "Yes", "Strong correlations found between sites indicating shared dependencies"])
        
        # Peak incident times - fix dictionary slicing error
        peak_times = pattern_results.get('peak_incident_times', {})  # Expect dict, not list
        if peak_times:
            display_data.append(["--- INCIDENT PATTERNS ---", "", ""])
            
            # Display peak hour if available
            if 'peak_hour' in peak_times:
                peak_hour = peak_times['peak_hour']
                display_data.append([
                    f"Peak Hour: {peak_hour.get('hour', 0):02d}:00", 
                    f"{peak_hour.get('count', 0)} incidents", 
                    f"{peak_hour.get('percentage', 0):.1f}% of total incidents"
                ])
            
            # Display peak day if available  
            if 'peak_day' in peak_times:
                peak_day = peak_times['peak_day']
                display_data.append([
                    f"Peak Day: {peak_day.get('day', 'Unknown')}s", 
                    f"{peak_day.get('count', 0)} incidents", 
                    f"{peak_day.get('percentage', 0):.1f}% of total incidents"
                ])
                
            # Display peak month if available
            if 'peak_month' in peak_times:
                peak_month = peak_times['peak_month']
                display_data.append([
                    f"Peak Month: {peak_month.get('month', 'Unknown')}", 
                    f"{peak_month.get('count', 0)} incidents", 
                    f"{peak_month.get('percentage', 0):.1f}% of total incidents"
                ])
    
    def _build_stability_insights_data(self, analytics_data: dict, display_data: list):
        """Build display data for stability insights"""
        insights = analytics_data.get('insights', [])
        
        display_data.append(["--- KEY INSIGHTS ---", "", ""])
        for i, insight in enumerate(insights, 1):
            display_data.append([f"Insight {i}", "Recommendation", insight])
        
        # Supporting metrics
        stability_metrics = analytics_data.get('stability_metrics')
        if stability_metrics:
            display_data.append(["--- SUPPORTING METRICS ---", "", ""])
            display_data.append(["Overall Stability", f"{stability_metrics.overall_stability_percentage:.1f}%", "Current overall system stability"])
            display_data.append(["Critical Incident Rate", f"{stability_metrics.critical_incident_rate:.1f}%", "Rate of critical incidents"])
            display_data.append(["Benchmark Score", f"{stability_metrics.benchmark_score:.1f}/100", "Performance against industry benchmarks"])
    
    def set_status(self, status: str):
        """Update status bar text"""
        self.status_label.config(text=status)
    
    def show_progress(self, show: bool = True, value: float = 0):
        """Show/hide progress bar"""
        if show:
            self.progress_bar.pack(side=tk.LEFT, padx=(10, 0))
            self.progress_var.set(value)
        else:
            self.progress_bar.pack_forget()
    
    def update_data_info(self, info: str):
        """Update data information in status bar"""
        self.data_info_label.config(text=info)
    
    def _update_ui_state(self, data_loaded: bool):
        """Update UI component states based on data availability"""
        state = "normal" if data_loaded else "disabled"
        
        # Update button states
        self.export_btn.config(state=state)
        self.export_comprehensive_btn.config(state=state)
        self.refresh_btn.config(state=state)
        self.export_selected_btn.config(state=state)
        
        # Update report button states
        report_buttons = [
            self.hotspots_btn, self.scorecard_btn, self.green_btn, 
            self.franchise_btn, self.equipment_btn, self.repeat_btn,
            self.resolution_btn, self.workload_btn, self.incident_details_btn,
            self.drill_down_btn, self.export_filtered_btn,
            # Phase 2 analytics buttons
            self.stability_dashboard_btn, self.pattern_analysis_btn,
            self.stability_insights_btn, self.data_quality_report_btn
        ]
        
        for btn in report_buttons:
            btn.config(state=state)
    
    def data_loaded(self, loaded: bool):
        """Update UI when data is loaded/unloaded"""
        self._update_ui_state(loaded)
    
    def get_quality_tab(self):
        """Get reference to quality management tab"""
        return self.quality_tab