from app.database.connection import Base, engine
from app.models import (
    User,
    Organization,
    OrganizationMember,
    Person,
    Attendance,
)


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()