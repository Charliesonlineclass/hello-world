"""
SCORPION AI - Lead Manager
Handle lead operations for the CRM
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from .database import get_connection
from .models import Lead, LeadStatus, Client, ClientTier


class LeadManager:
    """Manage lead operations"""

    def create_lead(self, data: Dict[str, Any]) -> Lead:
        """Create a new lead"""
        now = datetime.now()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leads (name, email, phone, company, source, status, score, notes, service_interest, tier_interest, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name', ''),
                data.get('email', ''),
                data.get('phone', ''),
                data.get('company', ''),
                data.get('source', 'website'),
                data.get('status', 'new'),
                self._calculate_initial_score(data),
                data.get('notes', ''),
                data.get('service_interest', ''),
                data.get('tier_interest', ''),
                now.isoformat(),
                now.isoformat()
            ))
            lead_id = cursor.lastrowid

            return self.get_lead(lead_id)

    def get_lead(self, lead_id: int) -> Optional[Lead]:
        """Get a lead by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
            row = cursor.fetchone()

            if row:
                return Lead.from_dict(dict(row))
            return None

    def update_lead(self, lead_id: int, data: Dict[str, Any]) -> Optional[Lead]:
        """Update an existing lead"""
        now = datetime.now()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Build update query dynamically
            allowed_fields = ['name', 'email', 'phone', 'company', 'source', 'status', 'score', 'notes', 'service_interest', 'tier_interest']
            updates = []
            values = []

            for field in allowed_fields:
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])

            if not updates:
                return self.get_lead(lead_id)

            updates.append("updated_at = ?")
            values.append(now.isoformat())
            values.append(lead_id)

            query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)

            return self.get_lead(lead_id)

    def delete_lead(self, lead_id: int) -> bool:
        """Delete a lead"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
            return cursor.rowcount > 0

    def list_leads(self, filters: Optional[Dict[str, Any]] = None) -> List[Lead]:
        """List leads with optional filters"""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM leads WHERE 1=1"
            params = []

            if filters:
                if 'status' in filters:
                    query += " AND status = ?"
                    params.append(filters['status'])
                if 'source' in filters:
                    query += " AND source = ?"
                    params.append(filters['source'])
                if 'min_score' in filters:
                    query += " AND score >= ?"
                    params.append(filters['min_score'])
                if 'search' in filters:
                    query += " AND (name LIKE ? OR email LIKE ? OR company LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term, search_term])

            query += " ORDER BY created_at DESC"

            if 'limit' in filters:
                query += " LIMIT ?"
                params.append(filters['limit'])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [Lead.from_dict(dict(row)) for row in rows]

    def score_lead(self, lead_id: int) -> int:
        """Calculate and update lead score"""
        lead = self.get_lead(lead_id)
        if not lead:
            return 0

        score = self._calculate_score(lead)
        self.update_lead(lead_id, {'score': score})
        return score

    def _calculate_initial_score(self, data: Dict[str, Any]) -> int:
        """Calculate initial score based on provided data"""
        score = 10  # Base score

        # Email provided
        if data.get('email'):
            score += 15

        # Phone provided
        if data.get('phone'):
            score += 10

        # Company provided
        if data.get('company'):
            score += 10

        # Service interest specified
        if data.get('service_interest'):
            score += 10

        # Tier interest specified
        if data.get('tier_interest'):
            score += 15
            # Higher tier = higher score
            tier = data.get('tier_interest', '').lower()
            if tier == 'empire':
                score += 20
            elif tier == 'pro':
                score += 10

        # Source quality
        source = data.get('source', '').lower()
        if source == 'referral':
            score += 20
        elif source == 'website':
            score += 5

        return min(score, 100)

    def _calculate_score(self, lead: Lead) -> int:
        """Calculate comprehensive lead score"""
        score = 10  # Base score

        # Contact info completeness
        if lead.email:
            score += 15
        if lead.phone:
            score += 10
        if lead.company:
            score += 10

        # Engagement indicators
        if lead.service_interest:
            score += 10
        if lead.tier_interest:
            score += 15
            tier = lead.tier_interest.lower()
            if tier == 'empire':
                score += 20
            elif tier == 'pro':
                score += 10

        # Status progression bonus
        status_scores = {
            'new': 0,
            'contacted': 10,
            'qualified': 20,
            'proposal': 30,
            'negotiation': 40,
        }
        score += status_scores.get(lead.status.value, 0)

        # Source quality
        source = lead.source.lower()
        if source == 'referral':
            score += 20
        elif source == 'chat':
            score += 10
        elif source == 'website':
            score += 5

        return min(score, 100)

    def change_status(self, lead_id: int, status: LeadStatus) -> Optional[Lead]:
        """Change lead status"""
        return self.update_lead(lead_id, {'status': status.value})

    def convert_to_client(self, lead_id: int, tier: ClientTier) -> Optional[Client]:
        """Convert a lead to a client"""
        lead = self.get_lead(lead_id)
        if not lead:
            return None

        # Map tier to monthly rate
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

        now = datetime.now()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Create client
            cursor.execute("""
                INSERT INTO clients (name, email, phone, company, tier, start_date, monthly_rate, baby_assigned, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.name,
                lead.email,
                lead.phone,
                lead.company,
                tier.value,
                now.isoformat(),
                tier_rates.get(tier, 100.0),
                tier_babies.get(tier, 'HERMES'),
                f"Converted from lead. Original notes: {lead.notes}",
                now.isoformat(),
                now.isoformat()
            ))
            client_id = cursor.lastrowid

            # Update lead status
            cursor.execute("UPDATE leads SET status = 'won', updated_at = ? WHERE id = ?", (now.isoformat(), lead_id))

            # Fetch and return the new client
            cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()

            if row:
                return Client.from_dict(dict(row))
            return None

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get lead pipeline statistics"""
        with get_connection() as conn:
            cursor = conn.cursor()

            stats = {
                'total': 0,
                'by_status': {},
                'by_source': {},
                'avg_score': 0,
                'conversion_rate': 0
            }

            # Total leads
            cursor.execute("SELECT COUNT(*) FROM leads")
            stats['total'] = cursor.fetchone()[0]

            # By status
            cursor.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status")
            for row in cursor.fetchall():
                stats['by_status'][row['status']] = row['count']

            # By source
            cursor.execute("SELECT source, COUNT(*) as count FROM leads GROUP BY source")
            for row in cursor.fetchall():
                stats['by_source'][row['source']] = row['count']

            # Average score
            cursor.execute("SELECT AVG(score) FROM leads")
            avg = cursor.fetchone()[0]
            stats['avg_score'] = round(avg, 1) if avg else 0

            # Conversion rate
            won = stats['by_status'].get('won', 0)
            total = stats['total'] or 1
            stats['conversion_rate'] = round((won / total) * 100, 1)

            return stats

    def search_leads(self, query: str) -> List[Lead]:
        """Search leads by name, email, or company"""
        return self.list_leads({'search': query})
