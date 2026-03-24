"""
Storage models for Human Design people and relationships.

These models enable storing birth information with tags for quick recall
during client sessions.
"""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import computed_field, field_serializer, field_validator
from sqlmodel import JSON, Column, Field, SQLModel

from ..models.bodygraph import BirthInfo, RawBodyGraph


class StoredPerson(SQLModel, table=True):
    """
    A person with birth info and tags for quick recall.

    Enables workflows like:
        - "Show me Sandy's chart"
        - "Find all people in 'Sandy's group'"
        - "List all clients"

    Birth information is stored, bodygraph calculated on demand.
    """

    __tablename__ = "people"  # type: ignore

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Sandy Rodriguez",
                "tags": ["client", "family", "Sandy's group"],
                "birth_date": "1990-01-15",
                "birth_localtime": "1990-01-15T09:13:00",
                "birth_city": "Albuquerque",
                "birth_country": "NM",
                "created_at": "2024-01-15T10:30:00"
            }
        }
    }

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique identifier"
    )

    name: str = Field(
        min_length=1,
        index=True,
        description="Full name (e.g., 'Sandy Rodriguez', 'Heath (husband)')"
    )

    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),  # type: ignore
        description="Tags for grouping (e.g., 'family', 'client', 'Sandy's group')"
    )

    # Birth information fields (denormalized for query performance)
    birth_date: str = Field(
        description="Birth date in YYYY-MM-DD format"
    )

    birth_localtime: str = Field(
        description="Birth time in ISO format (YYYY-MM-DDTHH:MM:SS)"
    )

    birth_city: str = Field(
        index=True,
        description="Birth city"
    )

    birth_country: str = Field(
        index=True,
        description="Birth country"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this person was added to storage"
    )
    
    @computed_field  # type: ignore
    @property
    def birth_info(self) -> BirthInfo:
        """
        Reconstruct BirthInfo from stored fields.

        This allows the rest of the codebase to work with BirthInfo objects
        while the database stores individual queryable fields.
        """
        return BirthInfo(
            date=self.birth_date,
            localtime=self.birth_localtime,
            city=self.birth_city,
            country=self.birth_country,
        )

    @computed_field  # type: ignore
    @property
    def chart(self) -> RawBodyGraph:
        """
        Calculate bodygraph on demand.

        Not cached - calculations are fast enough to recompute.
        This ensures chart always reflects current implementation.
        """
        return RawBodyGraph(birth_info=self.birth_info)
    
    def has_tag(self, tag: str) -> bool:
        """Check if person has specific tag (case-insensitive)."""
        return tag.lower() in [t.lower() for t in self.tags]
    
    def add_tag(self, tag: str) -> None:
        """Add tag if not already present."""
        if not self.has_tag(tag):
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove tag if present (case-insensitive)."""
        self.tags = [t for t in self.tags if t.lower() != tag.lower()]


class StoredRelationship(SQLModel, table=True):
    """
    A saved relationship (interaction, penta, multichart) with metadata.

    Enables workflows like:
        - "Show me Sandy + Heath interaction"
        - "Pull up Sandy's family penta"
        - "Show all pentas I've created"

    Chart is calculated on demand from stored person IDs.
    """

    __tablename__ = "relationships"  # type: ignore

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "650e8400-e29b-41d4-a716-446655440001",
                "name": "Sandy + Heath",
                "person_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440002"
                ],
                "tags": ["marriage", "primary"],
                "created_at": "2024-01-15T11:00:00"
            }
        }
    }

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique identifier"
    )

    name: str = Field(
        min_length=1,
        index=True,
        description="Relationship name (e.g., 'Sandy + Heath', 'Sandy's family')"
    )

    person_ids: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),  # type: ignore
        description="UUIDs of people in this relationship (stored as strings, 2-16)"
    )

    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),  # type: ignore
        description="Tags for grouping (e.g., 'family', 'work team')"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this relationship was saved"
    )

    @computed_field  # type: ignore
    @property
    def chart_type(self) -> str:
        """
        Classify chart type based on number of people.
        
        - 2 people: "interaction"
        - 3-5 people: "penta"
        - 6-16 people: "multichart"
        
        This is Human Design terminology from 64keys.
        """
        count = len(self.person_ids)
        if count == 2:
            return "interaction"
        elif 3 <= count <= 5:
            return "penta"
        else:
            return "multichart"
    
    def has_person(self, person_id: UUID | str) -> bool:
        """Check if person is in this relationship."""
        person_id_str = str(person_id)
        return person_id_str in self.person_ids
    
    def has_tag(self, tag: str) -> bool:
        """Check if relationship has specific tag (case-insensitive)."""
        return tag.lower() in [t.lower() for t in self.tags]
