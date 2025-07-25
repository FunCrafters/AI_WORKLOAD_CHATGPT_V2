from tools.db_rag_common import execute_universal_rag


def db_rag_get_gameplay_details(query: str) -> dict:
    """
    Search gameplay information from PostgreSQL rag_vectors (PostgreSQL version)

    Args:
        query: Search query for gameplay information

    Returns:
        str: JSON formatted gameplay information with separated QA and similarity results
    """
    return execute_universal_rag(
        query=query,
        chunk_section="GAMEPLAY",
        category="gameplay",
        function_name="db_rag_get_gameplay_details",
    )
