import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends, status, Response
from supabase import create_client, Client
from schemas import UserAuthSchema

# ------------------------------------------------------------------------------
# 1. Environment and Application Setup
# ------------------------------------------------------------------------------

# Resolve base directory path and load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Retrieve Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

# Initialize the Supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize the FastAPI application
app = FastAPI(title="FastAPI Supabase Auth API")


# ------------------------------------------------------------------------------
# 2. Authentication Dependency (Middleware Component)
# ------------------------------------------------------------------------------

def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Dependency function that extracts and validates the JWT Bearer token
    from the request authorization header using the Supabase Auth API.
    """
    # Verify that the authorization header exists and starts with "Bearer "
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"}
        )

    # Extract token string from the header value
    parts = authorization.split(" ")
    token = parts[1] if len(parts) > 1 else ""

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"}
        )

    try:
        # Validate the token using Supabase SDK
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid or expired token"}
            )

        # Return authenticated user instance and raw token for route consumption
        return {"user": response.user, "token": token}
    except HTTPException as http_ex:
        raise http_ex
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"}
        )


# ------------------------------------------------------------------------------
# 3. Root Endpoint
# ------------------------------------------------------------------------------

@app.get("/")
def read_root():
    """Root health check endpoint."""
    return {"message": "Auth API is up and running"}


# ------------------------------------------------------------------------------
# 4. Authentication Routes (Stage 1 & Stage 4)
# ------------------------------------------------------------------------------

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: UserAuthSchema):
    """Registers a new user using Supabase Auth."""
    try:
        response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed. Check email or password requirements."
            )

        return {
            "message": "User registered successfully",
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/auth/login", status_code=status.HTTP_200_OK)
def login(payload: UserAuthSchema):
    """Authenticates user credentials and returns session tokens."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid login credentials"}
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": response.session.token_type,
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"}
        )


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: dict = Depends(get_current_user)):
    """Logs out the authenticated user and revokes the active session."""
    try:
        supabase.auth.sign_out()  # <-- FIXED: REMOVED (scope="global")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )


# ------------------------------------------------------------------------------
# 5. Public and Protected Routes (Stage 2, Stage 3, and Stage 4)
# ------------------------------------------------------------------------------

@app.get("/public/info", status_code=status.HTTP_200_OK)
def public_info():
    """Unprotected endpoint accessible by any client."""
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", status_code=status.HTTP_200_OK)
def protected_profile(current_user: dict = Depends(get_current_user)):
    """Protected endpoint returning verified user profile information."""
    user = current_user["user"]
    return {
        "message": "Access granted to protected profile",
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": str(user.created_at)
        }
    }


@app.get("/protected/dashboard", status_code=status.HTTP_200_OK)
def protected_dashboard(current_user: dict = Depends(get_current_user)):
    """Secondary protected checkpoint endpoint utilizing the auth dependency."""
    user = current_user["user"]
    return {
        "message": "Welcome to your protected dashboard!",
        "user_id": user.id,
        "email": user.email
    }