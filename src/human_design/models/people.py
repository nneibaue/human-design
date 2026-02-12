"""
People models for 64keys API data.

Maps the cell array from 64keys list_api to named Pydantic fields.
"""

from pydantic import BaseModel, Field


class Person(BaseModel):
    """A person record from 64keys."""

    # Core identifiers
    row_number: int = Field(description="Row number in list (not the ID)")
    id: int = Field(description="64keys design ID")

    # Name
    lastname: str
    firstname: str

    # Demographics
    gender: str = Field(description="m/f/o")
    age: int | None = Field(default=None)

    # Human Design basics
    maintype: str = Field(
        description="Type: I=Initiator, C=Creator, B=Builder, S=Advisor, O=Observer"
    )
    cross_name: str = Field(description="Incarnation Cross name")
    profile: str = Field(description="Profile e.g. 3/5")
    cross_gates: str = Field(description="Cross gates e.g. 46-25/15-10")
    definitions: int = Field(description="Number of definitions 0-4")
    channels: str = Field(description="Comma-separated channel numbers")
    zodiac: str = Field(description="Sun sign abbreviation")

    # Birth data
    birth_date: str
    birth_time: str
    birth_variance: str = Field(description="Time uncertainty e.g. ± 12h")
    birth_country: str
    birth_city: str

    # Organization (optional)
    organisation: str = ""
    organisation_unit: str = ""
    department: str = ""
    team_name: str = ""
    co_function: str = ""
    since: int | None = None
    years: int | None = None
    flex: int | None = None
    pay: int | None = None
    qualification: int | None = None

    # Centers (1=defined, 0=undefined)
    centers_def: int = Field(description="Number of defined centers")
    center_1: int = Field(description="Head/Inspiration")
    center_2: int = Field(description="Ajna/Mind")
    center_3: int = Field(description="Throat/Expression")
    center_4: int = Field(description="G/Identity")
    center_5: int = Field(description="Heart/Will")
    center_6: int = Field(description="Solar Plexus/Emotion")
    center_7: int = Field(description="Sacral")
    center_8: int = Field(description="Spleen")
    center_9: int = Field(description="Root")

    # Team/Penta
    penta_role: str = Field(description="Role in team: No/Role/Energy/R+E/Support")
    gate_31: int = 0
    gate_7: int = 0
    gate_5: int = 0
    gate_15: int = 0
    gate_8: int = 0
    gate_1: int = 0
    gate_2: int = 0
    gate_14: int = 0
    gate_33: int = 0
    gate_13: int = 0
    gate_29: int = 0
    gate_46: int = 0

    # Full name (redundant but included)
    full_name: str = ""

    # Powerbase
    primary_powerbase: str = ""
    pb_organisation: int = 0
    pb_competition: int = 0
    pb_direction: int = 0
    pb_interaction: int = 0
    pb_strategy: int = 0
    pb_innovation: int = 0

    # O16 gates
    o_gate_45: int = 0
    o_gate_21: int = 0
    o_gate_51: int = 0
    o_gate_25: int = 0
    o_gate_2: int = 0
    o_gate_14: int = 0
    o_gate_59: int = 0
    o_gate_6: int = 0
    o_gate_27: int = 0
    o_gate_50: int = 0
    o_gate_3: int = 0
    o_gate_60: int = 0

    # Talent/Pearl
    pearl_talent: str = ""
    pearl_cooperation: str = ""
    pearl_charisma: str = ""
    pearl_prosperity: str = ""

    # Below/Variable
    variable_four: str = ""
    variable_type: str = ""
    motivation_color: str = ""
    motivation_tone: str = ""
    perspective_color: str = ""
    perspective_tone: str = ""
    health_color: str = ""
    health_tone: str = ""
    environment_color: str = ""
    environment_tone: str = ""
    p_sun_base: str = ""
    d_moon_color: str = ""

    # Lines
    line_sum_1: int = 0
    line_sum_2: int = 0
    line_sum_3: int = 0
    line_sum_4: int = 0
    line_sum_5: int = 0
    line_sum_6: int = 0

    # Labels/Relations
    related_by: str = ""
    families: str = ""
    tags: str = ""

    # User permissions
    view_users: str = ""
    edit_users: str = ""

    # Admin
    created_at: str = ""
    username: str = ""

    # Flags
    has_type_variance: bool = False
    has_modus_variance: bool = False
    is_verified: bool = False

    # Group membership (our addition)
    groups: list[str] = Field(
        default_factory=list, description="64keys groups this person belongs to"
    )

    # Custom tags (our addition)
    custom_tags: list[str] = Field(default_factory=list, description="User-defined tags")

    @classmethod
    def from_cell(cls, cell: list, groups: list[str] | None = None) -> "Person":
        """
        Create a Person from a 64keys cell array.

        The cell array positions are based on the jqGrid colModel configuration.
        """

        def safe_int(val, default: int = 0) -> int:
            if val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        def safe_str(val, default: str = "") -> str:
            if val is None:
                return default
            return str(val)

        def safe_bool(val) -> bool:
            return val == 1 or val == "1" or val is True

        return cls(
            row_number=safe_int(cell[0]),
            lastname=safe_str(cell[1]),
            firstname=safe_str(cell[2]),
            gender=safe_str(cell[3]),
            age=safe_int(cell[4]) if cell[4] else None,
            maintype=safe_str(cell[5]),
            cross_name=safe_str(cell[6]),
            profile=safe_str(cell[7]),
            cross_gates=safe_str(cell[8]),
            definitions=safe_int(cell[9]),
            channels=safe_str(cell[10]),
            zodiac=safe_str(cell[11]),
            birth_date=safe_str(cell[12]),
            birth_time=safe_str(cell[13]),
            birth_variance=safe_str(cell[14]),
            birth_country=safe_str(cell[15]),
            birth_city=safe_str(cell[16]),
            organisation=safe_str(cell[17]),
            organisation_unit=safe_str(cell[18]),
            department=safe_str(cell[19]),
            team_name=safe_str(cell[20]),
            co_function=safe_str(cell[21]),
            since=safe_int(cell[22]) if cell[22] else None,
            years=safe_int(cell[23]) if cell[23] else None,
            flex=safe_int(cell[24]) if cell[24] else None,
            pay=safe_int(cell[25]) if cell[25] else None,
            qualification=safe_int(cell[26]) if cell[26] else None,
            centers_def=safe_int(cell[27]),
            center_1=safe_int(cell[28]),
            center_2=safe_int(cell[29]),
            center_3=safe_int(cell[30]),
            center_4=safe_int(cell[31]),
            center_5=safe_int(cell[32]),
            center_6=safe_int(cell[33]),
            center_7=safe_int(cell[34]),
            center_8=safe_int(cell[35]),
            center_9=safe_int(cell[36]),
            penta_role=safe_str(cell[37]),
            gate_31=safe_int(cell[38]),
            gate_7=safe_int(cell[39]),
            gate_5=safe_int(cell[40]),
            gate_15=safe_int(cell[41]),
            gate_8=safe_int(cell[42]),
            gate_1=safe_int(cell[43]),
            gate_2=safe_int(cell[44]),
            gate_14=safe_int(cell[45]),
            gate_33=safe_int(cell[46]),
            gate_13=safe_int(cell[47]),
            gate_29=safe_int(cell[48]),
            gate_46=safe_int(cell[49]),
            full_name=safe_str(cell[50]),
            primary_powerbase=safe_str(cell[51]),
            pb_organisation=safe_int(cell[52]),
            pb_competition=safe_int(cell[53]),
            pb_direction=safe_int(cell[54]),
            pb_interaction=safe_int(cell[55]),
            pb_strategy=safe_int(cell[56]),
            pb_innovation=safe_int(cell[57]),
            o_gate_45=safe_int(cell[58]),
            o_gate_21=safe_int(cell[59]),
            o_gate_51=safe_int(cell[60]),
            o_gate_25=safe_int(cell[61]),
            o_gate_2=safe_int(cell[62]),
            o_gate_14=safe_int(cell[63]),
            o_gate_59=safe_int(cell[64]),
            o_gate_6=safe_int(cell[65]),
            o_gate_27=safe_int(cell[66]),
            o_gate_50=safe_int(cell[67]),
            o_gate_3=safe_int(cell[68]),
            o_gate_60=safe_int(cell[69]),
            pearl_talent=safe_str(cell[70]),
            pearl_cooperation=safe_str(cell[71]),
            pearl_charisma=safe_str(cell[72]),
            pearl_prosperity=safe_str(cell[73]),
            variable_four=safe_str(cell[74]),
            variable_type=safe_str(cell[75]),
            motivation_color=safe_str(cell[76]),
            motivation_tone=safe_str(cell[77]),
            perspective_color=safe_str(cell[78]),
            perspective_tone=safe_str(cell[79]),
            health_color=safe_str(cell[80]),
            health_tone=safe_str(cell[81]),
            environment_color=safe_str(cell[82]),
            environment_tone=safe_str(cell[83]),
            p_sun_base=safe_str(cell[84]),
            d_moon_color=safe_str(cell[85]),
            line_sum_1=safe_int(cell[86]),
            line_sum_2=safe_int(cell[87]),
            line_sum_3=safe_int(cell[88]),
            line_sum_4=safe_int(cell[89]),
            line_sum_5=safe_int(cell[90]),
            line_sum_6=safe_int(cell[91]),
            related_by=safe_str(cell[92]),
            families=safe_str(cell[93]),
            tags=safe_str(cell[94]),
            view_users=safe_str(cell[95]),
            edit_users=safe_str(cell[96]),
            id=safe_int(cell[97]),
            created_at=safe_str(cell[98]),
            username=safe_str(cell[99]),
            has_type_variance=safe_bool(cell[100]) if len(cell) > 100 else False,
            has_modus_variance=safe_bool(cell[101]) if len(cell) > 101 else False,
            is_verified=safe_bool(cell[102]) if len(cell) > 102 else False,
            groups=groups or [],
            custom_tags=[],
        )


