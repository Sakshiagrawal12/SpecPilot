from datetime import datetime, timedelta

from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import OAuth2PasswordBearer

from jose import jwt, JWTError

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


# =========================================================
# JWT CONFIGURATION
# =========================================================

SECRET_KEY = "YOUR_SECRET_KEY_CHANGE_THIS"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# =========================================================
# CREATE ACCESS TOKEN
# =========================================================

def create_access_token(user_id: int):

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# =========================================================
# GET CURRENT USER
# =========================================================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    print("\n=================================")
    print("AUTH DEBUG")
    print("=================================")
    print("TOKEN RECEIVED:", token)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        print("JWT PAYLOAD:", payload)

        user_id = payload.get("sub")

        print("SUB:", user_id)

        if user_id is None:
            print("ERROR: sub is missing")
            raise credentials_exception

        user_id = int(user_id)

        print("USER ID:", user_id)

    except JWTError as e:

        print("JWT ERROR:", type(e).__name__)
        print("JWT ERROR MESSAGE:", str(e))

        raise credentials_exception

    except (ValueError, TypeError) as e:

        print("USER ID ERROR:", type(e).__name__)
        print("USER ID ERROR MESSAGE:", str(e))

        raise credentials_exception

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    print("USER FOUND:", user)

    if user is None:

        print("ERROR: USER DOES NOT EXIST")

        raise credentials_exception

    print("AUTH SUCCESS")
    print("=================================\n")

    return user
