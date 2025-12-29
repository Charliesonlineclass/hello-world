"""
SCORPION-OTTER Notifier
=======================

Email and SMS notification system for meeting follow-ups and reminders.
Supports SMTP email and Twilio SMS.

Requirements:
    pip install twilio schedule
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union
import logging
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OTTER.notifier")

# Default SMTP configuration (from environment)
DEFAULT_SMTP_CONFIG = {
    'host': os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
    'port': int(os.environ.get('SMTP_PORT', 587)),
    'username': os.environ.get('SMTP_USERNAME', ''),
    'password': os.environ.get('SMTP_PASSWORD', ''),
    'from_email': os.environ.get('SMTP_FROM', ''),
    'use_tls': True
}

# Default Twilio configuration (from environment)
DEFAULT_TWILIO_CONFIG = {
    'account_sid': os.environ.get('TWILIO_ACCOUNT_SID', ''),
    'auth_token': os.environ.get('TWILIO_AUTH_TOKEN', ''),
    'from_number': os.environ.get('TWILIO_FROM_NUMBER', '')
}

# Scheduled reminders storage
_scheduled_reminders: List[Dict] = []
_scheduler_running = False


def send_email(
    to: Union[str, List[str]],
    subject: str,
    body: str,
    smtp_config: Optional[Dict] = None,
    html_body: Optional[str] = None,
    attachments: Optional[List[Union[str, Path]]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> bool:
    """
    Send an email via SMTP.

    Args:
        to: Recipient email(s)
        subject: Email subject
        body: Plain text body
        smtp_config: SMTP configuration dict (uses defaults if None)
        html_body: Optional HTML body
        attachments: Optional list of file paths to attach
        cc: Optional CC recipients
        bcc: Optional BCC recipients

    Returns:
        True if sent successfully, False otherwise
    """
    config = {**DEFAULT_SMTP_CONFIG, **(smtp_config or {})}

    if not config['username'] or not config['password']:
        logger.error("SMTP credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD.")
        return False

    # Handle single recipient
    if isinstance(to, str):
        to = [to]

    try:
        # Create message
        if html_body:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body, 'plain'))

        msg['Subject'] = subject
        msg['From'] = config['from_email'] or config['username']
        msg['To'] = ', '.join(to)

        if cc:
            msg['Cc'] = ', '.join(cc)

        # Add attachments
        if attachments:
            for attachment_path in attachments:
                path = Path(attachment_path)
                if path.exists():
                    with open(path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=path.name)
                        part['Content-Disposition'] = f'attachment; filename="{path.name}"'
                        msg.attach(part)
                else:
                    logger.warning(f"Attachment not found: {path}")

        # Calculate all recipients
        all_recipients = to.copy()
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)

        # Send email
        logger.info(f"Sending email to {', '.join(to)}...")

        with smtplib.SMTP(config['host'], config['port']) as server:
            if config['use_tls']:
                server.starttls()
            server.login(config['username'], config['password'])
            server.sendmail(config['from_email'] or config['username'],
                          all_recipients, msg.as_string())

        logger.info("Email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check username/password.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_sms_twilio(
    to: str,
    message: str,
    config: Optional[Dict] = None
) -> bool:
    """
    Send an SMS via Twilio.

    Args:
        to: Recipient phone number (E.164 format, e.g., +1234567890)
        message: SMS message body (max 1600 chars)
        config: Twilio configuration dict

    Returns:
        True if sent successfully, False otherwise
    """
    config = {**DEFAULT_TWILIO_CONFIG, **(config or {})}

    if not config['account_sid'] or not config['auth_token']:
        logger.error("Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
        return False

    if not config['from_number']:
        logger.error("Twilio from number not configured. Set TWILIO_FROM_NUMBER.")
        return False

    try:
        from twilio.rest import Client
    except ImportError:
        logger.error("Twilio not installed. Run: pip install twilio")
        return False

    try:
        # Ensure phone number format
        if not to.startswith('+'):
            to = '+1' + to.replace('-', '').replace(' ', '')

        # Truncate message if needed
        if len(message) > 1600:
            message = message[:1597] + "..."
            logger.warning("Message truncated to 1600 characters")

        # Send SMS
        logger.info(f"Sending SMS to {to}...")

        client = Client(config['account_sid'], config['auth_token'])
        sms = client.messages.create(
            body=message,
            from_=config['from_number'],
            to=to
        )

        logger.info(f"SMS sent! SID: {sms.sid}")
        return True

    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False


def schedule_reminder(
    when: Union[datetime, timedelta, str],
    message: str,
    method: str = 'email',
    recipient: Optional[str] = None,
    subject: Optional[str] = None
) -> Dict:
    """
    Schedule a reminder for later delivery.

    Args:
        when: When to send (datetime, timedelta from now, or ISO string)
        message: Reminder message
        method: 'email' or 'sms'
        recipient: Email address or phone number
        subject: Email subject (for email reminders)

    Returns:
        Reminder details dict with ID
    """
    global _scheduled_reminders

    # Parse 'when'
    if isinstance(when, str):
        send_at = datetime.fromisoformat(when)
    elif isinstance(when, timedelta):
        send_at = datetime.now() + when
    else:
        send_at = when

    reminder = {
        'id': len(_scheduled_reminders) + 1,
        'send_at': send_at.isoformat(),
        'message': message,
        'method': method,
        'recipient': recipient,
        'subject': subject or "Reminder",
        'status': 'scheduled',
        'created_at': datetime.now().isoformat()
    }

    _scheduled_reminders.append(reminder)
    logger.info(f"Reminder scheduled for {send_at}: {message[:50]}...")

    # Start scheduler if not running
    _start_scheduler()

    return reminder


def _start_scheduler():
    """Start the background scheduler thread."""
    global _scheduler_running

    if _scheduler_running:
        return

    def scheduler_loop():
        global _scheduler_running
        _scheduler_running = True

        while _scheduler_running and _scheduled_reminders:
            now = datetime.now()

            for reminder in _scheduled_reminders:
                if reminder['status'] != 'scheduled':
                    continue

                send_at = datetime.fromisoformat(reminder['send_at'])
                if now >= send_at:
                    _send_reminder(reminder)

            time.sleep(30)  # Check every 30 seconds

        _scheduler_running = False

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    logger.info("Reminder scheduler started")


def _send_reminder(reminder: Dict):
    """Send a scheduled reminder."""
    try:
        if reminder['method'] == 'sms':
            success = send_sms_twilio(
                reminder['recipient'],
                reminder['message']
            )
        else:
            success = send_email(
                reminder['recipient'],
                reminder['subject'],
                reminder['message']
            )

        reminder['status'] = 'sent' if success else 'failed'
        reminder['sent_at'] = datetime.now().isoformat()

    except Exception as e:
        logger.error(f"Failed to send reminder: {e}")
        reminder['status'] = 'failed'
        reminder['error'] = str(e)


def get_scheduled_reminders() -> List[Dict]:
    """Get all scheduled reminders."""
    return _scheduled_reminders.copy()


def cancel_reminder(reminder_id: int) -> bool:
    """Cancel a scheduled reminder."""
    for reminder in _scheduled_reminders:
        if reminder['id'] == reminder_id and reminder['status'] == 'scheduled':
            reminder['status'] = 'cancelled'
            logger.info(f"Reminder {reminder_id} cancelled")
            return True
    return False


def appointment_reminder(
    patient_name: str,
    appointment_datetime: Union[datetime, str],
    phone: Optional[str] = None,
    email: Optional[str] = None,
    provider_name: str = "your provider",
    location: str = "",
    hours_before: int = 24
) -> List[Dict]:
    """
    Schedule appointment reminder(s) for healthcare context.

    Args:
        patient_name: Patient's name
        appointment_datetime: Appointment date/time
        phone: Patient's phone for SMS reminder
        email: Patient's email for email reminder
        provider_name: Healthcare provider name
        location: Appointment location
        hours_before: Hours before appointment to send reminder

    Returns:
        List of scheduled reminder details
    """
    if isinstance(appointment_datetime, str):
        appt_dt = datetime.fromisoformat(appointment_datetime)
    else:
        appt_dt = appointment_datetime

    reminder_time = appt_dt - timedelta(hours=hours_before)

    # Format appointment time nicely
    appt_formatted = appt_dt.strftime("%A, %B %d at %I:%M %p")

    reminders = []

    # SMS reminder
    if phone:
        sms_message = (
            f"Hi {patient_name}! This is a reminder of your appointment "
            f"with {provider_name} on {appt_formatted}."
        )
        if location:
            sms_message += f" Location: {location}"
        sms_message += " Reply CONFIRM to confirm or call to reschedule."

        reminder = schedule_reminder(
            when=reminder_time,
            message=sms_message,
            method='sms',
            recipient=phone
        )
        reminders.append(reminder)

    # Email reminder
    if email:
        email_subject = f"Appointment Reminder - {appt_dt.strftime('%B %d, %Y')}"
        email_body = f"""Dear {patient_name},

