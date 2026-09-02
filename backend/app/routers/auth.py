from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
import bcrypt

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

from app.auth import (
    create_access_token,
    get_current_user
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


from app.schemas import SignupRequest, LoginRequest


# =========================================================
# SIGNUP / REGISTER
# =========================================================

@router.post("/signup", status_code=201)
def signup(
    signup_data: SignupRequest,
    db: Session = Depends(get_db)
):
    email = signup_data.email.strip().lower()
    name = signup_data.name.strip()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists."
        )

    # Hash password with bcrypt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(
        signup_data.password.encode("utf-8"),
        salt
    ).decode("utf-8")

    user = User(
        name=name,
        email=email,
        password_hash=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create JWT Token
    token = create_access_token(user.id)

    return {
        "message": "Account created successfully",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


# =========================================================
# LOGIN
# =========================================================

@router.post("/login")
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            User.email == login_data.email
        )
        .first()
    )


    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


    # -----------------------------------------
    # PASSWORD CHECK
    # -----------------------------------------

    password_valid = bcrypt.checkpw(
    login_data.password.encode("utf-8"),
    user.password_hash.encode("utf-8")
    )

    if not password_valid:
        raise HTTPException(
        status_code=401,
        detail="Invalid email or password"
    )


    # -----------------------------------------
    # CREATE JWT TOKEN
    # -----------------------------------------

    token = create_access_token(
        user.id
    )


    return {

        "message": "Login successful",

        "access_token": token,

        "token_type": "bearer",
        "user_id": user.id,

        "user": {

            "id": user.id,

            "name": user.name,

            "email": user.email

        }

    }

@router.get("/users")
def get_users(
    db: Session = Depends(get_db)
):
    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
        for user in users
    ]
# =========================================================
# CURRENT USER
# =========================================================

@router.get("/me")
def get_me(
    current_user: User = Depends(
        get_current_user
    )
):

    return {

        "id": current_user.id,

        "name": current_user.name,

        "email": current_user.email

    }