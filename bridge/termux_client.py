#!/usr/bin/env python3
"""
SCORPION Bridge - Termux Client
===============================

Simple client to query your Linux AI babies from Android Termux.
Run this on your phone after setting up Termux.

Requirements:
    pkg install python
    pip install requests

Usage:
    python termux_client.py ask marcus "What is Python?"
    python termux_client.py quick "Summarize this quickly"
    python termux_client.py status
    python termux_client.py babies

Setup:
    1. Set your server IP: export BRIDGE_HOST="192.168.1.100"
    2. Set API key if needed: export BRIDGE_API_KEY="your-key"
"""

import os
import sys
import json
import argparse
from typing import Optional

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)

# Configuration
BRIDGE_HOST = os.environ.get("BRIDGE_HOST", "localhost")
BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", 9876))
API_KEY = os.environ.get("BRIDGE_API_KEY", "scorpion-default-key")

BASE_URL = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}"


def get_headers():
    """Get request headers with API key."""
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }


def ask_baby(baby: str, prompt: str, context: str = None, max_tokens: int = 500) -> str:
    """
    Ask a specific baby a question.

    Args:
        baby: Baby name (marcus, hermes, athena, apollo)
        prompt: Your question
        context: Optional context
        max_tokens: Maximum response length

    Returns:
        AI response text
    """
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            headers=get_headers(),
            json={
                "baby": baby,
                "prompt": prompt,
                "context": context,
                "max_tokens": max_tokens
            },
            timeout=120
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("response", "No response")
            else:
                return f"Error: {data.get('error', 'Unknown error')}"
        else:
            return f"HTTP Error: {response.status_code}"

    except requests.exceptions.ConnectionError:
        return f"Cannot connect to server at {BASE_URL}"
    except Exception as e:
        return f"Error: {str(e)}"


def quick_ask(prompt: str, max_tokens: int = 200) -> str:
    """
    Quick ask using HERMES (fastest).

    Args:
        prompt: Your question
        max_tokens: Maximum response length

    Returns:
        AI response text
    """
    try:
        response = requests.post(
            f"{BASE_URL}/quick",
            headers=get_headers(),
            json={
                "prompt": prompt,
                "max_tokens": max_tokens
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("response", "No response")
            else:
                return f"Error: {data.get('error', 'Unknown error')}"
        else:
            return f"HTTP Error: {response.status_code}"

    except requests.exceptions.ConnectionError:
        return f"Cannot connect to server at {BASE_URL}"
    except Exception as e:
        return f"Error: {str(e)}"


def search_knowledge(query: str, n_results: int = 5) -> list:
    """
    Search the knowledge base.

    Args:
        query: Search query
        n_results: Number of results

    Returns:
        List of results
    """
    try:
        response = requests.post(
            f"{BASE_URL}/knowledge",
            headers=get_headers(),
            json={
                "query": query,
                "n_results": n_results
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("results", [])
            else:
                print(f"Error: {data.get('error', 'Unknown error')}")
                return []
        else:
            print(f"HTTP Error: {response.status_code}")
            return []

    except Exception as e:
        print(f"Error: {str(e)}")
        return []


def check_status() -> dict:
    """
    Check server status.

    Returns:
        Status dictionary
    """
    try:
        response = requests.get(
            f"{BASE_URL}/status",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}

    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to {BASE_URL}"}
    except Exception as e:
        return {"error": str(e)}


def list_babies() -> dict:
    """
    List available babies.

    Returns:
        Babies dictionary
    """
    try:
        response = requests.get(
            f"{BASE_URL}/babies",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}


def interactive_mode():
    """Run interactive chat mode."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              SCORPION BRIDGE - INTERACTIVE MODE              ║
╠══════════════════════════════════════════════════════════════╣
║  Connected to: {BASE_URL:<42} ║
║  Commands:                                                    ║
║    /baby <name>  - Switch baby (marcus, hermes, athena, apollo)║
║    /status       - Check server status                        ║
║    /quit         - Exit                                       ║
╚══════════════════════════════════════════════════════════════╝
    """)

    current_baby = "marcus"

    while True:
        try:
            prompt = input(f"[{current_baby.upper()}] > ").strip()

            if not prompt:
                continue

            if prompt.lower() == "/quit":
                print("Goodbye!")
                break

            elif prompt.lower() == "/status":
                status = check_status()
                print(json.dumps(status, indent=2))

            elif prompt.lower().startswith("/baby "):
                new_baby = prompt[6:].strip().lower()
                babies = ["marcus", "hermes", "athena", "apollo"]
                if new_baby in babies:
                    current_baby = new_baby
                    print(f"Switched to {current_baby.upper()}")
                else:
                    print(f"Unknown baby. Available: {', '.join(babies)}")

            else:
                print("Thinking...")
                response = ask_baby(current_baby, prompt)
                print(f"\n{response}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SCORPION Bridge - Query AI babies from Termux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python termux_client.py ask marcus "What is Python?"
  python termux_client.py quick "Give me a quick answer"
  python termux_client.py status
  python termux_client.py interactive

Environment Variables:
  BRIDGE_HOST     Server IP address (default: localhost)
  BRIDGE_PORT     Server port (default: 9876)
  BRIDGE_API_KEY  API key for authentication
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a baby a question")
    ask_parser.add_argument("baby", help="Baby name (marcus, hermes, athena, apollo)")
    ask_parser.add_argument("prompt", help="Your question")
    ask_parser.add_argument("--context", "-c", help="Optional context")
    ask_parser.add_argument("--max-tokens", "-m", type=int, default=500)

    # quick command
    quick_parser = subparsers.add_parser("quick", help="Quick ask (uses HERMES)")
    quick_parser.add_argument("prompt", help="Your question")
    quick_parser.add_argument("--max-tokens", "-m", type=int, default=200)

    # search command
    search_parser = subparsers.add_parser("search", help="Search knowledge base")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--results", "-n", type=int, default=5)

    # status command
    subparsers.add_parser("status", help="Check server status")

    # babies command
    subparsers.add_parser("babies", help="List available babies")

    # interactive command
    subparsers.add_parser("interactive", help="Interactive chat mode")

    args = parser.parse_args()

    if not args.command:
        # If no command, check if there's a single argument (quick mode)
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            prompt = " ".join(sys.argv[1:])
            print(f"Quick ask: {prompt}")
            print("-" * 40)
            response = quick_ask(prompt)
            print(response)
        else:
            parser.print_help()
        return

    if args.command == "ask":
        response = ask_baby(
            args.baby,
            args.prompt,
            context=args.context,
            max_tokens=args.max_tokens
        )
        print(response)

    elif args.command == "quick":
        response = quick_ask(args.prompt, max_tokens=args.max_tokens)
        print(response)

    elif args.command == "search":
        results = search_knowledge(args.query, n_results=args.results)
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"ID: {result.get('id')}")
            if result.get('document'):
                print(f"Content: {result['document'][:200]}...")
            if result.get('metadata'):
                print(f"Metadata: {result['metadata']}")

    elif args.command == "status":
        status = check_status()
        print(json.dumps(status, indent=2))

    elif args.command == "babies":
        babies = list_babies()
        for name, info in babies.items():
            print(f"\n{name.upper()}")
            print(f"  Model: {info.get('model')}")
            print(f"  Description: {info.get('description')}")

    elif args.command == "interactive":
        interactive_mode()


if __name__ == "__main__":
    main()
