#!/usr/bin/env python3
"""
Simple SQL debug to understand the issue
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

def test_basic_sql():
    """Test basic SQL without embeddings first"""
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Test 1: Basic count
        print("=== Test 1: Basic count ===")
        cursor.execute("SELECT COUNT(*) FROM rag_vectors WHERE metadata->>'chunk_section' = 'LOCATIONS'")
        count = cursor.fetchone()[0]
        print(f"Total LOCATIONS records: {count}")
        
        # Test 2: Basic query without embedding
        print("\n=== Test 2: Basic select ===")
        cursor.execute("""
            SELECT id, chunk_text, metadata 
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            AND NOT (metadata->>'chunk_name' LIKE '%QA%')
            LIMIT 3
        """)
        rows = cursor.fetchall()
        print(f"Found {len(rows)} rows")
        for i, row in enumerate(rows):
            print(f"Row {i}: {len(row)} columns - {[type(col) for col in row]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        import traceback
        traceback.print_exc()

def test_embedding_sql():
    """Test with embedding after basic works"""
    
    print("\n=== Initializing embeddings ===")
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
        
        # Test 3: With embedding
        print("\n=== Test 3: With embedding ===")
        test_query = """
            SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            AND NOT (metadata->>'chunk_name' LIKE '%%QA%%')
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        print("Query parameters:")
        print(f"- embedding: {len(query_embedding)} floats")
        print(f"- threshold: 0.4")
        print(f"- limit: 10")
        
        # Count placeholders
        placeholder_count = test_query.count('%s')
        print(f"- placeholders in query: {placeholder_count}")
        
        params = (query_embedding, query_embedding, 0.4, query_embedding, 10)
        print(f"- parameters provided: {len(params)}")
        
        cursor.execute(test_query, params)
        rows = cursor.fetchall()
        print(f"✅ Query executed successfully, found {len(rows)} rows")
        
        if rows:
            first_row = rows[0]
            print(f"First row: {len(first_row)} columns")
            print(f"Column types: {[type(col) for col in first_row]}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Embedding SQL Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_sql()
    test_embedding_sql()