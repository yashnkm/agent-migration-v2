"""
Planning Architecture Agent - Multi-step RAG-based architecture analysis
Uses LangGraph's create_react_agent with systematic querying approach
"""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field


# Architecture Analysis Checklist
ARCHITECTURE_ANALYSIS_PLAN = {
    "1. Entry Points": {
        "query": "@RestController @Controller main class entry points",
        "goal": "Identify application entry points, REST controllers, main classes"
    },
    "2. Business Logic": {
        "query": "@Service business logic use cases application services",
        "goal": "Find service classes, business logic, use cases"
    },
    "3. Data Access": {
        "query": "@Repository DAO database JPA Hibernate data access",
        "goal": "Identify repositories, DAOs, database interactions"
    },
    "4. Domain Model": {
        "query": "@Entity domain model DTO data classes",
        "goal": "Find entity classes, domain models, DTOs"
    },
    "5. Configuration": {
        "query": "@Configuration @Bean application properties configuration",
        "goal": "Identify configuration classes, beans, properties"
    },
    "6. Dependencies": {
        "query": "dependency injection autowired component relationships",
        "goal": "Understand component dependencies and relationships"
    },
    "7. Patterns": {
        "query": "design patterns architecture MVC layered hexagonal",
        "goal": "Identify architectural patterns and design patterns used"
    }
}


class PlanningArchitectureAgent:
    """
    Planning-based architecture agent that systematically queries RAG
    to build comprehensive architecture understanding
    """

    def __init__(self, vectorstore: FAISS):
        """
        Initialize planning architecture agent

        Args:
            vectorstore: FAISS vectorstore with codebase
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
            temperature=0.3
        )

        self.vectorstore = vectorstore

        # Create retriever tool for the agent
        self._create_retriever_tool()

        # Create the agent
        self._create_agent()

    def _create_retriever_tool(self):
        """Create retriever tool for agent to use"""

        @tool
        def search_codebase(query: str) -> str:
            """
            Search the codebase using semantic search.
            Use this tool to find relevant code, classes, methods, and patterns.

            Args:
                query: Search query describing what to look for

            Returns:
                Relevant code snippets and information
            """
            # Search vectorstore
            results = self.vectorstore.similarity_search(query, k=10)

            # Format results
            formatted_results = []
            for i, doc in enumerate(results, 1):
                content = doc.page_content
                metadata = doc.metadata
                formatted_results.append(
                    f"--- Result {i} ---\n"
                    f"File: {metadata.get('file_path', 'Unknown')}\n"
                    f"Type: {metadata.get('node_type', 'Unknown')}\n"
                    f"Content:\n{content}\n"
                )

            return "\n".join(formatted_results)

        self.search_tool = search_codebase

    def _create_agent(self):
        """Create the planning agent using LangGraph"""

        system_prompt = """You are an expert software architect analyzing a Java codebase.

Your task is to systematically analyze the architecture by following this checklist:

1. **Entry Points**: Identify @RestController, @Controller, main classes
2. **Business Logic**: Find @Service classes, business logic, use cases
3. **Data Access**: Locate @Repository, DAOs, database interactions
4. **Domain Model**: Find @Entity, domain models, DTOs
5. **Configuration**: Identify @Configuration, @Bean, properties
6. **Dependencies**: Understand component relationships and dependencies
7. **Patterns**: Identify architectural and design patterns

**Tool Usage - CRITICAL FORMAT**:
When using the search_codebase tool, you MUST use this EXACT format with BOTH lines:

Action: search_codebase
Action Input: "your search query here"

CORRECT Examples:
Action: search_codebase
Action Input: "@RestController @Controller entry points"

Action: search_codebase
Action Input: "@Service business logic"

INCORRECT Examples (DO NOT USE):
❌ Action: search_codebase(query="...") - Missing Action Input line
❌ Action:\nsearch_codebase - Missing Action Input line
❌ Just writing the query without Action: and Action Input: labels

REMEMBER: You MUST include BOTH the "Action:" line AND the "Action Input:" line

**Instructions**:
- Use the search_codebase tool MULTIPLE TIMES to gather information for EACH section
- For each section, formulate specific queries to find relevant code
- After each search, analyze the results before continuing
- Keep searching until you have full coverage of all 7 sections
- After gathering all information, synthesize it into a complete analysis

**Important**:
- You MUST search for each section systematically
- Don't make assumptions - use the tool to verify
- Cite actual class names, methods, and patterns you find
"""

        # Create agent with retriever tool using LangGraph
        self.agent = create_react_agent(
            self.llm,
            tools=[self.search_tool],
            state_modifier=system_prompt
        )

    def analyze_architecture(self, project_name: str = "Java Project") -> Dict[str, Any]:
        """
        Analyze architecture using planning approach

        Args:
            project_name: Name of the project

        Returns:
            Comprehensive architecture analysis
        """
        print(f"Starting systematic architecture analysis for {project_name}...")

        # Create analysis prompt with checklist
        analysis_prompt = f"""Analyze the architecture of the {project_name} codebase.

