"""
Business Logic Analyzer Agent - Uses AI to understand what code does
"""
import os
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

from src.agents.base_agent import BaseAgent
from src.knowledge_graph.graph import KnowledgeGraph, MethodNode


class BusinessLogicAnalyzerAgent(BaseAgent):
    """
    Agent that uses Claude AI to analyze and explain business logic:
    - Understand what methods do in plain English
    - Extract business rules and validations
    - Identify data transformations
    - Explain side effects
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        super().__init__(knowledge_graph, "BusinessLogicAnalyzer")

        # Load API key
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            self.log("WARNING: ANTHROPIC_API_KEY not found in environment")
            self.log("Business logic analysis will be limited without API key")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"

    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute business logic analysis

        Query types:
        - explain_method: Explain what a method does
        - extract_rules: Extract business rules from a method
        - explain_flow: Explain an end-to-end flow
        """
        query_type = query.get("type")

        if query_type == "explain_method":
            return self.explain_method(query.get("method"))
        elif query_type == "extract_rules":
            return self.extract_business_rules(query.get("method"))
        elif query_type == "explain_flow":
            return self.explain_flow(
                query.get("start_method"),
                query.get("path")
            )
        else:
            return {"error": f"Unknown query type: {query_type}"}

    def explain_method(self, method_name: str) -> Dict[str, Any]:
        """
        Explain what a method does in plain English

        Args:
            method_name: Full method name

        Returns:
            Dictionary with explanation
        """
        self.log(f"Explaining method: {method_name}")

        method_id = f"method:{method_name}"
        if method_id not in self.knowledge_graph.methods:
            return {
                "error": f"Method '{method_name}' not found",
                "method": method_name
            }

        method_node = self.knowledge_graph.methods[method_id]

        # If no API client, return basic info
        if not self.client:
            return self._basic_method_info(method_node)

        # Use Claude to analyze the method
        try:
            explanation = self._analyze_method_with_ai(method_node)
            return {
                "method": method_name,
                "explanation": explanation,
                "signature": method_node.signature,
                "return_type": method_node.return_type,
                "annotations": method_node.annotations
            }
        except Exception as e:
            self.log(f"Error calling Claude API: {e}")
            return self._basic_method_info(method_node)

    def extract_business_rules(self, method_name: str) -> Dict[str, Any]:
        """
        Extract business rules and validations from a method

        Args:
            method_name: Full method name

        Returns:
            Dictionary with business rules
        """
        self.log(f"Extracting business rules from: {method_name}")

        method_id = f"method:{method_name}"
        if method_id not in self.knowledge_graph.methods:
            return {
                "error": f"Method '{method_name}' not found",
                "method": method_name
            }

        method_node = self.knowledge_graph.methods[method_id]

        if not self.client or not method_node.body:
            return {
                "method": method_name,
                "rules": [],
                "note": "Business rule extraction requires API access and method body"
            }

        try:
            rules = self._extract_rules_with_ai(method_node)
            return {
                "method": method_name,
                "rules": rules
            }
        except Exception as e:
            self.log(f"Error calling Claude API: {e}")
            return {
                "method": method_name,
                "rules": [],
                "error": str(e)
            }

    def explain_flow(self, start_method: str, path: List[str]) -> Dict[str, Any]:
        """
        Explain an end-to-end flow through multiple methods

        Args:
            start_method: Starting method name
            path: List of method names in the flow

        Returns:
            Dictionary with flow explanation
        """
        self.log(f"Explaining flow starting from: {start_method}")

        if not self.client:
            return {
                "flow": "end-to-end",
                "explanation": "Flow explanation requires API access",
                "path": path
            }

        # Gather method bodies for the entire flow
        method_bodies = []
        for method_name in path:
            method_id = f"method:{method_name}"
            if method_id in self.knowledge_graph.methods:
                method_node = self.knowledge_graph.methods[method_id]
                if method_node.body:
                    method_bodies.append({
                        "name": method_name,
                        "body": method_node.body
                    })

        try:
            explanation = self._explain_flow_with_ai(method_bodies)
            return {
                "flow": "end-to-end",
                "start": start_method,
                "explanation": explanation,
                "path": path
            }
        except Exception as e:
            self.log(f"Error calling Claude API: {e}")
            return {
                "flow": "end-to-end",
                "error": str(e),
                "path": path
            }

    def _analyze_method_with_ai(self, method_node: MethodNode) -> str:
        """Use Claude to analyze a method and explain what it does"""

        prompt = f"""You are analyzing Java code. Explain what this method does in 2-3 clear sentences.

Method: {method_node.name}
Signature: {method_node.signature}
Return Type: {method_node.return_type}
Annotations: {', '.join(method_node.annotations) if method_node.annotations else 'None'}

Method Body:
```java
{method_node.body if method_node.body else '// No body available'}
```

Provide a concise explanation of:
1. What this method does
2. Key business logic or validations
3. What it returns

Keep it brief and focused."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def _extract_rules_with_ai(self, method_node: MethodNode) -> List[str]:
        """Use Claude to extract business rules from a method"""

        prompt = f"""You are analyzing Java code. Extract all business rules and validations from this method.

Method: {method_node.name}
Method Body:
```java
{method_node.body}
```

List each business rule or validation as a separate bullet point. Focus on:
- Validation checks (e.g., "Email must be unique")
- Business constraints (e.g., "Minimum salary is 30000")
- Default values (e.g., "Default department is 'General'")
- Conditional logic that enforces business rules

Return ONLY the bullet points, one per line, starting with "- ". If no rules found, return "- No explicit business rules found"."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse bullet points
        rules = []
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                rules.append(line[2:])  # Remove "- " prefix
            elif line.startswith('* '):
                rules.append(line[2:])  # Remove "* " prefix
            elif line and not line.startswith('#'):
                rules.append(line)

        return rules if rules else ["No explicit business rules found"]

    def _explain_flow_with_ai(self, method_bodies: List[Dict[str, str]]) -> str:
        """Use Claude to explain an end-to-end flow"""

        methods_text = "\n\n".join([
            f"Method: {m['name']}\n```java\n{m['body']}\n```"
            for m in method_bodies
        ])

        prompt = f"""You are analyzing a Java Spring Boot application flow. Explain how data flows through these methods.

Methods in the flow:
{methods_text}

Provide a clear explanation that covers:
1. What the flow accomplishes overall
2. How data is transformed or validated at each step
3. What happens at the end (e.g., saved to database, returned to user)

Keep it concise and focused on the data flow."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def _basic_method_info(self, method_node: MethodNode) -> Dict[str, Any]:
        """Return basic method info without AI analysis"""

        explanation = f"Method {method_node.name} "

        if method_node.annotations:
            if any(ann in ['GetMapping', 'PostMapping', 'PutMapping', 'DeleteMapping']
                   for ann in method_node.annotations):
                explanation += "is a REST endpoint handler. "

        if method_node.return_type != "void":
            explanation += f"Returns {method_node.return_type}. "

        if method_node.parameters:
            param_count = len(method_node.parameters)
            explanation += f"Takes {param_count} parameter{'s' if param_count != 1 else ''}."

        return {
            "method": f"{method_node.class_name}.{method_node.name}",
            "explanation": explanation,
            "signature": method_node.signature,
            "return_type": method_node.return_type,
            "annotations": method_node.annotations,
            "note": "Limited analysis - Claude API not available"
        }
