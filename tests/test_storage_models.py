"""
Unit tests for storage models.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from human_design.models import BirthInfo, LocalTime
from human_design.storage import StoredPerson, StoredRelationship


@pytest.fixture
def sample_birth_info() -> BirthInfo:
    """Sample birth information."""
    return BirthInfo(
        date="1990-01-15",
        localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
        city="Albuquerque",
        country="NM"
    )


def test_stored_person_creation(sample_birth_info: BirthInfo) -> None:
    """Test creating a stored person."""
    person = StoredPerson(
        name="Sandy Rodriguez",
        birth_date="1990-01-15",
        birth_localtime="1990-01-15T09:13:00",
        birth_city="Albuquerque",
        birth_country="NM",
        tags=["client", "family"]
    )

    assert person.name == "Sandy Rodriguez"
    assert len(person.tags) == 2
    assert "client" in person.tags
    assert person.id is not None
    assert isinstance(person.created_at, datetime)

    # Test that birth_info property reconstructs correctly
    birth_info = person.birth_info
    assert birth_info.date == "1990-01-15"
    assert birth_info.city == "Albuquerque"
    assert birth_info.country == "NM"


def test_stored_person_chart_property() -> None:
    """Test that chart property calculates bodygraph."""
    person = StoredPerson(
        name="Test Person",
        birth_date="1990-01-15",
        birth_localtime="1990-01-15T09:13:00",
        birth_city="Albuquerque",
        birth_country="NM"
    )

    chart = person.chart
    assert chart is not None
    assert hasattr(chart, "type")
    assert hasattr(chart, "authority")


def test_stored_person_tag_operations() -> None:
    """Test tag helper methods."""
    person = StoredPerson(
        name="Test",
        birth_date="1990-01-15",
        birth_localtime="1990-01-15T09:13:00",
        birth_city="Test",
        birth_country="Test",
        tags=["client"]
    )
    
    # has_tag (case-insensitive)
    assert person.has_tag("client")
    assert person.has_tag("CLIENT")
    assert not person.has_tag("family")
    
    # add_tag
    person.add_tag("family")
    assert person.has_tag("family")
    assert len(person.tags) == 2
    
    # add_tag (duplicate - should not add)
    person.add_tag("family")
    assert len(person.tags) == 2
    
    # remove_tag
    person.remove_tag("client")
    assert not person.has_tag("client")
    assert len(person.tags) == 1


def test_stored_relationship_creation() -> None:
    """Test creating a stored relationship."""
    id1, id2 = str(uuid4()), str(uuid4())

    rel = StoredRelationship(
        name="Sandy + Heath",
        person_ids=[id1, id2],
        tags=["marriage"]
    )
    
    assert rel.name == "Sandy + Heath"
    assert len(rel.person_ids) == 2
    assert rel.chart_type == "interaction"
    assert rel.id is not None


def test_stored_relationship_chart_type_classification() -> None:
    """Test chart type property logic."""
    # Interaction (2 people)
    rel = StoredRelationship(
        name="Test",
        person_ids=[str(uuid4()), str(uuid4())]
    )
    assert rel.chart_type == "interaction"

    # Penta (3-5 people)
    rel = StoredRelationship(
        name="Test",
        person_ids=[str(uuid4()), str(uuid4()), str(uuid4())]
    )
    assert rel.chart_type == "penta"

    rel = StoredRelationship(
        name="Test",
        person_ids=[str(uuid4()) for _ in range(5)]
    )
    assert rel.chart_type == "penta"

    # Multichart (6+ people)
    rel = StoredRelationship(
        name="Test",
        person_ids=[str(uuid4()) for _ in range(6)]
    )
    assert rel.chart_type == "multichart"


def test_stored_relationship_validation() -> None:
    """Test relationship validation rules.

    Note: With SQLModel tables, validation happens in the repository layer
    rather than at model initialization. See test_repository.py for
    repository-level validation tests.
    """
    # These should create successfully (validation happens in repository.add())
    rel1 = StoredRelationship(
        name="Test",
        person_ids=[str(uuid4())]  # Only 1 person - will fail at repo.add()
    )
    assert len(rel1.person_ids) == 1

    rel2 = StoredRelationship(
        name="Test",
        person_ids=[str(uuid4()) for _ in range(17)]  # 17 people - will fail at repo.add()
    )
    assert len(rel2.person_ids) == 17


def test_stored_relationship_helper_methods() -> None:
    """Test relationship helper methods."""
    id1, id2, id3 = str(uuid4()), str(uuid4()), str(uuid4())

    rel = StoredRelationship(
        name="Test",
        person_ids=[id1, id2],
        tags=["family"]
    )
    
    # has_person
    assert rel.has_person(id1)
    assert rel.has_person(id2)
    assert not rel.has_person(id3)
    
    # has_tag (case-insensitive)
    assert rel.has_tag("family")
    assert rel.has_tag("FAMILY")
    assert not rel.has_tag("work")
