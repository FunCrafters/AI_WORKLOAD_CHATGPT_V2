#!/usr/bin/env python3
"""
Database tool: Get boss details from PostgreSQL
Get detailed information about a specific boss from PostgreSQL rag_vectors table
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
logger = logging.getLogger("DB Boss Details")

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

def _search_boss_content(boss_name: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Search for boss content in PostgreSQL rag_vectors"""
    similarity_results = []
    qa_results = []
    
    try:
        # Generate embedding for the boss name
        query_embedding = _generate_query_embedding(boss_name)
        if not query_embedding:
            return similarity_results, qa_results
        
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Search for similarity results (BOSSES chunk_section, not QA)
        similarity_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'BOSSES'
            AND metadata->>'chunk_section' != 'QA'
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor.execute(similarity_query, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, query_embedding, SIMILARITY_LIMIT))
        similarity_rows = cursor.fetchall()
        
        for row in similarity_rows:
            chunk_text, metadata, similarity_score = row
            similarity_results.append({
                'content': chunk_text,
                'metadata': metadata,
                'similarity': float(similarity_score)
            })
        
        # Search for QA results (BOSSES chunk_section and QA)
        qa_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'BOSSES'
            AND metadata->'sections' ? 'QA'
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor.execute(qa_query, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, query_embedding, SIMILARITY_LIMIT))
        qa_rows = cursor.fetchall()
        
        for row in qa_rows:
            chunk_text, metadata, similarity_score = row
            qa_results.append({
                'content': chunk_text,
                'metadata': metadata,
                'similarity': float(similarity_score)
            })
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error searching boss content: {str(e)}")
    
    return similarity_results, qa_results

def _search_champion_fallback(boss_name: str) -> Optional[str]:
    """Search for champion information as fallback for boss queries"""
    try:
        # Generate embedding for the boss name
        query_embedding = _generate_query_embedding(boss_name)
        if not query_embedding:
            return None
        
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Search for champion content
        champion_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'CHAMPIONS'
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor.execute(champion_query, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, query_embedding, SIMILARITY_LIMIT))
        champion_rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if champion_rows:
            # Combine champion results
            champion_content = []
            for row in champion_rows:
                chunk_text, metadata, similarity_score = row
                name = metadata.get('name', 'unknown') if metadata else 'unknown'
                champion_content.append(f"### {name}\n{chunk_text}")
            
            if champion_content:
                combined_content = "\n\n".join(champion_content)
                return f"=== CHAMPION INFORMATION (used as boss reference) ===\n\n{combined_content}"
        
        return None
        
    except Exception as e:
        logger.error(f"Error searching champion fallback: {str(e)}")
        return None

def db_rag_get_boss_details(boss_name: str) -> str:
    """
    Get detailed information about a specific boss with fallback to champion details (PostgreSQL version)
    
    Args:
        boss_name: Name of the boss to get details for
        
    Returns:
        str: JSON formatted detailed information with separated QA and similarity results
    """
    try:
        # Search for boss-specific information
        similarity_results, qa_results = _search_boss_content(boss_name)
        
        # Process similarity results
        similarity_content = ""
        if similarity_results:
            # Randomly select from top results for variety
            selected_similarity = random.choice(similarity_results) if similarity_results else None
            if selected_similarity:
                name = selected_similarity['metadata'].get('name', 'unknown') if selected_similarity['metadata'] else 'unknown'
                similarity_content = f"### {name}\n{selected_similarity['content']}"
        
        # Process QA results  
        qa_content = ""
        if qa_results:
            # Randomly select from top results for variety
            selected_qa = random.choice(qa_results) if qa_results else None
            if selected_qa:
                name = selected_qa['metadata'].get('name', 'unknown') if selected_qa['metadata'] else 'unknown'
                qa_content = f"### Q&A: {name}\n{selected_qa['content']}"
        
        # Check if we found meaningful boss information
        has_boss_similarity = similarity_content and len(similarity_content.strip()) > 50
        has_boss_qa = qa_content and len(qa_content.strip()) > 50
        
        if has_boss_similarity or has_boss_qa:
            return json.dumps({
                "status": "success",
                "message": f"Found boss information for '{boss_name}'",
                "boss_name": boss_name,
                "content_type": "boss",
                "content": {
                    "similarity_results": similarity_content if has_boss_similarity else "",
                    "qa_results": qa_content if has_boss_qa else ""
                },
                "internal_info": {
                    "function_name": "db_rag_get_boss_details",
                    "parameters": {"boss_name": boss_name}
                }
            })
        
        # Fallback: Try to find champion information for this name
        # Many champions can appear as bosses in different game modes
        champion_content = _search_champion_fallback(boss_name)
        
        if champion_content and len(champion_content.strip()) > 50:
            return json.dumps({
                "status": "success",
                "message": f"Found champion information for '{boss_name}' (used as boss reference)",
                "boss_name": boss_name,
                "content_type": "champion_as_boss",
                "content": {
                    "similarity_results": champion_content,
                    "qa_results": ""
                },
                "internal_info": {
                    "function_name": "db_rag_get_boss_details",
                    "parameters": {"boss_name": boss_name}
                }
            })
        
        # If neither boss nor champion info found, return error
        return json.dumps({
            "status": "error",
            "message": f"No information found for boss '{boss_name}'",
            "boss_name": boss_name,
            "content_type": "none",
            "content": {
                "similarity_results": "",
                "qa_results": ""
            },
            "internal_info": {
                "function_name": "db_rag_get_boss_details",
                "parameters": {"boss_name": boss_name}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in db_get_boss_details: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Database error while searching for boss '{boss_name}'",
            "boss_name": boss_name,
            "content_type": "error",
            "content": {
                "similarity_results": "",
                "qa_results": ""
            },
            "internal_info": {
                "function_name": "db_rag_get_boss_details",
                "parameters": {"boss_name": boss_name},
                "error": str(e)
            }
        })