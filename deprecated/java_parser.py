"""
Java Code Parser using tree-sitter
Extracts structural information from Java files
"""
import os
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from tree_sitter import Language, Parser, Node
import tree_sitter_java as tsjava

from src.knowledge_graph.graph import (
    KnowledgeGraph, ClassNode, MethodNode, FieldNode, EndpointNode
)


class JavaParser:
    """
    Parser for Java source files using tree-sitter
    Extracts classes, methods, fields, and their relationships
    """

    def __init__(self):
        """Initialize the Java parser with tree-sitter"""
        self.language = Language(tsjava.language(), 'java')
        self.parser = Parser()
        self.parser.set_language(self.language)

        # Spring annotations that indicate different component types
        self.controller_annotations = {'Controller', 'RestController'}
        self.service_annotations = {'Service'}
        self.repository_annotations = {'Repository'}
        self.entity_annotations = {'Entity', 'Table'}
        self.endpoint_annotations = {
            'GetMapping', 'PostMapping', 'PutMapping',
            'DeleteMapping', 'PatchMapping', 'RequestMapping'
        }

    def parse_file(self, file_path: str) -> Optional[bytes]:
        """Parse a Java file and return the syntax tree"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            return source_code
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def extract_text(self, node: Node, source_code: bytes) -> str:
        """Extract text content from a tree-sitter node"""
        return source_code[node.start_byte:node.end_byte].decode('utf-8')

    def get_package_name(self, tree: Node, source_code: bytes) -> str:
        """Extract package name from the syntax tree"""
        query = self.language.query("(package_declaration (scoped_identifier) @package)")
        captures = query.captures(tree)

        for node, _ in captures:
            return self.extract_text(node, source_code)

        return ""

    def get_annotations(self, node: Node, source_code: bytes) -> List[str]:
        """Extract annotations from a node"""
        annotations = []

        # Look for modifiers node that contains annotations
        for child in node.children:
            if child.type == 'modifiers':
                for modifier_child in child.children:
                    if modifier_child.type == 'marker_annotation':
                        # Get annotation name
                        for ann_child in modifier_child.children:
                            if ann_child.type == 'identifier' or ann_child.type == 'scoped_identifier':
                                ann_name = self.extract_text(ann_child, source_code)
                                annotations.append(ann_name.split('.')[-1])  # Get simple name
                    elif modifier_child.type == 'annotation':
                        # Annotation with parameters
                        for ann_child in modifier_child.children:
                            if ann_child.type == 'identifier' or ann_child.type == 'scoped_identifier':
                                ann_name = self.extract_text(ann_child, source_code)
                                annotations.append(ann_name.split('.')[-1])

        return annotations

    def get_modifiers(self, node: Node, source_code: bytes) -> List[str]:
        """Extract modifiers (public, private, static, etc.) from a node"""
        modifiers = []

        for child in node.children:
            if child.type == 'modifiers':
                for modifier_child in child.children:
                    if modifier_child.type in ['public', 'private', 'protected', 'static', 'final', 'abstract']:
                        modifiers.append(modifier_child.type)

        return modifiers

    def classify_class_type(self, annotations: List[str]) -> str:
        """Determine the class type based on annotations"""
        annotation_set = set(annotations)

        if annotation_set & self.controller_annotations:
            return "Controller"
        elif annotation_set & self.service_annotations:
            return "Service"
        elif annotation_set & self.repository_annotations:
            return "Repository"
        elif annotation_set & self.entity_annotations:
            return "Entity"
        else:
            return "Class"

    def extract_classes(self, tree: Node, source_code: bytes, package: str, file_path: str) -> List[ClassNode]:
        """Extract all class declarations from the syntax tree"""
        classes = []

        query = self.language.query("""
            (class_declaration
                name: (identifier) @class_name
            ) @class
        """)

        captures = query.captures(tree)

        # Group captures by class node
        class_nodes = {}
        for node, capture_name in captures:
            if capture_name == "class":
                class_nodes[node.id] = {"node": node}
            elif capture_name == "class_name":
                # Find parent class node
                parent = node.parent
                while parent and parent.type != 'class_declaration':
                    parent = parent.parent
                if parent and parent.id in class_nodes:
                    class_nodes[parent.id]["name"] = self.extract_text(node, source_code)

        for class_data in class_nodes.values():
            if "name" not in class_data:
                continue

            node = class_data["node"]
            name = class_data["name"]

            annotations = self.get_annotations(node, source_code)
            modifiers = self.get_modifiers(node, source_code)
            class_type = self.classify_class_type(annotations)

            # Get superclass and interfaces
            superclass = None
            interfaces = []

            for child in node.children:
                if child.type == 'superclass':
                    for subchild in child.children:
                        if subchild.type == 'type_identifier':
                            superclass = self.extract_text(subchild, source_code)
                elif child.type == 'super_interfaces':
                    for subchild in child.children:
                        if subchild.type == 'type_list':
                            for interface_node in subchild.children:
                                if interface_node.type == 'type_identifier':
                                    interfaces.append(self.extract_text(interface_node, source_code))

            class_node = ClassNode(
                name=name,
                package=package,
                file_path=file_path,
                class_type=class_type,
                modifiers=modifiers,
                annotations=annotations,
                interfaces=interfaces,
                superclass=superclass,
                is_abstract='abstract' in modifiers
            )

            classes.append(class_node)

        return classes

    def extract_methods(self, tree: Node, source_code: bytes, class_name: str) -> List[MethodNode]:
        """Extract all method declarations from a class"""
        methods = []

        query = self.language.query("""
            (method_declaration
                name: (identifier) @method_name
            ) @method
        """)

        captures = query.captures(tree)

        # Group captures by method node
        method_nodes = {}
        for node, capture_name in captures:
            if capture_name == "method":
                method_nodes[node.id] = {"node": node}
            elif capture_name == "method_name":
                parent = node.parent
                if parent and parent.id in method_nodes:
                    method_nodes[parent.id]["name"] = self.extract_text(node, source_code)

        for method_data in method_nodes.values():
            if "name" not in method_data:
                continue

            node = method_data["node"]
            name = method_data["name"]

            # Extract return type manually from method node
            return_type = "void"
            for child in node.children:
                if child.type in ['type_identifier', 'integral_type', 'floating_point_type',
                                  'boolean_type', 'void_type', 'generic_type']:
                    return_type = self.extract_text(child, source_code)
                    break

            annotations = self.get_annotations(node, source_code)
            modifiers = self.get_modifiers(node, source_code)

            # Extract parameters
            parameters = []
            for child in node.children:
                if child.type == 'formal_parameters':
                    for param in child.children:
                        if param.type == 'formal_parameter':
                            param_type = None
                            param_name = None
                            for param_child in param.children:
                                if param_child.type in ['type_identifier', 'integral_type', 'floating_point_type', 'boolean_type', 'generic_type']:
                                    param_type = self.extract_text(param_child, source_code)
                                elif param_child.type == 'identifier':
                                    param_name = self.extract_text(param_child, source_code)

                            if param_type and param_name:
                                parameters.append({"type": param_type, "name": param_name})

            # Get method body
            body = None
            for child in node.children:
                if child.type == 'block':
                    body = self.extract_text(child, source_code)

            # Build signature
            param_types = [p["type"] for p in parameters]
            signature = f"{name}({', '.join(param_types)})"

            method_node = MethodNode(
                name=name,
                class_name=class_name,
                signature=signature,
                return_type=return_type,
                parameters=parameters,
                modifiers=modifiers,
                annotations=annotations,
                body=body,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1
            )

            methods.append(method_node)

        return methods

    def extract_fields(self, tree: Node, source_code: bytes, class_name: str) -> List[FieldNode]:
        """Extract all field declarations from a class"""
        fields = []

        query = self.language.query("""
            (field_declaration) @field
        """)

        captures = query.captures(tree)

        for node, capture_name in captures:
            if capture_name != "field":
                continue

            # Extract field type
            field_type = "unknown"
            field_names = []

            for child in node.children:
                if child.type in ['type_identifier', 'integral_type', 'floating_point_type',
                                  'boolean_type', 'generic_type']:
                    field_type = self.extract_text(child, source_code)
                elif child.type == 'variable_declarator':
                    # Get field name
                    for var_child in child.children:
                        if var_child.type == 'identifier':
                            field_names.append(self.extract_text(var_child, source_code))

            annotations = self.get_annotations(node, source_code)
            modifiers = self.get_modifiers(node, source_code)

            # Handle multiple field declarations (e.g., int a, b, c;)
            for field_name in field_names:
                field_node = FieldNode(
                    name=field_name,
                    class_name=class_name,
                    field_type=field_type,
                    modifiers=modifiers,
                    annotations=annotations
                )
                fields.append(field_node)

        return fields

    def parse_java_file(self, file_path: str, knowledge_graph: KnowledgeGraph):
        """
        Parse a single Java file and populate the knowledge graph
        """
        source_code = self.parse_file(file_path)
        if not source_code:
            return

        tree = self.parser.parse(source_code)
        root_node = tree.root_node

        # Extract package
        package = self.get_package_name(root_node, source_code)

        # Extract classes
        classes = self.extract_classes(root_node, source_code, package, file_path)

        for class_node in classes:
            # Add class to knowledge graph
            class_id = knowledge_graph.add_class(class_node)

            full_class_name = f"{package}.{class_node.name}" if package else class_node.name

            # Find the class node in the tree to extract its methods and fields
            query = self.language.query(f"""
                (class_declaration
                    name: (identifier) @name
                ) @class
            """)

            captures = query.captures(root_node)
            for node, capture_name in captures:
                if capture_name == "name":
                    if self.extract_text(node, source_code) == class_node.name:
                        class_tree_node = node.parent

                        # Extract methods
                        methods = self.extract_methods(class_tree_node, source_code, full_class_name)
                        for method in methods:
                            knowledge_graph.add_method(method)

                        # Extract fields
                        fields = self.extract_fields(class_tree_node, source_code, full_class_name)
                        for field in fields:
                            knowledge_graph.add_field(field)

    def parse_directory(self, directory_path: str, knowledge_graph: KnowledgeGraph):
        """
        Recursively parse all Java files in a directory
        """
        directory = Path(directory_path)

        java_files = list(directory.rglob("*.java"))
        print(f"Found {len(java_files)} Java files in {directory_path}")

        for java_file in java_files:
            print(f"Parsing: {java_file}")
            self.parse_java_file(str(java_file), knowledge_graph)

        print(f"\nParsing complete!")
        stats = knowledge_graph.get_stats()
        print(f"Knowledge Graph Stats: {stats}")
