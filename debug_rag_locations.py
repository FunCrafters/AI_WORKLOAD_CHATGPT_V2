#!/usr/bin/env python3
"""
Debug script for RAG LOCATIONS
Analyze why "Rishi Moon" doesn't find similarity matches in rag_vectors
"""

import json
import psycopg2
import logging
from typing import List, Dict, Any
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
TEST_QUERY = "Rishi Moon"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG Debug")

def generate_test_embedding(query: str) -> List[float]:
    """Generate embedding for test query using Ollama"""
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            logger.error("Failed to get vectorstore")
            return None
        
        embedding = vectorstore._embedding_function.embed_query(query)
        logger.info(f"Generated embedding for '{query}': {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None

def get_all_locations_data():
    """Get all records from rag_vectors with chunk_section=LOCATIONS"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Get all LOCATIONS records
        query = """
            SELECT id, chunk_text, metadata
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            ORDER BY id
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Found {len(rows)} LOCATIONS records")
        return rows
        
    except Exception as e:
        logger.error(f"Error fetching LOCATIONS data: {str(e)}")
        return []

def test_similarity_with_query(query_embedding: List[float]):
    """Test similarity of query embedding with all LOCATIONS records"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Test similarity with all LOCATIONS records
        similarity_query = """
            SELECT id, chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            ORDER BY similarity DESC
            LIMIT 20
        """
        
        cursor.execute(similarity_query, (query_embedding,))
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Found {len(rows)} similarity results")
        return rows
        
    except Exception as e:
        logger.error(f"Error testing similarity: {str(e)}")
        return []

def analyze_locations_content(locations_data, output_file="locations_debug.txt"):
    """Analyze and save all LOCATIONS content to file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"=== RAG LOCATIONS DEBUG ANALYSIS ===\n")
            f.write(f"Total records: {len(locations_data)}\n")
            f.write(f"Test query: '{TEST_QUERY}'\n")
            f.write(f"Similarity threshold: {SIMILARITY_THRESHOLD}\n\n")
            
            # Search for Rishi Moon mentions
            rishi_mentions = []
            
            for i, (record_id, chunk_text, metadata) in enumerate(locations_data):
                f.write(f"=== RECORD {i+1} (ID: {record_id}) ===\n")
                f.write(f"METADATA: {json.dumps(metadata, indent=2)}\n")
                f.write(f"CHUNK_TEXT ({len(chunk_text)} chars):\n")
                f.write(f"{chunk_text}\n")
                
                # Check for Rishi Moon mentions
                if "rishi" in chunk_text.lower() or "rishi moon" in chunk_text.lower():
                    rishi_mentions.append({
                        'record_id': record_id,
                        'chunk_text': chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                        'metadata': metadata
                    })
                    f.write(f"*** CONTAINS RISHI MENTION ***\n")
                
                f.write(f"\n{'-'*80}\n\n")
            
            # Summary of Rishi mentions
            f.write(f"\n=== RISHI MOON MENTIONS SUMMARY ===\n")
            f.write(f"Found {len(rishi_mentions)} records mentioning 'Rishi'\n\n")
            
            for mention in rishi_mentions:
                f.write(f"Record ID: {mention['record_id']}\n")
                f.write(f"Preview: {mention['chunk_text']}\n")
                f.write(f"Metadata: {json.dumps(mention['metadata'])}\n\n")
        
        logger.info(f"Locations analysis saved to {output_file}")
        return rishi_mentions
        
    except Exception as e:
        logger.error(f"Error analyzing locations content: {str(e)}")
        return []

