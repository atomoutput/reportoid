#!/usr/bin/env python3
"""
GUI test for the stability monitor application - runs for 3 seconds then closes
"""

import tkinter as tk
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stability_monitor.controllers.app_controller import AppController
from stability_monitor.config.settings import Settings

def auto_close_app(root, delay=3):
    """Auto-close the application after delay seconds"""
    time.sleep(delay)
    root.quit()

def test_gui():
    """Test GUI initialization"""
    try:
        print("Testing GUI initialization...")
        
        # Initialize settings
        settings = Settings()
        
        # Create main window
        root = tk.Tk()
        root.title("IT Stability Monitor - GUI Test")
        root.geometry("1200x800")
        
        # Initialize application controller
        app = AppController(root, settings)
        
        print("✓ GUI initialized successfully!")
        print("Window will close automatically in 3 seconds...")
        
        # Start auto-close timer in separate thread
        close_thread = threading.Thread(target=auto_close_app, args=(root, 3))
        close_thread.daemon = True
        close_thread.start()
        
        # Start the GUI
        root.mainloop()
        
        print("✓ GUI test completed successfully!")
        return True
        
    except Exception as e:
        print(f"GUI test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gui()
    print("GUI components are working correctly!" if success else "GUI test failed.")
    sys.exit(0 if success else 1)