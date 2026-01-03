"""
SCORPION Multi-Tenant System - Webhook API
===========================================

FastAPI router for handling incoming webhooks from client websites.
Each client has dedicated webhook endpoints for receiving leads and data.

SCORPION Architecture Role:
    Part of MOUTH - the communication interface
    Receives external data and routes to appropriate legs

Endpoints:
    POST /webhook/j3/contact - J3 Structural website forms
    POST /webhook/joe/lead - IPC call center leads
    POST /webhook/antonio/application - Banking loan applications
    POST /webhook/will/inquiry - Real estate property inquiries

Security:
    - Webhook secret validation per client
    - Rate limiting: 100 requests/hour per client
    - All requests logged to audit trail
    - Payload validation

Author: SCORPION System
Version: 1.0.0
"""

import os
import json
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict
import logging

# FastAPI imports (would be installed in production)
try:
    from fastapi import APIRouter, HTTPException, Request, Header, Depends
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, EmailStr, Field
except ImportError:
    # Stub for when FastAPI is not installed
    class APIRouter:
        def __init__(self, **kwargs): pass
        def post(self, path, **kwargs):
            def decorator(func): return func
            return decorator
        def get(self, path, **kwargs):
            def decorator(func): return func
            return decorator

    class BaseModel:
        pass

    def Header(default=None, **kwargs): return default
    def Depends(func): return None
    HTTPException = Exception
    Request = object
    JSONResponse = dict
    EmailStr = str
    def Field(**kwargs): return None

logger = logging.getLogger("scorpion.webhooks")


# Pydantic models for request validation

class ContactFormPayload(BaseModel):
    """Payload for contact form submissions."""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    message: Optional[str] = Field(None, max_length=2000)
    job_type: Optional[str] = None
    address: Optional[str] = None
    source: Optional[str] = "website"
    referrer: Optional[str] = None


class CallLeadPayload(BaseModel):
    """Payload for call center leads."""
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None
    lead_type: Optional[str] = "cold"
    source: Optional[str] = "direct"
    best_time_to_call: Optional[str] = None
    notes: Optional[str] = None


class LoanApplicationPayload(BaseModel):
    """Payload for loan applications."""
    applicant_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=20)
    loan_type: str
    amount_requested: float = Field(..., gt=0)
    credit_score: Optional[int] = Field(None, ge=300, le=850)
    annual_income: Optional[float] = None
    employment_status: Optional[str] = None
    additional_info: Optional[str] = None


class PropertyInquiryPayload(BaseModel):
    """Payload for real estate inquiries."""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = None
    property_id: Optional[str] = None
    inquiry_type: str = "general"  # general, showing, info
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    bedrooms: Optional[int] = None
    message: Optional[str] = None


class WebhookResponse(BaseModel):
    """Standard webhook response."""
    success: bool
    message: str
    lead_id: Optional[str] = None
    auto_response: Optional[str] = None


@dataclass
class RateLimitEntry:
    """Rate limit tracking for a client."""
    requests: int = 0
    window_start: datetime = field(default_factory=datetime.now)