class PeopleResponse(BaseModel):
    """Response from the people API."""

    total: int
    people: list[Person]


class Relationship(BaseModel):
    """A relationship between two people.

    This models the graph edge: Person A has relationship R to Person B.
    Example: {"from_id": 123, "to_id": 456, "relationship": "husband", "notes": "Sandy's husband"}

    Common relationship types:
    - Family: mother, father, sister, brother, daughter, son, grandmother, grandfather, aunt, uncle, cousin
    - Partner: husband, wife, partner, ex-husband, ex-wife, ex-partner
    - Friend: best_friend, close_friend, friend
    - Professional: client, colleague, mentor, mentee
    """

    from_id: int = Field(description="The person who 'has' this relationship")
    to_id: int = Field(description="The related person")
    relationship: str = Field(
        description="Type of relationship (mother, husband, best_friend, etc)"
    )
    notes: str = Field(default="", description="Optional notes about the relationship")


class HumunGroup(BaseModel):
    """A custom group of people (family, workshop, etc).

    Following Rebecca's philosophy:
    - The person who came first 'owns' the group
    - Group name often includes the owner (e.g. 'Sandy family')
    - Members can graduate to own their own groups later
    """

    name: str = Field(description="Group name, e.g. 'Sandy family'")
    owner_id: int | None = Field(
        default=None, description="The person who 'owns' this group (came first)"
    )
    member_ids: list[int] = Field(default_factory=list, description="All members including owner")
    description: str = Field(default="", description="Notes about this group")
    created_at: str = Field(default="", description="When this group was created")


