"""
Base Agent class - All agents inherit from this
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.knowledge_graph.graph import KnowledgeGraph


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system
    """

    def __init__(self, knowledge_graph: KnowledgeGraph, name: str):
        self.knowledge_graph = knowledge_graph
        self.name = name

    @abstractmethod
    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's task

        Args:
            query: Dictionary containing the query/task information

        Returns:
            Dictionary containing the results
        """
        pass

    def log(self, message: str):
        """Log a message with agent name"""
        print(f"[{self.name}] {message}")
