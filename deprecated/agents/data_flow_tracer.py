"""
Data Flow Tracer Agent - Traces data flows through the codebase
"""
from typing import Dict, Any, List, Set, Tuple, Optional
import networkx as nx
from src.agents.base_agent import BaseAgent
from src.knowledge_graph.graph import KnowledgeGraph, EdgeType


class DataFlowTracerAgent(BaseAgent):
    """
    Agent responsible for tracing data flows:
    - Backtracking from fields/methods to entry points
    - Forward tracing from entry points to entities
    - Finding all paths between two points
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        super().__init__(knowledge_graph, "DataFlowTracer")

    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute data flow tracing based on query type

        Query types:
        - backtrack_field: Find all entry points that can modify a field
        - forward_trace: Find all entities accessed from an entry point
        - find_paths: Find all paths between two nodes
        """
        query_type = query.get("type")

        if query_type == "backtrack_field":
            return self.backtrack_from_field(
                query.get("field"),
                query.get("access_type", None)
            )
        elif query_type == "backtrack_method":
            return self.backtrack_from_method(query.get("method"))
        elif query_type == "forward_trace":
            return self.forward_trace_from_endpoint(query.get("endpoint"))
        elif query_type == "find_paths":
            return self.find_all_paths(query.get("source"), query.get("target"))
        elif query_type == "impact_analysis":
            return self.analyze_impact(query.get("method"))
        else:
            return {"error": f"Unknown query type: {query_type}"}

    def backtrack_from_field(self, field_name: str, access_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Backtrack from a field to find all entry points that can access it

        Args:
            field_name: Full field name (e.g., "com.example.Employee.email")
            access_type: "read", "write", or None (both)

        Returns:
            Dictionary with paths from entry points to the field
        """
        self.log(f"Backtracking from field: {field_name} (access_type: {access_type or 'any'})")

        field_id = f"field:{field_name}"

        if field_id not in self.knowledge_graph.graph:
            return {
                "error": f"Field '{field_name}' not found in knowledge graph",
                "field": field_name
            }

        # Step 1: Find all methods that access this field
        accessing_methods = self.knowledge_graph.get_methods_accessing_field(
            field_name, access_type
        )

        self.log(f"Found {len(accessing_methods)} methods accessing the field")

        # Step 2: For each method, backtrack to entry points
        all_paths = []
        entry_points_found = set()

        for method_id in accessing_methods:
            # Get method info
            if method_id in self.knowledge_graph.methods:
                method_node = self.knowledge_graph.methods[method_id]
                method_full_name = f"{method_node.class_name}.{method_node.name}"
                self.log(f"  Analyzing: {method_full_name}")

                # Backtrack from this method to entry points
                paths = self.knowledge_graph.backtrack_to_entry_points(method_id)

                for path in paths:
                    all_paths.append({
                        "path": path,
                        "entry_point": path[0] if path else None,
                        "accessor_method": method_id,
                        "field": field_id
                    })

                    if path:
                        entry_points_found.add(path[0])

        self.log(f"Found {len(entry_points_found)} entry points")

        # Format results
        results = {
            "field": field_name,
            "access_type": access_type or "any",
            "total_paths": len(all_paths),
            "total_entry_points": len(entry_points_found),
            "accessing_methods": [
                self._format_node_id(m) for m in accessing_methods
            ],
            "entry_points": [],
            "paths": []
        }

        # Group by entry point
        for entry_point_id in entry_points_found:
            endpoint_paths = [p for p in all_paths if p["entry_point"] == entry_point_id]

            if entry_point_id in self.knowledge_graph.endpoints:
                endpoint = self.knowledge_graph.endpoints[entry_point_id]
                entry_point_info = {
                    "type": "REST Endpoint",
                    "http_method": endpoint.http_method,
                    "path": endpoint.path,
                    "handler": f"{endpoint.handler_class}.{endpoint.handler_method}",
                    "paths_count": len(endpoint_paths),
                    "sample_path": self._format_path(endpoint_paths[0]["path"]) if endpoint_paths else []
                }
                results["entry_points"].append(entry_point_info)

        # Add detailed paths
        for path_info in all_paths[:10]:  # Limit to 10 for brevity
            results["paths"].append({
                "entry_point": self._format_node_id(path_info["entry_point"]),
                "path": self._format_path(path_info["path"])
            })

        return results

    def backtrack_from_method(self, method_name: str) -> Dict[str, Any]:
        """
        Backtrack from a method to find all entry points that can call it

        Args:
            method_name: Full method name (e.g., "com.example.Service.calculateSalary")

        Returns:
            Dictionary with paths from entry points to the method
        """
        self.log(f"Backtracking from method: {method_name}")

        method_id = f"method:{method_name}"

        if method_id not in self.knowledge_graph.graph:
            return {
                "error": f"Method '{method_name}' not found in knowledge graph",
                "method": method_name
            }

        # Find all paths from entry points to this method
        paths = self.knowledge_graph.backtrack_to_entry_points(method_id)

        entry_points_found = set()
        for path in paths:
            if path:
                entry_points_found.add(path[0])

        self.log(f"Found {len(entry_points_found)} entry points that can reach this method")

        results = {
            "method": method_name,
            "total_paths": len(paths),
            "total_entry_points": len(entry_points_found),
            "entry_points": [],
            "paths": []
        }

        # Format entry points
        for entry_point_id in entry_points_found:
            if entry_point_id in self.knowledge_graph.endpoints:
                endpoint = self.knowledge_graph.endpoints[entry_point_id]
                results["entry_points"].append({
                    "type": "REST Endpoint",
                    "http_method": endpoint.http_method,
                    "path": endpoint.path,
                    "handler": f"{endpoint.handler_class}.{endpoint.handler_method}"
                })

        # Add paths
        for path in paths[:10]:
            results["paths"].append(self._format_path(path))

        return results

    def forward_trace_from_endpoint(self, endpoint_path: str) -> Dict[str, Any]:
        """
        Forward trace from an endpoint to find all entities and fields it accesses

        Args:
            endpoint_path: Endpoint identifier (e.g., "POST:/api/employees")

        Returns:
            Dictionary with all reachable nodes
        """
        self.log(f"Forward tracing from endpoint: {endpoint_path}")

        # Find the endpoint
        endpoint_id = None
        for ep_id, endpoint in self.knowledge_graph.endpoints.items():
            if f"{endpoint.http_method}:{endpoint.path}" == endpoint_path:
                endpoint_id = ep_id
                break

        if not endpoint_id:
            return {
                "error": f"Endpoint '{endpoint_path}' not found",
                "endpoint": endpoint_path
            }

        # Forward trace to find all reachable nodes
        reachable = self.knowledge_graph.forward_trace(endpoint_id, max_depth=20)

        # Categorize reachable nodes
        methods_called = []
        fields_accessed = []
        entities_touched = []

        for node_id in reachable:
            if node_id.startswith("method:"):
                if node_id in self.knowledge_graph.methods:
                    method = self.knowledge_graph.methods[node_id]
                    methods_called.append(f"{method.class_name}.{method.name}")
            elif node_id.startswith("field:"):
                if node_id in self.knowledge_graph.fields:
                    field = self.knowledge_graph.fields[node_id]
                    fields_accessed.append(f"{field.class_name}.{field.name}")
            elif node_id.startswith("class:"):
                if node_id in self.knowledge_graph.classes:
                    cls = self.knowledge_graph.classes[node_id]
                    if cls.class_type == "Entity":
                        entities_touched.append(f"{cls.package}.{cls.name}")

        self.log(f"Reachable: {len(methods_called)} methods, {len(fields_accessed)} fields, {len(entities_touched)} entities")

        return {
            "endpoint": endpoint_path,
            "total_reachable": len(reachable),
            "methods_called": methods_called,
            "fields_accessed": fields_accessed,
            "entities_touched": entities_touched
        }

    def find_all_paths(self, source: str, target: str) -> Dict[str, Any]:
        """
        Find all paths between two nodes

        Args:
            source: Source node ID
            target: Target node ID

        Returns:
            Dictionary with all paths
        """
        self.log(f"Finding paths from {source} to {target}")

        try:
            all_paths = list(nx.all_simple_paths(
                self.knowledge_graph.graph,
                source=source,
                target=target,
                cutoff=10
            ))

            return {
                "source": source,
                "target": target,
                "total_paths": len(all_paths),
                "paths": [self._format_path(path) for path in all_paths[:5]]
            }
        except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
            return {
                "error": str(e),
                "source": source,
                "target": target,
                "total_paths": 0,
                "paths": []
            }

    def analyze_impact(self, method_name: str) -> Dict[str, Any]:
        """
        Analyze the impact of changing a method

        Args:
            method_name: Full method name

        Returns:
            Dictionary with impact analysis
        """
        self.log(f"Analyzing impact of: {method_name}")

        method_id = f"method:{method_name}"

        if method_id not in self.knowledge_graph.graph:
            return {
                "error": f"Method '{method_name}' not found",
                "method": method_name
            }

        # Find direct callers
        direct_callers = []
        for pred in self.knowledge_graph.graph.predecessors(method_id):
            if pred.startswith("method:"):
                direct_callers.append(self._format_node_id(pred))

        # Find affected entry points
        paths = self.knowledge_graph.backtrack_to_entry_points(method_id)
        entry_points = set()
        for path in paths:
            if path:
                entry_points.add(path[0])

        # Find what this method accesses
        fields_accessed = []
        methods_called = []
        for succ in self.knowledge_graph.graph.successors(method_id):
            if succ.startswith("field:"):
                fields_accessed.append(self._format_node_id(succ))
            elif succ.startswith("method:"):
                methods_called.append(self._format_node_id(succ))

        affected_endpoints = []
        for ep_id in entry_points:
            if ep_id in self.knowledge_graph.endpoints:
                ep = self.knowledge_graph.endpoints[ep_id]
                affected_endpoints.append({
                    "http_method": ep.http_method,
                    "path": ep.path,
                    "handler": f"{ep.handler_class}.{ep.handler_method}"
                })

        return {
            "method": method_name,
            "direct_callers": direct_callers,
            "direct_callers_count": len(direct_callers),
            "affected_endpoints": affected_endpoints,
            "affected_endpoints_count": len(affected_endpoints),
            "fields_accessed": fields_accessed,
            "methods_called": methods_called,
            "risk_level": self._assess_risk_level(len(direct_callers), len(affected_endpoints))
        }

    def _assess_risk_level(self, callers_count: int, endpoints_count: int) -> str:
        """Assess risk level based on usage"""
        if endpoints_count > 3 or callers_count > 5:
            return "HIGH"
        elif endpoints_count > 1 or callers_count > 2:
            return "MEDIUM"
        else:
            return "LOW"

    def _format_path(self, path: List[str]) -> List[str]:
        """Format a path for display"""
        return [self._format_node_id(node_id) for node_id in path]

    def _format_node_id(self, node_id: str) -> str:
        """Format a node ID for display"""
        if not node_id:
            return ""

        # Remove type prefix
        if ":" in node_id:
            return node_id.split(":", 1)[1]
        return node_id
