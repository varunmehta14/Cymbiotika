"""
Server-Sent Events (SSE) implementation for streaming responses.
"""
import json
import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator

from fastapi import Request
from starlette.responses import StreamingResponse


def encode_sse_event(data: Any, event_type: str = "message") -> str:
    """
    Encode data as a Server-Sent Events (SSE) message.
    
    Args:
        data: Data to encode (will be JSON serialized)
        event_type: Optional event type
        
    Returns:
        str: Formatted SSE message
    """
    message = f"event: {event_type}\n"
    
    # Handle different data types
    if isinstance(data, str):
        # For strings, split by newlines and send each line separately
        for line in data.split("\n"):
            message += f"data: {line}\n"
    else:
        # For other types, JSON serialize
        message += f"data: {json.dumps(data)}\n"
    
    message += "\n"
    return message


async def generate_sse_stream(
    generator: AsyncGenerator,
    event_type: str = "message"
) -> StreamingResponse:
    """
    Generate a streaming response from an async generator.
    
    Args:
        generator: Async generator that yields SSE events
        event_type: Optional event type
        
    Returns:
        StreamingResponse: FastAPI streaming response
    """
    async def stream_generator():
        try:
            async for data in generator:
                yield encode_sse_event(data, event_type)
                
            # Send a completion event
            yield encode_sse_event({"status": "complete"}, "complete")
            
        except Exception as e:
            # Send an error event
            yield encode_sse_event({"status": "error", "message": str(e)}, "error")
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )


class SSECallback:
    """
    Callback for handling SSE streaming from LangChain.
    """
    
    def __init__(self, queue: asyncio.Queue):
        """
        Initialize the callback with a queue.
        
        Args:
            queue: Asyncio queue for message passing
        """
        self.queue = queue
    
    async def on_llm_new_token(self, token: str, **kwargs):
        """
        Handle new token generation from LLM.
        
        Args:
            token: Generated token
            kwargs: Additional arguments
        """
        await self.queue.put(token)


async def create_streaming_response(callback) -> StreamingResponse:
    """
    Create a streaming response for LLM output.
    
    Args:
        callback: Function to call for each token
        
    Returns:
        StreamingResponse: FastAPI streaming response
    """
    # Create a queue for message passing
    queue = asyncio.Queue()
    
    # Create an SSE callback
    sse_callback = SSECallback(queue)
    
    # Start the callback in a background task
    task = asyncio.create_task(callback(sse_callback))
    
    async def stream_generator():
        try:
            while True:
                if task.done():
                    # Check if the task raised an exception
                    if task.exception():
                        yield encode_sse_event(
                            {"status": "error", "message": str(task.exception())},
                            "error"
                        )
                    
                    # Send a completion event
                    yield encode_sse_event({"status": "complete"}, "complete")
                    break
                
                # Get the next token with a timeout
                try:
                    token = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield encode_sse_event(token)
                except asyncio.TimeoutError:
                    # No token available, continue waiting
                    continue
                
        except asyncio.CancelledError:
            # Handle client disconnection
            if not task.done():
                task.cancel()
            raise
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    ) 