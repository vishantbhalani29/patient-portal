from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.api import health, appointments
from app.services.appointment_service import AppointmentService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    # Seed deterministic demo data
    db = SessionLocal()
    try:
        AppointmentService.seed_data(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="Patient Portal API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(appointments.router, prefix="/api", tags=["Appointments"])
