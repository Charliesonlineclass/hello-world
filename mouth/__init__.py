"""
SCORPION Multi-Tenant System - Mouth Module
============================================

The MOUTH is SCORPION's communication interface with the outside world.
It handles incoming webhooks, chat widgets, and API endpoints.

Components:
    - api/webhooks.py: Webhook endpoints for client forms
    - widgets/chat_widget.py: Embeddable chat for client websites

Author: SCORPION System
Version: 1.0.0
"""

from .api.webhooks import WebhookRouter, WebhookSecurityManager
from .widgets.chat_widget import ChatWidget, WidgetConfig, WidgetTheme

__all__ = [
    'WebhookRouter',
    'WebhookSecurityManager',
    'ChatWidget',
    'WidgetConfig',
    'WidgetTheme',
]
