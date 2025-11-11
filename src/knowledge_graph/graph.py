"""
Knowledge Graph - Core data structure for storing codebase analysis
"""
import networkx as nx
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Types of nodes in the knowledge graph"""
    CLASS = "class"
    METHOD = "method"
    FIELD = "field"
    ENDPOINT = "endpoint"
    ANNOTATION = "annotation"
    INTERFACE = "interface"
    ENUM = "enum"


class EdgeType(Enum):
    """Types of edges/relationships in the knowledge graph"""
    CALLS = "calls"  # method -> method
    DEPENDS_ON = "depends_on"  # class -> class
    ACCESSES = "accesses"  # method -> field
    DECLARES = "declares"  # class -> method/field
    HANDLES = "handles"  # endpoint -> method
    IMPLEMENTS = "implements"  # class -> interface
    EXTENDS = "extends"  # class -> class
    ANNOTATED_WITH = "annotated_with"  # any -> annotation
    RETURNS = "returns"  # method -> type
    PARAMETER = "parameter"  # method -> type


@dataclass
class ClassNode:
    """Represents a Java class/interface/enum in the knowledge graph"""
    name: str
    package: str
    file_path: str
    class_type: str  # Controller, Service, Repository, Entity, etc.
    java_type: str = "class"  # "class", "interface", "enum", "annotation"
    modifiers: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    superclass: Optional[str] = None
    is_abstract: bool = False


@dataclass
class MethodNode:
    """Represents a Java method in the knowledge graph"""
    name: str
    class_name: str
    signature: str
    return_type: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    body: Optional[str] = None
    line_start: int = 0
    line_end: int = 0


@dataclass
class FieldNode:
    """Represents a Java field in the knowledge graph"""
    name: str
    class_name: str
    field_type: str
    modifiers: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    initial_value: Optional[str] = None


@dataclass
class EndpointNode:
    """Represents a REST endpoint in the knowledge graph"""
    http_method: str  # GET, POST, PUT, DELETE, etc.
    path: str
    handler_method: str
    handler_class: str
    params: List[Dict[str, Any]] = field(default_factory=list)
    consumes: List[str] = field(default_factory=list)
    produces: List[str] = field(default_factory=list)


class KnowledgeGraph:
    """
    Knowledge Graph for storing and querying codebase structure
    Uses NetworkX for graph operations
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.classes: Dict[str, ClassNode] = {}
        self.methods: Dict[str, MethodNode] = {}
        self.fields: Dict[str, FieldNode] = {}
        self.endpoints: Dict[str, EndpointNode] = {}

        # Maps for quick lookups
        self.field_access_map: Dict[str, List[str]] = {}  # field -> methods that access it
        self.method_call_map: Dict[str, List[str]] = {}  # method -> methods it calls
        self.entry_points: Set[str] = set()  # REST endpoints, scheduled jobs, etc.

    def add_class(self, class_node: ClassNode) -> str:
        """Add a class node to the graph"""
        node_id = f"class:{class_node.package}.{class_node.name}"
        self.classes[node_id] = class_node
        self.graph.add_node(node_id, type=NodeType.CLASS, data=class_node)
        return node_id

    def add_method(self, method_node: MethodNode) -> str:
        """Add a method node to the graph"""
        node_id = f"method:{method_node.class_name}.{method_node.name}"
        self.methods[node_id] = method_node
        self.graph.add_node(node_id, type=NodeType.METHOD, data=method_node)

        # Link to class
        class_id = f"class:{method_node.class_name}"
        if class_id in self.classes:
            self.graph.add_edge(class_id, node_id, type=EdgeType.DECLARES)

        return node_id

    def add_field(self, field_node: FieldNode) -> str:
        """Add a field node to the graph"""
        node_id = f"field:{field_node.class_name}.{field_node.name}"
        self.fields[node_id] = field_node
        self.graph.add_node(node_id, type=NodeType.FIELD, data=field_node)

        # Link to class
        class_id = f"class:{field_node.class_name}"
        if class_id in self.classes:
            self.graph.add_edge(class_id, node_id, type=EdgeType.DECLARES)

        return node_id

    def add_endpoint(self, endpoint_node: EndpointNode) -> str:
        """Add an endpoint node to the graph"""
        node_id = f"endpoint:{endpoint_node.http_method}:{endpoint_node.path}"
        self.endpoints[node_id] = endpoint_node
        self.graph.add_node(node_id, type=NodeType.ENDPOINT, data=endpoint_node)
        self.entry_points.add(node_id)

        # Link to handler method
        handler_id = f"method:{endpoint_node.handler_class}.{endpoint_node.handler_method}"
        if handler_id in self.methods:
            self.graph.add_edge(node_id, handler_id, type=EdgeType.HANDLES)

        return node_id

    def add_method_call(self, caller: str, callee: str):
        """Record a method call relationship"""
        caller_id = f"method:{caller}"
        callee_id = f"method:{callee}"

        # Only require caller to exist (callee might be external library or unresolved)
        if caller_id in self.methods:
            # Add edge even if callee doesn't exist (for call counting)
            self.graph.add_edge(caller_id, callee_id, type=EdgeType.CALLS)

            if caller not in self.method_call_map:
                self.method_call_map[caller] = []
            self.method_call_map[caller].append(callee)

    def add_field_access(self, method: str, field: str, access_type: str = "read"):
        """Record a field access (read or write)"""
        method_id = f"method:{method}"
        field_id = f"field:{field}"

        if method_id in self.methods and field_id in self.fields:
            self.graph.add_edge(method_id, field_id, type=EdgeType.ACCESSES, access_type=access_type)

            if field not in self.field_access_map:
                self.field_access_map[field] = []
            self.field_access_map[field].append(method)

    def get_methods_accessing_field(self, field: str, access_type: Optional[str] = None) -> List[str]:
        """Get all methods that access a specific field"""
        field_id = f"field:{field}"
        if field_id not in self.graph:
            return []

        accessors = []
        for pred in self.graph.predecessors(field_id):
            for edge_key in self.graph[pred][field_id]:
                edge_data = self.graph[pred][field_id][edge_key]
                if edge_data.get('type') == EdgeType.ACCESSES:
                    if access_type is None or edge_data.get('access_type') == access_type:
                        accessors.append(pred)

        return accessors

    def get_methods_called_by(self, method: str) -> List[str]:
        """Get all methods called by a specific method"""
        method_id = f"method:{method}"
        if method_id not in self.graph:
            return []

        callees = []
        for succ in self.graph.successors(method_id):
            for edge_key in self.graph[method_id][succ]:
                edge_data = self.graph[method_id][succ][edge_key]
                if edge_data.get('type') == EdgeType.CALLS:
                    callees.append(succ)

        return callees

    def backtrack_to_entry_points(self, target: str, max_depth: int = 10) -> List[List[str]]:
        """
        Backtrack from a target (field/method) to all entry points that can reach it
        Returns list of paths (each path is a list of node IDs)
        """
        paths = []

        for entry_point in self.entry_points:
            try:
                # Find all simple paths from entry point to target
                all_paths = nx.all_simple_paths(
                    self.graph,
                    source=entry_point,
                    target=target,
                    cutoff=max_depth
                )
                paths.extend(list(all_paths))
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        return paths

    def forward_trace(self, entry_point: str, max_depth: int = 10) -> Set[str]:
        """
        Forward trace from an entry point to find all reachable nodes
        Returns set of node IDs
        """
        if entry_point not in self.graph:
            return set()

        reachable = set()

        # BFS traversal
        visited = {entry_point}
        queue = [(entry_point, 0)]

        while queue:
            node, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            reachable.add(node)

            for successor in self.graph.successors(node):
                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, depth + 1))

        return reachable

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the knowledge graph"""
        # Count by java_type
        java_type_counts = {"class": 0, "interface": 0, "enum": 0}
        for class_node in self.classes.values():
            java_type = getattr(class_node, 'java_type', 'class')
            if java_type in java_type_counts:
                java_type_counts[java_type] += 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "classes": len(self.classes),  # Total: classes + interfaces + enums
            "classes_only": java_type_counts["class"],
            "interfaces": java_type_counts["interface"],
            "enums": java_type_counts["enum"],
            "methods": len(self.methods),
            "fields": len(self.fields),
            "endpoints": len(self.endpoints),
            "entry_points": len(self.entry_points)
        }

    def export_to_dict(self) -> Dict[str, Any]:
        """Export the knowledge graph to a dictionary for serialization"""
        return {
            "classes": {k: v.__dict__ for k, v in self.classes.items()},
            "methods": {k: v.__dict__ for k, v in self.methods.items()},
            "fields": {k: v.__dict__ for k, v in self.fields.items()},
            "endpoints": {k: v.__dict__ for k, v in self.endpoints.items()},
            "stats": self.get_stats()
        }
