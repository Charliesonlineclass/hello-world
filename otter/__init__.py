"""
SCORPION-OTTER: FOPSE Meeting Transcription System
===================================================

A comprehensive meeting transcription, summarization, and notification system.
Part of the SCORPION ecosystem - replacing expensive SaaS with local AI.

Modules:
    - transcriber: Audio to text using OpenAI Whisper
    - summarizer: Meeting summaries using Ollama/MARCUS
    - notifier: Email/SMS notifications and reminders
    - meeting_bot: Full pipeline automation

Usage:
    from otter import MeetingBot

    bot = MeetingBot()
    result = bot.process_recording("meeting.mp3")
    print(result['summary'])

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .transcriber import (
    transcribe_file,
    transcribe_audio,
    supported_formats,
    save_transcript
)

from .summarizer import (
    summarize_meeting,
    extract_action_items,
    extract_decisions,
    extract_participants,
    generate_followup_email
)

from .notifier import (
    send_email,
    send_sms_twilio,
    schedule_reminder,
    appointment_reminder
)

from .meeting_bot import MeetingBot

__version__ = "1.0.0"
__codename__ = "TESTUDO"
__all__ = [
    'MeetingBot',
    'transcribe_file',
    'transcribe_audio',
    'save_transcript',
    'summarize_meeting',
    'extract_action_items',
    'extract_decisions',
    'extract_participants',
    'generate_followup_email',
    'send_email',
    'send_sms_twilio',
    'schedule_reminder',
    'appointment_reminder'
]
