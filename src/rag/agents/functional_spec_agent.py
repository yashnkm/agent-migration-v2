"""
Functional Specification Agent
Generates functional requirements by tracing presentation components through all layers
Uses RAG to query relationships and LLM to synthesize specifications
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS

from src.inference.presentation_layer_extractor import ControllerInfo, EndpointInfo


@dataclass
class DataModelField:
    """Field in a data model/entity"""
    name: str
    type: str
    constraints: List[str] = field(default_factory=list)


@dataclass
class DataModel:
    """Data model/entity information"""
    name: str
    fields: List[DataModelField] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)


@dataclass
class BusinessRule:
    """Business rule extracted from code"""
    description: str
    source: str  # Which method/class this rule comes from


@dataclass
class FeatureSpec:
    """Functional specification for a single feature/component"""
    feature_name: str
    overview: str
    endpoints: List[Dict[str, str]]  # method, path, description, handler
    data_flow: str  # Text description of data flow
    data_models: List[DataModel]
    business_rules: List[BusinessRule]
    dependencies: List[str]
    source_component: str  # Original controller/action name


@dataclass
class ProjectSpec:
    """Complete project functional specification"""
    project_name: str
    generated_date: str
    total_features: int
    total_endpoints: int
    features: List[FeatureSpec]
    cross_cutting_concerns: List[str]
    entity_relationships: str  # Mermaid diagram


class FunctionalSpecAgent:
    """
    Agent that generates functional specifications by tracing
    presentation components through all architectural layers
    """

    def __init__(self, vectorstore: FAISS):
        """
        Initialize functional spec agent

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
            temperature=0.3
        )

        self.vectorstore = vectorstore

    def analyze_component(self, controller: ControllerInfo) -> FeatureSpec:
        """
        Analyze a single presentation component and generate functional spec

        Args:
            controller: Controller/Action info from presentation layer

        Returns:
            FeatureSpec for this component
        """
        print(f"\n{'='*60}")
        print(f"Analyzing: {controller.name}")
        print(f"{'='*60}")

        # Step 1: Get detailed controller information
        print("Step 1: Analyzing controller/action...")
        controller_details = self._query_controller_details(controller)

        # Step 2: Find service dependencies
        print("Step 2: Tracing service layer...")
        services_info = self._query_services(controller)

        # Step 3: Find repository/DAO layer
        print("Step 3: Tracing data access layer...")
        repositories_info = self._query_repositories(services_info)

        # Step 4: Find entities/data models
        print("Step 4: Analyzing entity layer...")
        entities_info = self._query_entities(repositories_info)

        # Step 5: Synthesize functional specification
        print("Step 5: Generating functional specification...")
        spec = self._synthesize_spec(
            controller,
            controller_details,
            services_info,
            repositories_info,
            entities_info
        )

        print(f"✓ Completed analysis for {controller.name}")
        return spec

    def analyze_full_project(
        self,
        controllers: List[ControllerInfo],
        project_name: str = "Java Project"
    ) -> ProjectSpec:
        """
        Analyze all presentation components and generate complete project spec

        Args:
            controllers: List of all controllers/actions
            project_name: Name of the project

        Returns:
            Complete ProjectSpec
        """
        print(f"\n{'='*60}")
        print(f"Generating Complete Functional Specification")
        print(f"Project: {project_name}")
        print(f"Components to analyze: {len(controllers)}")
        print(f"{'='*60}")

        # Analyze each component
        features = []
        for i, controller in enumerate(controllers, 1):
            print(f"\n[{i}/{len(controllers)}] Processing {controller.name}...")
            try:
                spec = self.analyze_component(controller)
                features.append(spec)
            except Exception as e:
                print(f"  ⚠️ Error analyzing {controller.name}: {str(e)}")
                continue

        # Calculate totals
        total_endpoints = sum(len(f.endpoints) for f in features)

        # Generate cross-cutting concerns
        print("\nAnalyzing cross-cutting concerns...")
        cross_cutting = self._analyze_cross_cutting_concerns()

        # Generate entity relationship diagram
        print("Generating entity relationships...")
        er_diagram = self._generate_entity_relationships(features)

        # Get current date
        from datetime import datetime
        generated_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        project_spec = ProjectSpec(
            project_name=project_name,
            generated_date=generated_date,
            total_features=len(features),
            total_endpoints=total_endpoints,
            features=features,
            cross_cutting_concerns=cross_cutting,
            entity_relationships=er_diagram
        )

        print(f"\n{'='*60}")
        print(f"✓ Complete! Generated specs for {len(features)} features")
        print(f"{'='*60}")

        return project_spec

    def _query_controller_details(self, controller: ControllerInfo) -> str:
        """Query RAG for detailed controller information"""
        query = f"""
        {controller.name} class methods annotations
        @RequestMapping @GetMapping @PostMapping
        REST endpoints handler methods parameters
        """

        results = self.vectorstore.similarity_search(query, k=8)
        return self._format_results(results)

    def _query_services(self, controller: ControllerInfo) -> str:
        """Query RAG for service layer dependencies"""
        # Query for services used by this controller
        query = f"""
        {controller.name} @Autowired @Inject service
        {' '.join(controller.dependencies)}
        business logic validation
        """

        results = self.vectorstore.similarity_search(query, k=10)
        return self._format_results(results)

    def _query_repositories(self, services_info: str) -> str:
        """Query RAG for repository/DAO layer"""
        query = f"""
        @Repository JpaRepository CrudRepository DAO
        database save find delete update
        data access layer persistence
        """

        results = self.vectorstore.similarity_search(query, k=10)
        return self._format_results(results)

    def _query_entities(self, repositories_info: str) -> str:
        """Query RAG for entity/model layer"""
        query = f"""
        @Entity @Table domain model
        fields attributes columns
        @Id @Column @ManyToOne @OneToMany
        data model entity class
        """

        results = self.vectorstore.similarity_search(query, k=10)
        return self._format_results(results)

    def _format_results(self, results) -> str:
        """Format RAG results into string"""
        formatted = []
        for i, doc in enumerate(results, 1):
            content = doc.page_content[:500]  # Limit content length
            metadata = doc.metadata
            formatted.append(f"""
Result {i}:
File: {metadata.get('file_path', 'Unknown')}
Type: {metadata.get('node_type', 'Unknown')}
Content:
{content}
""")
        return "\n".join(formatted)

    def _synthesize_spec(
        self,
        controller: ControllerInfo,
        controller_details: str,
        services_info: str,
        repositories_info: str,
        entities_info: str
    ) -> FeatureSpec:
        """Use LLM to synthesize functional specification from gathered information"""

        # Format endpoints for prompt
        endpoints_str = "\n".join([
            f"- {e.http_method} {e.path} → {e.handler_method}()"
            for e in controller.endpoints
        ])

        prompt = f"""You are a technical writer creating functional specifications from code analysis.

COMPONENT: {controller.name}
TYPE: {controller.type}
BASE PATH: {controller.base_path}

ENDPOINTS:
{endpoints_str}

DEPENDENCIES: {', '.join(controller.dependencies) if controller.dependencies else 'None found'}

=== CONTROLLER LAYER ANALYSIS ===
{controller_details}

=== SERVICE LAYER ANALYSIS ===
{services_info}

=== REPOSITORY LAYER ANALYSIS ===
{repositories_info}

=== ENTITY LAYER ANALYSIS ===
{entities_info}

Based on this code analysis, generate a functional specification with:

1. **Feature Name**: A clear, business-friendly name for this feature (e.g., "User Management", "Order Processing")

2. **Overview**: 2-3 sentences describing what this feature does from a business perspective

3. **Endpoints Description**: For each endpoint, provide:
   - HTTP Method and Path
   - Business description of what it does
   - Key parameters and return values

4. **Data Flow**: Describe how data flows through the layers:
   - Controller receives request
   - Service processes business logic
   - Repository accesses data
   - Entity represents data

5. **Data Models**: List the main entities/models with their key fields and types

6. **Business Rules**: Extract any business rules, validations, or constraints from the code:
   - Validation rules
   - Business logic conditions
   - Data constraints

7. **Dependencies**: List external dependencies (services, libraries)

IMPORTANT:
- Use actual class names, method names, and field names from the analysis
- Be specific and cite the code
- If information is not found, say "Not identified in analysis"
- Focus on functional/business aspects, not technical implementation

Generate the specification:"""

        response = self.llm.invoke(prompt)
        spec_text = response.content

        # Parse LLM response into structured FeatureSpec
        # For now, we'll create a simplified version
        # In production, you'd parse the LLM output more carefully

        feature_spec = FeatureSpec(
            feature_name=self._extract_feature_name(controller.name),
            overview=self._extract_section(spec_text, "Overview", "Endpoints"),
            endpoints=[
                {
                    "method": e.http_method,
                    "path": e.path,
                    "handler": e.handler_method,
                    "description": f"Handles {e.http_method} requests to {e.path}"
                }
                for e in controller.endpoints
            ],
            data_flow=self._extract_section(spec_text, "Data Flow", "Data Models"),
            data_models=self._extract_data_models(spec_text),
            business_rules=self._extract_business_rules(spec_text),
            dependencies=controller.dependencies,
            source_component=controller.name
        )

        # Store full LLM response for complete output
        feature_spec.full_spec_text = spec_text

        return feature_spec

    def _extract_feature_name(self, controller_name: str) -> str:
        """Extract feature name from controller name"""
        # UserController → User Management
        # OrderAction → Order Processing
        name = controller_name.replace("Controller", "").replace("Action", "").replace("Resource", "").replace("Servlet", "")
        return f"{name} Management"

    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract a section from LLM response"""
        try:
            start_idx = text.find(start_marker)
            end_idx = text.find(end_marker, start_idx + len(start_marker))

            if start_idx != -1 and end_idx != -1:
                section = text[start_idx:end_idx].strip()
                # Remove the marker itself
                section = section.replace(f"**{start_marker}**:", "").replace(f"{start_marker}:", "").strip()
                return section[:500]  # Limit length
            elif start_idx != -1:
                section = text[start_idx:start_idx + 500].strip()
                return section

            return "Not identified in analysis"
        except:
            return "Not identified in analysis"

    def _extract_data_models(self, text: str) -> List[DataModel]:
        """Extract data models from LLM response"""
        # Simplified extraction - in production, parse more carefully
        models = []

        # Look for entity mentions
        if "Entity" in text or "Model" in text:
            models.append(DataModel(
                name="Extracted from analysis",
                fields=[],
                relationships=[]
            ))

        return models

    def _extract_business_rules(self, text: str) -> List[BusinessRule]:
        """Extract business rules from LLM response"""
        rules = []

        # Look for common business rule indicators
        rule_indicators = ["must", "should", "required", "cannot", "validation", "constraint"]

        lines = text.split("\n")
        for line in lines:
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in rule_indicators):
                if len(line.strip()) > 10:  # Meaningful content
                    rules.append(BusinessRule(
                        description=line.strip()[:200],
                        source="Code analysis"
                    ))

        return rules[:10]  # Limit to 10 rules

    def _analyze_cross_cutting_concerns(self) -> List[str]:
        """Analyze cross-cutting concerns like security, logging, etc."""
        concerns = []

        # Query for security
        security_results = self.vectorstore.similarity_search(
            "@EnableWebSecurity @PreAuthorize JWT authentication authorization security",
            k=3
        )
        if security_results:
            concerns.append("Authentication and Authorization (Security layer detected)")

        # Query for logging
        logging_results = self.vectorstore.similarity_search(
            "Logger @Slf4j logging log.info log.error",
            k=3
        )
        if logging_results:
            concerns.append("Logging and Monitoring")

        # Query for exception handling
        exception_results = self.vectorstore.similarity_search(
            "@ControllerAdvice @ExceptionHandler GlobalExceptionHandler",
            k=3
        )
        if exception_results:
            concerns.append("Global Exception Handling")

        # Query for transactions
        transaction_results = self.vectorstore.similarity_search(
            "@Transactional transaction management",
            k=3
        )
        if transaction_results:
            concerns.append("Transaction Management")

        return concerns if concerns else ["No specific cross-cutting concerns identified"]

    def _generate_entity_relationships(self, features: List[FeatureSpec]) -> str:
        """Generate Mermaid ER diagram for entities"""
        # Query for all entities
        entity_results = self.vectorstore.similarity_search(
            "@Entity @Table @ManyToOne @OneToMany @ManyToMany relationships",
            k=15
        )

        if not entity_results:
            return "No entity relationships identified"

        # Format entity info for LLM
        entity_info = self._format_results(entity_results)

        prompt = f"""Based on these entity classes, generate a Mermaid ER diagram showing relationships:

