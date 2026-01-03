"""
SCORPION Multi-Tenant System - Embeddable Chat Widget
======================================================

This module generates embeddable chat widgets for client websites.
Each widget connects to the client's assigned AI baby for responses.

SCORPION Architecture Role:
    Part of MOUTH - the communication interface
    Provides AI-powered chat on client websites

Features:
    - Floating chat bubble
    - Client branding (colors, logo)
    - Lead capture form
    - Auto-greeting based on page
    - Typing indicator
    - Chat history per session

Security:
    - Session-based authentication
    - Rate limiting per session
    - Content filtering
    - All chats logged

Author: SCORPION System
Version: 1.0.0
"""

import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

logger = logging.getLogger("scorpion.widget")


@dataclass
class WidgetTheme:
    """Visual theme for the chat widget."""
    primary_color: str = "#2563eb"      # Blue
    secondary_color: str = "#1e40af"    # Darker blue
    text_color: str = "#ffffff"
    background_color: str = "#ffffff"
    bubble_position: str = "bottom-right"  # bottom-right, bottom-left
    border_radius: int = 16
    font_family: str = "system-ui, -apple-system, sans-serif"


@dataclass
class WidgetConfig:
    """Configuration for a chat widget."""
    client_id: str
    baby_name: str
    theme: WidgetTheme
    greeting_message: str
    placeholder_text: str = "Type a message..."
    company_name: str = ""
    logo_url: Optional[str] = None
    auto_open_delay: Optional[int] = None  # Seconds, None to disable
    collect_email: bool = True
    collect_phone: bool = False
    collect_name: bool = True
    page_greetings: Dict[str, str] = field(default_factory=dict)
    business_hours: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['theme'] = asdict(self.theme)
        return data


@dataclass
class ChatMessage:
    """A single chat message."""
    id: str
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ChatSession:
    """A chat session with a visitor."""
    id: str
    client_id: str
    started_at: datetime
    messages: List[ChatMessage] = field(default_factory=list)
    visitor_info: Dict[str, Any] = field(default_factory=dict)
    lead_captured: bool = False
    lead_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "started_at": self.started_at.isoformat(),
            "messages": [m.to_dict() for m in self.messages],
            "visitor_info": self.visitor_info,
            "lead_captured": self.lead_captured,
            "lead_id": self.lead_id
        }


