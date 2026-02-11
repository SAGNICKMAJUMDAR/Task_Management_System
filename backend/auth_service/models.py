from datetime import datetime
import enum
import uuid
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, Integer
from sqlalchemy import Integer, String, ForeignKey, DateTime, Boolean, Column, Index

from config import Base


class ROLE(enum.IntEnum):
    SUPER_ADMIN = 1
    ADMIN = 2
    MANAGER = 3
    USER = 4


class PERMISSIONS(enum.IntEnum):
    TASK_READ = 1
    TASK_CREATE = 2
    TASK_UPDATE = 3
    TASK_DELETE = 4


class IntEnumType(TypeDecorator):
    impl = Integer
    cache_ok = True

    def __init__(self, enum_class):
        self.enum_class = enum_class
        super().__init__()

    def process_bind_param(self, value, dialect):
        return value.value if value else None

    def process_result_value(self, value, dialect):
        return self.enum_class(value) if value else None


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(225), nullable=False)
    email = Column(String(225), unique=True, nullable=False)
    password = Column(String(225), nullable=False)
    phone_number = Column(String(225), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    roles = relationship(
        "UserRoles",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="user",
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_phone", "phone_number"),
        Index("idx_users_active", "is_active"),
    )


class Otp(Base):

    __tablename__ = "otp"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    otp_code = Column(Integer)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_otp_user", "user_id"),
        Index("idx_otp_code", "otp_code"),
        Index("idx_otp_expiry", "expires_at"),
    )


class Roles(Base):

    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_type = Column(IntEnumType(ROLE), nullable=False)
    users = relationship(
        "UserRoles",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="role",
    )

    permissions = relationship(
        "RolePermissions",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (Index("idx_roles_type", "role_type"),)


class UserRoles(Base):

    __tablename__ = "user_roles"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )

    user = relationship("User", back_populates="roles")

    role = relationship("Roles", back_populates="users")

    __table_args__ = (
        Index("idx_user_roles_user", "user_id"),
        Index("idx_user_roles_role", "role_id"),
    )


class Permissions(Base):

    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permission_type = Column(IntEnumType(PERMISSIONS), nullable=False)
    description = Column(String(255), nullable=True)

    __table_args__ = (Index("idx_permissions_type", "permission_type"),)


class RolePermissions(Base):
    __tablename__ = "roles_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(
        UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True
    )

    __table_args__ = (Index("idx_role_permissions_permission", "permission_id"),)


class RefreshTokens(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    expires_at = Column(DateTime, nullable=False)
    token = Column(String(225), nullable=False)
    is_revoked = Column(Boolean, nullable=False, default=False)
    token_replaced_by = Column(String(225), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_refresh_user", "user_id"),
        Index("idx_refresh_token", "token"),
        Index("idx_refresh_expiry", "expires_at"),
        Index("idx_refresh_revoked", "is_revoked"),
    )