{entity_info}

Generate ONLY valid Mermaid erDiagram syntax. Example format:
erDiagram
    User ||--o{{ Order : places
    Order ||--|{{ OrderItem : contains
    Product ||--o{{ OrderItem : "ordered in"

Rules:
- Use actual entity names from the analysis
- Show relationships: ||--o{{ (one-to-many), ||--|| (one-to-one), }}--{{ (many-to-many)
- Keep it simple, max 10 relationships
- Output ONLY the Mermaid code, no explanations

Generate the diagram:"""

        response = self.llm.invoke(prompt)
        return response.content.strip()


def format_feature_spec_markdown(spec: FeatureSpec) -> str:
    """Format a single feature spec as Markdown"""
    md = f"""## {spec.feature_name}

### Overview
{spec.overview if hasattr(spec, 'overview') else getattr(spec, 'full_spec_text', 'No overview available')[:500]}

### Endpoints
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
"""

    for ep in spec.endpoints:
        md += f"| {ep['method']} | {ep['path']} | {ep['handler']}() | {ep.get('description', '')} |\n"

    md += f"""
### Data Flow
{spec.data_flow if spec.data_flow else 'See detailed analysis below'}

### Business Rules
"""

    if spec.business_rules:
        for rule in spec.business_rules:
            md += f"- {rule.description}\n"
    else:
        md += "- No specific business rules identified\n"

    md += f"""
### Dependencies
{', '.join([f'`{dep}`' for dep in spec.dependencies]) if spec.dependencies else 'None identified'}

---
"""

    # Add full LLM analysis if available
    if hasattr(spec, 'full_spec_text'):
        md += f"""
### Detailed Analysis
{spec.full_spec_text}

---
"""

    return md


def format_project_spec_markdown(project_spec: ProjectSpec) -> str:
    """Format complete project spec as Markdown document"""
    md = f"""# {project_spec.project_name}
## Functional Specification Document

**Generated**: {project_spec.generated_date}
**Total Features**: {project_spec.total_features}
**Total Endpoints**: {project_spec.total_endpoints}

---

## Table of Contents
"""

    # Add TOC
    for i, feature in enumerate(project_spec.features, 1):
        md += f"{i}. [{feature.feature_name}](#{feature.feature_name.lower().replace(' ', '-')})\n"

    md += "\n---\n\n"

    # Add each feature
    for feature in project_spec.features:
        md += format_feature_spec_markdown(feature)

    # Add cross-cutting concerns
    md += """## Cross-Cutting Concerns

"""
    for concern in project_spec.cross_cutting_concerns:
        md += f"- {concern}\n"

    # Add entity relationships
    md += f"""
## Entity Relationships

```mermaid
{project_spec.entity_relationships}
```

---

*Generated by Java Codebase Analyzer*
"""

    return md


# Convenience functions

def create_functional_spec_agent(vectorstore: FAISS) -> FunctionalSpecAgent:
    """Create functional spec agent"""
    return FunctionalSpecAgent(vectorstore)


def generate_component_spec(
    vectorstore: FAISS,
    controller: ControllerInfo
) -> FeatureSpec:
    """Generate spec for single component"""
    agent = FunctionalSpecAgent(vectorstore)
    return agent.analyze_component(controller)


def generate_project_spec(
    vectorstore: FAISS,
    controllers: List[ControllerInfo],
    project_name: str = "Java Project"
) -> ProjectSpec:
    """Generate complete project specification"""
    agent = FunctionalSpecAgent(vectorstore)
    return agent.analyze_full_project(controllers, project_name)
