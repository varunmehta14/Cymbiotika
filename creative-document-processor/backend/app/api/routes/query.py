"""
Routes for querying documents and knowledge bases.
"""
from typing import Dict, List, Optional, Any
import asyncio

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse

from app.models.document import QueryRequest, QueryResponse, SupplementRewriteRequest
from app.services.langgraph_agent import run_agent
from app.services.sse import encode_sse_event
from app.core.config import settings

router = APIRouter()


@router.post("/", response_class=StreamingResponse)
async def query_knowledge_base(request: QueryRequest, req: Request):
    """
    Query a knowledge base with natural language.
    
    Args:
        request: Query request
        req: FastAPI request
        
    Returns:
        StreamingResponse: Streaming response with query results
    """
    print(f"Received query request: {request}")
    
    async def event_generator():
        try:
            # Stream initial status
            yield encode_sse_event("Processing query...")
            
            # Check if Google API key is available
            if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "":
                print("Warning: No Google API key found. Using mock response instead.")
                # Add small delay to simulate processing
                await asyncio.sleep(2)
                
                # Create mock response based on the knowledge base and query
                kb_type = request.kb
                prompt = request.prompt
                
                # Use our mock answers dictionary
                mock_answers = {
                    "recipes": {
                        "ingredients": "The main ingredients in this recipe are flour, sugar, eggs, butter, and vanilla extract. It also includes optional ingredients like chocolate chips or nuts for added flavor.",
                        "steps": "This recipe involves several steps: mixing the dry ingredients, creaming the butter and sugar, adding eggs one at a time, combining everything, and baking at 350°F for 25-30 minutes.",
                        "detail": "This is a classic cookie recipe that yields about 24 cookies. The texture is crisp on the outside and chewy on the inside. Perfect for family gatherings or dessert time."
                    },
                    "supplements": {
                        "benefits": "This supplement offers several benefits including improved immune function, increased energy levels, and support for cognitive health. It's designed to fill nutritional gaps in your diet.",
                        "ingredients": "The key ingredients in this supplement include Vitamin C, Zinc, Magnesium, B-complex vitamins, and a proprietary herbal blend for enhanced absorption.",
                        "usage": "For optimal results, take 2 capsules daily with food. It's recommended to use consistently for at least 30 days to experience the full benefits."
                    },
                    "api_docs": {
                        "endpoints": "The API provides several endpoints including /users, /products, and /orders. Each endpoint supports standard HTTP methods like GET, POST, PUT, and DELETE.",
                        "authentication": "Authentication is handled through JWT tokens. You need to first obtain a token via the /auth endpoint and then include it in the Authorization header for subsequent requests.",
                        "examples": "Example usage: `curl -H 'Authorization: Bearer TOKEN' https://api.example.com/users` to retrieve user information."
                    },
                    "resumes": {
                        "skills": "The candidate possesses strong skills in Python, JavaScript, and SQL. They also demonstrate proficiency in data analysis, project management, and communication.",
                        "experience": "The candidate has 5+ years of experience in software development, with specific expertise in web application development and database management.",
                        "education": "The candidate holds a Bachelor's degree in Computer Science from a reputable university, along with several professional certifications in their field."
                    }
                }
                
                # Determine which type of answer to provide based on the query
                answer_type = "detail"  # default
                
                if any(keyword in prompt.lower() for keyword in ["skill", "capable", "ability"]):
                    answer_type = "skills"
                elif any(keyword in prompt.lower() for keyword in ["experience", "work", "history"]):
                    answer_type = "experience"
                elif any(keyword in prompt.lower() for keyword in ["education", "degree", "university"]):
                    answer_type = "education"
                elif any(keyword in prompt.lower() for keyword in ["ingredient", "what's in", "contain"]):
                    answer_type = "ingredients"
                elif any(keyword in prompt.lower() for keyword in ["step", "how to", "procedure", "instruction"]):
                    answer_type = "steps"
                elif any(keyword in prompt.lower() for keyword in ["benefit", "advantage", "good for"]):
                    answer_type = "benefits"
                elif any(keyword in prompt.lower() for keyword in ["use", "take", "dosage", "how much"]):
                    answer_type = "usage"
                elif any(keyword in prompt.lower() for keyword in ["endpoint", "api", "route"]):
                    answer_type = "endpoints"
                elif any(keyword in prompt.lower() for keyword in ["auth", "token", "login"]):
                    answer_type = "authentication"
                elif any(keyword in prompt.lower() for keyword in ["example", "sample", "demo"]):
                    answer_type = "examples"
                
                # Get the answer or use a default response
                if kb_type in mock_answers and answer_type in mock_answers[kb_type]:
                    answer = mock_answers[kb_type][answer_type]
                else:
                    answer = f"Based on the document in the {kb_type} knowledge base, I can provide the following information related to your query about '{prompt}': This is a mock response for demonstration purposes."
                
                print(f"Generated answer: {answer[:50]}...")
                
                # Stream words with small delay to simulate LLM
                words = answer.split()
                for i in range(0, len(words), 3):
                    chunk = " ".join(words[i:i+3]) + " "
                    print(f"Yielding chunk: {chunk}")
                    yield encode_sse_event(chunk)
                    await asyncio.sleep(0.2)  # Small delay between chunks
                
                # Send final result
                print("Yielding final complete event")
                yield encode_sse_event({
                    "status": "complete", 
                    "answer": answer,
                    "sources": [{
                        "title": f"Mock {kb_type.capitalize()} Document",
                        "source": "mock_data",
                        "chunk_index": 0
                    }]
                })
            else:
                # Run the actual agent if API key is available
                try:
                    print(f"Starting agent run with Google API key: {request.prompt}, kb: {request.kb}, doc_id: {request.doc_id}")
                    
                    # Create a queue to receive events from the agent
                    queue = asyncio.Queue()
                    
                    # Start the agent in a background task
                    task = asyncio.create_task(run_agent(
                        query=request.prompt,
                        kb_type=request.kb,
                        document_id=request.doc_id,
                        stream_callback=lambda event: queue.put(event)
                    ))
                    
                    # Process events from the queue
                    while True:
                        if task.done():
                            # Check if the task raised an exception
                            if task.exception():
                                yield encode_sse_event({
                                    "status": "error",
                                    "message": str(task.exception())
                                })
                            
                            # Get the final result
                            result = task.result()
                            
                            # Yield the final answer
                            if result and "final_answer" in result:
                                yield encode_sse_event({
                                    "status": "complete",
                                    "answer": result["final_answer"],
                                    "sources": [chunk["metadata"] for chunk in result.get("retrieved_chunks", [])]
                                })
                            else:
                                yield encode_sse_event({
                                    "status": "error",
                                    "message": "No results found."
                                })
                            
                            break
                        
                        # Get message from queue with timeout
                        try:
                            message = await asyncio.wait_for(queue.get(), timeout=0.1)
                            yield encode_sse_event(message)
                        except asyncio.TimeoutError:
                            # No message available, continue
                            continue
                        
                except Exception as e:
                    print(f"Error in agent execution: {str(e)}")
                    yield encode_sse_event({
                        "status": "error",
                        "message": f"Error in agent execution: {str(e)}"
                    })
                
        except Exception as e:
            # Stream error
            print(f"Error in query processing: {str(e)}")
            yield encode_sse_event({
                "status": "error", 
                "message": str(e)
            })
    
    # Return streaming response
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/supplement/rewrite", response_class=StreamingResponse)
async def rewrite_supplement(request: SupplementRewriteRequest, req: Request):
    """
    Rewrite supplement product description with a specific tone.
    
    Args:
        request: Rewrite request
        req: FastAPI request
        
    Returns:
        StreamingResponse: Streaming response with rewritten content
    """
    print(f"Received rewrite request: {request}")
    
    async def event_generator():
        try:
            # Stream initial status
            yield encode_sse_event("Analyzing product for rewriting...")
            
            # Check if Google API key is available
            if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "":
                print("Warning: No Google API key found. Using mock response instead.")
                # Add small delay to simulate processing
                await asyncio.sleep(2)
                
                # Create different mock responses based on the tone
                tone = request.tone.lower()
                doc_id = request.doc_id
                
                # Define mock responses for different tones
                mock_rewrites = {
                    "enthusiastic": "🌟 WOW! This AMAZING supplement is a GAME-CHANGER for your health! Packed with POWERFUL natural ingredients, it SUPERCHARGES your immune system and BOOSTS your energy levels INSTANTLY! Users are ABSOLUTELY LOVING the incredible results they're seeing in just DAYS! Don't miss out on this REVOLUTIONARY formula that's changing lives! Try it TODAY and feel the DIFFERENCE immediately! 💪",
                    
                    "scientific": "This clinically-supported nutritional supplement contains a proprietary blend of bioactive compounds, including essential micronutrients and phytochemicals with demonstrated efficacy in randomized controlled trials. The formula's primary constituents have been shown to modulate immune function markers and enhance cellular energy production pathways. Statistical analyses of n=342 participants indicated significant improvements in key biomarkers compared to placebo (p<0.05). The recommended dosage is based on pharmacokinetic data establishing optimal absorption rates.",
                    
                    "balanced": "This well-formulated supplement offers a carefully selected blend of ingredients that support overall wellness. Developed through research and customer feedback, it provides nutritional benefits that may help enhance immune function and energy levels. Many users report positive experiences after consistent use. The natural formulation is designed to complement a healthy lifestyle, with clear dosage instructions for optimal results.",
                    
                    "minimalist": "Essential supplement. Natural ingredients. Supports immunity. Enhances energy. Simple dosing. Quality tested. Consistent results. Clean formula.",
                    
                    "premium": "Introducing our exclusive, artisanal wellness elixir, meticulously crafted from the world's most exceptional botanicals. This sophisticated formulation represents the pinnacle of nutritional science, elevating your well-being to extraordinary heights. Each small-batch blend undergoes rigorous quality assurance to ensure unparalleled potency. Discerning health enthusiasts will appreciate the refined efficacy and the subtle complexity of results that unfold with continued use."
                }
                
                # Get the appropriate rewrite or use a default
                if tone in mock_rewrites:
                    rewrite = mock_rewrites[tone]
                else:
                    rewrite = f"This supplement has been reformulated to reflect a {tone} tone while maintaining all factual information about its benefits, ingredients, and usage instructions. This is a mock response as no Google API key was provided for the LLM."
                
                print(f"Generated rewrite in {tone} tone: {rewrite[:50]}...")
                
                # Stream words with small delay to simulate LLM
                words = rewrite.split()
                for i in range(0, len(words), 3):
                    chunk = " ".join(words[i:i+3]) + " "
                    print(f"Yielding chunk: {chunk}")
                    yield encode_sse_event(chunk)
                    await asyncio.sleep(0.2)  # Small delay between chunks
                
                # Send final result
                print("Yielding final complete event")
                yield encode_sse_event({
                    "status": "complete", 
                    "rewritten": rewrite,
                    "original_doc_id": doc_id
                })
            else:
                # Create a specific query for rewriting
                query = f"Rewrite the product description in a {request.tone} tone. Make it persuasive but factual."
                
                # Create a queue to receive events from the agent
                queue = asyncio.Queue()
                
                # Start the agent in a background task
                task = asyncio.create_task(run_agent(
                    query=query,
                    kb_type="supplements",
                    document_id=request.doc_id,
                    stream_callback=lambda event: queue.put(event)
                ))
                
                # Process events from the queue
                while True:
                    if task.done():
                        # Check if the task raised an exception
                        if task.exception():
                            yield encode_sse_event({
                                "status": "error",
                                "message": str(task.exception())
                            })
                        
                        # Get the final result
                        result = task.result()
                        
                        # Yield the final answer
                        if result and "final_answer" in result:
                            yield encode_sse_event({
                                "status": "complete",
                                "rewritten": result["final_answer"],
                                "original_doc_id": request.doc_id
                            })
                        else:
                            yield encode_sse_event({
                                "status": "error",
                                "message": "Rewrite failed. No results found."
                            })
                        
                        break
                    
                    # Get message from queue with timeout
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=0.1)
                        yield encode_sse_event(message)
                    except asyncio.TimeoutError:
                        # No message available, continue
                        continue
                
        except Exception as e:
            # Stream error
            print(f"Error in rewrite processing: {str(e)}")
            yield encode_sse_event({
                "status": "error", 
                "message": str(e)
            })
    
    # Return streaming response
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    ) 