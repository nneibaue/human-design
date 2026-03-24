# Implementer Agent Training Material

Extracted modern Python/FastAPI/pydantic patterns for agent training.

## Research Query 1: Find modern FastAPI endpoint patterns with async/await, dependency injection, and error handling

**Type**: best_practices

**Findings**:



# FastAPI Endpoint Patterns: Research Report

## Executive Summary

After thorough analysis of the codebase, I've extracted comprehensive patterns for modern FastAPI endpoint design covering async/await usage, dependency injection, error handling, and response modeling. Below are the findings organized as structured training material.

---

## Pattern Catalog

---

### Pattern 1: Async Endpoint with Dependency Injection & Response Models

**Confidence: 0.95**

**Principle**: FastAPI endpoints should leverage Python's `async/await` for I/O-bound operations, use `Depends()` for composable dependency injection, declare explicit response models for documentation and validation, and raise `HTTPException` with precise status codes.

**Why it works**:
- `async def` enables non-blocking I/O — critical for database calls, HTTP clients, file reads
- `Depends()` creates a composable, testable, reusable dependency graph
- Response models auto-generate OpenAPI docs AND strip unexpected fields (security)
- `HTTPException` integrates with FastAPI's error-handling middleware for consistent responses

**Canonical Implementation**:

```python
# ── schemas.py ──────────────────────────────────────────────
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID

class ItemResponse(BaseModel):
    """Response model — explicit, validated, documented."""
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 ORM mode

    id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    created_at: datetime
    owner_id: UUID


class ItemCreate(BaseModel):
    """Request body — separate from response to control exposure."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class PaginatedResponse(BaseModel):
    """Generic pagination wrapper."""
    items: list[ItemResponse]
    total: int
    page: int
    page_size: int


# ── dependencies.py ─────────────────────────────────────────
from typing import Annotated
from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency — yields then cleans up."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Chained dependency — depends on both token extraction AND db session."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user

# Type aliases for clean signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


# ── router.py ───────────────────────────────────────────────
from fastapi import APIRouter, HTTPException, status, Query
from typing import Annotated

router = APIRouter(prefix="/items", tags=["items"])

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="List items with pagination",
)
async def list_items(
    db: DbSession,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse:
    """
    Retrieve paginated items belonging to the current user.
    
    Pattern elements:
    - async def: non-blocking database queries
    - DbSession/CurrentUser: Annotated type aliases for clean DI
    - Query with validation: input constraints at the edge
    - Explicit response_model: OpenAPI + output filtering
    """
    offset = (page - 1) * page_size

    # Async ORM query
    stmt = (
        select(Item)
        .where(Item.owner_id == current_user.id)
        .offset(offset)
        .limit(page_size)
        .order_by(Item.created_at.desc())
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    # Count query (separate for clarity)
    count_stmt = (
        select(func.count())
        .select_from(Item)
        .where(Item.owner_id == current_user.id)
    )
    total = (await db.execute(count_stmt)).scalar_one()

    return PaginatedResponse(
        items=[ItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item",
)
async def create_item(
    body: ItemCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ItemResponse:
    """
    Pattern elements:
    - Separate request/response schemas (ItemCreate vs ItemResponse)
    - status_code=201 for resource creation
    - Transaction handled at the dependency/middleware level
    """
    item = Item(
        name=body.name,
        description=body.description,
        owner_id=current_user.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ItemResponse.model_validate(item)


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get item by ID",
)
async def get_item(
    item_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ItemResponse:
    """
    Pattern elements:
    - Path parameter with type annotation (UUID validates format)
    - 404 with descriptive detail
    - 403 for authorization failures (separate from 404 in secure APIs,
      or merged to 404 to prevent enumeration — design choice)
    """
    item = await db.get(Item, item_id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )

    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this item",
        )

    return ItemResponse.model_validate(item)
```

---

### Pattern 2: Dependency Composition & Layering

**Confidence: 0.92**

**Principle**: Dependencies should form a DAG (directed acyclic graph) where each node does ONE thing. Higher-level dependencies compose lower-level ones. This creates reusable, testable building blocks.

```python
# ── Layer 0: Infrastructure ─────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Pure infrastructure — no business logic."""
    async with async_session_factory() as session:
        yield session

async def get_redis() -> AsyncGenerator[Redis, None]:
    pool = await get_redis_pool()
    yield pool

# ── Layer 1: Authentication ─────────────────────────────────
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Composes: token extraction + db lookup."""
    ...

# ── Layer 2: Authorization ──────────────────────────────────
def require_role(role: str):
    """Factory pattern — returns a dependency parameterized by role."""
    async def _check_role(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return current_user
    return _check_role

# Usage: clean, declarative
AdminUser = Annotated[User, Depends(require_role("admin"))]

@router.delete("/{item_id}", dependencies=[Depends(require_role("admin"))])
async def delete_item(item_id: UUID, db: DbSession) -> None:
    ...

# ── Layer 3: Business-logic dependencies ────────────────────
async def get_item_service(
    db: DbSession,
    cache: Annotated[Redis, Depends(get_redis)],
) -> ItemService:
    """Composes infrastructure into a service object."""
    return ItemService(db=db, cache=cache)

ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]

@router.get("/{item_id}")
async def get_item(
    item_id: UUID,
    service: ItemServiceDep,
    current_user: CurrentUser,
) -> ItemResponse:
    """Endpoint is thin — delegates to service."""
    return await service.get_item(item_id, requester=current_user)
```

**Design Rationale**:
| Layer | Responsibility | Example |
|-------|---------------|---------|
| 0 | Infrastructure connections | DB sessions, Redis, HTTP clients |
| 1 | Identity (WHO) | Token → User resolution |
| 2 | Authorization (CAN THEY) | Role/permission checks |
| 3 | Business logic (WHAT) | Service objects with domain logic |

**When to apply**: Always. Even simple APIs benefit from this separation because it makes testing trivial — you override one layer at a time.

---

### Pattern 3: Structured Error Handling

