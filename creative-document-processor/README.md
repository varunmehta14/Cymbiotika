# Creative Document Processor

A full-stack application for processing and analyzing various document types using AI-powered techniques.

## Architecture

![Architecture Diagram](./architecture.png)

## Features

- Document ingestion (PDF, TXT, MD) via file upload or URL fetch
- Knowledge base management for various document types (resumes, API docs, recipes, supplements)
- AI-powered document analysis and creative rewriting using Google Gemini 2 Flash
- Web scraping for supplement product data from Cymbiotika
- Vector storage using Chroma for efficient semantic search

## Tech Stack

- **Frontend**: React 18, Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.11), LangGraph agents
- **LLM**: Google Gemini 2 Flash via LangChain
- **Vector DB**: Chroma (local persistent store)
- **Scraper**: Playwright Python for headless web scraping

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (optional)

### Environment Variables

Copy the `.env.template` file to `.env` and fill in the required values:

```
GOOGLE_API_KEY=your_google_api_key_here
```

### Local Development Setup

1. **Backend Setup**:

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --reload
```

2. **Frontend Setup**:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

3. **Accessing the Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Docker Setup

Alternatively, you can use Docker Compose to run the entire application:

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down
```

## Usage

1. **Document Ingestion**:
   - Upload documents via the web interface
   - Provide URLs to fetch documents remotely
   - Select the appropriate knowledge base (KB) type

2. **Knowledge Base Interaction**:
   - Browse documents in each KB
   - View document previews
   - Query documents using natural language

3. **Specialized Features**:
   - Resume matching against job descriptions
   - API documentation Q&A
   - Recipe improvement suggestions
   - Personalized supplement bundle recommendations

## Design Decisions

### LangGraph Agent Architecture

The multi-step LLM pipeline uses LangGraph to orchestrate different processing nodes:

- **Parser Node**: Extracts key information from document chunks
- **Creative Node**: Implements an evaluator-optimizer loop for content refinement
- **ScraperTool Node**: Dynamically fetches supplement data when needed

### Vector Embeddings

- Using MiniLM-L6 for embedding generation due to its balance of performance and efficiency
- Chroma vector database provides persistent storage with efficient similarity search

### Data Flow Optimization

- Streaming responses with Server-Sent Events (SSE) for real-time UI updates
- Async processing for I/O-bound operations to maximize throughput

## Challenges and Trade-offs

### Performance vs. Accuracy

- Gemini 2 Flash offers faster responses but may sacrifice some accuracy compared to larger models
- Embedding model selection balances dimensionality and semantic representation quality

### Scraping Reliability

- Web scraping is inherently fragile to site changes
- Implemented resilient scraper with retry mechanisms and error handling

### Memory Management

- Large document processing can be memory-intensive
- Chunking strategies implemented to handle documents of any size

## License

MIT 