#!/usr/bin/env python3
"""
Test structure of rag_qa_vectors table
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

def test_qa_vectors_structure():
    """Test the structure of rag_qa_vectors table"""
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Check if table exists and get structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'rag_qa_vectors'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("=== rag_qa_vectors table structure ===")
        for col_name, col_type in columns:
            print(f"- {col_name}: {col_type}")
        
        # Get sample data
        cursor.execute("""
            SELECT * FROM rag_qa_vectors LIMIT 3
        """)
        
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        
        print(f"\n=== Sample data (columns: {column_names}) ===")
        for i, row in enumerate(rows):
            print(f"\nRecord {i+1}:")
            for j, col_name in enumerate(column_names):
                if col_name == 'embedding':
                    print(f"  {col_name}: [vector with {len(row[j]) if row[j] else 0} dimensions]")
                elif col_name == 'metadata' and row[j]:
                    print(f"  {col_name}: {row[j]}")
                else:
                    print(f"  {col_name}: {row[j]}")
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM rag_qa_vectors")
        count = cursor.fetchone()[0]
        print(f"\n=== Total records in rag_qa_vectors: {count} ===")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qa_vectors_structure()