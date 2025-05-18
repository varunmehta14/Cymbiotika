"""
Document models for the application.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, HttpUrl


class KnowledgeBaseType(str, Enum):
    """
    Enum for different knowledge base types.
    """
    RESUMES = "resumes"
    API_DOCS = "api_docs"
    RECIPES = "recipes"
    SUPPLEMENTS = "supplements"


class DocumentMetadata(BaseModel):
    """
    Metadata for a document.
    """
    title: str
    description: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    content_type: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """
    Document model representing a file or URL content.
    """
    id: str
    kb_type: str
    content: str
    metadata: DocumentMetadata
    chunks: List[Dict[str, Any]] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    """
    A chunk of a document for embedding and retrieval.
    """
    id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    """
    Request model for document ingestion.
    """
    kb: KnowledgeBaseType
    url: Optional[HttpUrl] = None
    
    class Config:
        use_enum_values = True


class QueryRequest(BaseModel):
    """
    Request model for querying knowledge bases.
    """
    kb: KnowledgeBaseType
    prompt: str
    doc_id: Optional[str] = None
    search_params: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class QueryResponse(BaseModel):
    """
    Response model for query results.
    """
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SupplementRewriteRequest(BaseModel):
    """
    Request model for rewriting supplement content.
    """
    doc_id: str
    tone: Optional[str] = "balanced"
    

class ProductSearchRequest(BaseModel):
    """
    Request model for searching products.
    """
    query: str 