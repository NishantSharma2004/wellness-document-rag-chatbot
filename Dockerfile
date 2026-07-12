FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and configurations
COPY config/ config/
COPY src/ src/
COPY data/sample_documents/ data/sample_documents/
COPY app.py .
COPY ingest.py .
COPY evaluate.py .
COPY pyproject.toml .
COPY .streamlit/ .streamlit/

# Create empty directories for ignored persistence
RUN mkdir -p data/documents data/chroma_db data/processed

# Expose port
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
