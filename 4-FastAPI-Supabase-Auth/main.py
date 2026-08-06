import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client

# Explicitly find the .env file in the same directory as main.py
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="FastAPI Supabase Auth API")


@app.on_event("startup")
def startup_event():
    print("Server running and connected to Supabase")


@app.get("/")
def read_root():
    return {"message": "Auth API is up and running"}