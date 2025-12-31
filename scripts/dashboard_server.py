#!/usr/bin/env python3
"""
Dashboard Server - Simple HTTP server for the SCORPION dashboard.

Usage:
    python scripts/dashboard_server.py
    python scripts/dashboard_server.py --port 9999
    python scripts/dashboard_server.py --open
"""

import argparse
import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path


DEFAULT_PORT = 8888
DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for serving the dashboard."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[Dashboard] {args[0]}")

    def do_GET(self):
        """Handle GET requests."""
        # Serve index.html for root path
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        return super().do_GET()


def find_dashboard_dir():
    """Find the dashboard directory."""
    # Try relative to this script
    script_dir = Path(__file__).parent.parent / "dashboard"
    if script_dir.exists():
        return script_dir

    # Try current working directory
    cwd_dir = Path.cwd() / "dashboard"
    if cwd_dir.exists():
        return cwd_dir

    # Try SCORPION_HOME environment variable
    scorpion_home = os.environ.get("SCORPION_HOME")
    if scorpion_home:
        env_dir = Path(scorpion_home) / "dashboard"
        if env_dir.exists():
            return env_dir

    return None


def start_server(port: int = DEFAULT_PORT, open_browser: bool = False):
    """Start the dashboard server."""
    global DASHBOARD_DIR

    dashboard_path = find_dashboard_dir()
    if not dashboard_path:
        print("Error: Dashboard directory not found!")
        print("Expected locations:")
        print(f"  - {Path(__file__).parent.parent / 'dashboard'}")
        print(f"  - {Path.cwd() / 'dashboard'}")
        print("\nMake sure the dashboard files are in place.")
        sys.exit(1)

    DASHBOARD_DIR = dashboard_path
    print(f"\nServing dashboard from: {DASHBOARD_DIR}")

    # Create a simple handler with the correct directory
    handler = lambda *args, **kwargs: DashboardHandler(*args, **kwargs)

    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"\n{'='*50}")
            print(" SCORPION Dashboard Server")
            print(f"{'='*50}")
            print(f"\n Dashboard URL: {url}")
            print(f" Serving from:  {DASHBOARD_DIR}")
            print(f"\n Press Ctrl+C to stop\n")
            print("="*50 + "\n")

            if open_browser:
                print("Opening browser...")
                webbrowser.open(url)

            httpd.serve_forever()

    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nError: Port {port} is already in use!")
            print(f"Try: python scripts/dashboard_server.py --port {port + 1}")
        else:
            raise
    except KeyboardInterrupt:
        print("\n\nDashboard server stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Start the SCORPION dashboard server"
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to serve on (default: {DEFAULT_PORT})"
    )

    parser.add_argument(
        "--open", "-o",
        action="store_true",
        help="Open dashboard in browser after starting"
    )

    parser.add_argument(
        "--dir", "-d",
        type=str,
        help="Dashboard directory path (auto-detected if not specified)"
    )

    args = parser.parse_args()

    if args.dir:
        global DASHBOARD_DIR
        DASHBOARD_DIR = Path(args.dir)
        if not DASHBOARD_DIR.exists():
            print(f"Error: Directory not found: {args.dir}")
            sys.exit(1)

    start_server(port=args.port, open_browser=args.open)


if __name__ == "__main__":
    main()