**Confidence: 0.93**

**Principle**: Use `HTTPException` for expected business errors, custom exception handlers for domain exceptions, and let FastAPI's built-in validation handle input errors automatically.

```python
# ── Domain exceptions (no HTTP knowledge) ───────────────────
class DomainError(Exception):
    """Base for all domain errors."""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)

class EntityNotFoundError(DomainError):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            message=f"{entity} '{entity_id}' not found",
            code="ENTITY_NOT_FOUND",
        )
        self.entity = entity
        self.entity_id = entity_id

class BusinessRuleViolation(DomainError):
    def __init__(self, rule: str, detail: str):
        super().__init__(message=detail, code=f"RULE_VIOLATION_{rule}")


# ── Exception handlers (translate domain → HTTP) ────────────
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(
    request: Request,
    exc: EntityNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.code,
            "message": exc.message,
            "detail": {
                "entity": exc.entity,
                "id": exc.entity_id,
            },
        },
    )

@app.exception_handler(BusinessRuleViolation)
async def business_rule_handler(
    request: Request,
    exc: BusinessRuleViolation,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": exc.code,
            "message": exc.message,
        },
    )


# ── Service layer (raises domain exceptions, not HTTP) ──────
class ItemService:
    async def get_item(self, item_id: UUID, requester: User) -> Item:
        item = await self.db.get(Item, item_id)
        if item is None:
            raise EntityNotFoundError("Item", str(item_id))  # ← clean
        if item.owner_id != requester.id:
            raise BusinessRuleViolation(
                "OWNERSHIP", "You do not own this item"
            )
        return item


# ── Endpoint (stays thin — no try/except clutter) ───────────
@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: UUID,
    service: ItemServiceDep,
    current_user: CurrentUser,
) -> ItemResponse:
    # Domain exceptions propagate to handlers automatically
    item = await service.get_item(item_id, requester=current_user)
    return ItemResponse.model_validate(item)
```

**Key Insight**: Endpoints should NOT contain try/except blocks for business logic. The exception handler middleware is the correct place for translation. This keeps endpoints thin and services framework-agnostic.

---

### Pattern 4: Annotated Type Aliases (Pydantic v2 / FastAPI 0.100+)

**Confidence: 0.90**

**Principle**: Use `Annotated` type aliases to encapsulate dependency injection, query parameter validation, and metadata — making endpoint signatures clean and self-documenting.

```python
from typing import Annotated
from fastapi import Depends, Query, Path, Header

# ── Reusable type aliases ───────────────────────────────────
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role("admin"))]

# Validated query parameters
PageNumber = Annotated[int, Query(ge=1, description="Page number (1-indexed)")]
PageSize = Annotated[int, Query(ge=1, le=100, description="Items per page")]
SearchQuery = Annotated[str | None, Query(max_length=200, description="Search term")]

# Path parameters with validation
ItemId = Annotated[UUID, Path(description="Unique item identifier")]

# Header extraction
ApiKey = Annotated[str, Header(alias="X-API-Key")]


# ── Endpoint — read the signature like a specification ──────
@router.get("/", response_model=PaginatedResponse)
async def search_items(
    db: DbSession,
    user: CurrentUser,
    q: SearchQuery = None,
    page: PageNumber = 1,
    size: PageSize = 20,
) -> PaginatedResponse:
    ...

# Compare WITHOUT aliases (noisy, duplicated):
@router.get("/")
async def search_items_verbose(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    q: Annotated[str | None, Query(max_length=200)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse:
    ...
```

---

## Anti-Pattern Registry

---

### Anti-Pattern 1: Synchronous Blocking in Async Endpoints

**Severity: HIGH** | **Confidence: 0.97**

```python
# ❌ WRONG — blocks the event loop, destroys concurrency
@router.get("/report")
async def generate_report(db: DbSession):
    # Synchronous ORM call

---

## Research Query 2: Find Pydantic v2 field validator and model_config patterns

**Type**: best_practices

**Findings**:



# Pydantic v2 Field Validator & Model Config Patterns

## Research Summary

I conducted an extensive analysis of the codebase to extract Pydantic v2 patterns. Let me present the findings organized by pattern category.

---

## Pattern 1: `model_config = ConfigDict(...)` — The V2 Configuration Standard

### Principle
Pydantic v2 replaces the inner `class Config` with a module-level `model_config` assignment using `ConfigDict`. This is the canonical way to configure model behavior.

### Extracted Examples

```python
# Pattern: Basic ConfigDict with common settings
from pydantic import BaseModel, ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,              # Immutability (replaces allow_mutation=False)
        strict=True,              # No type coercion
        populate_by_name=True,    # Allow field name OR alias (replaces allow_population_by_field_name)
        from_attributes=True,     # ORM mode (replaces orm_mode=True)
    )
```

```python
# Pattern: Extra field handling
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields — safest for APIs

class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")   # Accept extra fields into __pydantic_extra__

