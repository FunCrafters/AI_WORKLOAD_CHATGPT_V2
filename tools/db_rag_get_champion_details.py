from tools.db_rag_common import execute_universal_rag


def db_rag_get_champion_details(champion_name: str) -> dict:
    """
    Search champion information from PostgreSQL rag_vectors (PostgreSQL version)

    Args:
        champion_name: Search query for champion information

    Returns:
        str: JSON formatted champion information with separated QA and similarity results
    """
    return execute_universal_rag(query=champion_name, chunk_section="CHAMPIONS", category="champions", function_name="db_rag_get_champion_details")
