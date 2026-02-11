from config import get_settings, Base
from typing import List, Dict
from uuid import uuid4 as uuid

from sqlalchemy import create_engine, Select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from auth_service.models import (
    User,
    Roles,
    Permissions,
    RolePermissions,
    UserRoles,
    ROLE,
    PERMISSIONS,
)

from utils import get_password_hash

from fastapi.concurrency import run_in_threadpool

settings = get_settings()
DATABASE_URL = settings.database_url
CELERY_BACKEND_URL = settings.celery_backend_url

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


async def create_super_admin():
    email = settings.super_admin_email
    password = settings.super_admin_password
    if not email or not password:
        raise RuntimeError("Superadmin credentials not set in environment")
    with Session() as db_session:
        if existing_user := db_session.query(User).filter(User.email == email).first():
            return existing_user

        if not (
            role := db_session.query(Roles)
            .filter(Roles.role_type == ROLE.SUPER_ADMIN)
            .first()
        ):
            super_admin_role = Roles(role_type=ROLE.SUPER_ADMIN)
            db_session.add(super_admin_role)
            db_session.flush()
        existing_permissions: List[Permissions] = (
            db_session.execute(Select(Permissions)).scalars().all()
        )
        permission_types_map: Dict[PERMISSIONS, Permissions] = {
            permission.permission_type: permission
            for permission in existing_permissions
        }
        for permission in PERMISSIONS:
            if permission_types_map.get(permission) is None:
                value: Permissions = Permissions(permission_type=permission)
                db_session.add(value)
                permission_types_map[permission] = value
        db_session.flush()
        super_admin_role_permissions: List[Dict[str, uuid]] = [
            {"role_id": super_admin_role.id, "permission_id": permission_obj.id}
            for permission_obj in permission_types_map.values()
        ]
        stmt = (
            insert(RolePermissions)
            .values(super_admin_role_permissions)
            .on_conflict_do_nothing(index_elements=["role_id", "permission_id"])
        )
        db_session.execute(stmt)

        password_hash = await run_in_threadpool(get_password_hash, password)
        user = User(
            name=settings.super_admin_name,
            email=email,
            password=password_hash,
            phone_number=settings.super_admin_phone_number,
        )
        db_session.add(user)
        db_session.flush()

        user_roles = UserRoles(user_id=user.id, role_id=super_admin_role.id)
        db_session.add(user_roles)
        db_session.flush()

        db_session.commit()