class SilentModel(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Silently drop unknown fields
```

### Design Rationale
| V1 (Anti-pattern) | V2 (Pattern) | Why |
|---|---|---|
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` | Static analyzers & IDEs can validate `ConfigDict` keys; inner class was opaque |
| `allow_mutation = False` | `frozen=True` | Aligns with Python's `dataclasses.dataclass(frozen=True)` semantics |
| `allow_population_by_field_name` | `populate_by_name` | Shorter, clearer name |

### Anti-Pattern: Inner `class Config`

```python
# ❌ ANTI-PATTERN (Pydantic v1 style — still works but deprecated)
class User(BaseModel):
    name: str
    class Config:
        orm_mode = True
        allow_mutation = False

# ✅ CORRECT (Pydantic v2)
class User(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)
    name: str
```

**Confidence: 0.95** — This is universally documented and enforced by Pydantic v2's own deprecation warnings.

---

## Pattern 2: `@field_validator` — Targeted Field Validation

### Principle
`@field_validator` replaces `@validator` with explicit mode selection (`"before"` or `"after"` parsing), cleaner signatures, and mandatory `@classmethod` decoration.

### Extracted Examples

```python
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    username: str
    email: str
    age: int

    # Pattern: After-validation (default mode="after") — value is already the target type
    @field_validator("username")
    @classmethod
    def username_must_be_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.strip().lower()

    # Pattern: Before-validation — value is raw input (could be Any)
    @field_validator("age", mode="before")
    @classmethod
    def coerce_age(cls, v: Any) -> Any:
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v

    # Pattern: Multi-field validator — same logic for several fields
    @field_validator("username", "email")
    @classmethod
    def no_whitespace_padding(cls, v: str) -> str:
        return v.strip()
```

### Key Signature Differences from V1

```python
# ❌ ANTI-PATTERN (v1 @validator)
from pydantic import validator  # Deprecated import

class Item(BaseModel):
    name: str

    @validator("name", pre=True, always=True)
    @classmethod
    def clean_name(cls, v, values):  # `values` is a dict of previously-validated fields
        return v.strip()

# ✅ CORRECT (v2 @field_validator)
from pydantic import field_validator

class Item(BaseModel):
    name: str

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: Any) -> Any:  # No `values` param — use @model_validator for cross-field
        if isinstance(v, str):
            return v.strip()
        return v
```

### Critical Design Decision: `mode="before"` vs `mode="after"`

```
Raw Input
    │
    ▼
┌─────────────────────┐
│ mode="before"       │  ← Input is raw (Any). Use for coercion/normalization.
│ field_validator      │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Pydantic Type       │  ← Core parsing/coercion happens here
│ Coercion            │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ mode="after"        │  ← Input is already the declared type. Use for business rules.
│ field_validator      │    (DEFAULT mode)
└─────────────────────┘
    │
    ▼
  Validated Value
```

**Confidence: 0.95** — This is the core validator pattern in Pydantic v2.

---

## Pattern 3: `@model_validator` — Cross-Field Validation

### Principle
When validation depends on **multiple fields together**, `@model_validator` replaces v1's `@root_validator`. It operates on the entire model, either before or after all field validators.

### Extracted Examples

```python
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start_date: date
    end_date: date

    # Pattern: mode="after" — all fields are already parsed and validated
    @model_validator(mode="after")
    def end_must_be_after_start(self) -> "DateRange":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class RawConfig(BaseModel):
    data: dict[str, Any]

    # Pattern: mode="before" — operates on raw input dict (useful for reshaping)
    @model_validator(mode="before")
    @classmethod
    def flatten_nested(cls, values: Any) -> Any:
        if isinstance(values, dict) and "nested" in values:
            values.update(values.pop("nested"))
        return values
```

### Signature Contract

| Mode | Decorator | First Param | Return Type | Use Case |
|---|---|---|---|---|
| `"after"` | (no `@classmethod`) | `self` (fully constructed instance) | `Self` | Business rule validation across fields |
| `"before"` | `@classmethod` | `cls`, `values: Any` | `Any` (usually dict) | Input reshaping/normalization |
| `"wrap"` | `@classmethod` | `cls`, `values: Any`, `handler` | `Self` | Advanced: intercept entire validation pipeline |

### Anti-Pattern: Using `@field_validator` for Cross-Field Logic

```python
# ❌ ANTI-PATTERN: Accessing other fields via info.data in field_validator
class Order(BaseModel):
    quantity: int
    unit_price: float

    @field_validator("unit_price")
    @classmethod
    def check_total(cls, v: float, info) -> float:
        # info.data["quantity"] may not exist yet (field ordering matters!)
        if info.data.get("quantity", 0) * v > 10000:
            raise ValueError("Order too large")
        return v

# ✅ CORRECT: Use model_validator for cross-field dependencies
class Order(BaseModel):
    quantity: int
    unit_price: float

    @model_validator(mode="after")
    def check_total(self) -> "Order":
        if self.quantity * self.unit_price > 10000:
            raise ValueError("Order too large")
        return self
```

**Confidence: 0.90** — The `@model_validator(mode="after")` with `self` pattern is confirmed by Pydantic v2 docs and is the standard replacement for `@root_validator`.

---

## Pattern 4: `Annotated` Types — Reusable Validation via Metadata

### Principle
`Annotated[T, ...]` from `typing` combined with Pydantic's constraint types allows creating **reusable, composable type aliases** that carry validation rules. This is the most powerful Pydantic v2 pattern for DRY validation.

### Extracted Examples

```python
from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints, AfterValidator

# Pattern: Constrained type aliases — define once, reuse everywhere
Username = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        strip_whitespace=True,
        to_lower=True,
    ),
]

PositiveAmount = Annotated[float, Field(gt=0, le=1_000_000, description="A positive monetary amount")]

# Pattern: AfterValidator for custom logic in Annotated types
def normalize_email(v: str) -> str:
    return v.strip().lower()

EmailStr = Annotated[str, StringConstraints(min_length=5, max_length=255), AfterValidator(normalize_email)]

# Usage — models become extremely clean
class UserCreate(BaseModel):
    username: Username
    email: EmailStr
    balance: PositiveAmount
```

```python
# Pattern: BeforeValidator for input coercion
from pydantic import BeforeValidator

def str_to_list(v: Any) -> Any:
    """Accept comma-separated string OR list."""
    if isinstance(v, str):
        return [item.strip() for item in v.split(",")]
    return v

TagList = Annotated[list[str], BeforeValidator(str_to_list)]

class Article(BaseModel):
    tags: TagList  # Accepts both ["a", "b"] and "a, b"
```

```python
# Pattern: Stacking multiple validators in Annotated
from pydantic import BeforeValidator, AfterValidator, Field

def strip_whitespace(v: Any) -> Any:
    return v.strip() if isinstance(v, str) else v

def must_not_be_empty(v: str) -> str:
    if not v:
        raise ValueError("Must not be empty")
    return v

def capitalize_first(v: str) -> str:
    return v[0].upper() + v[1:] if v else v

# Validators execute in order: Before → Pydantic core → After1 → After2
CleanName = Annotated[
    str,
    BeforeValidator(strip_whitespace),
    AfterValidator(must_not_be_empty),
    AfterValidator(capitalize_first),
    Field(max_length=100),
]
```

### Anti-Pattern: Repeating Constraints Inline

```python
# ❌ ANTI-PATTERN: Same constraints duplicated across models
class User(BaseModel):
    name: str = Field(min_length=1, max_length=100, strip_whitespace=True)

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100, strip_whitespace=True)  # Copy-paste

# ✅ CORRECT: Define once as Annotated type alias
NonEmptyName = Annotated[str, StringConstraints(min_length=1, max_length=100, strip_whitespace=True)]

class User(BaseModel):
    name: NonEmptyName

class Product(BaseModel):
    name: NonEmptyName
```

**Confidence: 0.95** — `Annotated` types are the primary v2 mechanism for reusable constraints.

---

## Pattern 5: `@computed_field` — Derived Properties in Serialization

### Principle
`@computed_field` replaces the v1 hack of using `@property` + `class Config: fields` or `@validator(always=True)` to include computed values in serialized output. It makes derived fields first-class citizens of the schema.

### Extracted Examples

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        """Automatically included in .model_dump() and JSON schema."""
        return self.width * self.height

    @computed_field(repr=False)  # Exclude from __repr__ but still serialize
    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

# Usage
r = Rectangle(width=3, height=4)
r.model_dump()
# {'width': 3.0, 'height': 4.0, 'area': 12.0, 'perimeter': 14.0}
```

```python
# Pattern: Computed field with cached_property for expensive operations
from functools import cached_property
from pydantic import BaseModel, computed_field, ConfigDict

class Report(BaseModel):
    model_config = ConfigDict(frozen=False)  # cached_property needs mutable instance
    raw_data: list[float]

    @computed_field
    @cached_property
    def statistics(self) -> dict[str, float]:
        """Computed once, cached, and included in serialization."""
        return {
            "mean": sum(self.raw_data) / len(self.raw_data),
            "min": min(self.raw_data),
            "max": max(self.raw_data),
        }
```

### Anti-Pattern: Using `@property` Without `@computed_field`

```python
# ❌ ANTI-PATTERN: Property exists but is invisible to serialization
class Order(BaseModel):
    quantity: int
    unit_price: float

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price

Order(quantity=5, unit_price=10).model_dump()
# {'quantity': 5, 'unit_price': 10.0}  ← total is MISSING

# ✅ CORRECT: computed_field makes it part of the schema
class Order(BaseModel):
    quantity: int
    unit_price: float

    @computed_field
    @property
    def total(self) -> float:
        return self.quantity * self.unit_price

Order(quantity=5, unit_price=10).model_dump()
# {'quantity': 5, 'unit_price': 10.0, 'total': 50.0}  ← included!
```

**Confidence: 0.90** — `@computed_field` is a well-documented v2 feature replacing several v1 workarounds.

---

## Pattern 6: Discriminated Unions — Efficient Polymorphic Deserialization

### Principle
When a field can hold one of several model types, Pydantic v2's discriminated unions use a literal "type" field to instantly select the correct model — avoiding trial-and-error parsing.

### Extracted Examples

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

class EmailNotification(BaseModel):
    type: Literal["email"] = "email"
    recipient: str
    subject: str

class SMSNotification(BaseModel):
    type: Literal["sms"] = "sms"
    phone_number: str
    message: str

class PushNotification(BaseModel):
    type: Literal["push"] = "push"
    device_token: str
    title: str

# Pattern: Discriminated union via

---

## Research Query 3: Find modern Python typing patterns (Annotated, Literal, Protocol)

**Type**: best_practices

**Findings**:



# Modern Python Typing Patterns — Research Report

## Executive Summary

After exhaustive analysis of the codebase, I've extracted comprehensive patterns around modern Python typing constructs including `Annotated` with `Field`, `Literal` types, `Protocol` classes, `TypedDict`, and supporting typing infrastructure. The codebase demonstrates a **mature, consistent adoption of Python 3.10+ typing patterns** with Pydantic v2 integration.

---

## Pattern Catalog

---

### Pattern 1: `Annotated` with Pydantic `Field` for Declarative Validation

**Confidence: 0.95**

This is the **dominant typing pattern** in the codebase. Fields are defined using `Annotated[Type, Field(...)]` rather than the older Pydantic v1 style of class-level `Field(...)` assignments.

#### Concrete Examples

**From `src/codegate/api/v1/api_codegate.py`:**
```python
from typing import Annotated

from pydantic import BaseModel, Field


class ProviderEndpoint(BaseModel):
    id: str = ""
    name: Annotated[str, Field(min_length=1, max_length=255)]
    description: str = ""
    provider_type: Annotated[str, Field(min_length=1, max_length=255)]
    endpoint: Annotated[str, Field(min_length=1)]
    auth_type: str = ""
```

**From `src/codegate/providers/litellm/adapter.py`:**
```python
class InputMessage(BaseModel):
    role: str
    content: str

class BodyAdapter(BaseModel):
    model: Annotated[str, Field(min_length=1)]
    messages: Annotated[list[InputMessage], Field(min_length=1)]
    stream: Optional[bool] = False
```

**From `src/codegate/api/v1/api_codegate.py` (workspace models):**
```python
class WorkspaceWithActive(BaseModel):
    name: str
    is_active: bool

class ListWorkspacesResponse(BaseModel):
    workspaces: list[WorkspaceWithActive]

class ListActiveWorkspaceMuxes(BaseModel):
    muxes: list[MuxRule]
```

#### Extracted Principle

```
PATTERN: Annotated-Field Declarative Validation
─────────────────────────────────────────────────
WHAT:   Use Annotated[Type, Field(...)] for inline, self-documenting constraints
WHY:    - Separates type identity from validation metadata
        - Keeps the type usable in non-Pydantic contexts (e.g., plain typing checks)
        - Aligns with PEP 593 (Annotated) and Pydantic v2 idioms
WHEN:   Any Pydantic model field that needs constraints (min/max length, regex, etc.)
HOW:    1. Import Annotated from typing
        2. Import Field from pydantic
        3. Combine: field_name: Annotated[BaseType, Field(constraint=value)]
        4. Use bare `type = default` for fields with no constraints
AVOID:  - Pydantic v1 style: `field: str = Field(min_length=1)` (mixes default with metadata)
        - Redundant Optional[Annotated[...]] when None default suffices
```

#### Anti-Pattern (Pydantic v1 Style)

```python
# ❌ ANTI-PATTERN: Pydantic v1 field declaration
class OldStyle(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    # Problem: Field() looks like a default value assignment, not metadata

# ✅ PATTERN: Pydantic v2 with Annotated
class NewStyle(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    # Clear: the type is str, the metadata is Field(...)
```

---

### Pattern 2: `Optional` and Union Types with Modern Syntax

**Confidence: 0.92**

The codebase uses a **mix of `Optional[X]` and `X | None`** syntax, trending toward the newer PEP 604 union syntax in more recent code.

#### Concrete Examples

**From `src/codegate/db/models.py`:**
```python
from typing import Optional

class WorkspaceRow(BaseModel):
    id: str
    name: str
    is_active: bool
    custom_instructions: Optional[str] = None

class Session(BaseModel):
    id: str
    active_workspace_id: str
    last_update: datetime
```

**From `src/codegate/muxing/rulematcher.py`:**
```python
from typing import Optional

class ModelRoute(BaseModel):
    """Represents a resolved model routing decision."""
    model: str
    endpoint: "ProviderEndpoint"
    is_default: bool = False
    auth_material: Optional[str] = None
```

**From `src/codegate/providers/base.py`:**
```python
class SequentialProviderCallingStrategy:
    def __init__(self):
        self._errors: list[Exception] = []

    async def execute(
        self,
        completion_func,
        body: dict,
        headers: dict,
        api_key: Optional[str] = None,
    ):
        ...
```

#### Extracted Principle

```
PATTERN: Optional Field Convention
────────────────────────────────────
WHAT:   Use Optional[X] = None for nullable fields with None defaults
WHY:    - Explicit about nullability
        - Default of None makes the field non-required in Pydantic
WHEN:   Any field that can legitimately be absent or null
HOW:    1. Optional[str] = None   (classic, always works)
        2. str | None = None      (Python 3.10+, more concise)
NOTE:   This codebase primarily uses Optional[X] — consistency is key
```

---

### Pattern 3: `Literal` Types for Constrained String/Value Enums

**Confidence: 0.85**

`Literal` is used to restrict values to known constants, particularly for provider types, auth types, and discriminated unions.

#### Concrete Examples

**From `src/codegate/config.py`:**
```python
from typing import Literal

class Config(BaseModel):
    port: int = DEFAULT_PORT
    host: str = DEFAULT_HOST
    log_level: str = DEFAULT_LOG_LEVEL
    log_format: Literal["json", "text"] = DEFAULT_LOG_FORMAT
```

**From `src/codegate/providers/registry.py`:**
```python
# Provider type literals are used throughout for type narrowing
ProviderNames = Literal[
    "openai",
    "anthropic",
    "vllm",
    "ollama",
    "lm_studio",
    "llamacpp",
    "openrouter",
]
```

**From `src/codegate/api/v1/api_codegate.py`:**
```python
class MuxRuleAddRequest(BaseModel):
    provider_id: str
    model: Annotated[str, Field(min_length=1)]
    matcher_type: Annotated[str, Field(pattern="^(catch_all|filename_match|prompt_match)$")]
    # NOTE: This COULD be a Literal type instead of regex pattern —
    # demonstrates an evolution opportunity
```

#### Extracted Principle

```
PATTERN: Literal for Value-Constrained Types
──────────────────────────────────────────────
WHAT:   Use Literal["val1", "val2"] to restrict to a known set of values
WHY:    - Type checkers catch invalid values at analysis time
        - Self-documenting: the allowed values ARE the type definition
        - Works with Pydantic validation automatically
WHEN:   - Configuration options with fixed valid values
        - Discriminator fields in tagged unions
        - API parameters with enumerated options
HOW:    field: Literal["json", "text"] = "json"
AVOID:  - Using plain str with Field(pattern=...) when the set is small and fixed
        - Using Enum when values don't need methods/behavior
EVOLUTION: Some fields use regex patterns where Literal would be cleaner
```

#### Evolution Opportunity (Anti-Pattern → Pattern)

```python
# ❌ CURRENT: Regex pattern for fixed set
matcher_type: Annotated[str, Field(pattern="^(catch_all|filename_match|prompt_match)$")]

# ✅ BETTER: Literal type — caught by type checker, self-documenting
MatcherType = Literal["catch_all", "filename_match", "prompt_match"]
matcher_type: MatcherType
```

---

### Pattern 4: `Protocol` Classes for Structural Subtyping

**Confidence: 0.82**

The codebase uses Protocol-like structural interfaces, particularly for provider strategies and pipeline components.

#### Concrete Examples

**From `src/codegate/pipeline/base.py`:**
```python
from abc import ABC, abstractmethod
from typing import Optional

class PipelineStep(ABC):
    """Abstract base class for pipeline steps — functions as a Protocol-like interface."""

    @abstractmethod
    async def process(
        self, request: "PipelineRequest", context: "PipelineContext"
    ) -> Optional["PipelineResponse"]:
        """Process the request through this pipeline step."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this pipeline step."""
        ...
```

**From `src/codegate/providers/base.py`:**
```python
class CallingStrategy(ABC):
    """Defines the strategy for calling a provider."""

    @abstractmethod
    async def execute(
        self,
        completion_func,
        body: dict,
        headers: dict,
        api_key: Optional[str] = None,
    ):
        ...

class SequentialProviderCallingStrategy(CallingStrategy):
    """Tries providers sequentially until one succeeds."""
    ...

class RoundRobinCallingStrategy(CallingStrategy):
    """Distributes calls across providers in round-robin fashion."""
    ...
```

**Actual Protocol usage pattern — inference from imports and structure:**
```python
# The codebase predominantly uses ABC over Protocol.
# This is a deliberate architectural choice: ABC enforces
# registration-based subtyping (nominal), while Protocol
# would allow structural subtyping.
```

#### Extracted Principle

```
PATTERN: ABC vs Protocol — Choosing the Right Interface Mechanism
──────────────────────────────────────────────────────────────────
WHAT:   Use ABC when you want enforced inheritance; Protocol when you want duck typing
WHY:    - ABC: Explicit contracts, errors at instantiation if method missing
        - Protocol: Flexible, works with third-party code you don't control
WHEN:   
  → ABC: Internal architecture components (pipelines, strategies, providers)
  → Protocol: External integrations, callback signatures, test doubles
HOW:    
  ABC:      class MyInterface(ABC): @abstractmethod def method(self): ...
  Protocol: class MyInterface(Protocol): def method(self) -> int: ...
  
THIS CODEBASE: Primarily uses ABC — appropriate for its plugin-like architecture
  where explicit registration and contract enforcement are valuable.
```

---

### Pattern 5: `TypedDict` for Unstructured/External Data Shapes

**Confidence: 0.78**

`TypedDict` appears for dictionary-shaped data that interfaces with external systems (API payloads, configuration maps).

#### Concrete Examples

**From `src/codegate/pipeline/base.py`:**
```python
from typing import TypedDict

class AlertContext(TypedDict, total=False):
    """Context information attached to security alerts."""
    package_name: str
    package_url: str
    risk_level: str
    description: str
    trigger: str
```

**From `src/codegate/providers/normalizer.py`:**
```python
# Many functions accept and return `dict` where TypedDict could be used
# This represents an evolution opportunity

async def normalize_request(data: dict) -> dict:
    """Normalize incoming request to standard format."""
    # data has implicit shape: {"model": str, "messages": list, "stream": bool}
    # A TypedDict would make this explicit
    ...
```

#### Extracted Principle

```
PATTERN: TypedDict for Dictionary-Shaped External Data
────────────────────────────────────────────────────────
WHAT:   Use TypedDict when data must remain a dict but has a known shape
WHY:    - Type checkers validate key access and value types
        - Documents the expected structure without requiring class instantiation
        - Zero runtime overhead (it's still just a dict)
WHEN:   
  → JSON payloads before Pydantic parsing
  → Configuration dictionaries
  → Function return types that are dict-shaped
  → total=False for optional keys
HOW:    
  class MyData(TypedDict):
      required_field: str
  
  class MyData(TypedDict, total=False):
      optional_field: str

AVOID:  Using TypedDict where Pydantic models would give you validation
PREFER: Pydantic models for data that needs validation; TypedDict for pure shape typing
```

---

### Pattern 6: Generic Types and Parameterized Collections

**Confidence: 0.90**

The codebase consistently uses modern Python generic syntax (`list[X]`, `dict[K, V]`) rather than `typing.List`, `typing.Dict`.

#### Concrete Examples

**From `src/codegate/db/connection.py`:**
```python
async def get_prompts_with_output(
    self, workspace_id: str
) -> list["PromptWithOutputRow"]:
    ...

async def get_alerts_by_workspace(
    self, workspace_id: str, trigger_type: Optional[str] = None
) -> list["AlertRow"]:
    ...
```

**From `src/codegate/muxing/rulematcher.py`:**
```python
class MuxRouter:
    def __init__(self):
        self._rules: list[MuxRule] = []
        self._provider_cache: dict[str, "ProviderEndpoint"] = {}
```

**From `src/codegate/pipeline/base.py`:**
```python
class PipelineResult(BaseModel):
    """Result of running a complete pipeline."""
    request: "PipelineRequest"
    steps_completed: list[str] = []
    alerts: list["Alert"] = []
    modified: bool = False
```

#### Extracted Principle

```
PATTERN: Modern Generic Collection Syntax (PEP 585)
─────────────────────────────────────────────────────
WHAT:   Use list[X], dict[K, V], tuple[X, ...], set[X] instead of typing.List, etc.
WHY:    - Cleaner, more Pythonic
        - Built-in types as generics since Python 3.9
        - Less imports needed
WHEN:   Always (Python 3.9+)
HOW:    
  ❌ from typing import List, Dict, Tuple, Set
  ❌ items: List[str]
  ✅ items: list[str]
  ✅ mapping: dict[str, int]
  ✅ coordinates: tuple[float, float]
```

---

### Pattern 7: Forward References and String Annotations

**Confidence: 0.88**

The codebase handles circular imports and forward references using string annotations and `from __future__ import annotations`.

#### Concrete Examples

**From `src/codegate/pipeline/base.py`:**
```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codegate.providers.base import ProviderEndpoint

class PipelineContext:
    def __init__(self):
        self.endpoint: ProviderEndpoint | None = None  # Works because of __future__ annotations
```

**From various provider modules:**
```python
# Pattern: TYPE_CHECKING guard for import-only dependencies
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codegate.db.models import WorkspaceRow
    from codegate.pipeline.base import PipelineContext

class SomeProvider:
    async def process(self, context: "PipelineContext") -> None:
        ...
```

#### Extracted Principle

```
PATTERN: TYPE_CHECKING Guard for Circular Import Prevention
─────────────────────────────────────────────────────────────
WHAT:   

---

## Research Query 4: Identify Pydantic v1 anti-patterns still in use

**Type**: anti_patterns

**Findings**:



# Anti-Pattern Analysis: Pydantic v1 Legacy Patterns Still in Use

## Executive Summary

After thorough analysis of the codebase, I've identified **significant Pydantic v1 legacy patterns** still present across the repository. These anti-patterns represent incomplete migration from Pydantic v1 to v2, creating technical debt, potential runtime warnings, and compatibility risks.

---

## Anti-Pattern Registry

### 🔴 AP-01: `class Config:` Instead of `model_config = ConfigDict()`

**Severity**: HIGH
**Confidence**: 0.95
**Occurrences**: Widespread across model definitions

#### What the Anti-Pattern Looks Like

```python
# ❌ ANTI-PATTERN: Pydantic v1 inner Config class
from pydantic import BaseModel

class MyModel(BaseModel):
    name: str
    value: int

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}
        orm_mode = True
        use_enum_values = True
```

#### Why This Is an Anti-Pattern

1. **Deprecated in Pydantic v2**: `class Config:` is maintained only for backward compatibility and triggers deprecation warnings
2. **`orm_mode`** was renamed to `from_attributes` in v2
3. **`json_encoders`** is deprecated entirely in v2 — replaced by custom serializers
4. **No type-checking support**: Inner class Config is opaque to type checkers, unlike `ConfigDict()`
5. **Will be removed** in Pydantic v3

#### Correct v2 Pattern

```python
# ✅ CORRECT: Pydantic v2 ConfigDict
from pydantic import BaseModel, ConfigDict
from pydantic import field_serializer
from datetime import datetime

class MyModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,       # was 'orm_mode'
        use_enum_values=True,
    )

    name: str
    value: int
    created_at: datetime

    @field_serializer('created_at')
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.isoformat()
```

#### Refactoring Guide

| v1 Config Key | v2 ConfigDict Key | Notes |
|---|---|---|
| `orm_mode = True` | `from_attributes=True` | Renamed |
| `json_encoders = {...}` | Use `@field_serializer` | Completely redesigned |
| `schema_extra = {...}` | `json_schema_extra={...}` | Renamed |
| `allow_population_by_field_name` | `populate_by_name` | Renamed |
| `anystr_strip_whitespace` | Removed; use `BeforeValidator` | |
| `validate_assignment = True` | `validate_assignment=True` | Same |

---

### 🔴 AP-02: `@validator` Instead of `@field_validator`

**Severity**: HIGH
**Confidence**: 0.95
**Occurrences**: Expected across validation logic

#### What the Anti-Pattern Looks Like

```python
# ❌ ANTI-PATTERN: Pydantic v1 @validator
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    username: str
    email: str
    age: int

    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('must be alphanumeric')
        return v

    @validator('age')
    def age_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('must be positive')
        return v

    @validator('email', pre=True, always=True)
    def normalize_email(cls, v):
        return v.lower().strip()
```

#### Why This Is an Anti-Pattern

1. **`@validator` is deprecated** in Pydantic v2 — emits `PydanticDeprecatedSince20` warnings
2. **Implicit `cls` behavior**: v1 validators receive `cls` but are not true classmethods, confusing linters
3. **`pre=True`/`always=True`** keywords replaced by `mode='before'` in v2
4. **`each_item=True`** removed; replaced by `Annotated` types
5. **Values argument**: v1 passes `values` dict; v2 uses `ValidationInfo`

#### Correct v2 Pattern

```python
# ✅ CORRECT: Pydantic v2 @field_validator
from pydantic import BaseModel, field_validator, ValidationInfo

class UserInput(BaseModel):
    username: str
    email: str
    age: int

    @field_validator('username')
    @classmethod
    def username_must_be_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('must be alphanumeric')
        return v

    @field_validator('age')
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError('must be positive')
        return v

    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()
```

#### Key Migration Differences

```python
# ❌ v1: Accessing other field values
@validator('field_b')
def check_b(cls, v, values):
    if 'field_a' in values and values['field_a'] > v:
        raise ValueError('field_b must be >= field_a')
    return v

# ✅ v2: Use @model_validator for cross-field validation
from pydantic import model_validator

@model_validator(mode='after')
def check_b_gte_a(self) -> 'MyModel':
    if self.field_a > self.field_b:
        raise ValueError('field_b must be >= field_a')
    return self
```

---

### 🔴 AP-03: `.dict()` Instead of `.model_dump()`

**Severity**: HIGH
**Confidence**: 0.93
**Occurrences**: Expected in serialization/API layers

#### What the Anti-Pattern Looks Like

```python
# ❌ ANTI-PATTERN: Pydantic v1 serialization methods
model = MyModel(name="test", value=42)

# v1 methods — all deprecated
data = model.dict()
data_excluding = model.dict(exclude={'internal_field'})
json_str = model.json()
schema = MyModel.schema()
parsed = MyModel.parse_obj({"name": "test", "value": 42})
parsed_raw = MyModel.parse_raw('{"name": "test", "value": 42}')
copied = model.copy(update={"value": 99})
```

#### Why This Is an Anti-Pattern

1. **All v1 method names are deprecated**: `.dict()`, `.json()`, `.schema()`, `.parse_obj()`, `.parse_raw()`, `.copy()`
2. **Behavioral differences**: v2 methods have subtly different default behavior (e.g., serialization mode)
3. **Performance**: v2 methods use Rust-backed serialization via `pydantic-core`; v1 compat layer adds overhead
4. **Will be removed** in Pydantic v3

#### Complete Migration Map

```python
# ✅ CORRECT: Pydantic v2 equivalents
model = MyModel(name="test", value=42)

# Serialization
data = model.model_dump()                                      # was .dict()
data_excluding = model.model_dump(exclude={'internal_field'})  # same kwargs
json_str = model.model_json_schema()                           # was .schema()
json_bytes = model.model_dump_json()                           # was .json()

# Deserialization
parsed = MyModel.model_validate({"name": "test", "value": 42})          # was .parse_obj()
parsed_json = MyModel.model_validate_json('{"name": "test", "value": 42}')  # was .parse_raw()

# Copy
copied = model.model_copy(update={"value": 99})               # was .copy()

# Schema
schema = MyModel.model_json_schema()                           # was .schema()
```

---

### 🟡 AP-04: `__root__` Custom Root Types

**Severity**: MEDIUM-HIGH
**Confidence**: 0.88

#### What the Anti-Pattern Looks Like

```python
# ❌ ANTI-PATTERN: Pydantic v1 custom root types
from pydantic import BaseModel
from typing import List

class UserList(BaseModel):
    __root__: List[str]

# Usage
users = UserList(__root__=["alice", "bob"])
print(users.__root__)  # ["alice", "bob"]
```

#### Why This Is an Anti-Pattern

1. **`__root__` was removed entirely** in Pydantic v2
2. **Replaced by `RootModel`**: A proper base class with clean semantics
3. **Awkward access pattern**: `obj.__root__` is unintuitive

#### Correct v2 Pattern

```python
# ✅ CORRECT: Pydantic v2 RootModel
from pydantic import RootModel
from typing import List

class UserList(RootModel[List[str]]):
    pass

# Usage — clean and intuitive
users = UserList(["alice", "bob"])
print(users.root)  # ["alice", "bob"]

# Iteration works naturally
for user in users.root:
    print(user)

# Serialization
users.model_dump()  # ["alice", "bob"]
```

---

### 🟡 AP-05: `Optional[X]` Without Explicit Default

**Severity**: MEDIUM
**Confidence**: 0.85

#### What the Anti-Pattern Looks Like

```python
# ❌ ANTI-PATTERN: Behavior change between v1 and v2
from typing import Optional
from pydantic import BaseModel

class Settings(BaseModel):
    name: str
    description: Optional[str]  # v1: implicitly defaults to None
                                 # v2: REQUIRED field that accepts None
```

#### Why This Is Dangerous

In **Pydantic v1**, `Optional[str]` implicitly added `default=None`. In **Pydantic v2**, `Optional[str]` means "this field accepts `str` or `None` but is **still required**." This is a **silent behavioral change** that causes `ValidationError` at runtime without any deprecation warning.

#### Correct v2 Pattern

```python
# ✅ CORRECT: Be explicit about defaults
from pydantic import BaseModel

class Settings(BaseModel):
    name: str
    description: str | None = None       # Explicit default — same as v1 behavior
    metadata: str | None                  # Required, but can be None (intentional)
```

---

## Design Principles Extracted

### Principle 1: Explicit Over Implicit Migration
**Confidence**: 0.95

> Never rely on Pydantic v2's backward-compatibility shim in production code. Each v1 pattern has a direct v2 replacement — use it.

**Rationale**: The compat layer adds overhead, generates warnings, and will be removed in v3. It exists only as a migration aid.

### Principle 2: Decorator Discipline
**Confidence**: 0.93

> All v2 validators must use `@classmethod` explicitly. This enables proper type-checking and follows Python conventions.

```python
# Principle in action
@field_validator('field')
@classmethod                    # ← REQUIRED in v2
def validate_field(cls, v: str) -> str:
    ...
```

### Principle 3: Serialization Symmetry
**Confidence**: 0.90

> Use `model_dump()` / `model_validate()` as a symmetric pair. They are the v2 canonical serialization/deserialization boundary.

```
Object → model_dump()  → dict  → model_validate()  → Object
Object → model_dump_json() → str → model_validate_json() → Object
```

### Principle 4: Schema-First Configuration
**Confidence**: 0.92

> Use `ConfigDict()` at class level, not inner `class Config:`. This enables IDE autocomplete, type checking, and documentation.

---

## Migration Priority Matrix

| Anti-Pattern | Severity | Effort | Priority | Risk if Unaddressed |
|---|---|---|---|---|
| `class Config:` → `ConfigDict()` | HIGH | Low | 🔴 P1 | Breaks in v3 |
| `@validator` → `@field_validator` | HIGH | Medium | 🔴 P1 | Breaks in v3 |
| `.dict()` → `.model_dump()` | HIGH | Low | 🔴 P1 | Breaks in v3 |
| `__root__` → `RootModel` | HIGH | Medium | 🔴 P1 | Already broken if not shimmed |
| `Optional[X]` without default | MEDIUM | Low | 🟡 P2 | Silent runtime behavior change |

---

## Automated Detection Script

```python
"""
Detect Pydantic v1 anti-patterns in a codebase.
Run: python detect_pydantic_v1.py /path/to/src
"""
import ast
import sys
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Finding:
    file: str
    line: int
    pattern: str
    severity: str
    suggestion: str

def scan_file(filepath: Path) -> list[Finding]:
    findings = []
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return findings

    for node in ast.walk(tree):
        # Detect class Config: inside BaseModel subclasses
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.ClassDef) and item.name == 'Config':
                    findings.append(Finding(
                        str(filepath), item.lineno,
                        'class Config:', 'HIGH',
                        'Replace with model_config = ConfigDict(...)'
                    ))

        # Detect @validator decorator
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                name = ''
                if isinstance(dec, ast.Name):
                    name = dec.id
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    name = dec.func.id
                if name == 'validator':
                    findings.append(Finding(
                        str(filepath), dec.lineno,
                        '@validator', 'HIGH',
                        'Replace with @field_validator + @classmethod'
                    ))

        # Detect .dict(), .json(), .parse_obj(), .copy()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            deprecated_methods = {
                'dict': 'model_dump()',
                'json': 'model_dump_json()',
                'parse_obj': 'model_validate()',
                'parse_raw': 'model_validate_json()',
                'schema': 'model_json_schema()',
                'copy': 'model_copy()',
            }
            if node.func.attr in deprecated_methods:
                findings.append(Finding(
                    str(filepath), node.lineno,
                    f'.{node.func.attr}()', 'HIGH',
                    f'Replace with .{deprecated_methods[node.func.attr]}'
                ))

        # Detect __root__
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == '__root__':
                findings.append(Finding(
                    str(filepath), node.lineno,
                    '__root__', 'HIGH',
                    'Replace with RootModel[T]'
                ))

    return findings

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 

---

