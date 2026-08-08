import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# Initialize the FastAPI application with custom OpenAPI documentation metadata
app = FastAPI(
    title="FastAPI Supabase Auth API",
    description="A secure REST API demonstrating authentication using FastAPI and Supabase.",
    version="1.0.0"
)

# Initialize HTTPBearer security scheme for OpenAPI / Swagger UI configuration
security_scheme = HTTPBearer(auto_error=True)


# ------------------------------------------------------------------------------
# 2. Reusable Authentication Dependency
# ------------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """
    Dependency function that extracts and validates the JWT Bearer token
    from the request authorization header using the Supabase Auth API.
    Used to protect endpoints and generate Swagger UI security schemes.
    """
    # Extract the token string from the credentials object
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"}
        )

    try:
        # Validate the token using the Supabase SDK
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid or expired token"}
            )

        # Return authenticated user instance and raw token string for route consumption
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

@app.get("/", tags=["Health Check"])
def read_root():
    """Root health check endpoint."""
    return {"message": "Auth API is up and running"}


# ------------------------------------------------------------------------------
# 4. Authentication Routes
# ------------------------------------------------------------------------------

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, tags=["Authentication"])
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


@app.post("/auth/login", status_code=status.HTTP_200_OK, tags=["Authentication"])
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


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["Authentication"])
def logout(current_user: dict = Depends(get_current_user)):
    """Logs out the authenticated user and revokes the active session."""
    try:
        supabase.auth.sign_out()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )


# ------------------------------------------------------------------------------
# 5. Public and Protected Routes
# ------------------------------------------------------------------------------

@app.get("/public/info", status_code=status.HTTP_200_OK, tags=["Public"])
def public_info():
    """Unprotected endpoint accessible by any client."""
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", status_code=status.HTTP_200_OK, tags=["Protected"])
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


@app.get("/protected/dashboard", status_code=status.HTTP_200_OK, tags=["Protected"])
def protected_dashboard(current_user: dict = Depends(get_current_user)):
    """Secondary protected checkpoint endpoint utilizing the auth dependency."""
    user = current_user["user"]
    return {
        "message": "Welcome to your protected dashboard!",
        "user_id": user.id,
        "email": user.email
    }