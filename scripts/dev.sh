#!/bin/bash
set -e

echo "Starting local AI development stack..."

# Start Qdrant via Docker
docker compose -f docker-compose.dev.yml up -d

# Wait for Qdrant
echo "Waiting for Qdrant..."
until curl -sf http://localhost:6333/healthz > /dev/null 2>&1; do
    sleep 1
done
echo "Qdrant ready at http://localhost:6333"

# Check Ollama
if command -v ollama &> /dev/null; then
    if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Starting Ollama..."
        ollama serve &
        sleep 2
    fi
    echo "Ollama ready at http://localhost:11434"
else
    echo "WARNING: Ollama not installed. Run: brew install ollama"
fi

echo ""
echo "Local AI stack ready!"
echo "  Qdrant:  http://localhost:6333"
echo "  Ollama:  http://localhost:11434"
echo ""
echo "Run the app:  python -m uvicorn src.main:app --reload --port 8060"
echo "Run Chainlit: chainlit run src/chainlit_app.py --port 3060"
