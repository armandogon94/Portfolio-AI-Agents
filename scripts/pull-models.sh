#!/bin/bash
set -e

echo "Pulling Ollama models for local development..."

# Main LLM model
echo "Pulling llama3.1:8b (main agent model)..."
ollama pull llama3.1:8b

# Embedding model
echo "Pulling nomic-embed-text (embeddings)..."
ollama pull nomic-embed-text

# Optional: lighter model for quick tests
echo "Pulling llama3.2:3b (lightweight testing)..."
ollama pull llama3.2:3b

echo ""
echo "Models ready! Available models:"
ollama list
