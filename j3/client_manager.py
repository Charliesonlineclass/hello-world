"""
J3 Client Manager
=================

Manage construction clients and projects.
Track client info, project status, and history.

Requirements:
    pip install sqlalchemy (optional, for SQLite)
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Union
from dataclasses import dataclass, asdict, field
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("J3.client_manager")

# Client status options
CLIENT_STATUSES = [
    "lead",           # Initial contact
    "quoted",         # Quote sent
    "negotiating",    # Discussing terms
    "scheduled",      # Job scheduled
    "in_progress",    # Work ongoing
    "completed",      # Job finished
    "follow_up",      # Needs follow-up
    "inactive"        # No longer active
]


@dataclass
class Client:
    """Client data structure."""
    id: str
    name: str
    email: str
    phone: str
    address: str
    city: str = ""
    state: str = ""
    zip_code: str = ""
    status: str = "lead"
    source: str = ""  # How they found us
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    quotes: List[str] = field(default_factory=list)  # Quote IDs
    projects: List[str] = field(default_factory=list)  # Project IDs
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class Project:
    """Project data structure."""
    id: str
    client_id: str
    name: str
    job_type: str
    description: str
    status: str = "pending"
    quote_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    estimated_value: float = 0.0
    actual_cost: float = 0.0
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class ClientManager:
    """
    Manage construction clients and their projects.

    Usage:
        mgr = ClientManager()
        client_id = mgr.add_client("John Doe", "john@email.com", "555-1234", "123 Main St")
        mgr.update_status(client_id, "quoted")
        clients = mgr.list_active_clients()
    """

    def __init__(self, data_dir: str = "client_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.clients_file = self.data_dir / "clients.json"
        self.projects_file = self.data_dir / "projects.json"

        self._clients: Dict[str, Client] = {}
        self._projects: Dict[str, Project] = {}

        self._load_data()

    def _load_data(self):
        """Load clients and projects from JSON files."""
        if self.clients_file.exists():
            try:
                data = json.loads(self.clients_file.read_text())
                for client_data in data:
                    client = Client(**client_data)
                    self._clients[client.id] = client
                logger.info(f"Loaded {len(self._clients)} clients")
            except Exception as e:
                logger.error(f"Error loading clients: {e}")

        if self.projects_file.exists():
            try:
                data = json.loads(self.projects_file.read_text())
                for project_data in data:
                    project = Project(**project_data)
                    self._projects[project.id] = project
                logger.info(f"Loaded {len(self._projects)} projects")
            except Exception as e:
                logger.error(f"Error loading projects: {e}")

    def _save_data(self):
        """Save clients and projects to JSON files."""
        # Save clients
        clients_data = [asdict(c) for c in self._clients.values()]
        self.clients_file.write_text(json.dumps(clients_data, indent=2))

        # Save projects
        projects_data = [asdict(p) for p in self._projects.values()]
        self.projects_file.write_text(json.dumps(projects_data, indent=2))

    def add_client(
        self,
        name: str,
        email: str,
        phone: str,
        address: str,
        city: str = "",
        state: str = "",
        zip_code: str = "",
        source: str = "",
        notes: str = "",
        tags: List[str] = None
    ) -> str:
        """
        Add a new client.

        Args:
            name: Client name
            email: Email address
            phone: Phone number
            address: Street address
            city: City
            state: State
            zip_code: ZIP code
            source: Lead source
            notes: Additional notes
            tags: Client tags

        Returns:
            Client ID
        """
        client_id = str(uuid.uuid4())[:8]

        client = Client(
            id=client_id,
            name=name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            source=source,
            notes=notes,
            tags=tags or []
        )

        self._clients[client_id] = client
        self._save_data()

        logger.info(f"Added client: {name} (ID: {client_id})")
        return client_id

    def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID."""
        return self._clients.get(client_id)

    def find_client(self, search: str) -> List[Client]:
        """
        Find clients by name, email, or phone.

        Args:
            search: Search string

        Returns:
            List of matching clients
        """
        search = search.lower()
        results = []

        for client in self._clients.values():
            if (search in client.name.lower() or
                search in client.email.lower() or
                search in client.phone):
                results.append(client)

        return results

    def update_client(self, client_id: str, **kwargs) -> bool:
        """
        Update client information.

        Args:
            client_id: Client ID
            **kwargs: Fields to update

        Returns:
            True if updated successfully
        """
        client = self._clients.get(client_id)
        if not client:
            logger.error(f"Client not found: {client_id}")
            return False

        for key, value in kwargs.items():
            if hasattr(client, key):
                setattr(client, key, value)

        client.updated_at = datetime.now().isoformat()
        self._save_data()

        logger.info(f"Updated client {client_id}")
        return True

    def update_status(self, client_id: str, status: str) -> bool:
        """
        Update client status.

        Args:
            client_id: Client ID
            status: New status

        Returns:
            True if updated successfully
        """
        if status not in CLIENT_STATUSES:
            logger.error(f"Invalid status: {status}. Valid: {CLIENT_STATUSES}")
            return False

        return self.update_client(client_id, status=status)

    def add_quote(self, client_id: str, quote_id: str) -> bool:
        """Add a quote reference to client."""
        client = self._clients.get(client_id)
        if not client:
            return False

        if quote_id not in client.quotes:
            client.quotes.append(quote_id)
            client.updated_at = datetime.now().isoformat()
            self._save_data()

        return True

    def add_tag(self, client_id: str, tag: str) -> bool:
        """Add a tag to client."""
        client = self._clients.get(client_id)
        if not client:
            return False

        if tag not in client.tags:
            client.tags.append(tag)
            client.updated_at = datetime.now().isoformat()
            self._save_data()

        return True

    def remove_tag(self, client_id: str, tag: str) -> bool:
        """Remove a tag from client."""
        client = self._clients.get(client_id)
        if not client:
            return False

        if tag in client.tags:
            client.tags.remove(tag)
            client.updated_at = datetime.now().isoformat()
            self._save_data()

        return True

    def list_clients(
        self,
        status: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Client]:
        """
        List clients with optional filtering.

        Args:
            status: Filter by status
            tag: Filter by tag

        Returns:
            List of clients
        """
        results = list(self._clients.values())

        if status:
            results = [c for c in results if c.status == status]

        if tag:
            results = [c for c in results if tag in c.tags]

        return results

    def list_active_clients(self) -> List[Client]:
        """List all active (non-inactive) clients."""
        return [c for c in self._clients.values() if c.status != "inactive"]

    def list_leads(self) -> List[Client]:
        """List clients with lead status."""
        return self.list_clients(status="lead")

    def list_in_progress(self) -> List[Client]:
        """List clients with active projects."""
        return self.list_clients(status="in_progress")

    # Project management

    def add_project(
        self,
        client_id: str,
        name: str,
        job_type: str,
        description: str = "",
        quote_id: Optional[str] = None,
        estimated_value: float = 0.0
    ) -> Optional[str]:
        """
        Add a project for a client.

        Args:
            client_id: Client ID
            name: Project name
            job_type: Type of job
            description: Project description
            quote_id: Associated quote ID
            estimated_value: Estimated project value

        Returns:
            Project ID or None
        """
        client = self._clients.get(client_id)
        if not client:
            logger.error(f"Client not found: {client_id}")
            return None

        project_id = str(uuid.uuid4())[:8]

        project = Project(
            id=project_id,
            client_id=client_id,
            name=name,
            job_type=job_type,
            description=description,
            quote_id=quote_id,
            estimated_value=estimated_value
        )

        self._projects[project_id] = project
        client.projects.append(project_id)
        client.updated_at = datetime.now().isoformat()

        self._save_data()

        logger.info(f"Added project: {name} (ID: {project_id})")
        return project_id

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self._projects.get(project_id)

    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project information."""
        project = self._projects.get(project_id)
        if not project:
            logger.error(f"Project not found: {project_id}")
            return False

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.updated_at = datetime.now().isoformat()
        self._save_data()

        logger.info(f"Updated project {project_id}")
        return True

    def start_project(self, project_id: str) -> bool:
        """Mark project as started."""
        return self.update_project(
            project_id,
            status="in_progress",
            start_date=datetime.now().isoformat()
        )

    def complete_project(
        self,
        project_id: str,
        actual_cost: Optional[float] = None
    ) -> bool:
        """Mark project as completed."""
        updates = {
            "status": "completed",
            "end_date": datetime.now().isoformat()
        }
        if actual_cost is not None:
            updates["actual_cost"] = actual_cost

        # Also update client status
        project = self._projects.get(project_id)
        if project:
            self.update_status(project.client_id, "completed")

        return self.update_project(project_id, **updates)

    def get_client_projects(self, client_id: str) -> List[Project]:
        """Get all projects for a client."""
        return [
            self._projects[pid]
            for pid in self._clients.get(client_id, Client("", "", "", "", "")).projects
            if pid in self._projects
        ]

    # Statistics and reports

    def get_stats(self) -> Dict:
        """Get client and project statistics."""
        stats = {
            "total_clients": len(self._clients),
            "total_projects": len(self._projects),
            "clients_by_status": {},
            "projects_by_status": {},
            "total_estimated_value": 0,
            "total_actual_revenue": 0
        }

        # Count clients by status
        for client in self._clients.values():
            stats["clients_by_status"][client.status] = \
                stats["clients_by_status"].get(client.status, 0) + 1

        # Count projects by status
        for project in self._projects.values():
            stats["projects_by_status"][project.status] = \
                stats["projects_by_status"].get(project.status, 0) + 1
            stats["total_estimated_value"] += project.estimated_value
            stats["total_actual_revenue"] += project.actual_cost

        return stats

    def export_to_csv(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """Export clients to CSV file."""
        if output_path is None:
            output_path = self.data_dir / f"clients_export_{datetime.now().strftime('%Y%m%d')}.csv"

        output_path = Path(output_path)

        headers = ["ID", "Name", "Email", "Phone", "Address", "City", "State", "ZIP", "Status", "Source", "Created"]
        rows = []

        for client in self._clients.values():
            rows.append([
                client.id,
                client.name,
                client.email,
                client.phone,
                client.address,
                client.city,
                client.state,
                client.zip_code,
                client.status,
                client.source,
                client.created_at[:10]
            ])

        with open(output_path, 'w') as f:
            f.write(','.join(headers) + '\n')
            for row in rows:
                # Escape commas in fields
                escaped = [f'"{field}"' if ',' in str(field) else str(field) for field in row]
                f.write(','.join(escaped) + '\n')

        logger.info(f"Exported {len(rows)} clients to {output_path}")
        return output_path

    def get_follow_up_list(self) -> List[Dict]:
        """
        Get list of clients needing follow-up.
        Returns clients who were quoted more than 7 days ago without response.
        """
        follow_ups = []
        cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7 days ago

        for client in self._clients.values():
            if client.status == "quoted":
                updated = datetime.fromisoformat(client.updated_at).timestamp()
                if updated < cutoff:
                    follow_ups.append({
                        "client": client,
                        "days_since_quote": int((datetime.now().timestamp() - updated) / (24 * 60 * 60))
                    })

        return sorted(follow_ups, key=lambda x: x["days_since_quote"], reverse=True)


if __name__ == "__main__":
    # Demo usage
    print("J3 Client Manager - Demo")
    print("=" * 40)

    mgr = ClientManager()

    # Add sample clients
    client1_id = mgr.add_client(
        name="John Smith",
        email="john@example.com",
        phone="555-123-4567",
        address="123 Main St",
        city="Austin",
        state="TX",
        zip_code="78701",
        source="Referral",
        tags=["residential", "priority"]
    )

    client2_id = mgr.add_client(
        name="Jane Doe",
        email="jane@example.com",
        phone="555-987-6543",
        address="456 Oak Ave",
        city="Austin",
        state="TX",
        zip_code="78702",
        source="Website"
    )

    # Update status
    mgr.update_status(client1_id, "quoted")

    # Add project
    project_id = mgr.add_project(
        client_id=client1_id,
        name="Kitchen Remodel",
        job_type="kitchen",
        estimated_value=45000.00
    )

    # Print stats
    print("\nClient Statistics:")
    stats = mgr.get_stats()
    print(f"  Total Clients: {stats['total_clients']}")
    print(f"  Total Projects: {stats['total_projects']}")
    print(f"  Clients by Status: {stats['clients_by_status']}")

    # List clients
    print("\nAll Clients:")
    for client in mgr.list_clients():
        print(f"  - {client.name} ({client.status})")

    # Export
    csv_path = mgr.export_to_csv()
    print(f"\nExported to: {csv_path}")
