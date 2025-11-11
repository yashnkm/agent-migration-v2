"""
Framework Detection using Gemini 2.5 Flash via LangChain
Detects Java framework from code patterns
"""
import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.knowledge_graph.graph import KnowledgeGraph


class FrameworkCandidate(BaseModel):
    """Single framework candidate"""
    name: str = Field(description="Framework name (e.g., Spring Boot, Jakarta EE)")
    version: Optional[str] = Field(description="Estimated version if detectable")
    confidence: float = Field(description="Confidence score 0.0 to 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief explanation why this framework was detected")


class FrameworkDetectionResult(BaseModel):
    """Framework detection result"""
    primary_framework: FrameworkCandidate
    secondary_frameworks: List[FrameworkCandidate] = Field(default_factory=list)
    architecture_patterns: List[str] = Field(default_factory=list,
                                             description="Detected patterns like MVC, REST, Microservices")


class FrameworkDetector:
    """
    Detects Java framework using Gemini 2.5 Flash
    Uses LangChain for structured output
    """

    def __init__(self, confidence_threshold: float = 0.85):
        """
        Initialize framework detector

        Args:
            confidence_threshold: Threshold for auto-confirmation (default 0.85)
        """
        load_dotenv()

        self.confidence_threshold = confidence_threshold
        # Try unique key first, fallback to standard key for compatibility
        self.api_key = os.getenv("CODEBASE_GEMINI_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = os.getenv("CODEBASE_GEMINI_MODEL", "gemini-2.5-flash")

        if not self.api_key:
            print("⚠️  WARNING: CODEBASE_GEMINI_KEY not found in .env")
            print("   Framework detection will not be available")
            self.llm = None
        else:
            # Initialize Gemini (model from env)
            print(f"🤖 Initializing {self.model_name}...")
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=2048
            )

        # Setup output parser
        self.parser = PydanticOutputParser(pydantic_object=FrameworkDetectionResult)

    def detect_framework(self, knowledge_graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        Detect framework from knowledge graph

        Returns:
            {
                'framework': str,
                'confidence': float,
                'needs_confirmation': bool,
                'candidates': List[FrameworkCandidate],
                'source': 'LLM' | 'HEURISTIC'
            }
        """

        if not self.llm:
            # Fall back to heuristics only
            return self._heuristic_detection(knowledge_graph)

        # Step 1: Prepare sample for LLM
        sample = self._prepare_sample(knowledge_graph)

        # Step 2: Ask Gemini
        try:
            result = self._query_gemini(sample)

            # Step 3: Make decision based on confidence
            return self._make_decision(result)

        except Exception as e:
            print(f"⚠️  LLM detection failed: {e}")
            print("   Falling back to heuristics...")
            return self._heuristic_detection(knowledge_graph)

    def _prepare_sample(self, knowledge_graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        Extract small representative sample from knowledge graph
        Only send essentials to LLM (keep it fast and cheap)
        """

        # Collect unique annotations (limit 50)
        class_annotations = set()
        method_annotations = set()

        for class_node in knowledge_graph.classes.values():
            class_annotations.update(class_node.annotations)

        for method_node in knowledge_graph.methods.values():
            method_annotations.update(method_node.annotations)

        # Get class name patterns (limit 20)
        class_patterns = [
            class_node.name
            for class_node in list(knowledge_graph.classes.values())[:20]
        ]

        # Get package structure (top-level only, limit 10)
        packages = list(set(
            '.'.join(class_node.package.split('.')[:3])
            for class_node in knowledge_graph.classes.values()
            if class_node.package
        ))[:10]

        sample = {
            "class_annotations": sorted(list(class_annotations))[:50],
            "method_annotations": sorted(list(method_annotations))[:30],
            "class_names": class_patterns,
            "packages": packages,
            "stats": knowledge_graph.get_stats()
        }

        return sample

    def _query_gemini(self, sample: Dict[str, Any]) -> FrameworkDetectionResult:
        """Query Gemini 2.5 Flash for framework detection"""

        # Create prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a Java framework expert. Analyze code samples and identify the framework(s) being used.

Be confident ONLY if evidence is strong. Give lower confidence scores for uncertain cases.

Common frameworks:
- Spring Boot (annotations: @RestController, @Service, @Entity, @Repository)
- Jakarta EE / JAX-RS (annotations: @Path, @GET, @POST, @Stateless)
- Micronaut (annotations: @Controller, @Get, @Post, @Singleton)
- Quarkus (annotations: @Path, @ApplicationScoped, @Inject)
- Struts (annotations: @Action, @Result, @Namespace)
- Play Framework (different patterns)
- Plain Java (no framework-specific annotations)

{format_instructions}"""),
            ("human", """Analyze this Java codebase sample:

Class Annotations: {class_annotations}
Method Annotations: {method_annotations}
Class Name Patterns: {class_names}
Packages: {packages}
Statistics: {stats}

Identify the framework(s) and provide confidence scores.""")
        ])

        # Format sample data
        sample_str = {
            "class_annotations": ", ".join(sample['class_annotations']) if sample['class_annotations'] else "None",
            "method_annotations": ", ".join(sample['method_annotations']) if sample['method_annotations'] else "None",
            "class_names": ", ".join(sample['class_names']) if sample['class_names'] else "None",
            "packages": ", ".join(sample['packages']) if sample['packages'] else "None",
            "stats": json.dumps(sample['stats']),
            "format_instructions": self.parser.get_format_instructions()
        }

        # Create chain
        chain = prompt_template | self.llm | self.parser

        # Execute
        result = chain.invoke(sample_str)

        return result

    def _make_decision(self, result: FrameworkDetectionResult) -> Dict[str, Any]:
        """
        Make decision based on LLM result and confidence thresholds
        """

        primary = result.primary_framework
        secondaries = result.secondary_frameworks

        # High confidence → Auto-confirm
        if primary.confidence >= self.confidence_threshold:
            return {
                'framework': primary.name,
                'version': primary.version,
                'confidence': primary.confidence,
                'reasoning': primary.reasoning,
                'needs_confirmation': False,
                'candidates': [primary] + secondaries,
                'source': 'LLM',
                'architecture_patterns': result.architecture_patterns
            }

        # Medium confidence → Suggest with confirmation
        elif primary.confidence >= 0.60:
            return {
                'framework': primary.name,
                'version': primary.version,
                'confidence': primary.confidence,
                'reasoning': primary.reasoning,
                'needs_confirmation': True,
                'candidates': [primary] + secondaries,
                'source': 'LLM',
                'architecture_patterns': result.architecture_patterns
            }

        # Multiple strong candidates → Human intervention
        elif any(sec.confidence > 0.50 for sec in secondaries):
            return {
                'framework': None,
                'confidence': 0.0,
                'needs_confirmation': True,
                'needs_human_selection': True,
                'candidates': [primary] + secondaries,
                'source': 'LLM_AMBIGUOUS',
                'architecture_patterns': result.architecture_patterns
            }

        # Low confidence → Fall back to heuristics
        else:
            return {
                'framework': primary.name,
                'confidence': primary.confidence,
                'reasoning': primary.reasoning,
                'needs_confirmation': True,
                'candidates': [primary] + secondaries,
                'source': 'LLM_LOW_CONFIDENCE',
                'warning': 'Low confidence detection',
                'architecture_patterns': result.architecture_patterns
            }

    def _heuristic_detection(self, knowledge_graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        Fallback heuristic detection when LLM not available
        """

        sample = self._prepare_sample(knowledge_graph)

        class_anns = set(sample['class_annotations'])
        method_anns = set(sample['method_annotations'])

        scores = {
            'Spring Boot': 0.0,
            'Jakarta EE': 0.0,
            'Micronaut': 0.0,
            'Quarkus': 0.0,
            'Struts': 0.0,
            'Plain Java': 0.0
        }

        # Spring Boot detection
        spring_anns = {'RestController', 'Controller', 'Service', 'Repository',
                       'Entity', 'Component', 'Autowired', 'Configuration'}
        spring_count = len(class_anns & spring_anns)
        scores['Spring Boot'] = min(spring_count / 3.0, 1.0)

        # Jakarta EE detection
        jakarta_anns = {'Path', 'GET', 'POST', 'PUT', 'DELETE', 'Stateless',
                        'Singleton', 'ApplicationScoped'}
        jakarta_count = len(class_anns.union(method_anns) & jakarta_anns)
        scores['Jakarta EE'] = min(jakarta_count / 3.0, 1.0)

        # Micronaut detection
        micronaut_anns = {'Controller', 'Get', 'Post', 'Singleton', 'Inject'}
        micronaut_count = len(class_anns.union(method_anns) & micronaut_anns)
        scores['Micronaut'] = min(micronaut_count / 2.0, 1.0)

        # Plain Java (no framework)
        if not class_anns and not method_anns:
            scores['Plain Java'] = 0.8

        # Get best match
        best_framework = max(scores, key=scores.get)
        best_score = scores[best_framework]

        return {
            'framework': best_framework if best_score > 0.3 else 'Unknown',
            'confidence': best_score,
            'needs_confirmation': best_score < 0.70,
            'candidates': [
                {'name': name, 'confidence': score}
                for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
                if score > 0.1
            ],
            'source': 'HEURISTIC',
            'reasoning': f'Detected based on annotation patterns (score: {best_score:.2f})'
        }


# Example usage and testing
if __name__ == "__main__":
    # Test with mock data
    print("Framework Detector Test")
    print("=" * 50)

    detector = FrameworkDetector()

    if detector.llm:
        print("✅ Gemini API configured")
    else:
        print("⚠️  Gemini API not configured - will use heuristics")
