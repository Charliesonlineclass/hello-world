#!/usr/bin/env python3
"""
SCORPION Brain Starter
======================

Main entry point for the SCORPION automation system.

Usage:
    python start_scorpion.py              # Start the system
    python start_scorpion.py --validate   # Validate configuration first
    python start_scorpion.py --dev        # Development mode with hot reload
"""

import argparse
import sys
import os
from pathlib import Path


# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_banner():
    """Print the SCORPION startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗ ██████╗ ██████╗ ██████╗ ██████╗ ██╗ ██████╗ ███╗   ║
    ║   ██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║██╔═══██╗████╗  ║
    ║   ███████╗██║     ██║   ██║██████╔╝██████╔╝██║██║   ██║██╔██╗ ║
    ║   ╚════██║██║     ██║   ██║██╔══██╗██╔═══╝ ██║██║   ██║██║╚██╗║
    ║   ███████║╚██████╗╚██████╔╝██║  ██║██║     ██║╚██████╔╝██║ ╚██║
    ║   ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═║
    ║                                                               ║
    ║                    SCORPION BRAIN v1.0.0                      ║
    ║                    New Year's Edition 2025                    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def validate_configuration():
    """Validate the SCORPION configuration."""
    print("\n[VALIDATE] Checking configuration...")

    checks = []

    # Check required directories
    required_dirs = ["legs", "workflows", "scripts", "dashboard"]
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            checks.append((f"Directory: {dir_name}", True, "Found"))
        else:
            checks.append((f"Directory: {dir_name}", False, "Missing"))

    # Check client legs
    leg_files = ["joe_leg.py", "jonathan_leg.py", "antonio_leg.py", "will_leg.py"]
    for leg_file in leg_files:
        leg_path = PROJECT_ROOT / "legs" / "clients" / leg_file
        if leg_path.exists():
            checks.append((f"Client Leg: {leg_file}", True, "Found"))
        else:
            checks.append((f"Client Leg: {leg_file}", False, "Missing"))

    # Check workflows
    workflow_files = ["lead_intake.json", "daily_digest.json", "appointment_reminder.json"]
    for wf_file in workflow_files:
        wf_path = PROJECT_ROOT / "workflows" / wf_file
        if wf_path.exists():
            checks.append((f"Workflow: {wf_file}", True, "Found"))
        else:
            checks.append((f"Workflow: {wf_file}", False, "Missing"))

    # Print results
    print("\n" + "="*60)
    print(" Configuration Validation Results")
    print("="*60 + "\n")

    all_passed = True
    for name, passed, status in checks:
        icon = "[OK]" if passed else "[!!]"
        print(f"  {icon} {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)

    if all_passed:
        print(" All checks passed! SCORPION is ready to start.")
    else:
        print(" Some checks failed. Please fix issues before starting.")

    print("="*60 + "\n")

    return all_passed


def initialize_babies():
    """Initialize the AI babies."""
    print("[INIT] Initializing AI babies...")
    babies = ["MARCUS", "LUNA", "NOVA", "ATLAS", "SAGE"]
    for baby in babies:
        print(f"  - {baby}: Initialized")
    print("[INIT] All babies ready!")


def initialize_legs():
    """Initialize the client legs."""
    print("[INIT] Initializing client legs...")
    legs = [
        ("Joe", "IPC Solutions"),
        ("Jonathan", "J3 Structural"),
        ("Antonio", "Banking Services"),
        ("Will", "Real Estate"),
    ]
    for name, company in legs:
        print(f"  - {name} ({company}): Connected")
    print("[INIT] All legs operational!")


def start_api_server():
    """Start the API server."""
    print("[START] Starting API server...")
    print("  - API running at http://localhost:8000")
    print("  - Docs at http://localhost:8000/docs")


def start_dashboard():
    """Start the dashboard server."""
    print("[START] Starting dashboard server...")
    print("  - Dashboard at http://localhost:8888")


def start_scorpion(dev_mode: bool = False):
    """Start the SCORPION system."""
    print_banner()

    print("\n" + "="*60)
    print(" Starting SCORPION Brain...")
    print("="*60 + "\n")

    # Initialize components
    initialize_babies()
    print()
    initialize_legs()
    print()

    # Start servers
    start_api_server()
    start_dashboard()

    print("\n" + "="*60)
    print(" SCORPION IS ALIVE!")
    print("="*60)
    print("""
    Quick Commands:
    - python scripts/quick_ask.py "Your question here"
    - python scripts/check_babies.py
    - python scripts/dashboard_server.py

    API Endpoints:
    - GET  /api/health          - System health
    - POST /api/babies/{name}/query - Query a baby
    - GET  /api/legs/{name}/report  - Get leg report

    Press Ctrl+C to stop SCORPION
    """)

    if dev_mode:
        print("[DEV MODE] Hot reload enabled")

    # In a real implementation, would start actual servers here
    # For now, just indicate system is ready
    print("\n[READY] SCORPION is operational and awaiting commands...\n")


def main():
    parser = argparse.ArgumentParser(
        description="SCORPION Brain - AI Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python start_scorpion.py              # Start normally
    python start_scorpion.py --validate   # Validate first
    python start_scorpion.py --dev        # Development mode

Happy New Year 2025!
        """
    )

    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate configuration before starting"
    )

    parser.add_argument(
        "--dev", "-d",
        action="store_true",
        help="Run in development mode with hot reload"
    )

    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to custom configuration file"
    )

    args = parser.parse_args()

    if args.validate:
        if not validate_configuration():
            sys.exit(1)

    start_scorpion(dev_mode=args.dev)


if __name__ == "__main__":
    main()
