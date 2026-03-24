"""
Storage repository for Human Design people and relationships.

SQLModel/SQLAlchemy-based storage with tag-based queries.
"""

from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import Session, create_engine, select, SQLModel

from .models import StoredPerson, StoredRelationship


class StorageConfig(BaseModel):
    """Configuration for database storage."""

    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{Path.home() / '.human-design' / 'human_design.db'}",
        description="Database connection URL (default: SQLite in ~/.human-design/)"
    )

    def ensure_directories(self) -> None:
        """Create storage directory if using SQLite."""
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)


def get_engine(config: StorageConfig | None = None):
    """
    Get SQLAlchemy engine for database operations.

    Args:
        config: Storage configuration (uses default if None)

    Returns:
        SQLAlchemy engine
    """
    if config is None:
        config = StorageConfig()

    config.ensure_directories()
    engine = create_engine(
        config.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in config.database_url else {}
    )

    # Create tables if they don't exist
    SQLModel.metadata.create_all(engine)

    return engine


class PersonRepository:
    """
    Repository for person storage with tag-based queries.

    Uses SQLModel/SQLAlchemy for database operations:
    - Proper ACID transactions
    - Indexing for fast queries
    - Type-safe ORM models
    - Scalable to large datasets

    Thread-safety: Safe with proper session management
    Performance: Indexed queries with database optimization

    Example:
        >>> repo = PersonRepository()
        >>> sandy = repo.add(StoredPerson(name="Sandy", ...))
        >>> heath = repo.find_by_name("Heath")
        >>> clients = repo.find_by_tag("client")
    """

    def __init__(self, database_url: str | None = None):
        """
        Initialize repository.

        Args:
            database_url: Database connection URL. Defaults to SQLite in ~/.human-design/
        """
        config = StorageConfig() if database_url is None else StorageConfig(database_url=database_url)
        self.engine = get_engine(config)
    
    def add(self, person: StoredPerson) -> StoredPerson:
        """
        Add person to storage.

        Args:
            person: Person to add

        Returns:
            Same person (now persisted)

        Raises:
            ValueError: If person with this ID already exists

        Example:
            >>> person = StoredPerson(name="Sandy", birth_date="1990-01-15", ...)
            >>> saved = repo.add(person)
            >>> print(saved.id)
        """
        with Session(self.engine) as session:
            # Check for duplicate ID
            existing = session.get(StoredPerson, person.id)
            if existing:
                raise ValueError(f"Person with ID {person.id} already exists")

            session.add(person)
            session.commit()
            session.refresh(person)
            return person
    
    def get(self, person_id: UUID | str) -> StoredPerson | None:
        """
        Get person by ID.

        Args:
            person_id: UUID or string representation

        Returns:
            Person if found, None otherwise

        Example:
            >>> person = repo.get("550e8400-e29b-41d4-a716-446655440000")
            >>> person = repo.get(uuid_obj)
        """
        if isinstance(person_id, str):
            person_id = UUID(person_id)

        with Session(self.engine) as session:
            return session.get(StoredPerson, person_id)
    
    def find_by_name(self, name: str, case_sensitive: bool = False) -> StoredPerson | None:
        """
        Find person by exact name match.

        Args:
            name: Name to search for
            case_sensitive: Whether to match case (default: False)

        Returns:
            First matching person, or None

        Example:
            >>> sandy = repo.find_by_name("Sandy Rodriguez")
            >>> heath = repo.find_by_name("heath", case_sensitive=False)
        """
        with Session(self.engine) as session:
            if case_sensitive:
                statement = select(StoredPerson).where(StoredPerson.name == name)
            else:
                statement = select(StoredPerson).where(func.lower(StoredPerson.name) == name.lower())

            return session.exec(statement).first()
    
    def search_by_name(self, query: str) -> list[StoredPerson]:
        """
        Fuzzy search by name (substring match).

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching people (may be empty)

        Example:
            >>> # Find all "Rodriguez" family members
            >>> results = repo.search_by_name("Rodriguez")
            >>> # Find all "Sandy" variations
            >>> results = repo.search_by_name("Sandy")
        """
        with Session(self.engine) as session:
            statement = select(StoredPerson).where(
                func.lower(StoredPerson.name).contains(query.lower())
            )
            return list(session.exec(statement).all())
    
    def find_by_tag(self, tag: str) -> list[StoredPerson]:
        """
        Find all people with specific tag.

        Args:
            tag: Tag to search for (case-insensitive)

        Returns:
            List of people with tag (may be empty)

        Example:
            >>> clients = repo.find_by_tag("client")
            >>> family = repo.find_by_tag("Sandy's group")
        """
        with Session(self.engine) as session:
            statement = select(StoredPerson)
            people = session.exec(statement).all()
            return [p for p in people if p.has_tag(tag)]
    
    def list_all(self) -> list[StoredPerson]:
        """
        List all people in storage.

        Returns:
            All people, ordered by creation date (newest first)

        Example:
            >>> all_people = repo.list_all()
            >>> for person in all_people:
            ...     print(f"{person.name}: {person.tags}")
        """
        with Session(self.engine) as session:
            statement = select(StoredPerson).order_by(StoredPerson.created_at.desc())
            return list(session.exec(statement).all())
    
    def list_all_tags(self) -> list[str]:
        """
        Get all unique tags used across all people.

        Returns:
            Sorted list of unique tags

        Example:
            >>> tags = repo.list_all_tags()
            >>> print(tags)  # ['client', 'family', 'Sandy's group']
        """
        with Session(self.engine) as session:
            statement = select(StoredPerson)
            people = session.exec(statement).all()
            tags: set[str] = set()
            for person in people:
                tags.update(person.tags)
            return sorted(tags)
    
    def update(self, person: StoredPerson) -> StoredPerson:
        """
        Update person in storage.

        Args:
            person: Person with updated data (ID must match existing)

        Returns:
            Updated person

        Raises:
            ValueError: If person ID not found

        Example:
            >>> sandy = repo.find_by_name("Sandy")
            >>> sandy.add_tag("VIP")
            >>> repo.update(sandy)
        """
        with Session(self.engine) as session:
            existing = session.get(StoredPerson, person.id)
            if not existing:
                raise ValueError(f"Person with ID {person.id} not found")

            # Update fields
            for field in StoredPerson.model_fields:
                setattr(existing, field, getattr(person, field))

            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
    
    def delete(self, person_id: UUID | str) -> bool:
        """
        Delete person from storage.

        Args:
            person_id: UUID or string representation

        Returns:
            True if deleted, False if not found

        Example:
            >>> repo.delete("550e8400-e29b-41d4-a716-446655440000")
            >>> repo.delete(uuid_obj)
        """
        if isinstance(person_id, str):
            person_id = UUID(person_id)

        with Session(self.engine) as session:
            person = session.get(StoredPerson, person_id)
            if not person:
                return False

            session.delete(person)
            session.commit()
            return True


