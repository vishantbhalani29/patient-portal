from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import engine, Base, SessionLocal
from app.api import health, appointments
from app.services.appointment_service import AppointmentService
from app.exceptions import StaleAppointmentException, ProviderScheduleConflictException

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

@app.exception_handler(StaleAppointmentException)
async def stale_appointment_exception_handler(request: Request, exc: StaleAppointmentException):
    return JSONResponse(
        status_code=409,
        content={
            "code": "STALE_APPOINTMENT",
            "message": "This appointment was updated by another user.",
            "current_version": exc.current_version
        }
    )

@app.exception_handler(ProviderScheduleConflictException)
async def provider_schedule_conflict_exception_handler(request: Request, exc: ProviderScheduleConflictException):
    return JSONResponse(
        status_code=409,
        content={
            "code": "PROVIDER_SCHEDULE_CONFLICT",
            "message": "The provider already has a confirmed appointment during this time."
        }
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
