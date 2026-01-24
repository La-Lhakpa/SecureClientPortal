import argparse
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User
from .core.security import hash_password as get_password_hash


def seed(owner_email: str, owner_password: str, client_email: str, client_password: str):
    db: Session = SessionLocal()
    try:
        if not db.query(User).filter(User.email == owner_email).first():
            db.add(User(email=owner_email, password_hash=get_password_hash(owner_password), role="OWNER"))
        if not db.query(User).filter(User.email == client_email).first():
            db.add(User(email=client_email, password_hash=get_password_hash(client_password), role="CLIENT"))
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(prog="seed", description="Seed initial OWNER and CLIENT users.")
    parser.add_argument("--owner-email", required=True)
    parser.add_argument("--owner-password", required=True)
    parser.add_argument("--client-email", required=True)
    parser.add_argument("--client-password", required=True)
    args = parser.parse_args()
    seed(args.owner_email, args.owner_password, args.client_email, args.client_password)


if __name__ == "__main__":
    main()

