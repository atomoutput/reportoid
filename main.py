#!/usr/bin/env python3
"""
IT Stability & Operations Health Monitor
Main application entry point
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stability_monitor.controllers.app_controller import AppController
from stability_monitor.config.settings import Settings

def main():
    """Main application entry point"""
    try:
        # Initialize settings
        settings = Settings()
        
        # Create main window
        root = tk.Tk()
        root.title("IT Stability & Operations Health Monitor")
        root.geometry("1200x800")
        root.minsize(1024, 768)
        
        # Initialize application controller
        app = AppController(root, settings)
        
        # Start the application
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()