"""
SCORPION Security System - Access Control
==========================================

This module manages authentication, authorization, and access control
for the SCORPION multi-tenant system.

SCORPION Architecture Role:
    Part of TAIL/Labienus - the security backbone
    Controls who can access what data and actions

Access Levels:
    HEAD (100): Master Charlie - complete system access
    CLAW (75): Senior operators - multi-client access
    LEG (50): Client users - single client access
    PUBLIC (10): Unauthenticated - public website only

Security Model:
    - JWT-based authentication
    - Role-based access control (RBAC)
    - Resource-level permissions
    - Automatic token expiration
    - Audit trail for all auth events

Author: SCORPION System
Version: 1.0.0
"""

import os
import json
import hashlib
import secrets
import hmac
import base64
from datetime import datetime, timedelta
from enum import IntEnum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
import logging

logger = logging.getLogger("scorpion.security")


class AccessLevel(IntEnum):
    """
    Access levels in the SCORPION hierarchy.

    Higher numbers = more access.
    Each level can access resources at or below their level.
    """
    PUBLIC = 10      # Website visitors, no authenticated access
    LEG = 50         # Client users, access to their single client only
    CLAW = 75        # Senior operators, access to assigned clients
    HEAD = 100       # Master Charlie, complete system access


class Permission:
    """Permission constants for resource actions."""
    # Lead permissions
    LEAD_VIEW = "lead:view"
    LEAD_CREATE = "lead:create"
    LEAD_UPDATE = "lead:update"
    LEAD_DELETE = "lead:delete"
    LEAD_EXPORT = "lead:export"

    # Baby (AI) permissions
    BABY_QUERY = "baby:query"
    BABY_CONFIGURE = "baby:configure"

    # Report permissions
    REPORT_VIEW = "report:view"
    REPORT_GENERATE = "report:generate"
    REPORT_EXPORT = "report:export"

    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_CLIENTS = "admin:clients"
    ADMIN_AUDIT = "admin:audit"
    ADMIN_SYSTEM = "admin:system"

    # Client permissions
    CLIENT_VIEW = "client:view"
    CLIENT_SETTINGS = "client:settings"

    # Default permission sets by level
    LEG_PERMISSIONS = {
        LEAD_VIEW, LEAD_CREATE, LEAD_UPDATE,
        BABY_QUERY,
        REPORT_VIEW,
        CLIENT_VIEW,
    }

    CLAW_PERMISSIONS = LEG_PERMISSIONS | {
        LEAD_DELETE, LEAD_EXPORT,
        REPORT_GENERATE, REPORT_EXPORT,
        CLIENT_SETTINGS,
    }

    HEAD_PERMISSIONS = CLAW_PERMISSIONS | {
        BABY_CONFIGURE,
        ADMIN_USERS, ADMIN_CLIENTS, ADMIN_AUDIT, ADMIN_SYSTEM,
    }


