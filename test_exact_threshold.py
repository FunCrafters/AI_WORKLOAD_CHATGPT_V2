#!/usr/bin/env python3
"""
Test with exact threshold from our diagnostics
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

def test_with_actual_threshold():
    """Test with threshold that should work based on diagnostics"""
    
    print("=== Initializing embeddings ===")
    from workload_embedding import initialize_embeddings_and_vectorstore
    
    try:
        initialize_embeddings_and_vectorstore(config, "localhost", "11434")
        print("✅ Embeddings initialized")
    except Exception as e:
        print(f"❌ Failed to initialize embeddings: {e}")
        return
    
    # Generate embedding
    vectorstore = get_vectorstore()
    query_embedding = vectorstore._embedding_function.embed_query("Rishi Moon")
    print(f"✅ Generated embedding with {len(query_embedding)} dimensions")
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Test with threshold 0.35 (lower than the 0.42 we saw in diagnostics)
        print("\n=== Test with threshold 0.35 ===")
        test_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            AND NOT (metadata->>'chunk_name' LIKE '%%QA%%')
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        params = (query_embedding, query_embedding, 0.35, query_embedding, 10)
        print(f"Query has {test_query.count('%s')} placeholders")
        print(f"Providing {len(params)} parameters")
        
        cursor.execute(test_query, params)
        rows = cursor.fetchall()
        print(f"✅ Found {len(rows)} rows with threshold 0.35")
        
        for i, row in enumerate(rows):
            chunk_text, metadata, similarity = row
            entity_name = metadata.get('entity_name', 'Unknown') if metadata else 'Unknown'
            print(f"  {i+1}. {entity_name}: {float(similarity):.4f}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_actual_threshold()