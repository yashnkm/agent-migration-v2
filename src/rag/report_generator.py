"""
Architecture Report Generator
Generates comprehensive architecture reports and Mermaid diagrams
Uses Planning Architecture Agent for systematic multi-step analysis
"""
import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from src.rag.agents.framework_aware_architecture_agent import FrameworkAwareArchitectureAgent


# Pydantic Models for Structured Output

class LayerInfo(BaseModel):
    """Information about an architectural layer"""
    name: str = Field(description="Layer name (e.g., Presentation, Business, Data)")
    components: List[str] = Field(description="Components in this layer")
    responsibilities: str = Field(description="What this layer does")


class ComponentInfo(BaseModel):
    """Information about a key component"""
    name: str = Field(description="Component name")
    type: str = Field(description="Component type (Controller, Service, Repository, etc.)")
    purpose: str = Field(description="What this component does")
    dependencies: List[str] = Field(default_factory=list, description="What it depends on")


class ArchitectureReport(BaseModel):
    """Complete architecture report"""
    project_name: str = Field(description="Name of the project")
    executive_summary: str = Field(description="High-level overview (2-3 paragraphs)")
    architecture_patterns: List[str] = Field(description="Architecture patterns used (MVC, Layered, etc.)")
    layers: List[LayerInfo] = Field(description="Architectural layers")
    key_components: List[ComponentInfo] = Field(description="Key components")
    data_flow: str = Field(description="How data flows through the system (2-3 paragraphs)")
    technology_stack: List[str] = Field(description="Technologies and frameworks used")
    strengths: List[str] = Field(description="Architecture strengths")
    recommendations: List[str] = Field(description="Improvement recommendations")


class MermaidDiagram(BaseModel):
    """Mermaid diagram with metadata"""
    diagram_type: str = Field(description="Type: flowchart, classDiagram, or sequenceDiagram")
    title: str = Field(description="Diagram title")
    mermaid_code: str = Field(description="Valid Mermaid syntax")
    description: str = Field(description="What the diagram shows")


class ArchitectureReportGenerator:
    """Generates comprehensive architecture reports"""

    def __init__(self, vectorstore: FAISS):
        """
        Initialize report generator

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
            temperature=0.3  # Slightly creative but consistent
        )

        self.vectorstore = vectorstore

    def generate_report(self, project_name: str = "Java Project") -> ArchitectureReport:
        """
        Generate comprehensive architecture report using Planning Agent

        Args:
            project_name: Name of the project

        Returns:
            ArchitectureReport with all details
        """
        print("Starting framework-aware architecture analysis...")
        print("Step 1: Detecting framework...")
        print("Step 2: Framework-specific RAG queries...")
        print("Step 3: Comprehensive analysis...")

        # Use Framework-Aware Architecture Agent
        framework_agent = FrameworkAwareArchitectureAgent(self.vectorstore)

        # Get framework-aware analysis
        analysis_result = framework_agent.analyze_architecture(project_name)

        # Parse the agent's analysis into structured report
        print("Converting analysis into structured report...")
        report = self._parse_analysis_to_report(
            project_name,
            analysis_result['framework'],
            analysis_result['analysis']
        )

        print("✓ Architecture report generated!")
        return report

    def _parse_analysis_to_report(self, project_name: str, framework: str, analysis: str) -> ArchitectureReport:
        """
        Parse agent's analysis into structured ArchitectureReport

        Args:
            project_name: Project name
            framework: Detected framework
            analysis: Agent's comprehensive analysis text

        Returns:
            Structured ArchitectureReport
        """
        # Create prompt to convert analysis to structured format
        prompt = f"""Convert this {framework} architecture analysis into a structured report.

PROJECT: {project_name}
FRAMEWORK: {framework}

COMPREHENSIVE ANALYSIS:
{analysis}

