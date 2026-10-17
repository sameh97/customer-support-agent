#!/bin/bash
# Run once after docker-compose up to pull models into the Ollama container.
# Models are saved in the ollama_models volume — only needs to run once.

echo "Pulling LLM model..."
docker compose exec ollama ollama pull llama3.1:8b

echo "Pulling embedding model..."
docker compose exec ollama ollama pull nomic-embed-text

echo "Done. Models ready."