#!/usr/bin/env python3
"""
Simple debug script for RAG LOCATIONS
Check data presence without embeddings
"""

import json
import psycopg2
import logging

# Configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'user': 'tools', 
    'password': 'STAGING-kumquat-talon-succor-hum',
    'database': 'llm_tools',
    'port': 5432
}

TEST_QUERY = "Rishi Moon"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG Simple Debug")

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

def search_for_text(locations_data, search_term):
    """Search for specific text in locations data"""
    matches = []
    search_lower = search_term.lower()
    
    for record_id, chunk_text, metadata in locations_data:
        if search_lower in chunk_text.lower():
            matches.append({
                'record_id': record_id,
                'chunk_text': chunk_text,
                'metadata': metadata,
                'preview': chunk_text[:300] + "..." if len(chunk_text) > 300 else chunk_text
            })
    
    return matches

def analyze_metadata_structure(locations_data):
    """Analyze metadata structure"""
    metadata_keys = set()
    chunk_sections = set()
    
    for record_id, chunk_text, metadata in locations_data:
        if metadata:
            metadata_keys.update(metadata.keys())
            if 'chunk_section' in metadata:
                chunk_sections.add(metadata['chunk_section'])
    
    return metadata_keys, chunk_sections

def main():
    """Main diagnostic function"""
    print(f"Starting simple RAG LOCATIONS diagnostic for: '{TEST_QUERY}'")
    
    # Step 1: Get all LOCATIONS data
    print("Step 1: Fetching all LOCATIONS data...")
    locations_data = get_all_locations_data()
    if not locations_data:
        print("❌ No LOCATIONS data found!")
        return
    
    print(f"✅ Found {len(locations_data)} LOCATIONS records")
    
    # Step 2: Analyze metadata structure
    print("\nStep 2: Analyzing metadata structure...")
    metadata_keys, chunk_sections = analyze_metadata_structure(locations_data)
    print(f"Metadata keys found: {sorted(metadata_keys)}")
    print(f"Chunk sections found: {sorted(chunk_sections)}")
    
    # Step 3: Search for "Rishi Moon" in text
    print(f"\nStep 3: Searching for '{TEST_QUERY}' in text...")
    rishi_matches = search_for_text(locations_data, TEST_QUERY)
    
    if rishi_matches:
        print(f"✅ Found {len(rishi_matches)} records containing '{TEST_QUERY}':")
        for i, match in enumerate(rishi_matches):
            print(f"\n--- MATCH {i+1} ---")
            print(f"Record ID: {match['record_id']}")
            print(f"Metadata: {json.dumps(match['metadata'], indent=2)}")
            print(f"Preview: {match['preview']}")
    else:
        print(f"❌ No records found containing '{TEST_QUERY}'")
        
        # Try variations
        variations = ["rishi", "moon", "rishi-moon"]
        for variation in variations:
            var_matches = search_for_text(locations_data, variation)
            if var_matches:
                print(f"✅ Found {len(var_matches)} records containing '{variation}':")
                for match in var_matches[:3]:  # Show first 3
                    print(f"  Record {match['record_id']}: {match['preview'][:100]}...")
    
    # Step 4: Export all locations to file for manual inspection
    print(f"\nStep 4: Exporting all LOCATIONS data to file...")
    output_file = "all_locations_export.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"=== ALL LOCATIONS DATA EXPORT ===\n")
            f.write(f"Total records: {len(locations_data)}\n")
            f.write(f"Search term: '{TEST_QUERY}'\n\n")
            
            for i, (record_id, chunk_text, metadata) in enumerate(locations_data):
                f.write(f"=== RECORD {i+1} (ID: {record_id}) ===\n")
                f.write(f"METADATA: {json.dumps(metadata, indent=2)}\n")
                f.write(f"CHUNK_TEXT ({len(chunk_text)} chars):\n")
                f.write(f"{chunk_text}\n")
                f.write(f"\n{'-'*80}\n\n")
        
        print(f"✅ Data exported to {output_file}")
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
    
    # Step 5: Check a few sample records for content quality
    print(f"\nStep 5: Sample content analysis...")
    if locations_data:
        sample_size = min(3, len(locations_data))
        print(f"Showing first {sample_size} records:")
        
        for i in range(sample_size):
            record_id, chunk_text, metadata = locations_data[i]
            print(f"\n--- SAMPLE {i+1} ---")
            print(f"Record ID: {record_id}")
            print(f"Text length: {len(chunk_text)} chars")
            print(f"Metadata: {json.dumps(metadata)}")
            print(f"Text preview: {chunk_text[:200]}...")

if __name__ == "__main__":
    main()