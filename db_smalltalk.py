#!/usr/bin/env python3
"""
Smalltalk Database Handler
Manages smalltalk topics and knowledge from SQLite database
"""

import os
import logging
import sqlite3
import random
from typing import Dict, List, Tuple

# Logger
logger = logging.getLogger("Workload Smalltalk DB")

# Global cache variables
SMALLTALK_TOPICS = []
SMALLTALK_KNOWLEDGE = {}


def initialize_smalltalk_db():
    """Initialize smalltalk topics from database"""
    global SMALLTALK_TOPICS, SMALLTALK_KNOWLEDGE
    
    try:
        # Get database path from environment
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "smalltalk.db.sqlite")
        
        logger.info(f"Initializing smalltalk cache from: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all topics and knowledge
        cursor.execute("SELECT topic, knowledge FROM smalltalk_records")
        rows = cursor.fetchall()
        
        # Clear existing data
        SMALLTALK_TOPICS = []
        SMALLTALK_KNOWLEDGE = {}
        
        # Load data into memory
        for topic, knowledge in rows:
            SMALLTALK_TOPICS.append(topic)
            SMALLTALK_KNOWLEDGE[topic] = knowledge
        
        conn.close()
        
        logger.info(f"Smalltalk cache initialized: {len(SMALLTALK_TOPICS)} topics loaded")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing smalltalk cache: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Fall back to empty cache
        SMALLTALK_TOPICS = []
        SMALLTALK_KNOWLEDGE = {}
        return False


def get_random_smalltalk_topic_and_knowledge(topic_type: str = "general") -> Tuple[str, str]:
    """
    Get a random smalltalk topic and its knowledge from cache
    
    Args:
        topic_type (str): Type of topic to get (e.g. "general", "champions", "battles", etc.)
    
    Returns:
        Tuple[str, str]: (topic, knowledge)
    """
    # Make sure cache is initialized
    if not SMALLTALK_TOPICS and not SMALLTALK_KNOWLEDGE:
        initialize_smalltalk_db()
    
    if not SMALLTALK_TOPICS:
        # Return fallback if no topics available
        return ("General Star Wars Trivia", 
                "The Star Wars galaxy contains many interesting facts and stories. "
                "From the heroic Jedi to the fearsome Sith, there's always something to discuss.")
    
    try:
        # Connect to database to get filtered topics
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "smalltalk.db.sqlite")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get topics filtered by category
        if topic_type != "general":
            cursor.execute("SELECT topic, knowledge FROM smalltalk_records WHERE category = ?", (topic_type,))
        else:
            cursor.execute("SELECT topic, knowledge FROM smalltalk_records")
            
        rows = cursor.fetchall()
        
        if not rows:
            # If no topics found for specific type, fall back to general
            cursor.execute("SELECT topic, knowledge FROM smalltalk_records")
            rows = cursor.fetchall()
        
        conn.close()
        
        # Select a random topic from filtered results
        topic, knowledge = random.choice(rows)
        return (topic, knowledge)
        
    except Exception as e:
        logger.error(f"Error getting filtered smalltalk topic: {str(e)}")
        # Fall back to random selection from cache
        topic = random.choice(SMALLTALK_TOPICS)
        knowledge = SMALLTALK_KNOWLEDGE.get(topic, "No specific knowledge available for this topic.")
        return (topic, knowledge)


def get_smalltalk_database_info() -> List[str]:
    """
    Get comprehensive information about the smalltalk database
    
    Returns:
        List of strings containing database information
    """
    info_log = []
    info_log.append("\n--- SMALLTALK DATABASE (smalltalk.db.sqlite) ---")
    
    try:
        # Get database path
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "smalltalk.db.sqlite")
        
        # Get file size
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            file_size_mb = file_size / (1024 * 1024)
            info_log.append(f"Database file size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        else:
            info_log.append("❌ Database file not found!")
            return info_log
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total number of topics
        cursor.execute("SELECT COUNT(*) FROM smalltalk_records")
        total_topics = cursor.fetchone()[0]
        info_log.append(f"Total smalltalk topics: {total_topics}")
        
        # Get total knowledge size
        cursor.execute("SELECT SUM(LENGTH(knowledge)) FROM smalltalk_records")
        total_knowledge_size = cursor.fetchone()[0] or 0
        info_log.append(f"Total knowledge text size: {total_knowledge_size:,} characters")
        
        # Get average knowledge length
        if total_topics > 0:
            avg_knowledge_length = total_knowledge_size // total_topics
            info_log.append(f"Average knowledge per topic: {avg_knowledge_length:,} characters")
        
        # Get sample topics
        cursor.execute("SELECT topic FROM smalltalk_records ORDER BY RANDOM() LIMIT 10")
        sample_topics = cursor.fetchall()
        
        info_log.append("\n🎯 Sample smalltalk topics:")
        for topic in sample_topics:
            info_log.append(f"  • {topic[0]}")
        
        # Get topics by category
        info_log.append("\n📊 Topic categories:")
        cursor.execute("SELECT category, COUNT(*) as count FROM smalltalk_records GROUP BY category ORDER BY count DESC")
        sections = cursor.fetchall()
        
        for section, count in sections:
            percentage = (count / total_topics) * 100
            info_log.append(f"  {section}: {count} topics ({percentage:.1f}%)")
        
        # Cache status
        info_log.append("\n⚡ Cache status:")
        if SMALLTALK_TOPICS:
            info_log.append(f"  ✓ Cache loaded with {len(SMALLTALK_TOPICS)} topics")
            cache_size = sum(len(k) for k in SMALLTALK_KNOWLEDGE.values())
            info_log.append(f"  ✓ Cache memory usage: ~{cache_size:,} characters")
        else:
            info_log.append("  ❌ Cache not loaded")
        
        conn.close()
        
    except Exception as e:
        info_log.append(f"⚠️  Error getting smalltalk database info: {str(e)}")
        logger.error(f"Error getting smalltalk database info: {str(e)}")
    
    info_log.append("--- SMALLTALK DATABASE INFO END ---\n")
    return info_log