"""
Graph Summarizer - Creates structured summaries of the knowledge graph
For efficient LLM analysis without hitting token limits
"""
from typing import Dict, List, Any
from collections import Counter
from src.knowledge_graph.graph import KnowledgeGraph


class GraphSummarizer:
    """Creates compact, structured summaries of the knowledge graph for LLM analysis"""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph

    def create_framework_signature(self) -> Dict[str, Any]:
        """
        Create a compact signature of the codebase for framework detection

        Returns a structured summary containing:
        - Annotation counts and patterns
        - Package structure analysis
        - Inheritance patterns
        - Interface implementations
        - Sample representative classes
        """

        signature = {
            "total_classes": len(self.kg.classes),
            "total_methods": len(self.kg.methods),
            "total_fields": len(self.kg.fields),
            "java_type_breakdown": self._count_java_types(),
            "annotation_counts": self._count_annotations(),
            "package_analysis": self._analyze_packages(),
            "inheritance_patterns": self._analyze_inheritance(),
            "interface_patterns": self._analyze_interfaces(),
            "common_superclasses": self._find_common_superclasses(),
            "sample_classes": self._get_representative_samples(),
            "endpoint_patterns": self._analyze_endpoints(),
            "dependency_injection_hints": self._detect_di_patterns()
        }

        return signature

    def _count_java_types(self) -> Dict[str, int]:
        """Count classes, interfaces, enums"""
        counts = {"class": 0, "interface": 0, "enum": 0}

        for class_node in self.kg.classes.values():
            java_type = getattr(class_node, 'java_type', 'class')
            counts[java_type] += 1

        return counts

    def _count_annotations(self) -> Dict[str, int]:
        """Count all annotations across classes and methods"""
        annotation_counter = Counter()

        # Class annotations
        for class_node in self.kg.classes.values():
            for annotation in class_node.annotations:
                annotation_counter[annotation] += 1

        # Method annotations
        for method_node in self.kg.methods.values():
            for annotation in method_node.annotations:
                annotation_counter[annotation] += 1

        # Return top 20 most common
        return dict(annotation_counter.most_common(20))

    def _analyze_packages(self) -> Dict[str, Any]:
        """Analyze package structure to identify framework imports"""
        package_counter = Counter()
        top_level_packages = Counter()

        for class_node in self.kg.classes.values():
            if class_node.package:
                # Count full packages
                package_counter[class_node.package] += 1

                # Count top-level (e.g., "org.springframework" from "org.springframework.web.bind")
                parts = class_node.package.split('.')
                if len(parts) >= 2:
                    top_level = f"{parts[0]}.{parts[1]}"
                    top_level_packages[top_level] += 1

        return {
            "top_packages": dict(package_counter.most_common(10)),
            "top_level_packages": dict(top_level_packages.most_common(10)),
            "total_unique_packages": len(package_counter)
        }

    def _analyze_inheritance(self) -> Dict[str, int]:
        """Analyze what classes extend (inheritance patterns)"""
        superclass_counter = Counter()

        for class_node in self.kg.classes.values():
            if class_node.superclass:
                superclass_counter[class_node.superclass] += 1

        return dict(superclass_counter.most_common(10))

    def _analyze_interfaces(self) -> Dict[str, int]:
        """Analyze what interfaces are implemented"""
        interface_counter = Counter()

        for class_node in self.kg.classes.values():
            for interface in class_node.interfaces:
                interface_counter[interface] += 1

        return dict(interface_counter.most_common(10))

    def _find_common_superclasses(self) -> List[str]:
        """Find commonly extended base classes"""
        superclass_counter = Counter()

        for class_node in self.kg.classes.values():
            if class_node.superclass:
                superclass_counter[class_node.superclass] += 1

        # Return superclasses used by multiple classes
        return [sc for sc, count in superclass_counter.items() if count > 1]

    def _get_representative_samples(self, num_samples: int = 10) -> List[Dict[str, Any]]:
        """Get representative sample classes to show structure"""
        samples = []

        # Prioritize annotated classes
        annotated_classes = [
            cls for cls in self.kg.classes.values()
            if cls.annotations
        ]

        # Take up to num_samples
        for class_node in annotated_classes[:num_samples]:
            samples.append({
                "name": class_node.name,
                "java_type": getattr(class_node, 'java_type', 'class'),
                "package": class_node.package,
                "annotations": class_node.annotations,
                "interfaces": class_node.interfaces,
                "superclass": class_node.superclass,
                "is_abstract": class_node.is_abstract
            })

        return samples

    def _analyze_endpoints(self) -> Dict[str, Any]:
        """Analyze REST endpoints to identify web framework"""
        if not self.kg.endpoints:
            return {"count": 0, "patterns": []}

        method_counter = Counter()
        path_patterns = []

        for endpoint in self.kg.endpoints.values():
            method_counter[endpoint.http_method] += 1
            path_patterns.append(endpoint.path)

        return {
            "count": len(self.kg.endpoints),
            "http_methods": dict(method_counter),
            "sample_paths": path_patterns[:5]
        }

    def _detect_di_patterns(self) -> Dict[str, Any]:
        """Detect dependency injection patterns"""
        di_hints = {
            "autowired_fields": 0,
            "constructor_injection": 0,
            "setter_injection": 0
        }

        # Count @Autowired on fields
        for field_node in self.kg.fields.values():
            if "Autowired" in field_node.annotations:
                di_hints["autowired_fields"] += 1

        # Count @Autowired on methods (constructor/setter injection)
        for method_node in self.kg.methods.values():
            if "Autowired" in method_node.annotations:
                if method_node.name == method_node.class_name.split('.')[-1]:
                    # Constructor
                    di_hints["constructor_injection"] += 1
                elif method_node.name.startswith("set"):
                    # Setter
                    di_hints["setter_injection"] += 1

        return di_hints

    def create_compact_summary(self) -> str:
        """Create a human-readable compact summary"""
        signature = self.create_framework_signature()

        summary_lines = [
            "=== Codebase Structure Summary ===",
            f"Total: {signature['total_classes']} classes ({signature['java_type_breakdown']['class']} classes, "
            f"{signature['java_type_breakdown']['interface']} interfaces, {signature['java_type_breakdown']['enum']} enums)",
            f"Methods: {signature['total_methods']}, Fields: {signature['total_fields']}",
            "",
            "Top Annotations:",
        ]

        for annotation, count in list(signature['annotation_counts'].items())[:5]:
            summary_lines.append(f"  @{annotation}: {count}")

        summary_lines.extend([
            "",
            "Top Packages:",
        ])

        for package, count in list(signature['package_analysis']['top_level_packages'].items())[:5]:
            summary_lines.append(f"  {package}: {count} classes")

        if signature['endpoint_patterns']['count'] > 0:
            summary_lines.extend([
                "",
                f"REST Endpoints: {signature['endpoint_patterns']['count']}",
                f"HTTP Methods: {signature['endpoint_patterns']['http_methods']}"
            ])

        return "\n".join(summary_lines)
