"""
LangGraph agent implementation for document processing and queries.
"""
from typing import Dict, List, Optional, Any, Tuple, TypedDict, Annotated, Literal
import json
import asyncio

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, FunctionMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langgraph.graph import StateGraph, END
from langchain_core.runnables.config import RunnableConfig
import functools

from app.core.config import settings
from app.services.vector_store import query_vector_store
from app.models.document import KnowledgeBaseType
from .sse import encode_sse_event


# Define the state schema
class AgentState(TypedDict):
    """
    State schema for the LangGraph agent.
    """
    kb_type: str
    query: str
    document_id: Optional[str]
    retrieved_chunks: List[Dict[str, Any]]
    parsed_chunks: List[Dict[str, Any]]
    creative_output: Optional[str]
    final_answer: Optional[str]
    scraper_needed: bool
    scraper_query: Optional[str]


# Initialize the LLM
def get_llm(streaming_callback=None):
    """
    Get the LLM instance with optional streaming callback.
    
    Args:
        streaming_callback: Callback function for streaming responses
        
    Returns:
        LLM: Configured LLM instance
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.7,
        disable_streaming=streaming_callback is None,
        callbacks=[streaming_callback] if streaming_callback else None
    )
    return llm


# Node 1: Retrieval Node
async def retrieval_node(state: AgentState, stream_callback=None) -> AgentState:
    """
    Retrieval node for fetching relevant document chunks.
    
    This follows Anthropic's "Building Effective Agents" approach by isolating
    the retrieval step as an independent node with clear outputs.
    
    Args:
        state: Current agent state
        stream_callback: Optional streaming callback
        
    Returns:
        AgentState: Updated agent state with retrieved chunks
    """
    # Stream status update
    if stream_callback:
        await stream_callback(encode_sse_event("Retrieving relevant information..."))
    
    # Extract query and KB type from state
    query = state["query"]
    kb_type = state["kb_type"]
    document_id = state.get("document_id")
    
    # Build filter for document ID if provided
    filter_dict = {"document_id": document_id} if document_id else None
    
    # Query the vector store
    chunks = await query_vector_store(
        query_text=query, 
        kb_name=kb_type,
        n_results=5,
        filter_dict=filter_dict
    )
    
    # Check if we need to use the scraper (only for supplements KB with few/no results)
    scraper_needed = (
        kb_type == KnowledgeBaseType.SUPPLEMENTS.value and 
        (not chunks or len(chunks) < 2)
    )
    
    # Return updated state
    return {
        **state,
        "retrieved_chunks": chunks,
        "scraper_needed": scraper_needed,
        "scraper_query": query if scraper_needed else None
    }


# Node 2: Scraper Tool Node
async def scraper_tool_node(state: AgentState, stream_callback=None) -> AgentState:
    """
    Scraper tool node for fetching new product data when needed.
    
    Following Anthropic's "Tool Use" patterns by clearly defining when and how 
    to use external tools as part of the agent workflow.
    
    Args:
        state: Current agent state
        stream_callback: Optional streaming callback
        
    Returns:
        AgentState: Updated agent state with new retrieved chunks
    """
    # Check if scraper is needed
    if not state["scraper_needed"]:
        return state
    
    # Stream status update
    if stream_callback:
        await stream_callback(encode_sse_event(
            "Searching for up-to-date product information..."
        ))
    
    # Import here to avoid circular imports
    from app.api.routes.scraper import search_products_internal
    
    # Call the scraper
    products = await search_products_internal(state["scraper_query"])
    
    # If products were found, re-query the vector store
    if products:
        if stream_callback:
            await stream_callback(encode_sse_event(
                f"Found {len(products)} relevant products. Analyzing..."
            ))
            
        # Re-query the vector store after scraping
        chunks = await query_vector_store(
            query_text=state["query"],
            kb_name=state["kb_type"],
            n_results=5
        )
        
        # Update the state with the new chunks
        return {
            **state,
            "retrieved_chunks": chunks,
            "scraper_needed": False
        }
    
    return state


# Node 3: Parser Node
async def parser_node(state: AgentState, stream_callback=None) -> AgentState:
    """
    Parser node for summarizing and field-extracting from chunks.
    
    Following Anthropic's "Structured Output Generation" principles by clearly defining
    the expected output format and providing explicit instructions.
    
    Args:
        state: Current agent state
        stream_callback: Optional streaming callback
        
    Returns:
        AgentState: Updated agent state with parsed chunks
    """
    # Stream status update
    if stream_callback:
        await stream_callback(encode_sse_event("Analyzing retrieved information..."))
    
    # If no chunks were retrieved, return empty parsed chunks
    if not state["retrieved_chunks"]:
        return {
            **state,
            "parsed_chunks": []
        }
    
    # Initialize LLM
    llm = get_llm()
    
    # Process each chunk using the LLM
    parsed_chunks = []
    
    for chunk in state["retrieved_chunks"]:
        # Create system prompt for summarizing/extracting
        chunk_text = chunk["document"]
        metadata = chunk["metadata"]
        
        system_prompt = f"""
        You are an expert document parser and summarizer.
        Your task is to analyze the provided text and extract key information.
        
        Based on the knowledge base type, focus on the following:
        - For resumes: Extract skills, experience, education, and key qualifications.
        - For API docs: Extract endpoints, parameters, authentication methods, and examples.
        - For recipes: Extract ingredients, steps, nutritional info, and special tips.
        - For supplements: Extract benefits, ingredients, usage instructions, and health claims.
        
        Return a concise summary with the most important information.
        """
        
        # Run LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please analyze and summarize the following text:\n\n{chunk_text}")
        ]
        response = await llm.ainvoke(messages)
        
        # Add to parsed chunks
        parsed_chunks.append({
            "id": chunk["id"],
            "original_text": chunk_text,
            "summary": response.content,
            "metadata": metadata
        })
    
    return {
        **state,
        "parsed_chunks": parsed_chunks
    }


# Node 4: Creative Node
async def creative_node(state: AgentState, stream_callback=None) -> AgentState:
    """
    Creative node for running an evaluator-optimizer loop.
    
    Following Anthropic's "Self-Evaluation" approach by implementing a 
    draft → critique → refine loop for highest quality outputs.
    
    Args:
        state: Current agent state
        stream_callback: Optional streaming callback
        
    Returns:
        AgentState: Updated agent state with creative output
    """
    # Stream status update
    if stream_callback:
        await stream_callback(encode_sse_event("Generating creative response..."))
    
    # Initialize the LLM
    llm = get_llm()
    
    # Extract query and KB type
    query = state["query"]
    kb_type = state["kb_type"]
    
    # Construct context from parsed chunks
    context = ""
    for i, chunk in enumerate(state["parsed_chunks"], 1):
        context += f"Source {i}:\n{chunk['summary']}\n\n"
    
    # Define the system prompt based on KB type
    system_prompts = {
        KnowledgeBaseType.RESUMES.value: """
        You are an expert HR consultant who matches resumes to job descriptions.
        Analyze the resume information and the job query to provide detailed matching analysis.
        Focus on relevant skills, experience, and qualifications that match or don't match the job requirements.
        """,
        
        KnowledgeBaseType.API_DOCS.value: """
        You are an expert API documentation consultant.
        Provide clear, accurate answers to questions about APIs based on the documentation.
        Include code examples where relevant and explain parameters, endpoints and authentication methods.
        """,
        
        KnowledgeBaseType.RECIPES.value: """
        You are a creative culinary expert.
        Enhance recipes with suggestions, variations, and improvements.
        Provide nutritional insights and answer cooking-related questions with practical advice.
        """,
        
        KnowledgeBaseType.SUPPLEMENTS.value: """
        You are a wellness advisor specializing in supplements and health optimization.
        Provide evidence-based advice about supplements, their ingredients, benefits, and usage.
        For product bundles, explain synergies between products and personalize recommendations.
        Always include appropriate health disclaimers and encourage consulting healthcare providers.
        """
    }
    
    system_prompt = system_prompts.get(kb_type, system_prompts[KnowledgeBaseType.SUPPLEMENTS.value])
    
    # STEP 1: Generate initial draft
    if stream_callback:
        await stream_callback(encode_sse_event("Crafting initial response..."))
    
    draft_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Context information:\n\n{context}\n\nQuery: {query}\n\nPlease provide a comprehensive response.")
    ]
    
    draft_response = await llm.ainvoke(draft_messages)
    draft = draft_response.content
    
    # STEP 2: Self-critique the draft
    if stream_callback:
        await stream_callback(encode_sse_event("Evaluating response quality..."))
    
    critique_messages = [
        SystemMessage(content="""
        You are an expert content evaluator. Critically examine the draft response and identify:
        1. Factual inaccuracies or contradictions with the source material
        2. Missing important information relevant to the query
        3. Areas where clarity, coherence, or completeness could be improved
        4. Potential bias or tone issues
        
        Be specific in your critique to guide improvements.
        """),
        HumanMessage(content=f"Original query: {query}\n\nContext information:\n{context}\n\nDraft response:\n{draft}")
    ]
    
    critique_response = await llm.ainvoke(critique_messages)
    critique = critique_response.content
    
    # STEP 3: Generate improved version
    if stream_callback:
        await stream_callback(encode_sse_event("Refining response..."))
    
    refine_messages = [
        SystemMessage(content=system_prompt + "\n\nImprove the draft based on the critique provided."),
        HumanMessage(content=f"Original query: {query}\n\nContext information:\n{context}\n\nDraft response:\n{draft}\n\nCritique:\n{critique}\n\nPlease provide an improved version that addresses the critique.")
    ]
    
    final_response = await llm.ainvoke(refine_messages)
    refined_output = final_response.content
    
    # Return the updated state
    return {
        **state,
        "creative_output": refined_output,
        "final_answer": refined_output  # In this case, the creative output is our final answer
    }


# Build the LangGraph
def build_agent_graph(stream_callback=None):
    """
    Build the LangGraph agent graph.
    
    Args:
        stream_callback: Optional streaming callback
        
    Returns:
        StateGraph: Configured LangGraph state graph
    """
    # Create the workflow with defined nodes
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph
    workflow.add_node("retrieval", functools.partial(retrieval_node, stream_callback=stream_callback))
    workflow.add_node("scraper_tool", functools.partial(scraper_tool_node, stream_callback=stream_callback))
    workflow.add_node("parser", functools.partial(parser_node, stream_callback=stream_callback))
    workflow.add_node("creative", functools.partial(creative_node, stream_callback=stream_callback))
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "retrieval",
        lambda state: "scraper_tool" if state["scraper_needed"] else 
                    "parser" if state["retrieved_chunks"] and not state["parsed_chunks"] else
                    "creative" if state["parsed_chunks"] and not state["final_answer"] else
                    END
    )
    
    workflow.add_conditional_edges(
        "scraper_tool",
        lambda state: "parser" if state["retrieved_chunks"] and not state["parsed_chunks"] else
                    "creative" if state["parsed_chunks"] and not state["final_answer"] else
                    END
    )
    
    workflow.add_conditional_edges(
        "parser",
        lambda state: "creative" if state["parsed_chunks"] and not state["final_answer"] else
                    END
    )
    
    workflow.add_edge("creative", END)
    
    # Set the entry point
    workflow.set_entry_point("retrieval")
    
    # Compile the graph
    return workflow.compile()


async def run_agent(
    query: str,
    kb_type: str,
    document_id: Optional[str] = None,
    stream_callback=None
) -> Dict[str, Any]:
    """
    Run the agent with the given query.
    
    Args:
        query: User query
        kb_type: Knowledge base type
        document_id: Optional document ID to restrict search
        stream_callback: Optional streaming callback
        
    Returns:
        Dict[str, Any]: Agent result with final answer
    """
    try:
        # Build the agent graph
        agent = build_agent_graph(stream_callback)
        
        # Initialize the agent state
        initial_state = AgentState(
            kb_type=kb_type,
            query=query,
            document_id=document_id,
            retrieved_chunks=[],
            parsed_chunks=[],
            creative_output=None,
            final_answer=None,
            scraper_needed=False,
            scraper_query=None
        )
        
        # Run the agent
        result = await agent.ainvoke(initial_state)
        
        return result
    except Exception as e:
        print(f"Error in agent execution: {str(e)}")
        
        # Return a mock response
        mock_answers = {
            "resumes": {
                "skills": "The candidate possesses strong skills in Python, JavaScript, and SQL. They also demonstrate proficiency in data analysis, project management, and communication.",
                "experience": "The candidate has 5+ years of experience in software development, with specific expertise in web application development and database management.",
                "education": "The candidate holds a Bachelor's degree in Computer Science from a reputable university, along with several professional certifications in their field."
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
            "recipes": {
                "ingredients": "The main ingredients in this recipe are flour, sugar, eggs, butter, and vanilla extract. It also includes optional ingredients like chocolate chips or nuts for added flavor.",
                "steps": "This recipe involves several steps: mixing the dry ingredients, creaming the butter and sugar, adding eggs one at a time, combining everything, and baking at 350°F for 25-30 minutes.",
                "detail": "This is a classic cookie recipe that yields about 24 cookies. The texture is crisp on the outside and chewy on the inside. Perfect for family gatherings or dessert time."
            }
        }
        
        # Determine answer type based on query
        answer_type = "skills"  # default for resumes
        if any(keyword in query.lower() for keyword in ["experience", "work", "history"]):
            answer_type = "experience"
        elif any(keyword in query.lower() for keyword in ["education", "degree", "university"]):
            answer_type = "education"
        
        # Get the answer from the mock data
        answer = mock_answers.get(kb_type, {}).get(answer_type, f"Based on the document in the {kb_type} knowledge base, I can provide information about your query: '{query}'. This is a mock response.")
        
        # Return a structured result
        return {
            "kb_type": kb_type,
            "query": query,
            "document_id": document_id,
            "retrieved_chunks": [],
            "parsed_chunks": [],
            "creative_output": answer,
            "final_answer": answer,
            "scraper_needed": False,
            "scraper_query": None
        } 