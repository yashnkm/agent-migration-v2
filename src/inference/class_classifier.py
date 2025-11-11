"""
LLM-Based Class Classification
Uses Gemini to intelligently classify classes based on code patterns and framework context
NO HARDCODING - Pure pattern recognition
"""
import os
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.knowledge_graph.graph import KnowledgeGraph


class ClassClassification(BaseModel):
    """Classification for a single class"""
    class_id: str = Field(description="Class identifier")
    class_type: str = Field(
        description="Type: Entity, Controller, Service, Repository, or UNCLASSIFIED"
    )
    confidence: float = Field(description="Confidence 0.0 to 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Why this classification was chosen")


class ClassificationBatch(BaseModel):
    """Batch classification result"""
    classifications: List[ClassClassification]


class LLMClassClassifier:
    """
    Classifies classes using LLM based on framework context
    Zero hardcoding - pure pattern recognition
    """

    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("CODEBASE_GEMINI_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = os.getenv("CODEBASE_GEMINI_MODEL", "gemini-2.5-flash")

        if not self.api_key:
            print("⚠️  WARNING: CODEBASE_GEMINI_KEY not found in .env")
            print("   Class classification will not be available")
            self.llm = None
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.1,
                max_tokens=4096
            )

        self.parser = PydanticOutputParser(pydantic_object=ClassificationBatch)

    def classify_classes(
        self,
        knowledge_graph: KnowledgeGraph,
        detected_framework: str,
        batch_size: int = 20
    ) -> Dict[str, str]:
        """
        Classify all UNCLASSIFIED classes using LLM

        Args:
            knowledge_graph: The knowledge graph with parsed classes
            detected_framework: The detected framework (e.g., "Struts")
            batch_size: Number of classes to classify per LLM call

        Returns:
            Dict[class_id, class_type]
        """
        if not self.llm:
            print("⚠️  LLM not available - skipping classification")
            return {}

        # Collect UNCLASSIFIED classes
        unclassified = []
        for class_id, class_node in knowledge_graph.classes.items():
            if class_node.class_type == "UNCLASSIFIED":
                unclassified.append({
                    'id': class_id,
                    'node': class_node
                })

        if not unclassified:
            print("✅ No unclassified classes found")
            return {}

        print(f"🔍 Classifying {len(unclassified)} classes using {self.model_name}...")

        # Process in batches
        all_classifications = {}
        for i in range(0, len(unclassified), batch_size):
            batch = unclassified[i:i + batch_size]
            batch_result = self._classify_batch(batch, detected_framework, knowledge_graph)
            all_classifications.update(batch_result)

            print(f"  Processed {min(i + batch_size, len(unclassified))}/{len(unclassified)} classes")

        # Update knowledge graph
        for class_id, class_type in all_classifications.items():
            if class_id in knowledge_graph.classes:
                knowledge_graph.classes[class_id].class_type = class_type

        return all_classifications

    def _classify_batch(
        self,
        batch: List[Dict],
        framework: str,
        knowledge_graph: KnowledgeGraph
    ) -> Dict[str, str]:
        """Classify a batch of classes"""

        # Prepare class information for LLM
        classes_info = []
        for item in batch:
            class_id = item['id']
            class_node = item['node']

            # Count methods and fields
            full_class_name = f"{class_node.package}.{class_node.name}" if class_node.package else class_node.name

            method_count = sum(
                1 for m in knowledge_graph.methods.values()
                if m.class_name == full_class_name
            )

            field_count = sum(
                1 for f in knowledge_graph.fields.values()
                if f.class_name == full_class_name
            )

            # Get method names (first 10)
            method_names = [
                m.name for m in knowledge_graph.methods.values()
                if m.class_name == full_class_name
            ][:10]

            classes_info.append({
                'id': class_id,
                'name': class_node.name,
                'package': class_node.package or '',
                'annotations': class_node.annotations or [],
                'interfaces': class_node.interfaces or [],
                'superclass': class_node.superclass or '',
                'method_count': method_count,
                'field_count': field_count,
                'method_names': method_names,
                'is_abstract': class_node.is_abstract
            })

        # Create prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a Java architecture expert. Classify classes into their architectural roles based on code patterns.

Framework Context: {framework}

Classification Types:
- **Entity**: Domain model/data class (has fields, getters/setters, represents business data)
- **Controller**: Handles requests/actions (handles HTTP, user input, routing)
- **Service**: Business logic layer (orchestrates operations, contains business rules)
- **Repository**: Data access layer (database operations, file I/O, persistence)
- **UNCLASSIFIED**: Utility, helper, or unclear role

Analyze the code patterns:
- Package naming conventions (e.g., .models, .actions, .dao, .service)
- Class naming patterns (e.g., suffixes like Action, Dao, Service, Impl)
- Annotations (framework-specific)
- Method names (e.g., save, get, find = Repository; execute, handle = Controller)
- Field patterns (many fields with getters/setters = Entity)
- Inheritance patterns

{format_instructions}"""),
            ("human", """Classify these classes:

{classes_json}

Return classification for each class with confidence and reasoning.""")
        ])

        try:
            # Execute classification
            chain = prompt_template | self.llm | self.parser

            result = chain.invoke({
                'framework': framework,
                'classes_json': json.dumps(classes_info, indent=2),
                'format_instructions': self.parser.get_format_instructions()
            })

            # Convert to dict
            classifications = {}
            for classification in result.classifications:
                classifications[classification.class_id] = classification.class_type

            return classifications

        except Exception as e:
            print(f"⚠️  Batch classification failed: {e}")
            # Return UNCLASSIFIED for all
            return {item['id']: 'UNCLASSIFIED' for item in batch}

    def get_classification_report(
        self,
        classifications: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generate classification report"""
        counts = {
            "Entity": 0,
            "Controller": 0,
            "Service": 0,
            "Repository": 0,
            "UNCLASSIFIED": 0
        }

        for class_type in classifications.values():
            counts[class_type] = counts.get(class_type, 0) + 1

        return {
            "total_classes": len(classifications),
            "counts": counts,
            "classifications": classifications
        }


# Testing
if __name__ == "__main__":
    print("LLM-Based Class Classifier")
    print("=" * 60)
    print("Uses Gemini to classify classes based on patterns")
    print("NO hardcoded framework rules!")