def analyze_similarity_results(similarity_results, output_file="similarity_test.txt"):
    """Analyze similarity test results"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"=== SIMILARITY TEST RESULTS FOR '{TEST_QUERY}' ===\n")
            f.write(f"Threshold: {SIMILARITY_THRESHOLD}\n")
            f.write(f"Total results: {len(similarity_results)}\n\n")
            
            above_threshold = []
            below_threshold = []
            
            for i, (record_id, chunk_text, metadata, similarity) in enumerate(similarity_results):
                result_info = {
                    'rank': i + 1,
                    'record_id': record_id,
                    'similarity': float(similarity),
                    'chunk_preview': chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                    'metadata': metadata
                }
                
                if similarity >= SIMILARITY_THRESHOLD:
                    above_threshold.append(result_info)
                else:
                    below_threshold.append(result_info)
                
                f.write(f"RANK {i+1}: Similarity = {similarity:.4f} {'✓' if similarity >= SIMILARITY_THRESHOLD else '✗'}\n")
                f.write(f"Record ID: {record_id}\n")
                f.write(f"Preview: {result_info['chunk_preview']}\n")
                f.write(f"Metadata: {json.dumps(metadata)}\n")
                f.write(f"\n{'-'*60}\n\n")
            
            # Summary
            f.write(f"\n=== SUMMARY ===\n")
            f.write(f"Results above threshold ({SIMILARITY_THRESHOLD}): {len(above_threshold)}\n")
            f.write(f"Results below threshold: {len(below_threshold)}\n")
            
            if above_threshold:
                f.write(f"\nBest match: {above_threshold[0]['similarity']:.4f} (Record {above_threshold[0]['record_id']})\n")
            else:
                f.write(f"\nNo results above threshold! Best match: {similarity_results[0][3]:.4f}\n")
        
        logger.info(f"Similarity analysis saved to {output_file}")
        return above_threshold, below_threshold
        
    except Exception as e:
        logger.error(f"Error analyzing similarity results: {str(e)}")
        return [], []

def main():
    """Main diagnostic function"""
    print(f"Starting RAG LOCATIONS diagnostic for query: '{TEST_QUERY}'")
    
    # Step 1: Generate test embedding
    print("Step 1: Generating test embedding...")
    query_embedding = generate_test_embedding(TEST_QUERY)
    if not query_embedding:
        print("Failed to generate embedding. Exiting.")
        return
    
    # Step 2: Get all LOCATIONS data
    print("Step 2: Fetching all LOCATIONS data...")
    locations_data = get_all_locations_data()
    if not locations_data:
        print("No LOCATIONS data found. Exiting.")
        return
    
    # Step 3: Analyze content and save to file
    print("Step 3: Analyzing LOCATIONS content...")
    rishi_mentions = analyze_locations_content(locations_data)
    
    # Step 4: Test similarity
    print("Step 4: Testing similarity...")
    similarity_results = test_similarity_with_query(query_embedding)
    
    # Step 5: Analyze similarity results
    print("Step 5: Analyzing similarity results...")
    above_threshold, below_threshold = analyze_similarity_results(similarity_results)
    
    # Step 6: Print summary
    print(f"\n=== DIAGNOSTIC SUMMARY ===")
    print(f"Total LOCATIONS records: {len(locations_data)}")
    print(f"Records mentioning 'Rishi': {len(rishi_mentions)}")
    print(f"Similarity results above threshold: {len(above_threshold)}")
    print(f"Similarity results below threshold: {len(below_threshold)}")
    
    if similarity_results:
        best_similarity = similarity_results[0][3]
        print(f"Best similarity score: {best_similarity:.4f}")
        
        if best_similarity < SIMILARITY_THRESHOLD:
            print(f"❌ Problem: Best match ({best_similarity:.4f}) is below threshold ({SIMILARITY_THRESHOLD})")
            print("Possible issues:")
            print("- Embedding model mismatch")
            print("- Threshold too high") 
            print("- Query vs content mismatch")
        else:
            print(f"✅ Found matches above threshold")
    
    print(f"\nOutput files created:")
    print(f"- locations_debug.txt (all LOCATIONS data)")
    print(f"- similarity_test.txt (similarity test results)")

if __name__ == "__main__":
    main()