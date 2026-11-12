# The Portfolia

The Portfolia is a skills-first career development SaaS platform designed to help students build evidence-backed portfolios, collaborate in teams, and become discoverable to colleges, companies, and investors.

## Architecture summary

The platform is structured around five core stakeholder journeys:

- Students: register, track learning, upload proof, build portfolios, collaborate, and discover opportunities.
- Colleges: verify students, monitor skill development, endorse achievements, and run reports.
- Companies: publish opportunities, discover talent by evidence and skill, and manage hiring.
- Investors: discover promising teams, project portfolios, and high-potential talent.
- Super-admin: manage users, institutions, roles, settings, and platform health.

## Product architecture

```text
Browser / Web App
  -> Cloudflare Pages (frontend)
  -> FastAPI REST API
     -> SQLAlchemy + PostgreSQL
     -> RBAC + permissions checks
     -> email verification, password reset, audit logs
     -> portfolio, learning, team, and opportunity modules
```

## System design principles

1. Skills over certificates.
2. Practical work over theoretical claims.
3. Verified capability over self-declared skills.
4. Collaboration over isolated learning.
5. Human review for consequential decisions.

## Stage 1 implementation scope

This repo contains the AI-free foundation for Stage 1:

- secure authentication
- student profile and Port ID generation
- learning activity tracking
- skill assessment scaffolding
- portfolio scaffolding
- team and project collaboration basics
- opportunities and support modules
- role-based dashboards and administrator controls
- automated tests for core auth flows

## Approved technology stack

- Frontend: HTML5, CSS3, JavaScript, Fetch API
- Backend: FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, Uvicorn
- Database: PostgreSQL-first configuration with local SQLite fallback for easier local development
- Security: Argon2id password hashing, short-lived sessions, RBAC
- Testing: Pytest, HTTPX

## Development plan

### Phase 1 — Product and architecture
- confirm stakeholder journeys
- define roles and permissions
- document core modules and API contracts
- define security, privacy, and multi-tenant controls

### Phase 2 — Project setup
- create backend/frontend folders
- configure environment variables
- set up Python dependencies
- validate local database connectivity

### Phase 3 — Database and models
- create user and role models
- add student, institution, company, and investor profiles
- add audit and support tables
- create migratable schema

### Phase 4 — Authentication and RBAC
- registration and login
- email verification and password reset workflow
- access control and admin bootstrap

### Phase 5 — Student modules
- learning journeys and activities
- assessments and portfolio records
- team/project creation and collaboration

### Phase 6 — Institutional, company, and investor modules
- institution verification flows
- company opportunity management
- investor discovery and connections

### Phase 7 — Admin and deployment readiness
- platform operations, audit logs, health checks
- production configuration and documentation

## Local development

Windows PowerShell:

```powershell
cd D:\Projects\the-portfolia
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the frontend pages from the `frontend` folder or serve them with a lightweight static server if needed.

## Core API endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/health`

## Student portal

The student portal is served from `frontend/students/dashboard.html`. Its
sections use the authenticated API and load the student's persisted records;
the dashboard does not fill missing metrics with sample data. The main API
groups are:

| Module | API routes |
| --- | --- |
| Dashboard and profile | `/api/v1/students/...` and `/api/v1/students/me` |
| Skills | `/api/v1/students/skills` |
| Learning | `/api/v1/learning/paths`, `/milestones`, `/resources`, `/progress`, and `/timeline` |
| Skill assessments | `/api/v1/assessments` and `/api/v1/assessments/attempts` |
| Portfolio | `/api/v1/portfolios/projects`, `/certifications`, `/achievements`, and `/experience` |
| Teams and workspace | `/api/v1/teams` and `/api/v1/teams/{team_id}/tasks` or `/contributions` |
| Opportunities | `/api/v1/opportunities` and `/api/v1/opportunities/applications` |
| Support | `/api/v1/support/tickets` |
| Account | `/api/v1/students/settings`, `/password`, `/sessions`, and `/notifications` |

