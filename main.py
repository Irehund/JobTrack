"""
JobTrack — Main Entry Point
============================
Launches the JobTrack desktop application.

Run this file to start the app:
    python main.py

On first run, the setup wizard will appear automatically.
Subsequent runs go directly to the main window.
"""

import sys
import os

# Ensure the project root is on the path when running via PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from ui.app import JobTrackApp


def main():
    """Initialize and run the JobTrack application."""
    app = JobTrackApp()
    app.mainloop()


if __name__ == "__main__":
    main()
