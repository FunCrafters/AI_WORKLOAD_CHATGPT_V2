import os
from typing import List

import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def embed_ollama(text: str, model: str) -> List[float]:
    response = requests.post(OLLAMA_HOST, json={"model": model, "prompt": text}, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Failed to get embeddings: {response.text}")

    embedding = response.json()["embedding"]

    return embedding


def embd(text: str) -> List[float]:
    try:
        return embed_ollama(text, "nomic-embed-text")
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return []
