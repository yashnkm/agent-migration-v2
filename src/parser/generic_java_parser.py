"""
Generic Java Parser - Framework Agnostic
Extracts ALL code elements WITHOUT classification or filtering
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
from tree_sitter import Language, Parser, Node
import tree_sitter_java as tsjava

from src.knowledge_graph.graph import KnowledgeGraph, ClassNode, MethodNode, FieldNode


class GenericJavaParser:
    """
    Framework-agnostic Java parser
    Extracts everything WITHOUT hardcoded framework patterns

    Philosophy:
    - Extract ALL annotations (don't check if they match specific frameworks)
    - Don't classify class types (Controller/Service/etc.)
    - Store raw data, let inference engine classify later
    """

    def __init__(self):
        """Initialize tree-sitter parser"""
        self.language = Language(tsjava.language(), 'java')
        self.parser = Parser()
        self.parser.set_language(self.language)

    def parse_file(self, file_path: str) -> Optional[bytes]:
        """Read and return file content"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

    def extract_text(self, node: Node, source_code: bytes) -> str:
        """Extract text from node"""
        return source_code[node.start_byte:node.end_byte].decode('utf-8')

    def get_package_name(self, tree: Node, source_code: bytes) -> str:
        """Extract package name"""
        query = self.language.query("(package_declaration (scoped_identifier) @package)")
        captures = query.captures(tree)

        for node, _ in captures:
            return self.extract_text(node, source_code)
        return ""

    def get_all_annotations(self, node: Node, source_code: bytes) -> List[Dict[str, Any]]:
        """
        Extract ALL annotations without filtering
        Returns detailed annotation info including values
        """
        annotations = []

        for child in node.children:
            if child.type == 'modifiers':
                for modifier_child in child.children:
                    if modifier_child.type in ['marker_annotation', 'annotation']:
                        annotation_data = self._parse_annotation(modifier_child, source_code)
                        if annotation_data:
                            annotations.append(annotation_data)

        return annotations

    def _parse_annotation(self, node: Node, source_code: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse annotation with all its details
        Example: @RequestMapping(value="/api", method=RequestMethod.GET)
        """
        annotation_name = None
        annotation_values = {}

        for child in node.children:
            if child.type in ['identifier', 'scoped_identifier']:
                annotation_name = self.extract_text(child, source_code)
                # Get simple name (last part)
                annotation_name = annotation_name.split('.')[-1]

            elif child.type == 'annotation_argument_list':
                # Parse annotation parameters
                annotation_values = self._parse_annotation_arguments(child, source_code)

        if annotation_name:
            return {
                'name': annotation_name,
                'values': annotation_values,
                'raw': self.extract_text(node, source_code)
            }

        return None

    def _parse_annotation_arguments(self, node: Node, source_code: bytes) -> Dict[str, str]:
        """Parse annotation argument list"""
        arguments = {}

        for child in node.children:
            if child.type == 'element_value_pair':
                key = None
                value = None

                for pair_child in child.children:
                    if pair_child.type == 'identifier':
                        key = self.extract_text(pair_child, source_code)
                    elif pair_child.type == 'string_literal':
                        value = self.extract_text(pair_child, source_code).strip('"')

                if key and value:
                    arguments[key] = value

            elif child.type == 'string_literal':
                # Single value annotation: @Path("/users")
                arguments['value'] = self.extract_text(child, source_code).strip('"')

        return arguments

    def get_modifiers(self, node: Node, source_code: bytes) -> List[str]:
        """Extract modifiers (public, private, static, etc.)"""
        modifiers = []

        for child in node.children:
            if child.type == 'modifiers':
                for modifier_child in child.children:
                    if modifier_child.type in ['public', 'private', 'protected',
                                               'static', 'final', 'abstract', 'synchronized']:
                        modifiers.append(modifier_child.type)

        return modifiers

    def extract_classes(self, tree: Node, source_code: bytes,
                       package: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract all classes, interfaces, and enums WITHOUT classification
        No Controller/Service/Entity detection here
        """
        classes = []

        # Query for classes, interfaces, and enums
        query = self.language.query("""
            [
                (class_declaration
                    name: (identifier) @class_name
                ) @class

                (interface_declaration
                    name: (identifier) @interface_name
                ) @interface

                (enum_declaration
                    name: (identifier) @enum_name
                ) @enum
            ]
        """)

        captures = query.captures(tree)

        # Group captures and determine type
        class_nodes = {}
        for node, capture_name in captures:
            if capture_name in ["class", "interface", "enum"]:
                # Determine java_type from capture name
                java_type = "class" if capture_name == "class" else capture_name
                class_nodes[node.id] = {"node": node, "java_type": java_type}
            elif capture_name in ["class_name", "interface_name", "enum_name"]:
                parent = node.parent
                # Find parent declaration
                while parent and parent.type not in ['class_declaration', 'interface_declaration', 'enum_declaration']:
                    parent = parent.parent
                if parent and parent.id in class_nodes:
                    class_nodes[parent.id]["name"] = self.extract_text(node, source_code)

        for class_data in class_nodes.values():
            if "name" not in class_data:
                continue

            node = class_data["node"]
            name = class_data["name"]

            # Extract ALL annotations (no filtering)
            annotations = self.get_all_annotations(node, source_code)
            modifiers = self.get_modifiers(node, source_code)

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

            classes.append({
                'name': name,
                'package': package,
                'file_path': file_path,
                'java_type': class_data.get('java_type', 'class'),  # class, interface, or enum
                'annotations': annotations,  # Detailed annotation info
                'modifiers': modifiers,
                'interfaces': interfaces,
                'superclass': superclass,
                'is_abstract': 'abstract' in modifiers,
                'node': node  # Keep for method/field extraction
            })

        return classes

    def extract_methods(self, class_node: Node, source_code: bytes,
                       class_name: str) -> List[Dict[str, Any]]:
        """Extract all methods WITHOUT endpoint detection"""
        methods = []

        query = self.language.query("""
            (method_declaration
                name: (identifier) @method_name
            ) @method
        """)

        captures = query.captures(class_node)

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

            # Extract return type
            return_type = "void"
            for child in node.children:
                if child.type in ['type_identifier', 'integral_type',
                                  'floating_point_type', 'boolean_type',
                                  'void_type', 'generic_type']:
                    return_type = self.extract_text(child, source_code)
                    break

            # Extract ALL annotations (no filtering)
            annotations = self.get_all_annotations(node, source_code)
            modifiers = self.get_modifiers(node, source_code)

            # Extract parameters
            parameters = []
            for child in node.children:
                if child.type == 'formal_parameters':
                    parameters = self._extract_parameters(child, source_code)

            # Get method body
            body = None
            for child in node.children:
                if child.type == 'block':
                    body = self.extract_text(child, source_code)

            # Build signature
            param_types = [p["type"] for p in parameters]
            signature = f"{name}({', '.join(param_types)})"

            methods.append({
                'name': name,
                'class_name': class_name,
                'signature': signature,
                'return_type': return_type,
                'parameters': parameters,
                'modifiers': modifiers,
                'annotations': annotations,  # Detailed annotations
                'body': body,
                'line_start': node.start_point[0] + 1,
                'line_end': node.end_point[0] + 1
            })

        return methods

    def _extract_parameters(self, params_node: Node, source_code: bytes) -> List[Dict[str, str]]:
        """Extract method parameters"""
        parameters = []

        for param in params_node.children:
            if param.type == 'formal_parameter':
                param_type = None
                param_name = None
                param_annotations = []

                for param_child in param.children:
                    if param_child.type in ['type_identifier', 'integral_type',
                                           'floating_point_type', 'boolean_type', 'generic_type']:
                        param_type = self.extract_text(param_child, source_code)
                    elif param_child.type == 'identifier':
                        param_name = self.extract_text(param_child, source_code)
                    elif param_child.type == 'modifiers':
                        # Extract parameter annotations
                        param_annotations = self.get_all_annotations(param, source_code)

                if param_type and param_name:
                    parameters.append({
                        "type": param_type,
                        "name": param_name,
                        "annotations": param_annotations
                    })

        return parameters

    def extract_fields(self, class_node: Node, source_code: bytes,
                      class_name: str) -> List[Dict[str, Any]]:
        """Extract all fields"""
        fields = []

        query = self.language.query("(field_declaration) @field")
        captures = query.captures(class_node)

        for node, capture_name in captures:
            if capture_name != "field":
                continue

            field_type = "unknown"
            field_names = []

            for child in node.children:
                if child.type in ['type_identifier', 'integral_type',
                                  'floating_point_type', 'boolean_type', 'generic_type']:
                    field_type = self.extract_text(child, source_code)

                elif child.type == 'variable_declarator':
                    for var_child in child.children:
                        if var_child.type == 'identifier':
                            field_names.append(self.extract_text(var_child, source_code))

            annotations = self.get_all_annotations(node, source_code)
            modifiers = self.get_modifiers(node, source_code)

            for field_name in field_names:
                fields.append({
                    'name': field_name,
                    'class_name': class_name,
                    'field_type': field_type,
                    'modifiers': modifiers,
                    'annotations': annotations  # Detailed annotations
                })

        return fields

    def parse_java_file(self, file_path: str, knowledge_graph: KnowledgeGraph):
        """
        Parse a Java file and populate knowledge graph
        WITHOUT any classification
        """
        source_code = self.parse_file(file_path)
        if not source_code:
            return

        tree = self.parser.parse(source_code)
        root_node = tree.root_node

        package = self.get_package_name(root_node, source_code)
        classes = self.extract_classes(root_node, source_code, package, file_path)

        for class_data in classes:
            # Store class/interface/enum WITHOUT type classification
            class_node = ClassNode(
                name=class_data['name'],
                package=class_data['package'],
                file_path=class_data['file_path'],
                class_type="UNCLASSIFIED",  # Will be inferred later (Controller/Service/etc)
                java_type=class_data['java_type'],  # class, interface, or enum
                modifiers=class_data['modifiers'],
                annotations=[ann['name'] for ann in class_data['annotations']],  # Store names
                interfaces=class_data['interfaces'],
                superclass=class_data['superclass'],
                is_abstract=class_data['is_abstract']
            )

            class_id = knowledge_graph.add_class(class_node)
            full_class_name = f"{package}.{class_data['name']}" if package else class_data['name']

            # Store detailed annotations separately
            knowledge_graph.graph.nodes[class_id]['detailed_annotations'] = class_data['annotations']

            # Extract methods
            methods = self.extract_methods(class_data['node'], source_code, full_class_name)
            for method_data in methods:
                method_node = MethodNode(
                    name=method_data['name'],
                    class_name=method_data['class_name'],
                    signature=method_data['signature'],
                    return_type=method_data['return_type'],
                    parameters=method_data['parameters'],
                    modifiers=method_data['modifiers'],
                    annotations=[ann['name'] for ann in method_data['annotations']],
                    body=method_data['body'],
                    line_start=method_data['line_start'],
                    line_end=method_data['line_end']
                )
                method_id = knowledge_graph.add_method(method_node)

                # Store detailed annotations
                knowledge_graph.graph.nodes[method_id]['detailed_annotations'] = method_data['annotations']

            # Extract fields
            fields = self.extract_fields(class_data['node'], source_code, full_class_name)
            for field_data in fields:
                field_node = FieldNode(
                    name=field_data['name'],
                    class_name=field_data['class_name'],
                    field_type=field_data['field_type'],
                    modifiers=field_data['modifiers'],
                    annotations=[ann['name'] for ann in field_data['annotations']]
                )
                field_id = knowledge_graph.add_field(field_node)

                # Store detailed annotations
                knowledge_graph.graph.nodes[field_id]['detailed_annotations'] = field_data['annotations']

    def parse_directory(self, directory_path: str, knowledge_graph: KnowledgeGraph):
        """Parse all Java files in directory"""
        directory = Path(directory_path)
        java_files = list(directory.rglob("*.java"))

        print(f"Found {len(java_files)} Java files")

        for java_file in java_files:
            print(f"Parsing: {java_file}")
            self.parse_java_file(str(java_file), knowledge_graph)

        print(f"\nParsing complete!")
        stats = knowledge_graph.get_stats()
        print(f"   Classes: {stats['classes']}")
        print(f"   Methods: {stats['methods']}")
        print(f"   Fields: {stats['fields']}")
