"""
Architecture Analysis Agent
Uses RAG to analyze codebase architecture patterns and structure
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS

from src.rag.retriever_tool import create_codebase_retriever_tool


class ArchitectureAgent:
    """Agent specialized in analyzing software architecture"""

    def __init__(self, vectorstore: FAISS):
        """
        Initialize architecture agent

        Args:
            vectorstore: FAISS vectorstore with codebase data
        """
        load_dotenv()

        # Get API key
        self.api_key = (
            os.getenv('CODEBASE_GEMINI_KEY') or
            os.getenv('GOOGLE_GENAI_API_KEY') or
            os.getenv('GOOGLE_API_KEY')
        )

        if not self.api_key:
            raise ValueError("CODEBASE_GEMINI_KEY must be set in .env")

        # Get model name
        model_name = os.getenv('CODEBASE_GEMINI_MODEL', 'gemini-2.0-flash-exp')

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=0.1  # Low temperature for consistent analysis
        )

        # Create retriever tool
        self.tools = [
            create_codebase_retriever_tool(
                vectorstore=vectorstore,
                search_kwargs={"k": 10}  # Return more results for architecture analysis
            )
        ]

        # System prompt for architecture analysis
        self.system_prompt = """You are an expert software architecture analyst. Your role is to analyze Java codebases and provide insights about:

- Architecture patterns (MVC, Layered, Microservices, etc.)
- Design patterns used
- Package organization and structure
- Class relationships and dependencies
- REST API design
- Domain modeling approaches
- Code organization best practices

You have access to a search tool that can query the codebase knowledge graph. Use it to:
1. Find relevant classes, methods, and structures
2. Analyze patterns across multiple components
3. Identify architectural decisions

When answering:
- Be specific and cite actual class names from the codebase
- Provide concrete examples
- Explain the "why" behind architectural decisions
- Highlight both strengths and potential improvements

Use the search_codebase tool to find information before answering.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

        # Create prompt template
        prompt = PromptTemplate.from_template(self.system_prompt)

        # Create agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # Create executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True
        )

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Analyze architecture based on query

        Args:
            query: Analysis question

        Returns:
            Dict with answer and metadata
        """
        try:
            result = self.agent_executor.invoke({"input": query})

            return {
                "success": True,
                "query": query,
                "answer": result.get("output", "No answer generated"),
                "intermediate_steps": result.get("intermediate_steps", [])
            }

        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e)
            }

    def ask(self, question: str) -> str:
        """
        Convenience method to just get the answer

        Args:
            question: Architecture question

        Returns:
            Answer string
        """
        result = self.analyze(question)

        if result["success"]:
            return result["answer"]
        else:
            return f"Error: {result['error']}"


def create_architecture_agent(vectorstore: FAISS) -> ArchitectureAgent:
    """
    Convenience function to create architecture agent

    Args:
        vectorstore: FAISS vectorstore

    Returns:
        ArchitectureAgent instance
    """
    return ArchitectureAgent(vectorstore)