class RelationshipStore(BaseModel):
    """Storage for relationships between people (graph edges).

    This implements a directed graph where each edge represents a relationship.
    """

    relationships: list[Relationship] = Field(default_factory=list)

    def add_relationship(
        self, from_id: int, to_id: int, relationship: str, notes: str = ""
    ) -> None:
        """Add a relationship between two people."""
        # Check if relationship already exists
        for rel in self.relationships:
            if rel.from_id == from_id and rel.to_id == to_id:
                # Update existing
                rel.relationship = relationship
                rel.notes = notes
                return
        # Add new
        self.relationships.append(
            Relationship(from_id=from_id, to_id=to_id, relationship=relationship, notes=notes)
        )

    def remove_relationship(self, from_id: int, to_id: int) -> None:
        """Remove a relationship between two people."""
        self.relationships = [
            r for r in self.relationships if not (r.from_id == from_id and r.to_id == to_id)
        ]

    def get_relationships_for(self, person_id: int) -> list[Relationship]:
        """Get all relationships where this person is the 'from' side."""
        return [r for r in self.relationships if r.from_id == person_id]

    def get_relationships_to(self, person_id: int) -> list[Relationship]:
        """Get all relationships where this person is the 'to' side."""
        return [r for r in self.relationships if r.to_id == person_id]

    def get_all_related(self, person_id: int) -> list[int]:
        """Get all people related to this person (either direction)."""
        related = set()
        for r in self.relationships:
            if r.from_id == person_id:
                related.add(r.to_id)
            if r.to_id == person_id:
                related.add(r.from_id)
        return list(related)


