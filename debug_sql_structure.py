#!/usr/bin/env python3
"""
Debug SQL structure to understand tuple index issue
"""

import json
import logging
import psycopg2
from typing import List
from workload_embedding import get_vectorstore
from dotenv import load_dotenv, dotenv_values

# Load environment variables
load_dotenv()
config = dotenv_values(".env")

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
logger = logging.getLogger("SQL Debug")

def _generate_query_embedding(query: str) -> List[float]:
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

def debug_sql_query():
    """Debug the SQL query structure"""
    
    print("Initializing embeddings...")
    from workload_embedding import initialize_embeddings_and_vectorstore
    
    try:
        initialize_embeddings_and_vectorstore(config, "localhost", "11434")
        print("✅ Embeddings initialized")
    except Exception as e:
        print(f"❌ Failed to initialize embeddings: {e}")
        return
    
    query = "Rishi Moon"
    
    # Generate embedding
    query_embedding = _generate_query_embedding(query)
    if not query_embedding:
        print("❌ Failed to generate embedding")
        return
    
    print(f"✅ Generated embedding with {len(query_embedding)} dimensions")
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Test the similarity query
        print("\n=== Testing Similarity Query ===")
        similarity_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            AND NOT (metadata->>'chunk_name' LIKE '%QA%')
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor.execute(similarity_query, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, query_embedding, SIMILARITY_LIMIT))
        similarity_rows = cursor.fetchall()
        
        print(f"Similarity query returned {len(similarity_rows)} rows")
        if similarity_rows:
            first_row = similarity_rows[0]
            print(f"First row type: {type(first_row)}")
            print(f"First row length: {len(first_row)}")
            print(f"First row content: {first_row}")
            
            # Test unpacking
            try:
                chunk_text, metadata, similarity_score = first_row
                print(f"✅ Unpacking works: text={len(chunk_text)} chars, meta={type(metadata)}, sim={similarity_score}")
            except Exception as e:
                print(f"❌ Unpacking failed: {e}")
        
        # Test the QA query
        print("\n=== Testing QA Query ===")
        qa_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            AND metadata->>'chunk_name' LIKE '%QA%'
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor.execute(qa_query, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, query_embedding, SIMILARITY_LIMIT))
        qa_rows = cursor.fetchall()
        
        print(f"QA query returned {len(qa_rows)} rows")
        if qa_rows:
            first_row = qa_rows[0]
            print(f"First row type: {type(first_row)}")
            print(f"First row length: {len(first_row)}")
            print(f"First row content: {first_row}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sql_query()