This is a friendly reminder of your upcoming appointment:

Date & Time: {appt_formatted}
Provider: {provider_name}
"""
        if location:
            email_body += f"Location: {location}\n"

        email_body += """
Please arrive 15 minutes early to complete any necessary paperwork.

If you need to reschedule, please call us as soon as possible.

Thank you,
{provider_name}
"""

        reminder = schedule_reminder(
            when=reminder_time,
            message=email_body,
            method='email',
            recipient=email,
            subject=email_subject
        )
        reminders.append(reminder)

    return reminders


def send_bulk_email(
    recipients: List[str],
    subject: str,
    body: str,
    personalization: Optional[Dict[str, Dict]] = None,
    delay_seconds: float = 1.0
) -> Dict[str, bool]:
    """
    Send bulk emails with optional personalization.

    Args:
        recipients: List of email addresses
        subject: Email subject (can include {name} placeholder)
        body: Email body (can include {name}, {custom} placeholders)
        personalization: Dict mapping email to personalization values
        delay_seconds: Delay between emails to avoid rate limits

    Returns:
        Dict mapping email to success status
    """
    results = {}
    personalization = personalization or {}

    for email in recipients:
        person_data = personalization.get(email, {})

        # Apply personalization
        personalized_subject = subject
        personalized_body = body

        for key, value in person_data.items():
            personalized_subject = personalized_subject.replace(f'{{{key}}}', value)
            personalized_body = personalized_body.replace(f'{{{key}}}', value)

        success = send_email(email, personalized_subject, personalized_body)
        results[email] = success

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    sent_count = sum(1 for v in results.values() if v)
    logger.info(f"Bulk email complete: {sent_count}/{len(recipients)} sent successfully")

    return results


def load_template(template_name: str, template_dir: str = "templates") -> str:
    """
    Load a notification template from file.

    Args:
        template_name: Template filename
        template_dir: Directory containing templates

    Returns:
        Template content string
    """
    template_path = Path(template_dir) / template_name

    if not template_path.exists():
        # Try otter/templates
        template_path = Path(__file__).parent / "templates" / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    return template_path.read_text()


def render_template(template: str, **kwargs) -> str:
    """
    Render a template with variable substitution.

    Args:
        template: Template string with {variable} placeholders
        **kwargs: Variables to substitute

    Returns:
        Rendered template
    """
    result = template
    for key, value in kwargs.items():
        result = result.replace(f'{{{key}}}', str(value))
    return result


if __name__ == "__main__":
    # Test notifications
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python notifier.py email <to> <subject>")
        print("  python notifier.py sms <to> <message>")
        print("")
        print("Environment variables needed:")
        print("  Email: SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM")
        print("  SMS: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER")
        sys.exit(1)

    method = sys.argv[1].lower()

    if method == 'email':
        to = sys.argv[2]
        subject = sys.argv[3] if len(sys.argv) > 3 else "Test Email"
        body = "This is a test email from SCORPION-OTTER."

        if send_email(to, subject, body):
            print("✓ Email sent successfully!")
        else:
            print("✗ Email failed to send")

    elif method == 'sms':
        to = sys.argv[2]
        message = sys.argv[3] if len(sys.argv) > 3 else "Test SMS from SCORPION-OTTER"

        if send_sms_twilio(to, message):
            print("✓ SMS sent successfully!")
        else:
            print("✗ SMS failed to send")

    else:
        print(f"Unknown method: {method}")
        sys.exit(1)
