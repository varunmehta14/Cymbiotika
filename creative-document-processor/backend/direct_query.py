#!/usr/bin/env python3
"""
A standalone test script that implements a simplified version of the query endpoint.
"""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json

app = FastAPI()

class QueryRequest(BaseModel):
    kb: str
    prompt: str
    doc_id: str = None

def encode_sse_event(data, event_type="message"):
    """Encode data as an SSE event"""
    message = f"event: {event_type}\n"
    
    if isinstance(data, str):
        message += f"data: {data}\n"
    else:
        message += f"data: {json.dumps(data)}\n"
    
    message += "\n"
    return message

@app.post("/direct-query")
async def direct_query(request: QueryRequest, req: Request):
    """
    A simplified version of the query endpoint that directly yields the SSE events.
    """
    print(f"Received request: {request}")
    
    async def event_generator():
        # Initial status
        yield encode_sse_event("Processing query...")
        
        # Create a mock response
        kb_type = request.kb
        prompt = request.prompt
        
        answer = "The candidate possesses strong skills in Python, JavaScript, and SQL. They also demonstrate proficiency in data analysis, project management, and communication."
        
        # Stream words with small delay
        words = answer.split()
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            print(f"Yielding chunk: {chunk}")
            yield encode_sse_event(chunk)
            await asyncio.sleep(0.2)
        
        # Final complete event
        print("Yielding final complete event")
        yield encode_sse_event({
            "status": "complete",
            "answer": answer,
            "sources": [{"title": "Mock Resume", "source": "mock_data"}]
        })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 