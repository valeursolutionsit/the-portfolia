from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import Base, SessionLocal, engine
from backend.app.models.user import Permission, Role
from backend.app.routers.auth import router as auth_router
from backend.app.routers.admin import router as admin_router
from backend.app.routers.companies import router as companies_router
from backend.app.routers.institutions import router as institutions_router
from backend.app.routers.investors import router as investors_router
from backend.app.routers.portal import router as portal_router
from backend.app.routers.students import router as students_router

Base.metadata.create_all(bind=engine)

if settings.app_env.lower() == "production" and settings.secret_key == "change-me-in-production":
    raise RuntimeError("Set SECRET_KEY to a strong production secret before starting the API")


def seed_roles() -> None:
    db = SessionLocal()
    try:
        for role_name in ["student", "college_admin", "company", "investor", "admin", "super-admin"]:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name, description=f"{role_name.replace('-', ' ').title()} role"))
        for permission_name in [
            "view_profile",
            "edit_profile",
            "manage_learning",
            "manage_portfolio",
            "view_opportunities",
            "manage_students",
            "manage_company",
            "manage_admin",
        ]:
            if not db.query(Permission).filter(Permission.name == permission_name).first():
                db.add(Permission(name=permission_name, description=permission_name.replace("_", " ").title()))
        db.commit()
    finally:
        db.close()


seed_roles()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="The Portfolia backend API for Stage 1",
)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.app_env.lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(students_router, prefix="/api/v1")
app.include_router(portal_router, prefix="/api/v1")
app.include_router(institutions_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(investors_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "The Portfolia API is running"}
