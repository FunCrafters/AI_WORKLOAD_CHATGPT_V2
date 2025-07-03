#!/usr/bin/env python3
"""
Workload Embedding Functions
Embedding and vectorstore related functionality for the workload
"""

import os
import logging
import ollama
from typing import List, Any

from langchain_community.vectorstores.chroma import Chroma
from langchain_chroma import Chroma
from chromadb import PersistentClient

# Logger
logger = logging.getLogger("Workload Embedding")

#######################
# Global variables
#######################

vectorstore_ollama = None
vectorstore_log = None
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
        """Embed a single query (required by LangChain)"""
        try:
            response = self.client.embeddings(model=self.model, prompt=text)
            return response['embedding']
        except Exception as e:
            raise Exception(f"Embedding failed for text '{text[:50]}...': {e}")
            
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents (required by LangChain)"""
        return [self.embed_query(text) for text in texts]


#######################
# Initialization Functions
#######################

def initialize_embeddings_and_vectorstore(config: dict, ollama_host: str, ollama_port: str) -> tuple:
    """Initialize embeddings and vectorstore configurations."""
    global vectorstore_ollama, vectorstore_log, embedding_model_name
    
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
 
    db_dir = config.get('WORKLOAD_DB_PATH')
    embedding_log.append(f"Vector DB path: {db_dir}")
    
    # Check if database directory exists
    if not os.path.exists(db_dir):
        embedding_log.append(f"⚠️  WARNING: Database directory does not exist: {db_dir}")
        embedding_log.append("   This will create a new empty database.")
        embedding_log.append("   Check if the path is correct in your .env file.")
    else:
        embedding_log.append(f"✓ Database directory exists: {db_dir}")
    
    # Initialize vectorstore
    client = PersistentClient(path=db_dir)
    
    vectorstore_ollama = Chroma(
        embedding_function=embedding_ollama,
        client=client,
        collection_name="Mandocar"
    )
    
    embedding_log.append("Vectorstore initialized successfully")
    
    # Initialize game data cache
    try:
        # Import here to avoid circular imports
        from tools_functions import initialize_game_data_cache
        initialize_game_data_cache(vectorstore_ollama)
        embedding_log.append("✓ Game data cache initialized successfully")
    except Exception as e:
        embedding_log.append(f"⚠️  Warning: Failed to initialize game data cache: {str(e)}")
        logger.warning(f"Failed to initialize game data cache: {str(e)}")
    
    # Initialize smalltalk cache
    try:
        from db_smalltalk import initialize_smalltalk_db
        if initialize_smalltalk_db():
            embedding_log.append("✓ Smalltalk cache initialized successfully")
        else:
            embedding_log.append("⚠️  Warning: Failed to initialize smalltalk cache")
    except Exception as e:
        embedding_log.append(f"⚠️  Warning: Failed to initialize smalltalk cache: {str(e)}")
        logger.warning(f"Failed to initialize smalltalk cache: {str(e)}")
    
    # Analyze database content
    embedding_log.append("\n--- RAG DATABASE ANALYSIS (Mandocar.db) ---")
    try:
        collection = client.get_collection("Mandocar")
        total_documents = collection.count()
        embedding_log.append(f"Total documents in database: {total_documents}")
        
        if total_documents > 0:
            # Get ALL documents to analyze structure (like in builder.py)
            all_docs = collection.get(include=["metadatas"])
            
            # Analyze categories
            categories = {}
            sections = {}
            names = set()
            
            for metadata in all_docs['metadatas']:
                # Count categories
                category = metadata.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # Count sections
                section = metadata.get('section', 'unknown')
                sections[section] = sections.get(section, 0) + 1
                
                # Collect unique names
                name = metadata.get('name', 'unknown')
                names.add(name)
            
            embedding_log.append(f"Unique entities: {len(names)}")
            embedding_log.append(f"Categories found: {len(categories)}")
            for category, count in sorted(categories.items()):
                percentage = (count / total_documents) * 100
                embedding_log.append(f"  - {category}: {count} docs ({percentage:.1f}%)")
            
            # Special sections analysis
            qa_count = sections.get('Q&A', 0)
            smltk_count = sections.get('SMLTK', 0)
            if qa_count > 0:
                qa_percentage = (qa_count / total_documents) * 100
                embedding_log.append(f"Q&A section: {qa_count} docs ({qa_percentage:.1f}%)")
            if smltk_count > 0:
                smltk_percentage = (smltk_count / total_documents) * 100
                embedding_log.append(f"SMLTK section: {smltk_count} docs ({smltk_percentage:.1f}%)")
            
            embedding_log.append(f"Sections found: {len(sections)}")
            # Show only top 10 sections to avoid too much output
            sorted_sections = sorted(sections.items(), key=lambda x: x[1], reverse=True)
            for section, count in sorted_sections[:10]:
                percentage = (count / total_documents) * 100
                embedding_log.append(f"  - {section}: {count} docs ({percentage:.1f}%)")
            if len(sections) > 10:
                embedding_log.append(f"  ... and {len(sections) - 10} more sections")
            
            # Sample entity names
            sample_names = sorted(list(names))[:10]
            embedding_log.append(f"Sample entities: {', '.join(sample_names)}")
            if len(names) > 10:
                embedding_log.append(f"... and {len(names) - 10} more entities")
                
        else:
            embedding_log.append("⚠️  Database is empty - no documents found!")
            embedding_log.append("   This explains why RAG queries return no results.")
            embedding_log.append("   You need to populate the database using the builder tool.")
            
    except Exception as e:
        embedding_log.append(f"Error analyzing database: {str(e)}")
    
    embedding_log.append("--- RAG DATABASE ANALYSIS END ---")
    
    # Add GCS database information
    try:
        from db_gcs import initialize_gcs_db, get_gcs_database_info
        
        # Initialize GCS database connection
        if initialize_gcs_db():
            # Get GCS database info
            gcs_info = get_gcs_database_info()
            embedding_log.extend(gcs_info)
        else:
            embedding_log.append("\n⚠️  Failed to initialize GCS database connection")
    except Exception as e:
        embedding_log.append(f"\n⚠️  Error accessing GCS database: {str(e)}")
        logger.error(f"Error accessing GCS database: {str(e)}")
    
    # Add Smalltalk database information
    try:
        from db_smalltalk import get_smalltalk_database_info
        
        # Get smalltalk database info
        smalltalk_info = get_smalltalk_database_info()
        embedding_log.extend(smalltalk_info)
    except Exception as e:
        embedding_log.append(f"\n⚠️  Error accessing smalltalk database: {str(e)}")
        logger.error(f"Error accessing smalltalk database: {str(e)}")
    
    # Add Lore database information
    try:
        from db_lore import get_lore_database_info
        
        # Get lore database info
        lore_info = get_lore_database_info()
        embedding_log.extend(lore_info)
    except Exception as e:
        embedding_log.append(f"\n⚠️  Error accessing lore database: {str(e)}")
        logger.error(f"Error accessing lore database: {str(e)}")
    
    # Store the log globally
    vectorstore_log = embedding_log
    
    return vectorstore_ollama, embedding_log


#######################
# Getter Functions
#######################

def get_vectorstore():
    """Get the initialized vectorstore"""
    return vectorstore_ollama

def get_vectorstore_log():
    """Get the vectorstore initialization log"""
    return vectorstore_log

def get_embedding_model_name():
    """Get the embedding model name"""
    return embedding_model_name
