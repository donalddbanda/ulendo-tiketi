## `backend/README.md`

```markdown
# Ulendo Tiketi – Backend

## Overview

This directory contains the **Flask**-based backend implementation for the **Ulendo Tiketi** platform. The backend exposes a RESTful API that supports user authentication, bus company management, route and schedule handling, booking workflows, QR code generation, payment integration via PayChangu, and cashout processing as outlined in the project specification (Ulendo Tiketi.pdf).

Key technologies:
- **Python 3.11+**
- **Flask** (with Blueprints for modular routing)
- **SQLAlchemy** (ORM)
- **Flask-Migrate** (Alembic) for database migrations
- **uv** for dependency management (`uv.lock`, `pyproject.toml`)
- **PostgreSQL** (recommended production DB)
- **qrcode** and **Pillow** for QR code generation

All database models are consolidated in a single file (`models.py`) to streamline maintenance and migrations.

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Flask app factory, Blueprint registration
│   ├── config.py           # Configuration classes (Development, Production, Testing)
│   ├── models.py            # All SQLAlchemy models (Users, BusCompanies, Buses, etc.)
│   ├── blueprints/
│   │   ├── auth.py          # /register, /login, /reset-password
│   │   ├── companies.py     # /bus-companies, /buses
│   │   ├── routes.py        # /routes, /schedules
│   │   ├── bookings.py      # /bookings, /bookings/{id}/cancel, QR endpoints
│   │   ├── cashouts.py      # /cashouts/request, /cashouts
│   │   └── search.py        # /search
│   ├── utils/
│   │   ├── qr_generator.py  # QR code creation for bookings
│   │   └── payments.py      # PayChangu integration helpers
│   └── extensions.py        # db, migrate, bcrypt, etc.
├── migrations/              # Alembic migration scripts
├── tests/                   # Pytest suite
├── .env                     # Local environment variables (not committed)
├── .gitignore
├── pyproject.toml
├── uv.lock
├── run.py                   # Entry point for development
└── README.md
```

---

## API Endpoints (Summary)

| Category      | Method | Endpoint                      | Description |
|---------------|--------|-------------------------------|-------------|
| Authentication | POST   | `/register`                   | Register a new user |
| Authentication | POST   | `/login`                      | Login to the platform |
| Authentication | POST   | `/reset-password`             | Request a password reset link |
| Bus Companies  | POST   | `/bus-companies`              | Register a new bus company (admin) |
| Bus Companies  | GET    | `/bus-companies`              | View all companies |
| Bus Companies  | GET    | `/bus-companies/{id}`         | View specific company details |
| Buses          | POST   | `/buses`                      | Add a bus (admin/company) |
| Buses          | GET    | `/buses`                      | View all buses |
| Routes         | POST   | `/routes`                     | Create a new route |
| Routes         | GET    | `/routes`                     | View all routes |
| Schedules      | POST   | `/schedules`                  | Create schedule for a bus |
| Schedules      | GET    | `/schedules`                  | Get all available schedules |
| Bookings       | POST   | `/bookings`                   | Book a seat |
| Bookings       | GET    | `/bookings`                   | View all bookings for a user or company |
| Bookings       | PUT    | `/bookings/{id}/cancel`       | Cancel booking (within 24 hours before departure) |
| QR Code        | GET    | `/bookings/{id}/generate-qr`  | Generate QR code for a booking |
| QR Code        | POST   | `/bookings/scan-qr`           | Verify booking via QR scan |
| Cashouts       | POST   | `/cashouts/request`           | Company requests withdrawal |
| Cashouts       | GET    | `/cashouts`                   | View company’s cashout history |
| Search         | GET    | `/search`                     | Search routes and schedules by origin, destination, and date |

Full OpenAPI/Swagger documentation will be generated at `/api/docs` in development.

---

## Setup & Installation

1. **Clone the repository** (ensure you are on the appropriate branch).
2. **Navigate to backend directory**:
   ```bash
   cd backend
   ```
3. **Install dependencies with uv**:
   ```bash
   uv sync
   ```
4. **Set up environment variables** (copy `.env.example` → `.env` and fill in values):
   ```env
   FLASK_APP=run.py
   FLASK_ENV=development
   DATABASE_URL=postgresql://user:password@localhost/ulendo_db
   SECRET_KEY=your-secret-key
   PAYCHANGU_API_KEY=your-paychangu-key
   MAIL_SERVER=smtp.example.com
   MAIL_USERNAME=...
   ```
5. **Initialize the database**:
   ```bash
   flask db init    # (only once)
   flask db migrate
   flask db upgrade
   ```
6. **Run the development server**:
   ```bash
   uv run flask run
   ```

---

## Branching Policy

- **`main`** – Contains **production-ready**, fully tested code only.
- **Feature branches** – All development must occur on dedicated branches:
  - Naming: `feature/<short-description>` or `bugfix/<issue>`
  - Example: `feature/booking-cancellation-endpoint`
- **Pull Requests** – Required for merging into `main`. Must pass CI and be reviewed by at least one backend maintainer.

---

## Testing

```bash
uv run pytest -v
```

Tests are located in `tests/` and cover:
- Model integrity
- API endpoint responses
- Authentication flows
- Booking and cancellation logic
- QR code generation
- Payment and cashout simulation

---

## Deployment

1. Push `main` to production repository.
2. CI/CD pipeline (GitHub Actions) will:
   - Run tests
   - Build Docker image
   - Deploy to staging/production via Docker Compose or Kubernetes
3. Use `gunicorn` + `nginx` in production.

---

## Contributing

See the root-level `README.md` **Contribution Guidelines** section for complete instructions.

---

*Maintained by the Backend Developer – Donald Banda*
```
