"""
J3 Communicator
===============

Client communication automation: quote delivery, promos, reminders, follow-ups.

Requirements:
    pip install requests twilio
"""

import os
import json
import smtplib
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
logger = logging.getLogger("J3.communicator")

# Default configurations
SMTP_CONFIG = {
    'host': os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
    'port': int(os.environ.get('SMTP_PORT', 587)),
    'username': os.environ.get('SMTP_USERNAME', ''),
    'password': os.environ.get('SMTP_PASSWORD', ''),
    'from_email': os.environ.get('SMTP_FROM', ''),
    'from_name': os.environ.get('SMTP_FROM_NAME', 'J3 Construction')
}

TWILIO_CONFIG = {
    'account_sid': os.environ.get('TWILIO_ACCOUNT_SID', ''),
    'auth_token': os.environ.get('TWILIO_AUTH_TOKEN', ''),
    'from_number': os.environ.get('TWILIO_FROM_NUMBER', '')
}

# Scheduled follow-ups
_scheduled_followups: List[Dict] = []
_scheduler_running = False


def send_email(
    to: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    attachments: Optional[List[Union[str, Path]]] = None,
    from_name: Optional[str] = None,
    config: Optional[Dict] = None
) -> bool:
    """
    Send an email.

    Args:
        to: Recipient email
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        attachments: Optional list of file paths to attach
        from_name: Sender name
        config: SMTP configuration override

    Returns:
        True if sent successfully
    """
    config = {**SMTP_CONFIG, **(config or {})}
    from_name = from_name or config['from_name']

    if not config['username'] or not config['password']:
        logger.error("SMTP credentials not configured")
        return False

    try:
        if html_body:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body, 'plain'))

        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{config['from_email'] or config['username']}>"
        msg['To'] = to

        # Add attachments
        if attachments:
            for attachment_path in attachments:
                path = Path(attachment_path)
                if path.exists():
                    with open(path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=path.name)
                        part['Content-Disposition'] = f'attachment; filename="{path.name}"'
                        msg.attach(part)

        with smtplib.SMTP(config['host'], config['port']) as server:
            server.starttls()
            server.login(config['username'], config['password'])
            server.sendmail(
                config['from_email'] or config['username'],
                [to],
                msg.as_string()
            )

        logger.info(f"Email sent to {to}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_sms(
    to: str,
    message: str,
    config: Optional[Dict] = None
) -> bool:
    """
    Send SMS via Twilio.

    Args:
        to: Phone number
        message: SMS message
        config: Twilio config override

    Returns:
        True if sent successfully
    """
    config = {**TWILIO_CONFIG, **(config or {})}

    if not config['account_sid'] or not config['auth_token']:
        logger.error("Twilio credentials not configured")
        return False

    try:
        from twilio.rest import Client
    except ImportError:
        logger.error("Twilio not installed. Run: pip install twilio")
        return False

    try:
        if not to.startswith('+'):
            to = '+1' + to.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')

        client = Client(config['account_sid'], config['auth_token'])
        client.messages.create(
            body=message,
            from_=config['from_number'],
            to=to
        )

        logger.info(f"SMS sent to {to}")
        return True

    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False


def send_quote(
    client_id: str,
    quote_pdf_path: Union[str, Path],
    client_email: str,
    client_name: str,
    quote_number: str,
    quote_total: float,
    send_sms_also: bool = False,
    client_phone: Optional[str] = None
) -> Dict:
    """
    Send a quote to a client.

    Args:
        client_id: Client ID for tracking
        quote_pdf_path: Path to quote PDF
        client_email: Client's email
        client_name: Client's name
        quote_number: Quote number for reference
        quote_total: Quote total amount
        send_sms_also: Whether to also send SMS notification
        client_phone: Client phone for SMS

    Returns:
        Result dictionary with success status
    """
    result = {
        'client_id': client_id,
        'quote_number': quote_number,
        'email_sent': False,
        'sms_sent': False,
        'timestamp': datetime.now().isoformat()
    }

    # Prepare email
    subject = f"Your Quote from J3 Construction - {quote_number}"

    body = f"""Dear {client_name},

Thank you for considering J3 Construction for your project!

Please find attached your quote #{quote_number}.

Quote Summary:
- Quote Number: {quote_number}
- Total: ${quote_total:,.2f}
- Valid for 30 days

If you have any questions about this quote or would like to proceed, please don't hesitate to contact us.

We look forward to working with you!

Best regards,
J3 Construction Team

---
To accept this quote, simply reply to this email or call us.
"""

    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: #2c3e50; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">J3 Construction</h1>
    </div>

    <div style="padding: 20px;">
        <p>Dear {client_name},</p>

        <p>Thank you for considering J3 Construction for your project!</p>

        <p>Please find attached your quote <strong>#{quote_number}</strong>.</p>

        <div style="background-color: #f8f9fa; border-left: 4px solid #2c3e50; padding: 15px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Quote Summary</h3>
            <ul style="list-style: none; padding: 0;">
                <li>📋 Quote Number: <strong>{quote_number}</strong></li>
                <li>💰 Total: <strong>${quote_total:,.2f}</strong></li>
                <li>📅 Valid for 30 days</li>
            </ul>
        </div>

        <p>If you have any questions about this quote or would like to proceed, please don't hesitate to contact us.</p>

        <p>We look forward to working with you!</p>

        <p>Best regards,<br>
        <strong>J3 Construction Team</strong></p>
    </div>

    <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666;">
        <p>To accept this quote, simply reply to this email or call us.</p>
    </div>