Extract and structure the information into the required format.
Include {framework}-specific details in the architecture patterns and technology stack.
If information is missing, make reasonable inferences based on what was found."""

        # Use structured output
        structured_llm = self.llm.with_structured_output(ArchitectureReport)
        report = structured_llm.invoke(prompt)

        return report

    def _gather_architectural_context(self) -> str:
        """Gather relevant context from vectorstore"""
        queries = [
            "controller service repository architecture",
            "entity classes domain model",
            "REST API endpoints",
            "dependency injection",
            "package structure organization"
        ]

        all_docs = []
        for query in queries:
            docs = self.vectorstore.similarity_search(query, k=10)
            all_docs.extend(docs)

        # Create context string
        context = "\n\n".join([
            f"Document {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(all_docs[:30])  # Limit to 30 docs
        ])

        return context

    def _create_report_prompt(self, project_name: str, context: str) -> str:
        """Create prompt for report generation"""
        prompt = f"""You are an expert software architect. Analyze this Java codebase and create a comprehensive architecture report.

PROJECT NAME: {project_name}

CODEBASE INFORMATION:
{context}

Generate a detailed architecture report with:

1. **Executive Summary**: High-level overview of the architecture (2-3 paragraphs)

2. **Architecture Patterns**: Identify patterns like:
   - Layered Architecture
   - MVC (Model-View-Controller)
   - Microservices vs Monolith
   - Repository Pattern
   - Dependency Injection
   - Others you identify

3. **Layers**: Break down the architectural layers:
   - Presentation Layer (Controllers, REST endpoints)
   - Business Layer (Services, business logic)
   - Data Access Layer (Repositories, DAOs)
   - Domain Layer (Entities, models)
   - List components in each layer

4. **Key Components**: Identify 5-10 most important components and their purpose

5. **Data Flow**: Explain how data flows through the system (user request → response)

6. **Technology Stack**: List frameworks, libraries, patterns used

7. **Strengths**: What's good about this architecture?

8. **Recommendations**: What could be improved?

Be specific. Cite actual class names from the codebase. Provide actionable insights.

Generate the structured architecture report."""

        return prompt


class MermaidDiagramGenerator:
    """Generates Mermaid diagrams from architecture reports"""

    def __init__(self):
        """Initialize diagram generator"""
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
            temperature=0.1  # Low temp for consistent diagrams
        )

    def generate_component_diagram(self, report: ArchitectureReport) -> MermaidDiagram:
        """
        Generate component/layered architecture diagram

        Args:
            report: Architecture report

        Returns:
            MermaidDiagram with flowchart showing layers
        """
        print("Generating component architecture diagram...")

        prompt = f"""You are a Mermaid diagram expert. Generate ONLY valid Mermaid flowchart syntax.

PROJECT: {report.project_name}

ARCHITECTURE PATTERNS: {', '.join(report.architecture_patterns)}

LAYERS:
{self._format_layers(report.layers)}

KEY COMPONENTS:
{self._format_components(report.key_components)}

CRITICAL INSTRUCTIONS:
- Generate ONLY the Mermaid diagram code
- Do NOT include explanations, comments, or markdown formatting
- Do NOT wrap in code blocks or backticks
- Start directly with "graph TD" or "graph LR"
- Use simple, valid Mermaid syntax only
- Keep node IDs simple (A, B, C, etc.)
- Use square brackets for node labels: A[Label]
- Use --> for connections
- Test your syntax mentally before outputting

VALID EXAMPLE (use this exact format):
graph TD
    subgraph "Presentation Layer"
        A[UserController]
        B[OrderController]
    end
    subgraph "Business Layer"
        C[UserService]
        D[OrderService]
    end
    subgraph "Data Layer"
        E[UserRepository]
        F[OrderRepository]
    end
    A --> C
    B --> D
    C --> E
    D --> F

