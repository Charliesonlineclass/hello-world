#!/usr/bin/env python3
"""
Quick Ask - One-liner to query a SCORPION AI baby.

Usage:
    python scripts/quick_ask.py "What is Python?"
    python scripts/quick_ask.py "Explain machine learning" --baby LUNA
    python scripts/quick_ask.py "Write a haiku about coding" --baby NOVA
"""

import argparse
import sys
import json
from typing import Optional

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    sys.exit(1)


DEFAULT_BABY = "MARCUS"
API_BASE = "http://localhost:8000/api"


def query_baby(question: str, baby: str = DEFAULT_BABY) -> dict:
    """
    Send a query to a SCORPION AI baby.

    Args:
        question: The question to ask
        baby: Name of the baby to query (MARCUS, LUNA, NOVA, ATLAS, SAGE)

    Returns:
        Response from the baby
    """
    url = f"{API_BASE}/babies/{baby.lower()}/query"

    payload = {
        "query": question,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to SCORPION API. Is the server running?"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. The query may be too complex."}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def format_response(response: dict) -> str:
    """Format the response for display."""
    if "error" in response:
        return f"Error: {response['error']}"

    answer = response.get("response", response.get("answer", "No response received."))
    baby = response.get("baby", "UNKNOWN")
    tokens = response.get("tokens_used", "N/A")

    output = f"\n{'='*60}\n"
    output += f" {baby} says:\n"
    output += f"{'='*60}\n\n"
    output += f"{answer}\n\n"
    output += f"{'='*60}\n"
    output += f"Tokens used: {tokens}\n"

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Quick Ask - Query a SCORPION AI baby",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Babies:
  MARCUS  - General assistant, great for business questions
  LUNA    - Data analysis and insights
  NOVA    - Creative writing and content
  ATLAS   - Research and information gathering
  SAGE    - Code expert and technical questions

Examples:
  python scripts/quick_ask.py "What is Python?"
  python scripts/quick_ask.py "Analyze sales trends" --baby LUNA
  python scripts/quick_ask.py "Write a poem about automation" --baby NOVA
        """
    )

    parser.add_argument(
        "question",
        help="The question to ask the AI baby"
    )

    parser.add_argument(
        "--baby", "-b",
        default=DEFAULT_BABY,
        choices=["MARCUS", "LUNA", "NOVA", "ATLAS", "SAGE"],
        help=f"Which AI baby to ask (default: {DEFAULT_BABY})"
    )

    parser.add_argument(
        "--raw", "-r",
        action="store_true",
        help="Output raw JSON response"
    )

    args = parser.parse_args()

    print(f"\nAsking {args.baby}: {args.question}\n")

    response = query_baby(args.question, args.baby)

    if args.raw:
        print(json.dumps(response, indent=2))
    else:
        print(format_response(response))


if __name__ == "__main__":
    main()
