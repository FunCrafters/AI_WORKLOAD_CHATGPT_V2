#!/usr/bin/env python3
"""
Workload Embedding Functions
Embedding and vectorstore related functionality for the workload
"""

import os
import logging
import ollama
from typing import List, Any

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
        """Embed a single query"""
        try:
            response = self.client.embeddings(model=self.model, prompt=text)
            return response['embedding']
        except Exception as e:
            raise Exception(f"Embedding failed for text '{text[:50]}...': {e}")
            
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        return [self.embed_query(text) for text in texts]


#######################
# Initialization Functions
#######################

def initialize_embeddings_and_vectorstore(config: dict, ollama_host: str, ollama_port: str) -> tuple:
    """Initialize embeddings configurations (Chroma removed - PostgreSQL handles vectors)."""
    global embedding_ollama, embedding_log, embedding_model_name
    
    logger.info(f"Using embeddings from: {ollama_host}:{ollama_port}")
    embedding_log = []
    embedding_log.append(f"Initializing embeddings from: {ollama_host}:{ollama_port}")
   
    # Store embedding model name
    embedding_model_name = config.get('EMBEDDING_MODEL_ID', 'nomic-embed-text')
    
    # Use Ollama library for embeddings
    embedding_log.append("Initializing Ollama library embeddings...")
    
    embedding_ollama = OllamaEmbeddings(
        host=ollama_host,
        port=ollama_port,
        model=embedding_model_name
    )
    
    embedding_log.append("✓ Ollama library embeddings available")
    embedding_log.append(f"Using Ollama embeddings with dimension: {embedding_ollama.dimension}")
    embedding_log.append("✓ Vector storage handled by PostgreSQL with pgvector extension")
 
    embedding_log.append("Vector storage: PostgreSQL with pgvector extension")
    embedding_log.append("✓ Embedding generation ready for PostgreSQL vector operations")

    # Add PostgreSQL database information
    try:
        from db_postgres import initialize_postgres_db, get_postgres_database_info
        
        # Initialize PostgreSQL database connection
        if initialize_postgres_db():
            # Get PostgreSQL database info
            postgres_info = get_postgres_database_info()
            embedding_log.extend(postgres_info)
        else:
            embedding_log.append("\n⚠️  Failed to initialize PostgreSQL database connection")
    except Exception as e:
        embedding_log.append(f"\n⚠️  Error accessing PostgreSQL database: {str(e)}")
        logger.error(f"Error accessing PostgreSQL database: {str(e)}")
    
    
    return embedding_ollama, embedding_log


#######################
# Getter Functions
#######################

def get_embedding_function():
    """Get the initialized Ollama embedding function"""
    return embedding_ollama

def get_embedding_log():
    """Get the embedding initialization log"""
    return embedding_log
