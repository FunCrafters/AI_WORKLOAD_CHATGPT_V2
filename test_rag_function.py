#!/usr/bin/env python3
"""
Test RAG function directly
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

def test_rag_locations():
    """Test db_rag_get_locations function"""
    
    # Initialize embeddings first
    print("Initializing embeddings...")
    
    # Use default Ollama settings from .env
    ollama_host = "localhost"  # Default since OLLAMA_HOST is commented out in .env
    ollama_port = "11434"      # Default since OLLAMA_PORT is commented out in .env
    
    try:
        initialize_embeddings_and_vectorstore(config, ollama_host, ollama_port)
        print("✅ Embeddings initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize embeddings: {e}")
        return
    
    # Now test the RAG function
    print("\nTesting db_rag_get_locations...")
    
    try:
        from tools.db_rag_get_location_details import db_rag_get_location_details
        
        # Test with "Rishi Moon"
        result = db_rag_get_location_details("Rishi Moon")
        print(f"Result for 'Rishi Moon':")
        print(result)
        print("\n" + "="*50 + "\n")
        
        # Test with "Rishi"
        result2 = db_rag_get_location_details("Rishi")
        print(f"Result for 'Rishi':")
        print(result2)
        
    except Exception as e:
        print(f"❌ Error testing RAG function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_locations()