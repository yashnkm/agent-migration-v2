"""
Universal Domain Discovery - Framework-Agnostic
Discovers domains by analyzing behavior and call chains, not names or frameworks
"""
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
from src.knowledge_graph.graph import KnowledgeGraph, EdgeType


@dataclass
class DomainInfo:
    """Information about a discovered business domain"""
    name: str
    entry_points: List[str] = field(default_factory=list)  # Controller classes
    services: List[str] = field(default_factory=list)
    repositories: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)

    # Detailed information
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    fields: List[Dict[str, Any]] = field(default_factory=list)

    # Metrics
    complexity_score: int = 0
    endpoint_count: int = 0
    method_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entry_points": self.entry_points,
            "services": self.services,
            "repositories": self.repositories,
            "entities": self.entities,
            "endpoints": self.endpoints,
            "methods": self.methods,
            "fields": self.fields,
            "metrics": {
                "complexity_score": self.complexity_score,
                "endpoint_count": self.endpoint_count,
                "method_count": self.method_count
            }
        }


class UniversalDomainDiscovery:
    """
    Framework-agnostic domain discovery
    Discovers architecture by analyzing behavior and call chains
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.domains: Dict[str, DomainInfo] = {}

    def discover_domains(self):
        """
        Main discovery method
        """
        print("\n" + "=" * 70)
        print("UNIVERSAL DOMAIN DISCOVERY - Framework-Agnostic Analysis")
        print("=" * 70)

        # Step 1: Find entry points (controllers/actions/resources)
        print("\n[1/5] Finding entry points by behavior analysis...")
        entry_points = self.find_entry_points()
        print(f"  Found {len(entry_points)} entry point(s)")

        # Step 2: For each entry point, trace call chain
        print("\n[2/5] Tracing call chains from entry points...")
        for entry_point in entry_points:
            domain = self.build_domain_from_entry_point(entry_point)
            if domain:
                self.domains[domain.name] = domain
                print(f"  [+] Discovered domain: {domain.name}")

        # Step 3: Extract detailed information
        print("\n[3/5] Extracting methods and fields...")
        for domain_name, domain in self.domains.items():
            self.extract_domain_details(domain)

        # Step 4: Map endpoints
        print("\n[4/5] Mapping endpoints to domains...")
        self.map_endpoints_to_domains()

        # Step 5: Calculate metrics
        print("\n[5/5] Calculating complexity metrics...")
        self.calculate_metrics()

        print(f"\n[OK] Discovery complete! Found {len(self.domains)} domain(s)")

        # Return domains as list of dicts for compatibility
        return [domain.to_dict() for domain in self.domains.values()]

    def find_entry_points(self) -> List[Dict[str, Any]]:
        """
        Find entry points by analyzing behavior
        Entry points: classes that orchestrate (make many calls)
        """
        entry_points = []

        print(f"  Analyzing {len(self.knowledge_graph.classes)} classes...")

        for class_id, class_node in self.knowledge_graph.classes.items():
            full_class_name = f"{class_node.package}.{class_node.name}" if class_node.package else class_node.name

            # Get all methods in this class
            class_methods = [
                m for m in self.knowledge_graph.methods.values()
                if m.class_name == full_class_name
            ]

            if not class_methods:
                continue

            # Pattern 1: High fanout (makes many calls = orchestrator)
            high_fanout_methods = []
            for method in class_methods:
                call_count = self.count_method_calls(method)
                if call_count >= 2:  # Orchestrates at least 2 calls (lowered from 3)
                    high_fanout_methods.append(method)

            # Pattern 2: Check AI classification
            is_controller_by_ai = class_node.class_type == "Controller"

            # Pattern 3: Name suggests entry point
            entry_suffixes = ['Controller', 'Action', 'Resource', 'Endpoint', 'Handler', 'Rest']
            has_entry_suffix = any(class_node.name.endswith(s) for s in entry_suffixes)

            # Pattern 4: Has common entry point method names
            entry_method_names = ['execute', 'handle', 'process', 'doGet', 'doPost']
            has_entry_method = any(m.name in entry_method_names for m in class_methods)

            # DEBUG: Print what we found
            if has_entry_suffix or is_controller_by_ai or high_fanout_methods or has_entry_method:
                print(f"  Candidate: {class_node.name}")
                print(f"    - AI classified as: {class_node.class_type}")
                print(f"    - Has entry suffix: {has_entry_suffix}")
                print(f"    - High fanout methods: {len(high_fanout_methods)}")
                print(f"    - Has entry method: {has_entry_method}")

            # Calculate confidence
            confidence = 0
            if high_fanout_methods:
                confidence += 50
            if has_entry_suffix:
                confidence += 30
            if has_entry_method:
                confidence += 20
            if is_controller_by_ai:
                confidence += 40

            # If confidence is high enough, it's an entry point
            if confidence >= 30:  # Lowered threshold (suffix alone = 30)
                entry_points.append({
                    'class': class_node,
                    'full_name': full_class_name,
                    'entry_methods': high_fanout_methods or class_methods,
                    'confidence': confidence
                })
                print(f"    [OK] Entry point: {class_node.name} (confidence: {confidence}%)")

        return entry_points

    def count_method_calls(self, method) -> int:
        """Count how many other methods this method calls"""
        method_id = f"method:{method.class_name}.{method.name}"

        if method_id not in self.knowledge_graph.graph:
            return 0

        # Count CALLS edges
        call_count = 0
        for edge in self.knowledge_graph.graph.out_edges(method_id):
            _, target = edge
            edge_data = self.knowledge_graph.graph.get_edge_data(*edge)
            if edge_data:
                # Handle MultiDiGraph - edge_data might contain multiple edges
                if isinstance(edge_data, dict):
                    # Check if it's a nested dict (MultiDiGraph format)
                    for key, data in edge_data.items():
                        if data.get('type') == EdgeType.CALLS:
                            call_count += 1
                elif edge_data.get('type') == EdgeType.CALLS:
                    call_count += 1

        return call_count

    def build_domain_from_entry_point(self, entry_point: Dict) -> Optional[DomainInfo]:
        """
        Build domain by tracing call chain from entry point
        """
        class_node = entry_point['class']
        entry_methods = entry_point['entry_methods']

        # Trace what this entry point calls
        layers = self.trace_call_chain(entry_methods)

        # Extract domain name from entry point class name
        domain_name = self.extract_domain_name(class_node.name)

        # Create domain
        domain = DomainInfo(
            name=domain_name,
            entry_points=[entry_point['full_name']],
            services=list(layers['services']),
            repositories=list(layers['repositories']),
            entities=list(layers['entities'])
        )

        return domain

    def extract_domain_name(self, class_name: str) -> str:
        """
        Extract domain name from class name
        UserController → User
        RequestAction → Request
        ProductResource → Product
        """
        # Remove common suffixes
        suffixes = ['Controller', 'Action', 'Resource', 'Endpoint', 'Handler', 'Rest', 'Service']
        name = class_name
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        return name if name else class_name

    def trace_call_chain(self, entry_methods: List, max_depth: int = 4) -> Dict[str, Set[str]]:
        """
        Trace what entry methods call, recursively
        Returns layers: services, repositories, entities
        """
        layers = {
            'services': set(),
            'repositories': set(),
            'entities': set()
        }

        visited = set()

        for entry_method in entry_methods:
            self._trace_method_recursive(
                entry_method,
                layers,
                visited,
                depth=0,
                max_depth=max_depth
            )

        return layers

    def _trace_method_recursive(self, method, layers: Dict, visited: Set, depth: int, max_depth: int):
        """Recursively trace method calls"""
        if depth >= max_depth:
            return

        method_id = f"method:{method.class_name}.{method.name}"

        if method_id in visited:
            return

        visited.add(method_id)

        # Find what this method calls
        if method_id not in self.knowledge_graph.graph:
            return

        for edge in self.knowledge_graph.graph.out_edges(method_id):
            _, target = edge
            edge_data = self.knowledge_graph.graph.get_edge_data(*edge)

            if not edge_data or edge_data.get('type') != 'CALLS':
                continue

            if not target.startswith("method:"):
                continue

            # Extract called class name
            called_class_name = self.extract_class_from_method_id(target)
            if not called_class_name:
                continue

            # Don't trace back to entry point or same class
            if called_class_name == method.class_name:
                continue

            # Find the called class
            called_class = self.find_class_by_name(called_class_name)
            if not called_class:
                continue

            # Classify by behavior
            layer = self.classify_by_behavior(called_class)

            if layer == 'service':
                layers['services'].add(called_class_name)
                # Continue tracing through services
                called_method = self.get_method_from_id(target)
                if called_method:
                    self._trace_method_recursive(called_method, layers, visited, depth + 1, max_depth)

            elif layer == 'repository':
                layers['repositories'].add(called_class_name)
                # Extract entities from repository
                entities = self.extract_entities_from_repository(called_class)
                layers['entities'].update(entities)

            elif layer == 'entity':
                layers['entities'].add(called_class_name)

    def classify_by_behavior(self, class_node) -> str:
        """
        Classify class by analyzing what it DOES, not what it's called
        """
        full_class_name = f"{class_node.package}.{class_node.name}" if class_node.package else class_node.name

        # Get methods and fields
        methods = [
            m for m in self.knowledge_graph.methods.values()
            if m.class_name == full_class_name
        ]

        fields = [
            f for f in self.knowledge_graph.fields.values()
            if f.class_name == full_class_name
        ]

        # Pattern 1: ENTITY
        # Many fields, mostly getters/setters, few outgoing calls
        if len(fields) >= 3:
            getter_setter_count = sum(
                1 for m in methods
                if m.name.startswith('get') or m.name.startswith('set') or m.name.startswith('is')
            )
            getter_setter_ratio = getter_setter_count / len(methods) if methods else 0

            avg_calls = sum(self.count_method_calls(m) for m in methods) / len(methods) if methods else 0

            if getter_setter_ratio > 0.5 and avg_calls < 2:
                return 'entity'

        # Pattern 2: REPOSITORY
        # CRUD method names
        crud_verbs = ['save', 'find', 'get', 'delete', 'remove', 'update', 'create', 'insert', 'select', 'read']
        crud_method_count = sum(
            1 for m in methods
            if any(verb in m.name.lower() for verb in crud_verbs)
        )

        if crud_method_count >= 2:
            return 'repository'

        # Pattern 3: SERVICE
        # Orchestrates (makes multiple calls)
        avg_calls = sum(self.count_method_calls(m) for m in methods) / len(methods) if methods else 0

        business_verbs = ['process', 'calculate', 'validate', 'execute', 'handle', 'manage', 'perform']
        business_method_count = sum(
            1 for m in methods
            if any(verb in m.name.lower() for verb in business_verbs)
        )

        if avg_calls >= 2 or business_method_count >= 1:
            return 'service'

        return 'unknown'

    def extract_entities_from_repository(self, repository_class) -> Set[str]:
        """
        Find entities by analyzing repository method signatures
        """
        entities = set()
        full_class_name = f"{repository_class.package}.{repository_class.name}" if repository_class.package else repository_class.name

        methods = [
            m for m in self.knowledge_graph.methods.values()
            if m.class_name == full_class_name
        ]

        for method in methods:
            # Check return type
            entity = self.extract_domain_type(method.return_type)
            if entity:
                entities.add(entity)

            # Check parameters
            for param in method.parameters:
                entity = self.extract_domain_type(param['type'])
                if entity:
                    entities.add(entity)

        return entities

    def extract_domain_type(self, type_string: str) -> Optional[str]:
        """
        Extract domain type from type string
        'Request' → 'Request'
        'List<Request>' → 'Request'
        'Map<String, Request>' → 'Request'
        'String' → None (primitive)
        """
        if not type_string:
            return None

        # Remove generics and extract inner type
        if '<' in type_string:
            inner = type_string.split('<')[1].split('>')[0]
            types = [t.strip() for t in inner.split(',')]
            # Return first non-primitive type
            for t in types:
                if not self.is_primitive(t):
                    return t
            return None

        # Remove array notation
        type_string = type_string.replace('[]', '')

        # Check if primitive
        if self.is_primitive(type_string):
            return None

        return type_string

    def is_primitive(self, type_string: str) -> bool:
        """Check if type is primitive or common library class"""
        primitives = {
            'void', 'int', 'long', 'double', 'float', 'boolean', 'char', 'byte', 'short',
            'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Character',
            'List', 'Map', 'Set', 'Collection', 'Optional', 'Date', 'LocalDate', 'LocalDateTime',
            'HttpServletRequest', 'HttpServletResponse', 'ActionMapping', 'ActionForm',
            'Object', 'Class'
        }
        return type_string in primitives

    def extract_class_from_method_id(self, method_id: str) -> Optional[str]:
        """Extract class name from method ID like 'method:com.example.Class.methodName'"""
        if not method_id.startswith("method:"):
            return None

        parts = method_id[7:].rsplit('.', 1)  # Remove 'method:' and split
        if len(parts) == 2:
            return parts[0]
        return None

    def find_class_by_name(self, class_name: str):
        """Find class node by full class name"""
        for class_id, class_node in self.knowledge_graph.classes.items():
            full_name = f"{class_node.package}.{class_node.name}" if class_node.package else class_node.name
            if full_name == class_name:
                return class_node
        return None

    def get_method_from_id(self, method_id: str):
        """Get method node from method ID"""
        for method in self.knowledge_graph.methods.values():
            mid = f"method:{method.class_name}.{method.name}"
            if mid == method_id:
                return method
        return None

    def extract_domain_details(self, domain: DomainInfo):
        """Extract methods and fields for domain"""
        all_classes = domain.entry_points + domain.services + domain.repositories + domain.entities

        # Extract methods
        for class_name in all_classes:
            methods = [
                f"{m.class_name}.{m.name}"
                for m in self.knowledge_graph.methods.values()
                if m.class_name == class_name
            ]
            domain.methods.extend(methods)

        # Extract fields from entities
        for entity_name in domain.entities:
            fields = [
                {
                    'name': f.name,
                    'type': f.field_type,
                    'annotations': f.annotations
                }
                for f in self.knowledge_graph.fields.values()
                if f.class_name == entity_name
            ]
            domain.fields.extend(fields)

    def map_endpoints_to_domains(self):
        """Map endpoints to domains"""
        for endpoint_id, endpoint in self.knowledge_graph.endpoints.items():
            # Find which domain's entry point handles this
            for domain_name, domain in self.domains.items():
                if endpoint.handler_class in domain.entry_points:
                    domain.endpoints.append({
                        'http_method': endpoint.http_method,
                        'path': endpoint.path,
                        'handler_method': endpoint.handler_method,
                        'handler_class': endpoint.handler_class
                    })

    def calculate_metrics(self):
        """Calculate complexity metrics for domains"""
        for domain_name, domain in self.domains.items():
            domain.endpoint_count = len(domain.endpoints)
            domain.method_count = len(domain.methods)

            domain.complexity_score = (
                len(domain.endpoints) * 3 +
                len(domain.methods) * 1 +
                len(domain.fields) * 2
            )

            print(f"  {domain_name}: Complexity = {domain.complexity_score}")

    def export_domain_catalog(self) -> Dict[str, Any]:
        """Export complete domain catalog"""
        return {
            'domains': {name: domain.to_dict() for name, domain in self.domains.items()},
            'summary': {
                'total_domains': len(self.domains),
                'total_entry_points': sum(len(d.entry_points) for d in self.domains.values()),
                'total_services': sum(len(d.services) for d in self.domains.values()),
                'total_repositories': sum(len(d.repositories) for d in self.domains.values()),
                'total_entities': sum(len(d.entities) for d in self.domains.values())
            }
        }
