# Architecture Guidelines for Modern Python Applications

## Table of Contents

1. [Clean Architecture Principles](#clean-architecture-principles)
2. [Domain-Driven Design](#domain-driven-design)
3. [Dependency Injection](#dependency-injection)
4. [SOLID Principles in Python](#solid-principles-in-python)
5. [Design Patterns](#design-patterns)
6. [Microservices Architecture](#microservices-architecture)
7. [Data Architecture](#data-architecture)
8. [Security Architecture](#security-architecture)

---

## Clean Architecture Principles

### 1. Layered Architecture

**Implement clear separation of concerns:**

```python
# Domain Layer (Inner layer - no external dependencies)
# models/domain.py
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

@dataclass(frozen=True)
class User:
    """Core domain model - no external dependencies."""
    id: UUID
    email: str
    name: str
    is_active: bool
    
    def can_access_resource(self, resource: "Resource") -> bool:
        """Business logic stays in domain models."""
        return self.is_active and resource.is_public

class UserRepository(Protocol):
    """Repository interface - defines contract."""
    async def get_by_id(self, user_id: UUID) -> User | None: ...
    async def save(self, user: User) -> User: ...

# Application Layer (Use cases)
# services/user_service.py
class UserService:
    """Application service - orchestrates business logic."""
    
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository
    
    async def activate_user(self, user_id: UUID) -> User:
        """Use case: Activate a user."""
        user = await self._repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Business logic
        activated_user = User(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=True
        )
        
        return await self._repository.save(activated_user)

# Infrastructure Layer (Outer layer)
# repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from adapters.database import UserModel

class SQLUserRepository:
    """Concrete repository implementation."""
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def get_by_id(self, user_id: UUID) -> User | None:
        # Database-specific implementation
        result = await self._session.get(UserModel, user_id)
        if not result:
            return None
        
        return User(
            id=result.id,
            email=result.email,
            name=result.name,
            is_active=result.is_active
        )

# Presentation Layer
# api/user_router.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """API endpoint - presentation layer."""
    user = await service.activate_user(user_id)
    return UserResponse.from_domain(user)
```

### 2. Dependency Direction

**Ensure dependencies point inward:**

```python
# ✅ Good - Dependencies point inward
# Domain layer has no dependencies
class User:
    def calculate_subscription_fee(self) -> Decimal:
        # Pure business logic
        pass

# Application layer depends only on domain
class UserService:
    def __init__(self, repository: UserRepository): # Interface from domain
        self._repository = repository

# Infrastructure depends on domain interfaces
class SQLUserRepository(UserRepository): # Implements domain interface
    def __init__(self, session: AsyncSession):
        self._session = session

# ❌ Bad - Domain depends on infrastructure
class User:
    def save(self, session: AsyncSession): # Domain depends on SQLAlchemy!
        # This violates clean architecture
        pass
```

---

## Domain-Driven Design

### 1. Bounded Contexts

**Organize code by business domains:**

```python
# Financial Domain
# domains/financial/
├── models/
│   ├── portfolio.py
│   ├── transaction.py
│   └── market_data.py
├── services/
│   ├── portfolio_service.py
│   └── market_data_service.py
├── repositories/
│   └── interfaces.py
└── value_objects/
    ├── money.py
    └── currency.py

# User Domain
# domains/user/
├── models/
│   ├── user.py
│   └── profile.py
├── services/
│   └── user_service.py
└── repositories/
    └── interfaces.py

# Example: Financial Domain Models
from decimal import Decimal
from dataclasses import dataclass
from typing import NewType

# Value Objects
Currency = NewType('Currency', str)

@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts."""
    amount: Decimal
    currency: Currency
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
    
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

@dataclass(frozen=True)
class StockSymbol:
    """Value object for stock symbols."""
    symbol: str
    
    def __post_init__(self):
        if not self.symbol.isupper():
            object.__setattr__(self, 'symbol', self.symbol.upper())
        if len(self.symbol) > 5:
            raise ValueError("Stock symbol too long")

# Entities
@dataclass
class Portfolio:
    """Portfolio aggregate root."""
    id: UUID
    user_id: UUID
    name: str
    positions: list["Position"]
    
    def add_position(self, symbol: StockSymbol, quantity: int, price: Money) -> None:
        """Add a new position to portfolio."""
        position = Position(
            symbol=symbol,
            quantity=quantity,
            average_price=price
        )
        self.positions.append(position)
    
    def calculate_total_value(self, market_prices: dict[StockSymbol, Money]) -> Money:
        """Calculate total portfolio value."""
        total = Money(Decimal(0), Currency("USD"))
        
        for position in self.positions:
            if position.symbol in market_prices:
                market_price = market_prices[position.symbol]
                position_value = Money(
                    market_price.amount * position.quantity,
                    market_price.currency
                )
                total = total.add(position_value)
        
        return total

@dataclass
class Position:
    """Position within a portfolio."""
    symbol: StockSymbol
    quantity: int
    average_price: Money
    
    def calculate_unrealized_pnl(self, current_price: Money) -> Money:
        """Calculate unrealized profit/loss."""
        current_value = Money(
            current_price.amount * self.quantity,
            current_price.currency
        )
        cost_basis = Money(
            self.average_price.amount * self.quantity,
            self.average_price.currency
        )
        
        return current_value.add(Money(-cost_basis.amount, cost_basis.currency))
```

### 2. Domain Services

**Implement complex business logic in domain services:**

```python
# domains/financial/services/portfolio_analytics.py
from typing import Protocol

class MarketDataProvider(Protocol):
    """Interface for market data - defined in domain."""
    async def get_current_price(self, symbol: StockSymbol) -> Money: ...
    async def get_historical_prices(
        self, 
        symbol: StockSymbol, 
        days: int
    ) -> list[tuple[date, Money]]: ...

class PortfolioAnalyticsService:
    """Domain service for portfolio calculations."""
    
    def __init__(self, market_data: MarketDataProvider) -> None:
        self._market_data = market_data
    
    async def calculate_portfolio_metrics(
        self, 
        portfolio: Portfolio
    ) -> "PortfolioMetrics":
        """Calculate comprehensive portfolio metrics."""
        
        # Get current market prices
        symbols = {pos.symbol for pos in portfolio.positions}
        current_prices = {}
        
        for symbol in symbols:
            current_prices[symbol] = await self._market_data.get_current_price(symbol)
        
        # Calculate metrics
        total_value = portfolio.calculate_total_value(current_prices)
        total_cost = self._calculate_total_cost(portfolio)
        total_pnl = total_value.add(Money(-total_cost.amount, total_cost.currency))
        
        return PortfolioMetrics(
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            pnl_percentage=self._calculate_percentage(total_pnl, total_cost)
        )
    
    def _calculate_total_cost(self, portfolio: Portfolio) -> Money:
        """Calculate total cost basis of portfolio."""
        total = Money(Decimal(0), Currency("USD"))
        
        for position in portfolio.positions:
            cost = Money(
                position.average_price.amount * position.quantity,
                position.average_price.currency
            )
            total = total.add(cost)
        
        return total
    
    def _calculate_percentage(self, numerator: Money, denominator: Money) -> Decimal:
        """Calculate percentage change."""
        if denominator.amount == 0:
            return Decimal(0)
        return (numerator.amount / denominator.amount) * 100

@dataclass(frozen=True)
class PortfolioMetrics:
    """Value object for portfolio metrics."""
    total_value: Money
    total_cost: Money
    total_pnl: Money
    pnl_percentage: Decimal
```

### 3. Aggregates and Consistency

**Design aggregates for consistency boundaries:**

```python
# domains/trading/models/order.py
from enum import Enum
from datetime import datetime

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

@dataclass
class Order:
    """Order aggregate root - maintains consistency within order lifecycle."""
    id: UUID
    portfolio_id: UUID
    symbol: StockSymbol
    quantity: int
    order_type: OrderType
    limit_price: Money | None
    status: OrderStatus
    created_at: datetime
    filled_at: datetime | None = None
    filled_price: Money | None = None
    filled_quantity: int = 0
    
    def fill(self, price: Money, quantity: int) -> None:
        """Fill order - maintains business invariants."""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot fill order in status {self.status}")
        
        if quantity > self.quantity:
            raise ValueError("Cannot fill more than ordered quantity")
        
        if self.order_type == OrderType.LIMIT and self.limit_price:
            if price.amount > self.limit_price.amount:
                raise ValueError("Fill price exceeds limit price")
        
        self.filled_price = price
        self.filled_quantity = quantity
        self.filled_at = datetime.utcnow()
        
        if quantity == self.quantity:
            self.status = OrderStatus.FILLED
        else:
            # Partial fill logic could be added here
            self.status = OrderStatus.FILLED
    
    def cancel(self) -> None:
        """Cancel order if possible."""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot cancel order in status {self.status}")
        
        self.status = OrderStatus.CANCELLED

# Application service coordinates aggregates
class TradingService:
    """Application service for trading operations."""
    
    def __init__(
        self,
        order_repository: OrderRepository,
        portfolio_repository: PortfolioRepository,
        market_data: MarketDataProvider,
    ) -> None:
        self._order_repo = order_repository
        self._portfolio_repo = portfolio_repository
        self._market_data = market_data
    
    async def place_market_order(
        self,
        portfolio_id: UUID,
        symbol: StockSymbol,
        quantity: int,
    ) -> Order:
        """Place a market order."""
        
        # Validate portfolio exists
        portfolio = await self._portfolio_repo.get_by_id(portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundError(portfolio_id)
        
        # Get current market price
        current_price = await self._market_data.get_current_price(symbol)
        
        # Create order
        order = Order(
            id=uuid4(),
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            order_type=OrderType.MARKET,
            limit_price=None,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        
        # Simulate immediate fill for market order
        order.fill(current_price, quantity)
        
        # Save order
        await self._order_repo.save(order)
        
        # Update portfolio
        portfolio.add_position(symbol, quantity, current_price)
        await self._portfolio_repo.save(portfolio)
        
        return order
```

---

## Dependency Injection

### 1. Container-Based DI

**Implement dependency injection container:**

```python
# core/container.py
from typing import TypeVar, Generic, Callable, Any
from abc import ABC, abstractmethod

T = TypeVar('T')

class Container:
    """Simple dependency injection container."""
    
    def __init__(self) -> None:
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}
        self._singletons: dict[type, Any] = {}
    
    def register_singleton(self, interface: type[T], implementation: T) -> None:
        """Register a singleton instance."""
        self._singletons[interface] = implementation
    
    def register_factory(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register a factory function."""
        self._factories[interface] = factory
    
    def register_transient(self, interface: type[T], implementation: type[T]) -> None:
        """Register a transient service."""
        self._services[interface] = implementation
    
    def get(self, interface: type[T]) -> T:
        """Resolve a service."""
        
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check factories
        if interface in self._factories:
            instance = self._factories[interface]()
            return instance
        
        # Check transient services
        if interface in self._services:
            implementation = self._services[interface]
            # Auto-wire constructor dependencies
            return self._create_instance(implementation)
        
        raise ValueError(f"Service {interface} not registered")
    
    def _create_instance(self, cls: type[T]) -> T:
        """Create instance with dependency injection."""
        import inspect
        
        signature = inspect.signature(cls.__init__)
        kwargs = {}
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != param.empty:
                dependency = self.get(param.annotation)
                kwargs[param_name] = dependency
        
        return cls(**kwargs)

# Usage in application setup
def setup_container() -> Container:
    """Configure dependency injection."""
    container = Container()
    
    # Register database dependencies
    container.register_singleton(AsyncSession, get_database_session())
    
    # Register repositories
    container.register_transient(UserRepository, SQLUserRepository)
    container.register_transient(PortfolioRepository, SQLPortfolioRepository)
    
    # Register services
    container.register_transient(UserService, UserService)
    container.register_transient(PortfolioService, PortfolioService)
    
    # Register external services
    container.register_factory(
        MarketDataProvider,
        lambda: FinancialModelingPrepClient(api_key=get_settings().FINANCIAL_MODELING_PREP_API_KEY)
    )
    
    return container

# FastAPI integration
from fastapi import Depends

# Global container
_container: Container | None = None

def get_container() -> Container:
    """Get the DI container."""
    global _container
    if _container is None:
        _container = setup_container()
    return _container

def inject(service_type: type[T]) -> T:
    """Dependency injection for FastAPI."""
    def dependency() -> T:
        container = get_container()
        return container.get(service_type)
    
    return Depends(dependency)

# Usage in routes
@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    service: UserService = inject(UserService),
) -> UserResponse:
    user = await service.get_user(user_id)
    return UserResponse.from_domain(user)
```

### 2. Protocol-Based Dependency Injection

**Use protocols for loose coupling:**

```python
# Define protocols for dependencies
from typing import Protocol

class EmailService(Protocol):
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str
    ) -> None: ...

class NotificationService(Protocol):
    async def send_notification(
        self,
        user_id: UUID,
        message: str,
        type: str
    ) -> None: ...

class AuditLogger(Protocol):
    async def log_action(
        self,
        user_id: UUID,
        action: str,
        details: dict[str, Any]
    ) -> None: ...

# Service depends on protocols, not concrete implementations
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        email_service: EmailService,
        notification_service: NotificationService,
        audit_logger: AuditLogger,
    ) -> None:
        self._repository = repository
        self._email_service = email_service
        self._notification_service = notification_service
        self._audit_logger = audit_logger
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create user with side effects."""
        
        # Create user
        user = await self._repository.create(user_data)
        
        # Send welcome email
        await self._email_service.send_email(
            to=user.email,
            subject="Welcome!",
            body=f"Welcome {user.name}!"
        )
        
        # Send notification
        await self._notification_service.send_notification(
            user_id=user.id,
            message="Account created successfully",
            type="success"
        )
        
        # Log action
        await self._audit_logger.log_action(
            user_id=user.id,
            action="user_created",
            details={"email": user.email, "name": user.name}
        )
        
        return user

# Concrete implementations
class SMTPEmailService:
    """SMTP email implementation."""
    
    def __init__(self, smtp_config: SMTPConfig) -> None:
        self._config = smtp_config
    
    async def send_email(self, to: str, subject: str, body: str) -> None:
        # SMTP implementation
        pass

class DatabaseAuditLogger:
    """Database audit logging implementation."""
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def log_action(
        self,
        user_id: UUID,
        action: str,
        details: dict[str, Any]
    ) -> None:
        # Database logging implementation
        pass

# Easy to swap implementations for testing
class MockEmailService:
    """Mock email service for testing."""
    
    def __init__(self) -> None:
        self.sent_emails: list[dict] = []
    
    async def send_email(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body
        })
```

---

## SOLID Principles in Python

### 1. Single Responsibility Principle (SRP)

**Each class should have one reason to change:**

```python
# ❌ Bad - Multiple responsibilities
class UserManager:
    def create_user(self, user_data: dict) -> User:
        # User creation logic
        pass
    
    def send_welcome_email(self, user: User) -> None:
        # Email sending logic
        pass
    
    def log_user_creation(self, user: User) -> None:
        # Logging logic
        pass
    
    def validate_user_data(self, data: dict) -> bool:
        # Validation logic
        pass

# ✅ Good - Single responsibilities
class UserCreator:
    """Responsible only for user creation."""
    
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository
    
    async def create_user(self, user_data: UserCreate) -> User:
        return await self._repository.create(user_data)

class UserValidator:
    """Responsible only for user validation."""
    
    def validate_creation_data(self, data: UserCreate) -> None:
        if not data.email:
            raise ValidationError("Email is required")
        if len(data.password) < 8:
            raise ValidationError("Password too short")

class UserNotifier:
    """Responsible only for user notifications."""
    
    def __init__(self, email_service: EmailService) -> None:
        self._email_service = email_service
    
    async def send_welcome_notification(self, user: User) -> None:
        await self._email_service.send_email(
            to=user.email,
            subject="Welcome!",
            body=f"Welcome {user.name}!"
        )

class UserAuditor:
    """Responsible only for audit logging."""
    
    def __init__(self, logger: AuditLogger) -> None:
        self._logger = logger
    
    async def log_creation(self, user: User) -> None:
        await self._logger.log_action(
            user_id=user.id,
            action="user_created",
            details={"email": user.email}
        )

# Orchestrating service
class UserService:
    """Orchestrates user operations."""
    
    def __init__(
        self,
        creator: UserCreator,
        validator: UserValidator,
        notifier: UserNotifier,
        auditor: UserAuditor,
    ) -> None:
        self._creator = creator
        self._validator = validator
        self._notifier = notifier
        self._auditor = auditor
    
    async def register_user(self, user_data: UserCreate) -> User:
        # Validate
        self._validator.validate_creation_data(user_data)
        
        # Create
        user = await self._creator.create_user(user_data)
        
        # Notify (fire and forget)
        asyncio.create_task(self._notifier.send_welcome_notification(user))
        
        # Audit (fire and forget)
        asyncio.create_task(self._auditor.log_creation(user))
        
        return user
```

### 2. Open/Closed Principle (OCP)

**Open for extension, closed for modification:**

```python
from abc import ABC, abstractmethod

# Abstract base for calculation strategies
class PricingStrategy(ABC):
    """Base class for pricing strategies."""
    
    @abstractmethod
    async def calculate_price(
        self, 
        symbol: StockSymbol, 
        quantity: int
    ) -> Money:
        """Calculate price for given symbol and quantity."""
        pass

# Concrete strategies
class MarketPricingStrategy(PricingStrategy):
    """Market price strategy."""
    
    def __init__(self, market_data: MarketDataProvider) -> None:
        self._market_data = market_data
    
    async def calculate_price(
        self, 
        symbol: StockSymbol, 
        quantity: int
    ) -> Money:
        current_price = await self._market_data.get_current_price(symbol)
        return Money(current_price.amount * quantity, current_price.currency)

class VWAPPricingStrategy(PricingStrategy):
    """Volume-weighted average price strategy."""
    
    def __init__(self, market_data: MarketDataProvider) -> None:
        self._market_data = market_data
    
    async def calculate_price(
        self, 
        symbol: StockSymbol, 
        quantity: int
    ) -> Money:
        # Calculate VWAP
        vwap = await self._calculate_vwap(symbol)
        return Money(vwap.amount * quantity, vwap.currency)
    
    async def _calculate_vwap(self, symbol: StockSymbol) -> Money:
        # VWAP calculation logic
        pass

class DiscountPricingStrategy(PricingStrategy):
    """Discount pricing for large orders."""
    
    def __init__(
        self, 
        base_strategy: PricingStrategy,
        discount_threshold: int,
        discount_rate: Decimal
    ) -> None:
        self._base_strategy = base_strategy
        self._discount_threshold = discount_threshold
        self._discount_rate = discount_rate
    
    async def calculate_price(
        self, 
        symbol: StockSymbol, 
        quantity: int
    ) -> Money:
        base_price = await self._base_strategy.calculate_price(symbol, quantity)
        
        if quantity >= self._discount_threshold:
            discount = base_price.amount * self._discount_rate
            return Money(base_price.amount - discount, base_price.currency)
        
        return base_price

# Context class that uses strategies
class OrderPriceCalculator:
    """Calculator that can use different pricing strategies."""
    
    def __init__(self, strategy: PricingStrategy) -> None:
        self._strategy = strategy
    
    def set_strategy(self, strategy: PricingStrategy) -> None:
        """Change pricing strategy at runtime."""
        self._strategy = strategy
    
    async def calculate_order_price(
        self, 
        symbol: StockSymbol, 
        quantity: int
    ) -> Money:
        return await self._strategy.calculate_price(symbol, quantity)

# Easy to add new strategies without modifying existing code
class TimeBasedPricingStrategy(PricingStrategy):
    """New pricing strategy - no modification to existing code needed."""
    
    def __init__(self, market_data: MarketDataProvider) -> None:
        self._market_data = market_data
    
    async def calculate_price(
        self, 
        symbol: StockSymbol, 
        quantity: int
    ) -> Money:
        # Time-based pricing logic
        pass
```

### 3. Liskov Substitution Principle (LSP)

**Subtypes must be substitutable for their base types:**

```python
# Base class that defines contract
class DataProcessor(ABC):
    """Base class for data processors."""
    
    @abstractmethod
    async def process(self, data: bytes) -> dict[str, Any]:
        """
        Process data and return result.
        
        Preconditions:
        - data must not be empty
        
        Postconditions:
        - result must contain 'status' key
        - result['status'] must be 'success' or 'error'
        """
        pass

# ✅ Good - Respects base class contract
class JSONDataProcessor(DataProcessor):
    """Process JSON data."""
    
    async def process(self, data: bytes) -> dict[str, Any]:
        if not data:  # Respects precondition
            return {"status": "error", "message": "Empty data"}
        
        try:
            parsed = json.loads(data.decode('utf-8'))
            return {"status": "success", "data": parsed}  # Satisfies postcondition
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON"}  # Satisfies postcondition

class XMLDataProcessor(DataProcessor):
    """Process XML data."""
    
    async def process(self, data: bytes) -> dict[str, Any]:
        if not data:  # Respects precondition
            return {"status": "error", "message": "Empty data"}
        
        try:
            # XML processing logic
            parsed = self._parse_xml(data)
            return {"status": "success", "data": parsed}  # Satisfies postcondition
        except Exception:
            return {"status": "error", "message": "Invalid XML"}  # Satisfies postcondition

# ❌ Bad - Violates LSP
class StrictJSONProcessor(DataProcessor):
    """Violates LSP by adding stricter preconditions."""
    
    async def process(self, data: bytes) -> dict[str, Any]:
        # Violates LSP - adds stricter precondition
        if len(data) < 10:
            raise ValueError("Data must be at least 10 bytes")
        
        # Also violates postcondition format
        result = json.loads(data.decode('utf-8'))
        return result  # Missing 'status' key!

# Client code works with any processor
class DataService:
    def __init__(self, processor: DataProcessor) -> None:
        self._processor = processor
    
    async def handle_data(self, data: bytes) -> str:
        """Client code relies on base class contract."""
        result = await self._processor.process(data)
        
        # Can safely access 'status' due to postcondition
        if result["status"] == "success":
            return "Data processed successfully"
        else:
            return f"Processing failed: {result.get('message', 'Unknown error')}"
```

### 4. Interface Segregation Principle (ISP)

**Clients should not depend on interfaces they don't use:**

```python
# ❌ Bad - Fat interface
class UserManager(Protocol):
    async def create_user(self, data: UserCreate) -> User: ...
    async def update_user(self, id: UUID, data: UserUpdate) -> User: ...
    async def delete_user(self, id: UUID) -> None: ...
    async def get_user(self, id: UUID) -> User: ...
    async def send_email(self, user: User, subject: str, body: str) -> None: ...
    async def log_activity(self, user: User, activity: str) -> None: ...
    async def generate_report(self, user: User) -> bytes: ...
    async def backup_user_data(self, user: User) -> None: ...

# ✅ Good - Segregated interfaces
class UserReader(Protocol):
    """Interface for reading user data."""
    async def get_user(self, id: UUID) -> User | None: ...
    async def list_users(self, limit: int, offset: int) -> list[User]: ...

class UserWriter(Protocol):
    """Interface for writing user data."""
    async def create_user(self, data: UserCreate) -> User: ...
    async def update_user(self, id: UUID, data: UserUpdate) -> User: ...
    async def delete_user(self, id: UUID) -> None: ...

class UserNotifier(Protocol):
    """Interface for user notifications."""
    async def send_email(self, user: User, subject: str, body: str) -> None: ...
    async def send_push_notification(self, user: User, message: str) -> None: ...

class UserReporter(Protocol):
    """Interface for user reporting."""
    async def generate_user_report(self, user: User) -> bytes: ...
    async def export_user_data(self, user: User) -> dict: ...

# Services depend only on what they need
class UserDisplayService:
    """Only needs to read user data."""
    
    def __init__(self, reader: UserReader) -> None:
        self._reader = reader
    
    async def get_user_profile(self, user_id: UUID) -> UserProfile:
        user = await self._reader.get_user(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return UserProfile.from_user(user)

class UserRegistrationService:
    """Needs to write and notify."""
    
    def __init__(
        self, 
        writer: UserWriter, 
        notifier: UserNotifier
    ) -> None:
        self._writer = writer
        self._notifier = notifier
    
    async def register_user(self, data: UserCreate) -> User:
        user = await self._writer.create_user(data)
        await self._notifier.send_email(
            user, 
            "Welcome!", 
            "Welcome to our platform!"
        )
        return user

class UserAnalyticsService:
    """Only needs reporting capabilities."""
    
    def __init__(self, reporter: UserReporter) -> None:
        self._reporter = reporter
    
    async def generate_analytics(self, user_id: UUID) -> bytes:
        user = await self._reader.get_user(user_id)
        return await self._reporter.generate_user_report(user)
```

### 5. Dependency Inversion Principle (DIP)

**Depend on abstractions, not concretions:**

```python
# ❌ Bad - High-level module depends on low-level module
class OrderService:
    def __init__(self) -> None:
        # Direct dependency on concrete implementations
        self._db = PostgreSQLDatabase()  # Concrete dependency
        self._email = SMTPEmailService()  # Concrete dependency
        self._payment = StripePaymentGateway()  # Concrete dependency
    
    async def process_order(self, order_data: OrderCreate) -> Order:
        # Tightly coupled to specific implementations
        pass

# ✅ Good - Depend on abstractions
class OrderService:
    """High-level module depends only on abstractions."""
    
    def __init__(
        self,
        repository: OrderRepository,  # Abstract interface
        notifier: NotificationService,  # Abstract interface
        payment_gateway: PaymentGateway,  # Abstract interface
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._payment_gateway = payment_gateway
    
    async def process_order(self, order_data: OrderCreate) -> Order:
        # Create order
        order = Order.from_create_data(order_data)
        
        # Process payment through abstraction
        payment_result = await self._payment_gateway.charge(
            order.total_amount,
            order_data.payment_method
        )
        
        if payment_result.success:
            order.mark_as_paid()
            
            # Save through abstraction
            saved_order = await self._repository.save(order)
            
            # Notify through abstraction
            await self._notifier.send_notification(
                order.customer_email,
                "Order Confirmed",
                f"Your order {order.id} has been confirmed"
            )
            
            return saved_order
        else:
            order.mark_as_failed(payment_result.error_message)
            await self._repository.save(order)
            raise PaymentFailedError(payment_result.error_message)

# Abstract interfaces (high-level)
class OrderRepository(Protocol):
    async def save(self, order: Order) -> Order: ...
    async def get_by_id(self, order_id: UUID) -> Order | None: ...

class PaymentGateway(Protocol):
    async def charge(
        self, 
        amount: Money, 
        payment_method: PaymentMethod
    ) -> PaymentResult: ...

class NotificationService(Protocol):
    async def send_notification(
        self, 
        email: str, 
        subject: str, 
        body: str
    ) -> None: ...

# Concrete implementations (low-level)
class PostgreSQLOrderRepository:
    """Concrete implementation depends on abstraction."""
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def save(self, order: Order) -> Order:
        # PostgreSQL-specific implementation
        pass

class StripePaymentGateway:
    """Concrete implementation of payment gateway."""
    
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
    
    async def charge(
        self, 
        amount: Money, 
        payment_method: PaymentMethod
    ) -> PaymentResult:
        # Stripe-specific implementation
        pass

# Easy to swap implementations
class MockPaymentGateway:
    """Mock implementation for testing."""
    
    async def charge(
        self, 
        amount: Money, 
        payment_method: PaymentMethod
    ) -> PaymentResult:
        return PaymentResult(success=True, transaction_id="mock-123")

# Configuration determines concrete implementations
def configure_order_service(test_mode: bool = False) -> OrderService:
    """Factory function to configure dependencies."""
    
    if test_mode:
        repository = MockOrderRepository()
        payment_gateway = MockPaymentGateway()
        notifier = MockNotificationService()
    else:
        session = get_database_session()
        repository = PostgreSQLOrderRepository(session)
        payment_gateway = StripePaymentGateway(api_key=get_stripe_key())
        notifier = EmailNotificationService(smtp_config=get_smtp_config())
    
    return OrderService(
        repository=repository,
        payment_gateway=payment_gateway,
        notifier=notifier,
    )
```

This architecture guide provides a comprehensive foundation for building maintainable, testable, and scalable Python applications using proven architectural patterns and principles.