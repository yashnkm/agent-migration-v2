"""
Framework Detection using LangChain create_agent with structured output
Modern approach using agent with ToolStrategy for Pydantic model output
"""
import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.knowledge_graph.graph import KnowledgeGraph
from src.inference.graph_summarizer import GraphSummarizer


class FrameworkCandidate(BaseModel):
    """Single framework candidate"""
    name: str = Field(description="Framework name (e.g., Spring Boot, Struts, JAX-RS)")
    version: Optional[str] = Field(default=None, description="Estimated version if detectable")
    confidence: float = Field(description="Confidence score 0.0 to 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief explanation why this framework was detected")


class FrameworkDetectionResult(BaseModel):
    """Framework detection result with structured output"""
    primary_framework: FrameworkCandidate
    secondary_frameworks: List[FrameworkCandidate] = Field(
        default_factory=list,
        description="Other frameworks detected with lower confidence"
    )
    architecture_patterns: List[str] = Field(
        default_factory=list,
        description="Detected patterns like MVC, REST, Microservices"
    )


class FrameworkDetectorV2:
    """
    Framework detector using LangChain with_structured_output
    Uses Gemini with Pydantic model for reliable structured extraction
    """

    def __init__(self):
        """Initialize framework detector"""
        load_dotenv()

        # Get API key - try multiple env var names
        self.api_key = (
            os.getenv('CODEBASE_GEMINI_KEY') or
            os.getenv('GOOGLE_GENAI_API_KEY') or
            os.getenv('GOOGLE_API_KEY')
        )

        if not self.api_key:
            raise ValueError("CODEBASE_GEMINI_KEY, GOOGLE_GENAI_API_KEY, or GOOGLE_API_KEY must be set in .env")

        # Get model name from env or use default
        model_name = os.getenv('CODEBASE_GEMINI_MODEL', 'gemini-2.0-flash-exp')

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=0
        )

    def detect_framework(self, knowledge_graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        Detect framework using LLM with structured output

        Returns:
            {
                'framework': str,
                'confidence': float,
                'reasoning': str,
                'architecture_patterns': List[str],
                'source': 'LLM'
            }
        """
        try:
            # Create structured summary
            summarizer = GraphSummarizer(knowledge_graph)
            signature = summarizer.create_framework_signature()

            # Create the analysis prompt
            analysis_prompt = self._create_analysis_prompt(signature)

            # Create LLM with structured output
            structured_llm = self.llm.with_structured_output(FrameworkDetectionResult)

            # Invoke LLM
            detection: FrameworkDetectionResult = structured_llm.invoke(analysis_prompt)

            # Convert to output format
            return {
                'framework': detection.primary_framework.name,
                'confidence': detection.primary_framework.confidence,
                'reasoning': detection.primary_framework.reasoning,
                'architecture_patterns': detection.architecture_patterns,
                'source': 'LLM',
                'secondary_frameworks': [
                    {
                        'name': f.name,
                        'confidence': f.confidence,
                        'reasoning': f.reasoning
                    }
                    for f in detection.secondary_frameworks
                ]
            }

        except Exception as e:
            print(f"LLM detection failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to heuristic
            return self._heuristic_detection(knowledge_graph)

    def _create_analysis_prompt(self, signature: Dict[str, Any]) -> str:
        """Create comprehensive analysis prompt from structured summary"""

        prompt = f"""You are a Java framework expert. Analyze this codebase structure and identify the framework(s) being used.

CODEBASE STRUCTURE ANALYSIS:

Statistics:
- Total Classes: {signature['total_classes']}
- Java Types: {signature['java_type_breakdown']}
- Methods: {signature['total_methods']}
- Fields: {signature['total_fields']}

Top Annotations (with counts):
{json.dumps(signature['annotation_counts'], indent=2)}

Package Analysis:
{json.dumps(signature['package_analysis'], indent=2)}

Inheritance Patterns:
{json.dumps(signature['inheritance_patterns'], indent=2)}

Interface Implementations:
{json.dumps(signature['interface_patterns'], indent=2)}

REST Endpoints:
{json.dumps(signature['endpoint_patterns'], indent=2)}

Dependency Injection:
{json.dumps(signature['dependency_injection_hints'], indent=2)}

Sample Classes:
{json.dumps(signature['sample_classes'], indent=2)}

FRAMEWORKS TO CONSIDER:
- Spring Boot: @RestController, @Service, @Repository, @Autowired, JpaRepository
- Struts: @Action, @Result, @Namespace, extends Action
- JAX-RS: @Path, @GET, @POST, @Produces, @Consumes
- Jakarta EE: @Stateless, @Entity, @PersistenceContext
- Micronaut: @Controller, @Get, @Singleton
- Quarkus: @Path, @ApplicationScoped, @Inject
- Play Framework: Different patterns, no typical annotations
- Plain Java: No framework-specific patterns

INSTRUCTIONS:
1. Analyze ALL the patterns above
2. Identify the primary framework with confidence (0.0-1.0)
3. Be confident (>0.85) ONLY if evidence is strong
4. List secondary frameworks if multiple are present
5. Identify architecture patterns (MVC, REST, Microservices, etc.)
6. Provide clear reasoning based on the evidence

Analyze and provide structured framework detection result."""

        return prompt

    def _heuristic_detection(self, knowledge_graph: KnowledgeGraph) -> Dict[str, Any]:
        """Fallback heuristic detection if agent fails"""

        # Simple annotation-based scoring
        scores = {
            'Spring Boot': 0,
            'Struts': 0,
            'JAX-RS': 0,
            'Jakarta EE': 0,
            'Plain Java': 0
        }

        # Count framework-specific annotations
        for class_node in knowledge_graph.classes.values():
            annotations = set(class_node.annotations)

            if 'RestController' in annotations or 'Controller' in annotations:
                scores['Spring Boot'] += 10
            if 'Service' in annotations:
                scores['Spring Boot'] += 5
            if 'Repository' in annotations:
                scores['Spring Boot'] += 5
            if 'Autowired' in annotations:
                scores['Spring Boot'] += 3

            if 'Action' in annotations or 'Actions' in annotations:
                scores['Struts'] += 10
            if 'Namespace' in annotations:
                scores['Struts'] += 5

            if 'Path' in annotations:
                scores['JAX-RS'] += 10
            if any(a in annotations for a in ['GET', 'POST', 'PUT', 'DELETE']):
                scores['JAX-RS'] += 5

            if 'Stateless' in annotations or 'Stateful' in annotations:
                scores['Jakarta EE'] += 10

        # Determine winner
        max_score = max(scores.values())

        if max_score == 0:
            framework = 'Plain Java'
            confidence = 0.5
        else:
            framework = max(scores, key=scores.get)
            confidence = min(max_score / 30.0, 1.0)  # Normalize

        return {
            'framework': framework,
            'confidence': confidence,
            'reasoning': f'Heuristic detection based on annotation patterns (score: {max_score})',
            'architecture_patterns': [],
            'source': 'HEURISTIC'
        }
