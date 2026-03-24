"""
API layer for Human Design chart operations.

This module provides type-safe, testable functions for:
- Person management (add, retrieve, search)
- Chart composition (interaction, penta, transit)
- Relationship storage

All functions accept optional repository parameters for testing.
"""

from datetime import datetime
from pathlib import Path
from uuid import UUID

from ..models.bodygraph import BirthInfo, RawBodyGraph
from ..models.composite import CompositeBodyGraph
from ..models.transit import Transit
from ..storage import (
    PersonRepository,
    RelationshipRepository,
    StoredPerson,
    StoredRelationship,
)


def _resolve_person(
    identifier: str | UUID,
    repo: PersonRepository
) -> StoredPerson:
    """
    Resolve person from name or UUID.
    
    Helper for API functions that accept str | UUID.
    Raises ValueError with helpful message if not found.
    """
    if isinstance(identifier, UUID):
        person = repo.get(identifier)
        if person is None:
            raise ValueError(f"Person with ID {identifier} not found")
    else:
        # Try exact name match first
        person = repo.find_by_name(identifier)
        if person is None:
            # Try fuzzy search
            matches = repo.search_by_name(identifier)
            if not matches:
                raise ValueError(f"No person found matching '{identifier}'")
            if len(matches) > 1:
                names = [m.name for m in matches]
                raise ValueError(
                    f"Multiple people match '{identifier}': {names}. "
                    "Use full name or UUID."
                )
            person = matches[0]
    
    return person


def add_person(
    name: str,
    birth_info: BirthInfo,
    tags: list[str] | None = None,
    repo: PersonRepository | None = None
) -> StoredPerson:
    """
    Add person to storage.
    
    Args:
        name: Full name (e.g., "Sandy Rodriguez", "Heath (husband)")
        birth_info: Birth information for chart calculation
        tags: Optional tags for grouping (e.g., ["client", "family"])
        repo: Repository (defaults to ~/.human-design/people.json)
        
    Returns:
        StoredPerson with generated UUID
        
    Raises:
        ValueError: If person with this name already exists
        
    Example:
        >>> from human_design.models import BirthInfo, LocalTime
        >>> from datetime import datetime
        >>> 
        >>> birth_info = BirthInfo(
        ...     date="1990-01-15",
        ...     localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
        ...     city="Albuquerque",
        ...     country="NM"
        ... )
        >>> 
        >>> sandy = add_person(
        ...     name="Sandy Rodriguez",
        ...     birth_info=birth_info,
        ...     tags=["client", "family"]
        ... )
        >>> print(f"Added {sandy.name} with ID {sandy.id}")
    """
    if repo is None:
        repo = PersonRepository()
    
    # Check for duplicate name
    existing = repo.find_by_name(name)
    if existing:
        raise ValueError(
            f"Person '{name}' already exists (ID: {existing.id}). "
            "Use a different name or retrieve existing person."
        )
    
    person = StoredPerson(
        name=name,
        birth_info=birth_info,
        tags=tags or []
    )
    
    return repo.add(person)


def get_person(
    identifier: str | UUID,
    repo: PersonRepository | None = None
) -> StoredPerson:
    """
    Get person by name or UUID.
    
    Args:
        identifier: Person name (fuzzy match) or UUID (exact match)
        repo: Repository (defaults to standard location)
        
    Returns:
        StoredPerson
        
    Raises:
        ValueError: If person not found or name ambiguous
        
    Example:
        >>> # By name (fuzzy match)
        >>> sandy = get_person("Sandy")
        >>> 
        >>> # By UUID
        >>> person = get_person("550e8400-e29b-41d4-a716-446655440000")
        >>> 
        >>> # Access chart
        >>> print(sandy.chart.type)
    """
    if repo is None:
        repo = PersonRepository()
    
    return _resolve_person(identifier, repo)


def list_people(
    tag: str | None = None,
    repo: PersonRepository | None = None
) -> list[StoredPerson]:
    """
    List people, optionally filtered by tag.
    
    Args:
        tag: Optional tag to filter by (case-insensitive)
        repo: Repository (defaults to standard location)
        
    Returns:
        List of people (newest first)
        
    Example:
        >>> # List all people
        >>> all_people = list_people()
        >>> 
        >>> # List only clients
        >>> clients = list_people(tag="client")
        >>> 
        >>> # List Sandy's group
        >>> group = list_people(tag="Sandy's group")
    """
    if repo is None:
        repo = PersonRepository()
    
    if tag:
        return repo.find_by_tag(tag)
    else:
        return repo.list_all()


