import sys
import os

# Ensure the project root is in sys.path so `app` is importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.db.session import SessionLocal, engine, Base
from app.models.user import User, Role, Permission
from app.core.security import hash_password

ROLE_PERMISSIONS = {
    "Admin":   ["full_access"],
    "Analyst": ["upload_document", "edit_document", "view_document", "delete_document"],
    "Auditor": ["view_document", "review_document"],
    "Client":  ["view_document"],
}


def seed():
    # Auto-create tables in case alembic hasn't been run
    import app.models.user  # noqa
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        perm_cache: dict = {}

        for role_name, perm_names in ROLE_PERMISSIONS.items():
            for pname in perm_names:
                if pname not in perm_cache:
                    perm = db.query(Permission).filter(Permission.name == pname).first()
                    if not perm:
                        perm = Permission(name=pname, description=pname.replace("_", " ").title())
                        db.add(perm)
                        db.flush()
                    perm_cache[pname] = perm

            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=f"Default {role_name} role")
                db.add(role)
                db.flush()

            for pname in perm_names:
                if perm_cache[pname] not in role.permissions:
                    role.permissions.append(perm_cache[pname])

        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
            )
            db.add(admin)
            db.flush()

        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if admin_role and admin_role not in admin.roles:
            admin.roles.append(admin_role)

        db.commit()
        print("=" * 45)
        print("  Seed complete!")
        print("  Admin login → username: admin")
        print("              → password: admin123")
        print("=" * 45)

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
