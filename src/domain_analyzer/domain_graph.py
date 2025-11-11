"""
Domain-Centric Knowledge Graph
Groups all code elements by business domain/entity
"""
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
from src.knowledge_graph.graph import KnowledgeGraph


@dataclass
class DomainInfo:
    """Information about a single business domain"""
    name: str  # e.g., "User", "Book", "Order"
    entity_class: str  # Full class name: com.example.entity.User
    entity_package: str
    entity_file_path: str

    # Associated classes
    controller: Optional[str] = None  # com.example.controller.UserController
    service: Optional[str] = None  # com.example.service.UserService
    repository: Optional[str] = None  # com.example.repository.UserRepository

    # Related entities (through relationships)
    related_entities: List[str] = field(default_factory=list)

    # Entry points (endpoints)
    endpoints: List[Dict[str, Any]] = field(default_factory=list)

    # All methods in this domain
    methods: List[str] = field(default_factory=list)

    # All fields in the entity
    fields: List[str] = field(default_factory=list)

    # Metrics
    complexity_score: int = 0
    endpoint_count: int = 0
    method_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "entity_class": self.entity_class,
            "entity_package": self.entity_package,
            "entity_file_path": self.entity_file_path,
            "controller": self.controller,
            "service": self.service,
            "repository": self.repository,
            "related_entities": self.related_entities,
            "endpoints": self.endpoints,
            "methods": self.methods,
            "fields": self.fields,
            "metrics": {
                "complexity_score": self.complexity_score,
                "endpoint_count": self.endpoint_count,
                "method_count": self.method_count
            }
        }


