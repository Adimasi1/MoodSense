from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.analysis_router import router as analysis_router

app = FastAPI(
    title="MoodSense API",
    description="API for WhatApp conversation parsing, computing statistics on emotions and text.",
    version="1.0.0"
)

# CORS middleware
# For production, add your actual frontend domains here
allowed_origins = [
    "https://moodsense-b9ha.onrender.com",  # Your production API domain
    "http://localhost:3000",  # React/Next.js dev
    "http://localhost:5173",  # Vite dev
    "http://localhost",  # Flutter web dev (covers all localhost ports)
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