def get_interaction(
    person1: str | UUID,
    person2: str | UUID,
    repo: PersonRepository | None = None
) -> CompositeBodyGraph:
    """
    Create interaction chart between two people.
    
    Uses the + operator pattern internally: chart1 + chart2
    
    Args:
        person1: Name or UUID of first person
        person2: Name or UUID of second person
        repo: Repository (defaults to standard location)
        
    Returns:
        CompositeBodyGraph showing interaction
        
    Raises:
        ValueError: If either person not found
        
    Example:
        >>> # Show Sandy + Heath interaction
        >>> interaction = get_interaction("Sandy", "Heath")
        >>> 
        >>> # Check emergent channels (exist in combo but not individually)
        >>> emergent = interaction.emergent_channels()
        >>> for channel in emergent:
        ...     print(f"Channel {channel.gate_a}-{channel.gate_b}: {channel.name}")
        >>> 
        >>> # Check composite type and authority
        >>> print(f"Type: {interaction.type}")
        >>> print(f"Authority: {interaction.authority}")
    """
    if repo is None:
        repo = PersonRepository()
    
    p1 = _resolve_person(person1, repo)
    p2 = _resolve_person(person2, repo)
    
    # Use __add__ operator
    return p1.chart + p2.chart


def get_penta(
    people: list[str | UUID],
    repo: PersonRepository | None = None
) -> CompositeBodyGraph:
    """
    Create penta/multichart from multiple people.
    
    Supports 3-16 people:
    - 3-5 people: "penta" in Human Design terminology
    - 6-16 people: "multichart"
    
    Uses chained + operator: chart1 + chart2 + chart3 + ...
    
    Args:
        people: List of names or UUIDs (min 3, max 16)
        repo: Repository (defaults to standard location)
        
    Returns:
        CompositeBodyGraph
        
    Raises:
        ValueError: If < 3 or > 16 people, or any person not found
        
    Example:
        >>> # Sandy's family penta (4 people)
        >>> family = get_penta(["Sandy", "Heath", "daughter", "son"])
        >>> print(f"Type: {family.type}")
        >>> print(f"Defined centers: {family.defined_centers}")
        >>> 
        >>> # Check which channels are emergent
        >>> emergent = family.emergent_channels()
        >>> print(f"New channels formed: {len(emergent)}")
    """
    if repo is None:
        repo = PersonRepository()
    
    if len(people) < 3:
        raise ValueError("Penta requires at least 3 people")
    if len(people) > 16:
        raise ValueError("Multichart supports maximum 16 people")
    
    # Resolve all people first
    resolved = [_resolve_person(p, repo) for p in people]
    
    # Chain using __add__
    result = resolved[0].chart
    for person in resolved[1:]:
        result = result + person.chart
    
    return result


def add_transit_to_person(
    person: str | UUID,
    transit: Transit | None = None,
    repo: PersonRepository | None = None
) -> CompositeBodyGraph:
    """
    Add transit overlay to person's chart.
    
    Shows how current (or specific) planetary positions interact
    with the person's birth chart.
    
    Args:
        person: Name or UUID
        transit: Transit to overlay (defaults to Transit.now())
        repo: Repository (defaults to standard location)
        
    Returns:
        CompositeBodyGraph with transit overlay
        
    Raises:
        ValueError: If person not found
        
    Example:
        >>> # Sandy's chart with current transits
        >>> now_chart = add_transit_to_person("Sandy")
        >>> 
        >>> # With specific transit moment
        >>> from datetime import datetime
        >>> nye_transit = Transit.at(
        ...     datetime(2024, 12, 31, 23, 59),
        ...     location="New York, NY"
        ... )
        >>> nye_chart = add_transit_to_person("Sandy", nye_transit)
        >>> 
        >>> # Check what channels activate with transit
        >>> print(f"Active channels: {len(nye_chart.active_channels)}")
    """
    if repo is None:
        repo = PersonRepository()
    
    if transit is None:
        transit = Transit.now()
    
    p = _resolve_person(person, repo)
    
    # Use __add__ operator
    return p.chart + transit