class GroupStore(BaseModel):
    """Storage for custom humun groups."""

    groups: list[HumunGroup] = Field(default_factory=list)

    def add_group(
        self, name: str, owner_id: int | None = None, description: str = ""
    ) -> HumunGroup:
        """Create a new group."""
        group = HumunGroup(
            name=name,
            owner_id=owner_id,
            member_ids=[owner_id] if owner_id else [],
            description=description,
        )
        self.groups.append(group)
        return group

    def get_group(self, name: str) -> HumunGroup | None:
        """Get a group by name."""
        for g in self.groups:
            if g.name == name:
                return g
        return None

    def add_member(self, group_name: str, person_id: int) -> None:
        """Add a member to a group."""
        group = self.get_group(group_name)
        if group and person_id not in group.member_ids:
            group.member_ids.append(person_id)

    def remove_member(self, group_name: str, person_id: int) -> None:
        """Remove a member from a group."""
        group = self.get_group(group_name)
        if group and person_id in group.member_ids:
            group.member_ids.remove(person_id)

    def get_groups_for_person(self, person_id: int) -> list[HumunGroup]:
        """Get all groups a person belongs to."""
        return [g for g in self.groups if person_id in g.member_ids]

    def delete_group(self, name: str) -> None:
        """Delete a group."""
        self.groups = [g for g in self.groups if g.name != name]


class TagStore(BaseModel):
    """Storage for custom tags per person."""

    # person_id -> list of tags
    tags: dict[int, list[str]] = Field(default_factory=dict)

    def get_tags(self, person_id: int) -> list[str]:
        """Get tags for a person."""
        return self.tags.get(person_id, [])

    def add_tag(self, person_id: int, tag: str) -> None:
        """Add a tag to a person."""
        if person_id not in self.tags:
            self.tags[person_id] = []
        if tag not in self.tags[person_id]:
            self.tags[person_id].append(tag)

    def remove_tag(self, person_id: int, tag: str) -> None:
        """Remove a tag from a person."""
        if person_id in self.tags and tag in self.tags[person_id]:
            self.tags[person_id].remove(tag)
            if not self.tags[person_id]:
                del self.tags[person_id]

    def all_tags(self) -> list[str]:
        """Get all unique tags."""
        all_tags: set[str] = set()
        for tags in self.tags.values():
            all_tags.update(tags)
        return sorted(all_tags)
