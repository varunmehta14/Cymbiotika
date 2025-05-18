#!/usr/bin/env python3
import asyncio
import os
import json
from app.services.langgraph_agent import run_agent
from app.models.document import KnowledgeBaseType
from app.core.config import settings

async def main():
    """Test the agent directly without SSE streaming"""
    print("Testing direct agent execution")
    
    # Set API key directly
    api_key = "AIzaSyD1wnZAgNPnes4CmKyfc6RxQRFlGCWU0ZY"
    os.environ["GOOGLE_API_KEY"] = api_key
    settings.GOOGLE_API_KEY = api_key
    
    print(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Define query parameters
    kb_type = KnowledgeBaseType.RECIPES.value
    query = "What are the main ingredients in this recipe?"
    
    print(f"\nRunning agent with query: {query}")
    print(f"Knowledge base: {kb_type}")
    
    # Define a simple callback to print messages 
    async def print_callback(message):
        try:
            print(f"CALLBACK: {message}")
        except Exception as e:
            print(f"Callback error: {e}")
    
    try:
        # Run the agent directly
        result = await run_agent(
            query=query,
            kb_type=kb_type,
            document_id=None,
            stream_callback=print_callback
        )
        
        # Print the result
        print("\n--- AGENT RESULT ---")
        for key, value in result.items():
            if key in ["retrieved_chunks", "parsed_chunks"] and value:
                print(f"{key}: [{len(value)} items]")
            else:
                print(f"{key}: {value}")
        
        # Print the final answer if available
        if "final_answer" in result and result["final_answer"]:
            print("\n--- FINAL ANSWER ---")
            print(result["final_answer"])
        else:
            print("\n❌ No final answer in result!")
            
    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 