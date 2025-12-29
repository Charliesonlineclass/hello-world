"""
NSIPA Call Logger
=================

Healthcare appointment scheduling call tracking system.
Log calls, track outcomes, generate reports, and automate reminders.

Modules:
    - call_logger: Track outbound calls and outcomes
    - appointment_tracker: Manage scheduled appointments

Usage:
    from nsipa import CallLogger, AppointmentTracker

    # Log calls
    logger = CallLogger()
    logger.log_call("John Doe", "scheduled", "Booked for Monday 10am")

    # Track appointments
    tracker = AppointmentTracker()
    tracker.track_appointment("John Doe", "2024-01-15 10:00", "Dr. Smith")

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .call_logger import (
    CallLogger,
    CALL_OUTCOMES,
    log_call,
    get_daily_stats,
    export_calls
)

from .appointment_tracker import (
    AppointmentTracker,
    Appointment,
    track_appointment,
    send_reminder,
    confirm_appointment
)

__version__ = "1.0.0"
__codename__ = "TESTUDO"
__all__ = [
    'CallLogger',
    'CALL_OUTCOMES',
    'log_call',
    'get_daily_stats',
    'export_calls',
    'AppointmentTracker',
    'Appointment',
    'track_appointment',
    'send_reminder',
    'confirm_appointment'
]
