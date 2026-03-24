"""
Unit tests for repository layer.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from human_design.models import BirthInfo, LocalTime
from human_design.storage import (
    PersonRepository,
    RelationshipRepository,
    StoredPerson,
    StoredRelationship,
)


@pytest.fixture
def temp_person_repo() -> PersonRepository:
    """Create temporary person repository for testing (in-memory SQLite)."""
    return PersonRepository(database_url="sqlite:///:memory:")


@pytest.fixture
def temp_relationship_repo() -> RelationshipRepository:
    """Create temporary relationship repository for testing (in-memory SQLite)."""
    return RelationshipRepository(database_url="sqlite:///:memory:")


@pytest.fixture
def sample_person() -> StoredPerson:
    """Sample person for testing."""
    return StoredPerson(
        name="Sandy Rodriguez",
        birth_date="1990-01-15",
        birth_localtime="1990-01-15T09:13:00",
        birth_city="Albuquerque",
        birth_country="NM",
        tags=["client", "family"]
    )


# PersonRepository Tests

def test_person_repo_add(temp_person_repo: PersonRepository, sample_person: StoredPerson) -> None:
    """Test adding person to repository."""
    saved = temp_person_repo.add(sample_person)
    
    assert saved.id == sample_person.id
    assert saved.name == sample_person.name


def test_person_repo_add_duplicate_id(
    temp_person_repo: PersonRepository,
    sample_person: StoredPerson
) -> None:
    """Test that adding duplicate ID raises error."""
    temp_person_repo.add(sample_person)
    
    with pytest.raises(ValueError, match="already exists"):
        temp_person_repo.add(sample_person)


def test_person_repo_get(temp_person_repo: PersonRepository, sample_person: StoredPerson) -> None:
    """Test retrieving person by ID."""
    temp_person_repo.add(sample_person)
    
    retrieved = temp_person_repo.get(sample_person.id)
    assert retrieved is not None
    assert retrieved.id == sample_person.id
    assert retrieved.name == sample_person.name


def test_person_repo_get_nonexistent(temp_person_repo: PersonRepository) -> None:
    """Test getting nonexistent person returns None."""
    result = temp_person_repo.get(uuid4())
    assert result is None


def test_person_repo_find_by_name(
    temp_person_repo: PersonRepository,
    sample_person: StoredPerson
) -> None:
    """Test finding person by exact name."""
    temp_person_repo.add(sample_person)
    
    # Case-insensitive by default
    found = temp_person_repo.find_by_name("sandy rodriguez")
    assert found is not None
    assert found.name == sample_person.name
    
    # Case-sensitive
    found = temp_person_repo.find_by_name("Sandy Rodriguez", case_sensitive=True)
    assert found is not None
    
    not_found = temp_person_repo.find_by_name("sandy rodriguez", case_sensitive=True)
    assert not_found is None


def test_person_repo_search_by_name(temp_person_repo: PersonRepository) -> None:
    """Test fuzzy name search."""
    p1 = StoredPerson(
        name="Sandy Rodriguez",
        birth_date="1990-01-15",
        birth_localtime="1990-01-15T09:13:00",
        birth_city="Test",
        birth_country="Test"
    )
    p2 = StoredPerson(
        name="Sandy Smith",
        birth_date="1985-06-20",
        birth_localtime="1985-06-20T14:30:00",
        birth_city="Test",
        birth_country="Test"
    )
    p3 = StoredPerson(
        name="Heath Rodriguez",
        birth_date="1988-03-10",
        birth_localtime="1988-03-10T08:45:00",
        birth_city="Test",
        birth_country="Test"
    )
    
    temp_person_repo.add(p1)
    temp_person_repo.add(p2)
    temp_person_repo.add(p3)
    
    # Search "Sandy" should find 2
    results = temp_person_repo.search_by_name("Sandy")
    assert len(results) == 2
    
    # Search "Rodriguez" should find 2
    results = temp_person_repo.search_by_name("Rodriguez")
    assert len(results) == 2
    
    # Search "Smith" should find 1
    results = temp_person_repo.search_by_name("Smith")
    assert len(results) == 1


def test_person_repo_find_by_tag(temp_person_repo: PersonRepository) -> None:
    """Test finding people by tag."""
    p1 = StoredPerson(
        name="Person 1",
        birth_date="1990-01-15",
        birth_localtime="1990-01-15T09:13:00",
        birth_city="Test",
        birth_country="Test",
        tags=["client", "family"]
    )
    p2 = StoredPerson(
        name="Person 2",
        birth_date="1985-06-20",
        birth_localtime="1985-06-20T14:30:00",
        birth_city="Test",
        birth_country="Test",
        tags=["client"]
    )
    p3 = StoredPerson(
        name="Person 3",
        birth_date="1988-03-10",
        birth_localtime="1988-03-10T08:45:00",
        birth_city="Test",
        birth_country="Test",
        tags=["family"]
    )
    
    temp_person_repo.add(p1)
    temp_person_repo.add(p2)
    temp_person_repo.add(p3)
    
    # Find clients (should get 2)
    clients = temp_person_repo.find_by_tag("client")
    assert len(clients) == 2
    
    # Find family (should get 2)
    family = temp_person_repo.find_by_tag("family")
    assert len(family) == 2


def test_person_repo_list_all(temp_person_repo: PersonRepository) -> None:
    """Test listing all people."""
    p1 = StoredPerson(
        name="Person 1",
        birth_date="1990-01-15",
        birth_localtime="1990-01-15T09:13:00",
        birth_city="Test",
        birth_country="Test"
    )
    p2 = StoredPerson(
        name="Person 2",
        birth_date="1985-06-20",
        birth_localtime="1985-06-20T14:30:00",
        birth_city="Test",
        birth_country="Test"
    )
    
    temp_person_repo.add(p1)
    temp_person_repo.add(p2)
    
    all_people = temp_person_repo.list_all()
    assert len(all_people) == 2


def test_person_repo_list_all_tags(temp_person_repo: PersonRepository) -> None:
    """Test listing all unique tags."""
    p1 = StoredPerson(
        name="Person 1",
        birth_date="1990-01-15",
        birth_localtime="1990-01-15T09:13:00",
        birth_city="Test",
        birth_country="Test",
        tags=["client", "family"]
    )
    p2 = StoredPerson(
        name="Person 2",
        birth_date="1985-06-20",
        birth_localtime="1985-06-20T14:30:00",
        birth_city="Test",
        birth_country="Test",
        tags=["client", "VIP"]
    )
    
    temp_person_repo.add(p1)
    temp_person_repo.add(p2)
    
    tags = temp_person_repo.list_all_tags()
    assert len(tags) == 3
    assert "client" in tags
    assert "family" in tags
    assert "VIP" in tags


def test_person_repo_update(temp_person_repo: PersonRepository, sample_person: StoredPerson) -> None:
    """Test updating person."""
    temp_person_repo.add(sample_person)
    
    # Modify and update
    sample_person.add_tag("VIP")
    updated = temp_person_repo.update(sample_person)
    
    assert updated.has_tag("VIP")
    
    # Verify persistence
    retrieved = temp_person_repo.get(sample_person.id)
    assert retrieved is not None
    assert retrieved.has_tag("VIP")


def test_person_repo_update_nonexistent(
    temp_person_repo: PersonRepository,
    sample_person: StoredPerson
) -> None:
    """Test updating nonexistent person raises error."""
    with pytest.raises(ValueError, match="not found"):
        temp_person_repo.update(sample_person)


def test_person_repo_delete(temp_person_repo: PersonRepository, sample_person: StoredPerson) -> None:
    """Test deleting person."""
    temp_person_repo.add(sample_person)
    
    result = temp_person_repo.delete(sample_person.id)
    assert result is True
    
    # Verify deletion
    retrieved = temp_person_repo.get(sample_person.id)
    assert retrieved is None


def test_person_repo_delete_nonexistent(temp_person_repo: PersonRepository) -> None:
    """Test deleting nonexistent person returns False."""
    result = temp_person_repo.delete(uuid4())
    assert result is False


# RelationshipRepository Tests

def test_relationship_repo_add(temp_relationship_repo: RelationshipRepository) -> None:
    """Test adding relationship to repository."""
    rel = StoredRelationship(
        name="Test Relationship",
        person_ids=[str(uuid4()), str(uuid4())]
    )
    
    saved = temp_relationship_repo.add(rel)
    assert saved.id == rel.id
    assert saved.name == rel.name


def test_relationship_repo_find_by_name(temp_relationship_repo: RelationshipRepository) -> None:
    """Test finding relationship by name."""
    rel = StoredRelationship(
        name="Sandy + Heath",
        person_ids=[str(uuid4()), str(uuid4())]
    )
    
    temp_relationship_repo.add(rel)
    
    found = temp_relationship_repo.find_by_name("sandy + heath")
    assert found is not None
    assert found.name == rel.name


def test_relationship_repo_find_by_person(temp_relationship_repo: RelationshipRepository) -> None:
    """Test finding relationships containing a person."""
    person_id = uuid4()
    other_id = uuid4()
    
    rel1 = StoredRelationship(
        name="Rel 1",
        person_ids=[str(person_id), str(other_id)]
    )
    rel2 = StoredRelationship(
        name="Rel 2",
        person_ids=[str(person_id), str(uuid4())]
    )
    rel3 = StoredRelationship(
        name="Rel 3",
        person_ids=[str(uuid4()), str(uuid4())]
    )
    
    temp_relationship_repo.add(rel1)
    temp_relationship_repo.add(rel2)
    temp_relationship_repo.add(rel3)
    
    results = temp_relationship_repo.find_by_person(person_id)
    assert len(results) == 2


def test_relationship_repo_find_by_type(temp_relationship_repo: RelationshipRepository) -> None:
    """Test finding relationships by chart type."""
    interaction = StoredRelationship(
        name="Interaction",
        person_ids=[str(uuid4()), str(uuid4())]
    )
    penta = StoredRelationship(
        name="Penta",
        person_ids=[str(uuid4()), str(uuid4()), str(uuid4())]
    )
    multichart = StoredRelationship(
        name="Multichart",
        person_ids=[str(uuid4()) for _ in range(6)]
    )
    
    temp_relationship_repo.add(interaction)
    temp_relationship_repo.add(penta)
    temp_relationship_repo.add(multichart)
    
    interactions = temp_relationship_repo.find_by_type("interaction")
    assert len(interactions) == 1
    
    pentas = temp_relationship_repo.find_by_type("penta")
    assert len(pentas) == 1
    
    multicharts = temp_relationship_repo.find_by_type("multichart")
    assert len(multicharts) == 1


def test_relationship_repo_find_by_tag(temp_relationship_repo: RelationshipRepository) -> None:
    """Test finding relationships by tag."""
    rel1 = StoredRelationship(
        name="Rel 1",
        person_ids=[str(uuid4()), str(uuid4())],
        tags=["family"]
    )
    rel2 = StoredRelationship(
        name="Rel 2",
        person_ids=[str(uuid4()), str(uuid4())],
        tags=["family", "primary"]
    )
    rel3 = StoredRelationship(
        name="Rel 3",
        person_ids=[str(uuid4()), str(uuid4())],
        tags=["work"]
    )

    temp_relationship_repo.add(rel1)
    temp_relationship_repo.add(rel2)
    temp_relationship_repo.add(rel3)

    family_rels = temp_relationship_repo.find_by_tag("family")
    assert len(family_rels) == 2

    work_rels = temp_relationship_repo.find_by_tag("work")
    assert len(work_rels) == 1


def test_relationship_repo_validation_minimum(temp_relationship_repo: RelationshipRepository) -> None:
    """Test repository validates minimum 2 people."""
    rel = StoredRelationship(
        name="Invalid",
        person_ids=[str(uuid4())]  # Only 1 person
    )

    with pytest.raises(ValueError, match="at least 2 people"):
        temp_relationship_repo.add(rel)


def test_relationship_repo_validation_maximum(temp_relationship_repo: RelationshipRepository) -> None:
    """Test repository validates maximum 16 people."""
    rel = StoredRelationship(
        name="Invalid",
        person_ids=[str(uuid4()) for _ in range(17)]  # 17 people
    )

    with pytest.raises(ValueError, match="more than 16 people"):
        temp_relationship_repo.add(rel)