</body>
</html>
"""

    # Send email
    result['email_sent'] = send_email(
        to=client_email,
        subject=subject,
        body=body,
        html_body=html_body,
        attachments=[quote_pdf_path]
    )

    # Send SMS if requested
    if send_sms_also and client_phone:
        sms_message = (
            f"Hi {client_name}! Your quote from J3 Construction is ready. "
            f"Quote #{quote_number} for ${quote_total:,.2f}. "
            f"Check your email or call us to discuss!"
        )
        result['sms_sent'] = send_sms(client_phone, sms_message)

    return result


def send_promo(
    client_list: List[Dict],
    promo_template: str,
    subject: str,
    delay_seconds: float = 2.0
) -> Dict:
    """
    Send promotional email to multiple clients.

    Args:
        client_list: List of client dicts with 'name', 'email'
        promo_template: Email template with {name} placeholder
        subject: Email subject
        delay_seconds: Delay between sends

    Returns:
        Results dictionary
    """
    results = {
        'total': len(client_list),
        'sent': 0,
        'failed': 0,
        'details': []
    }

    for client in client_list:
        name = client.get('name', 'Valued Customer')
        email = client.get('email')

        if not email:
            results['failed'] += 1
            results['details'].append({'email': 'missing', 'success': False})
            continue

        body = promo_template.replace('{name}', name)

        success = send_email(
            to=email,
            subject=subject,
            body=body
        )

        if success:
            results['sent'] += 1
        else:
            results['failed'] += 1

        results['details'].append({'email': email, 'success': success})

        time.sleep(delay_seconds)

    logger.info(f"Promo sent: {results['sent']}/{results['total']} successful")
    return results


def send_reminder(
    client_id: str,
    message: str,
    client_email: Optional[str] = None,
    client_phone: Optional[str] = None,
    method: str = 'both'  # 'email', 'sms', or 'both'
) -> Dict:
    """
    Send a reminder to a client.

    Args:
        client_id: Client ID
        message: Reminder message
        client_email: Email address
        client_phone: Phone number
        method: 'email', 'sms', or 'both'

    Returns:
        Result dictionary
    """
    result = {
        'client_id': client_id,
        'email_sent': False,
        'sms_sent': False,
        'timestamp': datetime.now().isoformat()
    }

    if method in ('email', 'both') and client_email:
        result['email_sent'] = send_email(
            to=client_email,
            subject="Reminder from J3 Construction",
            body=message
        )

    if method in ('sms', 'both') and client_phone:
        result['sms_sent'] = send_sms(client_phone, message)

    return result


def schedule_followup(
    client_id: str,
    days: int,
    message: str,
    client_email: Optional[str] = None,
    client_phone: Optional[str] = None,
    method: str = 'email'
) -> Dict:
    """
    Schedule a follow-up for later.

    Args:
        client_id: Client ID
        days: Days from now to send
        message: Follow-up message
        client_email: Email address
        client_phone: Phone number
        method: 'email', 'sms', or 'both'

    Returns:
        Scheduled follow-up details
    """
    global _scheduled_followups

    send_at = datetime.now() + timedelta(days=days)

    followup = {
        'id': len(_scheduled_followups) + 1,
        'client_id': client_id,
        'send_at': send_at.isoformat(),
        'message': message,
        'client_email': client_email,
        'client_phone': client_phone,
        'method': method,
        'status': 'scheduled',
        'created_at': datetime.now().isoformat()
    }

    _scheduled_followups.append(followup)

    # Save to file for persistence
    _save_followups()

    # Start scheduler if not running
    _start_scheduler()

    logger.info(f"Follow-up scheduled for {send_at.strftime('%Y-%m-%d')}")
    return followup


def _save_followups():
    """Save scheduled follow-ups to file."""
    followups_file = Path("j3_scheduled_followups.json")
    with open(followups_file, 'w') as f:
        json.dump(_scheduled_followups, f, indent=2)


def _load_followups():
    """Load scheduled follow-ups from file."""
    global _scheduled_followups
    followups_file = Path("j3_scheduled_followups.json")
    if followups_file.exists():
        try:
            _scheduled_followups = json.loads(followups_file.read_text())
        except:
            pass


def _start_scheduler():
    """Start background scheduler for follow-ups."""
    global _scheduler_running

    if _scheduler_running:
        return

    _load_followups()

    def scheduler_loop():
        global _scheduler_running
        _scheduler_running = True

        while _scheduler_running:
            now = datetime.now()

            for followup in _scheduled_followups:
                if followup['status'] != 'scheduled':
                    continue

                send_at = datetime.fromisoformat(followup['send_at'])
                if now >= send_at:
                    _process_followup(followup)

            time.sleep(60)  # Check every minute

        _scheduler_running = False

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    logger.info("Follow-up scheduler started")


def _process_followup(followup: Dict):
    """Process a scheduled follow-up."""
    try:
        result = send_reminder(
            client_id=followup['client_id'],
            message=followup['message'],
            client_email=followup.get('client_email'),
            client_phone=followup.get('client_phone'),
            method=followup.get('method', 'email')
        )

        if result['email_sent'] or result['sms_sent']:
            followup['status'] = 'sent'
        else:
            followup['status'] = 'failed'

        followup['processed_at'] = datetime.now().isoformat()
        _save_followups()

    except Exception as e:
        logger.error(f"Error processing follow-up: {e}")
        followup['status'] = 'failed'
        followup['error'] = str(e)
        _save_followups()


def get_scheduled_followups() -> List[Dict]:
    """Get all scheduled follow-ups."""
    _load_followups()
    return _scheduled_followups


def cancel_followup(followup_id: int) -> bool:
    """Cancel a scheduled follow-up."""
    _load_followups()

    for followup in _scheduled_followups:
        if followup['id'] == followup_id and followup['status'] == 'scheduled':
            followup['status'] = 'cancelled'
            _save_followups()
            logger.info(f"Follow-up {followup_id} cancelled")
            return True

    return False


# Email templates
TEMPLATES = {
    "quote_followup": """Hi {name},