Follow the systematic checklist:

1. **Entry Points**: Search for @RestController, @Controller, main classes
2. **Business Logic**: Search for @Service classes, business logic
3. **Data Access**: Search for @Repository, DAOs
4. **Domain Model**: Search for @Entity, domain models
5. **Configuration**: Search for @Configuration, @Bean
6. **Dependencies**: Analyze component relationships
7. **Patterns**: Identify architectural patterns

For EACH section:
- Use search_codebase tool with specific queries
- Document what you find
- Cite actual class names

After completing all searches, provide a comprehensive summary covering:
- Executive summary
- Architecture patterns identified
- Layered structure (presentation, business, data, domain)
- Key components and their relationships
- Data flow
- Technology stack
- Strengths
- Recommendations

Be thorough and systematic. Don't rush - take time to search multiple times."""

        # Invoke agent
        print("Agent is systematically searching the codebase...")
        print("This will take multiple RAG queries to build complete understanding...")
        print("")

        try:
            result = self.agent.invoke({
                "messages": [{"role": "user", "content": analysis_prompt}]
            })

            # Debug: Check what we got back
            print(f"\nDEBUG: Got {len(result['messages'])} messages in result")

            # Check if agent actually used tools
            tool_calls_count = 0
            for msg in result['messages']:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls_count += len(msg.tool_calls)

            print(f"DEBUG: Agent made {tool_calls_count} tool calls")

            if tool_calls_count == 0:
                print("⚠️  WARNING: Agent did not use any tools - analysis may be generic!")
                print("⚠️  This usually means the agent hit the 'Action Input' error")

            # Extract final response
            final_message = result['messages'][-1]
            analysis = final_message.content

            print("\n✓ Systematic analysis complete!")

        except Exception as e:
            print(f"\n❌ ERROR during agent execution: {str(e)}")
            print("Falling back to direct RAG queries...")

            # Fallback: do direct RAG queries
            analysis = self._fallback_direct_queries(project_name)

            result = {"messages": []}

        # Parse and structure the analysis
        return {
            "project_name": project_name,
            "analysis": analysis,
            "messages": result['messages']  # Full conversation history
        }

    def get_detailed_section(self, section: str) -> str:
        """
        Get detailed analysis for a specific section

        Args:
            section: Section name (e.g., "Entry Points", "Business Logic")

        Returns:
            Detailed analysis for that section
        """
        if section not in ARCHITECTURE_ANALYSIS_PLAN:
            raise ValueError(f"Unknown section: {section}")

        plan = ARCHITECTURE_ANALYSIS_PLAN[section]

        prompt = f"""Analyze the {section} of this codebase.

Goal: {plan['goal']}
Suggested query: {plan['query']}

Use the search_codebase tool to find relevant information.
Provide a detailed analysis with actual class names and examples."""

        result = self.agent.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })

        return result['messages'][-1].content

    def _fallback_direct_queries(self, project_name: str) -> str:
        """
        Fallback: Direct RAG queries if agent fails

        Args:
            project_name: Project name

        Returns:
            Analysis from direct queries
        """
        print("\n🔄 Using direct RAG query fallback...")

        findings = []

        for section_name, section_info in ARCHITECTURE_ANALYSIS_PLAN.items():
            print(f"  🔍 Querying: {section_name}...")

            query = section_info['query']
            results = self.vectorstore.similarity_search(query, k=8)

            section_findings = f"\n### {section_name}\n"
            section_findings += f"Goal: {section_info['goal']}\n\n"

            if results:
                for i, doc in enumerate(results, 1):
                    content = doc.page_content[:400]
                    metadata = doc.metadata
                    section_findings += f"**{metadata.get('file_path', 'Unknown')}**\n"
                    section_findings += f"  Type: {metadata.get('node_type', 'Unknown')}\n"
                    section_findings += f"  {content}...\n\n"
            else:
                section_findings += "No results found.\n\n"

            findings.append(section_findings)

        all_findings = "\n".join(findings)

        # Synthesize findings with LLM
        synthesis_prompt = f"""Analyze this {project_name} codebase based on the search results below.

{all_findings}

Provide a comprehensive architecture analysis with:
- Executive summary
- Architecture patterns
- Layered structure
- Key components
- Data flow
- Technology stack
- Strengths
- Recommendations

Use actual class names and specifics from the search results."""

        response = self.llm.invoke(synthesis_prompt)
        return response.content
