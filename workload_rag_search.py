#!/usr/bin/env python3
"""
Workload RAG Search
RAG search functionality and related functions
"""

import logging
import re
from typing import Dict, List, Any

# Import embedding functions
from workload_embedding import get_vectorstore

# Logger
logger = logging.getLogger("Workload RAG Search")

#######################
# Helper Functions
#######################

def make_case_insensitive_filter(key: str, value: Any) -> Dict[str, Any]:
    """
    Convert a filter to case-insensitive if it's a name filter
    
    Args:
        key: Filter key (e.g., 'name', 'section')
        value: Filter value
        
    Returns:
        dict: Case-insensitive filter for name fields, original filter for others
    """
    if key == "name" and isinstance(value, str):
        # For ChromaDB, we need to use a different approach for case-insensitive matching
        # We'll use multiple $or conditions for different case variations
        value_lower = value.lower()
        value_upper = value.upper()
        value_title = value.title()
        
        # Create OR filter with common case variations
        variations = [value, value_lower, value_upper, value_title]
        # Remove duplicates while preserving order
        unique_variations = []
        for v in variations:
            if v not in unique_variations:
                unique_variations.append(v)
        
        if len(unique_variations) == 1:
            return {key: {"$eq": unique_variations[0]}}
        else:
            return {key: {"$in": unique_variations}}
    elif isinstance(value, dict):
        return {key: value}
    else:
        return {key: {"$eq": value}}

#######################
# Universal RAG Search Function
#######################

def rag_search(query: str, search_config: dict) -> str:
    """
    Universal RAG search function with configurable parameters
    
    Args:
        query: Search query for knowledge base
        search_config: Configuration dictionary with:
            - base_filters: dict - Additional filters for similarity search
            - required_sections: list - Specific sections to ensure are included
            - similarity_chunks: int - Number of similarity chunks (default: 7)
            - qa_chunks: int - Number of Q&A chunks (default: 7)
            - smltk_chunks: int - Number of SMLTK chunks (default: 0)
        
    Returns:
        str: Found information from knowledge base in text format
    """
    try:
        vectorstore = get_vectorstore()
        
        if not vectorstore:
            return "Error: Knowledge base not available"
        
        # Get configuration parameters with validation to prevent k=0 error
        base_filters = search_config.get('base_filters', {})
        required_sections = search_config.get('required_sections', [])
        similarity_chunks = max(1, search_config.get('similarity_chunks', 7)) if search_config.get('similarity_chunks', 7) > 0 else 0
        qa_chunks = max(1, search_config.get('qa_chunks', 7)) if search_config.get('qa_chunks', 7) > 0 else 0
        smltk_chunks = max(1, search_config.get('smltk_chunks', 0)) if search_config.get('smltk_chunks', 0) > 0 else 0
        
        context = []
        found_sections = set()
        
        # 1. Search general documents with base filters - Fixed ChromaDB syntax
        if similarity_chunks > 0:
            if base_filters:
                # Build proper ChromaDB filter with $and operator
                filter_conditions = [
                    {"section": {"$ne": "Q&A"}},
                    {"section": {"$ne": "SMLTK"}}
                ]
                for key, value in base_filters.items():
                    filter_conditions.append(make_case_insensitive_filter(key, value))
                
                general_filter = {"$and": filter_conditions}
            else:
                general_filter = {
                    "$and": [
                        {"section": {"$ne": "Q&A"}},
                        {"section": {"$ne": "SMLTK"}}
                    ]
                }
            
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": similarity_chunks,
                    "filter": general_filter
                }
            )
            
            docs = retriever.invoke(query)
            
            if docs:
                for doc in docs:
                    doc_name = doc.metadata.get('name', 'unknown')
                    doc_section = doc.metadata.get('section', '')
                    context.append(f"### {doc_name}\n{doc.page_content}")
                    
                    # Track found sections for required_sections check
                    if doc_section:
                        found_sections.add((doc.metadata.get('name', ''), doc_section))
        
        # 2. Search Q&A documents with base filters - Fixed ChromaDB syntax
        if qa_chunks > 0:
            if base_filters:
                # Build proper ChromaDB filter with $and operator
                filter_conditions = [{"section": {"$eq": "Q&A"}}]
                for key, value in base_filters.items():
                    filter_conditions.append(make_case_insensitive_filter(key, value))
                
                qa_filter = {"$and": filter_conditions}
            else:
                qa_filter = {"section": {"$eq": "Q&A"}}
            
            retriever_qa = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": qa_chunks,
                    "filter": qa_filter
                }
            )
            
            docs_qa = retriever_qa.invoke(query)
            
            if docs_qa:
                for doc in docs_qa:
                    doc_name = doc.metadata.get('name', 'unknown')
                    context.append(f"### Q&A: {doc_name}\n{doc.page_content}")
        
        # 3. Search SMLTK documents with base filters
        if smltk_chunks > 0:
            if base_filters:
                # Build proper ChromaDB filter with $and operator
                filter_conditions = [{"section": {"$eq": "SMLTK"}}]
                for key, value in base_filters.items():
                    filter_conditions.append(make_case_insensitive_filter(key, value))
                
                smltk_filter = {"$and": filter_conditions}
            else:
                smltk_filter = {"section": {"$eq": "SMLTK"}}
            
            retriever_smltk = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": smltk_chunks,
                    "filter": smltk_filter
                }
            )
            
            docs_smltk = retriever_smltk.invoke(query)
            
            if docs_smltk:
                for doc in docs_smltk:
                    doc_name = doc.metadata.get('name', 'unknown')
                    context.append(f"### SMLTK: {doc_name}\n{doc.page_content}")
        
        # 4. Check for required sections and add missing ones
        for required_section in required_sections:
            section_name = required_section.get('name', '')
            section_type = required_section.get('section', '')
            
            # Check if this section is already in our results
            if (section_name, section_type) not in found_sections:
                # Perform precise search for missing section with case-insensitive name
                name_filter = make_case_insensitive_filter("name", section_name)
                precise_filter = {
                    "$and": [
                        name_filter,
                        {"section": {"$eq": section_type}}
                    ]
                }
                
                # Add base filters if they exist
                if base_filters:
                    for key, value in base_filters.items():
                        if key not in ['name', 'section']:  # Avoid conflicts
                            if isinstance(value, dict):
                                precise_filter["$and"].append({key: value})
                            else:
                                precise_filter["$and"].append({key: {"$eq": value}})
                
                try:
                    precise_docs = vectorstore.get(where=precise_filter, include=["documents", "metadatas"])
                    
                    if precise_docs["documents"]:
                        for i, doc_content in enumerate(precise_docs["documents"]):
                            metadata = precise_docs["metadatas"][i] if i < len(precise_docs["metadatas"]) else {}
                            doc_name = metadata.get('name', section_name)
                            context.append(f"### {doc_name} - {section_type}\n{doc_content}")
                
                except Exception as e:
                    # If precise search fails, continue without it
                    pass
        
        if not context:
            return ""
        
        # Combine all contexts
        combined_context = "\n\n".join(context)
        return combined_context
        
    except Exception as e:
        return f"Error in RAG search: {str(e)}"


