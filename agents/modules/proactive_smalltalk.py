import json
import logging
import textwrap
from typing import List

import numpy as np
from openai.types.chat import ChatCompletionMessageParam
from sklearn.metrics.pairwise import cosine_similarity

from agents.modules.module import T3RNModule
from session import Session
from tools.db_rag_common import generate_embedding_from_conv, search_qa_similarity
from tools.db_rag_get_smalltalk import db_rag_get_smalltalk_from_embedding

logger = logging.getLogger("ProactiveSmallTalk")


class ProactiveSmalltalk(T3RNModule):
    SIMILLARITY_THRESHOLD = 0.5
    VARIATION_THRESHOLD = 0.8
    INJECT_MAX = 3

    def _cosine_matrix(self, smalltalks: List[dict]) -> np.ndarray:
        simmilarity_scores = np.zeros((len(smalltalks), len(smalltalks)))

        for i in range(len(smalltalks)):
            for j in range(i + 1, len(smalltalks)):
                simmilarity_scores[i][j] = cosine_similarity(
                    smalltalks[i]["embedding"],
                    smalltalks[j]["embedding"],
                )
                simmilarity_scores[j][i] = simmilarity_scores[i][j]

        return simmilarity_scores

    def _remove_duplicate(
        self, smalltalks: List[dict], simmilarity_scores: np.ndarray
    ) -> List[dict]:
        to_remove = set()
        for i in range(len(smalltalks)):
            for j in range(len(smalltalks)):
                if i == j or i in to_remove or j in to_remove:
                    continue
                if simmilarity_scores[i][j] > self.VARIATION_THRESHOLD:
                    if smalltalks[i]["similarity"] < smalltalks[j]["similarity"]:
                        to_remove.add(i)
                    else:
                        to_remove.add(j)

        return [s for i, s in enumerate(smalltalks) if i not in to_remove]

    def _apply_treshold(self, smalltalks: List[dict]) -> List[dict]:
        smalltalks_clean = [
            s for s in smalltalks if s["similarity"] >= self.SIMILLARITY_THRESHOLD
        ]
        return smalltalks_clean

    def remove_duplicate(self, smalltalks: List[dict]) -> List[dict]:
        simmilarity_scores = self._cosine_matrix(smalltalks)

        logger.debug(f"Simmilarity scores matrix:\n{simmilarity_scores}\n")

        smalltalks_clean = self._remove_duplicate(smalltalks, simmilarity_scores)

        smalltalks_clean = self._apply_treshold(smalltalks_clean)

        logger.info(
            f"Removed {len(smalltalks) - len(smalltalks_clean)} duplicates, remaining: {len(smalltalks_clean)}"
        )
        return smalltalks_clean

    def inject_after_user_message(
        self, session: Session
    ) -> List[ChatCompletionMessageParam]:
        memory = session.get_memory()

        last_exchange = memory.last_exchange()

        embedding = generate_embedding_from_conv(last_exchange)

        if embedding is None:
            self.channel_logger.log_to_logs(
                "Failed to generate embedding, returning empty injection"
            )
            self.channel_logger.log_to_tools(
                "Embedding generation failed, aborting smalltalk retrieval"
            )
            return []

        smalltalks = db_rag_get_smalltalk_from_embedding(
            embedding,
            RAG_SMALLTALK_SEARCH_LIMIT=4,
        )

        questions_answers = search_qa_similarity(
            embedding,
            limit=4,
        )

        # Create copies of lists without embeddings for logging
        smalltalks_log = [
            {
                "content": textwrap.shorten(s["content"], width=100),
                "similarity": s["similarity"],
            }
            for s in smalltalks
        ]
        qa_log = [
            {
                "content": textwrap.shorten(qa["content"], width=100),
                "similarity": qa["similarity"],
            }
            for qa in questions_answers
        ]

        logger.info(
            f"Retrieved smalltalks with similarity: {smalltalks_log} and questions/answers: {qa_log}"
        )

        smalltalks.extend(questions_answers)
        smalltalks = sorted(smalltalks, key=lambda x: x["similarity"], reverse=True)

        smalltalks_clean = self.remove_duplicate(smalltalks)

        smalltalks_clean_log = [
            {
                "content": s["content"],
                "similarity": s["similarity"],
            }
            for s in smalltalks_clean
        ]

        self.channel_logger.log_to_tools(
            f"ProactiveSmallTalk injection (Injecting top {self.INJECT_MAX}): {json.dumps(smalltalks_clean_log, indent=2)}"
        )

        smalltalks_clean = (
            smalltalks_clean[: self.INJECT_MAX]
            if len(smalltalks_clean) > self.INJECT_MAX
            else smalltalks_clean
        )

        response = f"""
System found some interesting information in your memory banks that might be relevant to this conversation:
{"\n".join([f"{s['content']} (similarity: {s['similarity']:.2f})" for s in smalltalks_clean])}
Droid, you can use this to enrich the conversation or ask follow-up questions. Ignore and use tools if not relevant.
"""

        injection_messages: List[ChatCompletionMessageParam] = [
            {
                "role": "developer",
                "content": response,
            }
        ]

        return injection_messages
