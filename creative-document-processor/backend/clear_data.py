#!/usr/bin/env python3
"""
Script to clear all documents and vector store data from the system.
This will remove all uploaded documents, their metadata, and their vector embeddings.
"""
import os
import shutil
import chromadb
from chromadb.config import Settings

from app.core.config import settings
from app.models.document import KnowledgeBaseType

def clear_all_data():
    """
    Clear all document data, including:
    1. Raw document files
    2. Vector store collections
    """
    # 1. Clear raw document files
    raw_docs_path = settings.RAW_DOCS_PATH
    print(f"Clearing raw documents from: {raw_docs_path}")
    
    for kb_type in KnowledgeBaseType:
        kb_path = os.path.join(raw_docs_path, kb_type.value)
        if os.path.exists(kb_path):
            print(f"Removing documents from {kb_type.value} knowledge base...")
            shutil.rmtree(kb_path)
            os.makedirs(kb_path, exist_ok=True)
            print(f"✓ Recreated empty directory: {kb_path}")
    
    # 2. Clear vector store collections
    print("\nClearing vector store collections...")
    chroma_client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIRECTORY,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get all collections
    collections = chroma_client.list_collections()
    
    if not collections:
        print("No collections found in vector store.")
    else:
        for collection in collections:
            collection_name = collection.name
            print(f"Removing collection: {collection_name}")
            chroma_client.delete_collection(collection_name)
        
        print(f"✓ Removed {len(collections)} collections from vector store.")
    
    print("\n✓ All document data has been cleared successfully! The system is ready for fresh uploads.")

if __name__ == "__main__":
    # Ask for confirmation
    print("WARNING: This will permanently delete ALL documents and their metadata from the system.")
    print("This action cannot be undone.")
    confirmation = input("Type 'DELETE ALL DATA' to confirm: ")
    
    if confirmation == "DELETE ALL DATA":
        clear_all_data()
    else:
        print("Operation cancelled. No data was deleted.") 