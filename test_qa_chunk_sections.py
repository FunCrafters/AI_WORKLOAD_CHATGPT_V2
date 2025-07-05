#!/usr/bin/env python3
"""
Test chunk_section values in rag_qa_vectors
"""

import psycopg2

# Direct PostgreSQL connection
POSTGRES_CONFIG = {
    'host': 'localhost',
    'user': 'tools', 
    'password': 'STAGING-kumquat-talon-succor-hum',
    'database': 'llm_tools',
    'port': 5432
}

def test_qa_chunk_sections():
    """Test what chunk_section values exist in rag_qa_vectors"""
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Get unique chunk_section values
        cursor.execute("""
            SELECT DISTINCT metadata->>'chunk_section' as chunk_section, COUNT(*) 
            FROM rag_qa_vectors 
            GROUP BY metadata->>'chunk_section'
            ORDER BY COUNT(*) DESC
        """)
        
        sections = cursor.fetchall()
        print("=== Unique chunk_section values in rag_qa_vectors ===")
        for section, count in sections:
            print(f"- {section}: {count} records")
        
        # Test for LOCATIONS QA
        cursor.execute("""
            SELECT chunk_text, metadata
            FROM rag_qa_vectors 
            WHERE metadata->>'entity_name' LIKE '%Rishi%'
            LIMIT 3
        """)
        
        rishi_qa = cursor.fetchall()
        print(f"\n=== Rishi-related QA records: {len(rishi_qa)} ===")
        for i, (chunk_text, metadata) in enumerate(rishi_qa):
            print(f"\nRecord {i+1}:")
            print(f"  chunk_text: {chunk_text[:100]}...")
            print(f"  metadata: {metadata}")
        
        # Test for MECHANICS QA  
        cursor.execute("""
            SELECT chunk_text, metadata
            FROM rag_qa_vectors 
            WHERE metadata->>'entity_name' LIKE '%Champion%'
            OR metadata->>'entity_name' LIKE '%Mechanic%'
            OR metadata->>'entity_name' LIKE '%Combat%'
            LIMIT 3
        """)
        
        mechanics_qa = cursor.fetchall()
        print(f"\n=== Mechanics-related QA records: {len(mechanics_qa)} ===")
        for i, (chunk_text, metadata) in enumerate(mechanics_qa):
            print(f"\nRecord {i+1}:")
            print(f"  chunk_text: {chunk_text[:100]}...")
            print(f"  metadata: {metadata}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qa_chunk_sections()