WHAT NOT TO DO:
❌ Do NOT add: "Here's the diagram:", "```mermaid", explanations, or any extra text
❌ Do NOT use special characters in node IDs (use A-Z, 0-9 only)
❌ Do NOT create invalid syntax or broken connections
❌ Do NOT add comments with %% inside the diagram

OUTPUT REQUIREMENTS:
- Start with: graph TD
- Use actual component names from the project
- Keep it simple and valid
- Maximum 15-20 nodes for clarity
- Only output the diagram code, nothing else"""

        structured_llm = self.llm.with_structured_output(MermaidDiagram)
        diagram = structured_llm.invoke(prompt)

        print("✓ Component diagram generated!")
        return diagram

    def generate_class_diagram(self, report: ArchitectureReport) -> MermaidDiagram:
        """
        Generate class diagram showing entities

        Args:
            report: Architecture report

        Returns:
            MermaidDiagram with class diagram
        """
        print("Generating class diagram...")

        prompt = f"""You are a Mermaid diagram expert. Generate ONLY valid Mermaid class diagram syntax.

PROJECT: {report.project_name}

KEY COMPONENTS (focus on entities/domain models):
{self._format_components(report.key_components)}

CRITICAL INSTRUCTIONS:
- Generate ONLY the Mermaid classDiagram code
- Do NOT include explanations, comments, or markdown formatting
- Do NOT wrap in code blocks or backticks
- Start directly with "classDiagram"
- Use simple, valid Mermaid syntax only
- Keep class names simple (no special characters except underscore)
- Use double curly braces for class body: class Name {{{{ }}}}
- Show 3-5 key attributes per class max
- Use standard relationship syntax
- Test your syntax mentally before outputting

VALID EXAMPLE (use this exact format):
classDiagram
    class User {{
        +Long id
        +String username
        +String email
    }}
    class Order {{
        +Long id
        +Date orderDate
        +Double totalAmount
    }}
    class Product {{
        +Long id
        +String name
        +Double price
    }}
    User "1" --> "*" Order : places
    Order "*" --> "*" Product : contains

WHAT NOT TO DO:
❌ Do NOT add: "Here's the diagram:", "```mermaid", explanations, or any extra text
❌ Do NOT use special characters in class names (use letters, numbers, underscore only)
❌ Do NOT create invalid syntax or broken relationships
❌ Do NOT add comments with %% inside the diagram
❌ Do NOT use complex generic types (keep it simple)
❌ Do NOT add methods (only show key attributes)

OUTPUT REQUIREMENTS:
- Start with: classDiagram
- Use actual entity names from the project
- Show only 3-5 most important attributes per class
- Use simple types: Long, String, Integer, Boolean, Date
- Maximum 8-10 classes for clarity
- Use standard relationships: -->, --|>, o--, *--
- Only output the diagram code, nothing else"""

        structured_llm = self.llm.with_structured_output(MermaidDiagram)
        diagram = structured_llm.invoke(prompt)

        print("✓ Class diagram generated!")
        return diagram

    def _format_layers(self, layers: List[LayerInfo]) -> str:
        """Format layers for prompt"""
        return "\n".join([
            f"- {layer.name}: {', '.join(layer.components[:5])}"
            for layer in layers
        ])

    def _format_components(self, components: List[ComponentInfo]) -> str:
        """Format components for prompt"""
        return "\n".join([
            f"- {comp.name} ({comp.type}): {comp.purpose}"
            for comp in components[:10]
        ])


# Convenience functions

def generate_architecture_report(vectorstore: FAISS, project_name: str = "Java Project") -> ArchitectureReport:
    """Generate architecture report"""
    generator = ArchitectureReportGenerator(vectorstore)
    return generator.generate_report(project_name)


def generate_diagrams(report: ArchitectureReport) -> dict:
    """Generate all diagrams"""
    generator = MermaidDiagramGenerator()

    return {
        "component": generator.generate_component_diagram(report),
        "class": generator.generate_class_diagram(report)
    }
