from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import register_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db),
):
    """Register a new customer account."""
    return register_user(db, user_in)


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """Log in with email and password to receive a JWT access token."""
    return authenticate_user(db, credentials.email, credentials.password)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get currently authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role.name if current_user.role else "customer",
        created_at=current_user.created_at,
    )
