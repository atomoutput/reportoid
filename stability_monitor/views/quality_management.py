"""
Data Quality Management Window for manual review and correction of data issues
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
import json

class DuplicateReviewDialog(tk.Toplevel):
    """Dialog for reviewing and managing duplicate ticket groups"""
    
    def __init__(self, parent, duplicate_group, callback=None):
        super().__init__(parent)
        self.duplicate_group = duplicate_group
        self.callback = callback
        self.result = None
        
        self.title(f"Review Duplicate Group - {duplicate_group.confidence_score:.1%} Confidence")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()
        
        # Make dialog modal
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        self._create_widgets()
        self._populate_data()
        
        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header with confidence score
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        confidence_label = ttk.Label(
            header_frame, 
            text=f"Duplicate Confidence: {self.duplicate_group.confidence_score:.1%}",
            font=("Arial", 12, "bold")
        )
        confidence_label.pack(side=tk.LEFT)
        
        status_color = "green" if self.duplicate_group.confidence_score >= 0.9 else "orange" if self.duplicate_group.confidence_score >= 0.7 else "red"
        
        # Tickets comparison frame
        comparison_frame = ttk.LabelFrame(main_frame, text="Ticket Comparison", padding=10)
        comparison_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create notebook for side-by-side comparison
        self.notebook = ttk.Notebook(comparison_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Comparison view (side by side)
        self.comparison_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.comparison_frame, text="Side-by-Side Comparison")
        
        # Details view (full details)
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="Full Details")
        
        # Action buttons frame
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Notes section
        notes_label = ttk.Label(action_frame, text="Review Notes:")
        notes_label.pack(anchor=tk.W)
        
        self.notes_text = scrolledtext.ScrolledText(action_frame, height=4, width=80)
        self.notes_text.pack(fill=tk.X, pady=(2, 10))
        
        # Buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(fill=tk.X)
        
        self.merge_btn = ttk.Button(
            button_frame, 
            text="✅ Merge as Duplicates", 
            command=self._on_merge,
            style="Accent.TButton"
        )
        self.merge_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.dismiss_btn = ttk.Button(
            button_frame, 
            text="❌ Dismiss (Not Duplicates)", 
            command=self._on_dismiss
        )
        self.dismiss_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.skip_btn = ttk.Button(
            button_frame, 
            text="⏭️ Skip for Now", 
            command=self._on_skip
        )
        self.skip_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        self.cancel_btn = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._on_cancel
        )
        self.cancel_btn.pack(side=tk.RIGHT)
    
    def _populate_data(self):
        """Populate dialog with duplicate group data"""
        self._create_comparison_view()
        self._create_details_view()
    
    def _create_comparison_view(self):
        """Create side-by-side comparison of tickets"""
        # Create canvas and scrollbar for comparison
        canvas = tk.Canvas(self.comparison_frame)
        scrollbar = ttk.Scrollbar(self.comparison_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Get all tickets in the group
        all_tickets = self.duplicate_group.get_all_tickets()
        
        # Create headers
        headers = ["Field", "Primary Ticket"] + [f"Duplicate {i+1}" for i in range(len(self.duplicate_group.duplicates))]
        
        for col, header in enumerate(headers):
            header_label = ttk.Label(scrollable_frame, text=header, font=("Arial", 10, "bold"))
            header_label.grid(row=0, column=col, padx=5, pady=2, sticky="ew")
        
        # Compare key fields
        fields_to_compare = [
            ("Ticket #", "Number"),
            ("Site", "Site"),
            ("Priority", "Priority"),
            ("Created", "Created"),
            ("Description", "Short description"),
            ("Category", "Category"),
            ("Subcategory", "Subcategory")
        ]
        
        for row, (field_name, field_key) in enumerate(fields_to_compare, 1):
            # Field name
            field_label = ttk.Label(scrollable_frame, text=field_name, font=("Arial", 9, "bold"))
            field_label.grid(row=row, column=0, padx=5, pady=1, sticky="w")
            
            # Values for each ticket
            for col, ticket in enumerate(all_tickets, 1):
                value = ticket.get(field_key, "N/A")
                
                # Format datetime fields
                if field_key in ["Created", "Resolved"] and hasattr(value, 'strftime'):
                    value = value.strftime("%Y-%m-%d %H:%M")
                
                # Highlight differences
                is_different = False
                if col > 1:  # Not the primary ticket
                    primary_value = all_tickets[0].get(field_key, "N/A")
                    is_different = str(value) != str(primary_value)
                
                # Create label with appropriate styling
                value_text = str(value)[:40] + "..." if len(str(value)) > 40 else str(value)
                
                value_label = ttk.Label(
                    scrollable_frame, 
                    text=value_text,
                    foreground="red" if is_different else "black"
                )
                value_label.grid(row=row, column=col, padx=5, pady=1, sticky="w")
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_details_view(self):
        """Create detailed view of all tickets"""
        details_text = scrolledtext.ScrolledText(self.details_frame, wrap=tk.WORD)
        details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add detailed information
        details_text.insert(tk.END, f"DUPLICATE GROUP ANALYSIS\n")
        details_text.insert(tk.END, f"{'='*50}\n\n")
        details_text.insert(tk.END, f"Confidence Score: {self.duplicate_group.confidence_score:.1%}\n")
        details_text.insert(tk.END, f"Total Tickets: {len(self.duplicate_group.get_all_tickets())}\n")
        details_text.insert(tk.END, f"Review Status: {getattr(self.duplicate_group, 'review_status', 'pending')}\n\n")
        
        all_tickets = self.duplicate_group.get_all_tickets()
        
        for i, ticket in enumerate(all_tickets):
            details_text.insert(tk.END, f"TICKET {i+1} {'(PRIMARY)' if i == 0 else f'(DUPLICATE {i})'}\n")
            details_text.insert(tk.END, f"{'-'*30}\n")
            
            for key, value in ticket.items():
                if key not in ['index']:  # Skip internal pandas fields
                    # Format datetime fields
                    if hasattr(value, 'strftime'):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    
                    details_text.insert(tk.END, f"{key}: {value}\n")
            
            details_text.insert(tk.END, "\n")
        
        details_text.config(state=tk.DISABLED)  # Make read-only
    
    def _on_merge(self):
        """Handle merge action"""
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        if not notes:
            if not messagebox.askyesno("Confirm Merge", "No review notes provided. Continue with merge?"):
                return
        
        primary_ticket = self.duplicate_group.primary_ticket
        duplicate_tickets = self.duplicate_group.duplicates
        
        self.result = {
            "action": "merge",
            "primary_ticket_id": str(primary_ticket.get("Number", "N/A")),
            "duplicate_ticket_ids": [str(dup.get("Number", "N/A")) for dup in duplicate_tickets],
            "notes": notes,
            "confidence": self.duplicate_group.confidence_score
        }
        
        self.destroy()
    
    def _on_dismiss(self):
        """Handle dismiss action"""
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        if not notes:
            messagebox.showwarning("Notes Required", "Please provide notes explaining why these are not duplicates.")
            return
        
        all_tickets = self.duplicate_group.get_all_tickets()
        
        self.result = {
            "action": "dismiss",
            "ticket_ids": [str(ticket.get("Number", "N/A")) for ticket in all_tickets],
            "notes": notes,
            "confidence": self.duplicate_group.confidence_score
        }
        
        self.destroy()
    
    def _on_skip(self):
        """Handle skip action"""
        self.result = {
            "action": "skip",
            "notes": self.notes_text.get("1.0", tk.END).strip()
        }
        
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel action"""
        self.result = None
        self.destroy()

