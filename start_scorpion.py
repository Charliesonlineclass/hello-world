#!/usr/bin/env python3
"""
SCORPION Main Entry Point
=========================

Main startup script for the SCORPION automation platform.
Initializes all services, calibrates AI babies, and monitors health.

Usage:
    python start_scorpion.py              # Full startup
    python start_scorpion.py --validate   # Check config only
    python start_scorpion.py --calibrate  # Warmup babies only
    python start_scorpion.py --dev        # Development mode
    python start_scorpion.py --status     # Show status

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import sys
import time
import signal
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "scorpion.log", mode='a')
    ]
)
logger = logging.getLogger("SCORPION")


# =============================================================================
# BANNER
# =============================================================================

BANNER = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║     ███████╗ ██████╗ ██████╗ ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗      ║
║     ██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║██╔═══██╗████╗  ██║      ║
║     ███████╗██║     ██║   ██║██████╔╝██████╔╝██║██║   ██║██╔██╗ ██║      ║
║     ╚════██║██║     ██║   ██║██╔══██╗██╔═══╝ ██║██║   ██║██║╚██╗██║      ║
║     ███████║╚██████╗╚██████╔╝██║  ██║██║     ██║╚██████╔╝██║ ╚████║      ║
║     ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝      ║
║                                                                           ║
║                    🦂  SCORPION KING v1.0.0  🦂                           ║
║                       TESTUDO Formation                                   ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

MINI_BANNER = """
🦂 SCORPION KING v1.0.0 - TESTUDO Formation
"""


# =============================================================================
# STARTUP MANAGER
# =============================================================================

class ScorpionManager:
    """
    Main manager for SCORPION startup and operation.
    """

    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode
        self.running = False
        self.startup_time = None

        # Create required directories
        self._ensure_directories()

        # Load modules lazily
        self._validator = None
        self._startup = None
        self._calibrator = None

        logger.info("ScorpionManager initialized")

    def _ensure_directories(self):
        """Ensure required directories exist."""
        dirs = ["data", "logs", "backups", "temp"]
        for d in dirs:
            (PROJECT_ROOT / d).mkdir(exist_ok=True)

    @property
    def validator(self):
        """Lazy load validator."""
        if self._validator is None:
            from engine.validator import ConfigValidator
            self._validator = ConfigValidator()
        return self._validator

    @property
    def startup(self):
        """Lazy load startup sequence."""
        if self._startup is None:
            from engine.startup import StartupSequence
            self._startup = StartupSequence()
        return self._startup

    @property
    def calibrator(self):
        """Lazy load calibrator."""
        if self._calibrator is None:
            from engine.calibrator import BabyCalibrator
            self._calibrator = BabyCalibrator()
        return self._calibrator

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def validate(self) -> bool:
        """Run full validation."""
        print("\n" + "=" * 60)
        print("  VALIDATING CONFIGURATION")
        print("=" * 60)

        report = self.validator.full_validation()

        if not report.passed:
            print("\n⚠️  Validation failed. Please fix errors before starting.")
            return False

        print("\n✅ Validation passed!")
        return True

    # -------------------------------------------------------------------------
    # Calibration
    # -------------------------------------------------------------------------

    def calibrate(self, warmup: bool = True) -> bool:
        """Calibrate and warmup AI babies."""
        print("\n" + "=" * 60)
        print("  CALIBRATING AI BABIES")
        print("=" * 60)

        # Check which babies are available
        results = self.calibrator.calibrate_all()

        online = sum(1 for r in results.values() if r.status == "pass")
        print(f"\n  Online: {online}/{len(results)} babies")

        if online == 0:
            print("\n⚠️  No babies online. Check Ollama is running.")
            return False

        if warmup:
            print("\n  Warming up babies...")
            self.calibrator.warmup_all(rounds=2)

        self.calibrator.print_report()
        return True

    # -------------------------------------------------------------------------
    # Full Startup
    # -------------------------------------------------------------------------

    def start(self) -> bool:
        """Full startup sequence."""
        print(BANNER)

        self.startup_time = datetime.now()

        # Phase 1: Validation
        print("\n📋 Phase 1: Validation")
        if not self.validate():
            return False

        # Phase 2: Start Services
        print("\n🔧 Phase 2: Starting Services")
        if not self.startup.start_services():
            print("\n❌ Service startup failed!")
            return False

        # Phase 3: Calibrate Babies
        print("\n🤖 Phase 3: Calibrating AI Babies")
        self.calibrate(warmup=True)

        # Phase 4: Ready
        self.running = True
        elapsed = (datetime.now() - self.startup_time).total_seconds()

        print("\n" + "=" * 60)
        print("  🦂 SCORPION IS READY!")
        print("=" * 60)
        print(f"  Started in: {elapsed:.1f} seconds")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        print("  Services:")
        print("    • API:      http://localhost:8080")
        print("    • Dashboard: http://localhost:8080/dashboard")
        print("    • ChromaDB: http://localhost:8000")
        print("    • n8n:      http://localhost:5678")
        print("")
        print("  Press Ctrl+C to shutdown")
        print("=" * 60 + "\n")

        return True

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    def show_status(self):
        """Show current status."""
        print(MINI_BANNER)
        self.startup.print_status()
        self.calibrator.calibrate_all()
        self.calibrator.print_report()

    # -------------------------------------------------------------------------
    # Shutdown
    # -------------------------------------------------------------------------

    def shutdown(self):
        """Graceful shutdown."""
        if not self.running:
            return

        print("\n" + "=" * 60)
        print("  🛑 SHUTTING DOWN SCORPION")
        print("=" * 60)

        self.running = False
        self.startup.graceful_shutdown()

        print("\n✅ SCORPION shutdown complete")
        print("=" * 60 + "\n")

    # -------------------------------------------------------------------------
    # Health Check Loop
    # -------------------------------------------------------------------------

    def health_check_loop(self, interval: int = 60):
        """Run periodic health checks."""
        logger.info("Starting health check loop")

        while self.running:
            try:
                time.sleep(interval)

                if not self.running:
                    break

                # Quick health check
                report = self.startup.health_check_all()

                unhealthy = [
                    name for name, status in report.items()
                    if status.get("status") not in ["running", "healthy"]
                ]

                if unhealthy:
                    logger.warning(f"Unhealthy services: {unhealthy}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")


# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

manager = None


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global manager
    print("\n\n⚡ Received shutdown signal...")
    if manager:
        manager.shutdown()
    sys.exit(0)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    global manager

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="SCORPION - Smart Coordination Of Resources, Processes, Intelligence, Operations & Networks"
    )
    parser.add_argument(
        "--dev", "-d",
        action="store_true",
        help="Development mode (more verbose)"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate configuration only"
    )
    parser.add_argument(
        "--calibrate", "-c",
        action="store_true",
        help="Calibrate babies only"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show current status"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )

    args = parser.parse_args()

    # Set log level
    if args.dev:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create manager
    manager = ScorpionManager(dev_mode=args.dev)

    # Execute requested action
    try:
        if args.validate:
            success = manager.validate()
            sys.exit(0 if success else 1)

        elif args.calibrate:
            success = manager.calibrate()
            sys.exit(0 if success else 1)

        elif args.status:
            manager.show_status()
            sys.exit(0)

        else:
            # Full startup
            if manager.start():
                # Run health check loop
                manager.health_check_loop()
            else:
                sys.exit(1)

    except KeyboardInterrupt:
        manager.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if manager:
            manager.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