@dataclass
class TokenData:
    """Data encoded in a JWT token."""
    user_id: str
    access_level: AccessLevel
    assigned_clients: List[str]
    issued_at: datetime
    expires_at: datetime
    token_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "access_level": self.access_level.value,
            "assigned_clients": self.assigned_clients,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "token_id": self.token_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenData':
        return cls(
            user_id=data["user_id"],
            access_level=AccessLevel(data["access_level"]),
            assigned_clients=data["assigned_clients"],
            issued_at=datetime.fromisoformat(data["issued_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            token_id=data["token_id"],
        )


@dataclass
class User:
    """A SCORPION system user."""
    id: str
    name: str
    email: str
    level: AccessLevel
    assigned_clients: List[str]
    token: Optional[str]
    created: datetime
    last_login: Optional[datetime]
    active: bool = True
    permissions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "level": self.level.value,
            "level_name": self.level.name,
            "assigned_clients": self.assigned_clients,
            "token": self.token,
            "created": self.created.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "active": self.active,
            "permissions": list(self.permissions),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            level=AccessLevel(data["level"]),
            assigned_clients=data["assigned_clients"],
            token=data.get("token"),
            created=datetime.fromisoformat(data["created"]),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            active=data.get("active", True),
            permissions=set(data.get("permissions", [])),
            metadata=data.get("metadata", {}),
        )


class AccessControl:
    """
    SCORPION Access Control System.

    Manages user authentication, authorization, and access control.
    Part of the Labienus security module (TAIL).

    Security Features:
    - JWT-like token generation and validation
    - Role-based access control
    - Client isolation
    - Token revocation
    - Automatic expiration

    Usage:
        ac = AccessControl()
        user = ac.create_user("John", "john@example.com", AccessLevel.LEG, ["j3_structural"])
        token = ac.generate_token(user.id)
        validated_user = ac.authenticate(token)
        can_access = ac.check_permission(user, "leads", "view")
    """

    def __init__(self, data_dir: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize access control system.

        Args:
            data_dir: Directory for storing user data
            secret_key: Secret key for token signing (generated if not provided)
        """
        self.data_dir = Path(data_dir) if data_dir else Path("./data/security")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._secret_key = secret_key or os.environ.get("SCORPION_SECRET_KEY") or secrets.token_hex(32)
        self._users: Dict[str, User] = {}
        self._revoked_tokens: Set[str] = set()
        self._token_to_user: Dict[str, str] = {}

        # Load existing data
        self._load_data()

        # Ensure HEAD user exists
        self._ensure_head_user()

        logger.info("AccessControl initialized")

    def _load_data(self) -> None:
        """Load users and revoked tokens from disk."""
        users_file = self.data_dir / "users.json"
        if users_file.exists():
            try:
                with open(users_file, 'r') as f:
                    data = json.load(f)
                    for user_data in data.get("users", []):
                        user = User.from_dict(user_data)
                        self._users[user.id] = user
                        if user.token:
                            self._token_to_user[user.token] = user.id
                    self._revoked_tokens = set(data.get("revoked_tokens", []))
            except Exception as e:
                logger.error(f"Error loading access control data: {e}")

    def _save_data(self) -> None:
        """Save users and revoked tokens to disk."""
        users_file = self.data_dir / "users.json"
        try:
            data = {
                "users": [user.to_dict() for user in self._users.values()],
                "revoked_tokens": list(self._revoked_tokens)[-1000:],  # Keep last 1000
            }
            with open(users_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving access control data: {e}")

    def _ensure_head_user(self) -> None:
        """Ensure the HEAD (Master Charlie) user exists."""
        head_users = [u for u in self._users.values() if u.level == AccessLevel.HEAD]
        if not head_users:
            self.create_user(
                name="Master Charlie",
                email="charlie@scorpion.local",
                level=AccessLevel.HEAD,
                assigned_clients=["*"],  # All clients
                user_id="head_charlie"
            )
            logger.info("Created HEAD user: Master Charlie")

    def create_user(
        self,
        name: str,
        email: str,
        level: AccessLevel,
        assigned_clients: List[str],
        user_id: Optional[str] = None
    ) -> User:
        """
        Create a new user.

        Args:
            name: User's display name
            email: User's email address
            level: Access level (HEAD, CLAW, LEG, PUBLIC)
            assigned_clients: List of client IDs user can access
            user_id: Optional specific user ID

        Returns:
            Created User object
        """
        if user_id is None:
            user_id = f"user_{secrets.token_hex(8)}"

        # Check if email already exists
        existing = next((u for u in self._users.values() if u.email == email), None)
        if existing:
            raise ValueError(f"User with email {email} already exists")

        # Assign default permissions based on level
        if level == AccessLevel.HEAD:
            permissions = Permission.HEAD_PERMISSIONS.copy()
        elif level == AccessLevel.CLAW:
            permissions = Permission.CLAW_PERMISSIONS.copy()
        elif level == AccessLevel.LEG:
            permissions = Permission.LEG_PERMISSIONS.copy()
        else:
            permissions = set()

        user = User(
            id=user_id,
            name=name,
            email=email,
            level=level,
            assigned_clients=assigned_clients,
            token=None,
            created=datetime.now(),
            last_login=None,
            permissions=permissions,
        )

        self._users[user_id] = user
        self._save_data()

        logger.info(f"Created user: {name} ({email}) with level {level.name}")

        return user

    def authenticate(self, token: str) -> Optional[User]:
        """
        Authenticate a user by their token.

        Args:
            token: JWT-like token string

        Returns:
            User object if valid, None otherwise
        """
        if not token or token in self._revoked_tokens:
            return None

        try:
            # Decode and verify token
            token_data = self._decode_token(token)
            if not token_data:
                return None

            # Check expiration
            if datetime.now() > token_data.expires_at:
                logger.warning(f"Token expired for user {token_data.user_id}")
                return None

            # Get user
            user = self._users.get(token_data.user_id)
            if not user or not user.active:
                return None

            # Update last login
            user.last_login = datetime.now()
            self._save_data()

            return user

        except Exception as e:
            logger.error(f"Token authentication error: {e}")
            return None

    def generate_token(self, user_id: str, expiry_hours: int = 24) -> str:
        """
        Generate a new authentication token for a user.

        Args:
            user_id: User ID to generate token for
            expiry_hours: Hours until token expires (default 24)

        Returns:
            JWT-like token string
        """
        user = self._users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        now = datetime.now()
        token_id = secrets.token_hex(16)

        token_data = TokenData(
            user_id=user_id,
            access_level=user.level,
            assigned_clients=user.assigned_clients,
            issued_at=now,
            expires_at=now + timedelta(hours=expiry_hours),
            token_id=token_id,
        )

        token = self._encode_token(token_data)

        # Update user's current token
        if user.token:
            self._token_to_user.pop(user.token, None)
        user.token = token
        self._token_to_user[token] = user_id
        self._save_data()

        logger.info(f"Generated token for user {user_id}, expires in {expiry_hours} hours")

        return token

    def refresh_token(self, old_token: str) -> Optional[str]:
        """
        Refresh an existing token.

        Args:
            old_token: Current valid token

        Returns:
            New token string, or None if old token invalid
        """
        user = self.authenticate(old_token)
        if not user:
            return None

        # Revoke old token
        self.revoke_token(old_token)

        # Generate new token
        return self.generate_token(user.id)

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token, preventing further use.

        Args:
            token: Token to revoke

        Returns:
            True if revoked, False if token not found
        """
        if not token:
            return False

        self._revoked_tokens.add(token)

        user_id = self._token_to_user.pop(token, None)
        if user_id and user_id in self._users:
            self._users[user_id].token = None

        self._save_data()
        logger.info(f"Revoked token for user {user_id}")

        return True

    def check_permission(
        self,
        user: User,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if a user has permission for an action on a resource.

        Args:
            user: User object
            resource: Resource type (e.g., "leads", "reports")
            action: Action type (e.g., "view", "create", "delete")

        Returns:
            True if permitted, False otherwise
        """
        if not user or not user.active:
            return False

        # HEAD can do everything
        if user.level == AccessLevel.HEAD:
            return True

        # Check specific permission
        permission_key = f"{resource}:{action}"
        if permission_key in user.permissions:
            return True

        # Check if action is allowed for user's level
        if user.level == AccessLevel.CLAW:
            return permission_key in Permission.CLAW_PERMISSIONS
        elif user.level == AccessLevel.LEG:
            return permission_key in Permission.LEG_PERMISSIONS

        return False

    def get_accessible_clients(self, user: User) -> List[str]:
        """
        Get list of client IDs a user can access.

        Args:
            user: User object

        Returns:
            List of client IDs
        """
        if not user or not user.active:
            return []

        # HEAD can access all clients
        if user.level == AccessLevel.HEAD or "*" in user.assigned_clients:
            from legs import AVAILABLE_LEGS
            return list(AVAILABLE_LEGS.keys())

        return user.assigned_clients

    def can_access_client(self, user: User, client_id: str) -> bool:
        """
        Check if a user can access a specific client.

        Args:
            user: User object
            client_id: Client ID to check

        Returns:
            True if user can access client
        """
        if not user or not user.active:
            return False

        if user.level == AccessLevel.HEAD:
            return True

        if "*" in user.assigned_clients:
            return True

        return client_id in user.assigned_clients

    def _encode_token(self, token_data: TokenData) -> str:
        """Encode token data into a signed string."""
        payload = json.dumps(token_data.to_dict()).encode()
        payload_b64 = base64.urlsafe_b64encode(payload).decode()

        signature = hmac.new(
            self._secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{payload_b64}.{signature}"

    def _decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and verify a token string."""
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return None

            payload_b64, signature = parts

            # Verify signature
            expected_sig = hmac.new(
                self._secret_key.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                logger.warning("Token signature verification failed")
                return None

            # Decode payload
            payload = base64.urlsafe_b64decode(payload_b64.encode())
            data = json.loads(payload)

            return TokenData.from_dict(data)

        except Exception as e:
            logger.error(f"Token decode error: {e}")
            return None

    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        return next((u for u in self._users.values() if u.email == email), None)

    def list_users(self, level: Optional[AccessLevel] = None) -> List[User]:
        """List all users, optionally filtered by level."""
        users = list(self._users.values())
        if level is not None:
            users = [u for u in users if u.level == level]
        return users

    def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[User]:
        """
        Update a user's information.

        Args:
            user_id: User ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated User object or None if not found
        """
        user = self._users.get(user_id)
        if not user:
            return None

        allowed_updates = {"name", "email", "assigned_clients", "active", "metadata"}

        for key, value in updates.items():
            if key in allowed_updates:
                setattr(user, key, value)

        self._save_data()
        logger.info(f"Updated user {user_id}: {list(updates.keys())}")

        return user

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.active = False
        if user.token:
            self.revoke_token(user.token)

        self._save_data()
        logger.info(f"Deactivated user {user_id}")

        return True

    def grant_permission(self, user_id: str, permission: str) -> bool:
        """Grant a specific permission to a user."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.permissions.add(permission)
        self._save_data()
        logger.info(f"Granted {permission} to user {user_id}")

        return True

    def revoke_permission(self, user_id: str, permission: str) -> bool:
        """Revoke a specific permission from a user."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.permissions.discard(permission)
        self._save_data()
        logger.info(f"Revoked {permission} from user {user_id}")

        return True
