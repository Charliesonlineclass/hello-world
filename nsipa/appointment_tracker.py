"""
NSIPA Appointment Tracker
=========================

Track scheduled appointments, send reminders, and manage confirmations.

No external dependencies required - uses built-in Python libraries.
For SMS/email reminders, configure SMTP/Twilio credentials.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Union
from dataclasses import dataclass, asdict, field
import logging
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NSIPA.appointment_tracker")

# Appointment statuses
APPOINTMENT_STATUSES = [
    "scheduled",    # Appointment confirmed
    "pending",      # Awaiting confirmation
    "confirmed",    # Patient confirmed
    "reminded",     # Reminder sent
    "checked_in",   # Patient arrived
    "completed",    # Appointment completed
    "no_show",      # Patient didn't show
    "cancelled",    # Cancelled
    "rescheduled"   # Rescheduled to different time
]


@dataclass
class Appointment:
    """Appointment data structure."""
    id: str
    patient_name: str
    patient_phone: str
    patient_email: str
    appointment_datetime: str
    provider: str
    appointment_type: str
    status: str = "scheduled"
    notes: str = ""
    reminder_sent: bool = False
    reminder_sent_at: Optional[str] = None
    confirmed: bool = False
    confirmed_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @property
    def datetime(self) -> datetime:
        """Get appointment as datetime object."""
        return datetime.fromisoformat(self.appointment_datetime)

    @property
    def is_today(self) -> bool:
        """Check if appointment is today."""
        return self.datetime.date() == date.today()

    @property
    def is_upcoming(self) -> bool:
        """Check if appointment is in the future."""
        return self.datetime > datetime.now()


class AppointmentTracker:
    """
    Track and manage scheduled appointments.

    Usage:
        tracker = AppointmentTracker()
        appt_id = tracker.track_appointment(
            "John Doe", "2024-01-15 10:00",
            "Dr. Smith", "555-1234", "john@email.com"
        )
        tracker.send_reminder(appt_id, hours_before=24)
    """

    def __init__(self, data_dir: str = "appointments"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.appointments_file = self.data_dir / "appointments.json"
        self._appointments: Dict[str, Appointment] = {}
        self._counter = 0

        self._load_data()

    def _load_data(self):
        """Load appointments from file."""
        if self.appointments_file.exists():
            try:
                data = json.loads(self.appointments_file.read_text())
                for appt_data in data:
                    appt = Appointment(**appt_data)
                    self._appointments[appt.id] = appt
                logger.info(f"Loaded {len(self._appointments)} appointments")
            except Exception as e:
                logger.error(f"Error loading appointments: {e}")

    def _save_data(self):
        """Save appointments to file."""
        data = [asdict(a) for a in self._appointments.values()]
        self.appointments_file.write_text(json.dumps(data, indent=2))

    def _generate_id(self) -> str:
        """Generate unique appointment ID."""
        self._counter += 1
        return f"APT-{date.today().strftime('%Y%m%d')}-{self._counter:04d}"

    def track_appointment(
        self,
        patient_name: str,
        appointment_datetime: Union[str, datetime],
        provider: str,
        patient_phone: str = "",
        patient_email: str = "",
        appointment_type: str = "General",
        notes: str = ""
    ) -> str:
        """
        Track a new appointment.

        Args:
            patient_name: Patient's name
            appointment_datetime: Appointment date/time
            provider: Provider/doctor name
            patient_phone: Patient's phone
            patient_email: Patient's email
            appointment_type: Type of appointment
            notes: Additional notes

        Returns:
            Appointment ID
        """
        if isinstance(appointment_datetime, datetime):
            appointment_datetime = appointment_datetime.isoformat()

        appt_id = self._generate_id()

        appointment = Appointment(
            id=appt_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_email=patient_email,
            appointment_datetime=appointment_datetime,
            provider=provider,
            appointment_type=appointment_type,
            notes=notes
        )

        self._appointments[appt_id] = appointment
        self._save_data()

        logger.info(f"Appointment tracked: {patient_name} with {provider}")
        return appt_id

    def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID."""
        return self._appointments.get(appointment_id)

    def update_appointment(self, appointment_id: str, **kwargs) -> bool:
        """Update appointment fields."""
        appt = self._appointments.get(appointment_id)
        if not appt:
            return False

        for key, value in kwargs.items():
            if hasattr(appt, key):
                setattr(appt, key, value)

        appt.updated_at = datetime.now().isoformat()
        self._save_data()
        return True

    def send_reminder(
        self,
        appointment_id: str,
        hours_before: int = 24,
        method: str = 'both'  # 'sms', 'email', 'both'
    ) -> Dict:
        """
        Send appointment reminder.

        Args:
            appointment_id: Appointment ID
            hours_before: Hours before appointment (for message)
            method: 'sms', 'email', or 'both'

        Returns:
            Result dictionary
        """
        appt = self._appointments.get(appointment_id)
        if not appt:
            return {'success': False, 'error': 'Appointment not found'}

        result = {
            'appointment_id': appointment_id,
            'email_sent': False,
            'sms_sent': False
        }

        # Format appointment time
        appt_dt = appt.datetime
        formatted_date = appt_dt.strftime("%A, %B %d, %Y")
        formatted_time = appt_dt.strftime("%I:%M %p")

        # SMS message
        sms_message = (
            f"Reminder: {appt.patient_name}, you have an appointment with "
            f"{appt.provider} on {formatted_date} at {formatted_time}. "
            f"Reply CONFIRM to confirm or call to reschedule."
        )

        # Email message
        email_subject = f"Appointment Reminder - {formatted_date}"
        email_body = f"""Dear {appt.patient_name},

This is a friendly reminder of your upcoming appointment:

📅 Date: {formatted_date}
⏰ Time: {formatted_time}
👨‍⚕️ Provider: {appt.provider}
📋 Type: {appt.appointment_type}

Please arrive 15 minutes early to complete any necessary paperwork.

If you need to reschedule or cancel, please call us as soon as possible.

Thank you!
"""

        # Send based on method
        if method in ('email', 'both') and appt.patient_email:
            result['email_sent'] = self._send_email(
                appt.patient_email, email_subject, email_body
            )

        if method in ('sms', 'both') and appt.patient_phone:
            result['sms_sent'] = self._send_sms(appt.patient_phone, sms_message)

        # Update appointment
        if result['email_sent'] or result['sms_sent']:
            appt.reminder_sent = True
            appt.reminder_sent_at = datetime.now().isoformat()
            appt.status = "reminded"
            appt.updated_at = datetime.now().isoformat()
            self._save_data()

        return result

    def _send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email (requires SMTP configuration)."""
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USERNAME', '')
        smtp_pass = os.environ.get('SMTP_PASSWORD', '')
        smtp_from = os.environ.get('SMTP_FROM', smtp_user)

        if not smtp_user or not smtp_pass:
            logger.warning("SMTP not configured, email not sent")
            return False

        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = smtp_from
            msg['To'] = to

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to], msg.as_string())

            logger.info(f"Email sent to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _send_sms(self, to: str, message: str) -> bool:
        """Send SMS via Twilio (requires configuration)."""
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        from_number = os.environ.get('TWILIO_FROM_NUMBER', '')

        if not account_sid or not auth_token:
            logger.warning("Twilio not configured, SMS not sent")
            return False

        try:
            from twilio.rest import Client

            if not to.startswith('+'):
                to = '+1' + to.replace('-', '').replace(' ', '')

            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message,
                from_=from_number,
                to=to
            )

            logger.info(f"SMS sent to {to}")
            return True

        except ImportError:
            logger.error("Twilio not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def confirm_appointment(self, appointment_id: str) -> bool:
        """Mark appointment as confirmed by patient."""
        appt = self._appointments.get(appointment_id)
        if not appt:
            return False

        appt.confirmed = True
        appt.confirmed_at = datetime.now().isoformat()
        appt.status = "confirmed"
        appt.updated_at = datetime.now().isoformat()
        self._save_data()

        logger.info(f"Appointment {appointment_id} confirmed")
        return True

    def reschedule(
        self,
        appointment_id: str,
        new_datetime: Union[str, datetime]
    ) -> bool:
        """Reschedule appointment to new time."""
        appt = self._appointments.get(appointment_id)
        if not appt:
            return False

        if isinstance(new_datetime, datetime):
            new_datetime = new_datetime.isoformat()

        old_datetime = appt.appointment_datetime
        appt.appointment_datetime = new_datetime
        appt.status = "rescheduled"
        appt.reminder_sent = False  # Need new reminder
        appt.confirmed = False
        appt.notes += f"\nRescheduled from {old_datetime}"
        appt.updated_at = datetime.now().isoformat()
        self._save_data()

        logger.info(f"Appointment {appointment_id} rescheduled to {new_datetime}")
        return True

    def mark_no_show(self, appointment_id: str) -> bool:
        """Mark appointment as no-show."""
        return self.update_appointment(appointment_id, status="no_show")

    def mark_completed(self, appointment_id: str) -> bool:
        """Mark appointment as completed."""
        return self.update_appointment(appointment_id, status="completed")

    def cancel_appointment(self, appointment_id: str, reason: str = "") -> bool:
        """Cancel an appointment."""
        appt = self._appointments.get(appointment_id)
        if not appt:
            return False

        appt.status = "cancelled"
        if reason:
            appt.notes += f"\nCancelled: {reason}"
        appt.updated_at = datetime.now().isoformat()
        self._save_data()

        logger.info(f"Appointment {appointment_id} cancelled")
        return True

    def get_todays_appointments(self) -> List[Appointment]:
        """Get all appointments for today."""
        today = date.today()
        return [
            a for a in self._appointments.values()
            if a.datetime.date() == today and a.status not in ('cancelled', 'rescheduled')
        ]

    def get_upcoming_appointments(
        self,
        days: int = 7,
        provider: Optional[str] = None
    ) -> List[Appointment]:
        """Get upcoming appointments."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)

        appointments = [
            a for a in self._appointments.values()
            if now <= a.datetime <= cutoff and a.status not in ('cancelled', 'rescheduled')
        ]

        if provider:
            appointments = [a for a in appointments if a.provider == provider]

        return sorted(appointments, key=lambda a: a.datetime)

    def get_needing_reminder(self, hours_before: int = 24) -> List[Appointment]:
        """Get appointments needing reminder."""
        target_time = datetime.now() + timedelta(hours=hours_before)

        return [
            a for a in self._appointments.values()
            if (not a.reminder_sent and
                a.status not in ('cancelled', 'rescheduled', 'completed') and
                datetime.now() < a.datetime <= target_time)
        ]

    def get_unconfirmed(self) -> List[Appointment]:
        """Get appointments not yet confirmed."""
        now = datetime.now()
        return [
            a for a in self._appointments.values()
            if (not a.confirmed and
                a.status not in ('cancelled', 'rescheduled', 'completed') and
                a.datetime > now)
        ]

    def daily_schedule(
        self,
        target_date: Optional[Union[str, date]] = None,
        provider: Optional[str] = None
    ) -> List[Appointment]:
        """
        Get daily schedule.

        Args:
            target_date: Date to get schedule for
            provider: Filter by provider

        Returns:
            List of appointments sorted by time
        """
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        appointments = [
            a for a in self._appointments.values()
            if a.datetime.date() == target_date and a.status not in ('cancelled', 'rescheduled')
        ]

        if provider:
            appointments = [a for a in appointments if a.provider == provider]

        return sorted(appointments, key=lambda a: a.datetime)

    def print_daily_schedule(
        self,
        target_date: Optional[Union[str, date]] = None,
        provider: Optional[str] = None
    ):
        """Print formatted daily schedule."""
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        appointments = self.daily_schedule(target_date, provider)

        print("\n" + "=" * 60)
        print(f"SCHEDULE FOR {target_date.strftime('%A, %B %d, %Y')}")
        if provider:
            print(f"Provider: {provider}")
        print("=" * 60)

        if not appointments:
            print("No appointments scheduled.")
        else:
            for appt in appointments:
                time_str = appt.datetime.strftime("%I:%M %p")
                status_icon = {
                    'confirmed': '✓',
                    'reminded': '📧',
                    'scheduled': '📅',
                    'no_show': '✗'
                }.get(appt.status, ' ')

                print(f"{time_str} [{status_icon}] {appt.patient_name}")
                print(f"         Provider: {appt.provider}")
                print(f"         Type: {appt.appointment_type}")
                if appt.notes:
                    print(f"         Notes: {appt.notes[:50]}")
                print()

        print("=" * 60 + "\n")

    def get_stats(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None
    ) -> Dict:
        """Get appointment statistics."""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        if end_date is None:
            end_date = date.today()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        appointments = [
            a for a in self._appointments.values()
            if start_date <= a.datetime.date() <= end_date
        ]

        total = len(appointments)
        by_status = {}
        by_provider = {}

        for appt in appointments:
            by_status[appt.status] = by_status.get(appt.status, 0) + 1
            by_provider[appt.provider] = by_provider.get(appt.provider, 0) + 1

        completed = by_status.get('completed', 0)
        no_shows = by_status.get('no_show', 0)
        cancelled = by_status.get('cancelled', 0)

        show_rate = ((completed) / (completed + no_shows) * 100) if (completed + no_shows) > 0 else 0

        return {
            'date_range': f"{start_date} to {end_date}",
            'total_appointments': total,
            'by_status': by_status,
            'by_provider': by_provider,
            'completed': completed,
            'no_shows': no_shows,
            'cancelled': cancelled,
            'show_rate': round(show_rate, 1)
        }


