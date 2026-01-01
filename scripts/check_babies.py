#!/usr/bin/env python3
"""
Check Babies - Check which SCORPION AI babies are online.

Usage:
    python scripts/check_babies.py
    python scripts/check_babies.py --detailed
"""

import argparse
import sys

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    sys.exit(1)


API_BASE = "http://localhost:8000/api"

BABIES = [
    {"name": "MARCUS", "role": "General Assistant", "specialty": "Business & Strategy"},
    {"name": "LUNA", "role": "Data Analyst", "specialty": "Analytics & Insights"},
    {"name": "NOVA", "role": "Creative Writer", "specialty": "Content & Marketing"},
    {"name": "ATLAS", "role": "Research Expert", "specialty": "Research & Knowledge"},
    {"name": "SAGE", "role": "Code Expert", "specialty": "Development & Tech"},
]


def check_baby_status(name: str) -> dict:
    """Check if a specific baby is online."""
    url = f"{API_BASE}/babies/{name.lower()}/health"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "online": True,
                "status": data.get("status", "healthy"),
                "model": data.get("model", "unknown"),
                "uptime": data.get("uptime", "N/A"),
            }
        else:
            return {"online": False, "status": "error", "error": response.status_code}
    except requests.exceptions.ConnectionError:
        return {"online": False, "status": "offline", "error": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"online": False, "status": "timeout", "error": "Request timed out"}
    except Exception as e:
        return {"online": False, "status": "error", "error": str(e)}


def print_status_table(detailed: bool = False):
    """Print a status table of all babies."""
    print("\n" + "="*70)
    print(" SCORPION AI BABIES STATUS")
    print("="*70)

    if detailed:
        print(f"\n{'Name':<10} {'Role':<20} {'Status':<10} {'Model':<15}")
        print("-"*70)
    else:
        print(f"\n{'Name':<10} {'Status':<10} {'Role':<25}")
        print("-"*50)

    online_count = 0
    for baby in BABIES:
        status = check_baby_status(baby["name"])

        if status["online"]:
            status_icon = "[ONLINE]"
            online_count += 1
        else:
            status_icon = "[OFFLINE]"

        if detailed:
            model = status.get("model", "N/A") if status["online"] else "-"
            print(f"{baby['name']:<10} {baby['role']:<20} {status_icon:<10} {model:<15}")
        else:
            print(f"{baby['name']:<10} {status_icon:<10} {baby['role']:<25}")

    print("-"*70 if detailed else "-"*50)
    print(f"\nTotal: {online_count}/{len(BABIES)} babies online")

    if online_count == len(BABIES):
        print("Status: All systems operational!")
    elif online_count == 0:
        print("Status: SCORPION server may not be running.")
        print("        Try: python start_scorpion.py")
    else:
        print("Status: Some babies are offline. Check server logs.")

    print()


def check_server_health():
    """Check overall server health."""
    url = f"{API_BASE}/health"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "code": response.status_code}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "error": "Cannot connect to SCORPION server"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Check which SCORPION AI babies are online"
    )

    parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Show detailed information including model versions"
    )

    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # First check server health
    server_health = check_server_health()

    if args.json:
        import json
        results = {
            "server": server_health,
            "babies": {}
        }
        for baby in BABIES:
            results["babies"][baby["name"]] = check_baby_status(baby["name"])
        print(json.dumps(results, indent=2))
    else:
        if server_health.get("status") == "offline":
            print("\nSCORPION server is not running!")
            print("Start it with: python start_scorpion.py\n")
            sys.exit(1)

        print_status_table(detailed=args.detailed)


if __name__ == "__main__":
    main()
