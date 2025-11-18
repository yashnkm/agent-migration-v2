"""
Presentation Layer Extractor
Extracts controllers, actions, servlets, and REST resources based on detected framework
Uses rule-based pattern matching on parsed annotations and class structure
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from src.knowledge_graph.graph import KnowledgeGraph, ClassNode, MethodNode


@dataclass
class EndpointInfo:
    """Information about a REST endpoint or action"""
    http_method: str  # GET, POST, PUT, DELETE, etc.
    path: str  # URL path
    handler_method: str  # Method name that handles this endpoint
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: str = ""
    annotations: List[str] = field(default_factory=list)


@dataclass
class ControllerInfo:
    """Information about a controller/action/servlet"""
    name: str
    package: str
    file_path: str
    type: str  # "Controller", "Action", "Servlet", "Resource"
    base_path: str = ""  # Base URL path (for REST controllers)
    endpoints: List[EndpointInfo] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Services used
    annotations: List[str] = field(default_factory=list)


@dataclass
class PresentationLayerInfo:
    """Complete presentation layer analysis"""
    framework: str
    controllers: List[ControllerInfo]
    total_controllers: int
    total_endpoints: int
    summary: str


class PresentationLayerExtractor:
    """
    Extracts presentation layer components based on framework
    """

    # Framework-specific patterns
    # Note: Annotations are stored WITHOUT @ symbol by the parser
    FRAMEWORK_PATTERNS = {
        "Spring Boot": {
            "class_annotations": ["RestController", "Controller"],
            "base_path_annotations": ["RequestMapping"],
            "method_annotations": {
                "GetMapping": "GET",
                "PostMapping": "POST",
                "PutMapping": "PUT",
                "DeleteMapping": "DELETE",
                "PatchMapping": "PATCH",
                "RequestMapping": "REQUEST"  # Can be any method
            }
        },
        "Struts": {
            "class_superclasses": ["ActionSupport", "Action"],
            "class_name_patterns": ["Action$"],  # Ends with "Action"
            "method_names": ["execute"],
            "config_files": ["struts.xml", "struts-config.xml"]
        },
        "Struts 2": {
            "class_superclasses": ["ActionSupport", "Action"],
            "class_name_patterns": ["Action$"],
            "method_names": ["execute"],
            "config_files": ["struts.xml"]
        },
        "JAX-RS": {
            "class_annotations": ["Path"],
            "method_annotations": {
                "GET": "GET",
                "POST": "POST",
                "PUT": "PUT",
                "DELETE": "DELETE",
                "HEAD": "HEAD",
                "OPTIONS": "OPTIONS"
            }
        },
        "Servlet/JSP": {
            "class_superclasses": ["HttpServlet", "GenericServlet"],
            "method_names": ["doGet", "doPost", "doPut", "doDelete", "service"]
        },
        "Jakarta EE": {
            "class_annotations": ["Path", "RestController"],
            "method_annotations": {
                "GET": "GET",
                "POST": "POST",
                "PUT": "PUT",
                "DELETE": "DELETE"
            }
        }
    }

    def __init__(self):
        pass

    def extract(
        self,
        knowledge_graph: KnowledgeGraph,
        framework: str
    ) -> PresentationLayerInfo:
        """
        Extract presentation layer based on detected framework

        Args:
            knowledge_graph: Parsed knowledge graph
            framework: Detected framework name

        Returns:
            PresentationLayerInfo with all controllers/actions
        """
        # Normalize framework name
        framework_key = self._normalize_framework_name(framework)

        if framework_key not in self.FRAMEWORK_PATTERNS:
            # Fallback: try to detect any common patterns
            framework_key = "Spring Boot"  # Default to most common

        patterns = self.FRAMEWORK_PATTERNS[framework_key]

        # Extract presentation layer classes
        controllers = []

        if framework_key == "Spring Boot":
            controllers = self._extract_spring_boot_controllers(knowledge_graph, patterns)
        elif framework_key in ["Struts", "Struts 2"]:
            controllers = self._extract_struts_actions(knowledge_graph, patterns)
        elif framework_key == "JAX-RS" or framework_key == "Jakarta EE":
            controllers = self._extract_jaxrs_resources(knowledge_graph, patterns)
        elif framework_key == "Servlet/JSP":
            controllers = self._extract_servlets(knowledge_graph, patterns)
        else:
            # Generic extraction
            controllers = self._extract_generic(knowledge_graph)

        # Calculate totals
        total_controllers = len(controllers)
        total_endpoints = sum(len(c.endpoints) for c in controllers)

        # Generate summary
        summary = self._generate_summary(framework_key, total_controllers, total_endpoints)

        return PresentationLayerInfo(
            framework=framework,
            controllers=controllers,
            total_controllers=total_controllers,
            total_endpoints=total_endpoints,
            summary=summary
        )

    def _normalize_framework_name(self, framework: str) -> str:
        """Normalize framework name to match patterns"""
        framework_lower = framework.lower()

        if "spring" in framework_lower:
            return "Spring Boot"
        elif "struts 2" in framework_lower:
            return "Struts 2"
        elif "struts" in framework_lower:
            return "Struts"
        elif "jax-rs" in framework_lower or "jaxrs" in framework_lower:
            return "JAX-RS"
        elif "jakarta" in framework_lower:
            return "Jakarta EE"
        elif "servlet" in framework_lower or "jsp" in framework_lower:
            return "Servlet/JSP"
        else:
            return framework

    def _extract_spring_boot_controllers(
        self,
        kg: KnowledgeGraph,
        patterns: Dict
    ) -> List[ControllerInfo]:
        """Extract Spring Boot controllers"""
        controllers = []

        for class_id, class_node in kg.classes.items():
            # Check if class has @RestController or @Controller
            # Use substring matching to handle annotation variations
            has_controller_annotation = False
            for ann in class_node.annotations:
                for pattern in patterns["class_annotations"]:
                    if pattern in ann:
                        has_controller_annotation = True
                        break
                if has_controller_annotation:
                    break

            if not has_controller_annotation:
                continue

            # Extract base path from @RequestMapping at class level
            base_path = self._extract_path_from_annotations(
                class_node.annotations,
                patterns["base_path_annotations"]
            )

            # Extract endpoints from methods
            endpoints = []
            for method_id, method_node in kg.methods.items():
                if method_node.class_name != f"{class_node.package}.{class_node.name}":
                    continue

                # Check for mapping annotations
                for annotation in method_node.annotations:
                    for mapping_ann, http_method in patterns["method_annotations"].items():
                        if mapping_ann in annotation:
                            method_path = self._extract_path_from_annotation(annotation)
                            full_path = base_path + method_path

                            endpoint = EndpointInfo(
                                http_method=http_method,
                                path=full_path,
                                handler_method=method_node.name,
                                parameters=method_node.parameters,
                                return_type=method_node.return_type,
                                annotations=method_node.annotations
                            )
                            endpoints.append(endpoint)

            # Extract dependencies (autowired services)
            dependencies = self._extract_dependencies(class_node, kg)

            controller = ControllerInfo(
                name=class_node.name,
                package=class_node.package,
                file_path=class_node.file_path,
                type="RestController" if "RestController" in str(class_node.annotations) else "Controller",
                base_path=base_path,
                endpoints=endpoints,
                dependencies=dependencies,
                annotations=class_node.annotations
            )
            controllers.append(controller)

        return controllers

    def _extract_struts_actions(
        self,
        kg: KnowledgeGraph,
        patterns: Dict
    ) -> List[ControllerInfo]:
        """Extract Struts action classes"""
        controllers = []

        for class_id, class_node in kg.classes.items():
            # Check if class extends ActionSupport or Action
            is_action = False

            if class_node.superclass:
                if any(sc in class_node.superclass for sc in patterns.get("class_superclasses", [])):
                    is_action = True

            # Or check if class name ends with "Action"
            if class_node.name.endswith("Action"):
                is_action = True

            if not is_action:
                continue

            # Extract execute methods
            endpoints = []
            for method_id, method_node in kg.methods.items():
                if method_node.class_name != f"{class_node.package}.{class_node.name}":
                    continue

                # Struts actions typically have execute() method
                if method_node.name in patterns.get("method_names", []):
                    endpoint = EndpointInfo(
                        http_method="ACTION",
                        path=f"/{class_node.name.replace('Action', '').lower()}",
                        handler_method=method_node.name,
                        parameters=method_node.parameters,
                        return_type=method_node.return_type,
                        annotations=method_node.annotations
                    )
                    endpoints.append(endpoint)

            dependencies = self._extract_dependencies(class_node, kg)

            controller = ControllerInfo(
                name=class_node.name,
                package=class_node.package,
                file_path=class_node.file_path,
                type="Action",
                endpoints=endpoints,
                dependencies=dependencies,
                annotations=class_node.annotations
            )
            controllers.append(controller)

        return controllers

    def _extract_jaxrs_resources(
        self,
        kg: KnowledgeGraph,
        patterns: Dict
    ) -> List[ControllerInfo]:
        """Extract JAX-RS resource classes"""
        controllers = []

        for class_id, class_node in kg.classes.items():
            # Check if class has @Path annotation (stored without @)
            if not any("Path" in ann for ann in class_node.annotations):
                continue

            # Extract base path from @Path at class level
            base_path = self._extract_path_from_annotations(
                class_node.annotations,
                ["Path"]
            )

            # Extract endpoints from methods
            endpoints = []
            for method_id, method_node in kg.methods.items():
                if method_node.class_name != f"{class_node.package}.{class_node.name}":
                    continue

                # Check for HTTP method annotations
                for annotation in method_node.annotations:
                    for http_ann, http_method in patterns["method_annotations"].items():
                        if http_ann in annotation:
                            method_path = self._extract_path_from_annotations(
                                method_node.annotations, ["Path"]
                            )
                            full_path = base_path + method_path

                            endpoint = EndpointInfo(
                                http_method=http_method,
                                path=full_path,
                                handler_method=method_node.name,
                                parameters=method_node.parameters,
                                return_type=method_node.return_type,
                                annotations=method_node.annotations
                            )
                            endpoints.append(endpoint)

            dependencies = self._extract_dependencies(class_node, kg)

            controller = ControllerInfo(
                name=class_node.name,
                package=class_node.package,
                file_path=class_node.file_path,
                type="Resource",
                base_path=base_path,
                endpoints=endpoints,
                dependencies=dependencies,
                annotations=class_node.annotations
            )
            controllers.append(controller)

        return controllers

    def _extract_servlets(
        self,
        kg: KnowledgeGraph,
        patterns: Dict
    ) -> List[ControllerInfo]:
        """Extract Servlet classes"""
        controllers = []

        for class_id, class_node in kg.classes.items():
            # Check if class extends HttpServlet
            if not class_node.superclass:
                continue

            if not any(sc in class_node.superclass for sc in patterns.get("class_superclasses", [])):
                continue

            # Extract doGet, doPost, etc. methods
            endpoints = []
            for method_id, method_node in kg.methods.items():
                if method_node.class_name != f"{class_node.package}.{class_node.name}":
                    continue

                if method_node.name in patterns.get("method_names", []):
                    http_method = method_node.name.replace("do", "").upper()

                    endpoint = EndpointInfo(
                        http_method=http_method,
                        path=f"/{class_node.name}",  # Servlet mapping usually in web.xml
                        handler_method=method_node.name,
                        parameters=method_node.parameters,
                        return_type=method_node.return_type,
                        annotations=method_node.annotations
                    )
                    endpoints.append(endpoint)

            dependencies = self._extract_dependencies(class_node, kg)

            controller = ControllerInfo(
                name=class_node.name,
                package=class_node.package,
                file_path=class_node.file_path,
                type="Servlet",
                endpoints=endpoints,
                dependencies=dependencies,
                annotations=class_node.annotations
            )
            controllers.append(controller)

        return controllers

    def _extract_generic(self, kg: KnowledgeGraph) -> List[ControllerInfo]:
        """Generic extraction - try to find any controller-like classes"""
        controllers = []

        # Look for common patterns
        controller_keywords = ["Controller", "Action", "Servlet", "Resource", "Endpoint"]

        for class_id, class_node in kg.classes.items():
            # Check if class name contains controller keywords
            if any(keyword in class_node.name for keyword in controller_keywords):
                controller = ControllerInfo(
                    name=class_node.name,
                    package=class_node.package,
                    file_path=class_node.file_path,
                    type="Controller",
                    annotations=class_node.annotations
                )
                controllers.append(controller)

        return controllers

    def _extract_path_from_annotations(
        self,
        annotations: List[str],
        path_annotations: List[str]
    ) -> str:
        """Extract path from annotations like @RequestMapping('/api/users')"""
        for annotation in annotations:
            for path_ann in path_annotations:
                if path_ann in annotation:
                    return self._extract_path_from_annotation(annotation)
        return ""

    def _extract_path_from_annotation(self, annotation: str) -> str:
        """
        Extract path from annotation string
        Examples:
          @RequestMapping("/api/users") -> /api/users
          @GetMapping(value="/list") -> /list
          @Path("/users") -> /users
        """
        # Try to extract path from annotation
        # Look for patterns like ("/path") or (value="/path")

        # Pattern 1: @Annotation("/path")
        match = re.search(r'["\']([^"\']+)["\']', annotation)
        if match:
            path = match.group(1)
            # Ensure path starts with /
            if not path.startswith("/"):
                path = "/" + path
            return path

        return ""

    def _extract_dependencies(
        self,
        class_node: ClassNode,
        kg: KnowledgeGraph
    ) -> List[str]:
        """Extract dependencies (autowired services)"""
        dependencies = []

        # Look for fields with @Autowired or @Inject (stored without @ symbol)
        for field_id, field_node in kg.fields.items():
            if field_node.class_name != f"{class_node.package}.{class_node.name}":
                continue

            # Check if field is autowired (use substring matching)
            is_injected = False
            for ann in field_node.annotations:
                if "Autowired" in ann or "Inject" in ann:
                    is_injected = True
                    break

            if is_injected:
                dependencies.append(field_node.field_type)

        return dependencies

    def _generate_summary(
        self,
        framework: str,
        total_controllers: int,
        total_endpoints: int
    ) -> str:
        """Generate summary text"""
        if framework == "Spring Boot":
            return f"Found {total_controllers} REST controllers with {total_endpoints} endpoints"
        elif framework in ["Struts", "Struts 2"]:
            return f"Found {total_controllers} action classes with {total_endpoints} actions"
        elif framework == "JAX-RS":
            return f"Found {total_controllers} JAX-RS resources with {total_endpoints} endpoints"
        elif framework == "Servlet/JSP":
            return f"Found {total_controllers} servlets with {total_endpoints} handler methods"
        else:
            return f"Found {total_controllers} presentation layer components"


def extract_presentation_layer(
    knowledge_graph: KnowledgeGraph,
    framework: str
) -> PresentationLayerInfo:
    """
    Convenience function to extract presentation layer

    Args:
        knowledge_graph: Parsed knowledge graph
        framework: Detected framework name

    Returns:
        PresentationLayerInfo
    """
    extractor = PresentationLayerExtractor()
    return extractor.extract(knowledge_graph, framework)
