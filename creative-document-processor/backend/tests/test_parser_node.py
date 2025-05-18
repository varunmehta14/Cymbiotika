"""
Unit tests for the Parser node in LangGraph agent.
"""
import pytest
from unittest.mock import AsyncMock, patch
import json

from app.services.langgraph_agent import parser_node


@pytest.mark.asyncio
async def test_parser_node_with_empty_chunks():
    """Test that parser node handles empty chunks correctly."""
    # Setup
    state = {
        "kb_type": "resumes",
        "query": "Test query",
        "document_id": None,
        "retrieved_chunks": [],
        "parsed_chunks": [],
        "creative_output": None,
        "final_answer": None,
        "scraper_needed": False,
        "scraper_query": None
    }
    
    # Execute
    result_state = await parser_node(state)
    
    # Assert
    assert result_state["parsed_chunks"] == []
    assert result_state["kb_type"] == "resumes"
    assert result_state["query"] == "Test query"
    

@pytest.mark.asyncio
@patch("app.services.langgraph_agent.get_llm")
async def test_parser_node_processes_chunks(mock_get_llm):
    """Test that parser node processes chunks correctly."""
    # Setup
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value.content = "Summarized content"
    mock_get_llm.return_value = mock_llm
    
    state = {
        "kb_type": "resumes",
        "query": "Test query",
        "document_id": None,
        "retrieved_chunks": [
            {
                "id": "chunk1",
                "document": "Test chunk content 1",
                "metadata": {"source": "test1"}
            },
            {
                "id": "chunk2",
                "document": "Test chunk content 2",
                "metadata": {"source": "test2"}
            }
        ],
        "parsed_chunks": [],
        "creative_output": None,
        "final_answer": None,
        "scraper_needed": False,
        "scraper_query": None
    }
    
    # Execute
    result_state = await parser_node(state)
    
    # Assert
    assert len(result_state["parsed_chunks"]) == 2
    assert result_state["parsed_chunks"][0]["id"] == "chunk1"
    assert result_state["parsed_chunks"][1]["id"] == "chunk2"
    assert result_state["parsed_chunks"][0]["summary"] == "Summarized content"
    assert result_state["parsed_chunks"][1]["summary"] == "Summarized content"
    assert result_state["parsed_chunks"][0]["metadata"]["source"] == "test1"
    assert result_state["parsed_chunks"][1]["metadata"]["source"] == "test2"
    
    # Verify LLM was called correctly
    assert mock_llm.ainvoke.call_count == 2
    

@pytest.mark.asyncio
@patch("app.services.langgraph_agent.get_llm")
async def test_parser_node_with_stream_callback(mock_get_llm):
    """Test that parser node handles streaming callback correctly."""
    # Setup
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value.content = "Summarized content"
    mock_get_llm.return_value = mock_llm
    
    state = {
        "kb_type": "api_docs",
        "query": "Test query",
        "document_id": None,
        "retrieved_chunks": [
            {
                "id": "chunk1",
                "document": "Test API documentation",
                "metadata": {"source": "api_doc1"}
            }
        ],
        "parsed_chunks": [],
        "creative_output": None,
        "final_answer": None,
        "scraper_needed": False,
        "scraper_query": None
    }
    
    # Mock stream callback
    callback_msgs = []
    async def mock_callback(msg):
        callback_msgs.append(msg)
    
    # Execute
    result_state = await parser_node(state, stream_callback=mock_callback)
    
    # Assert
    assert len(result_state["parsed_chunks"]) == 1
    assert result_state["parsed_chunks"][0]["id"] == "chunk1"
    assert result_state["parsed_chunks"][0]["summary"] == "Summarized content"
    
    # Verify stream callback was called
    assert len(callback_msgs) > 0
    
    # Verify LLM was called
    assert mock_llm.ainvoke.call_count == 1 