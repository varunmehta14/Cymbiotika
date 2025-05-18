FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/storage/raw/resumes \
    /app/storage/raw/api_docs \
    /app/storage/raw/recipes \
    /app/storage/raw/supplements \
    /app/storage/index/resumes \
    /app/storage/index/api_docs \
    /app/storage/index/recipes \
    /app/storage/index/supplements \
    /app/storage/chroma

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 