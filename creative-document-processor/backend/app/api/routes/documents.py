"""
Routes for managing documents in the knowledge base.
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import mimetypes
import logging
import json

from fastapi import APIRouter, HTTPException, Response, Request, Body, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from app.models.document import KnowledgeBaseType
from app.services.document_processor import get_document, list_documents
from app.core.config import settings
from app.services.langgraph_agent import run_agent, compare_resumes_to_job
from app.services.sse import sse_manager, encode_sse_event

router = APIRouter()


@router.get("/{kb}/{doc_id}", response_class=Response)
async def get_raw_document(kb: str, doc_id: str):
    """
    Get a raw document for preview.
    
    Args:
        kb: Knowledge base type
        doc_id: Document ID
        
    Returns:
        Response: Raw document content
    """
    # Validate KB type
    if kb not in [e.value for e in KnowledgeBaseType]:
        raise HTTPException(status_code=400, detail=f"Invalid knowledge base type: {kb}")
    
    # Get document metadata
    document = await get_document(doc_id, kb)
    
    if not document:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
    
    # Find the source file
    doc_dir = Path(f"{settings.RAW_DOCS_PATH}/{kb}/{doc_id}")
    
    if not doc_dir.exists() or not doc_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Document directory not found: {doc_id}")
    
    # Find the source file (first file that's not metadata.json)
    source_file = None
    for file in doc_dir.iterdir():
        if file.is_file() and file.name != "metadata.json":
            source_file = file
            break
    
    if not source_file:
        # If no source file found, return the content as text
        return Response(
            content=document.content,
            media_type="text/plain"
        )
    
    # Determine the content type
    content_type = document.metadata.content_type
    
    # Handle based on content type
    if content_type == "application/pdf":
        return FileResponse(
            path=source_file,
            media_type="application/pdf",
            filename=f"{document.metadata.title}.pdf"
        )
    elif content_type.startswith("text/"):
        with open(source_file, "rb") as f:
            content = f.read()
        return Response(
            content=content,
            media_type=content_type
        )
    else:
        # For unsupported preview types, return the raw file
        return FileResponse(
            path=source_file,
            media_type=content_type,
            filename=source_file.name
        )


@router.get("/{kb}", response_model=List[Dict[str, Any]])
async def list_kb_documents(kb: str):
    """
    List all documents in a knowledge base.
    
    Args:
        kb: Knowledge base type
        
    Returns:
        List[Dict[str, Any]]: List of documents
    """
    # Validate KB type
    if kb not in [e.value for e in KnowledgeBaseType]:
        raise HTTPException(status_code=400, detail=f"Invalid knowledge base type: {kb}")
    
    try:
        # Get document list
        documents = await list_documents(kb)
        
        if not documents:
            logging.info(f"No documents found in knowledge base: {kb}")
        else:
            logging.info(f"Found {len(documents)} documents in knowledge base: {kb}")
            
        return documents
    except Exception as e:
        logging.exception(f"Error listing documents for knowledge base {kb}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )


@router.post("/compare-resumes", response_model=Dict[str, Any])
async def compare_resumes(
    request: Request,
    job_description: str = Body(..., embed=True),
    document_ids: Optional[List[str]] = Body(None, embed=True),
):
    """
    Compare multiple resumes against a job description and return ranked candidates.
    
    Args:
        job_description: The job description to match against
        document_ids: Optional list of resume document IDs to compare (if None, all resumes will be used)
        
    Returns:
        Dict[str, Any]: Results with ranked candidates
    """
    # Create event generator for streaming responses
    generator = sse_manager.create_generator()
    background_tasks = BackgroundTasks()
    
    # Run the comparison in the background
    async def run_comparison():
        try:
            # Set up stream callback
            async def stream_callback(data: str):
                await sse_manager.send_event(generator.id, data)
            
            # Run the resume comparison
            result = await compare_resumes_to_job(
                job_description=job_description,
                document_ids=document_ids,
                stream_callback=stream_callback
            )
            
            # Send the final result and close the connection
            await sse_manager.send_event(
                generator.id,
                encode_sse_event(json.dumps({"result": result}), event="result")
            )
            await sse_manager.close_connection(generator.id)
        except Exception as e:
            # Handle errors
            error_message = f"Error comparing resumes: {str(e)}"
            await sse_manager.send_event(
                generator.id,
                encode_sse_event(json.dumps({"error": error_message}), event="error")
            )
            await sse_manager.close_connection(generator.id)
    
    # Add task to background tasks
    background_tasks.add_task(run_comparison)
    
    # Return streaming response
    return StreamingResponse(
        generator.iterator(),
        media_type="text/event-stream",
        background=background_tasks
    ) 