#!/usr/bin/env python3
"""
Test mechanic RAG function
"""

import sys
import os
from dotenv import load_dotenv, dotenv_values

# Load environment variables
load_dotenv()
config = dotenv_values(".env")

# Add workload directory to path
sys.path.append('/root/dev/Workload_ChatGPT')

# Initialize the embeddings system like in workload_main.py
from workload_embedding import initialize_embeddings_and_vectorstore

def test_rag_mechanics():
    """Test db_rag_get_mechanic_details function"""
    
    # Initialize embeddings first
    print("Initializing embeddings...")
    
    # Use default Ollama settings from .env
    ollama_host = "localhost"  
    ollama_port = "11434"      
    
    try:
        initialize_embeddings_and_vectorstore(config, ollama_host, ollama_port)
        print("✅ Embeddings initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize embeddings: {e}")
        return
    
    # Now test the RAG function
    print("\nTesting db_rag_get_mechanic_details...")
    
    try:
        from tools.db_rag_get_mechanic_details import db_rag_get_mechanic_details
        
        # Test with mechanics-related queries
        test_queries = [
            "combat mechanics",
            "abilities",
            "stats",
            "how does combat work"
        ]
        
        for query in test_queries:
            print(f"\n=== Testing: '{query}' ===")
            result = db_rag_get_mechanic_details(query)
            print(f"Result for '{query}':")
            print(result)
            print("\n" + "="*50)
        
    except Exception as e:
        print(f"❌ Error testing RAG function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_mechanics()