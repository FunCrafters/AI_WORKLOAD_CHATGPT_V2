#!/usr/bin/env python3
"""
Lore Database Handler
Manages champion lore data from SQLite database
"""

import os
import logging
import sqlite3
from typing import Dict, List, Optional

# Logger
logger = logging.getLogger("Workload Lore DB")


def get_lore_database_info() -> List[str]:
    """
    Get comprehensive information about the lore database
    
    Returns:
        List of strings containing database information
    """
    info_log = []
    info_log.append("\n--- LORE DATABASE (lore.db.sqlite) ---")
    
    try:
        # Get database path
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "lore.db.sqlite")
        
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
        
        # Get total number of champions
        cursor.execute("SELECT COUNT(*) FROM lore_records")
        total_champions = cursor.fetchone()[0]
        info_log.append(f"Total champion lore records: {total_champions}")
        
        # Get total lore text size
        cursor.execute("SELECT SUM(LENGTH(lore_text)) FROM lore_records WHERE lore_text IS NOT NULL")
        total_lore_size = cursor.fetchone()[0] or 0
        info_log.append(f"Total lore text size: {total_lore_size:,} characters")
        
        # Get average lore length
        if total_champions > 0:
            avg_lore_length = total_lore_size // total_champions
            info_log.append(f"Average lore per champion: {avg_lore_length:,} characters")
        
        # Get sample champions
        cursor.execute("SELECT champion_name FROM lore_records ORDER BY RANDOM() LIMIT 10")
        sample_champions = cursor.fetchall()
        
        info_log.append("\n🎯 Sample champions with lore:")
        for champion in sample_champions:
            info_log.append(f"  • {champion[0]}")
        
        # Get champions with longest lore
        cursor.execute("""
            SELECT champion_name, LENGTH(lore_text) as lore_length 
            FROM lore_records 
            WHERE lore_text IS NOT NULL 
            ORDER BY lore_length DESC 
            LIMIT 5
        """)
        longest_lore = cursor.fetchall()
        
        info_log.append("\n📚 Champions with most detailed lore:")
        for champion, length in longest_lore:
            info_log.append(f"  • {champion}: {length:,} characters")
        
        # Get champions without lore
        cursor.execute("SELECT COUNT(*) FROM lore_records WHERE lore_text IS NULL OR lore_text = ''")
        no_lore_count = cursor.fetchone()[0]
        if no_lore_count > 0:
            info_log.append(f"\n⚠️  Champions without lore: {no_lore_count}")
        
        # Database schema info
        cursor.execute("PRAGMA table_info(lore_records)")
        schema_info = cursor.fetchall()
        
        info_log.append("\n🗂️  Database schema:")
        info_log.append("  Table: lore_records")
        for column_info in schema_info:
            col_name = column_info[1]
            col_type = column_info[2]
            is_pk = " (PRIMARY KEY)" if column_info[5] else ""
            info_log.append(f"    • {col_name}: {col_type}{is_pk}")
        
        conn.close()
        
    except Exception as e:
        info_log.append(f"⚠️  Error getting lore database info: {str(e)}")
        logger.error(f"Error getting lore database info: {str(e)}")
    
    info_log.append("--- LORE DATABASE INFO END ---\n")
    return info_log


def initialize_lore_db() -> bool:
    """
    Initialize lore database connection test
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        # Get database path
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "lore.db.sqlite")
        
        logger.info(f"Testing lore database connection: {db_path}")
        
        # Test connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM lore_records")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"Lore database connected successfully: {count} records available")
        return True
        
    except Exception as e:
        logger.error(f"Error connecting to lore database: {str(e)}")
        return False