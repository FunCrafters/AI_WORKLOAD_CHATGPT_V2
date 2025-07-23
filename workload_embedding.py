#!/usr/bin/env python3
"""
Workload Embedding Functions
Embedding and vectorstore related functionality for the workload
"""

import logging
import textwrap
from typing import List

import ollama

# Chroma removed - all vector functionality is now in PostgreSQL

# Logger
logger = logging.getLogger("Workload Embedding")

#######################
# Global variables
#######################

embedding_ollama = None
embedding_log = None
embedding_model_name = None


#######################
# Embedding Classes
#######################


class OllamaEmbeddings:
    """Ollama embeddings using the ollama library"""

    def __init__(self, host: str, port: str, model: str):
        self.host = host
        self.port = port
        self.model = model
        self.client = ollama.Client(host=f"http://{host}:{port}")
        self.dimension = 768  # Known dimension for embedding models

    def embed_query(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings(model=self.model, prompt=text)
            return response["embedding"]
        except Exception as e:
            truncated_text = textwrap.shorten(text, width=50)
            raise Exception(f"Embedding failed for text '{truncated_text}': {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]


#######################
# Initialization Functions
#######################


def initialize_embeddings_and_vectorstore(config: dict, ollama_host: str, ollama_port: str) -> OllamaEmbeddings:
    """Initialize embeddings configurations and vectorstore using Ollama and PostgreSQL"""
    global embedding_ollama, embedding_log, embedding_model_name

    logger.info(f"Using embeddings from: {ollama_host}:{ollama_port}")
    logger.debug(f"Initializing embeddings from: {ollama_host}:{ollama_port}")

    # Store embedding model name
    embedding_model_name = config.get("EMBEDDING_MODEL_ID", "nomic-embed-text")

    embedding_ollama = OllamaEmbeddings(host=ollama_host, port=ollama_port, model=embedding_model_name)

    # Add PostgreSQL database information
    try:
        from db_postgres import get_postgres_database_info, initialize_postgres_db

        # Initialize PostgreSQL database connection
        if initialize_postgres_db():
            # Get PostgreSQL database info
            postgres_info = get_postgres_database_info()
            for info in postgres_info:
                logger.info(info)
        else:
            logger.error("Failed to initialize PostgreSQL database connection")
    except Exception as e:
        logger.error(f"Error accessing PostgreSQL database: {str(e)}")

    return embedding_ollama


#######################
# Getter Functions
#######################


def get_embedding_function():
    return embedding_ollama


def get_embedding_log():
    return embedding_log
