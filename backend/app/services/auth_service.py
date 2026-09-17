from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import UserRegister, Token, UserResponse


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def register_user(db: Session, user_in: UserRegister) -> UserResponse:
    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    customer_role = db.query(Role).filter(Role.name == "customer").first()
    if not customer_role:
        customer_role = Role(name="customer", description="Standard customer role")
        db.add(customer_role)
        db.commit()
        db.refresh(customer_role)

    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        phone=user_in.phone.strip() if user_in.phone else None,
        hashed_password=hash_password(user_in.password),
        role_id=customer_role.id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        phone=new_user.phone,
        role=customer_role.name,
        created_at=new_user.created_at,
    )


def authenticate_user(db: Session, email: str, password: str) -> Token:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_name = user.role.name if user.role else "customer"
    access_token = create_access_token(
        subject=user.id,
        role=role_name,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    user_resp = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=role_name,
        created_at=user.created_at,
    )

    return Token(access_token=access_token, token_type="bearer", user=user_resp)
