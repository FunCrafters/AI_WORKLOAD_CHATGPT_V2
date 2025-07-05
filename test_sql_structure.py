#!/usr/bin/env python3
"""
Test SQL structure to see actual column names
"""

import psycopg2
from dotenv import load_dotenv, dotenv_values

# Load environment
load_dotenv()
config = dotenv_values(".env")

# Direct PostgreSQL connection (like original code)
POSTGRES_CONFIG = {
    'host': 'localhost',
    'user': 'tools', 
    'password': 'STAGING-kumquat-talon-succor-hum',
    'database': 'llm_tools',
    'port': 5432
}

def test_sql_structure():
    """Test actual SQL query structure"""
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Test the exact query from our function
        cursor.execute("""
            SELECT chunk_text, metadata, 1 - (embedding <=> embedding) as similarity
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            LIMIT 1
        """)
        
        # Get column names
        column_names = [desc[0] for desc in cursor.description]
        print("Nazwy kolumn z SQL query:", column_names)
        
        rows = cursor.fetchall()
        if rows:
            row = rows[0]
            print(f"Przykładowy rekord (tuple): {type(row)} -> {len(row)} elementów")
            print(f"Element 0 (chunk_text): {type(row[0])}")
            print(f"Element 1 (metadata): {type(row[1])}")
            if len(row) > 2:
                print(f"Element 2 (similarity): {type(row[2])}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Błąd: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sql_structure()