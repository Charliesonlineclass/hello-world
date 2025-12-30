"""
SCORPION TAIL - LABIENUS Access Control
========================================

Security and access control system for the SCORPION ecosystem.

Access Levels:
    - HEAD (100): Full system access - Commander level
    - CLAW (75): Business unit access - Manager level
    - LEG (50): Container-specific access - Worker level
    - PUBLIC (10): Read-only public content

Features:
    - Token-based authentication
    - Role-based access control
    - Resource permissions
    - Container isolation
"""

import os
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TAIL.labienus")


class AccessLevel(Enum):
    """Access levels with numeric values for comparison."""
    HEAD = 100      # Full access - Commander
    CLAW = 75       # Business unit - Manager
    LEG = 50        # Container specific - Worker
    PUBLIC = 10     # Public read-only


# Resource categories and their required access levels
RESOURCE_PERMISSIONS = {
    # System resources
    "system.config": AccessLevel.HEAD,
    "system.logs": AccessLevel.HEAD,
    "system.users": AccessLevel.HEAD,
    "system.backup": AccessLevel.HEAD,

    # AI babies
    "babies.all": AccessLevel.CLAW,
    "babies.marcus": AccessLevel.LEG,
    "babies.hermes": AccessLevel.LEG,
    "babies.athena": AccessLevel.CLAW,
    "babies.apollo": AccessLevel.LEG,

    # Business units
    "claw1.sales": AccessLevel.CLAW,
    "claw1.crm": AccessLevel.CLAW,
    "claw2.lcms": AccessLevel.CLAW,

    # Containers
    "leg.j3": AccessLevel.LEG,
    "leg.nsipa": AccessLevel.LEG,
    "leg.default": AccessLevel.LEG,

    # Data
    "data.read": AccessLevel.PUBLIC,
    "data.write": AccessLevel.LEG,
    "data.delete": AccessLevel.CLAW,
    "data.export": AccessLevel.CLAW,

    # API
    "api.read": AccessLevel.PUBLIC,
    "api.write": AccessLevel.LEG,
    "api.admin": AccessLevel.HEAD
}


@dataclass
class User:
    """User account structure."""
    id: str
    username: str
    password_hash: str
    email: str
    access_level: str
    containers: List[str] = field(default_factory=list)  # LEG users' allowed containers
    permissions: List[str] = field(default_factory=list)  # Additional explicit permissions
    is_active: bool = True
    created_at: str = ""
    last_login: Optional[str] = None
    failed_attempts: int = 0
    locked_until: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Token:
    """Authentication token."""
    token: str
    user_id: str
    created_at: str
    expires_at: str
    is_revoked: bool = False


