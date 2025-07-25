#!/usr/bin/env python3
"""
PostgreSQL Database Handler
Manages PostgreSQL database connection for the application
"""

import logging
import os
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras

# Logger
logger = logging.getLogger("PGSQLHandler")

# Global database connection
POSTGRES_CONNECTION: Optional[psycopg2.extensions.connection] = None


def initialize_postgres_db():
    """Initialize PostgreSQL database connection (keep it open for regular queries)"""
    global POSTGRES_CONNECTION

    try:
        # Get database configuration from environment
        host = os.environ["POSTGRES_HOST"]
        port = int(os.environ["POSTGRES_PORT"])
        user = os.environ["POSTGRES_USER"]
        password = os.environ["POSTGRES_PASSWORD"]
        database = os.environ["POSTGRES_DB"]

        logger.info(f"Opening PostgreSQL database connection: {host}:{port}/{database}")

        # Connect to database
        POSTGRES_CONNECTION = psycopg2.connect(host=host, port=port, user=user, password=password, database=database)

        # Test connection
        cursor = POSTGRES_CONNECTION.cursor()
        cursor.execute("SELECT version()")
        (version,) = cursor.fetchone() or ["Unknown version"]
        cursor.close()

        logger.info("PostgreSQL database connected successfully")
        logger.info(f"PostgreSQL version: {version}")
        return True

    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL database: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        POSTGRES_CONNECTION = None
        return False


def execute_query(query: str, params: tuple | list | None = None) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query on the PostgreSQL database

    Args:
        query: SQL query to execute
        params: Optional parameters for parameterized queries

    Returns:
        List of dictionaries representing rows
    """
    global POSTGRES_CONNECTION
    if POSTGRES_CONNECTION is None:
        raise ValueError("PostgreSQL connection not initialized. Call initialize_postgres_db() first.")

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

        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
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
    info = []

    if not POSTGRES_CONNECTION or POSTGRES_CONNECTION.closed:
        info.append("⚠️  PostgreSQL database not connected")
        return info

    try:
        cursor = POSTGRES_CONNECTION.cursor()

        # Get database version
        cursor.execute("SELECT version()")
        (version,) = cursor.fetchone() or ["Unknown version"]
        info.append(f"📊 PostgreSQL Version: {version}")

        # Get database name
        cursor.execute("SELECT current_database()")
        (db_name,) = cursor.fetchone() or ["Unknown database"]
        info.append(f"🗄️  Database: {db_name}")

        # Get all tables with record counts
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        tables = cursor.fetchall()

        if tables:
            info.append(f"📋 Total Tables: {len(tables)}")
            info.append("")
            info.append("### 📊 TABLE RECORD COUNTS")
            info.append("")

            total_records = 0
            table_info = []

            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    (count,) = cursor.fetchone() or [0]
                    table_info.append((table_name, count))
                    total_records += count
                except Exception as e:
                    table_info.append((table_name, f"Error: {str(e)}"))

            # Sort tables by record count (descending)
            table_info.sort(key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True)

            # Display tables with counts
            for table_name, count in table_info:
                if isinstance(count, int):
                    percentage = (count / total_records * 100) if total_records > 0 else 0
                    info.append(f"📄 {table_name:<25} | {count:>8,} records ({percentage:>5.1f}%)")
                else:
                    info.append(f"📄 {table_name:<25} | {count}")

            info.append("")
            info.append(f"🔢 **Total Records**: {total_records:,}")
        else:
            info.append("📋 No tables found in database")

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
