"""
SCORPION AI - Chat API Routes
Handle AI chat endpoints for public and client portals
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import httpx
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crm.database import get_connection
from crm.clients import ClientManager

router = APIRouter()
client_manager = ClientManager()

# Simple in-memory rate limiting (in production, use Redis)
rate_limits: Dict[str, List[datetime]] = {}
RATE_LIMIT = 20  # requests per hour
RATE_WINDOW = 3600  # 1 hour in seconds


class ChatMessage(BaseModel):
    """Schema for chat message"""
    message: str
    session_id: Optional[str] = None
    history: Optional[List[Dict]] = []


class ClientChatMessage(BaseModel):
    """Schema for authenticated client chat"""
    message: str
    client_id: int


def check_rate_limit(ip: str) -> bool:
    """Check if IP is within rate limit"""
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_WINDOW)

    if ip not in rate_limits:
        rate_limits[ip] = []

    # Clean old entries
    rate_limits[ip] = [t for t in rate_limits[ip] if t > window_start]

    if len(rate_limits[ip]) >= RATE_LIMIT:
        return False

    rate_limits[ip].append(now)
    return True


async def call_ollama(
    prompt: str,
    model: str = "tinyllama",
    system_prompt: Optional[str] = None
) -> str:
    """Call Ollama API for AI response"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "I apologize, I'm having trouble responding right now.")
            else:
                return get_fallback_response(prompt)

    except Exception as e:
        print(f"Ollama error: {e}")
        return get_fallback_response(prompt)


def get_fallback_response(message: str) -> str:
    """Get fallback response when AI is unavailable"""
    message_lower = message.lower()

    responses = {
        'pricing': "We offer three tiers: Starter ($100/mo), Pro ($200/mo), and Empire ($500/mo). All plans include our rent-to-own model - after 12 months, you own your AI system!",
        'price': "We offer three tiers: Starter ($100/mo), Pro ($200/mo), and Empire ($500/mo). All plans include our rent-to-own model!",
        'service': "We offer AI Virtual Assistants, Website Development, Business Automation, and Training & Consulting. What area interests you?",
        'hello': "Hello! I'm HERMES, your AI assistant. How can I help you today with AI automation solutions?",
        'hi': "Hi there! I'm HERMES. How can I assist you today?",
        'help': "I'm here to help! I can tell you about our services, pricing, or connect you with our team.",
        'contact': "You can reach us at info@ometeolt.com or via WhatsApp. Would you like more information?",
        'demo': "Great! Please share your contact info or visit our contact page to schedule a demo.",
        'own': "With our rent-to-own model, after 12 months of payments, you fully own your AI system!",
    }

    for keyword, response in responses.items():
        if keyword in message_lower:
            return response

    return "I'd be happy to help! Could you tell me more about what you're looking for? I can assist with our AI services, pricing, or connect you with our team."


def save_chat_session(session_id: str, messages: List[Dict]):
    """Save chat session to database"""
    try:
        import json
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_sessions (session_id, messages, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    messages = ?,
                    updated_at = ?
            """, (
                session_id,
                json.dumps(messages),
                datetime.now().isoformat(),
                json.dumps(messages),
                datetime.now().isoformat()
            ))
    except Exception as e:
        print(f"Error saving chat session: {e}")


@router.post("/public")
async def public_chat(request: Request, chat: ChatMessage):
    """
    Public chat endpoint for website visitors.
    Rate limited: 20 requests per hour per IP.
    Uses HERMES (tinyllama) for fast responses.
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )

    # Build context from history
    context = ""
    if chat.history:
        for msg in chat.history[-5:]:  # Last 5 messages for context
            role = "User" if msg.get('role') == 'user' else "HERMES"
            context += f"{role}: {msg.get('content', '')}\n"

    # System prompt for public chat
    system_prompt = """You are HERMES, a friendly AI assistant for SCORPION AI / Ometeolt.
You help website visitors learn about AI automation services.

Key information:
- Services: AI Virtual Assistants, Website Development, Business Automation, Training
- Pricing: Starter $100/mo, Pro $200/mo, Empire $500/mo
- Unique model: Rent-to-Own - after 12 months, customers fully own their AI system
- AI Babies: HERMES (basic), VULCAN (builder), MARCUS (analyst)
- Location: El Salvador

Be helpful, concise, and friendly. Keep responses under 3 sentences.
If asked about specific technical implementations or custom quotes, suggest contacting the team.
Always be positive about the services without being pushy."""

    # Call AI
    full_prompt = f"{context}User: {chat.message}\nHERMES:"
    response = await call_ollama(full_prompt, "tinyllama", system_prompt)

    # Save session
    if chat.session_id:
        messages = chat.history or []
        messages.append({"role": "user", "content": chat.message})
        messages.append({"role": "bot", "content": response})
        save_chat_session(chat.session_id, messages)

    return {
        "response": response,
        "session_id": chat.session_id
    }


@router.post("/client")
async def client_chat(chat: ClientChatMessage):
    """
    Authenticated client chat endpoint.
    Uses the client's assigned AI baby.
    No rate limit for authenticated clients.
    """
    # Get client info
    client = client_manager.get_client(chat.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get baby configuration
    baby_configs = {
        'HERMES': {
            'model': 'tinyllama',
            'system': "You are HERMES, a helpful AI assistant. Be concise and friendly."
        },
        'VULCAN': {
            'model': 'phi3:mini',
            'system': "You are VULCAN, an expert builder and problem solver. Help with technical challenges and implementation."
        },
        'MARCUS': {
            'model': 'qwen2.5:7b',
            'system': "You are MARCUS, a strategic analyst. Provide deep insights, analysis, and strategic recommendations."
        }
    }

    baby_name = client.baby_assigned or 'HERMES'
    baby_config = baby_configs.get(baby_name, baby_configs['HERMES'])

    # Personalize system prompt
    system_prompt = f"""{baby_config['system']}

You are assisting {client.name} from {client.company or 'their company'}.
Their tier: {client.tier.value}
Ownership progress: {client.months_paid}/12 months ({client.ownership_percent:.0f}%)

Be helpful and personalized to their needs."""

    # Call AI
    response = await call_ollama(chat.message, baby_config['model'], system_prompt)

    return {
        "response": response,
        "baby": baby_name,
        "client_id": chat.client_id
    }


@router.get("/models")
async def get_available_models():
    """Get available AI models (babies)"""
    return {
        "models": [
            {
                "name": "HERMES",
                "model": "tinyllama",
                "description": "Fast, friendly public chat assistant",
                "tier_required": "starter"
            },
            {
                "name": "VULCAN",
                "model": "phi3:mini",
                "description": "Builder & technical problem solver",
                "tier_required": "pro"
            },
            {
                "name": "MARCUS",
                "model": "qwen2.5:7b",
                "description": "Strategic analysis & deep insights",
                "tier_required": "empire"
            }
        ]
    }


@router.get("/health")
async def chat_health():
    """Check if Ollama is available"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                return {"status": "healthy", "ollama": "connected"}
    except Exception:
        pass

    return {"status": "degraded", "ollama": "unavailable", "fallback": "active"}
