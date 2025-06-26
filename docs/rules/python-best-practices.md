# Python Best Practices for Modern Development (Python 3.11+)

## Table of Contents

1. [General Principles](#general-principles)
2. [Code Style and Formatting](#code-style-and-formatting)
3. [Type Hints and Static Analysis](#type-hints-and-static-analysis)
4. [Project Structure and Architecture](#project-structure-and-architecture)
5. [Error Handling and Validation](#error-handling-and-validation)
6. [Asynchronous Programming](#asynchronous-programming)
7. [Testing Best Practices](#testing-best-practices)
8. [Security Guidelines](#security-guidelines)
9. [Performance Optimization](#performance-optimization)
10. [Documentation Standards](#documentation-standards)
11. [Dependency Management](#dependency-management)
12. [Configuration Management](#configuration-management)

---

## General Principles

### 1. Follow PEP 8 and Modern Python Standards

- **Use Python 3.11+** features and syntax
- **Follow PEP 8** style guide religiously
- **Use pathlib** instead of os.path for file operations
- **Prefer f-strings** over .format() or % formatting
- **Use dataclasses** or Pydantic models for structured data

```python
# ✅ Good - Modern Python 3.11+ patterns
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    name: str
    email: str
    age: Optional[int] = None

def process_file(file_path: Path) -> str:
    content = file_path.read_text(encoding="utf-8")
    return f"Processed {len(content)} characters from {file_path.name}"

# ❌ Bad - Legacy patterns
import os

class User:
    def __init__(self, name, email, age=None):
        self.name = name
        self.email = email
        self.age = age

def process_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    return "Processed %d characters from %s" % (len(content), os.path.basename(file_path))
```

### 2. Write Self-Documenting Code

- **Use descriptive variable and function names**
- **Prefer composition over inheritance**
- **Keep functions small and focused** (single responsibility principle)
- **Use meaningful constants** instead of magic numbers

```python
# ✅ Good - Self-documenting
MAX_RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 30

async def fetch_user_profile(user_id: UUID) -> UserProfile:
    """Fetch user profile with retry logic and timeout."""
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            response = await http_client.get(
                f"/users/{user_id}",
                timeout=TIMEOUT_SECONDS
            )
            return UserProfile.model_validate(response.json())
        except TimeoutError:
            if attempt == MAX_RETRY_ATTEMPTS - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

# ❌ Bad - Magic numbers and unclear intent
async def fetch_user_profile(user_id):
    for i in range(3):
        try:
            response = await http_client.get(f"/users/{user_id}", timeout=30)
            return response.json()
        except:
            if i == 2:
                raise
            await asyncio.sleep(2 ** i)
```

---

## Code Style and Formatting

### 1. Use Automated Formatting Tools

**Primary Tool: Ruff** (combines linting and formatting)

```bash
# Install and configure ruff
uv add --dev ruff

# Format code
ruff format .

# Lint and auto-fix
ruff check --fix .
```

**pyproject.toml configuration:**

```toml
[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py

[tool.ruff.mccabe]
max-complexity = 10
```

### 2. Import Organization

**Use absolute imports and organize logically:**

```python
# ✅ Good - Organized imports
# Standard library
import asyncio
import logging
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

# Third-party
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
import httpx

# Local application
from src.core.config import settings
from src.core.exceptions import UserNotFound
from src.models.user import User
from src.services.auth import AuthService

# ❌ Bad - Unorganized imports
from fastapi import *
import asyncio, logging, httpx
from src.models.user import User
from typing import Any
from src.core.config import settings
```

### 3. Line Length and Code Organization

- **Maximum line length: 100 characters** (modern standard)
- **Use parentheses for multi-line expressions**
- **Break long argument lists logically**

```python
# ✅ Good - Readable multi-line formatting
user = await user_service.create_user(
    name=user_data.name,
    email=user_data.email,
    password_hash=auth_service.hash_password(user_data.password),
    roles=user_data.roles or ["user"],
    metadata={
        "created_by": current_user.id,
        "registration_source": "api",
    }
)

# Long conditions
if (
    user.is_active
    and user.has_permission("read_data")
    and not user.is_suspended
    and user.subscription_active
):
    return await data_service.fetch_user_data(user.id)
```

---

## Type Hints and Static Analysis

### 1. Comprehensive Type Annotations

**Use type hints for all public APIs and complex functions:**

```python
from typing import Any, Dict, List, Optional, Union, Protocol
from collections.abc import Sequence, Mapping
from dataclasses import dataclass

# ✅ Good - Comprehensive typing
@dataclass
class APIResponse[T]:
    """Generic API response wrapper."""
    data: T
    status: str
    message: Optional[str] = None
    errors: Optional[List[str]] = None

async def process_user_data(
    user_id: UUID,
    data: Dict[str, Any],
    *,
    validate: bool = True,
    timeout: Optional[int] = None
) -> APIResponse[User]:
    """Process user data with validation and timeout."""
    # Implementation here
    pass

# Protocol for dependency injection
class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        ...
    
    async def create(self, user_data: UserCreate) -> User:
        ...
```

### 2. Modern Type Hints (Python 3.11+)

**Use new union syntax and generic improvements:**

```python
# ✅ Good - Python 3.11+ syntax
def process_data(
    data: list[dict[str, Any]]  # New generic syntax
) -> str | None:  # Union with | operator
    if not data:
        return None
    return json.dumps(data)

# Generic type variables
from typing import TypeVar

T = TypeVar('T')

class Repository[T]:
    """Generic repository pattern."""
    
    def __init__(self, model_class: type[T]) -> None:
        self.model_class = model_class
    
    async def get_by_id(self, id: UUID) -> T | None:
        # Implementation
        pass

# ❌ Bad - Legacy typing syntax
from typing import Union, List, Dict, Optional

def process_data(
    data: List[Dict[str, Any]]
) -> Optional[str]:
    # ... implementation
```

### 3. Static Analysis Tools

**Configure mypy for strict type checking:**

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

---

## Project Structure and Architecture

### 1. Domain-Driven Design Structure

**Organize code by business domains:**

```
src/
├── __init__.py
├── main.py                 # Application entry point
├── core/                   # Shared core functionality
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── database.py        # Database setup
│   ├── exceptions.py      # Global exception classes
│   ├── middleware.py      # Custom middleware
│   └── security.py        # Security utilities
├── models/                 # Shared data models
│   ├── __init__.py
│   ├── base.py            # Base model classes
│   └── common.py          # Common model mixins
├── auth/                   # Authentication domain
│   ├── __init__.py
│   ├── router.py          # FastAPI routes
│   ├── service.py         # Business logic
│   ├── repository.py      # Data access layer
│   ├── models.py          # Domain models
│   ├── schemas.py         # Pydantic schemas
│   ├── dependencies.py    # FastAPI dependencies
│   ├── exceptions.py      # Domain-specific exceptions
│   └── utils.py           # Utility functions
├── users/                  # User management domain
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   ├── models.py
│   ├── schemas.py
│   ├── dependencies.py
│   ├── exceptions.py
│   └── utils.py
└── financial/              # Financial data domain
    ├── __init__.py
    ├── workflow.py         # Agno workflow
    ├── agents/            # Agno agents
    │   ├── __init__.py
    │   ├── router.py
    │   ├── extractor.py
    │   └── chat.py
    ├── tools/             # Custom tools
    │   ├── __init__.py
    │   └── fmp_client.py
    ├── schemas.py
    └── exceptions.py
```

### 2. Separation of Concerns

**Implement clean architecture layers:**

```python
# repository.py - Data Access Layer
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        pass
    
    @abstractmethod
    async def create(self, user: UserCreate) -> User:
        pass

class SQLUserRepository(UserRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def get_by_id(self, user_id: UUID) -> User | None:
        # Database implementation
        pass

# service.py - Business Logic Layer
class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository
    
    async def create_user(self, user_data: UserCreate) -> User:
        # Validate business rules
        if await self._email_exists(user_data.email):
            raise EmailAlreadyExistsError()
        
        # Apply business logic
        user = await self.repository.create(user_data)
        
        # Trigger side effects
        await self._send_welcome_email(user)
        
        return user
    
    async def _email_exists(self, email: str) -> bool:
        # Private helper method
        pass

# router.py - API Layer
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user."""
    user = await service.create_user(user_data)
    return UserResponse.model_validate(user)
```

### 3. Configuration Management

**Use Pydantic Settings for environment-aware configuration:**

```python
# core/config.py
from functools import lru_cache
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Application settings
    APP_NAME: str = "Financial Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    
    # API Keys
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key for Claude")
    OPENAI_API_KEY: str | None = Field(None, description="Optional OpenAI API key")
    FINANCIAL_MODELING_PREP_API_KEY: str = Field(..., description="FMP API key")
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT_SECONDS: int = 30

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Domain-specific configuration
# auth/config.py
from src.core.config import get_settings

class AuthConfig(BaseSettings):
    JWT_ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    
    @property
    def secret_key(self) -> str:
        return get_settings().SECRET_KEY

auth_config = AuthConfig()
```

---

## Error Handling and Validation

### 1. Custom Exception Hierarchy

**Create domain-specific exceptions:**

```python
# core/exceptions.py
class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

class ValidationError(AppException):
    """Validation error."""
    pass

class NotFoundError(AppException):
    """Resource not found error."""
    pass

class AuthenticationError(AppException):
    """Authentication error."""
    pass

# Domain-specific exceptions
# users/exceptions.py
from src.core.exceptions import NotFoundError, ValidationError

class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: UUID) -> None:
        super().__init__(
            f"User with ID {user_id} not found",
            error_code="USER_NOT_FOUND",
            details={"user_id": str(user_id)}
        )

class EmailAlreadyExistsError(ValidationError):
    def __init__(self, email: str) -> None:
        super().__init__(
            f"User with email {email} already exists",
            error_code="EMAIL_EXISTS",
            details={"email": email}
        )
```

### 2. Pydantic Validation

**Use comprehensive validation with custom validators:**

```python
from pydantic import BaseModel, Field, field_validator, model_validator
import re

STRONG_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]"
)

class UserCreate(BaseModel):
    """User creation schema with validation."""
    
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    age: int | None = Field(None, ge=13, le=120)
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", value):
            raise ValueError("Invalid email format")
        return value.lower()
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not STRONG_PASSWORD_PATTERN.match(value):
            raise ValueError(
                "Password must contain at least one lowercase letter, "
                "one uppercase letter, one digit, and one special character"
            )
        return value
    
    @model_validator(mode="after")
    def validate_model(self) -> "UserCreate":
        # Cross-field validation
        if self.age and self.age < 18 and "@business.com" in self.email:
            raise ValueError("Business email requires user to be 18+")
        return self

# ✅ Good - Proper validation error handling
@router.post("/users/")
async def create_user(user_data: UserCreate) -> UserResponse:
    try:
        user = await user_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details,
            }
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
```

### 3. Structured Logging

**Implement comprehensive logging:**

```python
import logging
import structlog
from typing import Any

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in services
class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        log = logger.bind(operation="create_user", email=user_data.email)
        
        try:
            log.info("Starting user creation")
            
            if await self._email_exists(user_data.email):
                log.warning("User creation failed: email already exists")
                raise EmailAlreadyExistsError(user_data.email)
            
            user = await self.repository.create(user_data)
            
            log.info(
                "User created successfully",
                user_id=user.id,
                created_at=user.created_at.isoformat(),
            )
            
            return user
            
        except Exception as e:
            log.error(
                "User creation failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise
```

---

## Asynchronous Programming

### 1. Async Best Practices

**Proper async/await usage:**

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# ✅ Good - Proper async patterns
class AsyncUserService:
    def __init__(self, db: AsyncSession, http_client: httpx.AsyncClient) -> None:
        self.db = db
        self.http_client = http_client
    
    async def get_user_with_profile(self, user_id: UUID) -> UserWithProfile:
        """Fetch user and external profile data concurrently."""
        # Concurrent execution
        user_task = self.get_user(user_id)
        profile_task = self.fetch_external_profile(user_id)
        
        user, profile = await asyncio.gather(user_task, profile_task)
        
        return UserWithProfile(user=user, profile=profile)
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Database transaction context manager."""
        async with self.db.begin():
            try:
                yield self.db
            except Exception:
                await self.db.rollback()
                raise
            else:
                await self.db.commit()
    
    async def bulk_create_users(
        self,
        users_data: list[UserCreate],
        *,
        batch_size: int = 100,
    ) -> list[User]:
        """Create users in batches to avoid overwhelming the database."""
        all_users = []
        
        for i in range(0, len(users_data), batch_size):
            batch = users_data[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self.create_user(user_data) for user_data in batch]
            batch_users = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for j, result in enumerate(batch_users):
                if isinstance(result, Exception):
                    logger.error(
                        "Failed to create user in batch",
                        batch_index=i + j,
                        error=str(result),
                    )
                else:
                    all_users.append(result)
        
        return all_users

# ❌ Bad - Blocking the event loop
async def bad_service():
    time.sleep(10)  # Blocks the entire event loop!
    return "done"

# ✅ Good - Non-blocking
async def good_service():
    await asyncio.sleep(10)  # Non-blocking sleep
    return "done"

# ✅ Good - Running sync code in thread pool
from starlette.concurrency import run_in_threadpool

async def process_with_sync_library(data: bytes) -> str:
    """Use sync library without blocking event loop."""
    # Run CPU-intensive or blocking operation in thread pool
    result = await run_in_threadpool(
        sync_processing_function,
        data,
        option1=True,
        option2="value",
    )
    return result
```

### 2. Resource Management

**Proper async resource management:**

```python
from contextlib import asynccontextmanager
import aiofiles

class FileProcessor:
    @asynccontextmanager
    async def open_file(self, file_path: Path) -> AsyncGenerator[aiofiles.threadpool.text.AsyncTextIOWrapper, None]:
        """Async file context manager."""
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            yield file
    
    async def process_large_file(self, file_path: Path) -> dict[str, int]:
        """Process large file line by line."""
        stats = {"lines": 0, "words": 0, "chars": 0}
        
        async with self.open_file(file_path) as file:
            async for line in file:
                stats["lines"] += 1
                stats["words"] += len(line.split())
                stats["chars"] += len(line)
                
                # Yield control periodically for large files
                if stats["lines"] % 1000 == 0:
                    await asyncio.sleep(0)  # Yield to event loop
        
        return stats

# HTTP client resource management
class APIClient:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self) -> "APIClient":
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=100),
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
    
    async def get(self, url: str) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        response = await self._client.get(url)
        response.raise_for_status()
        return response.json()

# Usage
async def fetch_multiple_apis():
    async with APIClient() as client:
        urls = ["https://api1.com/data", "https://api2.com/data"]
        tasks = [client.get(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results
```

---

## Testing Best Practices

### 1. Test Structure and Organization

**Organize tests to mirror source structure:**

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_main.py            # Application tests
├── unit/                   # Unit tests
│   ├── __init__.py
│   ├── auth/
│   │   ├── test_service.py
│   │   └── test_repository.py
│   └── users/
│       ├── test_service.py
│       └── test_repository.py
├── integration/            # Integration tests
│   ├── __init__.py
│   ├── test_auth_flow.py
│   └── test_user_creation.py
├── e2e/                   # End-to-end tests
│   ├── __init__.py
│   └── test_user_journey.py
└── fixtures/              # Test data
    ├── __init__.py
    ├── users.py
    └── responses.py
```

### 2. Comprehensive Test Fixtures

**Create reusable, well-structured fixtures:**

```python
# conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.core.database import get_db
from src.core.config import get_settings

@pytest.fixture(scope="session")
def settings():
    """Test settings."""
    return get_settings()

@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create async database engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        echo=False,
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncSession:
    """Create database session for testing."""
    async_session = sessionmaker(
        async_engine, 
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Create test client with database session override."""
    
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    
    app.dependency_overrides.clear()

# Test data factories
@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "SecurePass123!",
    }

@pytest.fixture
def mock_external_api(respx_mock):
    """Mock external API responses."""
    respx_mock.get("https://api.external.com/users/123").mock(
        return_value=httpx.Response(
            200,
            json={"id": 123, "name": "External User"},
        )
    )
    return respx_mock
```

### 3. Test Implementation Patterns

**Write clear, maintainable tests:**

```python
# test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from src.users.service import UserService
from src.users.exceptions import EmailAlreadyExistsError
from src.users.schemas import UserCreate

class TestUserService:
    """Test suite for UserService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock user repository."""
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_repository):
        """User service with mocked dependencies."""
        return UserService(repository=mock_repository)
    
    async def test_create_user_success(
        self,
        user_service: UserService,
        mock_repository: AsyncMock,
        user_data: dict[str, str],
    ):
        """Test successful user creation."""
        # Arrange
        user_create = UserCreate(**user_data)
        expected_user = User(id=uuid4(), **user_data)
        
        mock_repository.get_by_email.return_value = None
        mock_repository.create.return_value = expected_user
        
        # Act
        result = await user_service.create_user(user_create)
        
        # Assert
        assert result == expected_user
        mock_repository.get_by_email.assert_called_once_with(user_data["email"])
        mock_repository.create.assert_called_once_with(user_create)
    
    async def test_create_user_email_exists(
        self,
        user_service: UserService,
        mock_repository: AsyncMock,
        user_data: dict[str, str],
    ):
        """Test user creation with existing email."""
        # Arrange
        user_create = UserCreate(**user_data)
        existing_user = User(id=uuid4(), **user_data)
        
        mock_repository.get_by_email.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(EmailAlreadyExistsError) as exc_info:
            await user_service.create_user(user_create)
        
        assert exc_info.value.details["email"] == user_data["email"]
        mock_repository.get_by_email.assert_called_once_with(user_data["email"])
        mock_repository.create.assert_not_called()

# Integration test
@pytest.mark.asyncio
async def test_user_creation_flow(client: AsyncClient, user_data: dict[str, str]):
    """Test complete user creation flow."""
    # Create user
    response = await client.post("/users/", json=user_data)
    assert response.status_code == 201
    
    user_response = response.json()
    assert user_response["email"] == user_data["email"]
    assert "id" in user_response
    assert "password" not in user_response  # Security check
    
    # Verify user exists
    user_id = user_response["id"]
    response = await client.get(f"/users/{user_id}")
    assert response.status_code == 200
    
    # Verify duplicate email fails
    response = await client.post("/users/", json=user_data)
    assert response.status_code == 409
    assert "email" in response.json()["details"]

# Parametrized tests
@pytest.mark.parametrize(
    "email,expected_valid",
    [
        ("test@example.com", True),
        ("invalid-email", False),
        ("@example.com", False),
        ("test@", False),
        ("", False),
    ],
)
def test_email_validation(email: str, expected_valid: bool):
    """Test email validation logic."""
    if expected_valid:
        user = UserCreate(name="Test", email=email, password="SecurePass123!")
        assert user.email == email.lower()
    else:
        with pytest.raises(ValueError):
            UserCreate(name="Test", email=email, password="SecurePass123!")
```

---

## Security Guidelines

### 1. Input Validation and Sanitization

**Always validate and sanitize user inputs:**

```python
from pydantic import BaseModel, Field, field_validator
import bleach
import re

class SafeUserInput(BaseModel):
    """Safe user input with validation and sanitization."""
    
    username: str = Field(min_length=3, max_length=50)
    bio: str = Field(max_length=500)
    website: str | None = Field(None, max_length=200)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        # Only allow alphanumeric, underscore, and hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise ValueError("Username can only contain letters, numbers, underscore, and hyphen")
        
        # Prevent reserved usernames
        reserved = {"admin", "root", "api", "www", "mail"}
        if value.lower() in reserved:
            raise ValueError("Username is reserved")
        
        return value
    
    @field_validator("bio")
    @classmethod
    def sanitize_bio(cls, value: str) -> str:
        # Remove HTML tags and potentially harmful content
        allowed_tags = ["b", "i", "em", "strong"]
        return bleach.clean(value, tags=allowed_tags, strip=True)
    
    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None:
            return None
        
        # Ensure URL starts with https
        if not value.startswith(("https://", "http://")):
            value = f"https://{value}"
        
        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$", re.IGNORECASE
        )
        
        if not url_pattern.match(value):
            raise ValueError("Invalid URL format")
        
        return value
```

### 2. Authentication and Authorization

**Implement secure authentication patterns:**

```python
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Password security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    def hash_password(self, password: str) -> str:
        """Hash password securely."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {e}")

# FastAPI dependencies
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Get current authenticated user."""
    try:
        payload = auth_service.verify_token(token)
        user_id = UUID(payload.get("sub"))
        
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
    except (JWTError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user

# Permission-based authorization
from enum import Enum

class Permission(str, Enum):
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    ADMIN = "admin"

def require_permission(permission: Permission):
    """Dependency factory for permission-based authorization."""
    
    async def check_permission(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {permission} required",
            )
        return current_user
    
    return check_permission

# Usage in routes
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.DELETE_USERS)),
    user_service: UserService = Depends(get_user_service),
):
    """Delete a user (requires delete:users permission)."""
    await user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}
```

### 3. Secure Configuration

**Handle secrets and sensitive data properly:**

```python
from pathlib import Path
from cryptography.fernet import Fernet

class SecureConfig:
    """Secure configuration management."""
    
    def __init__(self) -> None:
        # Load encryption key from environment or file
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            key_file = Path(".secrets/encryption.key")
            if key_file.exists():
                key = key_file.read_text().strip()
            else:
                # Generate new key for development
                key = Fernet.generate_key().decode()
                key_file.parent.mkdir(exist_ok=True)
                key_file.write_text(key)
        
        self.fernet = Fernet(key.encode())
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt sensitive value."""
        return self.fernet.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive value."""
        return self.fernet.decrypt(encrypted_value.encode()).decode()

# Environment-specific settings
class SecureSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Database URL (automatically parsed and validated)
    DATABASE_URL: PostgresDsn
    
    # API keys (marked as sensitive)
    ANTHROPIC_API_KEY: str = Field(..., json_schema_extra={"format": "password"})
    OPENAI_API_KEY: str | None = Field(None, json_schema_extra={"format": "password"})
    
    # Security settings
    SECRET_KEY: str = Field(..., min_length=32)
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return value
    
    @field_validator("ALLOWED_HOSTS")
    @classmethod
    def validate_hosts(cls, value: list[str]) -> list[str]:
        # Validate each host format
        for host in value:
            if not re.match(r"^[a-zA-Z0-9.-]+$", host):
                raise ValueError(f"Invalid host format: {host}")
        return value
```

---

## Performance Optimization

### 1. Database Optimization

**Implement efficient database patterns:**

```python
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload

class OptimizedUserRepository:
    """Repository with performance optimizations."""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def get_users_with_posts(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        include_inactive: bool = False,
    ) -> list[User]:
        """Get users with their posts in a single query."""
        query = (
            select(User)
            .options(
                # Eager load posts to avoid N+1 queries
                selectinload(User.posts).selectinload(Post.tags),
                # Join load user profile
                joinedload(User.profile),
            )
            .limit(limit)
            .offset(offset)
            .order_by(User.created_at.desc())
        )
        
        if not include_inactive:
            query = query.where(User.is_active == True)
        
        result = await self.db.execute(query)
        return result.scalars().unique().all()
    
    async def get_user_stats(self) -> dict[str, int]:
        """Get user statistics efficiently."""
        query = select(
            func.count(User.id).label("total_users"),
            func.count(User.id).filter(User.is_active == True).label("active_users"),
            func.count(User.id).filter(
                User.created_at >= datetime.utcnow() - timedelta(days=30)
            ).label("new_users_this_month"),
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        return {
            "total_users": row.total_users,
            "active_users": row.active_users,
            "new_users_this_month": row.new_users_this_month,
        }
    
    async def bulk_update_users(
        self,
        updates: list[dict[str, Any]],
        *,
        batch_size: int = 1000,
    ) -> int:
        """Efficiently update multiple users."""
        updated_count = 0
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            # Use bulk update for better performance
            await self.db.execute(
                update(User),
                batch,
            )
            
            updated_count += len(batch)
        
        await self.db.commit()
        return updated_count
```

### 2. Caching Strategies

**Implement intelligent caching:**

```python
import redis.asyncio as redis
from functools import wraps
import pickle
import hashlib
from typing import Callable, Any

class CacheService:
    """Redis-based caching service."""
    
    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Any:
        """Get value from cache."""
        try:
            data = await self.redis.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set value in cache."""
        try:
            serialized = pickle.dumps(value)
            await self.redis.setex(
                key,
                ttl or self.default_ttl,
                serialized,
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
    
    def cached(
        self,
        prefix: str,
        ttl: int | None = None,
        skip_cache: Callable[..., bool] | None = None,
    ):
        """Decorator for caching function results."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Check if we should skip cache
                if skip_cache and skip_cache(*args, **kwargs):
                    return await func(*args, **kwargs)
                
                # Generate cache key
                cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Call function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator

# Usage example
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        cache: CacheService,
    ) -> None:
        self.repository = repository
        self.cache = cache
    
    @cache.cached("user_profile", ttl=1800)  # 30 minutes
    async def get_user_profile(self, user_id: UUID) -> UserProfile:
        """Get user profile with caching."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Expensive profile computation
        profile_data = await self._compute_profile_data(user)
        
        return UserProfile(**profile_data)
    
    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """Update user and invalidate cache."""
        user = await self.repository.update(user_id, data)
        
        # Invalidate related caches
        cache_key = self.cache._generate_key("user_profile", user_id)
        await self.cache.delete(cache_key)
        
        return user
```

### 3. Async Performance Patterns

**Optimize async operations:**

```python
import asyncio
from asyncio import Semaphore
from typing import TypeVar, Callable
import time

T = TypeVar('T')

class PerformanceOptimizer:
    """Utilities for async performance optimization."""
    
    def __init__(self, max_concurrent: int = 10) -> None:
        self.semaphore = Semaphore(max_concurrent)
    
    async def run_with_concurrency_limit(
        self,
        tasks: list[Callable[[], Any]],
    ) -> list[Any]:
        """Run tasks with concurrency limiting."""
        async def limited_task(task):
            async with self.semaphore:
                return await task()
        
        return await asyncio.gather(*[limited_task(task) for task in tasks])
    
    async def batch_process(
        self,
        items: list[T],
        processor: Callable[[T], Any],
        batch_size: int = 100,
        delay_between_batches: float = 0.1,
    ) -> list[Any]:
        """Process items in batches with delays."""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [processor(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            results.extend(batch_results)
            
            # Delay between batches to avoid overwhelming resources
            if i + batch_size < len(items):
                await asyncio.sleep(delay_between_batches)
        
        return results
    
    async def timeout_wrapper(
        self,
        coro: Any,
        timeout: float,
        default: Any = None,
    ) -> Any:
        """Wrap coroutine with timeout and default value."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout}s")
            return default

# Performance monitoring decorator
def monitor_performance(func_name: str | None = None):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                
                logger.info(
                    "Function performance",
                    function=name,
                    duration_ms=duration * 1000,
                    success=success,
                    args_count=len(args),
                    kwargs_count=len(kwargs),
                )
        
        return wrapper
    return decorator

# Usage
class APIService:
    def __init__(self) -> None:
        self.optimizer = PerformanceOptimizer(max_concurrent=20)
    
    @monitor_performance("fetch_user_data")
    async def fetch_multiple_users(
        self,
        user_ids: list[UUID],
    ) -> list[User]:
        """Fetch multiple users efficiently."""
        
        async def fetch_single_user(user_id: UUID) -> User:
            return await self.optimizer.timeout_wrapper(
                self.user_repository.get_by_id(user_id),
                timeout=5.0,
                default=None,
            )
        
        tasks = [lambda uid=uid: fetch_single_user(uid) for uid in user_ids]
        
        results = await self.optimizer.run_with_concurrency_limit(tasks)
        
        # Filter out None results (timeouts)
        return [user for user in results if user is not None]
```

---

## Documentation Standards

### 1. Comprehensive Docstrings

**Write detailed, standardized docstrings:**

```python
from typing import Optional, Dict, Any
from uuid import UUID

class UserService:
    """
    Service class for managing user-related operations.
    
    This class provides high-level operations for user management,
    including creation, retrieval, updating, and deletion of users.
    It handles business logic validation and coordinates with the
    repository layer for data persistence.
    
    Attributes:
        repository: User repository for data access
        cache: Cache service for performance optimization
        notification_service: Service for sending notifications
    
    Example:
        >>> service = UserService(repository, cache, notification_service)
        >>> user = await service.create_user(user_data)
        >>> profile = await service.get_user_profile(user.id)
    """
    
    def __init__(
        self,
        repository: UserRepository,
        cache: CacheService,
        notification_service: NotificationService,
    ) -> None:
        """
        Initialize UserService with dependencies.
        
        Args:
            repository: Repository for user data operations
            cache: Cache service for performance optimization
            notification_service: Service for sending notifications
        """
        self.repository = repository
        self.cache = cache
        self.notification_service = notification_service
    
    async def create_user(
        self,
        user_data: UserCreate,
        *,
        send_welcome_email: bool = True,
        auto_verify: bool = False,
    ) -> User:
        """
        Create a new user with validation and side effects.
        
        This method performs comprehensive validation of user data,
        checks for existing users with the same email, creates the user
        record, and optionally sends a welcome email.
        
        Args:
            user_data: User creation data containing name, email, and password
            send_welcome_email: Whether to send welcome email to new user.
                Defaults to True.
            auto_verify: Whether to automatically verify the user's email.
                Defaults to False. Should only be True for admin-created users.
        
        Returns:
            User: The created user object with generated ID and metadata
        
        Raises:
            EmailAlreadyExistsError: If a user with the provided email already exists
            ValidationError: If the user data fails validation rules
            ExternalServiceError: If welcome email sending fails and is required
        
        Example:
            >>> user_data = UserCreate(
            ...     name="John Doe",
            ...     email="john@example.com",
            ...     password="SecurePass123!"
            ... )
            >>> user = await service.create_user(user_data)
            >>> print(f"Created user {user.name} with ID {user.id}")
        
        Note:
            This method will automatically hash the password before storage.
            The returned User object will not contain the password hash for
            security reasons.
        """
        logger.info(
            "Starting user creation",
            email=user_data.email,
            auto_verify=auto_verify,
        )
        
        # Validate email uniqueness
        if await self.repository.get_by_email(user_data.email):
            raise EmailAlreadyExistsError(user_data.email)
        
        # Apply business rules
        processed_data = self._process_user_data(user_data, auto_verify)
        
        # Create user
        user = await self.repository.create(processed_data)
        
        # Send welcome email if requested
        if send_welcome_email:
            try:
                await self.notification_service.send_welcome_email(user)
            except Exception as e:
                logger.error(
                    "Failed to send welcome email",
                    user_id=user.id,
                    error=str(e),
                )
                # Don't fail user creation if email fails
        
        logger.info(
            "User created successfully",
            user_id=user.id,
            email=user.email,
        )
        
        return user
    
    def _process_user_data(
        self,
        user_data: UserCreate,
        auto_verify: bool,
    ) -> Dict[str, Any]:
        """
        Process and validate user data before creation.
        
        This is a private method that applies business rules and
        transformations to user data before it's stored.
        
        Args:
            user_data: Raw user creation data
            auto_verify: Whether to mark email as verified
        
        Returns:
            Dict containing processed user data ready for storage
        
        Note:
            This method is internal and should not be called directly.
        """
        # Implementation details...
        pass
```

### 2. README and Project Documentation

**Create comprehensive project documentation:**

```markdown
# Financial Assistant - Agno Migration

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](http://mypy-lang.org/)

A modern financial assistant application built with the Agno framework, migrated from LangGraph/LangChain for improved performance and maintainability.

## Features

- 🤖 **Intelligent Financial Analysis**: Multi-agent workflow for comprehensive financial data processing
- 📊 **Real-time Data**: Integration with Financial Modeling Prep API for current market data
- 🔄 **Three Workflow Patterns**: Single data queries, comprehensive reports, and conversational chat
- ⚡ **High Performance**: 90%+ memory reduction and 30-50% faster response times vs legacy system
- 🔒 **Enterprise Security**: Comprehensive input validation, secure API key management
- 📈 **Scalable Architecture**: Async-first design supporting high concurrent user loads

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management
- PostgreSQL 13+ (for production)
- Redis 6+ (for caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/financial-assistant.git
   cd financial-assistant
   ```

2. **Install dependencies with uv**
   ```bash
   # Install uv if not already installed
   pipx install uv
   
   # Create virtual environment and install dependencies
   uv venv --python 3.11
   uv sync
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run the application**
   ```bash
   uv run streamlit run src/main.py
   ```

### Environment Variables

```bash
# Required API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here
FINANCIAL_MODELING_PREP_API_KEY=your_fmp_key_here

# Optional API Keys (for multi-provider support)
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here

# Database (use SQLite for development)
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Redis (optional, improves performance)
REDIS_URL=redis://localhost:6379/0

# Application Settings
DEFAULT_LLM_PROVIDER=anthropic
LOG_LEVEL=INFO
DEBUG=false
```

## Development

### Code Quality

This project enforces high code quality standards:

```bash
# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check --fix .

# Type checking
uv run mypy src/

# Run tests
uv run pytest

# Test coverage
uv run pytest --cov=src --cov-report=html
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_workflow.py

# Run integration tests only
uv run pytest tests/integration/
```

## Architecture

### High-Level Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     Agno        │    │   Financial     │
│   Frontend      │───▶│   Workflow      │───▶│   Data APIs     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   5 Specialized │              │
         └──────────────│     Agents      │──────────────┘
                        │                 │
                        └─────────────────┘
```

### Agent Architecture

1. **RouterAgent**: Categorizes user requests
2. **SymbolExtractionAgent**: Extracts stock symbols from natural language
3. **FinancialDataAgents**: Fetch specific financial data (income, metrics, prices)
4. **ReportGenerationAgent**: Creates comprehensive reports
5. **ChatAgent**: Handles conversational interactions

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development process.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following our [coding standards](docs/rules/python-best-practices.md)
4. Write tests for your changes
5. Ensure all tests pass: `uv run pytest`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-org/financial-assistant/issues)
- 💬 [Discussions](https://github.com/your-org/financial-assistant/discussions)
```

---

## Dependency Management

### 1. Using uv for Modern Python Package Management

**Configure pyproject.toml properly:**

```toml
[project]
name = "financial-assistant"
version = "0.1.0"
description = "Modern financial assistant with Agno framework"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
keywords = ["finance", "ai", "agents", "agno", "financial-analysis"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Office/Business :: Financial",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

# Core dependencies
dependencies = [
    "agno>=0.1.0",
    "streamlit>=1.44.0",
    "pydantic>=2.11.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.24.0",
    "python-dotenv>=1.0.0",
    "structlog>=24.0.0",
    "asyncpg>=0.29.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "alembic>=1.13.0",
    "redis[hiredis]>=5.0.0",
    "passlib[bcrypt]>=1.7.0",
    "python-jose[cryptography]>=3.3.0",
    "python-multipart>=0.0.6",
]

# Optional dependencies
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.14.0",
    "httpx>=0.24.0",  # For async testing
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "pre-commit>=3.0.0",
]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.14.0",
    "httpx>=0.24.0",
    "respx>=0.20.0",  # HTTP mocking
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
    "mkdocstrings[python]>=0.24.0",
]

[project.urls]
Homepage = "https://github.com/your-org/financial-assistant"
Documentation = "https://financial-assistant.readthedocs.io"
Repository = "https://github.com/your-org/financial-assistant.git"
Issues = "https://github.com/your-org/financial-assistant/issues"

# Build system
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Tool configurations
[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "N",   # pep8-naming
    "ANN", # flake8-annotations
    "S",   # flake8-bandit
    "T20", # flake8-print
]
ignore = [
    "E501",   # line too long (handled by formatter)
    "ANN101", # missing type annotation for self
    "ANN102", # missing type annotation for cls
    "S101",   # use of assert (OK in tests)
]

[tool.ruff.per-file-ignores]
"tests/**/*.py" = ["S101", "ANN", "T20"]
"**/__init__.py" = ["F401"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
minversion = "8.0"
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### 2. Dependency Management Commands

**Essential uv commands for project management:**

```bash
# Project initialization
uv init financial-assistant --python 3.11
cd financial-assistant

# Install core dependencies
uv add agno streamlit pydantic httpx python-dotenv

# Install development dependencies
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy

# Install optional dependency groups
uv sync --extra dev
uv sync --extra test
uv sync --extra docs

# Update dependencies
uv lock --upgrade
uv sync

# Install from lock file (production)
uv sync --frozen

# Remove dependency
uv remove requests

# Show dependency tree
uv tree

# Check for security vulnerabilities
uv audit

# Export requirements (for compatibility)
uv export --format requirements-txt --output-file requirements.txt
```

---

## Configuration Management

### 1. Avoid Global Variables

**NEVER use global variables - they create hidden dependencies and make testing difficult:**

```python
# ❌ Bad - Global variables create hidden state
DATABASE_CONNECTION = None
CURRENT_USER = None
CACHE = {}

def get_user_data(user_id):
    global CURRENT_USER, DATABASE_CONNECTION
    # Hidden dependencies make this untestable
    return DATABASE_CONNECTION.query(user_id)

def set_current_user(user):
    global CURRENT_USER
    CURRENT_USER = user  # Mutable global state

# ❌ Bad - Global configuration
API_KEY = "secret-key"
DEBUG_MODE = True

# ✅ Good - Dependency injection with configuration objects
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str
    debug_mode: bool = False
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

class UserService:
    def __init__(self, db_connection, settings: Settings):
        self.db = db_connection
        self.settings = settings
    
    def get_user_data(self, user_id: int) -> User:
        # Explicit dependencies, easily testable
        return self.db.query(user_id)

# ✅ Good - Configuration passed explicitly
def create_user_service(db_connection) -> UserService:
    settings = get_settings()
    return UserService(db_connection, settings)
```

**Why global variables are problematic:**
- **Hidden Dependencies**: Functions that use globals have invisible requirements
- **Testing Difficulty**: Hard to mock or isolate for unit testing
- **Thread Safety**: Global state creates race conditions in concurrent code
- **Code Clarity**: Makes data flow and dependencies unclear
- **Reusability**: Functions become coupled to specific global state

**Alternatives to global variables:**
- **Dependency Injection**: Pass dependencies as parameters
- **Configuration Objects**: Use Pydantic Settings for configuration
- **Context Managers**: For temporary state that needs cleanup
- **Class Instances**: Encapsulate related state and behavior
- **Function Parameters**: Make dependencies explicit

### 2. Environment-Aware Settings

**Implement comprehensive configuration management:**

```python
# core/settings.py
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )
    
    # Application metadata
    APP_NAME: str = "Financial Assistant"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-powered financial assistant"
    
    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    
    # Server configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Enable auto-reload")
    
    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://user:pass@localhost/dbname",
        description="Database connection URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="Enable SQL logging")
    
    # Redis
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        ..., 
        min_length=32,
        description="Secret key for cryptographic operations"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=10080,  # 1 week max
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Refresh token expiration time in days"
    )
    
    # API Keys
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key")
    OPENAI_API_KEY: str | None = Field(None, description="OpenAI API key")
    GROQ_API_KEY: str | None = Field(None, description="Groq API key")
    FINANCIAL_MODELING_PREP_API_KEY: str = Field(..., description="FMP API key")
    
    # LLM Configuration
    DEFAULT_LLM_PROVIDER: str = Field(
        default="anthropic",
        description="Default LLM provider"
    )
    MAX_TOKENS: int = Field(default=4000, ge=100, le=100000)
    TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum concurrent requests"
    )
    REQUEST_TIMEOUT_SECONDS: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    
    # Caching
    CACHE_TTL_SECONDS: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Default cache TTL in seconds"
    )
    
    # Logging
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO)
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=1)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=3600, ge=60)
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value: str) -> Environment:
        """Validate and normalize environment."""
        try:
            return Environment(value.lower())
        except ValueError:
            raise ValueError(f"Invalid environment: {value}")
    
    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        """Validate CORS origins."""
        for origin in value:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin}")
        return value
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.ENVIRONMENT == Environment.TESTING
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return str(self.DATABASE_URL).replace("+asyncpg", "")

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Environment-specific configurations
def get_test_settings() -> Settings:
    """Get settings for testing."""
    return Settings(
        ENVIRONMENT=Environment.TESTING,
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
        REDIS_URL="redis://localhost:6379/1",
        SECRET_KEY="test-secret-key-32-characters-long",
        LOG_LEVEL=LogLevel.DEBUG,
    )
