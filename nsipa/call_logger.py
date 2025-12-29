"""
NSIPA Call Logger
=================

Track outbound scheduling calls for healthcare appointments.
Log outcomes, calculate conversion rates, and generate reports.

No external dependencies required - uses built-in Python libraries.
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Union, Tuple
from dataclasses import dataclass, asdict, field
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NSIPA.call_logger")

# Call outcome types
CALL_OUTCOMES = {
    "scheduled": {
        "label": "Scheduled",
        "description": "Appointment successfully scheduled",
        "is_success": True,
        "color": "green"
    },
    "voicemail": {
        "label": "Left Voicemail",
        "description": "Left voicemail message",
        "is_success": False,
        "color": "yellow"
    },
    "no_answer": {
        "label": "No Answer",
        "description": "No answer, no voicemail",
        "is_success": False,
        "color": "orange"
    },
    "declined": {
        "label": "Declined",
        "description": "Patient declined appointment",
        "is_success": False,
        "color": "red"
    },
    "callback": {
        "label": "Callback Requested",
        "description": "Patient requested callback at specific time",
        "is_success": False,
        "color": "blue"
    },
    "wrong_number": {
        "label": "Wrong Number",
        "description": "Number is incorrect or disconnected",
        "is_success": False,
        "color": "gray"
    },
    "busy": {
        "label": "Busy",
        "description": "Line was busy",
        "is_success": False,
        "color": "orange"
    },
    "rescheduled": {
        "label": "Rescheduled",
        "description": "Existing appointment rescheduled",
        "is_success": True,
        "color": "green"
    },
    "cancelled": {
        "label": "Cancelled",
        "description": "Appointment cancelled",
        "is_success": False,
        "color": "red"
    }
}


@dataclass
class CallRecord:
    """Single call record."""
    id: str
    patient_name: str
    patient_phone: str
    outcome: str
    notes: str
    duration_seconds: int
    caller_id: str
    call_time: str
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    provider: Optional[str] = None
    callback_time: Optional[str] = None
    attempt_number: int = 1
    campaign: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class CallLogger:
    """
    Track and analyze scheduling calls.

    Usage:
        logger = CallLogger()
        logger.log_call("John Doe", "555-1234", "scheduled",
                       notes="Booked Monday 10am with Dr. Smith")
        stats = logger.daily_summary()
    """

    def __init__(
        self,
        data_dir: str = "call_logs",
        caller_id: str = "default"
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.caller_id = caller_id

        self._calls: List[CallRecord] = []
        self._call_counter = 0

        self._load_data()

    def _get_today_file(self) -> Path:
        """Get today's log file path."""
        today = date.today().strftime("%Y-%m-%d")
        return self.data_dir / f"calls_{today}.json"

    def _load_data(self):
        """Load today's calls."""
        today_file = self._get_today_file()
        if today_file.exists():
            try:
                data = json.loads(today_file.read_text())
                self._calls = [CallRecord(**call) for call in data]
                self._call_counter = len(self._calls)
                logger.info(f"Loaded {len(self._calls)} calls for today")
            except Exception as e:
                logger.error(f"Error loading calls: {e}")
                self._calls = []

    def _save_data(self):
        """Save calls to today's file."""
        today_file = self._get_today_file()
        data = [asdict(call) for call in self._calls]
        today_file.write_text(json.dumps(data, indent=2))

    def log_call(
        self,
        patient_name: str,
        patient_phone: str,
        outcome: str,
        notes: str = "",
        duration_seconds: int = 0,
        appointment_date: Optional[str] = None,
        appointment_time: Optional[str] = None,
        provider: Optional[str] = None,
        callback_time: Optional[str] = None,
        campaign: str = ""
    ) -> CallRecord:
        """
        Log a call.

        Args:
            patient_name: Patient's name
            patient_phone: Phone number called
            outcome: Call outcome (scheduled, voicemail, no_answer, etc.)
            notes: Call notes
            duration_seconds: Call duration in seconds
            appointment_date: Scheduled appointment date (if applicable)
            appointment_time: Scheduled appointment time (if applicable)
            provider: Provider/doctor (if applicable)
            callback_time: Requested callback time (if applicable)
            campaign: Campaign identifier

        Returns:
            CallRecord object
        """
        if outcome not in CALL_OUTCOMES:
            logger.warning(f"Unknown outcome '{outcome}', using 'no_answer'")
            outcome = "no_answer"

        self._call_counter += 1
        call_id = f"{date.today().strftime('%Y%m%d')}-{self._call_counter:04d}"

        # Determine attempt number for this patient
        attempt = sum(1 for c in self._calls
                     if c.patient_phone == patient_phone) + 1

        record = CallRecord(
            id=call_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            outcome=outcome,
            notes=notes,
            duration_seconds=duration_seconds,
            caller_id=self.caller_id,
            call_time=datetime.now().strftime("%H:%M:%S"),
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            provider=provider,
            callback_time=callback_time,
            attempt_number=attempt,
            campaign=campaign
        )

        self._calls.append(record)
        self._save_data()

        outcome_info = CALL_OUTCOMES[outcome]
        logger.info(f"Call logged: {patient_name} - {outcome_info['label']}")

        return record

    def get_calls(
        self,
        outcome: Optional[str] = None,
        campaign: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> List[CallRecord]:
        """
        Get calls with optional filtering.

        Args:
            outcome: Filter by outcome
            campaign: Filter by campaign
            date_str: Get calls from specific date (YYYY-MM-DD)

        Returns:
            List of CallRecord objects
        """
        if date_str and date_str != date.today().strftime("%Y-%m-%d"):
            # Load from specific date file
            file_path = self.data_dir / f"calls_{date_str}.json"
            if file_path.exists():
                data = json.loads(file_path.read_text())
                calls = [CallRecord(**call) for call in data]
            else:
                calls = []
        else:
            calls = self._calls.copy()

        if outcome:
            calls = [c for c in calls if c.outcome == outcome]

        if campaign:
            calls = [c for c in calls if c.campaign == campaign]

        return calls

    def calculate_stats(
        self,
        calls: Optional[List[CallRecord]] = None
    ) -> Dict:
        """
        Calculate call statistics.

        Args:
            calls: Calls to analyze (defaults to today's calls)

        Returns:
            Statistics dictionary
        """
        if calls is None:
            calls = self._calls

        if not calls:
            return {
                "total_calls": 0,
                "scheduled": 0,
                "conversion_rate": 0.0,
                "outcomes": {},
                "avg_duration": 0,
                "total_duration": 0,
                "calls_per_appointment": 0
            }

        # Count outcomes
        outcomes = defaultdict(int)
        for call in calls:
            outcomes[call.outcome] += 1

        # Calculate metrics
        total = len(calls)
        scheduled = outcomes.get("scheduled", 0) + outcomes.get("rescheduled", 0)
        conversion_rate = (scheduled / total * 100) if total > 0 else 0

        total_duration = sum(c.duration_seconds for c in calls)
        avg_duration = total_duration / total if total > 0 else 0

        calls_per_appt = total / scheduled if scheduled > 0 else 0

        return {
            "total_calls": total,
            "scheduled": scheduled,
            "conversion_rate": round(conversion_rate, 1),
            "outcomes": dict(outcomes),
            "avg_duration_seconds": round(avg_duration, 1),
            "total_duration_seconds": total_duration,
            "calls_per_appointment": round(calls_per_appt, 1)
        }

    def daily_summary(self, date_str: Optional[str] = None) -> Dict:
        """
        Generate end-of-day summary.

        Args:
            date_str: Date to summarize (defaults to today)

        Returns:
            Summary dictionary
        """
        if date_str:
            calls = self.get_calls(date_str=date_str)
        else:
            calls = self._calls

        stats = self.calculate_stats(calls)

        # Add time-based analysis
        if calls:
            call_times = [datetime.strptime(c.call_time, "%H:%M:%S") for c in calls]
            first_call = min(call_times).strftime("%H:%M")
            last_call = max(call_times).strftime("%H:%M")
        else:
            first_call = "N/A"
            last_call = "N/A"

        # Callbacks needed
        callbacks = [c for c in calls if c.outcome == "callback"]

        summary = {
            **stats,
            "date": date_str or date.today().strftime("%Y-%m-%d"),
            "caller_id": self.caller_id,
            "first_call": first_call,
            "last_call": last_call,
            "callbacks_pending": len(callbacks),
            "callbacks": [
                {
                    "patient": c.patient_name,
                    "phone": c.patient_phone,
                    "callback_time": c.callback_time,
                    "notes": c.notes
                }
                for c in callbacks
            ]
        }

        return summary

    def print_summary(self, date_str: Optional[str] = None):
        """Print formatted daily summary."""
        summary = self.daily_summary(date_str)

        print("\n" + "=" * 60)
        print(f"CALL LOG SUMMARY - {summary['date']}")
        print("=" * 60)
        print(f"Caller: {summary['caller_id']}")
        print(f"Time Range: {summary['first_call']} - {summary['last_call']}")
        print("-" * 60)
        print(f"Total Calls: {summary['total_calls']}")
        print(f"Appointments Scheduled: {summary['scheduled']}")
        print(f"Conversion Rate: {summary['conversion_rate']}%")
        print(f"Calls per Appointment: {summary['calls_per_appointment']}")
        print("-" * 60)
        print("OUTCOMES:")
        for outcome, count in summary['outcomes'].items():
            label = CALL_OUTCOMES.get(outcome, {}).get('label', outcome)
            pct = (count / summary['total_calls'] * 100) if summary['total_calls'] > 0 else 0
            print(f"  {label}: {count} ({pct:.1f}%)")

        if summary['callbacks_pending'] > 0:
            print("-" * 60)
            print(f"CALLBACKS PENDING ({summary['callbacks_pending']}):")
            for cb in summary['callbacks']:
                print(f"  • {cb['patient']} - {cb['phone']}")
                if cb['callback_time']:
                    print(f"    Requested time: {cb['callback_time']}")

        print("=" * 60 + "\n")

    def export_to_csv(
        self,
        output_path: Optional[Union[str, Path]] = None,
        date_range: Optional[Tuple[str, str]] = None
    ) -> Path:
        """
        Export calls to CSV file.

        Args:
            output_path: Output file path
            date_range: Optional (start_date, end_date) tuple

        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"calls_export_{timestamp}.csv"

        output_path = Path(output_path)

        # Collect calls
        all_calls = []

        if date_range:
            start = datetime.strptime(date_range[0], "%Y-%m-%d").date()
            end = datetime.strptime(date_range[1], "%Y-%m-%d").date()
            current = start
            while current <= end:
                date_str = current.strftime("%Y-%m-%d")
                all_calls.extend(self.get_calls(date_str=date_str))
                current += timedelta(days=1)
        else:
            all_calls = self._calls.copy()

        # Write CSV
        headers = [
            "ID", "Date", "Time", "Patient Name", "Phone", "Outcome",
            "Duration (s)", "Appointment Date", "Appointment Time",
            "Provider", "Attempt #", "Campaign", "Notes"
        ]

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for call in all_calls:
                writer.writerow([
                    call.id,
                    call.created_at[:10],
                    call.call_time,
                    call.patient_name,
                    call.patient_phone,
                    CALL_OUTCOMES.get(call.outcome, {}).get('label', call.outcome),
                    call.duration_seconds,
                    call.appointment_date or "",
                    call.appointment_time or "",
                    call.provider or "",
                    call.attempt_number,
                    call.campaign,
                    call.notes
                ])

        logger.info(f"Exported {len(all_calls)} calls to {output_path}")
        return output_path

    def export_to_excel(
        self,
        output_path: Optional[Union[str, Path]] = None,
        date_range: Optional[Tuple[str, str]] = None
    ) -> Path:
        """
        Export calls to Excel-compatible CSV with summary sheet.

        Args:
            output_path: Output file path
            date_range: Optional date range

        Returns:
            Path to exported file
        """
        # First export to CSV
        csv_path = self.export_to_csv(output_path, date_range)

        # Create summary file
        summary_path = csv_path.parent / f"{csv_path.stem}_summary.csv"

        # Collect stats by date
        if date_range:
            start = datetime.strptime(date_range[0], "%Y-%m-%d").date()
            end = datetime.strptime(date_range[1], "%Y-%m-%d").date()
        else:
            start = end = date.today()

        daily_stats = []
        current = start

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            calls = self.get_calls(date_str=date_str)
            stats = self.calculate_stats(calls)
            stats['date'] = date_str
            daily_stats.append(stats)
            current += timedelta(days=1)

        # Write summary
        with open(summary_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Date", "Total Calls", "Scheduled", "Conversion Rate",
                "Avg Duration (s)", "Calls per Appointment"
            ])

            for stats in daily_stats:
                writer.writerow([
                    stats['date'],
                    stats['total_calls'],
                    stats['scheduled'],
                    f"{stats['conversion_rate']}%",
                    stats['avg_duration_seconds'],
                    stats['calls_per_appointment']
                ])

        logger.info(f"Summary exported to {summary_path}")
        return csv_path

    def get_callbacks_due(self) -> List[CallRecord]:
        """Get callbacks that are due now or overdue."""
        now = datetime.now()
        due_callbacks = []

        for call in self._calls:
            if call.outcome == "callback" and call.callback_time:
                try:
                    callback_dt = datetime.strptime(
                        f"{date.today()} {call.callback_time}",
                        "%Y-%m-%d %H:%M"
                    )
                    if callback_dt <= now:
                        due_callbacks.append(call)
                except:
                    # If can't parse time, include it
                    due_callbacks.append(call)

        return due_callbacks

    def get_retry_list(self, max_attempts: int = 3) -> List[Dict]:
        """
        Get list of patients to retry calling.

        Args:
            max_attempts: Maximum attempts before giving up

        Returns:
            List of patients needing retry
        """
        # Group by phone number
        by_phone = defaultdict(list)
        for call in self._calls:
            by_phone[call.patient_phone].append(call)

        retry_list = []
        for phone, calls in by_phone.items():
            latest = max(calls, key=lambda c: c.created_at)

            # Skip if already scheduled or declined
            if latest.outcome in ('scheduled', 'rescheduled', 'declined', 'wrong_number'):
                continue

            # Skip if max attempts reached
            if latest.attempt_number >= max_attempts:
                continue

            retry_list.append({
                'patient_name': latest.patient_name,
                'patient_phone': phone,
                'last_outcome': latest.outcome,
                'attempts': latest.attempt_number,
                'last_call': latest.call_time,
                'notes': latest.notes
            })

        return retry_list


# Convenience functions
_default_logger: Optional[CallLogger] = None


def log_call(
    patient_name: str,
    patient_phone: str,
    outcome: str,
    **kwargs
) -> CallRecord:
    """Log a call using default logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = CallLogger()
    return _default_logger.log_call(patient_name, patient_phone, outcome, **kwargs)


def get_daily_stats() -> Dict:
    """Get daily stats from default logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = CallLogger()
    return _default_logger.daily_summary()


def export_calls(output_path: Optional[str] = None) -> Path:
    """Export calls from default logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = CallLogger()
    return _default_logger.export_to_csv(output_path)


if __name__ == "__main__":
    # Demo usage
    print("NSIPA Call Logger - Demo")
    print("=" * 40)

    logger = CallLogger(caller_id="demo_user")

    # Log some sample calls
    logger.log_call("John Smith", "555-1234", "scheduled",
                    notes="Booked Monday 10am",
                    appointment_date="2024-01-15",
                    appointment_time="10:00",
                    provider="Dr. Johnson",
                    duration_seconds=180)

    logger.log_call("Jane Doe", "555-5678", "voicemail",
                    notes="Left message about appointment",
                    duration_seconds=45)

    logger.log_call("Bob Wilson", "555-9999", "callback",
                    notes="Patient at work, call after 5pm",
                    callback_time="17:00",
                    duration_seconds=60)

    logger.log_call("Mary Johnson", "555-4321", "no_answer",
                    duration_seconds=30)

    logger.log_call("Tom Brown", "555-8765", "scheduled",
                    notes="Tuesday 2pm with Dr. Smith",
                    appointment_date="2024-01-16",
                    appointment_time="14:00",
                    provider="Dr. Smith",
                    duration_seconds=240)

    # Print summary
    logger.print_summary()

    # Show retry list
    print("\nRETRY LIST:")
    for patient in logger.get_retry_list():
        print(f"  • {patient['patient_name']} ({patient['patient_phone']})")
        print(f"    Last: {patient['last_outcome']} - Attempts: {patient['attempts']}")

    # Export
    csv_path = logger.export_to_csv()
    print(f"\nExported to: {csv_path}")
