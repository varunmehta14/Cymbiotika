"""
Vector store service for managing document embeddings.
"""
import os
from typing import Dict, List, Optional, Any, Tuple
import uuid

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.core.config import settings


# Initialize the embedding model
embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIRECTORY,
    settings=Settings(anonymized_telemetry=False)
)


def get_collection(kb_name: str):
    """
    Get or create a collection for the specified knowledge base.
    
    Args:
        kb_name: Knowledge base name
        
    Returns:
        Collection: ChromaDB collection for the KB
    """
    if kb_name not in settings.KNOWLEDGE_BASES:
        raise ValueError(f"Invalid knowledge base: {kb_name}")
    
    return chroma_client.get_or_create_collection(name=kb_name)


async def embed_text(
    text: str, 
    doc_id: str, 
    kb_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Embed text and store it in the vector database.
    
    Args:
        text: Text to embed
        doc_id: Document ID
        kb_name: Knowledge base name
        metadata: Additional metadata
        
    Returns:
        str: ID of the embedded document chunk
    """
    if not text.strip():
        return None
        
    # Generate a chunk ID
    chunk_id = str(uuid.uuid4())
    
    # Get embeddings
    embedding = embedding_model.encode(text).tolist()
    
    # Store in ChromaDB
    collection = get_collection(kb_name)
    
    # Add metadata if provided
    meta = metadata or {}
    meta["document_id"] = doc_id
    
    collection.add(
        ids=[chunk_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[meta]
    )
    
    return chunk_id


async def query_vector_store(
    query_text: str,
    kb_name: str,
    n_results: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Query the vector store for similar documents.
    
    Args:
        query_text: Query text
        kb_name: Knowledge base name
        n_results: Number of results to return
        filter_dict: Filter criteria for the query
        
    Returns:
        List[Dict[str, Any]]: List of matching documents with metadata
    """
    # Get embeddings for the query
    query_embedding = embedding_model.encode(query_text).tolist()
    
    # Query the collection
    collection = get_collection(kb_name)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=filter_dict
    )
    
    # Format the results
    formatted_results = []
    if results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            })
    
    return formatted_results


async def delete_document(doc_id: str, kb_name: str) -> int:
    """
    Delete a document and all its chunks from the vector store.
    
    Args:
        doc_id: Document ID to delete
        kb_name: Knowledge base name
        
    Returns:
        int: Number of chunks deleted
    """
    collection = get_collection(kb_name)
    
    # Find all chunks for this document ID
    results = collection.get(where={"document_id": doc_id})
    
    if not results["ids"]:
        return 0
    
    # Delete the chunks
    collection.delete(ids=results["ids"])
    
    return len(results["ids"])


async def get_all_documents(
    kb_name: str,
    filter_dict: Optional[Dict[str, Any]] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Retrieve all documents from a knowledge base with optional filtering.
    
    Args:
        kb_name: The name of the knowledge base
        filter_dict: Optional dictionary for filtering documents
        limit: Maximum number of documents to retrieve
    
    Returns:
        List[Dict[str, Any]]: List of document chunks
    """
    try:
        # Get the collection - get_collection is not async so don't use await
        collection = get_collection(kb_name)
        
        # Build filter condition if provided
        filter_condition = None
        if filter_dict:
            # Convert filter dict to appropriate filter condition
            if "document_ids" in filter_dict and filter_dict["document_ids"]:
                filter_condition = {"document_id": {"$in": filter_dict["document_ids"]}}
            elif "document_id" in filter_dict and filter_dict["document_id"]:
                filter_condition = {"document_id": filter_dict["document_id"]}
        
        # Query all documents with the filter - get method is not async
        results = collection.get(
            where=filter_condition,
            limit=limit
        )
        
        # Format the results
        chunks = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                chunks.append({
                    "id": doc_id,
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i] if "metadatas" in results and i < len(results["metadatas"]) else {}
                })
        
        return chunks
    except Exception as e:
        print(f"Error retrieving all documents: {str(e)}")
        return [] 