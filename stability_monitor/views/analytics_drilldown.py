"""
Analytics Drilldown Dialog - Enhanced analytics with evidence view
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Dict, Any

class AnalyticsDrilldownDialog:
    """Dialog for showing enhanced analytics with underlying ticket evidence"""
    
    def __init__(self, parent: tk.Tk, title: str, analytics_data: Dict[str, Any], 
                 underlying_tickets: pd.DataFrame, report_type: str):
        self.parent = parent
        self.title = title
        self.analytics_data = analytics_data
        self.underlying_tickets = underlying_tickets
        self.report_type = report_type
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (parent.winfo_screenwidth() // 2) - (1000 // 2)
        y = (parent.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"1000x700+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title label
        title_label = ttk.Label(main_frame, text=self.title, font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create notebook for different views
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Analytics summary tab
        analytics_frame = ttk.Frame(notebook)
        notebook.add(analytics_frame, text="Analytics Summary")
        self._create_analytics_summary(analytics_frame)
        
        # Evidence tab
        evidence_frame = ttk.Frame(notebook)
        notebook.add(evidence_frame, text="Underlying Evidence")
        self._create_evidence_view(evidence_frame)
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_button = ttk.Button(button_frame, text="Close", command=self.dialog.destroy)
        close_button.pack(side=tk.RIGHT)
        
        export_button = ttk.Button(button_frame, text="Export to Excel", command=self._export_data)
        export_button.pack(side=tk.RIGHT, padx=(0, 10))
    
    def _create_analytics_summary(self, parent):
        """Create analytics summary view"""
        # Create text widget with scrollbar
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Display analytics based on report type
        if self.report_type == "system_stability_dashboard":
            self._display_stability_metrics(text_widget)
        elif self.report_type == "time_pattern_analysis":
            self._display_pattern_analysis(text_widget)
        elif self.report_type == "stability_insights":
            self._display_stability_insights(text_widget)
        else:
            text_widget.insert(tk.END, "Analytics data not available for this report type.")
        
        text_widget.config(state=tk.DISABLED)
    
    def _display_stability_metrics(self, text_widget):
        """Display stability metrics summary"""
        text_widget.insert(tk.END, "SYSTEM STABILITY DASHBOARD\n")
        text_widget.insert(tk.END, "=" * 50 + "\n\n")
        
        stability_metrics = self.analytics_data.get('stability_metrics', {})
        
        # Core metrics
        text_widget.insert(tk.END, "📊 CORE STABILITY METRICS:\n")
        text_widget.insert(tk.END, f"• Overall Stability: {stability_metrics.get('overall_stability_percentage', 0):.1f}%\n")
        text_widget.insert(tk.END, f"• Weighted Stability Score: {stability_metrics.get('weighted_stability_score', 0):.1f}%\n")
        text_widget.insert(tk.END, f"• Critical Incident Rate: {stability_metrics.get('critical_incident_rate', 0):.1f}%\n")
        text_widget.insert(tk.END, f"• Mean Time to Recovery: {stability_metrics.get('mean_time_to_recovery', 0):.1f} hours\n")
        text_widget.insert(tk.END, f"• System Availability: {stability_metrics.get('system_availability', 0):.1f}%\n")
        text_widget.insert(tk.END, f"• Stability Trend: {stability_metrics.get('stability_trend', 'Unknown').title()}\n")
        text_widget.insert(tk.END, f"• Benchmark Score: {stability_metrics.get('benchmark_score', 0):.1f}/100\n\n")
        
        # Site performance distribution
        distribution = stability_metrics.get('site_performance_distribution', {})
        if distribution:
            text_widget.insert(tk.END, "🏢 SITE PERFORMANCE DISTRIBUTION:\n")
            dist_data = distribution.get('distribution', {})
            for category, data in dist_data.items():
                text_widget.insert(tk.END, f"• {category.title()}: {data['count']} sites ({data['percentage']:.1f}%)\n")
            text_widget.insert(tk.END, "\n")
    
    def _display_pattern_analysis(self, text_widget):
        """Display pattern analysis results"""
        text_widget.insert(tk.END, "TIME PATTERN ANALYSIS\n")
        text_widget.insert(tk.END, "=" * 50 + "\n\n")
        
        pattern_results = self.analytics_data.get('pattern_results', {})
        
        # Synchronized incidents
        sync_incidents = pattern_results.get('synchronized_incidents', [])
        if sync_incidents:
            text_widget.insert(tk.END, f"🔗 SYNCHRONIZED INCIDENTS ({len(sync_incidents)} found):\n")
            for i, incident in enumerate(sync_incidents[:5], 1):
                text_widget.insert(tk.END, f"{i}. {incident.likely_root_cause}\n")
                text_widget.insert(tk.END, f"   Sites: {len(incident.sites)}, Correlation: {incident.correlation_score:.1%}\n")
            text_widget.insert(tk.END, "\n")
        
        # Correlations
        correlations = pattern_results.get('time_correlation_matrix', {})
        if correlations:
            text_widget.insert(tk.END, "📊 SITE CORRELATIONS:\n")
            text_widget.insert(tk.END, "Strong correlations detected between sites indicate shared dependencies.\n\n")
    
    def _display_stability_insights(self, text_widget):
        """Display stability insights"""
        text_widget.insert(tk.END, "STABILITY INSIGHTS & RECOMMENDATIONS\n")
        text_widget.insert(tk.END, "=" * 50 + "\n\n")
        
        insights = self.analytics_data.get('insights', [])
        if insights:
            text_widget.insert(tk.END, "💡 KEY INSIGHTS:\n")
            for i, insight in enumerate(insights, 1):
                text_widget.insert(tk.END, f"{i}. {insight}\n")
            text_widget.insert(tk.END, "\n")
        
        # Display associated metrics
        stability_metrics = self.analytics_data.get('stability_metrics')
        if stability_metrics:
            text_widget.insert(tk.END, "📈 SUPPORTING METRICS:\n")
            text_widget.insert(tk.END, f"• Overall Stability: {stability_metrics.overall_stability_percentage:.1f}%\n")
            text_widget.insert(tk.END, f"• Critical Rate: {stability_metrics.critical_incident_rate:.1f}%\n")
            text_widget.insert(tk.END, f"• Benchmark Score: {stability_metrics.benchmark_score:.1f}/100\n")
    
    def _create_evidence_view(self, parent):
        """Create evidence view with ticket details"""
        # Create treeview for tickets
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Define columns
        columns = ("Number", "Site", "Priority", "Created", "Description", "Status")
        
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Define headings
        for col in columns:
            tree.heading(col, text=col)
            if col == "Description":
                tree.column(col, width=300)
            elif col in ["Number", "Status"]:
                tree.column(col, width=100)
            else:
                tree.column(col, width=120)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack everything
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Populate with ticket data
        for _, ticket in self.underlying_tickets.iterrows():
            status = "Resolved" if pd.notna(ticket.get('Resolved')) else "Open"
            created = ticket['Created'].strftime('%Y-%m-%d %H:%M') if pd.notna(ticket.get('Created')) else 'Unknown'
            description = str(ticket.get('Short description', ''))[:50] + ("..." if len(str(ticket.get('Short description', ''))) > 50 else "")
            
            tree.insert("", tk.END, values=(
                ticket.get('Number', 'N/A'),
                ticket.get('Site', 'Unknown'),
                ticket.get('Priority', 'Unknown'),
                created,
                description,
                status
            ))
        
        # Add summary label
        summary_frame = ttk.Frame(parent)
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        total_tickets = len(self.underlying_tickets)
        critical_tickets = len(self.underlying_tickets[self.underlying_tickets['Priority'].str.contains('Critical', case=False, na=False)])
        
        summary_label = ttk.Label(summary_frame, 
                                text=f"Total Evidence: {total_tickets} tickets | Critical: {critical_tickets} tickets")
        summary_label.pack()
    
    def _export_data(self):
        """Export analytics and evidence data to Excel"""
        from tkinter import filedialog, messagebox
        import openpyxl
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Export Analytics Data"
            )
            
            if file_path:
                # Create workbook and export data
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Analytics Evidence"
                
                # Add ticket data
                for r in dataframe_to_rows(self.underlying_tickets, index=False, header=True):
                    ws.append(r)
                
                wb.save(file_path)
                messagebox.showinfo("Export Complete", f"Analytics data exported to:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")