class RelationshipRepository:
    """
    Repository for relationship storage.

    Similar to PersonRepository but for saved chart combinations.

    Example:
        >>> repo = RelationshipRepository()
        >>> rel = repo.add(StoredRelationship(
        ...     name="Sandy + Heath",
        ...     person_ids=[sandy_id, heath_id]
        ... ))
        >>> pentas = repo.find_by_type("penta")
    """

    def __init__(self, database_url: str | None = None):
        """
        Initialize repository.

        Args:
            database_url: Database connection URL. Defaults to SQLite in ~/.human-design/
        """
        config = StorageConfig() if database_url is None else StorageConfig(database_url=database_url)
        self.engine = get_engine(config)
    
    def add(self, relationship: StoredRelationship) -> StoredRelationship:
        """Add relationship to storage."""
        # Validate person_ids length
        count = len(relationship.person_ids)
        if count < 2:
            raise ValueError("Relationship must have at least 2 people")
        if count > 16:
            raise ValueError("Relationship cannot have more than 16 people")

        with Session(self.engine) as session:
            # Check for duplicate ID
            existing = session.get(StoredRelationship, relationship.id)
            if existing:
                raise ValueError(f"Relationship with ID {relationship.id} already exists")

            session.add(relationship)
            session.commit()
            session.refresh(relationship)
            return relationship
    
    def get(self, relationship_id: UUID | str) -> StoredRelationship | None:
        """Get relationship by ID."""
        if isinstance(relationship_id, str):
            relationship_id = UUID(relationship_id)

        with Session(self.engine) as session:
            return session.get(StoredRelationship, relationship_id)
    
    def find_by_name(self, name: str, case_sensitive: bool = False) -> StoredRelationship | None:
        """Find relationship by exact name match."""
        with Session(self.engine) as session:
            if case_sensitive:
                statement = select(StoredRelationship).where(StoredRelationship.name == name)
            else:
                statement = select(StoredRelationship).where(
                    func.lower(StoredRelationship.name) == name.lower()
                )

            return session.exec(statement).first()
    
    def find_by_person(self, person_id: UUID | str) -> list[StoredRelationship]:
        """Find all relationships containing a specific person."""
        if isinstance(person_id, str):
            person_id = UUID(person_id)

        with Session(self.engine) as session:
            statement = select(StoredRelationship)
            relationships = session.exec(statement).all()
            return [r for r in relationships if r.has_person(person_id)]
    
    def find_by_type(
        self,
        chart_type: Literal["interaction", "penta", "multichart"]
    ) -> list[StoredRelationship]:
        """Find all relationships of specific type."""
        with Session(self.engine) as session:
            statement = select(StoredRelationship)
            relationships = session.exec(statement).all()
            return [r for r in relationships if r.chart_type == chart_type]
    
    def find_by_tag(self, tag: str) -> list[StoredRelationship]:
        """Find all relationships with specific tag."""
        with Session(self.engine) as session:
            statement = select(StoredRelationship)
            relationships = session.exec(statement).all()
            return [r for r in relationships if r.has_tag(tag)]
    
    def list_all(self) -> list[StoredRelationship]:
        """List all relationships, ordered by creation date (newest first)."""
        with Session(self.engine) as session:
            statement = select(StoredRelationship).order_by(StoredRelationship.created_at.desc())
            return list(session.exec(statement).all())
    
    def update(self, relationship: StoredRelationship) -> StoredRelationship:
        """Update relationship in storage."""
        with Session(self.engine) as session:
            existing = session.get(StoredRelationship, relationship.id)
            if not existing:
                raise ValueError(f"Relationship with ID {relationship.id} not found")

            # Update fields
            for field in StoredRelationship.model_fields:
                setattr(existing, field, getattr(relationship, field))

            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
    
    def delete(self, relationship_id: UUID | str) -> bool:
        """Delete relationship from storage."""
        if isinstance(relationship_id, str):
            relationship_id = UUID(relationship_id)

        with Session(self.engine) as session:
            relationship = session.get(StoredRelationship, relationship_id)
            if not relationship:
                return False

            session.delete(relationship)
            session.commit()
            return True
