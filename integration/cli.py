#!/usr/bin/env python3
"""
SCORPION CLI - Command Line Interface
======================================

Unified command-line interface for all SCORPION operations.

USAGE:
    ./scorpion <command> [options]
    python -m integration.cli <command> [options]

COMMANDS:
    ask         Query an AI baby
    search      Search knowledge base
    status      Show system status
    quote       Generate J3 quote
    log-call    Log NSIPA call
    lead        Submit new lead
    babies      List available AI models
    pipeline    Show sales pipeline

EXAMPLES:
    ./scorpion ask marcus "Explain Python decorators"
    ./scorpion status --json
    ./scorpion quote framing 1500 --client "John Doe"
    ./scorpion log-call "John Smith" 555-1234 scheduled

Requirements:
    pip install rich click colorama requests
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import time

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better output: pip install rich")

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

# Configuration
API_HOST = os.environ.get("SCORPION_API_HOST", "http://localhost:8080")
API_KEY = os.environ.get("SCORPION_API_KEY", "scorpion-key")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Rich console
console = Console() if RICH_AVAILABLE else None


def print_output(message: str, style: str = None):
    """Print with optional rich styling."""
    if RICH_AVAILABLE and console:
        console.print(message, style=style)
    else:
        print(message)


def print_error(message: str):
    """Print error message."""
    print_output(f"[red]ERROR:[/red] {message}" if RICH_AVAILABLE else f"ERROR: {message}")


def print_success(message: str):
    """Print success message."""
    print_output(f"[green]✓[/green] {message}" if RICH_AVAILABLE else f"✓ {message}")


def print_warning(message: str):
    """Print warning message."""
    print_output(f"[yellow]WARNING:[/yellow] {message}" if RICH_AVAILABLE else f"WARNING: {message}")


def make_api_request(method: str, endpoint: str, data: Dict = None) -> Dict:
    """Make API request to SCORPION backend."""
    url = f"{API_HOST}{endpoint}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=120)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=120)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}

    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to SCORPION API at {API_HOST}"}
    except Exception as e:
        return {"error": str(e)}


def call_ollama_direct(baby: str, prompt: str, max_tokens: int = 500) -> Dict:
    """Call Ollama directly (fallback when API unavailable)."""
    babies = {
        "marcus": {"model": "mistral", "system": "You are MARCUS, a helpful AI assistant."},
        "hermes": {"model": "phi", "system": "You are HERMES. Give brief, direct answers."},
        "athena": {"model": "codellama", "system": "You are ATHENA, a coding expert."},
        "apollo": {"model": "llama2", "system": "You are APOLLO, a creative AI."}
    }

    config = babies.get(baby, babies["marcus"])
    full_prompt = f"{config['system']}\n\nUser: {prompt}\n\nAssistant:"

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": config["model"],
                "prompt": full_prompt,
                "stream": False,
                "options": {"num_predict": max_tokens}
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            return {"success": True, "response": result.get("response", "").strip()}
        else:
            return {"error": f"Ollama error: {response.status_code}"}

    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to Ollama at {OLLAMA_HOST}"}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# COMMANDS
# =============================================================================

def cmd_ask(args):
    """Query an AI baby."""
    baby = args.baby.lower()
    prompt = " ".join(args.prompt)

    if not prompt:
        print_error("Please provide a prompt")
        return 1

    print_output(f"\n[bold]Asking {baby.upper()}...[/bold]" if RICH_AVAILABLE else f"\nAsking {baby.upper()}...")

    # Try API first, fallback to direct Ollama
    if RICH_AVAILABLE:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                     console=console, transient=True) as progress:
            progress.add_task("Thinking...", total=None)
            result = make_api_request("POST", "/ask", {
                "baby": baby,
                "prompt": prompt,
                "context": args.context,
                "max_tokens": args.max_tokens
            })

            if "error" in result and "Cannot connect" in result["error"]:
                result = call_ollama_direct(baby, prompt, args.max_tokens)
    else:
        print("Thinking...")
        result = make_api_request("POST", "/ask", {
            "baby": baby,
            "prompt": prompt,
            "context": args.context,
            "max_tokens": args.max_tokens
        })
        if "error" in result and "Cannot connect" in result["error"]:
            result = call_ollama_direct(baby, prompt, args.max_tokens)

    if "error" in result:
        print_error(result["error"])
        return 1

    # Display response
    response = result.get("response", "No response")

    if RICH_AVAILABLE:
        panel = Panel(
            Markdown(response),
            title=f"[bold cyan]{baby.upper()}[/bold cyan]",
            border_style="cyan"
        )
        console.print(panel)
    else:
        print(f"\n{baby.upper()}:\n{'-' * 40}\n{response}\n")

    return 0


def cmd_status(args):
    """Show system status."""
    result = make_api_request("GET", "/status")

    if "error" in result:
        # Try checking services directly
        result = {
            "status": "checking",
            "ollama": check_service(OLLAMA_HOST, "/api/tags"),
            "api": check_service(API_HOST, "/health")
        }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    # Display status table
    if RICH_AVAILABLE:
        table = Table(title="SCORPION Status", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")

        # API
        api_status = "🟢 Online" if result.get("status") == "online" else "🔴 Offline"
        table.add_row("MOUTH API", api_status, API_HOST)

        # Ollama
        components = result.get("components", {})
        ollama_info = components.get("ollama", {})
        ollama_status = "🟢 Online" if ollama_info.get("status") == "online" else "🔴 Offline"
        table.add_row("Ollama", ollama_status, ollama_info.get("host", OLLAMA_HOST))

        # Babies
        babies = components.get("babies", {})
        for baby, info in babies.items():
            status = "🟢" if info.get("available") else "🔴"
            table.add_row(f"  {baby.upper()}", status, info.get("model", ""))

        # Modules
        modules = result.get("modules", {})
        for module, status in modules.items():
            icon = "🟢" if status == "available" else "⚪"
            table.add_row(f"Module: {module}", icon, status)

        console.print(table)
    else:
        print("\nSCORPION Status")
        print("=" * 40)
        print(f"API: {result.get('status', 'unknown')}")
        print(json.dumps(result, indent=2))

    return 0


def check_service(host: str, endpoint: str) -> str:
    """Check if a service is responding."""
    try:
        response = requests.get(f"{host}{endpoint}", timeout=5)
        return "online" if response.status_code == 200 else "error"
    except:
        return "offline"


def cmd_babies(args):
    """List available AI babies."""
    result = make_api_request("GET", "/babies")

    if "error" in result:
        # Try Ollama directly
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                result = {
                    "marcus": {"model": "mistral", "available": any("mistral" in m["name"] for m in models)},
                    "hermes": {"model": "phi", "available": any("phi" in m["name"] for m in models)},
                    "athena": {"model": "codellama", "available": any("codellama" in m["name"] for m in models)},
                    "apollo": {"model": "llama2", "available": any("llama2" in m["name"] for m in models)}
                }
        except:
            print_error("Cannot connect to services")
            return 1

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    if RICH_AVAILABLE:
        table = Table(title="Available AI Babies", show_header=True)
        table.add_column("Baby", style="cyan bold")
        table.add_column("Model")
        table.add_column("Status")
        table.add_column("Description")

        descriptions = {
            "marcus": "Main assistant - balanced and helpful",
            "hermes": "Fast responder - quick answers",
            "athena": "Code specialist - programming help",
            "apollo": "Creative writer - content generation"
        }

        for baby, info in result.items():
            status = "🟢 Ready" if info.get("available") else "🔴 Unavailable"
            table.add_row(baby.upper(), info.get("model", ""), status, descriptions.get(baby, ""))

        console.print(table)
    else:
        print("\nAvailable AI Babies:")
        for baby, info in result.items():
            status = "Ready" if info.get("available") else "Unavailable"
            print(f"  {baby.upper()}: {info.get('model')} ({status})")

    return 0


def cmd_quote(args):
    """Generate a J3 construction quote."""
    result = make_api_request("POST", "/quote", {
        "job_type": args.job_type,
        "sqft": args.sqft,
        "materials": args.materials,
        "client_name": args.client or "",
        "client_email": args.email or "",
        "client_phone": args.phone or "",
        "client_address": args.address or ""
    })

    if "error" in result:
        # Try local module
        try:
            from j3.quote_generator import QuoteGenerator
            gen = QuoteGenerator()
            estimate = gen.calculate_estimate(args.job_type, args.sqft, materials=args.materials)
            result = {"success": True, "estimate": estimate}
        except Exception as e:
            print_error(f"Quote generation failed: {e}")
            return 1

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    estimate = result.get("estimate", result)

    if RICH_AVAILABLE:
        table = Table(title=f"Quote: {estimate.get('job_name', args.job_type)}", show_header=False)
        table.add_column("Item", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Job Type", estimate.get("job_name", args.job_type))
        table.add_row("Square Footage", f"{args.sqft:,} sqft")
        table.add_row("Materials", args.materials.title())
        table.add_row("", "")
        table.add_row("Labor", f"${estimate.get('labor_cost', 0):,.2f}")
        table.add_row("Materials", f"${estimate.get('materials_cost', 0):,.2f}")
        table.add_row("Subtotal", f"${estimate.get('subtotal', 0):,.2f}")
        table.add_row("Tax", f"${estimate.get('tax_amount', 0):,.2f}")
        table.add_row("[bold]TOTAL[/bold]", f"[bold green]${estimate.get('total', 0):,.2f}[/bold green]")
        table.add_row("", "")
        table.add_row("Est. Duration", estimate.get("estimated_duration", "TBD"))

        console.print(table)
    else:
        print(f"\nQuote: {estimate.get('job_name', args.job_type)}")
        print(f"  Sqft: {args.sqft}")
        print(f"  Labor: ${estimate.get('labor_cost', 0):,.2f}")
        print(f"  Materials: ${estimate.get('materials_cost', 0):,.2f}")
        print(f"  TOTAL: ${estimate.get('total', 0):,.2f}")

    return 0


def cmd_log_call(args):
    """Log an NSIPA scheduling call."""
    result = make_api_request("POST", "/log-call", {
        "patient_name": args.patient_name,
        "patient_phone": args.phone,
        "outcome": args.outcome,
        "notes": args.notes or "",
        "duration_seconds": args.duration or 0,
        "appointment_date": args.appointment_date,
        "appointment_time": args.appointment_time
    })

    if "error" in result:
        # Try local module
        try:
            from nsipa.call_logger import CallLogger
            logger = CallLogger()
            record = logger.log_call(
                patient_name=args.patient_name,
                patient_phone=args.phone,
                outcome=args.outcome,
                notes=args.notes or "",
                duration_seconds=args.duration or 0,
                appointment_date=args.appointment_date,
                appointment_time=args.appointment_time
            )
            result = {"success": True, "call_id": record.id}
        except Exception as e:
            print_error(f"Call logging failed: {e}")
            return 1

    if result.get("success"):
        print_success(f"Call logged: {result.get('call_id', 'OK')}")
    else:
        print_error(result.get("error", "Unknown error"))
        return 1

    return 0


def cmd_lead(args):
    """Submit a new lead."""
    result = make_api_request("POST", "/lead", {
        "name": args.name,
        "email": args.email,
        "phone": args.phone or "",
        "company": args.company or "",
        "message": args.message or "",
        "source": args.source
    })

    if "error" in result:
        # Try local module
        try:
            from claw1.sales.lead_capture import LeadCapture
            capture = LeadCapture()
            lead = capture.process_form({
                "name": args.name,
                "email": args.email,
                "phone": args.phone or "",
                "company": args.company or "",
                "message": args.message or ""
            }, source=args.source)
            result = {"success": True, "lead_id": lead.id, "score": lead.score, "priority": lead.priority}
        except Exception as e:
            print_error(f"Lead submission failed: {e}")
            return 1

    if result.get("success"):
        if RICH_AVAILABLE:
            console.print(Panel(
                f"Lead ID: {result.get('lead_id')}\n"
                f"Score: {result.get('score', 0)}/100\n"
                f"Priority: {result.get('priority', 0)}/10\n"
                f"Assigned: {result.get('assigned_leg', 'pending')}",
                title="Lead Captured",
                border_style="green"
            ))
        else:
            print_success(f"Lead captured: {result.get('lead_id')}")
            print(f"  Score: {result.get('score')}, Priority: {result.get('priority')}")
    else:
        print_error(result.get("error", "Unknown error"))
        return 1

    return 0


def cmd_search(args):
    """Search knowledge base."""
    query = " ".join(args.query)

    result = make_api_request("POST", "/knowledge", {
        "query": query,
        "n_results": args.limit
    })

    if "error" in result:
        print_error(result["error"])
        return 1

    results = result.get("results", [])

    if not results:
        print_warning("No results found")
        return 0

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    if RICH_AVAILABLE:
        for i, item in enumerate(results, 1):
            console.print(Panel(
                item.get("document", "")[:500] + "..." if len(item.get("document", "")) > 500 else item.get("document", ""),
                title=f"Result {i}",
                subtitle=f"Score: {item.get('distance', 'N/A')}"
            ))
    else:
        for i, item in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(item.get("document", "")[:500])

    return 0


def cmd_pipeline(args):
    """Show sales pipeline."""
    result = make_api_request("GET", "/pipeline")

    if "error" in result:
        # Try local module
        try:
            from claw1.crm.pipeline import Pipeline
            pipeline = Pipeline()
            result = {
                "success": True,
                "pipeline": pipeline.get_pipeline_view(),
                "stats": pipeline.get_pipeline_stats()
            }
        except Exception as e:
            print_error(f"Pipeline fetch failed: {e}")
            return 1

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    stats = result.get("stats", {})
    pipeline = result.get("pipeline", {})

    if RICH_AVAILABLE:
        # Summary
        console.print(Panel(
            f"Active Deals: {stats.get('active_deals', 0)}\n"
            f"Active Value: ${stats.get('active_value', 0):,.2f}\n"
            f"Weighted Pipeline: ${stats.get('weighted_pipeline', 0):,.2f}\n"
            f"Win Rate: {stats.get('win_rate', 0)}%",
            title="Pipeline Summary",
            border_style="blue"
        ))

        # Stages
        table = Table(title="Pipeline Stages", show_header=True)
        table.add_column("Stage", style="cyan")
        table.add_column("Deals", justify="right")
        table.add_column("Value", justify="right")

        for stage in ["new", "contacted", "quoted", "negotiating", "closed", "lost"]:
            deals = pipeline.get(stage, [])
            value = sum(d.get("value", 0) for d in deals)
            table.add_row(stage.upper(), str(len(deals)), f"${value:,.2f}")

        console.print(table)
    else:
        print("\nPipeline Summary:")
        print(f"  Active Value: ${stats.get('active_value', 0):,.2f}")
        print(f"  Win Rate: {stats.get('win_rate', 0)}%")

    return 0


# =============================================================================
# MAIN
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="scorpion",
        description="SCORPION CLI - Command-line interface for the SCORPION AI ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ask marcus "Explain Python decorators"
  %(prog)s status --json
  %(prog)s quote framing 1500 --materials premium
  %(prog)s log-call "John Smith" 555-1234 scheduled
  %(prog)s lead "Jane Doe" jane@email.com --company "Acme Inc"
  %(prog)s babies
  %(prog)s pipeline

Environment Variables:
  SCORPION_API_HOST   API host (default: http://localhost:8080)
  SCORPION_API_KEY    API key for authentication
  OLLAMA_HOST         Ollama host (default: http://localhost:11434)
        """
    )

    parser.add_argument("--version", action="version", version="SCORPION CLI 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ask
    ask_parser = subparsers.add_parser("ask", help="Query an AI baby")
    ask_parser.add_argument("baby", help="Baby name (marcus, hermes, athena, apollo)")
    ask_parser.add_argument("prompt", nargs="+", help="Your question")
    ask_parser.add_argument("--context", "-c", help="Additional context")
    ask_parser.add_argument("--max-tokens", "-m", type=int, default=500)
    ask_parser.set_defaults(func=cmd_ask)

    # status
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    status_parser.set_defaults(func=cmd_status)

    # babies
    babies_parser = subparsers.add_parser("babies", help="List available AI babies")
    babies_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    babies_parser.set_defaults(func=cmd_babies)

    # quote
    quote_parser = subparsers.add_parser("quote", help="Generate J3 quote")
    quote_parser.add_argument("job_type", help="Job type (framing, drywall, full_remodel, etc.)")
    quote_parser.add_argument("sqft", type=float, help="Square footage")
    quote_parser.add_argument("--materials", "-m", default="standard", help="Material grade")
    quote_parser.add_argument("--client", help="Client name")
    quote_parser.add_argument("--email", help="Client email")
    quote_parser.add_argument("--phone", help="Client phone")
    quote_parser.add_argument("--address", help="Client address")
    quote_parser.add_argument("--json", "-j", action="store_true")
    quote_parser.set_defaults(func=cmd_quote)

    # log-call
    call_parser = subparsers.add_parser("log-call", help="Log NSIPA call")
    call_parser.add_argument("patient_name", help="Patient name")
    call_parser.add_argument("phone", help="Phone number")
    call_parser.add_argument("outcome", help="Outcome (scheduled, voicemail, no_answer, declined, callback)")
    call_parser.add_argument("--notes", "-n", help="Call notes")
    call_parser.add_argument("--duration", "-d", type=int, help="Duration in seconds")
    call_parser.add_argument("--appointment-date", help="Appointment date (YYYY-MM-DD)")
    call_parser.add_argument("--appointment-time", help="Appointment time (HH:MM)")
    call_parser.set_defaults(func=cmd_log_call)

    # lead
    lead_parser = subparsers.add_parser("lead", help="Submit new lead")
    lead_parser.add_argument("name", help="Lead name")
    lead_parser.add_argument("email", help="Email address")
    lead_parser.add_argument("--phone", "-p", help="Phone number")
    lead_parser.add_argument("--company", "-c", help="Company name")
    lead_parser.add_argument("--message", "-m", help="Message/inquiry")
    lead_parser.add_argument("--source", "-s", default="cli", help="Lead source")
    lead_parser.set_defaults(func=cmd_lead)

    # search
    search_parser = subparsers.add_parser("search", help="Search knowledge base")
    search_parser.add_argument("query", nargs="+", help="Search query")
    search_parser.add_argument("--limit", "-l", type=int, default=5, help="Number of results")
    search_parser.add_argument("--json", "-j", action="store_true")
    search_parser.set_defaults(func=cmd_search)

    # pipeline
    pipeline_parser = subparsers.add_parser("pipeline", help="Show sales pipeline")
    pipeline_parser.add_argument("--json", "-j", action="store_true")
    pipeline_parser.set_defaults(func=cmd_pipeline)

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if RICH_AVAILABLE:
        console.print("\n[bold cyan]🦂 SCORPION CLI[/bold cyan]", justify="center")

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
