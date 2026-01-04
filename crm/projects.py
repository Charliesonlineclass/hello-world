"""
SCORPION AI - Project Manager
Handle project operations for the CRM
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from .database import get_connection
from .models import Project, ProjectStatus


class ProjectManager:
    """Manage project operations"""

    def create_project(self, client_id: int, data: Dict[str, Any]) -> Project:
        """Create a new project"""
        now = datetime.now()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (client_id, name, description, status, start_date, due_date, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id,
                data.get('name', ''),
                data.get('description', ''),
                data.get('status', 'planning'),
                data.get('start_date', now.isoformat()),
                data.get('due_date'),
                data.get('notes', ''),
                now.isoformat(),
                now.isoformat()
            ))
            project_id = cursor.lastrowid

            return self.get_project(project_id)

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()

            if row:
                return Project.from_dict(dict(row))
            return None

    def update_project(self, project_id: int, data: Dict[str, Any]) -> Optional[Project]:
        """Update an existing project"""
        now = datetime.now()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Build update query dynamically
            allowed_fields = ['name', 'description', 'status', 'start_date', 'due_date', 'completed_date', 'notes']
            updates = []
            values = []

            for field in allowed_fields:
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])

            if not updates:
                return self.get_project(project_id)

            updates.append("updated_at = ?")
            values.append(now.isoformat())
            values.append(project_id)

            query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)

            return self.get_project(project_id)

    def update_status(self, project_id: int, status: ProjectStatus) -> Optional[Project]:
        """Update project status"""
        data = {'status': status.value}

        # Auto-set completed_date when marking complete
        if status == ProjectStatus.COMPLETED:
            data['completed_date'] = datetime.now().isoformat()

        return self.update_project(project_id, data)

    def delete_project(self, project_id: int) -> bool:
        """Delete a project"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0

    def list_projects(self, filters: Optional[Dict[str, Any]] = None) -> List[Project]:
        """List projects with optional filters"""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM projects WHERE 1=1"
            params = []

            if filters:
                if 'client_id' in filters:
                    query += " AND client_id = ?"
                    params.append(filters['client_id'])
                if 'status' in filters:
                    query += " AND status = ?"
                    params.append(filters['status'])
                if 'search' in filters:
                    query += " AND (name LIKE ? OR description LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])

            query += " ORDER BY created_at DESC"

            if filters and 'limit' in filters:
                query += " LIMIT ?"
                params.append(filters['limit'])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [Project.from_dict(dict(row)) for row in rows]

    def get_active_projects(self) -> List[Project]:
        """Get all active projects"""
        return self.list_projects({'status': 'active'})

    def get_overdue_projects(self) -> List[Project]:
        """Get all overdue projects"""
        now = datetime.now().isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects
                WHERE status != 'completed'
                AND due_date IS NOT NULL
                AND due_date < ?
                ORDER BY due_date ASC
            """, (now,))
            rows = cursor.fetchall()

            return [Project.from_dict(dict(row)) for row in rows]

    def get_project_timeline(self, project_id: int) -> List[Dict[str, Any]]:
        """Get timeline events for a project"""
        project = self.get_project(project_id)
        if not project:
            return []

        timeline = []

        # Project creation
        if project.created_at:
            timeline.append({
                'date': project.created_at.isoformat(),
                'event': 'Project Created',
                'description': f"Project '{project.name}' was created"
            })

        # Project start
        if project.start_date:
            timeline.append({
                'date': project.start_date.isoformat(),
                'event': 'Project Started',
                'description': f"Work began on the project"
            })

        # Due date
        if project.due_date:
            timeline.append({
                'date': project.due_date.isoformat(),
                'event': 'Due Date',
                'description': f"Project deadline"
            })

        # Completion
        if project.completed_date:
            timeline.append({
                'date': project.completed_date.isoformat(),
                'event': 'Project Completed',
                'description': f"Project was completed"
            })

        # Sort by date
        timeline.sort(key=lambda x: x['date'])

        return timeline

    def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics"""
        with get_connection() as conn:
            cursor = conn.cursor()

            stats = {
                'total': 0,
                'by_status': {},
                'overdue_count': 0,
                'completion_rate': 0
            }

            # Total projects
            cursor.execute("SELECT COUNT(*) FROM projects")
            stats['total'] = cursor.fetchone()[0]

            # By status
            cursor.execute("SELECT status, COUNT(*) as count FROM projects GROUP BY status")
            for row in cursor.fetchall():
                stats['by_status'][row['status']] = row['count']

            # Overdue count
            now = datetime.now().isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE status != 'completed'
                AND due_date IS NOT NULL
                AND due_date < ?
            """, (now,))
            stats['overdue_count'] = cursor.fetchone()[0]

            # Completion rate
            completed = stats['by_status'].get('completed', 0)
            total = stats['total'] or 1
            stats['completion_rate'] = round((completed / total) * 100, 1)

            return stats
