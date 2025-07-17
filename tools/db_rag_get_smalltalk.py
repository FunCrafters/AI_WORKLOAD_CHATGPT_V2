import logging
import random
from typing import List

from db_postgres import execute_query
from workload_embedding import get_embedding_function

# Logger
logger = logging.getLogger("DBSmalltalk")

# Configuration
SIMILARITY_THRESHOLD = 0.4
# Get top 10 similar results, then pick random one
RAG_SMALLTALK_SEARCH_LIMIT = 10

SAMPLE_SMALLTALK_TOPICS = [
    "Since you're not asking about anything specific, I was just processing...",
    "Ah, no particular query I see. Well, I've been analyzing...",
    "Without a specific tactical question to address, let me share what's been cycling through my processors...",
    "Greetings! Since we're just chatting, I've been pondering...",
    "No mission parameters detected, so perhaps we can discuss...",
    "My tactical subroutines are currently idle, which gives me time to consider...",
    "In the absence of direct orders, my processors have been evaluating...",
    "While waiting for your next command, I've been calculating...",
    "My sensor array is picking up a casual conversation opportunity, so I thought...",
    "With no immediate tactical objectives, I've been analyzing some interesting data about..",
]

SMALLTALK_SPECIALIST_EMBEDDING = """
Droid, start your response with a natural transition that acknowledges the user isn't asking a specific question. Use phrases like:
{}
Always refrase the answer to make it more natural, mandalorian style and droid humorus.
Then naturally transit into the topic using the knowledge provided. Incorporate military perspectives, tactical analysis, or academy anecdotes where appropriate. 
"""


def _generate_query_embedding(query_text: str) -> list | None:
    """Generate embedding for query text using Ollama"""
    try:
        embedding_function = get_embedding_function()
        if not embedding_function:
            logger.error("Embedding function not available")
            return None

        # Generate embedding using Ollama
        embedding = embedding_function.embed_query(query_text)
        return embedding

    except Exception as e:
        logger.error(f"Failed to generate embedding for query: {e}")
        return None


