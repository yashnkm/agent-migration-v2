"""
Business Logic Analyzer for Domains
Extracts business logic on-demand for specific domains
"""
import os
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

from src.knowledge_graph.graph import KnowledgeGraph, MethodNode


class DomainBusinessAnalyzer:
    """
    Analyzes business logic for a specific domain on-demand
    """

    def __init__(self):
        """Initialize the business analyzer"""
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            print("WARNING: ANTHROPIC_API_KEY not found in environment")
            print("Business logic analysis requires an Anthropic API key")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"

    def analyze_domain(self, domain_info: Dict[str, Any], knowledge_graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        Analyze business logic for an entire domain

        Args:
            domain_info: DomainInfo object (as dict)
            knowledge_graph: KnowledgeGraph containing all code

        Returns:
            Dictionary with business logic analysis
        """
        if not self.client:
            return {
                "error": "Claude API not available",
                "domain": domain_info["name"],
                "note": "Set ANTHROPIC_API_KEY environment variable to enable business logic analysis"
            }

        domain_name = domain_info["name"]
        print(f"\nAnalyzing business logic for {domain_name} domain...")

        analysis = {
            "domain": domain_name,
            "endpoints": [],
            "business_methods": [],
            "business_rules": [],
            "workflows": []
        }

        # Analyze endpoints
        for endpoint in domain_info.get("endpoints", []):
            endpoint_analysis = self._analyze_endpoint(endpoint, knowledge_graph)
            if endpoint_analysis:
                analysis["endpoints"].append(endpoint_analysis)

        # Analyze key business methods (Service layer)
        service_class = domain_info.get("service")
        if service_class:
            service_methods = self._get_methods_for_class(service_class, knowledge_graph)
            for method_id, method_node in service_methods:
                method_analysis = self._analyze_method(method_node)
                if method_analysis:
                    analysis["business_methods"].append(method_analysis)

        # Extract all business rules
        all_rules = []
        for endpoint in analysis["endpoints"]:
            all_rules.extend(endpoint.get("business_rules", []))
        for method in analysis["business_methods"]:
            all_rules.extend(method.get("business_rules", []))

        # Deduplicate rules
        analysis["business_rules"] = list(set(all_rules))

        print(f"  Analyzed {len(analysis['endpoints'])} endpoints")
        print(f"  Analyzed {len(analysis['business_methods'])} business methods")
        print(f"  Extracted {len(analysis['business_rules'])} business rules")

        return analysis

    def _analyze_endpoint(self, endpoint: Dict[str, Any], knowledge_graph: KnowledgeGraph) -> Optional[Dict[str, Any]]:
        """
        Analyze a single endpoint

        Args:
            endpoint: Endpoint info from domain
            knowledge_graph: KnowledgeGraph

        Returns:
            Dictionary with endpoint analysis
        """
        handler_class = endpoint["handler_class"]
        handler_method = endpoint["handler_method"]
        method_full_name = f"{handler_class}.{handler_method}"

        # Get method from knowledge graph
        method_id = f"method:{method_full_name}"
        if method_id not in knowledge_graph.methods:
            return None

        method_node = knowledge_graph.methods[method_id]

        if not method_node.body:
            return {
                "http_method": endpoint["http_method"],
                "path": endpoint["path"],
                "handler": method_full_name,
                "explanation": "No method body available for analysis",
                "business_rules": []
            }

        try:
            # Use Claude to analyze the endpoint
            prompt = f"""Analyze this Spring Boot REST endpoint handler method.

HTTP Method: {endpoint['http_method']}
Path: {endpoint['path']}
Handler: {handler_method}

Method Code:
```java
{method_node.body}
```

Provide a concise analysis in this format:

1. Purpose: (one sentence - what does this endpoint do?)
2. Business Logic: (2-3 sentences - key operations and flow)
3. Business Rules: (bullet list - validations, constraints, important logic)

Keep it clear and focused on business logic, not technical implementation details."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse response
            purpose = ""
            business_logic = ""
            business_rules = []

            for line in response_text.split('\n'):
                line = line.strip()
                if line.startswith("1. Purpose:"):
                    purpose = line.replace("1. Purpose:", "").strip()
                elif line.startswith("2. Business Logic:"):
                    business_logic = line.replace("2. Business Logic:", "").strip()
                elif line.startswith("3. Business Rules:"):
                    continue
                elif line.startswith("-") or line.startswith("•"):
                    rule = line.lstrip("-•").strip()
                    if rule:
                        business_rules.append(rule)

            return {
                "http_method": endpoint["http_method"],
                "path": endpoint["path"],
                "handler": method_full_name,
                "purpose": purpose,
                "business_logic": business_logic,
                "business_rules": business_rules
            }

        except Exception as e:
            print(f"  Error analyzing endpoint {endpoint['path']}: {e}")
            return None

    def _analyze_method(self, method_node: MethodNode) -> Optional[Dict[str, Any]]:
        """
        Analyze a single business method

        Args:
            method_node: MethodNode from knowledge graph

        Returns:
            Dictionary with method analysis
        """
        if not method_node.body:
            return None

        try:
            prompt = f"""Analyze this Java business method.

Method: {method_node.name}
Signature: {method_node.signature}
Return Type: {method_node.return_type}

Method Code:
```java
{method_node.body}
```

Provide:
1. Purpose: (one sentence)
2. Key Operations: (2-3 bullet points of what it does)
3. Business Rules: (bullet list of validations, constraints, important logic)

Focus on business logic, not technical details."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse response
            purpose = ""
            operations = []
            business_rules = []

            current_section = None
            for line in response_text.split('\n'):
                line = line.strip()
                if "Purpose:" in line:
                    purpose = line.split("Purpose:", 1)[1].strip()
                    current_section = "purpose"
                elif "Key Operations:" in line or "Operations:" in line:
                    current_section = "operations"
                elif "Business Rules:" in line or "Rules:" in line:
                    current_section = "rules"
                elif line.startswith("-") or line.startswith("•"):
                    item = line.lstrip("-•").strip()
                    if current_section == "operations":
                        operations.append(item)
                    elif current_section == "rules":
                        business_rules.append(item)

            return {
                "method": f"{method_node.class_name}.{method_node.name}",
                "purpose": purpose,
                "operations": operations,
                "business_rules": business_rules
            }

        except Exception as e:
            print(f"  Error analyzing method {method_node.name}: {e}")
            return None

    def _get_methods_for_class(self, class_name: str, knowledge_graph: KnowledgeGraph) -> List[tuple]:
        """
        Get all methods for a specific class

        Args:
            class_name: Full class name
            knowledge_graph: KnowledgeGraph

        Returns:
            List of (method_id, method_node) tuples
        """
        methods = []
        for method_id, method_node in knowledge_graph.methods.items():
            if method_node.class_name == class_name:
                methods.append((method_id, method_node))
        return methods
