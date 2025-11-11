"""
API Documentation Agent - Documents REST APIs
"""
from typing import Dict, Any, List, Optional
from src.agents.base_agent import BaseAgent
from src.knowledge_graph.graph import KnowledgeGraph, EndpointNode


class APIDocumentationAgent(BaseAgent):
    """
    Agent responsible for documenting REST APIs:
    - Extract all REST endpoints
    - Document request/response formats
    - Identify parameters
    - Generate API documentation
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        super().__init__(knowledge_graph, "APIDocumentation")

    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute API documentation tasks

        Query types:
        - document_endpoint: Document a specific endpoint
        - document_all: Document all endpoints
        - get_endpoint_details: Get detailed info about an endpoint
        """
        query_type = query.get("type")

        if query_type == "document_endpoint":
            return self.document_endpoint(query.get("endpoint_id"))
        elif query_type == "document_all":
            return self.document_all_endpoints()
        elif query_type == "get_endpoint_details":
            return self.get_endpoint_details(query.get("endpoint_path"))
        else:
            return {"error": f"Unknown query type: {query_type}"}

    def document_endpoint(self, endpoint_id: str) -> Dict[str, Any]:
        """
        Generate documentation for a specific endpoint

        Args:
            endpoint_id: Endpoint identifier

        Returns:
            Dictionary with endpoint documentation
        """
        self.log(f"Documenting endpoint: {endpoint_id}")

        if endpoint_id not in self.knowledge_graph.endpoints:
            return {
                "error": f"Endpoint '{endpoint_id}' not found",
                "endpoint": endpoint_id
            }

        endpoint = self.knowledge_graph.endpoints[endpoint_id]

        # Get handler method details
        handler_method_id = f"method:{endpoint.handler_class}.{endpoint.handler_method}"
        handler_method = None
        if handler_method_id in self.knowledge_graph.methods:
            handler_method = self.knowledge_graph.methods[handler_method_id]

        # Build documentation
        doc = {
            "http_method": endpoint.http_method,
            "path": endpoint.path,
            "handler": {
                "class": endpoint.handler_class,
                "method": endpoint.handler_method
            },
            "parameters": self._extract_parameters(endpoint, handler_method),
            "description": self._generate_description(endpoint, handler_method),
            "return_type": handler_method.return_type if handler_method else "unknown"
        }

        return doc

    def document_all_endpoints(self) -> Dict[str, Any]:
        """
        Generate documentation for all endpoints

        Returns:
            Dictionary with all endpoint documentation
        """
        self.log("Documenting all endpoints")

        endpoints_doc = []

        for endpoint_id, endpoint in self.knowledge_graph.endpoints.items():
            doc = self.document_endpoint(endpoint_id)
            if "error" not in doc:
                endpoints_doc.append(doc)

        return {
            "total_endpoints": len(endpoints_doc),
            "endpoints": endpoints_doc
        }

    def get_endpoint_details(self, endpoint_path: str) -> Dict[str, Any]:
        """
        Get detailed information about an endpoint by path

        Args:
            endpoint_path: Endpoint path (e.g., "POST:/api/employees")

        Returns:
            Dictionary with endpoint details
        """
        self.log(f"Getting details for: {endpoint_path}")

        # Find endpoint by path
        for endpoint_id, endpoint in self.knowledge_graph.endpoints.items():
            if f"{endpoint.http_method}:{endpoint.path}" == endpoint_path:
                return self.document_endpoint(endpoint_id)

        return {
            "error": f"Endpoint '{endpoint_path}' not found",
            "endpoint": endpoint_path
        }

    def _extract_parameters(self, endpoint: EndpointNode,
                           handler_method) -> List[Dict[str, str]]:
        """Extract parameters from endpoint and handler method"""

        parameters = []

        if not handler_method:
            return parameters

        for param in handler_method.parameters:
            param_info = {
                "name": param["name"],
                "type": param["type"],
                "source": "unknown"
            }

            # Try to determine parameter source based on common Spring annotations
            # This is simplified - in reality we'd need to parse annotations
            param_name_lower = param["name"].lower()

            if "id" in param_name_lower or param["type"] == "Long":
                param_info["source"] = "path"
            elif param["type"] == "String" and len(handler_method.parameters) == 1:
                param_info["source"] = "path"
            else:
                param_info["source"] = "body"

            parameters.append(param_info)

        return parameters

    def _generate_description(self, endpoint: EndpointNode, handler_method) -> str:
        """Generate a description for the endpoint"""

        method_name = endpoint.handler_method.lower()

        # Generate description based on HTTP method and handler name
        descriptions = {
            "GET": {
                "get": "Retrieves",
                "find": "Finds",
                "list": "Lists",
                "all": "Retrieves all"
            },
            "POST": {
                "create": "Creates a new",
                "add": "Adds a new",
                "save": "Saves a new"
            },
            "PUT": {
                "update": "Updates an existing",
                "edit": "Edits an existing",
                "modify": "Modifies an existing"
            },
            "DELETE": {
                "delete": "Deletes",
                "remove": "Removes"
            }
        }

        # Try to match method name patterns
        http_method = endpoint.http_method
        if http_method in descriptions:
            for keyword, action in descriptions[http_method].items():
                if keyword in method_name:
                    # Extract entity name from handler class
                    class_name = endpoint.handler_class.split('.')[-1]
                    entity = class_name.replace('Controller', '').replace('Service', '')

                    if keyword == "all":
                        return f"{action} {entity.lower()} records"
                    else:
                        return f"{action} {entity.lower()} record"

        # Default descriptions
        default_descriptions = {
            "GET": f"Retrieves data via {endpoint.handler_method}",
            "POST": f"Creates data via {endpoint.handler_method}",
            "PUT": f"Updates data via {endpoint.handler_method}",
            "DELETE": f"Deletes data via {endpoint.handler_method}",
            "PATCH": f"Partially updates data via {endpoint.handler_method}"
        }

        return default_descriptions.get(http_method, f"Performs {http_method} operation")

    def generate_openapi_style_doc(self) -> Dict[str, Any]:
        """
        Generate OpenAPI-style documentation

        Returns:
            OpenAPI-like documentation structure
        """
        self.log("Generating OpenAPI-style documentation")

        paths = {}

        for endpoint_id, endpoint in self.knowledge_graph.endpoints.items():
            path = endpoint.path
            method = endpoint.http_method.lower()

            if path not in paths:
                paths[path] = {}

            doc = self.document_endpoint(endpoint_id)

            paths[path][method] = {
                "summary": doc.get("description", ""),
                "operationId": endpoint.handler_method,
                "parameters": [
                    {
                        "name": p["name"],
                        "in": p["source"],
                        "required": True,
                        "schema": {"type": self._java_type_to_openapi(p["type"])}
                    }
                    for p in doc.get("parameters", [])
                ],
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }

        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Java Codebase API",
                "version": "1.0.0"
            },
            "paths": paths
        }

    def _java_type_to_openapi(self, java_type: str) -> str:
        """Convert Java type to OpenAPI type"""
        type_mapping = {
            "String": "string",
            "Long": "integer",
            "Integer": "integer",
            "int": "integer",
            "long": "integer",
            "Double": "number",
            "double": "number",
            "Float": "number",
            "float": "number",
            "Boolean": "boolean",
            "boolean": "boolean",
            "List": "array",
            "ArrayList": "array"
        }

        return type_mapping.get(java_type, "string")
