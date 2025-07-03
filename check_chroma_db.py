#!/usr/bin/env python3
"""
Check ChromaDB database structure and content
"""

import os
from chromadb import PersistentClient

def check_database():
    """Check the ChromaDB database structure"""
    print("Checking ChromaDB database structure...")
    
    db_path = "/mnt/raid/dev/WorkloadData/DB_V1"
    
    try:
        client = PersistentClient(path=db_path)
        
        # List all collections (returns collection names in v0.6.0)
        collection_names = client.list_collections()
        print(f"Found {len(collection_names)} collections:")
        
        for collection_name in collection_names:
            print(f"\nCollection: {collection_name}")
            
            # Get the actual collection object
            try:
                collection = client.get_collection(collection_name)
                print(f"  - Count: {collection.count()}")
                
                if collection.count() > 0:
                    # Get a sample of documents
                    sample = collection.get(limit=3, include=["metadatas", "documents"])
                    print(f"  - Sample IDs: {sample['ids']}")
                    
                    # Check different sections
                    all_docs = collection.get(include=["metadatas"])
                    sections = set()
                    categories = set()
                    for metadata in all_docs['metadatas']:
                        if 'section' in metadata:
                            sections.add(metadata['section'])
                        if 'category' in metadata:
                            categories.add(metadata['category'])
                    
                    print(f"  - Available sections: {sorted(sections)}")
                    print(f"  - Available categories: {sorted(categories)}")
                    
                    # Look for Q&A documents specifically
                    qa_sample = collection.get(
                        where={"section": {"$eq": "Q&A"}},
                        limit=3,
                        include=["metadatas", "documents"]
                    )
                    
                    if sample['metadatas']:
                        print("  - Sample metadata:")
                        for i, metadata in enumerate(sample['metadatas']):
                            print(f"    Document {i+1}: {metadata}")
                    
                    if qa_sample['documents']:
                        print("  - Q&A documents found:")
                        for i, doc in enumerate(qa_sample['documents']):
                            print(f"    Q&A {i+1}: {doc[:200]}...")
                            if i < len(qa_sample['metadatas']):
                                print(f"    Q&A {i+1} metadata: {qa_sample['metadatas'][i]}")
                    
                    if sample['documents']:
                        print("  - Sample regular documents (first 100 chars):")
                        for i, doc in enumerate(sample['documents']):
                            print(f"    Document {i+1}: {doc[:100]}...")
                else:
                    print("  - Collection is empty")
                    
            except Exception as e:
                print(f"  - Error accessing collection {collection_name}: {str(e)}")
        
        if len(collection_names) == 0:
            print("No collections found in database!")
            
    except Exception as e:
        print(f"Error checking database: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()
