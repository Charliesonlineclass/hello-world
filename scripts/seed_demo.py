#!/usr/bin/env python3
"""
SCORPION AI - Demo Data Seeder
Seed the database with demonstration data
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crm.database import init_database, seed_demo_data, get_database_stats


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   🦂  SCORPION AI - Demo Data Seeder                          ║
╚═══════════════════════════════════════════════════════════════╝
""")

    print("📦 Initializing database...")
    init_database()

    print("\n🌱 Seeding demo data...")
    seed_demo_data()

    print("\n📊 Database Statistics:")
    print("─" * 40)
    stats = get_database_stats()
    for key, value in stats.items():
        if key == 'total_revenue':
            print(f"  {key}: ${value:,.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n✅ Demo data seeded successfully!")
    print("""
Demo Accounts Created:
─────────────────────
📧 Clients:
   • j3@structural.com (Pro tier, VULCAN)
   • contact@ipc.com (Empire tier, MARCUS)
   • antonio@bank.com (Empire tier, MARCUS)

📧 Leads:
   • maria@example.com (Qualified)
   • roberto@example.com (Contacted)
   • ana@example.com (New)
   • carlos@example.com (Proposal)
""")


if __name__ == "__main__":
    main()
