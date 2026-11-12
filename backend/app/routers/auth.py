import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.student_portal import UserSession
from backend.app.models.user import Role, User
from backend.app.schemas.auth import AdminRegister, TokenResponse, UserLogin, UserProfileOut, UserRegister

router = APIRouter()


def generate_port_id(db: Session) -> str:
    while True:
        year_suffix = str(datetime.now(UTC).year)[-2:]
        port_id = f"TP{year_suffix}{secrets.randbelow(90000) + 10000}"
        if not db.query(User).filter(User.port_id == port_id).first():
            return port_id


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="portfolia_access_token",
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def create_session(user: User, request: Request, db: Session) -> str:
    now = datetime.now(UTC)
    session = UserSession(
        user_id=user.id,
        created_at=now,
        expires_at=now + timedelta(minutes=settings.access_token_expire_minutes),
        user_agent=request.headers.get("user-agent", "")[:500] or None,
    )
    db.add(session)
    db.flush()
    token = create_access_token(str(user.id), session_id=session.id)
    db.commit()
    return token


@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, request: Request, response: Response, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower().strip()
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    requested_role = payload.user_type if payload.user_type in {"student", "college_admin", "company", "investor"} else "student"
    role = db.query(Role).filter(Role.name == requested_role).first()
    if role is None:
        role = Role(name=requested_role, description=f"{requested_role.replace('_', ' ').title()} user")
        db.add(role)
        db.commit()
        db.refresh(role)

    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
        is_verified=False,
        port_id=generate_port_id(db),
        user_type=requested_role,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session(user, request, db)
    set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        port_id=user.port_id,
    )


@router.post("/register-admin", response_model=TokenResponse)
def register_admin(
    payload: AdminRegister,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    registration_key = settings.admin_registration_key
    if not registration_key or not hmac.compare_digest(payload.registration_key, registration_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin registration is unavailable or the key is invalid")

    normalized_email = payload.email.lower().strip()
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    role = db.query(Role).filter(Role.name == "admin").first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin role is not configured")
    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
        is_verified=False,
        port_id=generate_port_id(db),
        user_type="admin",
    )
    user.roles.append(role)
    db.add(user)
    try:
        db.flush()
        token = create_session(user, request, db)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or Port ID is already in use") from exc

    set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        port_id=user.port_id,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive")

    token = create_session(user, request, db)
    set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        port_id=user.port_id,
    )


@router.get("/me", response_model=UserProfileOut)
def me(current_user: User = Depends(get_current_user)):
    return UserProfileOut(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        port_id=current_user.port_id,
        user_type=current_user.user_type,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    token = request.cookies.get("portfolia_access_token")
    if token is None:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
    if token:
        session_id = decode_access_token(token).get("jti")
        if session_id:
            session = db.query(UserSession).filter(
                UserSession.id == session_id,
                UserSession.user_id == current_user.id,
            ).first()
            if session is not None:
                session.revoked_at = datetime.now(UTC)
                db.commit()
    response.delete_cookie(
        key="portfolia_access_token",
        path="/",
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
    )
    return {"message": "Logged out successfully"}
