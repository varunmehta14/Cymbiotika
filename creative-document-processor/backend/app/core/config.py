"""
Configuration settings for the backend application.
"""
import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # API settings
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    BACKEND_DEBUG: bool = os.getenv("BACKEND_DEBUG", "False").lower() == "true"
    
    # Google AI API settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Storage paths
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./storage")
    RAW_DOCS_PATH: str = os.getenv("RAW_DOCS_PATH", "./storage/raw")
    INDEX_PATH: str = os.getenv("INDEX_PATH", "./storage/index")
    
    # Chroma settings
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./storage/chroma")
    
    # Playwright settings
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "True").lower() == "true"
    
    # Knowledge bases
    KNOWLEDGE_BASES: List[str] = ["resumes", "api_docs", "recipes", "supplements"]
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Model settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_MODEL: str = "gemini-1.5-flash"  # Using Gemini 2 Flash
    
    # Create necessary directories
    def setup_directories(self):
        """
        Create necessary directories for storage if they don't exist.
        """
        Path(self.STORAGE_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.RAW_DOCS_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.INDEX_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)
        
        # Create KB subdirectories
        for kb in self.KNOWLEDGE_BASES:
            Path(f"{self.RAW_DOCS_PATH}/{kb}").mkdir(parents=True, exist_ok=True)
            Path(f"{self.INDEX_PATH}/{kb}").mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
settings.setup_directories() 