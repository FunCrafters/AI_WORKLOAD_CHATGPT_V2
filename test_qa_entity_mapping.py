#!/usr/bin/env python3
"""
Test entity_name mapping between rag_vectors and rag_qa_vectors
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

def test_entity_mapping():
    """Test how entity_name maps between main and QA tables"""
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Get sample entity_names from LOCATIONS in main table
        print("=== LOCATIONS entities in rag_vectors ===")
        cursor.execute("""
            SELECT DISTINCT metadata->>'entity_name' as entity_name
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            ORDER BY entity_name
            LIMIT 5
        """)
        
        location_entities = cursor.fetchall()
        for (entity_name,) in location_entities:
            print(f"- {entity_name}")
        
        # Check if these entities exist in QA table
        print("\n=== Corresponding QA entities for LOCATIONS ===")
        for (entity_name,) in location_entities:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM rag_qa_vectors 
                WHERE metadata->>'entity_name' = %s
            """, (entity_name,))
            
            qa_count = cursor.fetchone()[0]
            print(f"- {entity_name}: {qa_count} QA records")
        
        # Get sample entity_names from MECHANICS in main table
        print("\n=== MECHANICS entities in rag_vectors ===")
        cursor.execute("""
            SELECT DISTINCT metadata->>'entity_name' as entity_name
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'MECHANICS'
            ORDER BY entity_name
            LIMIT 5
        """)
        
        mechanic_entities = cursor.fetchall()
        for (entity_name,) in mechanic_entities:
            print(f"- {entity_name}")
        
        # Check if these entities exist in QA table
        print("\n=== Corresponding QA entities for MECHANICS ===")
        for (entity_name,) in mechanic_entities:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM rag_qa_vectors 
                WHERE metadata->>'entity_name' = %s
            """, (entity_name,))
            
            qa_count = cursor.fetchone()[0]
            print(f"- {entity_name}: {qa_count} QA records")
        
        # Alternative approach: check if we can use a different mapping strategy
        print("\n=== QA entity_name samples ===")
        cursor.execute("""
            SELECT DISTINCT metadata->>'entity_name' as entity_name, COUNT(*)
            FROM rag_qa_vectors 
            GROUP BY metadata->>'entity_name'
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        qa_entities = cursor.fetchall()
        for entity_name, count in qa_entities:
            print(f"- {entity_name}: {count} QA records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_entity_mapping()