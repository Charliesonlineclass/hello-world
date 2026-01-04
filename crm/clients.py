"""
SCORPION AI - Client Manager
Handle client operations for the CRM
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from .database import get_connection
from .models import Client, ClientTier, Project, Invoice, Communication


class ClientManager:
    """Manage client operations"""

    def create_client(self, data: Dict[str, Any]) -> Client:
        """Create a new client"""
        now = datetime.now()

        # Map tier to monthly rate
        tier = ClientTier(data.get('tier', 'starter'))
        tier_rates = {
            ClientTier.STARTER: 100.0,
            ClientTier.PRO: 200.0,
            ClientTier.EMPIRE: 500.0
        }

        # Map tier to default baby
        tier_babies = {
            ClientTier.STARTER: 'HERMES',
            ClientTier.PRO: 'VULCAN',
            ClientTier.EMPIRE: 'MARCUS'
        }

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (name, email, phone, company, tier, start_date, monthly_rate, months_paid, balance_paid, baby_assigned, notes, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name', ''),
                data.get('email', ''),
                data.get('phone', ''),
                data.get('company', ''),
                tier.value,
                data.get('start_date', now.isoformat()),
                data.get('monthly_rate', tier_rates.get(tier, 100.0)),
                data.get('months_paid', 0),
                data.get('balance_paid', 0.0),
                data.get('baby_assigned', tier_babies.get(tier, 'HERMES')),
                data.get('notes', ''),
                1,
                now.isoformat(),
                now.isoformat()
            ))
            client_id = cursor.lastrowid

            return self.get_client(client_id)

    def get_client(self, client_id: int) -> Optional[Client]:
        """Get a client by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()

            if row:
                return Client.from_dict(dict(row))
            return None

    def get_client_by_email(self, email: str) -> Optional[Client]:
        """Get a client by email"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE email = ?", (email,))
            row = cursor.fetchone()

            if row:
                return Client.from_dict(dict(row))
            return None

    def update_client(self, client_id: int, data: Dict[str, Any]) -> Optional[Client]:
        """Update an existing client"""
        now = datetime.now()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Build update query dynamically
            allowed_fields = ['name', 'email', 'phone', 'company', 'tier', 'monthly_rate', 'months_paid', 'balance_paid', 'baby_assigned', 'notes', 'is_active']
            updates = []
            values = []

            for field in allowed_fields:
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])

            if not updates:
                return self.get_client(client_id)

            updates.append("updated_at = ?")
            values.append(now.isoformat())
            values.append(client_id)

            query = f"UPDATE clients SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)

            return self.get_client(client_id)

    def list_clients(self, filters: Optional[Dict[str, Any]] = None) -> List[Client]:
        """List clients with optional filters"""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM clients WHERE 1=1"
            params = []

            if filters:
                if 'tier' in filters:
                    query += " AND tier = ?"
                    params.append(filters['tier'])
                if 'is_active' in filters:
                    query += " AND is_active = ?"
                    params.append(1 if filters['is_active'] else 0)
                if 'is_owned' in filters:
                    if filters['is_owned']:
                        query += " AND months_paid >= 12"
                    else:
                        query += " AND months_paid < 12"
                if 'search' in filters:
                    query += " AND (name LIKE ? OR email LIKE ? OR company LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term, search_term])

            query += " ORDER BY created_at DESC"

            if filters and 'limit' in filters:
                query += " LIMIT ?"
                params.append(filters['limit'])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [Client.from_dict(dict(row)) for row in rows]

    def get_client_projects(self, client_id: int) -> List[Project]:
        """Get all projects for a client"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
            rows = cursor.fetchall()

            return [Project.from_dict(dict(row)) for row in rows]

    def get_client_invoices(self, client_id: int) -> List[Invoice]:
        """Get all invoices for a client"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
            rows = cursor.fetchall()

            return [Invoice.from_dict(dict(row)) for row in rows]

    def get_client_communications(self, client_id: int, limit: int = 50) -> List[Communication]:
        """Get communications for a client"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM communications
                WHERE client_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (client_id, limit))
            rows = cursor.fetchall()

            return [Communication.from_dict(dict(row)) for row in rows]

    def calculate_lifetime_value(self, client_id: int) -> float:
        """Calculate total lifetime value of a client"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance_paid FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()

            if row:
                return row['balance_paid']
            return 0.0

    def check_ownership_status(self, client_id: int) -> Dict[str, Any]:
        """Check ownership status for a client"""
        client = self.get_client(client_id)
        if not client:
            return {}

        return {
            'client_id': client_id,
            'tier': client.tier.value,
            'monthly_rate': client.monthly_rate,
            'months_paid': client.months_paid,
            'total_paid': client.balance_paid,
            'total_cost': client.total_value,
            'remaining_balance': client.remaining_balance,
            'remaining_months': client.remaining_months,
            'ownership_percent': client.ownership_percent,
            'is_owned': client.is_owned,
            'baby_assigned': client.baby_assigned
        }

    def assign_baby(self, client_id: int, baby_name: str) -> Optional[Client]:
        """Assign an AI baby to a client"""
        return self.update_client(client_id, {'baby_assigned': baby_name})

    def record_payment(self, client_id: int, amount: Optional[float] = None) -> Optional[Client]:
        """Record a monthly payment for a client"""
        client = self.get_client(client_id)
        if not client:
            return None

        payment_amount = amount or client.monthly_rate

        return self.update_client(client_id, {
            'months_paid': client.months_paid + 1,
            'balance_paid': client.balance_paid + payment_amount
        })

    def get_client_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        with get_connection() as conn:
            cursor = conn.cursor()

            stats = {
                'total': 0,
                'active': 0,
                'by_tier': {},
                'fully_owned': 0,
                'total_revenue': 0,
                'avg_ownership_percent': 0
            }

            # Total and active clients
            cursor.execute("SELECT COUNT(*) FROM clients")
            stats['total'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM clients WHERE is_active = 1")
            stats['active'] = cursor.fetchone()[0]

            # By tier
            cursor.execute("SELECT tier, COUNT(*) as count FROM clients GROUP BY tier")
            for row in cursor.fetchall():
                stats['by_tier'][row['tier']] = row['count']

            # Fully owned
            cursor.execute("SELECT COUNT(*) FROM clients WHERE months_paid >= 12")
            stats['fully_owned'] = cursor.fetchone()[0]

            # Total revenue
            cursor.execute("SELECT SUM(balance_paid) FROM clients")
            revenue = cursor.fetchone()[0]
            stats['total_revenue'] = revenue or 0

            # Average ownership percent
            cursor.execute("SELECT AVG(CAST(months_paid AS FLOAT) / 12 * 100) FROM clients WHERE months_paid < 12")
            avg = cursor.fetchone()[0]
            stats['avg_ownership_percent'] = round(avg, 1) if avg else 0

            return stats
