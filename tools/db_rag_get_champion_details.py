#!/usr/bin/env python3
"""
Database tool: Get champion details from PostgreSQL rag_vectors
Get detailed information about a specific champion from PostgreSQL rag_vectors table
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
logger = logging.getLogger("DB Champion RAG Details")

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

def db_rag_get_champion_details(champion_name: str) -> str:
    """
    Get detailed information about a specific champion from rag_vectors (PostgreSQL version)
    
    Args:
        champion_name: Name of the champion to get details for
        
    Returns:
        str: JSON formatted detailed information with separated QA and similarity results
    """
    try:
        # Generate embedding for the champion name
        query_embedding = _generate_query_embedding(champion_name)
        if not query_embedding:
            return json.dumps({
                "status": "error",
                "message": f"Failed to generate embedding for champion '{champion_name}'",
                "champion_name": champion_name,
                "content": {
                    "similarity_results": "",
                    "qa_results": ""
                },
                "internal_info": {
                    "function_name": "db_rag_get_champion_details",
                    "parameters": {"champion_name": champion_name}
                }
            })
        
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Search for similarity results (CHAMPIONS chunk_section, not QA)
        similarity_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'CHAMPIONS'
            AND NOT (metadata->'sections' ? 'QA')
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor.execute(similarity_query, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, query_embedding, SIMILARITY_LIMIT))
        similarity_rows = cursor.fetchall()
        
        # Search for QA results (CHAMPIONS chunk_section and QA)
        qa_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'CHAMPIONS'
            AND metadata->'sections' ? 'QA'
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor.execute(qa_query, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, query_embedding, SIMILARITY_LIMIT))
        qa_rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Process similarity results
        similarity_content = ""
        if similarity_rows:
            # Randomly select from top results for variety
            similarity_results = []
            for row in similarity_rows:
                chunk_text, metadata, similarity_score = row
                similarity_results.append({
                    'content': chunk_text,
                    'metadata': metadata,
                    'similarity': float(similarity_score)
                })
            
            if similarity_results:
                selected_result = random.choice(similarity_results)
                name = selected_result['metadata'].get('name', 'unknown') if selected_result['metadata'] else 'unknown'
                similarity_content = f"### {name}\n{selected_result['content']}"
        
        # Process QA results  
        qa_content = ""
        if qa_rows:
            # Randomly select from top results for variety
            qa_results = []
            for row in qa_rows:
                chunk_text, metadata, similarity_score = row
                qa_results.append({
                    'content': chunk_text,
                    'metadata': metadata,
                    'similarity': float(similarity_score)
                })
            
            if qa_results:
                selected_result = random.choice(qa_results)
                name = selected_result['metadata'].get('name', 'unknown') if selected_result['metadata'] else 'unknown'
                qa_content = f"### Q&A: {name}\n{selected_result['content']}"
        
        # Check if we have any meaningful results
        has_similarity = similarity_content and similarity_content.strip()
        has_qa = qa_content and qa_content.strip()
        
        if not has_similarity and not has_qa:
            return json.dumps({
                "status": "error",
                "message": f"No information found for champion '{champion_name}'",
                "champion_name": champion_name,
                "content": {
                    "similarity_results": "",
                    "qa_results": ""
                },
                "internal_info": {
                    "function_name": "db_rag_get_champion_details",
                    "parameters": {"champion_name": champion_name}
                }
            })
        
        return json.dumps({
            "status": "success", 
            "message": f"Found detailed information for champion '{champion_name}'",
            "champion_name": champion_name,
            "content": {
                "similarity_results": similarity_content if has_similarity else "",
                "qa_results": qa_content if has_qa else ""
            },
            "internal_info": {
                "function_name": "db_rag_get_champion_details",
                "parameters": {"champion_name": champion_name}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in db_get_champion_rag_details: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Database error while searching for champion '{champion_name}'",
            "champion_name": champion_name,
            "content": {
                "similarity_results": "",
                "qa_results": ""
            },
            "internal_info": {
                "function_name": "db_rag_get_champion_details",
                "parameters": {"champion_name": champion_name},
                "error": str(e)
            }
        })