#!/bin/sh

# 1. Start Ollama in the background
/bin/ollama serve &
pid=$!

# 2. Wait for Ollama to wake up
sleep 5
echo "🔴 Checking if Ollama is ready..."

# We use 'ollama list' to check if the server is up (instead of curl)
# If it can't connect, this command returns an error code
while ! ollama list > /dev/null 2>&1; do
    echo "Waiting for Ollama server..."
    sleep 1
done

# 3. Pull the default model automatically
echo "🟢 Ollama is ready! Pulling default model (llama3)..."
ollama pull llama3

# 4. Wait for the background process to keep the container running
wait $pid