# Convenience functions
_default_tracker: Optional[AppointmentTracker] = None


def track_appointment(
    patient_name: str,
    appointment_datetime: Union[str, datetime],
    provider: str,
    **kwargs
) -> str:
    """Track appointment using default tracker."""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = AppointmentTracker()
    return _default_tracker.track_appointment(
        patient_name, appointment_datetime, provider, **kwargs
    )


def send_reminder(appointment_id: str, **kwargs) -> Dict:
    """Send reminder using default tracker."""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = AppointmentTracker()
    return _default_tracker.send_reminder(appointment_id, **kwargs)


def confirm_appointment(appointment_id: str) -> bool:
    """Confirm appointment using default tracker."""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = AppointmentTracker()
    return _default_tracker.confirm_appointment(appointment_id)


if __name__ == "__main__":
    # Demo usage
    print("NSIPA Appointment Tracker - Demo")
    print("=" * 40)

    tracker = AppointmentTracker()

    # Add sample appointments
    tomorrow = datetime.now() + timedelta(days=1)

    appt1 = tracker.track_appointment(
        patient_name="John Smith",
        appointment_datetime=tomorrow.replace(hour=9, minute=0),
        provider="Dr. Johnson",
        patient_phone="555-1234",
        patient_email="john@example.com",
        appointment_type="Annual Physical"
    )

    appt2 = tracker.track_appointment(
        patient_name="Jane Doe",
        appointment_datetime=tomorrow.replace(hour=10, minute=30),
        provider="Dr. Johnson",
        patient_phone="555-5678",
        patient_email="jane@example.com",
        appointment_type="Follow-up"
    )

    appt3 = tracker.track_appointment(
        patient_name="Bob Wilson",
        appointment_datetime=tomorrow.replace(hour=14, minute=0),
        provider="Dr. Smith",
        patient_phone="555-9999",
        appointment_type="New Patient"
    )

    # Confirm one appointment
    tracker.confirm_appointment(appt1)

    # Print tomorrow's schedule
    tracker.print_daily_schedule(tomorrow.date())

    # Get needing reminder
    print("\nAppointments needing reminder:")
    for appt in tracker.get_needing_reminder(hours_before=48):
        print(f"  • {appt.patient_name} - {appt.datetime}")

    # Print stats
    print("\nStatistics:")
    stats = tracker.get_stats()
    print(f"  Total: {stats['total_appointments']}")
    print(f"  By Status: {stats['by_status']}")
