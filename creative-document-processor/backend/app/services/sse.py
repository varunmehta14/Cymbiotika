"""
Server-Sent Events (SSE) implementation for streaming responses.
"""
import json
import asyncio
import uuid
from typing import Any, Dict, List, Optional, AsyncGenerator, Callable

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


class SSEGenerator:
    """
    Generator for SSE events with a unique ID.
    """
    def __init__(self):
        self.id = str(uuid.uuid4())
        self._queue = asyncio.Queue()
        self._closed = False
    
    async def put(self, data: str):
        """Add data to the queue."""
        if not self._closed:
            await self._queue.put(data)
    
    async def close(self):
        """Close the generator."""
        self._closed = True
        await self._queue.put(None)  # Signal end
    
    async def iterator(self):
        """Return an async iterator for the queue."""
        while not self._closed:
            try:
                data = await self._queue.get()
                if data is None:  # End signal
                    break
                yield data
            except Exception as e:
                yield encode_sse_event({"error": str(e)}, "error")
                break


class SSEManager:
    """
    Manager for server-sent events connections.
    """
    def __init__(self):
        self._generators: Dict[str, SSEGenerator] = {}
    
    def create_generator(self) -> SSEGenerator:
        """
        Create a new SSE generator.
        
        Returns:
            SSEGenerator: New generator with unique ID
        """
        generator = SSEGenerator()
        self._generators[generator.id] = generator
        return generator
    
    async def send_event(self, generator_id: str, data: str):
        """
        Send an event to a specific generator.
        
        Args:
            generator_id: Generator ID
            data: Data to send
        """
        if generator_id in self._generators:
            await self._generators[generator_id].put(data)
    
    async def broadcast(self, data: str):
        """
        Broadcast an event to all generators.
        
        Args:
            data: Data to send
        """
        for generator in self._generators.values():
            await generator.put(data)
    
    async def close_connection(self, generator_id: str):
        """
        Close a specific connection.
        
        Args:
            generator_id: Generator ID to close
        """
        if generator_id in self._generators:
            await self._generators[generator_id].close()
            del self._generators[generator_id]


# Create a singleton instance
sse_manager = SSEManager()


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