FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install Ollama CLI
RUN curl https://ollama.com/install.sh | sh

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["/bin/bash"]