def db_rag_get_smalltalk(query: str = "") -> dict:
    try:
        search_query = query if query else "random topic"

        # Case 1: Empty query - get random topic
        if not query or query.strip() == "":
            logger.info("Empty query received, selecting random smalltalk topic")

            random_sql = """
            SELECT topic, category, knowledge_text
            FROM smalltalk_vectors
            ORDER BY RANDOM()
            LIMIT 1
            """

            results = execute_query(random_sql)

            if results:
                result = results[0]
                topic = result["topic"]
                category = result["category"]
                knowledge_text = result["knowledge_text"]

                content = f"### Information from galactic database: {topic} ({category})\n{knowledge_text}"

                random_subset = random.sample(SAMPLE_SMALLTALK_TOPICS, 3)

                return {
                    "status": "success",
                    "message": "Selected random smalltalk topic",
                    "search_query": search_query,
                    "content": {"smltk_results": content},
                    "llm_instruction": SMALLTALK_SPECIALIST_EMBEDDING.format(
                        "\n".join(random_subset)
                    ),
                    "internal_info": {
                        "function_name": "db_rag_get_smalltalk",
                        "parameters": {"query": query},
                        "method": "random_selection",
                    },
                }
            else:
                return {
                    "status": "success",
                    "message": "No smalltalk topics available in database",
                    "search_query": search_query,
                    "content": {"smltk_results": ""},
                    "internal_info": {
                        "function_name": "db_rag_get_smalltalk",
                        "parameters": {"query": query},
                    },
                }

        # Case 2: Query provided - perform embedding similarity search
        else:
            logger.info(f"Searching for smalltalk context with query: {query}")

            # Generate embedding using Ollama
            query_embedding = _generate_query_embedding(query)

            if query_embedding is not None:
                # Real pgvector similarity search
                logger.info("Using Ollama embedding-based similarity search")

                # Convert embedding to PostgreSQL vector format
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

                # Get multiple similar results and pick one randomly for variety
                similarity_sql = """
                SELECT topic, category, knowledge_text, 
                       1 - (embedding <=> %s::vector) as similarity
                FROM smalltalk_vectors
                WHERE 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """

                results = execute_query(
                    similarity_sql,
                    (
                        embedding_str,
                        embedding_str,
                        SIMILARITY_THRESHOLD,
                        embedding_str,
                        RAG_SMALLTALK_SEARCH_LIMIT,
                    ),
                )

                if results:
                    # Randomly select one from the top similar results for variety
                    result = random.choice(results)
                    logger.info(
                        f"Selected random result from {len(results)} similar topics"
                    )
                    topic = result["topic"]
                    category = result["category"]
                    knowledge_text = result["knowledge_text"]
                    similarity = result["similarity"]

                    content = f"### Information in galactic database: {topic} ({category})\n{knowledge_text}"

                    return {
                        "status": "success",
                        "message": f"Found smalltalk context for '{query}' (similarity: {similarity:.3f})",
                        "search_query": search_query,
                        "content": {"smltk_results": content},
                        "llm_instruction": SMALLTALK_SPECIALIST_EMBEDDING,
                        "internal_info": {
                            "function_name": "db_rag_get_smalltalk",
                            "parameters": {"query": query},
                            "method": "ollama_embedding_similarity_search",
                            "similarity_score": similarity,
                            "threshold": SIMILARITY_THRESHOLD,
                            "candidates_found": len(results),
                        },
                    }

                logger.info(
                    f"No embedding match above threshold {SIMILARITY_THRESHOLD}, falling back to random"
                )

            else:
                logger.info("Embedding generation failed, falling back to random")

            # No good match found - get random topic instead
            logger.info(
                f"No good smalltalk match for query '{query}', selecting random topic"
            )

            random_sql = """
            SELECT topic, category, knowledge_text
            FROM smalltalk_vectors
            ORDER BY RANDOM()
            LIMIT 1
            """

            results = execute_query(random_sql)

            if results:
                result = results[0]
                topic = result["topic"]
                category = result["category"]
                knowledge_text = result["knowledge_text"]

                content = f"### Information in galactic database: {topic} ({category})\n{knowledge_text}"

                return {
                    "status": "success",
                    "message": f"No specific match for '{query}', selected random smalltalk topic",
                    "search_query": search_query,
                    "content": {"smltk_results": content},
                    "llm_instruction": SMALLTALK_SPECIALIST_EMBEDDING,
                    "internal_info": {
                        "function_name": "db_rag_get_smalltalk",
                        "parameters": {"query": query},
                        "method": "random_fallback",
                    },
                }
            else:
                return {
                    "status": "success",
                    "message": "No smalltalk topics available in database",
                    "search_query": search_query,
                    "content": {"smltk_results": ""},
                    "internal_info": {
                        "function_name": "db_rag_get_smalltalk",
                        "parameters": {"query": query},
                    },
                }

    except Exception as e:
        logger.error(f"Error in db_get_smalltalk: {str(e)}")
        return {
            "status": "error",
            "message": f"Error searching smalltalk context: {str(e)}",
            "search_query": query if query else "random topic",
            "content": {"smltk_results": ""},
            "internal_info": {
                "function_name": "db_rag_get_smalltalk",
                "parameters": {"query": query},
                "error": str(e),
            },
        }


def db_rag_get_smalltalk_from_embedding(
    embeddings: List[float],
    RAG_SMALLTALK_SEARCH_LIMIT: int = 2,
) -> List[dict]:
    """
    Search smalltalk knowledge base using embeddings

    Args:
        embeddings: List of floats representing the query embedding
        SIMILARITY_THRESHOLD: Minimum similarity score to consider a match
        RAG_SMALLTALK_SEARCH_LIMIT: Number of results to return

    Returns:
        dict: Search results with status and content
    """
    if not embeddings:
        return []

    # Convert embedding to PostgreSQL vector format
    embedding_str = "[" + ",".join(map(str, embeddings)) + "]"

    # Perform similarity search
    similarity_sql = """
    SELECT topic, category, knowledge_text, embedding,
           1 - (embedding <=> %s::vector) as similarity
    FROM smalltalk_vectors
    ORDER BY similarity DESC
    LIMIT %s
    """

    results = execute_query(
        similarity_sql,
        (
            embedding_str,
            RAG_SMALLTALK_SEARCH_LIMIT,
        ),
    )

    if not results:
        return []

    # Format results in same structure as search_qa_similarity
    formatted_results = [
        {
            "similarity": float(r["similarity"]),
            "content": f"### {r['topic']} ({r['category']})\n{r['knowledge_text']}",
            "embedding": [float(x) for x in r["embedding"].strip("[]").split(",")],
        }
        for r in results
    ]

    return formatted_results


def db_get_smalltalk_text(query: str = "") -> str:
    """
    Search smalltalk knowledge base (text format for backward compatibility)

    Args:
        query: Search query for smalltalk topics. If empty, returns random topic.

    Returns:
        str: Smalltalk context information in text format
    """
    # Use the main function and extract text content
    json_result = db_rag_get_smalltalk(query)

    result_dict = json_result
    if result_dict.get("status") == "success":
        return result_dict["content"]["smltk_results"]
    else:
        return ""
