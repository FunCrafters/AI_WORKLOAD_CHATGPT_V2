#!/usr/bin/env python3
"""
Database tool: Get locations details from PostgreSQL
Get location information from PostgreSQL rag_vectors table
"""

from tools.db_rag_common import execute_universal_rag


def db_rag_get_location_details(query: str) -> dict:
    """
    Search location information from PostgreSQL rag_vectors (PostgreSQL version)

    Args:
        query: Search query for location information

    Returns:
        str: JSON formatted location information with separated QA and similarity results
    """
    return execute_universal_rag(
        query=query,
        chunk_section="LOCATIONS",
        category="locations",
        function_name="db_rag_get_location_details",
    )