class DomainGraph:
    """
    Domain-centric knowledge graph
    Organizes everything by business domain (entity)
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.domains: Dict[str, DomainInfo] = {}  # domain_name -> DomainInfo
        self.unassigned_classes: List[str] = []  # Classes not belonging to any domain

    def discover_domains(self):
        """
        Main method: Discover all domains from the knowledge graph
        """
        print("\n" + "=" * 70)
        print("DOMAIN DISCOVERY - Analyzing Codebase Structure")
        print("=" * 70)

        # Step 1: Find all entity classes (these define domains)
        self._identify_entities()

        # Step 2: For each domain, find associated classes
        self._map_domain_classes()

        # Step 3: Map endpoints to domains
        self._map_endpoints_to_domains()

        # Step 4: Map methods to domains
        self._map_methods_to_domains()

        # Step 5: Extract fields from entities
        self._extract_entity_fields()

        # Step 6: Find related entities (through relationships)
        self._find_related_entities()

        # Step 7: Calculate complexity metrics
        self._calculate_metrics()

        print(f"\n[OK] Domain discovery complete!")
        print(f"  Found {len(self.domains)} business domain(s)")

    def _identify_entities(self):
        """Step 1: Find all entity classes"""
        print("\n[1/7] Identifying entity classes...")

        entity_count = 0
        for class_id, class_node in self.knowledge_graph.classes.items():
            if class_node.class_type == "Entity":
                domain_name = class_node.name
                full_class_name = f"{class_node.package}.{class_node.name}"

                self.domains[domain_name] = DomainInfo(
                    name=domain_name,
                    entity_class=full_class_name,
                    entity_package=class_node.package,
                    entity_file_path=class_node.file_path
                )

                entity_count += 1
                print(f"  [+] Found domain: {domain_name} ({full_class_name})")

        print(f"  Total entities found: {entity_count}")

    def _map_domain_classes(self):
        """Step 2: Find Controller, Service, Repository for each domain"""
        print("\n[2/7] Mapping domain classes (Controller/Service/Repository)...")

        for domain_name, domain_info in self.domains.items():
            # Look for classes with domain name in them
            domain_lower = domain_name.lower()

            for class_id, class_node in self.knowledge_graph.classes.items():
                class_name_lower = class_node.name.lower()
                full_class_name = f"{class_node.package}.{class_node.name}"

                # Check if class belongs to this domain
                if domain_lower in class_name_lower:
                    if class_node.class_type == "Controller":
                        domain_info.controller = full_class_name
                        print(f"  [+] {domain_name}: Found Controller -> {class_node.name}")

                    elif class_node.class_type == "Service":
                        domain_info.service = full_class_name
                        print(f"  [+] {domain_name}: Found Service -> {class_node.name}")

                    elif class_node.class_type == "Repository":
                        domain_info.repository = full_class_name
                        print(f"  [+] {domain_name}: Found Repository -> {class_node.name}")

    def _map_endpoints_to_domains(self):
        """Step 3: Map REST endpoints to domains"""
        print("\n[3/7] Mapping endpoints to domains...")

        for endpoint_id, endpoint in self.knowledge_graph.endpoints.items():
            # Find which domain this endpoint belongs to
            handler_class = endpoint.handler_class

            # Try to match endpoint to domain
            assigned = False
            for domain_name, domain_info in self.domains.items():
                if domain_info.controller == handler_class:
                    domain_info.endpoints.append({
                        "http_method": endpoint.http_method,
                        "path": endpoint.path,
                        "handler_method": endpoint.handler_method,
                        "handler_class": endpoint.handler_class
                    })
                    assigned = True
                    print(f"  [+] {domain_name}: {endpoint.http_method} {endpoint.path}")
                    break

            if not assigned:
                print(f"  [\!] Unassigned endpoint: {endpoint.http_method} {endpoint.path}")

    def _map_methods_to_domains(self):
        """Step 4: Map methods to domains"""
        print("\n[4/7] Mapping methods to domains...")

        for domain_name, domain_info in self.domains.items():
            domain_classes = [
                domain_info.entity_class,
                domain_info.controller,
                domain_info.service,
                domain_info.repository
            ]

            # Remove None values
            domain_classes = [c for c in domain_classes if c]

            # Find all methods in these classes
            method_count = 0
            for method_id, method_node in self.knowledge_graph.methods.items():
                if method_node.class_name in domain_classes:
                    method_full_name = f"{method_node.class_name}.{method_node.name}"
                    domain_info.methods.append(method_full_name)
                    method_count += 1

            print(f"  [+] {domain_name}: Found {method_count} methods")

    def _extract_entity_fields(self):
        """Step 5: Extract fields from entity classes"""
        print("\n[5/7] Extracting entity fields...")

        for domain_name, domain_info in self.domains.items():
            entity_class = domain_info.entity_class

            field_count = 0
            for field_id, field_node in self.knowledge_graph.fields.items():
                if field_node.class_name == entity_class:
                    domain_info.fields.append({
                        "name": field_node.name,
                        "type": field_node.field_type,
                        "annotations": field_node.annotations
                    })
                    field_count += 1

            print(f"  [+] {domain_name}: Found {field_count} fields")

    def _find_related_entities(self):
        """Step 6: Find related entities through JPA relationships"""
        print("\n[6/7] Finding related entities...")

        # TODO: Parse JPA annotations (@OneToMany, @ManyToOne, etc.) to find relationships
        # For now, this is a placeholder

        for domain_name in self.domains:
            print(f"  [O] {domain_name}: Relationship detection not yet implemented")

    def _calculate_metrics(self):
        """Step 7: Calculate complexity metrics"""
        print("\n[7/7] Calculating complexity metrics...")

        for domain_name, domain_info in self.domains.items():
            domain_info.endpoint_count = len(domain_info.endpoints)
            domain_info.method_count = len(domain_info.methods)

            # Simple complexity score
            domain_info.complexity_score = (
                len(domain_info.endpoints) * 3 +  # Endpoints are important
                len(domain_info.methods) * 1 +    # Methods add complexity
                len(domain_info.fields) * 2       # Fields indicate state
            )

            print(f"  [+] {domain_name}: Complexity Score = {domain_info.complexity_score}")

    def get_domain_summary(self) -> Dict[str, Any]:
        """Get summary of all domains"""
        return {
            "total_domains": len(self.domains),
            "domains": [
                {
                    "name": domain_name,
                    "has_controller": domain_info.controller is not None,
                    "has_service": domain_info.service is not None,
                    "has_repository": domain_info.repository is not None,
                    "endpoint_count": domain_info.endpoint_count,
                    "method_count": domain_info.method_count,
                    "field_count": len(domain_info.fields),
                    "complexity_score": domain_info.complexity_score
                }
                for domain_name, domain_info in self.domains.items()
            ]
        }

    def get_domain_details(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific domain"""
        if domain_name not in self.domains:
            return None

        domain_info = self.domains[domain_name]
        return domain_info.to_dict()

    def export_domain_catalog(self) -> Dict[str, Any]:
        """Export complete domain catalog"""
        return {
            "summary": self.get_domain_summary(),
            "domains": {
                domain_name: domain_info.to_dict()
                for domain_name, domain_info in self.domains.items()
            }
        }

    def print_domain_catalog(self):
        """Print a human-readable domain catalog"""
        print("\n" + "=" * 70)
        print("DOMAIN CATALOG")
        print("=" * 70)

        if not self.domains:
            print("\nNo domains found!")
            return

        print(f"\nTotal Business Domains: {len(self.domains)}")
        print()

        # Sort by complexity
        sorted_domains = sorted(
            self.domains.items(),
            key=lambda x: x[1].complexity_score,
            reverse=True
        )

        for idx, (domain_name, domain_info) in enumerate(sorted_domains, 1):
            print(f"{idx}. {domain_name} Domain")
            print(f"   {'-' * 60}")
            print(f"   Entity:     {domain_info.entity_class}")
            print(f"   Controller: {domain_info.controller or '[X] Not Found'}")
            print(f"   Service:    {domain_info.service or '[X] Not Found'}")
            print(f"   Repository: {domain_info.repository or '[X] Not Found'}")
            print(f"   ")
            print(f"   Endpoints:  {domain_info.endpoint_count}")
            print(f"   Methods:    {domain_info.method_count}")
            print(f"   Fields:     {len(domain_info.fields)}")
            print(f"   Complexity: {domain_info.complexity_score} {'[HIGH] HIGH' if domain_info.complexity_score > 50 else '[MED] MEDIUM' if domain_info.complexity_score > 20 else '[LOW] LOW'}")
            print()

        print("=" * 70)

    def print_domain_details(self, domain_name: str):
        """Print detailed information about a specific domain"""
        if domain_name not in self.domains:
            print(f"Domain '{domain_name}' not found!")
            return

        domain_info = self.domains[domain_name]

        print("\n" + "=" * 70)
        print(f"{domain_name.upper()} DOMAIN - DETAILED VIEW")
        print("=" * 70)

        print(f"\n[ENTITY] Entity Class")
        print(f"   {domain_info.entity_class}")
        print(f"   Location: {domain_info.entity_file_path}")

        print(f"\n[ARCH]  Architecture")
        print(f"   Controller: {domain_info.controller or '[X] Not Found'}")
        print(f"   Service:    {domain_info.service or '[X] Not Found'}")
        print(f"   Repository: {domain_info.repository or '[X] Not Found'}")

        if domain_info.fields:
            print(f"\n[FIELDS] Entity Fields ({len(domain_info.fields)})")
            for field in domain_info.fields:
                annotations = f" [{', '.join(field['annotations'])}]" if field['annotations'] else ""
                print(f"   • {field['name']}: {field['type']}{annotations}")

        if domain_info.endpoints:
            print(f"\n[API] REST Endpoints ({len(domain_info.endpoints)})")
            for endpoint in domain_info.endpoints:
                print(f"   {endpoint['http_method']:6} {endpoint['path']}")
                print(f"          -> {endpoint['handler_method']}()")

        if domain_info.methods:
            print(f"\n[METHODS]  Methods ({len(domain_info.methods)})")
            for method in domain_info.methods[:10]:  # Show first 10
                print(f"   • {method}")
            if len(domain_info.methods) > 10:
                print(f"   ... and {len(domain_info.methods) - 10} more")

        print(f"\n[METRICS] Metrics")
        print(f"   Complexity Score: {domain_info.complexity_score}")
        print(f"   Endpoint Count:   {domain_info.endpoint_count}")
        print(f"   Method Count:     {domain_info.method_count}")
        print(f"   Field Count:      {len(domain_info.fields)}")

        print("\n" + "=" * 70)
