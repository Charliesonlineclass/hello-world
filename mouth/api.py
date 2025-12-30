"""
SCORPION MOUTH - Dashboard API
===============================

FastAPI backend providing unified access to all SCORPION components.

Endpoints:
    GET  /              - API info
    GET  /status        - System status
    GET  /babies        - Available AI babies
    GET  /stats         - System statistics

    POST /ask           - Query AI babies
    POST /quote         - Generate J3 quote
    POST /log-call      - Log NSIPA call
    POST /lead          - Submit lead

Requirements:
    pip install fastapi uvicorn requests
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging
import requests

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, HTTPException, Header, Depends, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn")
    FastAPI = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MOUTH.api")

# Configuration
API_PORT = int(os.environ.get("MOUTH_PORT", 8000))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
API_KEY = os.environ.get("SCORPION_API_KEY", "scorpion-key")

# AI Baby configurations
BABIES = {
    "marcus": {"model": "mistral", "description": "Main assistant"},
    "hermes": {"model": "phi", "description": "Fast responder"},
    "athena": {"model": "codellama", "description": "Code specialist"},
    "apollo": {"model": "llama2", "description": "Creative writer"}
}


# Request/Response Models
class AskRequest(BaseModel):
    baby: str = "marcus"
    prompt: str
    context: Optional[str] = None
    max_tokens: int = 500


class AskResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    baby: str = ""
    elapsed: float = 0
    error: Optional[str] = None


class QuoteRequest(BaseModel):
    job_type: str
    sqft: float
    materials: str = "standard"
    client_name: str = ""
    client_email: str = ""
    client_phone: str = ""
    client_address: str = ""


class CallLogRequest(BaseModel):
    patient_name: str
    patient_phone: str
    outcome: str
    notes: str = ""
    duration_seconds: int = 0
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None


class LeadRequest(BaseModel):
    name: str
    email: str
    phone: str = ""
    company: str = ""
    message: str = ""
    source: str = "website"


class StatsResponse(BaseModel):
    system: Dict[str, Any]
    leads: Optional[Dict] = None
    pipeline: Optional[Dict] = None
    calls: Optional[Dict] = None
    courses: Optional[Dict] = None


# Create FastAPI app
if FastAPI:
    app = FastAPI(
        title="SCORPION MOUTH API",
        description="Unified dashboard API for the SCORPION ecosystem",
        version="1.0.0"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # API Key verification
    def verify_api_key(x_api_key: str = Header(None)):
        """Verify API key from header."""
        if API_KEY != "scorpion-key" and x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return True

    # Health check helper
    def check_ollama() -> bool:
        """Check if Ollama is running."""
        try:
            resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            return resp.status_code == 200
        except:
            return False

    def get_available_models() -> List[str]:
        """Get list of available Ollama models."""
        try:
            resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if resp.status_code == 200:
                return [m["name"] for m in resp.json().get("models", [])]
        except:
            pass
        return []

    # ===== ENDPOINTS =====

    @app.get("/")
    async def root():
        """API information."""
        return {
            "name": "SCORPION MOUTH API",
            "version": "1.0.0",
            "status": "online",
            "docs": "/docs",
            "endpoints": {
                "status": "GET /status",
                "babies": "GET /babies",
                "stats": "GET /stats",
                "ask": "POST /ask",
                "quote": "POST /quote",
                "log_call": "POST /log-call",
                "lead": "POST /lead"
            }
        }

    @app.get("/status")
    async def status():
        """
        Get system status.

        Returns status of all SCORPION components.
        """
        available_models = get_available_models()

        babies_status = {}
        for name, config in BABIES.items():
            is_available = any(config["model"] in m for m in available_models)
            babies_status[name] = {
                "model": config["model"],
                "available": is_available
            }

        return {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "mouth": {"status": "online", "port": API_PORT},
                "ollama": {"status": "online" if check_ollama() else "offline", "host": OLLAMA_HOST},
                "babies": babies_status
            },
            "modules": {
                "otter": _check_module("otter"),
                "bridge": _check_module("bridge"),
                "j3": _check_module("j3"),
                "nsipa": _check_module("nsipa"),
                "claw1": _check_module("claw1"),
                "claw2": _check_module("claw2"),
                "tail": _check_module("tail")
            }
        }

    def _check_module(name: str) -> str:
        """Check if a module is available."""
        try:
            __import__(name)
            return "available"
        except ImportError:
            return "not_installed"

    @app.get("/babies")
    async def list_babies():
        """
        List available AI babies.

        Returns configuration for each baby.
        """
        available_models = get_available_models()

        result = {}
        for name, config in BABIES.items():
            is_available = any(config["model"] in m for m in available_models)
            result[name] = {
                **config,
                "available": is_available
            }

        return result

    @app.get("/stats")
    async def get_stats(
        include_leads: bool = True,
        include_pipeline: bool = True,
        include_calls: bool = True,
        include_courses: bool = True
    ):
        """
        Get system statistics.

        Args:
            include_leads: Include lead capture stats
            include_pipeline: Include pipeline stats
            include_calls: Include call log stats
            include_courses: Include LCMS stats
        """
        stats = {
            "system": {
                "timestamp": datetime.now().isoformat(),
                "ollama_online": check_ollama(),
                "available_models": len(get_available_models())
            },
            "leads": None,
            "pipeline": None,
            "calls": None,
            "courses": None
        }

        # Lead stats
        if include_leads:
            try:
                from claw1.sales.lead_capture import LeadCapture
                capture = LeadCapture()
                stats["leads"] = capture.get_stats()
            except Exception as e:
                stats["leads"] = {"error": str(e)}

        # Pipeline stats
        if include_pipeline:
            try:
                from claw1.crm.pipeline import Pipeline
                pipeline = Pipeline()
                stats["pipeline"] = pipeline.get_pipeline_stats()
            except Exception as e:
                stats["pipeline"] = {"error": str(e)}

        # Call stats
        if include_calls:
            try:
                from nsipa.call_logger import CallLogger
                call_logger = CallLogger()
                stats["calls"] = call_logger.daily_summary()
            except Exception as e:
                stats["calls"] = {"error": str(e)}

        # Course stats
        if include_courses:
            try:
                from claw2.lcms.course_manager import CourseManager
                manager = CourseManager()
                stats["courses"] = manager.get_stats()
            except Exception as e:
                stats["courses"] = {"error": str(e)}

        return stats

    @app.post("/ask", response_model=AskResponse)
    async def ask_baby(request: AskRequest, _: bool = Depends(verify_api_key)):
        """
        Query an AI baby.

        Args:
            baby: Which baby to query (marcus, hermes, athena, apollo)
            prompt: User prompt
            context: Optional context
            max_tokens: Maximum response tokens
        """
        import time

        if request.baby not in BABIES:
            return AskResponse(
                success=False,
                error=f"Unknown baby: {request.baby}. Available: {list(BABIES.keys())}"
            )

        baby_config = BABIES[request.baby]
        start = time.time()

        # Build prompt
        system_prompts = {
            "marcus": "You are MARCUS, a helpful AI assistant. Be concise and practical.",
            "hermes": "You are HERMES, a fast AI. Give brief, direct answers.",
            "athena": "You are ATHENA, a coding expert. Help with programming tasks.",
            "apollo": "You are APOLLO, a creative AI. Help with writing and content."
        }

        full_prompt = system_prompts.get(request.baby, "")
        if request.context:
            full_prompt += f"\n\nContext: {request.context}"
        full_prompt += f"\n\nUser: {request.prompt}\n\nAssistant:"

        try:
            resp = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": baby_config["model"],
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"num_predict": request.max_tokens}
                },
                timeout=120
            )

            if resp.status_code == 200:
                result = resp.json()
                return AskResponse(
                    success=True,
                    response=result.get("response", "").strip(),
                    baby=request.baby,
                    elapsed=round(time.time() - start, 2)
                )
            else:
                return AskResponse(
                    success=False,
                    error=f"Ollama error: {resp.status_code}"
                )

        except requests.exceptions.ConnectionError:
            return AskResponse(
                success=False,
                error=f"Cannot connect to Ollama at {OLLAMA_HOST}"
            )
        except Exception as e:
            return AskResponse(success=False, error=str(e))

    @app.post("/quote")
    async def generate_quote(request: QuoteRequest, _: bool = Depends(verify_api_key)):
        """
        Generate a J3 construction quote.

        Args:
            job_type: Type of job (framing, drywall, full_remodel, etc.)
            sqft: Square footage
            materials: Material grade (standard, premium)
            client_*: Client information
        """
        try:
            from j3.quote_generator import QuoteGenerator

            gen = QuoteGenerator()
            estimate = gen.calculate_estimate(
                job_type=request.job_type,
                sqft=request.sqft,
                materials=request.materials
            )

            # Create quote if client info provided
            if request.client_name and request.client_email:
                client_info = {
                    "name": request.client_name,
                    "email": request.client_email,
                    "phone": request.client_phone,
                    "address": request.client_address
                }
                quote = gen.create_quote(client_info, estimate)
                pdf_path = gen.generate_quote_pdf(quote)
                estimate["quote_number"] = quote.quote_number
                estimate["pdf_path"] = str(pdf_path)

            return {
                "success": True,
                "estimate": estimate
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/log-call")
    async def log_call(request: CallLogRequest, _: bool = Depends(verify_api_key)):
        """
        Log an NSIPA scheduling call.

        Args:
            patient_name: Patient name
            patient_phone: Phone number
            outcome: Call outcome (scheduled, voicemail, no_answer, etc.)
            notes: Call notes
            duration_seconds: Call duration
        """
        try:
            from nsipa.call_logger import CallLogger

            logger = CallLogger()
            record = logger.log_call(
                patient_name=request.patient_name,
                patient_phone=request.patient_phone,
                outcome=request.outcome,
                notes=request.notes,
                duration_seconds=request.duration_seconds,
                appointment_date=request.appointment_date,
                appointment_time=request.appointment_time
            )

            return {
                "success": True,
                "call_id": record.id,
                "outcome": request.outcome
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/lead")
    async def submit_lead(request: LeadRequest, _: bool = Depends(verify_api_key)):
        """
        Submit a new lead.

        Args:
            name: Lead name
            email: Email address
            phone: Phone number
            company: Company name
            message: Message/inquiry
            source: Lead source
        """
        try:
            from claw1.sales.lead_capture import LeadCapture

            capture = LeadCapture()
            lead = capture.process_form({
                "name": request.name,
                "email": request.email,
                "phone": request.phone,
                "company": request.company,
                "message": request.message
            }, source=request.source)

            return {
                "success": True,
                "lead_id": lead.id,
                "score": lead.score,
                "priority": lead.priority,
                "assigned_leg": lead.assigned_leg
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/pipeline")
    async def get_pipeline(_: bool = Depends(verify_api_key)):
        """Get sales pipeline view."""
        try:
            from claw1.crm.pipeline import Pipeline

            pipeline = Pipeline()
            return {
                "success": True,
                "pipeline": pipeline.get_pipeline_view(),
                "stats": pipeline.get_pipeline_stats()
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }

else:
    app = None


def start_server(host: str = "0.0.0.0", port: int = API_PORT):
    """Start the SCORPION MOUTH API server."""
    if app is None:
        print("FastAPI not available. Install with: pip install fastapi uvicorn")
        return

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  SCORPION MOUTH API                           ║
╠══════════════════════════════════════════════════════════════╣
║  Server: http://{host}:{port}                               ║
║  Docs:   http://{host}:{port}/docs                          ║
║  Status: http://{host}:{port}/status                        ║
╠══════════════════════════════════════════════════════════════╣
║  Endpoints:                                                   ║
║    GET  /status      System status                           ║
║    GET  /babies      List AI babies                          ║
║    GET  /stats       System statistics                       ║
║    GET  /pipeline    Sales pipeline                          ║
║    POST /ask         Query AI baby                           ║
║    POST /quote       Generate J3 quote                       ║
║    POST /log-call    Log NSIPA call                          ║
║    POST /lead        Submit new lead                         ║
╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import sys

    port = API_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    start_server(port=port)
