#!/usr/bin/env python3
"""
Database tool: Get gameplay details from PostgreSQL
Get gameplay strategies and tactics from PostgreSQL rag_vectors table
"""

import json
import logging
import psycopg2
import random
from typing import List, Dict, Any, Optional
from workload_embedding import get_vectorstore

# Configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'user': 'tools', 
    'password': 'STAGING-kumquat-talon-succor-hum',
    'database': 'llm_tools',
    'port': 5432
}

SIMILARITY_THRESHOLD = 0.4
SIMILARITY_LIMIT = 10

# Logger
logger = logging.getLogger("DB Gameplay Details")

def _generate_query_embedding(query: str) -> Optional[List[float]]:
    """Generate embedding for query using Ollama"""
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            logger.error("Failed to get vectorstore")
            return None
        
        embedding = vectorstore._embedding_function.embed_query(query)
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None

def db_rag_get_gameplay_details(query: str) -> str:
    """
    Search gameplay information from PostgreSQL rag_vectors (PostgreSQL version)
    
    Args:
        query: Search query for gameplay information
        
    Returns:
        str: JSON formatted gameplay information from knowledge base
    """
    try:
        # Generate embedding for the query
        query_embedding = _generate_query_embedding(query)
        if not query_embedding:
            return json.dumps({
                "status": "error",
                "message": f"Failed to generate embedding for query '{query}'",
                "query": query,
                "content": "",
                "internal_info": {
                    "function_name": "db_rag_get_gameplay_details",
                    "parameters": {"query": query}
                }
            })
        
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Search for all results (GAMEPLAY chunk_section, both QA and non-QA)
        gameplay_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'GAMEPLAY'
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor.execute(gameplay_query, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, query_embedding, SIMILARITY_LIMIT))
        gameplay_rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Process results
        if gameplay_rows:
            # Randomly select from top results for variety
            gameplay_results = []
            for row in gameplay_rows:
                chunk_text, metadata, similarity_score = row
                gameplay_results.append({
                    'content': chunk_text,
                    'metadata': metadata,
                    'similarity': float(similarity_score)
                })
            
            if gameplay_results:
                selected_result = random.choice(gameplay_results)
                name = selected_result['metadata'].get('name', 'unknown') if selected_result['metadata'] else 'unknown'
                gameplay_content = f"### {name}\n{selected_result['content']}"
                
                return json.dumps({
                    "status": "success",
                    "message": f"Found gameplay information for query: '{query}'",
                    "query": query,
                    "content": gameplay_content,
                    "internal_info": {
                        "function_name": "db_rag_get_gameplay_details",
                        "parameters": {"query": query}
                    }
                })
        
        # No results found
        return json.dumps({
            "status": "error",
            "message": f"No gameplay information found for query: '{query}'",
            "query": query,
            "content": "",
            "internal_info": {
                "function_name": "db_rag_get_gameplay_details",
                "parameters": {"query": query}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in db_get_gameplay_details: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Database error while searching for gameplay '{query}'",
            "query": query,
            "content": "",
            "internal_info": {
                "function_name": "db_rag_get_gameplay_details",
                "parameters": {"query": query},
                "error": str(e)
            }
        })