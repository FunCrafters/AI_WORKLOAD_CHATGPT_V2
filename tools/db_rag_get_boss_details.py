#!/usr/bin/env python3
"""
Database tool: Get boss details from PostgreSQL
Get boss information from PostgreSQL rag_vectors table
"""

from tools.db_rag_common import execute_universal_rag


def db_rag_get_boss_details(boss_name: str) -> dict:
    """
    Search boss information from PostgreSQL rag_vectors (PostgreSQL version)

    Args:
        boss_name: Search query for boss information

    Returns:
        str: JSON formatted boss information with separated QA and similarity results
    """
    return execute_universal_rag(
        query=boss_name,
        chunk_section="BOSSES",
        category="bosses",
        function_name="db_rag_get_boss_details",
    )
