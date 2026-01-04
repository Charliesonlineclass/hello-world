"""
SCORPION AI - Communication Manager
Handle communication logging for the CRM
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from .database import get_connection
from .models import Communication, CommunicationType, CommunicationDirection


class CommunicationManager:
    """Manage communication operations"""

    def log_communication(
        self,
        client_id: int,
        comm_type: CommunicationType,
        content: str,
        direction: CommunicationDirection = CommunicationDirection.OUTBOUND,
        subject: str = ""
    ) -> Communication:
        """Log a new communication"""
        now = datetime.now()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO communications (client_id, comm_type, direction, subject, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                client_id,
                comm_type.value,
                direction.value,
                subject,
                content,
                now.isoformat()
            ))
            comm_id = cursor.lastrowid

            cursor.execute("SELECT * FROM communications WHERE id = ?", (comm_id,))
            row = cursor.fetchone()

            if row:
                return Communication.from_dict(dict(row))

    def get_communications(
        self,
        client_id: int,
        type_filter: Optional[CommunicationType] = None,
        date_range: Optional[Dict[str, datetime]] = None,
        limit: int = 100
    ) -> List[Communication]:
        """Get communications for a client with optional filters"""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM communications WHERE client_id = ?"
            params = [client_id]

            if type_filter:
                query += " AND comm_type = ?"
                params.append(type_filter.value)

            if date_range:
                if 'start' in date_range:
                    query += " AND timestamp >= ?"
                    params.append(date_range['start'].isoformat())
                if 'end' in date_range:
                    query += " AND timestamp <= ?"
                    params.append(date_range['end'].isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [Communication.from_dict(dict(row)) for row in rows]

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent activity across all clients"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, cl.name as client_name, cl.company as client_company
                FROM communications c
                JOIN clients cl ON c.client_id = cl.id
                ORDER BY c.timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def search_communications(self, query: str, limit: int = 50) -> List[Communication]:
        """Search communications by content"""
        with get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM communications
                WHERE content LIKE ? OR subject LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (search_term, search_term, limit))
            rows = cursor.fetchall()

            return [Communication.from_dict(dict(row)) for row in rows]

    def get_communication_stats(self, client_id: Optional[int] = None) -> Dict[str, Any]:
        """Get communication statistics"""
        with get_connection() as conn:
            cursor = conn.cursor()

            where_clause = ""
            params = []
            if client_id:
                where_clause = "WHERE client_id = ?"
                params.append(client_id)

            stats = {
                'total': 0,
                'by_type': {},
                'by_direction': {},
                'last_30_days': 0,
                'last_7_days': 0
            }

            # Total
            cursor.execute(f"SELECT COUNT(*) FROM communications {where_clause}", params)
            stats['total'] = cursor.fetchone()[0]

            # By type
            cursor.execute(f"""
                SELECT comm_type, COUNT(*) as count
                FROM communications {where_clause}
                GROUP BY comm_type
            """, params)
            for row in cursor.fetchall():
                stats['by_type'][row['comm_type']] = row['count']

            # By direction
            cursor.execute(f"""
                SELECT direction, COUNT(*) as count
                FROM communications {where_clause}
                GROUP BY direction
            """, params)
            for row in cursor.fetchall():
                stats['by_direction'][row['direction']] = row['count']

            # Last 30 days
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            where_30 = f"WHERE timestamp >= ?" if not client_id else f"{where_clause} AND timestamp >= ?"
            params_30 = [thirty_days_ago] if not client_id else params + [thirty_days_ago]
            cursor.execute(f"SELECT COUNT(*) FROM communications {where_30}", params_30)
            stats['last_30_days'] = cursor.fetchone()[0]

            # Last 7 days
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            where_7 = f"WHERE timestamp >= ?" if not client_id else f"{where_clause} AND timestamp >= ?"
            params_7 = [seven_days_ago] if not client_id else params + [seven_days_ago]
            cursor.execute(f"SELECT COUNT(*) FROM communications {where_7}", params_7)
            stats['last_7_days'] = cursor.fetchone()[0]

            return stats

    def log_email(self, client_id: int, subject: str, content: str, direction: CommunicationDirection = CommunicationDirection.OUTBOUND) -> Communication:
        """Log an email communication"""
        return self.log_communication(
            client_id=client_id,
            comm_type=CommunicationType.EMAIL,
            content=content,
            direction=direction,
            subject=subject
        )

    def log_call(self, client_id: int, notes: str, direction: CommunicationDirection = CommunicationDirection.OUTBOUND) -> Communication:
        """Log a phone call"""
        return self.log_communication(
            client_id=client_id,
            comm_type=CommunicationType.CALL,
            content=notes,
            direction=direction,
            subject="Phone Call"
        )

    def log_meeting(self, client_id: int, subject: str, notes: str) -> Communication:
        """Log a meeting"""
        return self.log_communication(
            client_id=client_id,
            comm_type=CommunicationType.MEETING,
            content=notes,
            direction=CommunicationDirection.OUTBOUND,
            subject=subject
        )

    def log_chat(self, client_id: int, content: str, direction: CommunicationDirection = CommunicationDirection.INBOUND) -> Communication:
        """Log a chat message"""
        return self.log_communication(
            client_id=client_id,
            comm_type=CommunicationType.CHAT,
            content=content,
            direction=direction,
            subject="Chat Message"
        )

    def add_note(self, client_id: int, note: str) -> Communication:
        """Add an internal note"""
        return self.log_communication(
            client_id=client_id,
            comm_type=CommunicationType.NOTE,
            content=note,
            direction=CommunicationDirection.OUTBOUND,
            subject="Internal Note"
        )
