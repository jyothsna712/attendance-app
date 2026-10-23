from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.auth import bearer_scheme, get_current_user
from app.core.security import ACCESS_TOKEN_MINUTES, create_access_token, hash_password, verify_password
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == str(user_data.email)).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email is already registered")

    new_user = User(
        name=user_data.name,
        email=str(user_data.email),
        password_hash=hash_password(user_data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message": "User registered successfully",
        "id": str(new_user.id),
        "name": new_user.name,
        "email": new_user.email,
    }


@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(user_data.email)).first()
    if user is None or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(str(user.id))
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_MINUTES * 60,
    )


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
    _credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
    }