#!/usr/bin/env python3
"""
RAG tool: Get smalltalk context
Search SMLTK knowledge base for casual conversation topics
Available only when application is in smalltalk mode
"""

import json
import os
import sqlite3
import logging
import random
from workload_rag_search import rag_search_details
from agents.agent_prompts import SMALLTALK_SPECIALIST_EMBEDDING

# Logger
logger = logging.getLogger("RAG Smalltalk Context")


def get_random_smalltalk_topic(conn: sqlite3.Connection) -> tuple:
    """
    Get a random smalltalk topic from the database
    
    Args:
        conn: SQLite database connection
        
    Returns:
        tuple: (id, topic, category, knowledge) or None if no records found
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, topic, category, knowledge 
        FROM smalltalk_records 
        ORDER BY RANDOM() 
        LIMIT 1
    """)
    return cursor.fetchone()


def rag_get_smalltalk_context(query: str = "") -> str:
    """
    Search smalltalk knowledge base for casual conversation topics (OpenAI Function Calling format)
    This function is only available when the application is in smalltalk mode.
    
    Args:
        query: Search query for smalltalk topics and casual conversation content. 
               If empty, returns a random smalltalk topic.
        
    Returns:
        str: JSON formatted smalltalk context information with SMLTK results
    """
    # Variables to track success and content
    success = False
    full_content = ""
    search_query = query if query else "random topic"
    message = ""
    
    try:
        # Connect to SQLite database once
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "smalltalk.db.sqlite")
        conn = sqlite3.connect(db_path)
        
        try:
            # Case 1: Empty query - get random topic
            if not query or query.strip() == "":
                logger.info("Empty query received, selecting random smalltalk topic")
                row = get_random_smalltalk_topic(conn)
                
                if row:
                    row_id, topic, category, knowledge = row
                    full_content = f"### SMLTK: {topic} ({category})\n{knowledge}"
                    message = "Selected random smalltalk topic"
                    success = True
                else:
                    message = "No smalltalk topics available in database"
                    
            else:
                # Case 2: Query provided - search in RAG first
                logger.info(f"Searching for smalltalk context with query: {query}")
                
                # Search using RAG
                smltk_config = {
                    "base_filters": {},
                    "required_sections": [],
                    "similarity_chunks": 0,
                    "qa_chunks": 0,
                    "smltk_chunks": 5  # Get 5 documents for random selection
                }
                
                search_results = rag_search_details(query, smltk_config)
                
                # Check if RAG search was successful
                if "error" not in search_results and search_results.get("smltk"):
                    smltk_docs = search_results.get("smltk", [])
                    
                    if smltk_docs:
                        # Log how many chunks we got
                        logger.info(f"Retrieved {len(smltk_docs)} smalltalk chunks from RAG")
                        
                        # Randomly select one chunk from the results
                        doc = random.choice(smltk_docs)
                        logger.info(f"Randomly selected chunk: {doc.metadata.get('name', 'unknown')}")
                        
                        # Extract topic from RAG result
                        topic = doc.metadata.get('name', '')
                        
                        if topic:
                            # Try to get full content from SQLite
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT id, topic, category, knowledge FROM smalltalk_records WHERE topic = ?", 
                                (topic,)
                            )
                            row = cursor.fetchone()
                            
                            if row:
                                # Success - found in both RAG and SQLite
                                row_id, topic, category, knowledge = row
                                full_content = f"### SMLTK: {topic} ({category})\n{knowledge}"
                                message = f"Found smalltalk context for '{query}'"
                                success = True
                            else:
                                # Topic found in RAG but not in SQLite - use chunk content
                                doc_name = doc.metadata.get('name', 'unknown')
                                category = doc.metadata.get('category', 'unknown')
                                full_content = f"### SMLTK: {doc_name} ({category})\n{doc.page_content}"
                                message = f"Found smalltalk context for '{query}' (using chunk)"
                                success = True
                        else:
                            # No topic in metadata - use chunk content
                            doc_name = doc.metadata.get('name', 'unknown')
                            category = doc.metadata.get('category', 'unknown') 
                            full_content = f"### SMLTK: {doc_name} ({category})\n{doc.page_content}"
                            message = f"Found smalltalk context for '{query}' (using chunk)"
                            success = True
                
                # If no success yet (RAG didn't find anything), get random topic
                if not success:
                    logger.info(f"No smalltalk context found for query '{query}', selecting random topic")
                    row = get_random_smalltalk_topic(conn)
                    
                    if row:
                        row_id, topic, category, knowledge = row
                        full_content = f"### SMLTK: {topic} ({category})\n{knowledge}"
                        message = f"No specific match for '{query}', selected random smalltalk topic"
                        success = True
                    else:
                        message = "No smalltalk topics available in database"
        
        finally:
            # Always close the connection
            conn.close()
        
        # Return success or failure based on what happened
        if success:
            return json.dumps({
                "status": "success",
                "message": message,
                "search_query": search_query,
                "content": {
                    "smltk_results": full_content
                },
                "llm_instruction": SMALLTALK_SPECIALIST_EMBEDDING,
                "internal_info": {
                    "function_name": "rag_get_smalltalk_context",
                    "parameters": {"query": query}
                }
            })
        else:
            # This should rarely happen - only if database is completely empty
            return json.dumps({
                "status": "error",
                "message": message,
                "search_query": search_query,
                "content": {"smltk_results": ""},
                "internal_info": {
                    "function_name": "rag_get_smalltalk_context",
                    "parameters": {"query": query}
                }
            })
            
    except Exception as e:
        # Single error handling point
        logger.error(f"Error in rag_get_smalltalk_context: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching smalltalk context: {str(e)}",
            "search_query": search_query,
            "content": {"smltk_results": ""},
            "internal_info": {
                "function_name": "rag_get_smalltalk_context",
                "parameters": {"query": query},
                "error": str(e)
            }
        })


def rag_get_smalltalk_context_text(query: str = "") -> str:
    """
    Search smalltalk knowledge base (text format for backward compatibility)
    Available only when application is in smalltalk mode.
    
    Args:
        query: Search query for smalltalk topics. If empty, returns random topic.
        
    Returns:
        str: Smalltalk context information in text format
    """
    # Use the main function and extract text content
    json_result = rag_get_smalltalk_context(query)
    
    try:
        result_dict = json.loads(json_result)
        if result_dict.get("status") == "success":
            return result_dict["content"]["smltk_results"]
        else:
            return ""
    except:
        return ""