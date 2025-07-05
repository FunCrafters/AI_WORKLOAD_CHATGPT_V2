#!/usr/bin/env python3
"""
PostgreSQL Database Tool: Get Smalltalk Context
Search smalltalk vectors for casual conversation topics using Ollama embeddings
"""

import json
import logging
import random
from db_postgres import execute_query
from agents.agent_prompts import SMALLTALK_SPECIALIST_EMBEDDING
from workload_embedding import get_vectorstore

# Logger
logger = logging.getLogger("DB Get Smalltalk")

# Configuration
SIMILARITY_THRESHOLD = 0.4
SEARCH_LIMIT = 10  # Get top 10 similar results, then pick random one


def _generate_query_embedding(query_text: str) -> list:
    """Generate embedding for query text using Ollama"""
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            logger.error("Vectorstore not available")
            return None
        
        # Get embedding function from vectorstore
        embedding_function = vectorstore._embedding_function
        if not embedding_function:
            logger.error("Embedding function not available")
            return None
        
        # Generate embedding using Ollama
        embedding = embedding_function.embed_query(query_text)
        return embedding
        
    except Exception as e:
        logger.error(f"Failed to generate embedding for query: {e}")
        return None


def db_rag_get_smalltalk(query: str = "") -> str:
    """
    Search smalltalk knowledge base for casual conversation topics using PostgreSQL embedding similarity.
    
    Args:
        query: Search query for smalltalk topics. If empty, returns random topic.
        
    Returns:
        str: JSON formatted smalltalk context information
    """
    try:
        search_query = query if query else "random topic"
        
        # Case 1: Empty query - get random topic
        if not query or query.strip() == "":
            logger.info("Empty query received, selecting random smalltalk topic")
            
            random_sql = """
            SELECT topic, category, knowledge_text
            FROM smalltalk_vectors
            ORDER BY RANDOM()
            LIMIT 1
            """
            
            results = execute_query(random_sql)
            
            if results:
                result = results[0]
                topic = result['topic']
                category = result['category']
                knowledge_text = result['knowledge_text']
                
                content = f"### SMLTK: {topic} ({category})\n{knowledge_text}"
                
                return json.dumps({
                    "status": "success",
                    "message": "Selected random smalltalk topic",
                    "search_query": search_query,
                    "content": {
                        "smltk_results": content
                    },
                    "llm_instruction": SMALLTALK_SPECIALIST_EMBEDDING,
                    "internal_info": {
                        "function_name": "db_rag_get_smalltalk",
                        "parameters": {"query": query},
                        "method": "random_selection"
                    }
                })
            else:
                return json.dumps({
                    "status": "success",
                    "message": "No smalltalk topics available in database",
                    "search_query": search_query,
                    "content": {"smltk_results": ""},
                    "internal_info": {
                        "function_name": "db_rag_get_smalltalk",
                        "parameters": {"query": query}
                    }
                })
        
        # Case 2: Query provided - perform embedding similarity search
        else:
            logger.info(f"Searching for smalltalk context with query: {query}")
            
            # Generate embedding using Ollama
            query_embedding = _generate_query_embedding(query)
            
            if query_embedding is not None:
                # Real pgvector similarity search
                logger.info("Using Ollama embedding-based similarity search")
                
                # Convert embedding to PostgreSQL vector format
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                # Get multiple similar results and pick one randomly for variety
                similarity_sql = """
                SELECT topic, category, knowledge_text, 
                       1 - (embedding <=> %s::vector) as similarity
                FROM smalltalk_vectors
                WHERE 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """
                
                results = execute_query(similarity_sql, (
                    embedding_str, embedding_str, SIMILARITY_THRESHOLD, embedding_str, SEARCH_LIMIT
                ))
                
                if results:
                    # Randomly select one from the top similar results for variety
                    result = random.choice(results)
                    logger.info(f"Selected random result from {len(results)} similar topics")
                    topic = result['topic']
                    category = result['category']
                    knowledge_text = result['knowledge_text']
                    similarity = result['similarity']
                    
                    content = f"### SMLTK: {topic} ({category})\n{knowledge_text}"
                    
                    return json.dumps({
                        "status": "success",
                        "message": f"Found smalltalk context for '{query}' (similarity: {similarity:.3f})",
                        "search_query": search_query,
                        "content": {
                            "smltk_results": content
                        },
                        "llm_instruction": SMALLTALK_SPECIALIST_EMBEDDING,
                        "internal_info": {
                            "function_name": "db_rag_get_smalltalk",
                            "parameters": {"query": query},
                            "method": "ollama_embedding_similarity_search",
                            "similarity_score": similarity,
                            "threshold": SIMILARITY_THRESHOLD,
                            "candidates_found": len(results)
                        }
                    })
                
                logger.info(f"No embedding match above threshold {SIMILARITY_THRESHOLD}, falling back to random")
            
            else:
                logger.info("Embedding generation failed, falling back to random")
            
            # No good match found - get random topic instead
            logger.info(f"No good smalltalk match for query '{query}', selecting random topic")
            
            random_sql = """
            SELECT topic, category, knowledge_text
            FROM smalltalk_vectors
            ORDER BY RANDOM()
            LIMIT 1
            """
            
            results = execute_query(random_sql)
            
            if results:
                result = results[0]
                topic = result['topic']
                category = result['category']
                knowledge_text = result['knowledge_text']
                
                content = f"### SMLTK: {topic} ({category})\n{knowledge_text}"
                
                return json.dumps({
                    "status": "success",
                    "message": f"No specific match for '{query}', selected random smalltalk topic",
                    "search_query": search_query,
                    "content": {
                        "smltk_results": content
                    },
                    "llm_instruction": SMALLTALK_SPECIALIST_EMBEDDING,
                    "internal_info": {
                        "function_name": "db_rag_get_smalltalk",
                        "parameters": {"query": query},
                        "method": "random_fallback"
                    }
                })
            else:
                return json.dumps({
                    "status": "success",
                    "message": "No smalltalk topics available in database",
                    "search_query": search_query,
                    "content": {"smltk_results": ""},
                    "internal_info": {
                        "function_name": "db_rag_get_smalltalk",
                        "parameters": {"query": query}
                    }
                })
                    
    except Exception as e:
        logger.error(f"Error in db_get_smalltalk: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching smalltalk context: {str(e)}",
            "search_query": query if query else "random topic",
            "content": {"smltk_results": ""},
            "internal_info": {
                "function_name": "db_rag_get_smalltalk",
                "parameters": {"query": query},
                "error": str(e)
            }
        })


def db_get_smalltalk_text(query: str = "") -> str:
    """
    Search smalltalk knowledge base (text format for backward compatibility)
    
    Args:
        query: Search query for smalltalk topics. If empty, returns random topic.
        
    Returns:
        str: Smalltalk context information in text format
    """
    # Use the main function and extract text content
    json_result = db_get_smalltalk(query)
    
    try:
        result_dict = json.loads(json_result)
        if result_dict.get("status") == "success":
            return result_dict["content"]["smltk_results"]
        else:
            return ""
    except:
        return ""