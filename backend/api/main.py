# api/main.py
# FastAPI entry point. CORS, lifespan, route mounting.

import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from agent.db import init_schema
from api.routes import jobs, keywords, contractors, classification, health, auth, cities, settings

load_dotenv()

# Support comma-separated list of allowed origins via FRONTEND_URL env var
_raw_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
FRONTEND_URLS = [u.strip() for u in _raw_frontend_url.split(",") if u.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Contractor Scraper API...")
    try:
        init_schema()
        print("✅ init_schema() completed successfully")
    except Exception as e:
        print(f"❌ DB schema init FAILED: {e}")
        traceback.print_exc()  # full stack trace in Cloud Run logs
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Contractor Scraper API",
    description="Florida contractor lead generation pipeline",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        *FRONTEND_URLS,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["keywords"])
app.include_router(cities.router, prefix="/api/cities", tags=["cities"])
app.include_router(contractors.router, prefix="/api/contractors", tags=["contractors"])
app.include_router(classification.router, prefix="/api/classification-log", tags=["classification"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/")
async def root():
    return {
        "service": "contractor-scraper-api",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/api/seed-admin")
async def seed_admin():
    """Force-seed the test user and report what's in the users tab. Remove after debugging."""
    try:
        from agent.sheets_client import get_db
        from agent.db import _seed_test_user_if_missing
        _seed_test_user_if_missing()
        db = get_db()
        users = db.all_rows("users")
        return {
            "status": "ok",
            "users_count": len(users),
            "emails": [u.get("email") for u in users],
        }
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}
