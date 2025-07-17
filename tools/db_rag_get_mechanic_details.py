#!/usr/bin/env python3
"""
Database tool: Get mechanics details from PostgreSQL
Get game mechanics information from PostgreSQL rag_vectors table
"""

from tools.db_rag_common import execute_universal_rag


def db_rag_get_mechanic_details(query: str) -> dict:
    """
    Search game mechanics information from PostgreSQL rag_vectors (PostgreSQL version)

    Args:
        query: Search query for mechanics information

    Returns:
        str: JSON formatted mechanics information with separated QA and similarity results
    """
    return execute_universal_rag(
        query=query,
        chunk_section="MECHANICS",
        category="mechanics",
        function_name="db_rag_get_mechanic_details",
    )