def rag_search_details(query: str, search_config: dict) -> Dict[str, List[Any]]:
    """
    Universal RAG search function that returns document objects with metadata
    
    Args:
        query: Search query for knowledge base
        search_config: Configuration dictionary with:
            - base_filters: dict - Additional filters for similarity search
            - required_sections: list - Specific sections to ensure are included
            - similarity_chunks: int - Number of similarity chunks (default: 7)
            - qa_chunks: int - Number of Q&A chunks (default: 7)
            - smltk_chunks: int - Number of SMLTK chunks (default: 0)
        
    Returns:
        dict: Dictionary with 'similarity', 'qa', 'smltk' keys containing lists of document objects
    """
    try:
        vectorstore = get_vectorstore()
        
        if not vectorstore:
            return {"similarity": [], "qa": [], "smltk": [], "error": "Knowledge base not available"}
        
        # Get configuration parameters with validation to prevent k=0 error
        base_filters = search_config.get('base_filters', {})
        required_sections = search_config.get('required_sections', [])
        similarity_chunks = max(1, search_config.get('similarity_chunks', 7)) if search_config.get('similarity_chunks', 7) > 0 else 0
        qa_chunks = max(1, search_config.get('qa_chunks', 7)) if search_config.get('qa_chunks', 7) > 0 else 0
        smltk_chunks = max(1, search_config.get('smltk_chunks', 0)) if search_config.get('smltk_chunks', 0) > 0 else 0
        
        result = {
            "similarity": [],
            "qa": [],
            "smltk": []
        }
        
        # 1. Search general documents with base filters
        if similarity_chunks > 0:
            if base_filters:
                # Build proper ChromaDB filter with $and operator
                filter_conditions = [
                    {"section": {"$ne": "Q&A"}},
                    {"section": {"$ne": "SMLTK"}}
                ]
                for key, value in base_filters.items():
                    filter_conditions.append(make_case_insensitive_filter(key, value))
                
                general_filter = {"$and": filter_conditions}
            else:
                general_filter = {
                    "$and": [
                        {"section": {"$ne": "Q&A"}},
                        {"section": {"$ne": "SMLTK"}}
                    ]
                }
            
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": similarity_chunks,
                    "filter": general_filter
                }
            )
            
            docs = retriever.invoke(query)
            result["similarity"] = docs if docs else []
        
        # 2. Search Q&A documents with base filters
        if qa_chunks > 0:
            if base_filters:
                # Build proper ChromaDB filter with $and operator
                filter_conditions = [{"section": {"$eq": "Q&A"}}]
                for key, value in base_filters.items():
                    filter_conditions.append(make_case_insensitive_filter(key, value))
                
                qa_filter = {"$and": filter_conditions}
            else:
                qa_filter = {"section": {"$eq": "Q&A"}}
            
            retriever_qa = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": qa_chunks,
                    "filter": qa_filter
                }
            )
            
            docs_qa = retriever_qa.invoke(query)
            result["qa"] = docs_qa if docs_qa else []
        
        # 3. Search SMLTK documents with base filters
        if smltk_chunks > 0:
            if base_filters:
                # Build proper ChromaDB filter with $and operator
                filter_conditions = [{"section": {"$eq": "SMLTK"}}]
                for key, value in base_filters.items():
                    filter_conditions.append(make_case_insensitive_filter(key, value))
                
                smltk_filter = {"$and": filter_conditions}
            else:
                smltk_filter = {"section": {"$eq": "SMLTK"}}
            
            retriever_smltk = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": smltk_chunks,
                    "filter": smltk_filter
                }
            )
            
            docs_smltk = retriever_smltk.invoke(query)
            result["smltk"] = docs_smltk if docs_smltk else []
        
        # 4. Handle required sections (simplified for this version)
        # This could be extended to include required sections in the result
        
        return result
        
    except Exception as e:
        return {"similarity": [], "qa": [], "smltk": [], "error": str(e)}
