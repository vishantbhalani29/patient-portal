# Patient Portal App

A full-stack Patient Portal application built with FastAPI, React, TypeScript, SQLAlchemy, and SQLite. The application allows patients to request appointments while providers confirm, reschedule, and manage their schedules.

## Tech Stack

### Frontend
- React 19
- TypeScript
- Vite
- Vanilla CSS

### Backend
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite

### Testing
- Pytest (41 automated backend tests)

## Features

### Patient
- View upcoming appointments
- Request a new appointment
- Cancel confirmed appointments
- Automatic refresh after stale updates (409 Conflict)

### Provider
- View assigned appointments
- Confirm pending appointments
- Reschedule appointments
- View complete appointment history

## Engineering Problems Solved

### 1. Optimistic Concurrency Control

Appointments use version-based optimistic concurrency.

If a client submits an outdated version, the API returns:

- **HTTP 409 Conflict**
- Current version information
- No data is overwritten

### 2. Immutable Audit History

Every successful mutation creates an append-only audit event containing:

- Before state
- After state
- Actor
- Action
- Timestamp

### 3. Asynchronous Notifications

Appointment confirmation schedules a background notification using FastAPI `BackgroundTasks`.

The notification is intentionally a stub that logs:

> Would send appointment confirmation email...

Confirmation never fails because of notification delivery.

### 4. Provider Schedule Protection

The backend prevents overlapping confirmed appointments for the same provider using server-side validation.

Adjacent appointments are allowed.

## Running Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Backend: http://127.0.0.1:8000

Frontend: http://localhost:5173

## Test

```bash
cd backend
pytest
```

Current result:

**41 passed**

## Demo Personas

| Role | User |
|------|------|
| Patient | Olivia Carter (`patient-001`) |
| Provider | Dr. Ethan Brooks (`provider-001`) |

## Timezone

- Database stores all timestamps in **UTC**
- API exchanges UTC ISO timestamps
- Frontend displays all dates in **Indian Standard Time (Asia/Kolkata)**

## Project Structure

```text
backend/
frontend/
README.md
AI_SESSION_TRANSCRIPT.md
```