#!/usr/bin/env python3
"""
Test execute_query to see what it actually returns
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Test execute_query
from db_postgres import execute_query

def test_execute_query():
    """Test what execute_query actually returns"""
    
    try:
        # Simple test query  
        result = execute_query("""
            SELECT chunk_text, metadata
            FROM rag_vectors 
            WHERE metadata->>'chunk_section' = 'LOCATIONS'
            LIMIT 1
        """)
        
        print(f"execute_query result type: {type(result)}")
        if result:
            print(f"First record type: {type(result[0])}")
            print(f"First record keys: {list(result[0].keys()) if hasattr(result[0], 'keys') else 'No keys method'}")
            print(f"First record: {result[0]}")
            
            # Test accessing fields
            first_record = result[0]
            if hasattr(first_record, 'keys'):
                print("\n=== Testing field access ===")
                try:
                    chunk_text = first_record['chunk_text']
                    print(f"✅ first_record['chunk_text'] works: {type(chunk_text)}")
                except Exception as e:
                    print(f"❌ first_record['chunk_text'] failed: {e}")
                
                try:
                    metadata = first_record['metadata']  
                    print(f"✅ first_record['metadata'] works: {type(metadata)}")
                except Exception as e:
                    print(f"❌ first_record['metadata'] failed: {e}")
        else:
            print("❌ No results returned")
            
    except Exception as e:
        print(f"❌ execute_query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_execute_query()