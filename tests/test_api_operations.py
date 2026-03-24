"""
Unit tests for API operations.
"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from human_design.api import (
    add_person,
    add_transit_to_person,
    get_interaction,
    get_penta,
    get_person,
    get_relationship,
    list_people,
    list_relationships,
    save_relationship,
)
from human_design.models import BirthInfo, CompositeBodyGraph, LocalTime, Transit
from human_design.storage import PersonRepository, RelationshipRepository


@pytest.fixture
def temp_person_repo(tmp_path: Path) -> PersonRepository:
    """Create temporary person repository for testing."""
    return PersonRepository(storage_path=tmp_path / "people.json")


@pytest.fixture
def temp_relationship_repo(tmp_path: Path) -> RelationshipRepository:
    """Create temporary relationship repository for testing."""
    return RelationshipRepository(storage_path=tmp_path / "relationships.json")


@pytest.fixture
def sample_birth_info_1() -> BirthInfo:
    """Sample birth info for testing."""
    return BirthInfo(
        date="1990-01-15",
        localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
        city="Albuquerque",
        country="NM"
    )


@pytest.fixture
def sample_birth_info_2() -> BirthInfo:
    """Sample birth info for testing."""
    return BirthInfo(
        date="1985-06-20",
        localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
        city="Denver",
        country="CO"
    )


# add_person tests

def test_add_person(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo
) -> None:
    """Test adding person through API."""
    person = add_person(
        name="Sandy Rodriguez",
        birth_info=sample_birth_info_1,
        tags=["client", "family"],
        repo=temp_person_repo
    )
    
    assert person.name == "Sandy Rodriguez"
    assert len(person.tags) == 2
    assert person.id is not None
    
    # Verify persistence
    retrieved = temp_person_repo.get(person.id)
    assert retrieved is not None
    assert retrieved.name == person.name


def test_add_person_duplicate_name(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo
) -> None:
    """Test that adding duplicate name raises error."""
    add_person(
        name="Sandy Rodriguez",
        birth_info=sample_birth_info_1,
        repo=temp_person_repo
    )
    
    with pytest.raises(ValueError, match="already exists"):
        add_person(
            name="Sandy Rodriguez",
            birth_info=sample_birth_info_1,
            repo=temp_person_repo
        )


# get_person tests

def test_get_person_by_name(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo
) -> None:
    """Test getting person by name."""
    added = add_person(
        name="Sandy Rodriguez",
        birth_info=sample_birth_info_1,
        repo=temp_person_repo
    )
    
    retrieved = get_person("Sandy", repo=temp_person_repo)
    assert retrieved.id == added.id


def test_get_person_by_uuid(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo
) -> None:
    """Test getting person by UUID."""
    added = add_person(
        name="Sandy Rodriguez",
        birth_info=sample_birth_info_1,
        repo=temp_person_repo
    )
    
    retrieved = get_person(added.id, repo=temp_person_repo)
    assert retrieved.id == added.id


def test_get_person_not_found(temp_person_repo: PersonRepository) -> None:
    """Test getting nonexistent person raises error."""
    with pytest.raises(ValueError, match="not found"):
        get_person("Nonexistent", repo=temp_person_repo)


def test_get_person_ambiguous_name(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test that ambiguous name raises helpful error."""
    add_person(name="Sandy Rodriguez", birth_info=sample_birth_info_1, repo=temp_person_repo)
    add_person(name="Sandy Smith", birth_info=sample_birth_info_2, repo=temp_person_repo)
    
    with pytest.raises(ValueError, match="Multiple people match"):
        get_person("Sandy", repo=temp_person_repo)


# list_people tests

