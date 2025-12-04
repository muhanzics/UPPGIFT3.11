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

# Expose Streamlit port
EXPOSE 8501

# Copy source code
COPY . .

CMD echo "\n\n\033[1;32m👉 OPEN THIS LINK: http://localhost:8501\033[0m\n\n" && \
    streamlit run gui.py --server.address=0.0.0.0