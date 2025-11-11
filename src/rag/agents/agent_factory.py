"""
Agent Factory - Creates different specialized agents for various analysis tasks
Extensible design for adding more agent types in the future
"""
from typing import Dict, Any, Optional
from enum import Enum

from langchain_community.vectorstores import FAISS
from src.rag.agents.architecture_agent import ArchitectureAgent


class AgentType(Enum):
    """Available agent types"""
    ARCHITECTURE = "architecture"
    # Future agent types:
    # SECURITY = "security"
    # DOMAIN = "domain"
    # PERFORMANCE = "performance"
    # DOCUMENTATION = "documentation"


class AgentFactory:
    """Factory for creating specialized agents"""

    @staticmethod
    def create_agent(
        agent_type: AgentType,
        vectorstore: FAISS,
        **kwargs
    ):
        """
        Create an agent of specified type

        Args:
            agent_type: Type of agent to create
            vectorstore: FAISS vectorstore with codebase data
            **kwargs: Additional agent-specific parameters

        Returns:
            Agent instance

        Raises:
            ValueError: If agent_type is not supported
        """
        if agent_type == AgentType.ARCHITECTURE:
            return ArchitectureAgent(vectorstore)

        # Future agent implementations:
        # elif agent_type == AgentType.SECURITY:
        #     return SecurityAgent(vectorstore)
        # elif agent_type == AgentType.DOMAIN:
        #     return DomainAgent(vectorstore)

        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

    @staticmethod
    def get_available_agents() -> Dict[str, str]:
        """
        Get list of available agent types with descriptions

        Returns:
            Dict of agent_type -> description
        """
        return {
            "architecture": "Analyzes software architecture patterns, design choices, and structure",
            # Future:
            # "security": "Identifies potential security vulnerabilities and best practices",
            # "domain": "Analyzes business domain models and entity relationships",
            # "performance": "Identifies performance bottlenecks and optimization opportunities",
            # "documentation": "Generates documentation and explains code functionality",
        }


# Convenience functions

def create_architecture_agent_via_factory(vectorstore: FAISS) -> ArchitectureAgent:
    """Create architecture agent via factory"""
    return AgentFactory.create_agent(AgentType.ARCHITECTURE, vectorstore)


def get_agent_capabilities() -> Dict[str, str]:
    """Get descriptions of all available agents"""
    return AgentFactory.get_available_agents()
