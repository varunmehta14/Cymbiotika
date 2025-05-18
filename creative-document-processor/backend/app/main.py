"""
Main FastAPI application for the Creative Document Processor.
"""
import os
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl

from app.core.config import settings
from app.api.routes import ingest, query, scraper, documents
from app.services.sse import generate_sse_stream

app = FastAPI(
    title="Creative Document Processor API",
    description="API for ingesting, processing, and querying documents using LLM",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(scraper.router, prefix="/scrape", tags=["Scraper"])
app.include_router(documents.router, prefix="/doc", tags=["Documents"])

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify if the service is running.
    """
    return {"status": "healthy", "version": app.__version__}

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_DEBUG,
    ) 