"""
Relationship Extractor - Extracts method calls and field accesses
"""
from typing import List, Set, Dict, Tuple
from tree_sitter import Node
from src.knowledge_graph.graph import KnowledgeGraph


class RelationshipExtractor:
    """
    Extracts relationships between code elements:
    - Method calls (who calls whom)
    - Field accesses (who reads/writes what)
    - Endpoint mappings
    """

    def __init__(self, parser):
        """Initialize with a JavaParser instance"""
        self.parser = parser
        self.language = parser.language

    def extract_method_calls(self, method_body: str, method_full_name: str,
                            source_code: bytes, knowledge_graph: KnowledgeGraph):
        """
        Extract all method calls within a method body
        """
        if not method_body:
            return

        # Parse the method body
        tree = self.parser.parser.parse(method_body.encode('utf-8'))
        root = tree.root_node

        # Query for method invocations
        query = self.language.query("""
            (method_invocation
                name: (identifier) @method_name
            ) @call
        """)

        captures = query.captures(root)

        for node, capture_name in captures:
            if capture_name == "method_name":
                called_method = self.parser.extract_text(node, method_body.encode('utf-8'))

                # Add method call to knowledge graph
                # Note: called_method is just the method name, not fully qualified
                # The graph will store this and domain discovery will resolve it
                knowledge_graph.add_method_call(method_full_name, called_method)
                print(f"  {method_full_name} calls {called_method}")

    def extract_field_accesses(self, method_body: str, method_full_name: str,
                               class_name: str, source_code: bytes,
                               knowledge_graph: KnowledgeGraph):
        """
        Extract all field accesses (reads and writes) within a method body
        """
        if not method_body:
            return

        tree = self.parser.parser.parse(method_body.encode('utf-8'))
        root = tree.root_node

        # Query for field access (reading)
        read_query = self.language.query("""
            (field_access
                field: (identifier) @field_name
            ) @access
        """)

        # Query for assignments (writing)
        write_query = self.language.query("""
            (assignment_expression
                left: (identifier) @field_name
            ) @assignment
        """)

        # Extract reads
        captures = read_query.captures(root)
        for node, capture_name in captures:
            if capture_name == "field_name":
                field_name = self.parser.extract_text(node, method_body.encode('utf-8'))
                full_field_name = f"{class_name}.{field_name}"

                # Check if field exists in knowledge graph
                field_id = f"field:{full_field_name}"
                if field_id in knowledge_graph.fields:
                    knowledge_graph.add_field_access(method_full_name, full_field_name, "read")
                    print(f"  {method_full_name} reads {full_field_name}")

        # Extract writes
        captures = write_query.captures(root)
        for node, capture_name in captures:
            if capture_name == "field_name":
                field_name = self.parser.extract_text(node, method_body.encode('utf-8'))
                full_field_name = f"{class_name}.{field_name}"

                field_id = f"field:{full_field_name}"
                if field_id in knowledge_graph.fields:
                    knowledge_graph.add_field_access(method_full_name, full_field_name, "write")
                    print(f"  {method_full_name} writes {full_field_name}")

    def extract_endpoints(self, method_node, class_name: str, knowledge_graph: KnowledgeGraph):
        """
        Extract REST endpoint information from controller methods
        """
        endpoint_annotations = {
            'GetMapping': 'GET',
            'PostMapping': 'POST',
            'PutMapping': 'PUT',
            'DeleteMapping': 'DELETE',
            'PatchMapping': 'PATCH',
            'RequestMapping': 'REQUEST'
        }

        for annotation in method_node.annotations:
            if annotation in endpoint_annotations:
                http_method = endpoint_annotations[annotation]

                # For POC, use method name as path
                # TODO: Extract actual path from annotation value
                path = f"/{method_node.name.lower()}"

                from src.knowledge_graph.graph import EndpointNode
                endpoint = EndpointNode(
                    http_method=http_method,
                    path=path,
                    handler_method=method_node.name,
                    handler_class=class_name
                )

                knowledge_graph.add_endpoint(endpoint)
                print(f"  Found endpoint: {http_method} {path} -> {class_name}.{method_node.name}")

    def extract_all_relationships(self, knowledge_graph: KnowledgeGraph):
        """
        Extract all relationships for methods in the knowledge graph
        """
        print("\n=== Extracting Relationships ===")

        for method_id, method_node in knowledge_graph.methods.items():
            print(f"\nAnalyzing: {method_node.class_name}.{method_node.name}")

            # Extract endpoints if this is a controller method
            self.extract_endpoints(method_node, method_node.class_name, knowledge_graph)

            # Extract field accesses
            if method_node.body:
                self.extract_field_accesses(
                    method_node.body,
                    f"{method_node.class_name}.{method_node.name}",
                    method_node.class_name,
                    b"",  # Not needed for parsing method body
                    knowledge_graph
                )

                # Extract method calls
                self.extract_method_calls(
                    method_node.body,
                    f"{method_node.class_name}.{method_node.name}",
                    b"",
                    knowledge_graph
                )
