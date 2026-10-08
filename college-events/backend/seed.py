import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.abspath("."))

from app.database import get_engine
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.user import User

def seed():
    with Session(get_engine()) as db:
        user = db.query(User).filter(User.role == "organizer").first()
        if not user:
            user = db.query(User).first()
            
        if not user:
            print("No users found. Creating a dummy admin user.")
            from app.security import hash_password
            user = User(
                email="admin@example.com",
                full_name="Admin User",
                hashed_password=hash_password("password"),
                role="admin",
                is_active=True
            )
            db.add(user)
            db.flush()
            
        now = datetime.now(timezone.utc)
        evt = Event(
            title="Welcome Party 2026",
            description="Kick off the semester with our annual Welcome Party! Food, music, and great company.",
            category="Entertainment",
            venue="Main Auditorium",
            capacity=200,
            start_time=now + timedelta(days=2, hours=10),
            end_time=now + timedelta(days=2, hours=15),
            registration_deadline=now + timedelta(days=1, hours=23),
            organizer_id=user.id,
            slug="welcome-party-2026",
            status="PUBLISHED"
        )
        
        db.add(evt)
        db.commit()
        print("Dummy event created!")
        
if __name__ == "__main__":
    seed()
