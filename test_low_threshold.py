#!/usr/bin/env python3
"""
Test RAG with lower threshold to see actual similarity scores
"""

import json
import logging
import psycopg2
from typing import List
from workload_embedding import get_vectorstore

# Configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'user': 'tools', 
    'password': 'STAGING-kumquat-talon-succor-hum',
    'database': 'llm_tools',
    'port': 5432
}

# Very low threshold to see all results
LOW_THRESHOLD = 0.0
LIMIT = 20

# Logger
logger = logging.getLogger("Low Threshold Test")

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

def test_similarity_with_low_threshold(query: str):
    """Test similarity with very low threshold to see actual scores"""
    
    print(f"Testing similarity for query: '{query}'")
    
    # Generate embedding
    query_embedding = _generate_query_embedding(query)
    if not query_embedding:
        print("❌ Failed to generate embedding")
        return
    
    print(f"✅ Generated embedding with {len(query_embedding)} dimensions")
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Search with very low threshold
        similarity_query = """
            SELECT id, chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            ORDER BY similarity DESC
            LIMIT %s
        """
        
        cursor.execute(similarity_query, (query_embedding, LIMIT))
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"\n=== SIMILARITY RESULTS ===")
        print(f"Found {len(rows)} results (ordered by similarity)")
        print(f"Query: '{query}'")
        print(f"Normal threshold: 0.4")
        print(f"Test threshold: {LOW_THRESHOLD}")
        
        for i, (record_id, chunk_text, metadata, similarity) in enumerate(rows):
            similarity_float = float(similarity)
            entity_name = metadata.get('entity_name', 'Unknown') if metadata else 'Unknown'
            
            status = "✅ ABOVE" if similarity_float >= 0.4 else "❌ BELOW"
            
            print(f"\n--- RANK {i+1} ---")
            print(f"Record ID: {record_id}")
            print(f"Entity: {entity_name}")
            print(f"Similarity: {similarity_float:.6f} {status} threshold (0.4)")
            print(f"Preview: {chunk_text[:100]}...")
            
            # Check if this contains "Rishi"
            if "rishi" in chunk_text.lower():
                print(f"🎯 CONTAINS 'RISHI' - but similarity is {similarity_float:.6f}")
        
        # Summary
        above_threshold = [r for r in rows if float(r[3]) >= 0.4]
        below_threshold = [r for r in rows if float(r[3]) < 0.4]
        
        print(f"\n=== SUMMARY ===")
        print(f"Results above threshold (0.4): {len(above_threshold)}")
        print(f"Results below threshold: {len(below_threshold)}")
        
        if above_threshold:
            best = above_threshold[0]
            print(f"Best above threshold: {float(best[3]):.6f}")
        else:
            if rows:
                best = rows[0]
                print(f"Best overall: {float(best[3]):.6f} (still below threshold!)")
                print("❌ PROBLEM: Even the best match is below threshold!")
                print("Possible causes:")
                print("1. Embedding model mismatch")
                print("2. Threshold too high")
                print("3. Text preprocessing differences")
                print("4. Different embedding dimensions")
        
        # Check specifically for Rishi content
        rishi_matches = [(r[0], r[1], r[2], float(r[3])) for r in rows if "rishi" in r[1].lower()]
        if rishi_matches:
            print(f"\n=== RISHI CONTENT ANALYSIS ===")
            for record_id, chunk_text, metadata, similarity in rishi_matches:
                entity_name = metadata.get('entity_name', 'Unknown') if metadata else 'Unknown'
                print(f"Record {record_id} ({entity_name}): {similarity:.6f}")
                print(f"  Preview: {chunk_text[:150]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    
    # Initialize embeddings first
    print("Initializing embeddings...")
    
    from dotenv import load_dotenv, dotenv_values
    load_dotenv()
    config = dotenv_values(".env")
    
    from workload_embedding import initialize_embeddings_and_vectorstore
    
    try:
        initialize_embeddings_and_vectorstore(config, "localhost", "11434")
        print("✅ Embeddings initialized")
    except Exception as e:
        print(f"❌ Failed to initialize embeddings: {e}")
        return
    
    # Test different queries
    queries = ["Rishi Moon", "Rishi", "moon", "station"]
    
    for query in queries:
        print(f"\n{'='*60}")
        test_similarity_with_low_threshold(query)

if __name__ == "__main__":
    main()