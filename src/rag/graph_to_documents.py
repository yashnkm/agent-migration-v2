"""
Convert KnowledgeGraph to LangChain Documents for RAG
Each class/interface/enum/method becomes a searchable document
"""
from typing import List
from langchain_core.documents import Document
from src.knowledge_graph.graph import KnowledgeGraph


class GraphDocumentConverter:
    """Converts KnowledgeGraph to LangChain Documents"""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph

    def convert_to_documents(self) -> List[Document]:
        """
        Convert entire knowledge graph to documents

        Returns:
            List of Document objects with metadata
        """
        documents = []

        # Convert classes/interfaces/enums
        documents.extend(self._convert_classes())

        # Convert methods (important for understanding behavior)
        documents.extend(self._convert_methods())

        # Convert endpoints (REST APIs)
        documents.extend(self._convert_endpoints())

        print(f"Created {len(documents)} documents from knowledge graph")
        return documents

    def _convert_classes(self) -> List[Document]:
        """Convert all classes/interfaces/enums to documents"""
        documents = []

        for class_id, class_node in self.kg.classes.items():
            # Create rich text content
            content_parts = [
                f"Type: {class_node.java_type.upper()}",
                f"Name: {class_node.name}",
                f"Full Name: {class_node.package}.{class_node.name}" if class_node.package else f"Name: {class_node.name}",
                f"Package: {class_node.package}" if class_node.package else "",
                f"Classification: {class_node.class_type}" if class_node.class_type else "",
            ]

            # Add annotations
            if class_node.annotations:
                content_parts.append(f"Annotations: {', '.join([f'@{ann}' for ann in class_node.annotations])}")

            # Add inheritance info
            if class_node.superclass:
                content_parts.append(f"Extends: {class_node.superclass}")

            if class_node.interfaces:
                content_parts.append(f"Implements: {', '.join(class_node.interfaces)}")

            # Add modifiers
            if class_node.is_abstract:
                content_parts.append("Modifier: Abstract")

            # Get methods in this class
            class_methods = [
                method.name for method in self.kg.methods.values()
                if method.class_name == f"{class_node.package}.{class_node.name}"
            ]
            if class_methods:
                content_parts.append(f"Methods ({len(class_methods)}): {', '.join(class_methods[:10])}")
                if len(class_methods) > 10:
                    content_parts.append(f"... and {len(class_methods) - 10} more methods")

            # Get fields in this class
            class_fields = [
                field.name for field in self.kg.fields.values()
                if field.class_name == f"{class_node.package}.{class_node.name}"
            ]
            if class_fields:
                content_parts.append(f"Fields ({len(class_fields)}): {', '.join(class_fields[:10])}")

            page_content = "\n".join([part for part in content_parts if part])

            # Create document with rich metadata
            doc = Document(
                page_content=page_content,
                metadata={
                    "type": "class",
                    "java_type": class_node.java_type,
                    "class_name": class_node.name,
                    "full_name": f"{class_node.package}.{class_node.name}",
                    "package": class_node.package or "",
                    "classification": class_node.class_type or "Unknown",
                    "annotations": class_node.annotations,
                    "superclass": class_node.superclass or "",
                    "interfaces": class_node.interfaces,
                    "is_abstract": class_node.is_abstract,
                    "file_path": class_node.file_path,
                    "method_count": len(class_methods),
                    "field_count": len(class_fields)
                }
            )

            documents.append(doc)

        return documents

    def _convert_methods(self) -> List[Document]:
        """Convert methods to documents (for behavior analysis)"""
        documents = []

        for method_id, method_node in self.kg.methods.items():
            # Create content
            content_parts = [
                f"Type: METHOD",
                f"Method Name: {method_node.name}",
                f"Class: {method_node.class_name}",
                f"Return Type: {method_node.return_type}" if method_node.return_type else "",
            ]

            # Add parameters
            if method_node.parameters:
                params = [f"{p['name']}: {p['type']}" for p in method_node.parameters]
                content_parts.append(f"Parameters: {', '.join(params)}")

            # Add annotations
            if method_node.annotations:
                content_parts.append(f"Annotations: {', '.join([f'@{ann}' for ann in method_node.annotations])}")

            page_content = "\n".join([part for part in content_parts if part])

            doc = Document(
                page_content=page_content,
                metadata={
                    "type": "method",
                    "method_name": method_node.name,
                    "class_name": method_node.class_name,
                    "return_type": method_node.return_type or "",
                    "annotations": method_node.annotations,
                    "parameter_count": len(method_node.parameters) if method_node.parameters else 0
                }
            )

            documents.append(doc)

        return documents

    def _convert_endpoints(self) -> List[Document]:
        """Convert REST endpoints to documents"""
        documents = []

        for endpoint_id, endpoint in self.kg.endpoints.items():
            # Create content
            content_parts = [
                f"Type: REST ENDPOINT",
                f"HTTP Method: {endpoint.http_method}",
                f"Path: {endpoint.path}",
                f"Handler Class: {endpoint.handler_class}",
                f"Handler Method: {endpoint.handler_method}",
            ]

            page_content = "\n".join(content_parts)

            doc = Document(
                page_content=page_content,
                metadata={
                    "type": "endpoint",
                    "http_method": endpoint.http_method,
                    "path": endpoint.path,
                    "handler_class": endpoint.handler_class,
                    "handler_method": endpoint.handler_method
                }
            )

            documents.append(doc)

        return documents


def convert_graph_to_documents(knowledge_graph: KnowledgeGraph) -> List[Document]:
    """
    Convenience function to convert KnowledgeGraph to documents

    Args:
        knowledge_graph: The knowledge graph to convert

    Returns:
        List of LangChain Document objects
    """
    converter = GraphDocumentConverter(knowledge_graph)
    return converter.convert_to_documents()
