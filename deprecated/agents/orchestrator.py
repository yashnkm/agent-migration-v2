"""
Orchestrator Agent - Master coordinator for all agents

DEPRECATED: This was designed for query-based reactive system.
Current system uses automatic proactive analysis (analyze_domains.py).

This file is kept for reference and potential future use.
"""
import re
from typing import Dict, Any, Optional, List
from src.agents.base_agent import BaseAgent
from src.agents.data_flow_tracer import DataFlowTracerAgent
from src.agents.business_logic_analyzer import BusinessLogicAnalyzerAgent
from src.agents.api_documentation_agent import APIDocumentationAgent
from src.knowledge_graph.graph import KnowledgeGraph


class OrchestratorAgent(BaseAgent):
    """
    Master coordinator that:
    - Receives user queries
    - Analyzes query intent
    - Delegates to appropriate specialized agents
    - Aggregates and formats results
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        super().__init__(knowledge_graph, "Orchestrator")

        # Initialize specialized agents
        self.data_flow_tracer = DataFlowTracerAgent(knowledge_graph)
        self.business_logic_analyzer = BusinessLogicAnalyzerAgent(knowledge_graph)
        self.api_doc_agent = APIDocumentationAgent(knowledge_graph)

        # Query patterns for intent detection
        self.patterns = {
            "backtrack_field": [
                r"what.*endpoints?.*(?:modify|change|update|write).*?(?:field\s+)?(\w+(?:\.\w+)*)\??",
                r"what.*endpoints?.*(?:can|could).*modify.*?(\w+(?:\.\w+)*)\??",
                r"(?:which|what).*endpoints?.*(?:access|use).*?(\w+(?:\.\w+)*)\??",
            ],
            "backtrack_method": [
                r"what.*endpoints?.*(?:call|use|invoke).*method.*(\w+\.?\w+)",
                r"what.*endpoints?.*reach.*(\w+\.?\w+)",
            ],
            "forward_trace": [
                r"what.*(?:does|do).*endpoint.*(\w+:\/[\w\/\{\}]+).*(?:access|touch|use)",
                r"what.*entities.*endpoint.*(\w+:\/[\w\/\{\}]+)",
                r"trace.*endpoint.*(\w+:\/[\w\/\{\}]+)",
            ],
            "impact_analysis": [
                r"what.*(?:break|breaks|fail|fails|affected?).*(?:if|when).*(?:change|modify).*?(\w+(?:\.\w+)*)\??",
                r"impact.*(?:of|for).*(?:changing|modifying).*?(\w+(?:\.\w+)*)\??",
                r"what.*depends.*on.*?(\w+(?:\.\w+)*)\??",
            ],
            "list_endpoints": [
                r"(?:list|show|what).*(?:all\s)?endpoints",
                r"what.*api",
            ],
            "list_entities": [
                r"(?:list|show|what).*(?:all\s)?entities",
                r"what.*entities.*(?:do we have|exist)",
            ],
            "explain_flow": [
                r"explain.*how\s+(\w+)\s+(?:creation|works?)",
                r"how.*does\s+(\w+)\s+(?:creation|work)",
                r"describe.*(?:flow|process).*(?:for|of)\s+(\w+)",
            ],
            "explain_method": [
                r"explain.*(?:method|function)\s+(\w+(?:\.\w+)*)",
                r"what.*does.*method\s+(\w+(?:\.\w+)*).*do",
                r"describe.*method\s+(\w+(?:\.\w+)*)",
            ],
            "document_api": [
                r"document.*(?:api|endpoints?)",
                r"generate.*(?:api|endpoint).*doc",
                r"show.*api.*documentation",
            ]
        }

    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute orchestrator logic - analyze and delegate query

        Args:
            query: Dictionary with 'text' key containing user query

        Returns:
            Formatted results from delegated agents
        """
        query_text = query.get("text", "")
        self.log(f"Received query: '{query_text}'")

        # Analyze intent
        intent, params = self.analyze_intent(query_text)
        self.log(f"Detected intent: {intent}")

        # Delegate to appropriate agent
        if intent == "backtrack_field":
            field_name = params.get("entity")
            # Try to resolve short field name to full name
            resolved_field = self._resolve_field_name(field_name)
            access_type = self._detect_access_type(query_text)
            result = self.data_flow_tracer.execute({
                "type": "backtrack_field",
                "field": resolved_field,
                "access_type": access_type
            })
            return self._format_backtrack_field_result(result, query_text)

        elif intent == "backtrack_method":
            method_name = params.get("entity")
            resolved_method = self._resolve_method_name(method_name)
            result = self.data_flow_tracer.execute({
                "type": "backtrack_method",
                "method": resolved_method
            })
            return self._format_backtrack_method_result(result, query_text)

        elif intent == "forward_trace":
            endpoint = params.get("entity")
            result = self.data_flow_tracer.execute({
                "type": "forward_trace",
                "endpoint": endpoint
            })
            return self._format_forward_trace_result(result, query_text)

        elif intent == "impact_analysis":
            method_name = params.get("entity")
            resolved_method = self._resolve_method_name(method_name)
            result = self.data_flow_tracer.execute({
                "type": "impact_analysis",
                "method": resolved_method
            })
            return self._format_impact_analysis_result(result, query_text)

        elif intent == "list_endpoints":
            return self._list_endpoints()

        elif intent == "list_entities":
            return self._list_entities()

        elif intent == "explain_flow":
            entity = params.get("entity")
            return self._explain_flow(entity)

        elif intent == "explain_method":
            method_name = params.get("entity")
            resolved_method = self._resolve_method_name(method_name)
            result = self.business_logic_analyzer.execute({
                "type": "explain_method",
                "method": resolved_method
            })
            return self._format_explain_method_result(result, query_text)

        elif intent == "document_api":
            result = self.api_doc_agent.execute({
                "type": "document_all"
            })
            return self._format_api_doc_result(result, query_text)

        else:
            return {
                "error": "Could not understand query",
                "query": query_text,
                "suggestion": "Try queries like:\n"
                             "  - 'What endpoints can modify Employee.email?'\n"
                             "  - 'What would break if I change calculateSalary?'\n"
                             "  - 'Explain method createEmployee'\n"
                             "  - 'List all endpoints'\n"
                             "  - 'Document API'"
            }

    def analyze_intent(self, query_text: str) -> tuple:
        """
        Analyze query intent using pattern matching

        Returns:
            (intent, parameters) tuple
        """
        query_lower = query_text.lower()

        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    params = {}
                    if match.groups():
                        # Extract from original query to preserve case
                        original_match = re.search(pattern, query_lower)
                        start, end = match.span(1)
                        params["entity"] = query_text[start:end]
                    return intent, params

        return "unknown", {}

    def _resolve_field_name(self, field_name: str) -> str:
        """
        Resolve a short field name to full name if possible
        e.g., "email" -> "com.example.demo.entity.Employee.email"
        e.g., "Employee.email" -> "com.example.demo.entity.Employee.email"
        """
        if not field_name:
            return field_name

        # Search for matching field in knowledge graph
        for field_id in self.knowledge_graph.fields.keys():
            # field_id format: "field:com.example.Package.Class.fieldName"
            full_name = field_id.split(":", 1)[1]  # Remove "field:" prefix

            # Check for exact match
            if full_name == field_name:
                return full_name

            # Check if ends with the pattern (e.g., "Employee.email" matches "*.Employee.email")
            if full_name.endswith(f".{field_name}"):
                return full_name

            # Check for Class.field pattern match
            if "." in field_name:
                parts = field_name.split(".")
                if len(parts) == 2:
                    class_name, fname = parts
                    if full_name.endswith(f".{class_name}.{fname}"):
                        return full_name

        # If not found, return as-is (will error in data flow tracer)
        return field_name

    def _resolve_method_name(self, method_name: str) -> str:
        """
        Resolve a short method name to full name if possible
        """
        if not method_name:
            return method_name

        # If already fully qualified, return as-is
        if method_name.count('.') >= 2:
            return method_name

        # Search for matching method in knowledge graph
        for method_id in self.knowledge_graph.methods.keys():
            # method_id format: "method:com.example.Package.Class.methodName"
            if method_id.endswith(f".{method_name}"):
                return method_id.split(":", 1)[1]

        return method_name

    def _detect_access_type(self, query_text: str) -> Optional[str]:
        """Detect if query is asking about read or write access"""
        query_lower = query_text.lower()

        write_keywords = ["modify", "change", "update", "write", "set"]
        read_keywords = ["read", "get", "fetch", "access"]

        has_write = any(kw in query_lower for kw in write_keywords)
        has_read = any(kw in query_lower for kw in read_keywords)

        if has_write and not has_read:
            return "write"
        elif has_read and not has_write:
            return "read"
        else:
            return None  # Both or neither

    def _format_backtrack_field_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format backtrack field results for display"""
        if "error" in result:
            return result

        formatted = {
            "query": query,
            "summary": f"Found {result['total_entry_points']} endpoint(s) that can {result['access_type']} field '{result['field']}'",
            "field": result["field"],
            "access_type": result["access_type"],
            "endpoints": result["entry_points"],
            "accessing_methods": result["accessing_methods"]
        }

        return formatted

    def _format_backtrack_method_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format backtrack method results for display"""
        if "error" in result:
            return result

        formatted = {
            "query": query,
            "summary": f"Found {result['total_entry_points']} endpoint(s) that can call method '{result['method']}'",
            "method": result["method"],
            "endpoints": result["entry_points"],
            "total_paths": result["total_paths"]
        }

        return formatted

    def _format_forward_trace_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format forward trace results for display"""
        if "error" in result:
            return result

        formatted = {
            "query": query,
            "summary": f"Endpoint '{result['endpoint']}' accesses {len(result['fields_accessed'])} field(s) and {len(result['entities_touched'])} entity/entities",
            "endpoint": result["endpoint"],
            "methods_called": result["methods_called"],
            "fields_accessed": result["fields_accessed"],
            "entities_touched": result["entities_touched"]
        }

        return formatted

    def _format_impact_analysis_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format impact analysis results for display"""
        if "error" in result:
            return result

        formatted = {
            "query": query,
            "summary": f"Method '{result['method']}' has {result['direct_callers_count']} direct caller(s) and affects {result['affected_endpoints_count']} endpoint(s) - Risk: {result['risk_level']}",
            "method": result["method"],
            "risk_level": result["risk_level"],
            "direct_callers": result["direct_callers"],
            "affected_endpoints": result["affected_endpoints"],
            "fields_accessed": result["fields_accessed"],
            "methods_called": result["methods_called"]
        }

        return formatted

    def _list_endpoints(self) -> Dict[str, Any]:
        """List all REST endpoints"""
        endpoints = []

        for endpoint_id, endpoint in self.knowledge_graph.endpoints.items():
            endpoints.append({
                "http_method": endpoint.http_method,
                "path": endpoint.path,
                "handler": f"{endpoint.handler_class}.{endpoint.handler_method}"
            })

        return {
            "query": "List all endpoints",
            "summary": f"Found {len(endpoints)} endpoint(s)",
            "endpoints": endpoints
        }

    def _list_entities(self) -> Dict[str, Any]:
        """List all entity classes"""
        entities = []

        for class_id, class_node in self.knowledge_graph.classes.items():
            if class_node.class_type == "Entity":
                entities.append({
                    "name": f"{class_node.package}.{class_node.name}",
                    "file": class_node.file_path
                })

        return {
            "query": "List all entities",
            "summary": f"Found {len(entities)} entity/entities",
            "entities": entities
        }

    def _explain_flow(self, entity: str) -> Dict[str, Any]:
        """Explain the flow for a specific entity or operation"""
        # Find creation endpoints for the entity
        entity_lower = entity.lower()

        # Look for entity class
        entity_class = None
        for class_id, class_node in self.knowledge_graph.classes.items():
            if class_node.class_type == "Entity" and entity_lower in class_node.name.lower():
                entity_class = class_node
                break

        if not entity_class:
            return {
                "query": f"Explain how {entity} works",
                "error": f"Entity '{entity}' not found",
                "suggestion": "Try listing entities first with 'List all entities'"
            }

        # Find endpoints that create this entity
        creation_endpoints = []
        for ep_id, endpoint in self.knowledge_graph.endpoints.items():
            if endpoint.http_method == "POST" and entity_lower in endpoint.handler_method.lower():
                creation_endpoints.append(endpoint)

        if not creation_endpoints:
            return {
                "query": f"Explain how {entity} creation works",
                "entity": f"{entity_class.package}.{entity_class.name}",
                "note": "No creation endpoints found for this entity"
            }

        # Get details for the first creation endpoint
        endpoint = creation_endpoints[0]
        handler_method_name = f"{endpoint.handler_class}.{endpoint.handler_method}"

        # Use business logic analyzer
        explanation = self.business_logic_analyzer.execute({
            "type": "explain_method",
            "method": handler_method_name
        })

        # Use data flow tracer
        flow = self.data_flow_tracer.execute({
            "type": "forward_trace",
            "endpoint": f"{endpoint.http_method}:{endpoint.path}"
        })

        return {
            "query": f"Explain how {entity} creation works",
            "entity": f"{entity_class.package}.{entity_class.name}",
            "endpoint": f"{endpoint.http_method} {endpoint.path}",
            "handler": handler_method_name,
            "explanation": explanation.get("explanation", "No explanation available"),
            "fields_accessed": flow.get("fields_accessed", []),
            "methods_called": flow.get("methods_called", [])
        }

    def _format_explain_method_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format method explanation results"""
        if "error" in result:
            return result

        return {
            "query": query,
            "method": result.get("method"),
            "explanation": result.get("explanation", "No explanation available"),
            "signature": result.get("signature"),
            "return_type": result.get("return_type"),
            "annotations": result.get("annotations", [])
        }

    def _format_api_doc_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format API documentation results"""
        return {
            "query": query,
            "summary": f"Found {result.get('total_endpoints', 0)} endpoint(s)",
            "endpoints": result.get("endpoints", [])
        }
