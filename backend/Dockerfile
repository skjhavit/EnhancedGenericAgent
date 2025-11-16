FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies using uv
RUN uv venv /app/venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies with uv (much faster than pip!)
RUN uv pip install -r requirements.txt

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads /data/chroma

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