```

### 2. Configuration Validation

**Validate configuration at startup:**

```python
# core/config_validator.py
import sys
from pathlib import Path
from typing import Any

import structlog
from pydantic import ValidationError

from .settings import Settings, get_settings

logger = structlog.get_logger()

class ConfigurationError(Exception):
    """Configuration validation error."""
    pass

class ConfigValidator:
    """Validate application configuration."""
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
    
    def validate_all(self) -> None:
        """Run all configuration validations."""
        validations = [
            self._validate_environment,
            self._validate_database,
            self._validate_redis,
            self._validate_api_keys,
            self._validate_security,
            self._validate_file_permissions,
        ]
        
        errors = []
        
        for validation in validations:
            try:
                validation()
            except ConfigurationError as e:
                errors.append(str(e))
            except Exception as e:
                errors.append(f"Unexpected validation error: {e}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error("Configuration validation failed", errors=errors)
            raise ConfigurationError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def _validate_environment(self) -> None:
        """Validate environment configuration."""
        if self.settings.is_production:
            if self.settings.DEBUG:
                raise ConfigurationError("DEBUG cannot be True in production")
            
            if self.settings.SECRET_KEY == "changeme" or len(self.settings.SECRET_KEY) < 32:
                raise ConfigurationError("SECRET_KEY must be secure in production")
    
    def _validate_database(self) -> None:
        """Validate database configuration."""
        if self.settings.is_production:
            if "sqlite" in str(self.settings.DATABASE_URL):
                logger.warning("Using SQLite in production is not recommended")
        
        # Check if database URL is accessible (basic format validation)
        db_url = str(self.settings.DATABASE_URL)
        if not any(db_url.startswith(prefix) for prefix in ["postgresql", "mysql", "sqlite"]):
            raise ConfigurationError(f"Unsupported database URL: {db_url}")
    
    def _validate_redis(self) -> None:
        """Validate Redis configuration."""
        redis_url = str(self.settings.REDIS_URL)
        if not redis_url.startswith("redis://"):
            raise ConfigurationError(f"Invalid Redis URL format: {redis_url}")
    
    def _validate_api_keys(self) -> None:
        """Validate API key configuration."""
        required_keys = {
            "ANTHROPIC_API_KEY": self.settings.ANTHROPIC_API_KEY,
            "FINANCIAL_MODELING_PREP_API_KEY": self.settings.FINANCIAL_MODELING_PREP_API_KEY,
        }
        
        for key_name, key_value in required_keys.items():
            if not key_value or key_value == "changeme":
                raise ConfigurationError(f"{key_name} is required")
            
            if len(key_value) < 10:  # Basic length check
                raise ConfigurationError(f"{key_name} appears to be invalid (too short)")
    
    def _validate_security(self) -> None:
        """Validate security configuration."""
        if len(self.settings.SECRET_KEY) < 32:
            raise ConfigurationError("SECRET_KEY must be at least 32 characters long")
        
        if self.settings.ACCESS_TOKEN_EXPIRE_MINUTES > 1440:  # 24 hours
            logger.warning("Access token expiration is very long (>24h)")
    
    def _validate_file_permissions(self) -> None:
        """Validate file and directory permissions."""
        if self.settings.is_production:
            # Check that sensitive files are not world-readable
            sensitive_files = [".env", "secrets/"]
            
            for file_path in sensitive_files:
                path = Path(file_path)
                if path.exists():
                    mode = path.stat().st_mode
                    if mode & 0o044:  # World or group readable
                        logger.warning(
                            "Sensitive file has broad permissions",
                            file=str(path),
                            permissions=oct(mode),
                        )

def validate_configuration() -> Settings:
    """Validate configuration and return settings."""
    try:
        settings = get_settings()
        validator = ConfigValidator(settings)
        validator.validate_all()
        return settings
    except ValidationError as e:
        logger.error("Configuration validation failed", error=str(e))
        sys.exit(1)
    except ConfigurationError as e:
        logger.error("Configuration error", error=str(e))
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected configuration error", error=str(e))
        sys.exit(1)

# Usage in main.py
def main():
    # Validate configuration at startup
    settings = validate_configuration()
    
    logger.info(
        "Application starting",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        version=settings.APP_VERSION,
    )
    
    # Continue with application initialization...
```

This comprehensive guide covers all the essential best practices for modern Python development with a focus on Python 3.11+ features, maintainable architecture, and production-ready code quality standards.