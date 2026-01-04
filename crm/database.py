"""
SCORPION AI - Database Module
SQLite database management for Pandora's Castle CRM
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional
import json

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "castle.db"


def get_db_path() -> Path:
    """Get database file path, creating directories if needed"""
    db_path = DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def get_connection(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections"""
    path = db_path or get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database(db_path: Optional[Path] = None) -> None:
    """Initialize the database with all required tables"""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT DEFAULT '',
                company TEXT DEFAULT '',
                source TEXT DEFAULT '',
                status TEXT DEFAULT 'new',
                score INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                service_interest TEXT DEFAULT '',
                tier_interest TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Clients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT DEFAULT '',
                company TEXT DEFAULT '',
                tier TEXT DEFAULT 'starter',
                start_date TIMESTAMP,
                monthly_rate REAL DEFAULT 100.0,
                months_paid INTEGER DEFAULT 0,
                balance_paid REAL DEFAULT 0.0,
                baby_assigned TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'planning',
                start_date TIMESTAMP,
                due_date TIMESTAMP,
                completed_date TIMESTAMP,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)

        # Invoices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                due_date TIMESTAMP,
                paid_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)

        # Communications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                comm_type TEXT DEFAULT 'note',
                direction TEXT DEFAULT 'outbound',
                subject TEXT DEFAULT '',
                content TEXT DEFAULT '',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)

        # Chat sessions table for public chat
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                lead_id INTEGER,
                messages TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_tier ON clients(tier)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_communications_client ON communications(client_id)")

        conn.commit()
        print("🦂 Database initialized successfully")


def seed_demo_data(db_path: Optional[Path] = None) -> None:
    """Seed the database with demo data"""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM clients")
        if cursor.fetchone()[0] > 0:
            print("Demo data already exists, skipping...")
            return

        now = datetime.now().isoformat()

        # Demo leads
        leads = [
            ("Maria Garcia", "maria@example.com", "+503 7890 1234", "Garcia Construction", "website", "qualified", 75, "Interested in AI assistant for lead gen", "ai-assistant", "pro"),
            ("Roberto Mendez", "roberto@example.com", "+503 7890 5678", "Mendez Law Firm", "referral", "contacted", 60, "Looking for automation solutions", "automation", "empire"),
            ("Ana Torres", "ana@example.com", "+503 7890 9012", "Torres Marketing", "chat", "new", 40, "Inquired about pricing", "web-dev", "starter"),
            ("Carlos Reyes", "carlos@example.com", "+503 7890 3456", "Reyes Auto", "website", "proposal", 85, "Ready to sign for Pro tier", "ai-assistant", "pro"),
        ]

        for lead in leads:
            cursor.execute("""
                INSERT INTO leads (name, email, phone, company, source, status, score, notes, service_interest, tier_interest, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*lead, now, now))

        # Demo clients
        clients = [
            ("J3 Structural Solutions", "j3@structural.com", "+503 2200 1111", "J3 Structural", "pro", "2024-01-15", 200.0, 6, 1200.0, "VULCAN", "Construction company - AI lead qualification", 1),
            ("IPC Solutions", "contact@ipc.com", "+503 2200 2222", "IPC Solutions", "empire", "2024-02-01", 500.0, 5, 2500.0, "MARCUS", "Call center optimization project", 1),
            ("Antonio Martinez", "antonio@bank.com", "+503 2200 3333", "Banking Corp", "empire", "2024-04-01", 500.0, 9, 4500.0, "MARCUS", "Banking automation - 3 months to ownership!", 1),
        ]

        for client in clients:
            cursor.execute("""
                INSERT INTO clients (name, email, phone, company, tier, start_date, monthly_rate, months_paid, balance_paid, baby_assigned, notes, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*client, now, now))

        # Demo projects
        projects = [
            (1, "AI Lead Qualification System", "24/7 AI assistant for construction leads", "active", "2024-01-20", "2024-03-20", None, "Phase 2: Integration with CRM"),
            (1, "Website Redesign", "Modern website with chat widget", "completed", "2024-01-25", "2024-02-15", "2024-02-10", "Completed ahead of schedule"),
            (2, "Call Center AI Integration", "AI-powered call assistance system", "active", "2024-02-05", "2024-05-01", None, "Training phase with agents"),
            (3, "Document Automation", "Automated document processing", "active", "2024-04-15", "2024-06-15", None, "Compliance review in progress"),
            (3, "Customer Service Bot", "Banking FAQ chatbot", "review", "2024-04-20", "2024-05-20", None, "Final testing phase"),
        ]

        for project in projects:
            cursor.execute("""
                INSERT INTO projects (client_id, name, description, status, start_date, due_date, completed_date, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*project, now, now))

        # Demo communications
        communications = [
            (1, "call", "outbound", "Onboarding Call", "Walked through initial setup and AI training requirements", now),
            (1, "email", "outbound", "Progress Update", "Sent weekly report on lead qualification metrics", now),
            (2, "meeting", "outbound", "Strategy Session", "Discussed phase 2 implementation with team leads", now),
            (3, "chat", "inbound", "Support Request", "Client asked about upcoming features", now),
        ]

        for comm in communications:
            cursor.execute("""
                INSERT INTO communications (client_id, comm_type, direction, subject, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, comm)

        conn.commit()
        print("🦂 Demo data seeded successfully")


def backup_database(db_path: Optional[Path] = None, backup_path: Optional[Path] = None) -> Path:
    """Create a backup of the database"""
    source = db_path or get_db_path()
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = source.parent / f"castle_backup_{timestamp}.db"

    import shutil
    shutil.copy2(source, backup_path)
    print(f"🦂 Database backed up to: {backup_path}")
    return backup_path


def get_database_stats(db_path: Optional[Path] = None) -> dict:
    """Get statistics about the database"""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        stats = {}

        tables = ['leads', 'clients', 'projects', 'invoices', 'communications']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]

        # Additional stats
        cursor.execute("SELECT SUM(balance_paid) FROM clients")
        stats['total_revenue'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM clients WHERE months_paid >= 12")
        stats['fully_owned'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'active'")
        stats['active_projects'] = cursor.fetchone()[0]

        return stats


if __name__ == "__main__":
    # Initialize and seed when run directly
    init_database()
    seed_demo_data()
    print("\n📊 Database Stats:")
    for key, value in get_database_stats().items():
        print(f"  {key}: {value}")
