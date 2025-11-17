from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.analysis_router import router as analysis_router

app = FastAPI(
    title="MoodSense API",
    description="API for WhatApp conversation parsing, computing statistics on emotions and text.",
    version="1.0.0"
)

# CORS middleware - restrict to your actual frontend domains
allowed_origins = [
    "https://moodsense-38104758698.europe-west1.run.app",  # Cloud Run production
    "http://localhost:3000",  # Local dev (React/Next.js)
    "http://localhost:5173",  # Local dev (Vite)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific domains only
    allow_credentials=False,  # Set True only if using cookies/auth
    allow_methods=["GET", "POST"],  # Only methods you actually use
    allow_headers=["*"],  # Can restrict to ["Content-Type", "Authorization"] if needed
)

app.include_router(analysis_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "MoodSense API API is running (stateless)",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "analyze-conversation": "/api/v1/analyze-single",
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# For local development: uvicorn main:app --reload
# For Cloud Run: the Dockerfile CMD handles port binding via $PORT