class DataQualityTab(ttk.Frame):
    """Data Quality Management tab for the main application"""
    
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.settings = settings
        self.callbacks = {}
        
        self._create_widgets()
        self._update_ui_state(data_loaded=False)
    
    def _create_widgets(self):
        """Create the data quality management interface"""
        
        # Header frame with summary
        header_frame = ttk.LabelFrame(self, text="📊 Data Quality Overview", padding=10)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Quality metrics
        metrics_frame = ttk.Frame(header_frame)
        metrics_frame.pack(fill=tk.X)
        
        self.quality_score_label = ttk.Label(
            metrics_frame, 
            text="Quality Score: N/A",
            font=("Arial", 12, "bold")
        )
        self.quality_score_label.pack(side=tk.LEFT)
        
        self.duplicates_label = ttk.Label(
            metrics_frame,
            text="Duplicates: N/A",
            font=("Arial", 10)
        )
        self.duplicates_label.pack(side=tk.LEFT, padx=(20, 0))
        
        self.review_queue_label = ttk.Label(
            metrics_frame,
            text="Review Queue: N/A",
            font=("Arial", 10)
        )
        self.review_queue_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Action buttons
        action_frame = ttk.Frame(header_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.refresh_btn = ttk.Button(
            action_frame,
            text="🔄 Refresh Quality Analysis",
            command=self._on_refresh_quality,
            state="disabled"
        )
        self.refresh_btn.pack(side=tk.LEFT)
        
        self.auto_process_btn = ttk.Button(
            action_frame,
            text="🤖 Auto-Process High Confidence",
            command=self._on_auto_process,
            state="disabled"
        )
        self.auto_process_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        self.export_log_btn = ttk.Button(
            action_frame,
            text="📤 Export Audit Log",
            command=self._on_export_audit,
            state="disabled"
        )
        self.export_log_btn.pack(side=tk.RIGHT)
        
        # Main content notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Duplicate Review tab
        self.duplicate_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.duplicate_frame, text="🔍 Duplicate Review")
        self._create_duplicate_review_tab()
        
        # Quality Report tab
        self.report_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.report_frame, text="📊 Quality Report")
        self._create_quality_report_tab()
        
        # Audit Trail tab
        self.audit_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.audit_frame, text="📋 Audit Trail")
        self._create_audit_trail_tab()
    
    def _create_duplicate_review_tab(self):
        """Create duplicate review interface"""
        # Control frame
        control_frame = ttk.Frame(self.duplicate_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Duplicate Groups Queue:").pack(side=tk.LEFT)
        
        self.queue_filter = ttk.Combobox(
            control_frame,
            values=["All", "High Confidence", "Manual Review Required", "Low Confidence"],
            state="readonly",
            width=20
        )
        self.queue_filter.set("Manual Review Required")
        self.queue_filter.pack(side=tk.LEFT, padx=(10, 0))
        self.queue_filter.bind("<<ComboboxSelected>>", self._on_filter_change)
        
        self.review_btn = ttk.Button(
            control_frame,
            text="👁️ Review Selected",
            command=self._on_review_selected,
            state="disabled"
        )
        self.review_btn.pack(side=tk.RIGHT)
        
        self.batch_process_btn = ttk.Button(
            control_frame,
            text="⚡ Batch Process",
            command=self._on_batch_process,
            state="disabled"
        )
        self.batch_process_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Queue treeview
        tree_frame = ttk.Frame(self.duplicate_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Group ID", "Primary Ticket", "Duplicates", "Confidence", "Site", "Created", "Status", "Action Needed")
        
        self.queue_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        column_widths = {"Group ID": 80, "Primary Ticket": 100, "Duplicates": 150, 
                        "Confidence": 80, "Site": 200, "Created": 120, "Status": 100, "Action Needed": 150}
        
        for col in columns:
            self.queue_tree.heading(col, text=col)
            self.queue_tree.column(col, width=column_widths.get(col, 120), minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.queue_tree.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.queue_tree.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.queue_tree.configure(xscrollcommand=h_scrollbar.set)
        
        self.queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind double-click
        self.queue_tree.bind("<Double-1>", lambda e: self._on_review_selected())
        
        # Status frame
        queue_status_frame = ttk.Frame(self.duplicate_frame)
        queue_status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.queue_status_label = ttk.Label(queue_status_frame, text="No duplicate groups loaded")
        self.queue_status_label.pack(side=tk.LEFT)
    
    def _create_quality_report_tab(self):
        """Create quality report display"""
        report_text = scrolledtext.ScrolledText(
            self.report_frame, 
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        report_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.quality_report_text = report_text
    
    def _create_audit_trail_tab(self):
        """Create audit trail display"""
        # Control frame
        audit_control_frame = ttk.Frame(self.audit_frame)
        audit_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(audit_control_frame, text="Filter by:").pack(side=tk.LEFT)
        
        self.audit_filter = ttk.Combobox(
            audit_control_frame,
            values=["All Actions", "Merge Duplicates", "Dismiss Duplicates", "Manual Corrections", "Reversals"],
            state="readonly",
            width=20
        )
        self.audit_filter.set("All Actions")
        self.audit_filter.pack(side=tk.LEFT, padx=(10, 0))
        
        self.refresh_audit_btn = ttk.Button(
            audit_control_frame,
            text="🔄 Refresh",
            command=self._refresh_audit_trail
        )
        self.refresh_audit_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Audit trail treeview
        audit_tree_frame = ttk.Frame(self.audit_frame)
        audit_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        audit_columns = ("Timestamp", "Action", "User", "Description", "Affected Tickets", "Status")
        
        self.audit_tree = ttk.Treeview(audit_tree_frame, columns=audit_columns, show='headings', height=12)
        
        # Configure audit columns
        audit_column_widths = {"Timestamp": 120, "Action": 100, "User": 80,
                              "Description": 300, "Affected Tickets": 150, "Status": 80}
        
        for col in audit_columns:
            self.audit_tree.heading(col, text=col)
            self.audit_tree.column(col, width=audit_column_widths.get(col, 120), minwidth=80)
        
        # Audit scrollbars
        audit_v_scrollbar = ttk.Scrollbar(audit_tree_frame, orient=tk.VERTICAL, command=self.audit_tree.yview)
        audit_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.audit_tree.configure(yscrollcommand=audit_v_scrollbar.set)
        
        self.audit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Event handlers
    def _on_refresh_quality(self):
        """Handle refresh quality analysis"""
        if 'refresh_quality' in self.callbacks:
            self.callbacks['refresh_quality']()
    
    def _on_auto_process(self):
        """Handle auto-process high confidence duplicates"""
        if messagebox.askyesno("Confirm Auto-Process", 
                              "Automatically process all high-confidence duplicate groups?\n\n"
                              "This will merge duplicates with >95% confidence."):
            if 'auto_process_duplicates' in self.callbacks:
                self.callbacks['auto_process_duplicates']()
    
    def _on_export_audit(self):
        """Handle export audit log"""
        if 'export_audit_log' in self.callbacks:
            self.callbacks['export_audit_log']()
    
    def _on_filter_change(self, event=None):
        """Handle duplicate queue filter change"""
        self._refresh_duplicate_queue()
    
    def _on_review_selected(self):
        """Handle review selected duplicate group"""
        selected_items = self.queue_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a duplicate group to review.")
            return
        
        if 'review_duplicate_group' in self.callbacks:
            item = self.queue_tree.item(selected_items[0])
            group_id = item['values'][0]
            self.callbacks['review_duplicate_group'](group_id)
    
    def _on_batch_process(self):
        """Handle batch processing of selected duplicates"""
        selected_items = self.queue_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select duplicate groups to batch process.")
            return
        
        if len(selected_items) > 10:
            if not messagebox.askyesno("Large Batch", f"Process {len(selected_items)} groups? This may take a while."):
                return
        
        if 'batch_process_duplicates' in self.callbacks:
            group_ids = [self.queue_tree.item(item)['values'][0] for item in selected_items]
            self.callbacks['batch_process_duplicates'](group_ids)
    
    def _refresh_duplicate_queue(self):
        """Refresh the duplicate queue display"""
        if 'get_duplicate_queue' in self.callbacks:
            filter_type = self.queue_filter.get()
            queue_data = self.callbacks['get_duplicate_queue'](filter_type)
            self._update_queue_display(queue_data)
    
    def _refresh_audit_trail(self):
        """Refresh the audit trail display"""
        if 'get_audit_trail' in self.callbacks:
            filter_type = self.audit_filter.get()
            audit_data = self.callbacks['get_audit_trail'](filter_type)
            self._update_audit_display(audit_data)
    
    def _update_queue_display(self, queue_data):
        """Update duplicate queue tree display"""
        # Clear existing items
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        
        # Add new items
        for group in queue_data:
            self.queue_tree.insert('', 'end', values=group)
        
        # Update status
        self.queue_status_label.config(text=f"{len(queue_data)} duplicate groups in queue")
    
    def _update_audit_display(self, audit_data):
        """Update audit trail tree display"""
        # Clear existing items
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)
        
        # Add new items
        for action in audit_data:
            self.audit_tree.insert('', 'end', values=action)
    
    def _update_ui_state(self, data_loaded: bool = False, has_duplicates: bool = False):
        """Update UI state based on data availability"""
        state = "normal" if data_loaded else "disabled"
        
        self.refresh_btn.config(state=state)
        self.export_log_btn.config(state=state)
        
        duplicate_state = "normal" if has_duplicates else "disabled"
        self.auto_process_btn.config(state=duplicate_state)
        self.review_btn.config(state=duplicate_state)
        self.batch_process_btn.config(state=duplicate_state)
    
    # Public methods for controller interaction
    def set_callback(self, event_name: str, callback: Callable):
        """Set callback function for UI events"""
        self.callbacks[event_name] = callback
    
    def update_quality_metrics(self, quality_report: Dict[str, Any]):
        """Update quality metrics display"""
        quality_score = quality_report.get("data_quality_score", 0)
        dup_analysis = quality_report.get("duplicate_analysis", {})
        
        # Update labels
        score_color = "green" if quality_score >= 90 else "orange" if quality_score >= 75 else "red"
        self.quality_score_label.config(text=f"Quality Score: {quality_score:.1f}%")
        
        total_groups = dup_analysis.get("total_duplicate_groups", 0)
        manual_review = dup_analysis.get("manual_review_required", 0)
        
        self.duplicates_label.config(text=f"Duplicate Groups: {total_groups}")
        self.review_queue_label.config(text=f"Manual Review: {manual_review}")
        
        # Update quality report text
        self._update_quality_report_text(quality_report)
        
        # Update UI state
        self._update_ui_state(data_loaded=True, has_duplicates=total_groups > 0)
    
    def _update_quality_report_text(self, quality_report: Dict[str, Any]):
        """Update quality report text display"""
        self.quality_report_text.delete(1.0, tk.END)
        
        # Format quality report
        report_text = f"""DATA QUALITY REPORT
{'='*50}

Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Overall Quality Score: {quality_report.get('data_quality_score', 0):.1f}%

SITE FILTERING
{'-'*20}
Original Records: {quality_report.get('original_dataset', {}).get('total_tickets', 0)}
Filtered Records: {quality_report.get('site_filtering', {}).get('filtered_count', 0)}
Removed Records: {quality_report.get('site_filtering', {}).get('removed_count', 0)}

DUPLICATE ANALYSIS
{'-'*20}
Total Duplicate Groups: {quality_report.get('duplicate_analysis', {}).get('total_duplicate_groups', 0)}
Tickets Affected: {quality_report.get('duplicate_analysis', {}).get('tickets_affected', 0)}
Duplicate Percentage: {quality_report.get('duplicate_analysis', {}).get('duplicate_percentage', 0):.1f}%
High Confidence Groups: {quality_report.get('duplicate_analysis', {}).get('high_confidence_groups', 0)}
Manual Review Required: {quality_report.get('duplicate_analysis', {}).get('manual_review_required', 0)}

RECOMMENDATIONS
{'-'*20}
"""
        
        recommendations = quality_report.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            report_text += f"{i}. {rec}\n"
        
        self.quality_report_text.insert(1.0, report_text)
        self.quality_report_text.config(state=tk.DISABLED)
    
    def show_review_dialog(self, duplicate_group):
        """Show duplicate review dialog"""
        dialog = DuplicateReviewDialog(self, duplicate_group)
        self.wait_window(dialog)
        return dialog.result