def test_list_people_all(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test listing all people."""
    add_person(name="Person 1", birth_info=sample_birth_info_1, repo=temp_person_repo)
    add_person(name="Person 2", birth_info=sample_birth_info_2, repo=temp_person_repo)
    
    all_people = list_people(repo=temp_person_repo)
    assert len(all_people) == 2


def test_list_people_by_tag(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test listing people filtered by tag."""
    add_person(
        name="Person 1",
        birth_info=sample_birth_info_1,
        tags=["client"],
        repo=temp_person_repo
    )
    add_person(
        name="Person 2",
        birth_info=sample_birth_info_2,
        tags=["family"],
        repo=temp_person_repo
    )
    
    clients = list_people(tag="client", repo=temp_person_repo)
    assert len(clients) == 1
    assert clients[0].name == "Person 1"


# get_interaction tests

def test_get_interaction(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test creating interaction chart."""
    p1 = add_person(name="Sandy", birth_info=sample_birth_info_1, repo=temp_person_repo)
    p2 = add_person(name="Heath", birth_info=sample_birth_info_2, repo=temp_person_repo)
    
    # Test by name
    interaction = get_interaction("Sandy", "Heath", repo=temp_person_repo)
    assert isinstance(interaction, CompositeBodyGraph)
    assert len(interaction.charts) == 2
    
    # Test by UUID
    interaction = get_interaction(p1.id, p2.id, repo=temp_person_repo)
    assert isinstance(interaction, CompositeBodyGraph)


def test_get_interaction_person_not_found(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo
) -> None:
    """Test interaction with nonexistent person raises error."""
    add_person(name="Sandy", birth_info=sample_birth_info_1, repo=temp_person_repo)
    
    with pytest.raises(ValueError, match="not found"):
        get_interaction("Sandy", "Nonexistent", repo=temp_person_repo)


# get_penta tests

def test_get_penta(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test creating penta chart."""
    add_person(name="Person 1", birth_info=sample_birth_info_1, repo=temp_person_repo)
    add_person(name="Person 2", birth_info=sample_birth_info_2, repo=temp_person_repo)
    add_person(name="Person 3", birth_info=sample_birth_info_1, repo=temp_person_repo)
    
    penta = get_penta(["Person 1", "Person 2", "Person 3"], repo=temp_person_repo)
    assert isinstance(penta, CompositeBodyGraph)
    assert len(penta.charts) == 3


def test_get_penta_too_few_people(temp_person_repo: PersonRepository) -> None:
    """Test penta with < 3 people raises error."""
    with pytest.raises(ValueError, match="at least 3"):
        get_penta(["Person 1", "Person 2"], repo=temp_person_repo)


def test_get_penta_too_many_people(temp_person_repo: PersonRepository) -> None:
    """Test penta with > 16 people raises error."""
    people = [f"Person {i}" for i in range(17)]
    with pytest.raises(ValueError, match="maximum 16"):
        get_penta(people, repo=temp_person_repo)


# add_transit_to_person tests

def test_add_transit_to_person(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo
) -> None:
    """Test adding transit to person's chart."""
    add_person(name="Sandy", birth_info=sample_birth_info_1, repo=temp_person_repo)
    
    transit = Transit.at(
        dt=datetime(2024, 6, 21, 12, 0),
        location="Denver, CO"
    )
    
    chart = add_transit_to_person("Sandy", transit=transit, repo=temp_person_repo)
    assert isinstance(chart, CompositeBodyGraph)
    assert len(chart.charts) == 2  # Birth chart + transit


def test_add_transit_default(
    temp_person_repo: PersonRepository,
    sample_birth_info_1: BirthInfo
) -> None:
    """Test adding default (now) transit."""
    add_person(name="Sandy", birth_info=sample_birth_info_1, repo=temp_person_repo)
    
    chart = add_transit_to_person("Sandy", repo=temp_person_repo)
    assert isinstance(chart, CompositeBodyGraph)


# save_relationship tests

def test_save_relationship(
    temp_person_repo: PersonRepository,
    temp_relationship_repo: RelationshipRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test saving relationship."""
    add_person(name="Sandy", birth_info=sample_birth_info_1, repo=temp_person_repo)
    add_person(name="Heath", birth_info=sample_birth_info_2, repo=temp_person_repo)
    
    rel = save_relationship(
        name="Sandy + Heath",
        people=["Sandy", "Heath"],
        tags=["marriage"],
        person_repo=temp_person_repo,
        rel_repo=temp_relationship_repo
    )
    
    assert rel.name == "Sandy + Heath"
    assert len(rel.person_ids) == 2
    assert rel.chart_type == "interaction"


def test_save_relationship_duplicate_name(
    temp_person_repo: PersonRepository,
    temp_relationship_repo: RelationshipRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test saving duplicate relationship name raises error."""
    add_person(name="Sandy", birth_info=sample_birth_info_1, repo=temp_person_repo)
    add_person(name="Heath", birth_info=sample_birth_info_2, repo=temp_person_repo)
    
    save_relationship(
        name="Sandy + Heath",
        people=["Sandy", "Heath"],
        person_repo=temp_person_repo,
        rel_repo=temp_relationship_repo
    )
    
    with pytest.raises(ValueError, match="already exists"):
        save_relationship(
            name="Sandy + Heath",
            people=["Sandy", "Heath"],
            person_repo=temp_person_repo,
            rel_repo=temp_relationship_repo
        )


def test_save_relationship_too_few_people(
    temp_person_repo: PersonRepository,
    temp_relationship_repo: RelationshipRepository
) -> None:
    """Test saving relationship with < 2 people raises error."""
    with pytest.raises(ValueError, match="at least 2"):
        save_relationship(
            name="Test",
            people=["Person 1"],
            person_repo=temp_person_repo,
            rel_repo=temp_relationship_repo
        )


# get_relationship tests

def test_get_relationship(
    temp_person_repo: PersonRepository,
    temp_relationship_repo: RelationshipRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test retrieving saved relationship."""
    add_person(name="Sandy", birth_info=sample_birth_info_1, repo=temp_person_repo)
    add_person(name="Heath", birth_info=sample_birth_info_2, repo=temp_person_repo)
    
    save_relationship(
        name="Sandy + Heath",
        people=["Sandy", "Heath"],
        person_repo=temp_person_repo,
        rel_repo=temp_relationship_repo
    )
    
    chart = get_relationship(
        "Sandy + Heath",
        person_repo=temp_person_repo,
        rel_repo=temp_relationship_repo
    )
    assert isinstance(chart, CompositeBodyGraph)
    assert len(chart.charts) == 2


def test_get_relationship_not_found(
    temp_person_repo: PersonRepository,
    temp_relationship_repo: RelationshipRepository
) -> None:
    """Test getting nonexistent relationship raises error."""
    with pytest.raises(ValueError, match="not found"):
        get_relationship(
            "Nonexistent",
            person_repo=temp_person_repo,
            rel_repo=temp_relationship_repo
        )


# list_relationships tests

def test_list_relationships(
    temp_person_repo: PersonRepository,
    temp_relationship_repo: RelationshipRepository,
    sample_birth_info_1: BirthInfo,
    sample_birth_info_2: BirthInfo
) -> None:
    """Test listing relationships."""
    add_person(name="Person 1", birth_info=sample_birth_info_1, repo=temp_person_repo)
    add_person(name="Person 2", birth_info=sample_birth_info_2, repo=temp_person_repo)
    
    save_relationship(
        name="Rel 1",
        people=["Person 1", "Person 2"],
        tags=["family"],
        person_repo=temp_person_repo,
        rel_repo=temp_relationship_repo
    )
    save_relationship(
        name="Rel 2",
        people=["Person 1", "Person 2"],
        tags=["work"],
        person_repo=temp_person_repo,
        rel_repo=temp_relationship_repo
    )
    
    # List all
    all_rels = list_relationships(rel_repo=temp_relationship_repo)
    assert len(all_rels) == 2
    
    # List by tag
    family_rels = list_relationships(tag="family", rel_repo=temp_relationship_repo)
    assert len(family_rels) == 1
    assert family_rels[0].name == "Rel 1"
