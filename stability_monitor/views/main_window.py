"""
Main application window
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Callable

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
        
        self.export_btn = ttk.Button(toolbar_frame, text="💾 Export", command=self._on_export_results, state="disabled")
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_btn = ttk.Button(toolbar_frame, text="🔄 Refresh", command=self._on_refresh, state="disabled")
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
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
    
    def _create_filter_panel(self):
        """Create the filters panel"""
        # Filters frame
        filters_frame = ttk.LabelFrame(self.analysis_frame, text="📊 Filters", padding=10)
        filters_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Configure grid for filters
        filters_frame.grid_columnconfigure(1, weight=1)
        filters_frame.grid_columnconfigure(3, weight=1)
        
        # Date range filters
        ttk.Label(filters_frame, text="Date Range:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        date_frame = ttk.Frame(filters_frame)
        date_frame.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT)
        self.date_from_var = tk.StringVar()
        self.date_from_entry = ttk.Entry(date_frame, textvariable=self.date_from_var, width=12)
        self.date_from_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT)
        self.date_to_var = tk.StringVar()
        self.date_to_entry = ttk.Entry(date_frame, textvariable=self.date_to_var, width=12)
        self.date_to_entry.pack(side=tk.LEFT, padx=(5, 0))
        
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
        
        # Company and Site filters
        ttk.Label(filters_frame, text="Company:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(10, 0))
        
        self.company_var = tk.StringVar(value="All")
        self.company_combo = ttk.Combobox(filters_frame, textvariable=self.company_var, state="readonly", width=30)
        self.company_combo.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=(10, 0))
        self.company_combo.bind('<<ComboboxSelected>>', self._on_company_changed)
        
        ttk.Label(filters_frame, text="Site:").grid(row=1, column=2, sticky="w", padx=(0, 5), pady=(10, 0))
        
        self.site_var = tk.StringVar(value="All")
        self.site_combo = ttk.Combobox(filters_frame, textvariable=self.site_var, state="readonly", width=30)
        self.site_combo.grid(row=1, column=3, sticky="ew", pady=(10, 0))
        self.site_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        # Advanced filters (collapsible)
        self.advanced_visible = tk.BooleanVar(value=False)
        self.advanced_btn = ttk.Button(filters_frame, text="▼ Advanced Filters", 
                                     command=self._toggle_advanced_filters)
        self.advanced_btn.grid(row=2, column=0, sticky="w", pady=(10, 0))
        
        # Advanced filters frame (initially hidden)
        self.advanced_frame = ttk.Frame(filters_frame)
        
        # Category and Subcategory
        ttk.Label(self.advanced_frame, text="Category:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=(10, 0))
        
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(self.advanced_frame, textvariable=self.category_var, state="readonly", width=20)
        self.category_combo.grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=(10, 0))
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_changed)
        
        ttk.Label(self.advanced_frame, text="Subcategory:").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=(10, 0))
        
        self.subcategory_var = tk.StringVar(value="All")
        self.subcategory_combo = ttk.Combobox(self.advanced_frame, textvariable=self.subcategory_var, state="readonly", width=20)
        self.subcategory_combo.grid(row=0, column=3, sticky="ew", pady=(10, 0))
        self.subcategory_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
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
        self.workload_btn.pack(side=tk.LEFT)
    
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
        self.refresh_btn.config(state=state)
        self.export_selected_btn.config(state=state)
        
        # Update report button states
        report_buttons = [
            self.hotspots_btn, self.scorecard_btn, self.green_btn, 
            self.franchise_btn, self.equipment_btn, self.repeat_btn,
            self.resolution_btn, self.workload_btn
        ]
        
        for btn in report_buttons:
            btn.config(state=state)
    
    def data_loaded(self, loaded: bool):
        """Update UI when data is loaded/unloaded"""
        self._update_ui_state(loaded)