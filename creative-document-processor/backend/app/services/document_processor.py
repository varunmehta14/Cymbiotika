"""
Document processing service for ingestion and chunking.
"""
import os
import uuid
import aiofiles
import aiohttp
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import mimetypes
import tempfile
import json
import logging

# PDF processing
import PyPDF2
import io

# Document processing
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.models.document import Document, DocumentMetadata, KnowledgeBaseType
from app.services.vector_store import embed_text


async def ingest_from_url(url: str, kb_type: str) -> Document:
    """
    Ingest a document from a URL.
    
    Args:
        url: URL to fetch the document from
        kb_type: Knowledge base type
        
    Returns:
        Document: Processed document
    """
    # Validate KB type
    if kb_type not in [e.value for e in KnowledgeBaseType]:
        raise ValueError(f"Invalid knowledge base type: {kb_type}")
    
    # Fetch the document
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").split(";")[0]
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Determine file extension
            content_ext = mimetypes.guess_extension(content_type) or ""
            
            # Create directory for the document
            doc_dir = Path(f"{settings.RAW_DOCS_PATH}/{kb_type}/{doc_id}")
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the raw content
            filename = f"source{content_ext}"
            file_path = doc_dir / filename
            
            # Read the content
            raw_content = await response.read()
            
            # Save the raw file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(raw_content)
            
            # Process the content based on content type
            if content_type == "application/pdf":
                text_content, metadata = await _process_pdf(raw_content, url)
            elif content_type.startswith("text/"):
                text_content = raw_content.decode("utf-8")
                metadata = {"source": url, "content_type": content_type}
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                title=metadata.get("title", os.path.basename(url)),
                description=metadata.get("description", ""),
                source=url,
                source_type="url",
                content_type=content_type,
                extra=metadata
            )
            
            # Create the document
            document = Document(
                id=doc_id,
                kb_type=kb_type,
                content=text_content,
                metadata=doc_metadata,
                chunks=[]
            )
            
            # Process and chunk the document
            await process_document(document)
            
            return document


async def ingest_from_file(file_content: bytes, filename: str, kb_type: str) -> Document:
    """
    Ingest a document from an uploaded file.
    
    Args:
        file_content: Raw file content
        filename: Original filename
        kb_type: Knowledge base type
        
    Returns:
        Document: Processed document
    """
    # Validate KB type
    if kb_type not in [e.value for e in KnowledgeBaseType]:
        raise ValueError(f"Invalid knowledge base type: {kb_type}")
    
    # Generate document ID
    doc_id = str(uuid.uuid4())
    
    # Get file extension and mime type
    _, file_ext = os.path.splitext(filename)
    content_type, _ = mimetypes.guess_type(filename)
    
    if not content_type:
        # Default to text if we can't determine
        content_type = "text/plain"
    
    # Create directory for the document
    doc_dir = Path(f"{settings.RAW_DOCS_PATH}/{kb_type}/{doc_id}")
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the raw file
    file_path = doc_dir / filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)
    
    # Process the content based on content type
    if content_type == "application/pdf":
        text_content, metadata = await _process_pdf(file_content, filename)
    elif content_type.startswith("text/") or file_ext.lower() in [".txt", ".md"]:
        # Handle text files
        text_content = file_content.decode("utf-8")
        metadata = {"source": filename, "content_type": content_type}
    else:
        raise ValueError(f"Unsupported content type: {content_type} for file: {filename}")
    
    # Create document metadata
    doc_metadata = DocumentMetadata(
        title=metadata.get("title", filename),
        description=metadata.get("description", ""),
        source=filename,
        source_type="file",
        content_type=content_type,
        extra=metadata
    )
    
    # Create the document
    document = Document(
        id=doc_id,
        kb_type=kb_type,
        content=text_content,
        metadata=doc_metadata,
        chunks=[]
    )
    
    # Process and chunk the document
    await process_document(document)
    
    return document


async def _process_pdf(pdf_content: bytes, source: str) -> Tuple[str, Dict[str, Any]]:
    """
    Process a PDF document to extract text and metadata.
    
    Args:
        pdf_content: Raw PDF content
        source: Source identifier (URL or filename)
        
    Returns:
        Tuple[str, Dict[str, Any]]: Extracted text and metadata
    """
    # Read the PDF
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    
    # Extract text
    text_content = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text_content += page.extract_text() + "\n\n"
    
    # Extract metadata
    metadata = {
        "source": source,
        "content_type": "application/pdf",
        "pages": len(pdf_reader.pages),
        "title": source,  # Default to source name
    }
    
    # Try to extract title from PDF metadata
    if pdf_reader.metadata:
        if pdf_reader.metadata.title:
            metadata["title"] = pdf_reader.metadata.title
        if pdf_reader.metadata.author:
            metadata["author"] = pdf_reader.metadata.author
    
    return text_content, metadata