def save_relationship(
    name: str,
    people: list[str | UUID],
    tags: list[str] | None = None,
    person_repo: PersonRepository | None = None,
    rel_repo: RelationshipRepository | None = None
) -> StoredRelationship:
    """
    Save a relationship (interaction/penta) for later recall.
    
    This allows naming and tagging chart combinations:
    - "Sandy + Heath" (interaction)
    - "Sandy's family" (penta)
    - "Work team alpha" (multichart)
    
    Args:
        name: Relationship name
        people: List of names or UUIDs (2-16)
        tags: Optional tags (e.g., ["family", "primary"])
        person_repo: Person repository
        rel_repo: Relationship repository
        
    Returns:
        StoredRelationship with generated UUID
        
    Raises:
        ValueError: If < 2 or > 16 people, or any person not found
        
    Example:
        >>> # Save Sandy + Heath interaction
        >>> rel = save_relationship(
        ...     name="Sandy + Heath",
        ...     people=["Sandy", "Heath"],
        ...     tags=["marriage", "primary"]
        ... )
        >>> 
        >>> # Save family penta
        >>> family = save_relationship(
        ...     name="Sandy's family",
        ...     people=["Sandy", "Heath", "daughter", "son"],
        ...     tags=["family"]
        ... )
    """
    if person_repo is None:
        person_repo = PersonRepository()
    if rel_repo is None:
        rel_repo = RelationshipRepository()
    
    if len(people) < 2:
        raise ValueError("Relationship requires at least 2 people")
    if len(people) > 16:
        raise ValueError("Relationship supports maximum 16 people")
    
    # Resolve all people to get UUIDs
    resolved = [_resolve_person(p, person_repo) for p in people]
    person_ids = [p.id for p in resolved]
    
    # Check for duplicate name
    existing = rel_repo.find_by_name(name)
    if existing:
        raise ValueError(
            f"Relationship '{name}' already exists (ID: {existing.id}). "
            "Use a different name or retrieve existing relationship."
        )
    
    relationship = StoredRelationship(
        name=name,
        person_ids=person_ids,
        tags=tags or []
    )
    
    return rel_repo.add(relationship)


def get_relationship(
    identifier: str | UUID,
    person_repo: PersonRepository | None = None,
    rel_repo: RelationshipRepository | None = None
) -> CompositeBodyGraph:
    """
    Retrieve saved relationship and calculate chart.
    
    Args:
        identifier: Relationship name or UUID
        person_repo: Person repository
        rel_repo: Relationship repository
        
    Returns:
        CompositeBodyGraph
        
    Raises:
        ValueError: If relationship not found or people missing
        
    Example:
        >>> # Recall by name
        >>> interaction = get_relationship("Sandy + Heath")
        >>> 
        >>> # Recall by UUID
        >>> chart = get_relationship("650e8400-e29b-41d4-a716-446655440001")
    """
    if person_repo is None:
        person_repo = PersonRepository()
    if rel_repo is None:
        rel_repo = RelationshipRepository()
    
    # Resolve relationship
    if isinstance(identifier, UUID):
        rel = rel_repo.get(identifier)
        if rel is None:
            raise ValueError(f"Relationship with ID {identifier} not found")
    else:
        rel = rel_repo.find_by_name(identifier)
        if rel is None:
            raise ValueError(f"No relationship found matching '{identifier}'")
    
    # Get all people and compose
    charts = []
    for person_id in rel.person_ids:
        person = person_repo.get(person_id)
        if person is None:
            raise ValueError(f"Person {person_id} in relationship not found in storage")
        charts.append(person.chart)
    
    # Chain using __add__
    result = charts[0]
    for chart in charts[1:]:
        result = result + chart
    
    return result


def list_relationships(
    tag: str | None = None,
    rel_repo: RelationshipRepository | None = None
) -> list[StoredRelationship]:
    """
    List relationships, optionally filtered by tag.
    
    Args:
        tag: Optional tag to filter by (case-insensitive)
        rel_repo: Relationship repository
        
    Returns:
        List of relationships (newest first)
        
    Example:
        >>> # List all relationships
        >>> all_rels = list_relationships()
        >>> 
        >>> # List only family relationships
        >>> family = list_relationships(tag="family")
    """
    if rel_repo is None:
        rel_repo = RelationshipRepository()
    
    if tag:
        return rel_repo.find_by_tag(tag)
    else:
        return rel_repo.list_all()
