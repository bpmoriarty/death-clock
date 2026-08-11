"""Entry point for Death Clock. Uses .pyw extension to avoid console window."""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Inject .venv site-packages so the app works when double-clicked
# (double-click uses system Python, not the activated venv)
venv_site_packages = os.path.join(project_root, '.venv', 'Lib', 'site-packages')
if os.path.isdir(venv_site_packages):
    sys.path.insert(0, venv_site_packages)

from death_clock.app import DeathClockApp

if __name__ == "__main__":
    app = DeathClockApp()
    app.run()
