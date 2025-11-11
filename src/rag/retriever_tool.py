"""
Retriever Tool - Wraps FAISS vectorstore as a LangChain tool for agents
"""
from typing import Optional
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool


def create_codebase_retriever_tool(
    vectorstore: FAISS,
    search_kwargs: Optional[dict] = None,
    name: str = "search_codebase",
    description: str = None
):
    """
    Create a retriever tool from FAISS vectorstore

    Args:
        vectorstore: FAISS vectorstore
        search_kwargs: Search parameters (e.g., {"k": 5})
        name: Tool name
        description: Tool description (shown to LLM)

    Returns:
        LangChain retriever tool
    """
    if search_kwargs is None:
        search_kwargs = {"k": 5}

    if description is None:
        description = """Search the Java codebase knowledge graph.

Use this tool to find:
- Classes, interfaces, and enums with their annotations and relationships
- Methods and their signatures
- REST API endpoints and their handlers
- Architecture patterns and design choices
- Package structure and organization

Input should be a search query describing what you're looking for.
Examples:
- "Find all controller classes"
- "What REST endpoints exist?"
- "Show classes that use @Service annotation"
- "Find entity classes in the user domain"
"""

    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

    tool = create_retriever_tool(
        retriever=retriever,
        name=name,
        description=description
    )

    return tool
