
from fastapi import FastAPI
from sqlalchemy import text

from app.database.connection import engine
from app.routers.user import router as users_router

app = FastAPI(title="Attendance API")

app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "Attendance API is running!"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected"
        }