async def process_document(document: Document) -> Document:
    """
    Process a document for ingestion into the knowledge base.
    This includes chunking and embedding the text.
    
    Args:
        document: Document to process
        
    Returns:
        Document: Processed document with chunks
    """
    # Split the document into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_text(document.content)
    
    # Create document chunks and embed them
    document.chunks = []
    
    for i, chunk_text in enumerate(chunks):
        # Generate a chunk ID
        chunk_id = await embed_text(
            text=chunk_text,
            doc_id=document.id,
            kb_name=document.kb_type,
            metadata={
                "title": document.metadata.title,
                "source": document.metadata.source,
                "chunk_index": i,
                **document.metadata.extra
            }
        )
        
        # Add to document chunks
        if chunk_id:
            document.chunks.append({
                "id": chunk_id,
                "text": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text,
                "index": i
            })
    
    # Save the processed document metadata
    doc_dir = Path(f"{settings.RAW_DOCS_PATH}/{document.kb_type}/{document.id}")
    meta_path = doc_dir / "metadata.json"
    
    async with aiofiles.open(meta_path, "w") as f:
        await f.write(json.dumps(document.model_dump(), indent=2, default=str))
    
    return document


async def get_document(doc_id: str, kb_type: str) -> Optional[Document]:
    """
    Get a document from the knowledge base.
    
    Args:
        doc_id: Document ID
        kb_type: Knowledge base type
        
    Returns:
        Optional[Document]: Document if found, None otherwise
    """
    meta_path = Path(f"{settings.RAW_DOCS_PATH}/{kb_type}/{doc_id}/metadata.json")
    
    if not meta_path.exists():
        return None
    
    try:
        async with aiofiles.open(meta_path, "r") as f:
            content = await f.read()
            try:
                # Try Pydantic V1 first
                document = Document.parse_raw(content)
            except Exception as parse_err:
                logging.warning(f"Failed to parse using parse_raw: {str(parse_err)}")
                # Try Pydantic V2 approach
                try:
                    doc_data = json.loads(content)
                    document = Document(**doc_data)
                except Exception as e:
                    logging.error(f"Failed to parse document: {str(e)}")
                    raise
            
        return document
    except Exception as e:
        logging.exception(f"Error getting document {doc_id}: {str(e)}")
        return None


async def list_documents(kb_type: str) -> List[Dict[str, Any]]:
    """
    List all documents in a knowledge base.
    
    Args:
        kb_type: Knowledge base type
        
    Returns:
        List[Dict[str, Any]]: List of document summaries
    """
    logging.info(f"Listing documents for knowledge base: {kb_type}")
    kb_path = Path(f"{settings.RAW_DOCS_PATH}/{kb_type}")
    
    if not kb_path.exists():
        logging.warning(f"Knowledge base path does not exist: {kb_path}")
        return []
    
    documents = []
    
    for doc_dir in kb_path.iterdir():
        if doc_dir.is_dir():
            meta_path = doc_dir / "metadata.json"
            
            if meta_path.exists():
                try:
                    logging.info(f"Reading metadata file: {meta_path}")
                    async with aiofiles.open(meta_path, "r") as f:
                        content = await f.read()
                        
                        # For debugging purposes
                        logging.info(f"Metadata content first 100 chars: {content[:100]}")
                        
                        # Try both Pydantic V1 and V2 approaches
                        document = None
                        try:
                            # V1 approach
                            document = Document.parse_raw(content)
                        except Exception as parse_err:
                            logging.warning(f"V1 parsing failed: {str(parse_err)}")
                            try:
                                # V2 approach
                                doc_data = json.loads(content)
                                document = Document(**doc_data)
                            except Exception as e:
                                logging.error(f"V2 parsing failed too: {str(e)}")
                                # Add error info to documents list
                                documents.append({
                                    "id": doc_dir.name,
                                    "title": "Error: Failed to parse metadata",
                                    "source": meta_path.as_posix(),
                                    "error": str(e)
                                })
                                continue
                        
                        if document:
                            documents.append({
                                "id": document.id,
                                "title": document.metadata.title,
                                "source": document.metadata.source,
                                "source_type": document.metadata.source_type,
                                "created_at": document.metadata.created_at.isoformat() 
                                    if hasattr(document.metadata.created_at, "isoformat") 
                                    else document.metadata.created_at,
                                "content_type": document.metadata.content_type,
                                "chunk_count": len(document.chunks)
                            })
                except Exception as e:
                    logging.exception(f"Error reading metadata file {meta_path}: {str(e)}")
    
    # Sort by created_at descending
    try:
        documents.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception as sort_err:
        logging.warning(f"Could not sort documents: {str(sort_err)}")
    
    return documents 