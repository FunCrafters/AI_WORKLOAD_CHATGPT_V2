from tools.db_rag_common import execute_universal_rag


def db_rag_get_battle_details(query: str) -> dict:
    """
    Search battle information from PostgreSQL rag_vectors (PostgreSQL version)

    Args:
        query: Search query for battle information

    Returns:
        str: JSON formatted battle information with separated QA and similarity results
    """
    return execute_universal_rag(
        query=query,
        chunk_section="BATTLES",
        category="battles",
        function_name="db_rag_get_battle_details",
    )
