"""
Routes for document ingestion into knowledge bases.
"""
import os
from typing import Optional, Dict, Any
import tempfile
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile, HTTPException, Depends
from pydantic import HttpUrl, ValidationError

from app.models.document import IngestRequest, Document
from app.services.document_processor import ingest_from_url, ingest_from_file

router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
async def ingest_document(
    background_tasks: BackgroundTasks,
    kb: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Ingest a document from a URL or file upload.
    
    Args:
        background_tasks: FastAPI background tasks
        kb: Knowledge base type
        url: Optional URL to fetch
        file: Optional file upload
        
    Returns:
        Dict[str, Any]: Document info
    """
    # Validate input
    if url is None and file is None:
        raise HTTPException(status_code=400, detail="Either url or file must be provided")
    
    if url is not None and file is not None:
        raise HTTPException(status_code=400, detail="Only one of url or file can be provided")
    
    # Validate the KB type
    try:
        request = IngestRequest(kb=kb, url=url)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid knowledge base type: {kb}")
    
    # Process based on input type
    document = None
    
    # URL processing
    if url:
        try:
            document = await ingest_from_url(url, kb)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process URL: {str(e)}")
    
    # File processing
    elif file:
        try:
            # Read file content
            content = await file.read()
            
            # Ingest the file
            document = await ingest_from_file(content, file.filename, kb)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    
    # Return document info
    return {
        "id": document.id,
        "kb": kb,
        "title": document.metadata.title,
        "source": document.metadata.source,
        "source_type": document.metadata.source_type,
        "chunks": len(document.chunks),
        "status": "success"
    } 