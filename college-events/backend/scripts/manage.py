"""Trusted local administration. Never exposed through the HTTP API."""
import argparse
import getpass
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import Role, User
from app.security import hash_password
from app.services.auth_service import set_password


def read_password() -> str:
    password = getpass.getpass("Password (12–128 characters): ")
    if not 12 <= len(password) <= 128:
        raise ValueError("Password must contain 12–128 characters.")
    if password != getpass.getpass("Repeat password: "):
        raise ValueError("Passwords do not match.")
    return password


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-manager", help="Create a new event manager.")
    create.add_argument("--email", required=True)
    create.add_argument("--full-name", required=True)
    create.add_argument("--authorize", action="store_true", required=True,
                        help="Attest that you are authorized to administer this database.")
    reset = commands.add_parser("reset-password", help="Reset an account's password locally.")
    reset.add_argument("--email", required=True)
    reset.add_argument("--authorize", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if not sys.stdin.isatty():
            raise ValueError("Run this command in a trusted interactive terminal.")
        email = str(TypeAdapter(EmailStr).validate_python(args.email.strip().lower()))
        password = read_password()
        with Session(get_engine()) as db, db.begin():
            user = db.scalar(select(User).where(User.email == email).with_for_update())
            if args.command == "create-manager":
                if user:
                    raise ValueError("An account with this email already exists; roles are not changed.")
                full_name = args.full_name.strip()
                if not 2 <= len(full_name) <= 120:
                    raise ValueError("Full name must contain 2–120 characters.")
                db.add(User(full_name=full_name, email=email, role=Role.MANAGER,
                            password_hash=hash_password(password)))
            else:
                if not user:
                    raise ValueError("Account not found.")
                set_password(user, password)
        print("Manager created." if args.command == "create-manager" else "Password reset.")
        return 0
    except (ValueError, ValidationError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("Database operation failed. Check connectivity and apply migrations.", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Cancelled.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
