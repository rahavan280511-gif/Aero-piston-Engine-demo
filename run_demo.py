"""
Launcher script for UAV Aero-Piston Engine Digital Twin Demo.

Launches FastAPI backend (port 8000) and Streamlit dashboard (port 8501)
together in sub-processes and opens the dashboard in your default browser.

Usage:
    python run_demo.py
"""

import sys
import time
import subprocess
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def main():
    print("=" * 65)
    print("  UAV Aero-Piston Engine Digital Twin Demo Launcher")
    print("=" * 65)

    # 1. Start FastAPI backend
    print("\n[1/3] Starting FastAPI Backend on http://localhost:8000...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(PROJECT_ROOT))
    time.sleep(2.5)

    # 2. Start Streamlit dashboard
    print("\n[2/3] Starting Streamlit Dashboard on http://localhost:8501...")
    dashboard_cmd = [
        sys.executable, "-m", "streamlit", "run", "dashboard/app.py",
        "--server.port", "8501",
        "--server.headless", "true"
    ]
    dashboard_proc = subprocess.Popen(dashboard_cmd, cwd=str(PROJECT_ROOT))
    time.sleep(2.5)

    # 3. Open browser
    print("\n[3/3] Opening Digital Twin Dashboard in browser...")
    webbrowser.open("http://localhost:8501")

    print("\n" + "=" * 65)
    print("  Demo is running!")
    print("  - Streamlit Dashboard: http://localhost:8501")
    print("  - FastAPI OpenAPI Docs: http://localhost:8000/docs")
    print("  Press Ctrl+C in this terminal to stop both servers.")
    print("=" * 65 + "\n")

    try:
        backend_proc.wait()
        dashboard_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_proc.terminate()
        dashboard_proc.terminate()
        print("[OK] Demo stopped.")


if __name__ == "__main__":
    main()
