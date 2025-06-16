# agents/retriever.py
# agents/retriever.py

import logging
logger = logging.getLogger(__name__)

from typing import Dict, Any, List
from langchain_core.runnables import Runnable
from tools.vector_store import get_vector_retriever

class RetrieverAgent(Runnable):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def invoke(self, input: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
        import re
        path = input["uploaded_file_path"]
        query = input["user_input"]

        retriever = None
        try:
            retriever = get_vector_retriever(path)
            results = retriever.get_relevant_documents(query)

            self.logger.info(f"Retrieved {len(results)} chunks for query: {query}")

            if not results or all(len(d.page_content.strip()) < 30 for d in results):
                self.logger.warning("Fallback triggered: No meaningful content retrieved.")
                return {
                    "retrieved_chunks": ["⚠️ No meaningful content found in the uploaded file for this query."]
                }

            # Semantic similarity filtering (prefer retriever if available)
            def is_relevant_semantic(chunk: str, query: str, threshold: float = 0.2) -> bool:
                # Use retriever's similarity if available
                if hasattr(retriever, "similarity_fn"):
                    try:
                        score = retriever.similarity_fn(chunk, query)
                        return score > threshold
                    except Exception:
                        pass
                # Fallback: SequenceMatcher
                from difflib import SequenceMatcher
                return SequenceMatcher(None, chunk.lower(), query.lower()).ratio() > threshold

            cleaned_chunks = [
                doc.page_content.strip().replace("\\n", " ").replace("\n", " ")
                for doc in results
            ]

            # Shortcut: Exact string match bypass
            for chunk in cleaned_chunks:
                if query.lower() in chunk.lower():
                    self.logger.info("⚡ Exact match found, prioritizing.")
                    return {"retrieved_chunks": [chunk]}

            filtered = [
                chunk for chunk in cleaned_chunks
                if is_relevant_semantic(chunk, query)
            ]

            leadership_keywords = ["leadership", "traits", "principles", "leaders", "qualities", "amazon"]
            # Removed leadership principles list and mentions_multiple_principles function and enrichment logic

            # Optional override for leadership queries
            if not filtered and any(kw in query.lower() for kw in leadership_keywords):
                self.logger.warning("Leadership query override: relaxing filters (include top chunks).")
                filtered = cleaned_chunks[:3]

            if not filtered and cleaned_chunks:
                self.logger.warning("No relevant chunks found. Returning top 3 as fallback.")
                filtered = cleaned_chunks[:3]
            elif not filtered:
                self.logger.warning("No content available for fallback.")
                return {
                    "retrieved_chunks": ["⚠️ No meaningful content found in the uploaded file for this query."]
                }

            return {"retrieved_chunks": filtered}

        except Exception as e:
            self.logger.error(f"RetrieverAgent failed: {str(e)}")
            return {
                "retrieved_chunks": [f"⚠️ Error: {str(e)}"]
            }
        finally:
            if retriever and hasattr(retriever, "close"):
                try:
                    retriever.close()
                except Exception as close_exc:
                    self.logger.error(f"Error closing retriever: {close_exc}")

    def __str__(self):
        return "retriever"