#!/usr/bin/env python3
"""
GCS Database Handler
Manages GCS (Game Content System) data from SQLite database
"""

import os
import logging
import sqlite3
from typing import Dict, List, Any, Optional

# Logger
logger = logging.getLogger("Workload GCS DB")

# Global database connection
GCS_CONNECTION: Optional[sqlite3.Connection] = None
GCS_CURSOR: Optional[sqlite3.Cursor] = None


def initialize_gcs_db():
    """Initialize GCS database connection (keep it open for regular queries)"""
    global GCS_CONNECTION, GCS_CURSOR
    
    try:
        # Get database path from environment
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "gcs_data.db.sqlite")
        
        logger.info(f"Opening GCS database connection: {db_path}")
        
        # Connect to database
        GCS_CONNECTION = sqlite3.connect(db_path)
        GCS_CONNECTION.row_factory = sqlite3.Row  # Enable column access by name
        GCS_CURSOR = GCS_CONNECTION.cursor()
        
        # Get all tables in the database (just for logging)
        GCS_CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = GCS_CURSOR.fetchall()
        table_names = [table[0] for table in tables]
        
        logger.info(f"GCS database connected successfully")
        logger.info(f"Available tables: {table_names}")
        return True
        
    except Exception as e:
        logger.error(f"Error connecting to GCS database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        GCS_CONNECTION = None
        GCS_CURSOR = None
        return False


def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query on the GCS database
    
    Args:
        query: SQL query to execute
        params: Optional parameters for parameterized queries
        
    Returns:
        List of dictionaries representing rows
    """
    global GCS_CONNECTION, GCS_CURSOR
    
    # Make sure connection is established
    if not GCS_CONNECTION or not GCS_CURSOR:
        if not initialize_gcs_db():
            logger.error("Failed to initialize GCS database connection")
            return []
    
    try:
        if params:
            GCS_CURSOR.execute(query, params)
        else:
            GCS_CURSOR.execute(query)
        
        rows = GCS_CURSOR.fetchall()
        
        # Convert rows to list of dictionaries
        result = []
        for row in rows:
            result.append(dict(zip(row.keys(), row)))
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Params: {params}")
        return []


def get_gcs_table_names() -> List[str]:
    """
    Get list of available GCS table names
    
    Returns:
        List of table names
    """
    query = "SELECT name FROM sqlite_master WHERE type='table'"
    tables = execute_query(query)
    return [table['name'] for table in tables]


def query_gcs_table(table_name: str, filters: Dict[str, Any] = None, limit: int = None) -> List[Dict[str, Any]]:
    """
    Query specific GCS table with optional filters
    
    Args:
        table_name: Name of the table to query
        filters: Optional dictionary of column:value filters
        limit: Optional limit on number of results
        
    Returns:
        List of matching records
    """
    # Build query
    query = f"SELECT * FROM {table_name}"
    params = []
    
    if filters:
        where_clauses = []
        for key, value in filters.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        query += " WHERE " + " AND ".join(where_clauses)
    
    if limit:
        query += f" LIMIT {limit}"
    
    return execute_query(query, tuple(params) if params else None)


def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    Get schema information for a specific table
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of column information
    """
    query = f"PRAGMA table_info({table_name})"
    return execute_query(query)


def get_gcs_database_info() -> List[str]:
    """
    Get comprehensive information about the GCS database
    
    Returns:
        List of strings containing database information
    """
    info_log = []
    info_log.append("\n--- GCS DATABASE (gcs_data.db.sqlite) ---")
    
    try:
        # Get all table names
        tables = get_gcs_table_names()
        info_log.append(f"Total tables in GCS database: {len(tables)}")
        info_log.append(f"Tables: {', '.join(tables)}")
        
        # Get champions information
        info_log.append("\n📊 CHAMPIONS DATA:")
        champions_query = """
            SELECT DISTINCT 
                id,
                name,
                rarity,
                class_type as class,
                affinity,
                character_name
            FROM game_entities 
            WHERE entity_type = 'champion'
            ORDER BY name
        """
        champions = execute_query(champions_query)
        
        if champions:
            info_log.append(f"Total champions in database: {len(champions)}")
            
            # Group by rarity
            rarities = {}
            for champ in champions:
                rarity = champ.get('rarity', 'Unknown')
                if rarity not in rarities:
                    rarities[rarity] = []
                rarities[rarity].append(champ['name'])
            
            info_log.append("\n🔸 Champions by rarity:")
            for rarity, champ_list in sorted(rarities.items()):
                info_log.append(f"  {rarity}: {len(champ_list)} champions")
            
            # Group by class
            classes = {}
            for champ in champions:
                class_name = champ.get('class', 'Unknown')
                if class_name not in classes:
                    classes[class_name] = []
                classes[class_name].append(champ['name'])
            
            info_log.append("\n🔸 Champions by class:")
            for class_name, champ_list in sorted(classes.items()):
                info_log.append(f"  {class_name}: {len(champ_list)} champions")
            
            # Group by affinity
            affinities = {}
            for champ in champions:
                affinity = champ.get('affinity', 'Unknown')
                if affinity not in affinities:
                    affinities[affinity] = []
                affinities[affinity].append(champ['name'])
            
            info_log.append("\n🔸 Champions by affinity:")
            for affinity, champ_list in sorted(affinities.items()):
                info_log.append(f"  {affinity}: {len(champ_list)} champions")
            
            # List all champions
            info_log.append("\n🎯 ALL CHAMPIONS IN DATABASE:")
            for champ in champions:
                info_log.append(f"  • {champ['name']} ({champ['rarity']}, {champ['class']}, {champ['affinity']})")
        else:
            info_log.append("❌ No champions found in database")
        
        # Get enemies information
        info_log.append("\n📊 ENEMIES DATA:")
        enemies_query = """
            SELECT COUNT(DISTINCT id) as enemy_count
            FROM game_entities
            WHERE entity_type = 'enemy'
        """
        enemies_result = execute_query(enemies_query)
        if enemies_result:
            info_log.append(f"Total enemies in database: {enemies_result[0]['enemy_count']}")
        
        # Get some statistics about other tables
        info_log.append("\n📊 OTHER TABLES STATISTICS:")
        for table in tables:
            if table != 'game_entities':  # We already covered game_entities above
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                result = execute_query(count_query)
                if result:
                    info_log.append(f"  {table}: {result[0]['count']} records")
        
    except Exception as e:
        info_log.append(f"⚠️  Error getting GCS database info: {str(e)}")
        logger.error(f"Error getting GCS database info: {str(e)}")
    
    info_log.append("--- GCS DATABASE INFO END ---\n")
    return info_log


def close_gcs_connection():
    """Close the GCS database connection"""
    global GCS_CONNECTION, GCS_CURSOR
    
    if GCS_CONNECTION:
        GCS_CONNECTION.close()
        GCS_CONNECTION = None
        GCS_CURSOR = None
        logger.info("GCS database connection closed")