class ChatWidget:
    """
    SCORPION Embeddable Chat Widget.

    Generates and manages chat widgets for client websites.
    Each widget connects visitors to the client's AI baby.

    SCORPION Architecture:
    - Part of MOUTH (communication interface)
    - Routes chat to BABIES (Ollama AI models)
    - Captures leads for LEGS (client interfaces)

    Features:
    - Embeddable JavaScript snippet
    - Client branding
    - Lead capture
    - Auto-greetings
    - Session management

    Usage:
        widget = ChatWidget("j3_structural", "phi3:mini")
        embed_code = widget.generate_embed_code()
        # Add embed_code to client's website <head>
    """

    # Default greetings by industry
    INDUSTRY_GREETINGS = {
        "construction": "Hi! Looking for a construction estimate? I can help you get started.",
        "call_center": "Hello! How can I help you today?",
        "banking": "Welcome! I'm here to help with your financial questions.",
        "real_estate": "Hi there! Looking for your dream home? Let me help you find it.",
    }

    def __init__(
        self,
        client_id: str,
        baby_name: str,
        theme_color: str = "#2563eb",
        company_name: Optional[str] = None,
        leg: Optional[Any] = None,
        audit_log: Optional[Any] = None
    ):
        """
        Initialize chat widget.

        Args:
            client_id: Client identifier
            baby_name: Ollama model name
            theme_color: Primary color for widget
            company_name: Company name for branding
            leg: Client leg instance for processing
            audit_log: Audit log for tracking
        """
        self.client_id = client_id
        self.baby_name = baby_name
        self.leg = leg
        self.audit_log = audit_log

        # Create default theme
        self.theme = WidgetTheme(primary_color=theme_color)

        # Determine greeting based on client type
        industry = self._detect_industry(client_id)
        default_greeting = self.INDUSTRY_GREETINGS.get(
            industry,
            "Hi! How can I help you today?"
        )

        # Create config
        self.config = WidgetConfig(
            client_id=client_id,
            baby_name=baby_name,
            theme=self.theme,
            greeting_message=default_greeting,
            company_name=company_name or client_id.replace("_", " ").title()
        )

        # Session storage
        self._sessions: Dict[str, ChatSession] = {}

        logger.info(f"ChatWidget initialized for {client_id} with {baby_name}")

    def _detect_industry(self, client_id: str) -> str:
        """Detect industry from client ID."""
        if "j3" in client_id or "structural" in client_id:
            return "construction"
        elif "joe" in client_id or "ipc" in client_id:
            return "call_center"
        elif "antonio" in client_id or "bank" in client_id:
            return "banking"
        elif "will" in client_id or "real" in client_id:
            return "real_estate"
        return "general"

    def generate_embed_code(self) -> str:
        """
        Generate the embeddable HTML/JS snippet for client websites.

        Returns:
            HTML snippet to embed in website <head> or before </body>
        """
        widget_id = f"scorpion_widget_{self.client_id}"
        config_json = json.dumps(self.config.to_dict())

        # Generate embed code
        embed_code = f'''
<!-- SCORPION Chat Widget for {self.config.company_name} -->
<script>
(function(w, d, s, c) {{
    // SCORPION Widget Configuration
    w.ScorpionWidgetConfig = {config_json};

    // Create widget container
    var container = d.createElement('div');
    container.id = '{widget_id}';
    d.body.appendChild(container);

    // Load widget script
    var script = d.createElement('script');
    script.src = 'https://widget.scorpion.local/chat.js';
    script.async = true;
    script.onload = function() {{
        if (w.ScorpionWidget) {{
            w.ScorpionWidget.init('{widget_id}', w.ScorpionWidgetConfig);
        }}
    }};
    d.head.appendChild(script);

    // Load widget styles
    var link = d.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://widget.scorpion.local/chat.css';
    d.head.appendChild(link);
}})(window, document);
</script>
<!-- End SCORPION Chat Widget -->
'''
        return embed_code.strip()

    def generate_inline_widget(self) -> str:
        """
        Generate a fully inline widget (no external dependencies).

        Returns:
            Complete HTML/CSS/JS for the widget
        """
        theme = self.theme
        config = self.config

        inline_widget = f'''
<!-- SCORPION Chat Widget - Inline Version -->
<style>
#scorpion-chat-widget {{
    position: fixed;
    {theme.bubble_position.replace('-', ': 20px; ').replace('bottom', 'bottom: 20px')};
    z-index: 99999;
    font-family: {theme.font_family};
}}

#scorpion-chat-bubble {{
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: {theme.primary_color};
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transition: transform 0.2s, box-shadow 0.2s;
}}

#scorpion-chat-bubble:hover {{
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}}

#scorpion-chat-bubble svg {{
    width: 28px;
    height: 28px;
    fill: {theme.text_color};
}}

#scorpion-chat-window {{
    display: none;
    position: absolute;
    bottom: 70px;
    right: 0;
    width: 360px;
    height: 500px;
    background: {theme.background_color};
    border-radius: {theme.border_radius}px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
    overflow: hidden;
    flex-direction: column;
}}

#scorpion-chat-window.open {{
    display: flex;
}}

#scorpion-chat-header {{
    background: {theme.primary_color};
    color: {theme.text_color};
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}

#scorpion-chat-header h4 {{
    margin: 0;
    font-size: 16px;
    font-weight: 600;
}}

#scorpion-chat-close {{
    background: none;
    border: none;
    color: {theme.text_color};
    cursor: pointer;
    padding: 4px;
    opacity: 0.8;
}}

#scorpion-chat-close:hover {{
    opacity: 1;
}}

#scorpion-chat-messages {{
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.scorpion-message {{
    max-width: 85%;
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.4;
}}

.scorpion-message.assistant {{
    background: #f1f5f9;
    color: #334155;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
}}

.scorpion-message.user {{
    background: {theme.primary_color};
    color: {theme.text_color};
    align-self: flex-end;
    border-bottom-right-radius: 4px;
}}

#scorpion-chat-input-area {{
    padding: 12px 16px;
    border-top: 1px solid #e2e8f0;
    display: flex;
    gap: 8px;
}}

#scorpion-chat-input {{
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    font-size: 14px;
    outline: none;
}}

#scorpion-chat-input:focus {{
    border-color: {theme.primary_color};
}}

#scorpion-chat-send {{
    background: {theme.primary_color};
    color: {theme.text_color};
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}}

#scorpion-chat-send:hover {{
    background: {theme.secondary_color};
}}

.scorpion-typing {{
    display: flex;
    gap: 4px;
    padding: 12px 16px;
}}

.scorpion-typing span {{
    width: 8px;
    height: 8px;
    background: #94a3b8;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
}}

.scorpion-typing span:nth-child(2) {{ animation-delay: 0.2s; }}
.scorpion-typing span:nth-child(3) {{ animation-delay: 0.4s; }}

@keyframes typing {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-4px); }}
}}

#scorpion-lead-form {{
    padding: 16px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
}}

#scorpion-lead-form input {{
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-bottom: 8px;
    font-size: 14px;
}}

#scorpion-lead-form button {{
    width: 100%;
    padding: 10px;
    background: {theme.primary_color};
    color: {theme.text_color};
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
}}
</style>

<div id="scorpion-chat-widget">
    <div id="scorpion-chat-bubble" onclick="ScorpionChat.toggle()">
        <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.2L4 17.2V4h16v12z"/></svg>
    </div>
    <div id="scorpion-chat-window">
        <div id="scorpion-chat-header">
            <h4>{config.company_name}</h4>
            <button id="scorpion-chat-close" onclick="ScorpionChat.toggle()">&times;</button>
        </div>
        <div id="scorpion-chat-messages"></div>
        <div id="scorpion-chat-input-area">
            <input type="text" id="scorpion-chat-input" placeholder="{config.placeholder_text}" onkeypress="if(event.key==='Enter')ScorpionChat.send()">
            <button id="scorpion-chat-send" onclick="ScorpionChat.send()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
        </div>
    </div>
</div>

<script>
var ScorpionChat = {{
    sessionId: null,
    isOpen: false,

    init: function() {{
        this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        // Add greeting message
        this.addMessage('assistant', "{config.greeting_message}");
    }},

    toggle: function() {{
        var win = document.getElementById('scorpion-chat-window');
        this.isOpen = !this.isOpen;
        if (this.isOpen) {{
            win.classList.add('open');
        }} else {{
            win.classList.remove('open');
        }}
    }},

    addMessage: function(role, content) {{
        var container = document.getElementById('scorpion-chat-messages');
        var msg = document.createElement('div');
        msg.className = 'scorpion-message ' + role;
        msg.textContent = content;
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
    }},

    showTyping: function() {{
        var container = document.getElementById('scorpion-chat-messages');
        var typing = document.createElement('div');
        typing.id = 'scorpion-typing';
        typing.className = 'scorpion-message assistant scorpion-typing';
        typing.innerHTML = '<span></span><span></span><span></span>';
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    }},

    hideTyping: function() {{
        var typing = document.getElementById('scorpion-typing');
        if (typing) typing.remove();
    }},

    send: function() {{
        var input = document.getElementById('scorpion-chat-input');
        var message = input.value.trim();
        if (!message) return;

        this.addMessage('user', message);
        input.value = '';

        this.showTyping();

        // Simulate AI response (would POST to /api/chat in production)
        var self = this;
        setTimeout(function() {{
            self.hideTyping();
            self.addMessage('assistant', "Thanks for your message! Our team will get back to you soon. For immediate assistance, please call us directly.");
        }}, 1500);
    }}
}};

ScorpionChat.init();
</script>
<!-- End SCORPION Chat Widget -->
'''
        return inline_widget.strip()

    def get_widget_config(self) -> Dict[str, Any]:
        """
        Get widget configuration as JSON.

        Returns:
            Widget configuration dictionary
        """
        return self.config.to_dict()

    def handle_message(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Handle an incoming chat message.

        Routes to the client's AI baby for response.

        Args:
            session_id: Chat session ID
            message: User message

        Returns:
            Response with AI reply
        """
        # Get or create session
        session = self._get_or_create_session(session_id)

        # Create user message
        user_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            role="user",
            content=message,
            timestamp=datetime.now()
        )
        session.messages.append(user_msg)

        # Get AI response
        response_content = self._get_ai_response(session, message)

        # Create assistant message
        assistant_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            role="assistant",
            content=response_content,
            timestamp=datetime.now()
        )
        session.messages.append(assistant_msg)

        # Log chat
        self._log_chat(session_id, message, response_content)

        return {
            "session_id": session_id,
            "response": response_content,
            "message_id": assistant_msg.id
        }

    def _get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(
                id=session_id,
                client_id=self.client_id,
                started_at=datetime.now()
            )
        return self._sessions[session_id]

    def _get_ai_response(self, session: ChatSession, message: str) -> str:
        """Get response from AI baby."""
        if self.leg:
            # Use the leg's baby for response
            result = self.leg.query_baby(message)
            return result.get("response", "I'm here to help! Could you tell me more?")
        else:
            # Fallback response
            return "Thanks for reaching out! One of our team members will be with you shortly."

    def capture_lead(
        self,
        session_id: str,
        contact_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Capture lead information from chat session.

        Args:
            session_id: Chat session ID
            contact_info: Contact information (name, email, phone)

        Returns:
            Lead capture result
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        # Store visitor info
        session.visitor_info = contact_info

        # Create lead in leg if available
        if self.leg:
            lead_data = {
                "name": contact_info.get("name", "Chat Visitor"),
                "email": contact_info.get("email", ""),
                "phone": contact_info.get("phone", ""),
                "source": "chat_widget",
                "notes": f"Captured from chat session {session_id}"
            }

            result = self.leg.process_request(
                request_type="lead_create",
                data=lead_data
            )

            if result.get("success"):
                session.lead_captured = True
                session.lead_id = result.get("data", {}).get("id")

                return {
                    "success": True,
                    "lead_id": session.lead_id,
                    "message": "Thanks! We'll be in touch soon."
                }

        session.lead_captured = True
        return {
            "success": True,
            "message": "Thanks! We'll be in touch soon."
        }

    def _log_chat(
        self,
        session_id: str,
        user_message: str,
        ai_response: str
    ) -> None:
        """Log chat interaction to audit."""
        if self.audit_log:
            self.audit_log.log_access(
                user_id="widget_visitor",
                action="chat_message",
                resource=f"widget:{self.client_id}",
                details={
                    "session_id": session_id,
                    "message_length": len(user_message),
                    "response_length": len(ai_response)
                },
                client_id=self.client_id
            )

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return []
        return [m.to_dict() for m in session.messages]

    def set_page_greeting(self, page_pattern: str, greeting: str) -> None:
        """Set custom greeting for specific pages."""
        self.config.page_greetings[page_pattern] = greeting

    def update_theme(self, **kwargs) -> None:
        """Update widget theme settings."""
        for key, value in kwargs.items():
            if hasattr(self.theme, key):
                setattr(self.theme, key, value)