Protected student routes require a student account. API documentation is
available at `http://localhost:8000/docs` while the API is running.

## Database migrations

Apply the schema migrations from the repository root after setting
`DATABASE_URL` in `.env`:

```powershell
python -m alembic upgrade head
```

For a new local database, copy `.env.example` to `.env` first; the default
`DATABASE_URL` uses SQLite. Migrations are additive and preserve existing
records.

## Local frontend

Run the API and static frontend in separate PowerShell terminals. Port 8080 is
included in the default development CORS origins:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
python -m http.server 8080 --directory frontend
```

Then open `http://localhost:8080/students/dashboard.html`.

## Admin console

Open `http://localhost:8080/admin/`. The same page provides a separate admin
registration form and the authenticated console. Admin registration is disabled
unless the API operator sets a strong, private `ADMIN_REGISTRATION_KEY` in
`.env` before starting the API. Do not publish or commit that key. The admin
password must be at least 12 characters.

The admin console includes real database-backed user and organization review,
account verification and activation controls, opportunity moderation, support
ticket responses and status changes, platform metrics, and audit activity.
Protected admin APIs require an account with the server-side `admin` or
`super-admin` role; the registration form assigns the ordinary `admin` role,
not `super-admin`.

The **Students** section supports paginated search, account creation, profile
editing, password resets, activation and verification, and permanent account
deletion. Admins can manage student skills, learning activities and paths,
milestones, resources, portfolio projects, certifications, achievements, work
experience, and teams. The student record view also manages notifications,
applications and saved opportunities, account settings, team memberships and
invitations, workspace tasks and contributions, and session revocation.
Assessment attempts can be reviewed or removed, but their scores and answers
cannot be edited. Support history links to the support workflow for replies and
status changes. Admin student-activity mutations are recorded in the audit log.
Student-owned dependent data is cleaned up on account deletion, and shared
project links are detached.

The **Skill tests** section lets admins create and maintain tests with exactly
30 multiple-choice questions, four distinct options per question, topic tags,
and an answer key. Students take available tests in the portal and receive
backend-scored marks and topic breakdowns; answer keys are never included in
the student assessment responses. Test questions lock after the first attempt
to preserve score integrity. Tests with attempts can be deactivated but not
deleted.

For a frontend hosted separately from the API, set the
`portfolia-api-base` meta tag on the login, registration, student, and admin
pages to the complete API root (for example
`https://api.example.com/api/v1`). In local development the frontend
automatically calls port 8000 on the same host used to open the page, keeping
the browser's HttpOnly auth cookie aligned on both `localhost` and
`127.0.0.1`.

## Authentication and implementation notes

- Browser login uses an `HttpOnly`, `SameSite=Lax` cookie and server-side
  sessions; frontend API requests include credentials. Bearer tokens remain
  accepted for API clients.
- Admin registration uses a private server-side `ADMIN_REGISTRATION_KEY`;
  without it, admin registration is disabled. Admin actions are recorded in
  the audit log.
- Set a unique, strong `SECRET_KEY` and HTTPS in production. The API refuses to
  start in production with the development default secret.
- Profile photos and portfolio evidence currently reference URLs; binary file
  uploads are not implemented.
- Skill tests are authored by admins and require exactly 30 multiple-choice
  questions; the platform does not provide a built-in curriculum or question
  bank.
- Team membership is invitation-based; self-service team join requests are
  not implemented.
- Support ticket response/status APIs and the admin support interface are
  available. Email preferences are stored, but email delivery is not connected.

## Security baseline

- passwords hashed with Argon2id
- no plaintext secrets committed to source control
- server-side RBAC enforcement on protected routes
- no user-supplied role or ownership data trusted for access decisions
- all sensitive routes require an authenticated session

## Important note

This repository intentionally avoids AI features in the Stage 1 baseline. AI modules are reserved for Stage 2 and must reuse the same accounts, roles, portfolios, and permissions.
