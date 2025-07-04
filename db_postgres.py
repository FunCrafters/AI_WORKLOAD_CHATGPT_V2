#!/usr/bin/env python3
"""
PostgreSQL Database Handler
Manages PostgreSQL database connection for the application
"""

import os
import logging
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional

# Logger
logger = logging.getLogger("Workload PostgreSQL DB")

# Global database connection
POSTGRES_CONNECTION: Optional[psycopg2.extensions.connection] = None


def initialize_postgres_db():
    """Initialize PostgreSQL database connection (keep it open for regular queries)"""
    global POSTGRES_CONNECTION
    
    try:
        # Get database configuration from environment
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = int(os.getenv('POSTGRES_PORT', '5432'))
        user = os.getenv('POSTGRES_USER', 'tools')
        password = os.getenv('POSTGRES_PASSWORD')
        database = os.getenv('POSTGRES_DB', 'llm_tools')
        
        logger.info(f"Opening PostgreSQL database connection: {host}:{port}/{database}")
        
        # Connect to database
        POSTGRES_CONNECTION = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        # Test connection
        cursor = POSTGRES_CONNECTION.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        
        logger.info(f"PostgreSQL database connected successfully")
        logger.info(f"PostgreSQL version: {version}")
        return True
        
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        POSTGRES_CONNECTION = None
        return False


def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query on the PostgreSQL database
    
    Args:
        query: SQL query to execute
        params: Optional parameters for parameterized queries
        
    Returns:
        List of dictionaries representing rows
    """
    global POSTGRES_CONNECTION
    
    # Make sure connection is established
    if not POSTGRES_CONNECTION or POSTGRES_CONNECTION.closed:
        if not initialize_postgres_db():
            logger.error("Failed to initialize PostgreSQL database connection")
            return []
    
    try:
        cursor = POSTGRES_CONNECTION.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Check if this is a SELECT query
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            # Convert RealDictRow to regular dict
            result = [dict(row) for row in rows]
        else:
            # For non-SELECT queries, commit the transaction
            POSTGRES_CONNECTION.commit()
            result = []
        
        cursor.close()
        return result
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        if POSTGRES_CONNECTION:
            POSTGRES_CONNECTION.rollback()
        return []


def get_postgres_database_info() -> List[str]:
    """
    Get PostgreSQL database information for logging
    
    Returns:
        List of info strings
    """
    info = []
    
    if not POSTGRES_CONNECTION or POSTGRES_CONNECTION.closed:
        info.append("⚠️  PostgreSQL database not connected")
        return info
    
    try:
        cursor = POSTGRES_CONNECTION.cursor()
        
        # Get database version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        info.append(f"📊 PostgreSQL Version: {version}")
        
        # Get database name
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()[0]
        info.append(f"🗄️  Database: {db_name}")
        
        # Get table count
        cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        info.append(f"📋 Tables: {table_count}")
        
        # Get some table names
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5")
        tables = cursor.fetchall()
        if tables:
            table_names = [table[0] for table in tables]
            info.append(f"📄 Sample tables: {', '.join(table_names)}")
        
        cursor.close()
        
    except Exception as e:
        info.append(f"⚠️  Error getting PostgreSQL info: {str(e)}")
    
    return info


def close_postgres_connection():
    """Close the PostgreSQL database connection"""
    global POSTGRES_CONNECTION
    
    if POSTGRES_CONNECTION and not POSTGRES_CONNECTION.closed:
        POSTGRES_CONNECTION.close()
        POSTGRES_CONNECTION = None
        logger.info("PostgreSQL database connection closed")