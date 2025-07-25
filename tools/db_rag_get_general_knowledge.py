from tools.db_rag_common import execute_universal_rag


def db_rag_get_general_knowledge(query: str) -> dict:
    """
    Search general knowledge base from PostgreSQL rag_vectors (PostgreSQL version)

    Args:
        query: Search query for knowledge base

    Returns:
        str: JSON formatted knowledge information with separated QA and similarity results
    """
    return execute_universal_rag(
        query=query,
        chunk_section=None,  # No filtering - search entire database
        category="general",
        function_name="db_rag_get_general_knowledge",
    )