class AccessControl:
    """
    LABIENUS Access Control System.

    Usage:
        ac = AccessControl()
        user_id = ac.create_user("worker1", "password", "worker@example.com", AccessLevel.LEG, containers=["j3"])
        token = ac.login("worker1", "password")
        if ac.check_permission(token, "leg.j3"):
            # Access granted
            pass
    """

    def __init__(self, data_dir: str = "security"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self._users: Dict[str, User] = {}
        self._tokens: Dict[str, Token] = {}
        self._token_expiry_hours = 24

        self._load_data()
        self._ensure_commander()

    def _load_data(self):
        """Load users and tokens from files."""
        users_file = self.data_dir / "users.json"
        if users_file.exists():
            try:
                data = json.loads(users_file.read_text())
                for user_data in data:
                    user = User(**user_data)
                    self._users[user.id] = user
            except Exception as e:
                logger.error(f"Error loading users: {e}")

        tokens_file = self.data_dir / "tokens.json"
        if tokens_file.exists():
            try:
                data = json.loads(tokens_file.read_text())
                for token_data in data:
                    token = Token(**token_data)
                    if not self._is_token_expired(token):
                        self._tokens[token.token] = token
            except Exception as e:
                logger.error(f"Error loading tokens: {e}")

    def _save_data(self):
        """Save users and tokens to files."""
        users_data = [asdict(u) for u in self._users.values()]
        (self.data_dir / "users.json").write_text(json.dumps(users_data, indent=2))

        # Only save non-expired tokens
        active_tokens = [asdict(t) for t in self._tokens.values() if not self._is_token_expired(t)]
        (self.data_dir / "tokens.json").write_text(json.dumps(active_tokens, indent=2))

    def _ensure_commander(self):
        """Ensure a HEAD user exists (Commander)."""
        has_head = any(u.access_level == AccessLevel.HEAD.name for u in self._users.values())
        if not has_head:
            commander_pass = os.environ.get("SCORPION_COMMANDER_PASS", "changeme")
            self.create_user(
                username="commander",
                password=commander_pass,
                email="commander@scorpion.local",
                access_level=AccessLevel.HEAD
            )
            logger.warning("Created default commander user - CHANGE THE PASSWORD!")

    def _hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        hash_val = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        ).hex()
        return f"{salt}${hash_val}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            salt, stored_hash = password_hash.split('$')
            check_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000
            ).hex()
            return secrets.compare_digest(stored_hash, check_hash)
        except:
            return False

    def _generate_token(self) -> str:
        """Generate secure token."""
        return secrets.token_urlsafe(32)

    def _is_token_expired(self, token: Token) -> bool:
        """Check if token is expired."""
        if token.is_revoked:
            return True
        expires = datetime.fromisoformat(token.expires_at)
        return datetime.now() > expires

    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        access_level: AccessLevel,
        containers: List[str] = None,
        permissions: List[str] = None
    ) -> str:
        """
        Create a new user.

        Args:
            username: Unique username
            password: Password (will be hashed)
            email: User email
            access_level: AccessLevel enum
            containers: For LEG users, list of allowed containers
            permissions: Additional explicit permissions

        Returns:
            User ID
        """
        # Check username uniqueness
        for user in self._users.values():
            if user.username.lower() == username.lower():
                raise ValueError(f"Username already exists: {username}")

        user_id = secrets.token_hex(8)
        password_hash = self._hash_password(password)

        user = User(
            id=user_id,
            username=username,
            password_hash=password_hash,
            email=email,
            access_level=access_level.name,
            containers=containers or [],
            permissions=permissions or []
        )

        self._users[user_id] = user
        self._save_data()

        logger.info(f"User created: {username} ({access_level.name})")
        return user_id

    def login(
        self,
        username: str,
        password: str
    ) -> Optional[str]:
        """
        Authenticate user and return token.

        Args:
            username: Username
            password: Password

        Returns:
            Auth token or None if failed
        """
        user = self._get_user_by_username(username)
        if not user:
            logger.warning(f"Login failed: User not found - {username}")
            return None

        # Check if locked
        if user.locked_until:
            locked = datetime.fromisoformat(user.locked_until)
            if datetime.now() < locked:
                logger.warning(f"Login failed: Account locked - {username}")
                return None
            else:
                user.locked_until = None
                user.failed_attempts = 0

        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                logger.warning(f"Account locked due to failed attempts: {username}")
            self._save_data()
            logger.warning(f"Login failed: Wrong password - {username}")
            return None

        # Success - reset failed attempts
        user.failed_attempts = 0
        user.last_login = datetime.now().isoformat()

        # Create token
        token_str = self._generate_token()
        expires = datetime.now() + timedelta(hours=self._token_expiry_hours)

        token = Token(
            token=token_str,
            user_id=user.id,
            created_at=datetime.now().isoformat(),
            expires_at=expires.isoformat()
        )

        self._tokens[token_str] = token
        self._save_data()

        logger.info(f"Login successful: {username}")
        return token_str

    def logout(self, token: str) -> bool:
        """Revoke a token (logout)."""
        if token in self._tokens:
            self._tokens[token].is_revoked = True
            self._save_data()
            return True
        return False

    def authenticate(self, token: str) -> Optional[User]:
        """
        Authenticate a token and return user.

        Args:
            token: Auth token

        Returns:
            User object or None if invalid
        """
        token_obj = self._tokens.get(token)
        if not token_obj or self._is_token_expired(token_obj):
            return None

        user = self._users.get(token_obj.user_id)
        if not user or not user.is_active:
            return None

        return user

    def check_permission(
        self,
        token_or_user: str | User,
        resource: str,
        container: Optional[str] = None
    ) -> bool:
        """
        Check if user has permission for a resource.

        Args:
            token_or_user: Auth token or User object
            resource: Resource path (e.g., "leg.j3", "data.write")
            container: Container context for LEG users

        Returns:
            True if permitted
        """
        # Get user
        if isinstance(token_or_user, str):
            user = self.authenticate(token_or_user)
        else:
            user = token_or_user

        if not user:
            return False

        user_level = AccessLevel[user.access_level]

        # HEAD has all access
        if user_level == AccessLevel.HEAD:
            return True

        # Check explicit permissions
        if resource in user.permissions:
            return True

        # Get required level for resource
        required_level = RESOURCE_PERMISSIONS.get(resource)
        if required_level is None:
            # Unknown resource - deny by default
            return False

        # Check level hierarchy
        if user_level.value >= required_level.value:
            # For LEG users, also check container restrictions
            if user_level == AccessLevel.LEG and container:
                if user.containers and container not in user.containers:
                    return False
            return True

        return False

    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user in self._users.values():
            if user.username.lower() == username.lower():
                return user
        return None

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.password_hash = self._hash_password(new_password)
        self._save_data()
        return True

    def set_access_level(self, user_id: str, access_level: AccessLevel) -> bool:
        """Update user access level."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.access_level = access_level.name
        self._save_data()
        return True

    def add_container(self, user_id: str, container: str) -> bool:
        """Add container access for LEG user."""
        user = self._users.get(user_id)
        if not user:
            return False

        if container not in user.containers:
            user.containers.append(container)
            self._save_data()
        return True

    def remove_container(self, user_id: str, container: str) -> bool:
        """Remove container access for LEG user."""
        user = self._users.get(user_id)
        if not user:
            return False

        if container in user.containers:
            user.containers.remove(container)
            self._save_data()
        return True

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.is_active = False

        # Revoke all tokens
        for token in self._tokens.values():
            if token.user_id == user_id:
                token.is_revoked = True

        self._save_data()
        return True

    def list_users(self, access_level: Optional[AccessLevel] = None) -> List[Dict]:
        """List users with optional filter."""
        users = []
        for user in self._users.values():
            if access_level and user.access_level != access_level.name:
                continue
            users.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "access_level": user.access_level,
                "containers": user.containers,
                "is_active": user.is_active,
                "last_login": user.last_login
            })
        return users

    def get_user_permissions(self, user: User) -> Set[str]:
        """Get all resources a user can access."""
        permissions = set()
        user_level = AccessLevel[user.access_level]

        for resource, required_level in RESOURCE_PERMISSIONS.items():
            if user_level.value >= required_level.value:
                permissions.add(resource)

        permissions.update(user.permissions)
        return permissions


# Convenience functions
_ac: Optional[AccessControl] = None


def authenticate(token: str) -> Optional[User]:
    """Authenticate token using default controller."""
    global _ac
    if _ac is None:
        _ac = AccessControl()
    return _ac.authenticate(token)


def check_permission(token: str, resource: str, container: Optional[str] = None) -> bool:
    """Check permission using default controller."""
    global _ac
    if _ac is None:
        _ac = AccessControl()
    return _ac.check_permission(token, resource, container)


def create_user(username: str, password: str, email: str, access_level: AccessLevel, **kwargs) -> str:
    """Create user using default controller."""
    global _ac
    if _ac is None:
        _ac = AccessControl()
    return _ac.create_user(username, password, email, access_level, **kwargs)


if __name__ == "__main__":
    print("TAIL LABIENUS Access Control - Demo")
    print("=" * 40)

    ac = AccessControl()

    # Create users at different levels
    try:
        claw_user = ac.create_user(
            "manager1", "password123", "manager@example.com",
            AccessLevel.CLAW
        )
        leg_user = ac.create_user(
            "worker1", "password123", "worker@example.com",
            AccessLevel.LEG,
            containers=["j3"]
        )
    except ValueError as e:
        print(f"Users may already exist: {e}")

    # Test login
    print("\nTesting logins:")
    commander_token = ac.login("commander", os.environ.get("SCORPION_COMMANDER_PASS", "changeme"))
    manager_token = ac.login("manager1", "password123")
    worker_token = ac.login("worker1", "password123")

    print(f"  Commander: {'OK' if commander_token else 'FAIL'}")
    print(f"  Manager: {'OK' if manager_token else 'FAIL'}")
    print(f"  Worker: {'OK' if worker_token else 'FAIL'}")

    # Test permissions
    print("\nTesting permissions:")
    tests = [
        ("Commander", commander_token, "system.config", None),
        ("Commander", commander_token, "leg.j3", "j3"),
        ("Manager", manager_token, "claw1.sales", None),
        ("Manager", manager_token, "system.config", None),
        ("Worker", worker_token, "leg.j3", "j3"),
        ("Worker", worker_token, "leg.nsipa", "nsipa"),
        ("Worker", worker_token, "data.read", None),
    ]

    for name, token, resource, container in tests:
        if token:
            result = ac.check_permission(token, resource, container)
            status = "✓" if result else "✗"
            print(f"  {status} {name} -> {resource}: {'ALLOWED' if result else 'DENIED'}")

    # Show user list
    print("\nUsers:")
    for user in ac.list_users():
        print(f"  - {user['username']} ({user['access_level']})")
