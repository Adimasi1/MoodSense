from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from analysis_endpoints import router as analysis_router

app = FastAPI(
    title="Sentiment Analysis API",
    description="API for text cleaning, sentiment analysis, and emotion detection (stateless).",
    version="2.0.0"
)

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Sentiment Analyzer API is running (stateless)",
        "version": "2.0.0",
        "endpoints": {
            "docs": "/docs",
            "analyze_single": "/api/v1/analyze-single",
            "analyze_batch": "/api/v1/analyze-batch"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}