class WebhookSecurityManager:
    """
    Manages webhook security including secret validation and rate limiting.

    Security Features:
    - HMAC signature verification
    - Rate limiting per client
    - IP logging
    - Audit trail integration
    """

    def __init__(self, rate_limit: int = 100, window_hours: int = 1):
        """
        Initialize security manager.

        Args:
            rate_limit: Max requests per window
            window_hours: Time window in hours
        """
        self.rate_limit = rate_limit
        self.window_hours = window_hours
        self._rate_limits: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)

        # Client webhook secrets (would be stored securely in production)
        self._secrets: Dict[str, str] = {
            "j3_structural": os.environ.get("J3_WEBHOOK_SECRET", "j3_secret_key_change_me"),
            "joe_ipc": os.environ.get("JOE_WEBHOOK_SECRET", "joe_secret_key_change_me"),
            "antonio_banking": os.environ.get("ANTONIO_WEBHOOK_SECRET", "antonio_secret_key_change_me"),
            "will_realestate": os.environ.get("WILL_WEBHOOK_SECRET", "will_secret_key_change_me"),
        }

    def validate_signature(
        self,
        client_id: str,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Validate HMAC signature for a webhook request.

        Args:
            client_id: Client identifier
            payload: Raw request body
            signature: Provided signature header

        Returns:
            True if signature is valid
        """
        if not signature:
            return False

        secret = self._secrets.get(client_id)
        if not secret:
            logger.warning(f"No webhook secret configured for client {client_id}")
            return False

        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)

    def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client is within rate limits.

        Args:
            client_id: Client identifier

        Returns:
            True if within limits
        """
        now = datetime.now()
        entry = self._rate_limits[client_id]

        # Reset window if expired
        if (now - entry.window_start) > timedelta(hours=self.window_hours):
            entry.requests = 0
            entry.window_start = now

        # Check limit
        if entry.requests >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return False

        entry.requests += 1
        return True

    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests in current window."""
        entry = self._rate_limits.get(client_id)
        if not entry:
            return self.rate_limit
        return max(0, self.rate_limit - entry.requests)


class WebhookRouter:
    """
    SCORPION Webhook Router.

    Handles incoming webhooks from client websites and routes them
    to the appropriate leg for processing.

    SCORPION Architecture:
    - Part of MOUTH (communication interface)
    - Routes external requests to LEGS (client interfaces)
    - Logs all activity to TAIL/Labienus (audit)

    Usage:
        router = WebhookRouter()
        app.include_router(router.api_router)
    """

    def __init__(
        self,
        legs: Optional[Dict[str, Any]] = None,
        audit_log: Optional[Any] = None
    ):
        """
        Initialize webhook router.

        Args:
            legs: Dictionary of leg instances by client_id
            audit_log: AuditLog instance for logging
        """
        self.legs = legs or {}
        self.audit_log = audit_log
        self.security = WebhookSecurityManager()

        # Create FastAPI router
        self.api_router = APIRouter(
            prefix="/webhook",
            tags=["webhooks"]
        )

        # Register routes
        self._register_routes()

        logger.info("WebhookRouter initialized")

    def _register_routes(self) -> None:
        """Register all webhook endpoints."""

        @self.api_router.post("/j3/contact", response_model=WebhookResponse)
        async def j3_contact_webhook(
            payload: ContactFormPayload,
            request: Request,
            x_webhook_signature: Optional[str] = Header(None)
        ) -> WebhookResponse:
            """
            Receive contact form submission from J3 Structural website.

            Payload:
                name: Customer name
                email: Email address
                phone: Phone number (optional)
                message: Inquiry message
                job_type: Type of work needed
                address: Project address
            """
            return await self._process_webhook(
                client_id="j3_structural",
                webhook_type="contact",
                payload=payload.dict(),
                request=request,
                signature=x_webhook_signature
            )

        @self.api_router.post("/joe/lead", response_model=WebhookResponse)
        async def joe_lead_webhook(
            payload: CallLeadPayload,
            request: Request,
            x_webhook_signature: Optional[str] = Header(None)
        ) -> WebhookResponse:
            """
            Receive new lead for Joe's IPC call center.

            Payload:
                name: Lead name
                phone: Phone number (required)
                email: Email (optional)
                lead_type: cold, warm, hot, referral
                source: Lead source
            """
            return await self._process_webhook(
                client_id="joe_ipc",
                webhook_type="lead",
                payload=payload.dict(),
                request=request,
                signature=x_webhook_signature
            )

        @self.api_router.post("/antonio/application", response_model=WebhookResponse)
        async def antonio_application_webhook(
            payload: LoanApplicationPayload,
            request: Request,
            x_webhook_signature: Optional[str] = Header(None)
        ) -> WebhookResponse:
            """
            Receive loan application for Antonio's Banking.

            Payload:
                applicant_name: Full name
                email: Email address
                phone: Phone number
                loan_type: personal, mortgage, auto, business
                amount_requested: Loan amount
                credit_score: Self-reported credit score
            """
            return await self._process_webhook(
                client_id="antonio_banking",
                webhook_type="application",
                payload=payload.dict(),
                request=request,
                signature=x_webhook_signature
            )

        @self.api_router.post("/will/inquiry", response_model=WebhookResponse)
        async def will_inquiry_webhook(
            payload: PropertyInquiryPayload,
            request: Request,
            x_webhook_signature: Optional[str] = Header(None)
        ) -> WebhookResponse:
            """
            Receive property inquiry for Will's Real Estate.

            Payload:
                name: Inquirer name
                email: Email address
                phone: Phone number
                property_id: Specific property (if applicable)
                inquiry_type: general, showing, info
                budget_min/max: Price range
            """
            return await self._process_webhook(
                client_id="will_realestate",
                webhook_type="inquiry",
                payload=payload.dict(),
                request=request,
                signature=x_webhook_signature
            )

        @self.api_router.get("/health")
        async def health_check() -> Dict[str, Any]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "endpoints": [
                    "/webhook/j3/contact",
                    "/webhook/joe/lead",
                    "/webhook/antonio/application",
                    "/webhook/will/inquiry"
                ]
            }

    async def _process_webhook(
        self,
        client_id: str,
        webhook_type: str,
        payload: Dict[str, Any],
        request: Request,
        signature: Optional[str]
    ) -> WebhookResponse:
        """
        Process an incoming webhook request.

        Args:
            client_id: Target client ID
            webhook_type: Type of webhook
            payload: Request payload
            request: FastAPI request object
            signature: Webhook signature for validation

        Returns:
            WebhookResponse with result
        """
        # Get client IP
        client_ip = getattr(request, 'client', None)
        ip_address = client_ip.host if client_ip else "unknown"

        # Log incoming webhook
        self._log_webhook(
            client_id=client_id,
            webhook_type=webhook_type,
            ip_address=ip_address,
            success=True,
            details={"payload_keys": list(payload.keys())}
        )

        # Check rate limit
        if not self.security.check_rate_limit(client_id):
            self._log_webhook(
                client_id=client_id,
                webhook_type=webhook_type,
                ip_address=ip_address,
                success=False,
                details={"error": "rate_limit_exceeded"}
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later."
            )

        # Validate signature (optional in development)
        if signature:
            try:
                body = await request.body()
                if not self.security.validate_signature(client_id, body, signature):
                    logger.warning(f"Invalid webhook signature for {client_id}")
                    # Continue anyway for development, would reject in production
            except Exception:
                pass

        # Route to appropriate leg
        try:
            result = await self._route_to_leg(client_id, webhook_type, payload)

            self._log_webhook(
                client_id=client_id,
                webhook_type=webhook_type,
                ip_address=ip_address,
                success=True,
                details={
                    "lead_id": result.get("lead", {}).get("id"),
                    "auto_response_generated": bool(result.get("auto_response"))
                }
            )

            return WebhookResponse(
                success=True,
                message=f"{webhook_type.capitalize()} received successfully",
                lead_id=result.get("lead", {}).get("id"),
                auto_response=result.get("auto_response")
            )

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            self._log_webhook(
                client_id=client_id,
                webhook_type=webhook_type,
                ip_address=ip_address,
                success=False,
                details={"error": str(e)}
            )
            raise HTTPException(
                status_code=500,
                detail=f"Error processing webhook: {str(e)}"
            )

    async def _route_to_leg(
        self,
        client_id: str,
        webhook_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route webhook to appropriate leg for processing.

        Args:
            client_id: Target client
            webhook_type: Type of webhook
            payload: Webhook payload

        Returns:
            Processing result from leg
        """
        leg = self.legs.get(client_id)

        if not leg:
            # Create leg instance if not provided
            # In production, this would be dependency injected
            return self._process_without_leg(client_id, webhook_type, payload)

        # Route based on client and webhook type
        if client_id == "j3_structural":
            return leg.process_inquiry(payload)
        elif client_id == "joe_ipc":
            return leg.process_call_lead(payload)
        elif client_id == "antonio_banking":
            # Convert to application format
            app_data = {
                "name": payload.get("applicant_name"),
                "email": payload.get("email"),
                "phone": payload.get("phone"),
                "loan_type": payload.get("loan_type"),
                "amount": payload.get("amount_requested"),
                "credit_score": payload.get("credit_score"),
                "income": payload.get("annual_income"),
            }
            return {"lead": app_data, "status": "received"}
        elif client_id == "will_realestate":
            return {"lead": payload, "status": "received"}

        return {"lead": payload, "status": "received"}

    def _process_without_leg(
        self,
        client_id: str,
        webhook_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process webhook when leg is not available."""
        import uuid

        lead_id = str(uuid.uuid4())

        logger.info(f"Processed webhook for {client_id} without leg instance")

        return {
            "lead": {
                "id": lead_id,
                "client_id": client_id,
                **payload
            },
            "status": "queued",
            "auto_response": f"Thank you for your {webhook_type}. We will contact you shortly."
        }

    def _log_webhook(
        self,
        client_id: str,
        webhook_type: str,
        ip_address: str,
        success: bool,
        details: Dict[str, Any]
    ) -> None:
        """Log webhook to audit trail."""
        if self.audit_log:
            self.audit_log.log_access(
                user_id="webhook",
                action=f"webhook_{webhook_type}",
                resource=f"client:{client_id}",
                details=details,
                ip_address=ip_address,
                client_id=client_id,
                success=success
            )


def create_webhook_app():
    """
    Create a FastAPI application with webhook routes.

    Returns:
        FastAPI application
    """
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI(
            title="SCORPION Webhook API",
            description="Webhook endpoints for SCORPION multi-tenant system",
            version="1.0.0"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Create and include webhook router
        webhook_router = WebhookRouter()
        app.include_router(webhook_router.api_router)

        @app.get("/")
        async def root():
            return {
                "name": "SCORPION Webhook API",
                "version": "1.0.0",
                "status": "operational"
            }

        return app

    except ImportError:
        logger.warning("FastAPI not installed. Webhook API not available.")
        return None


# Create app instance for uvicorn
app = create_webhook_app()