I wanted to follow up on the quote we sent over on {quote_date}.

Have you had a chance to review it? We'd be happy to answer any questions or discuss the project in more detail.

If you'd like to proceed, just let us know and we can get you on the schedule.

Looking forward to hearing from you!

Best,
J3 Construction""",

    "thank_you": """Dear {name},

Thank you for choosing J3 Construction for your {job_type} project!

We truly appreciate your trust in us and are committed to delivering excellent results.

If you have any questions during the project, don't hesitate to reach out.

Best regards,
J3 Construction Team""",

    "project_complete": """Dear {name},

Great news - your {job_type} project is now complete!

We hope you're happy with the results. If there's anything that needs attention, please let us know within the next 7 days.

We'd really appreciate it if you could leave us a review. It helps other homeowners find quality contractors!

Thank you for choosing J3 Construction.

Best regards,
The J3 Team""",

    "seasonal_promo": """Hi {name},

Hope you're doing well! We have some exciting news...

🏠 SEASONAL SPECIAL 🏠
Book any project before the end of the month and receive 10% off labor costs!

Whether you've been thinking about that kitchen remodel, new deck, or home addition - now's the perfect time.

Reply to this email or call us to schedule a free consultation.

Best,
J3 Construction"""
}


def get_template(template_name: str) -> Optional[str]:
    """Get an email template."""
    return TEMPLATES.get(template_name)


def list_templates() -> List[str]:
    """List available email templates."""
    return list(TEMPLATES.keys())


if __name__ == "__main__":
    print("J3 Communicator - Demo")
    print("=" * 40)

    print("\nAvailable Templates:")
    for name in list_templates():
        print(f"  - {name}")

    print("\nScheduled Follow-ups:")
    followups = get_scheduled_followups()
    if followups:
        for f in followups:
            print(f"  - {f['id']}: {f['status']} - {f['send_at']}")
    else:
        print("  No scheduled follow-ups")
