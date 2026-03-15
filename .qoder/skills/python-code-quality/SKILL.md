---
name: python-code-quality
description:编写高质量的Python代码，要求使用面向对象编程，函数入参和返回值必须使用类型注解。采用现代Python最佳实践(SOLID原则、设计模式、Python 3.10+特性)。适用于代码审查、重构和新功能开发。当用户需要编写Python代码、进行代码审查或重构时使用。
---

# Python代码质量指南

##🎯 核心目标
设计并编写符合现代Python最佳实践的工业级代码。要求代码在兼容Python 3.10的前提下，采用最高版本的工程化思维。

##🏗️设计约束 (SOLID原则)

1. **S (单一职责)**:每个类或函数只做一件事。数据处理、业务逻辑、IO操作必须解耦。
2. **O (开闭原则)**: 核心逻辑对扩展开放，对修改关闭。优先使用"策略模式"处理不同的算法。
3. **L (里氏替换)**:子类必须能替换掉基类，确保继承体系的逻辑一致性。
4. **I (接口隔离)**: 优先使用 `typing.Protocol`定义轻量级、非侵入式的接口。
5. **D (依赖倒置)**:高层模块不依赖底层实现，通过抽象接口注入依赖。

##🐍 3.10+技术栈规范

###现类型系统

```python
from __future__ import annotations
from typing import Protocol, Annotated
from dataclasses import dataclass

# 使用现代联合类型语法 (Python 3.10+)
UserIdentifier = int | str
UserData = dict[str, int | str | bool]

# 使用Annotated增强语义
from typing import Annotated
Email = Annotated[str, "Valid email address"]

@dataclass(slots=True, frozen=True)
class User:
    """不可变的用户数据类，内存效率优化"""
    id: int
    name: str
    email: Email
    is_active: bool = True
    
    def __post_init__(self) -> None:
        """数据验证"""
        if "@" not in self.email:
            raise ValueError("Invalid email format")

# 使用Protocol定义轻量级接口
class UserRepository(Protocol):
    """用户仓储接口 - 结构化类型"""
    def get_by_id(self, user_id: int) -> User | None: ...
    def save(self, user: User) -> None: ...

# 依赖注入实现
class UserService:
    """高层服务类 - 依赖倒置原则"""
    def __init__(self, repository: UserRepository) -> None:
        self.repo = repository
    
    def get_user(self, user_id: int) -> User | None:
        """获取用户信息 -单一职责"""
        return self.repo.get_by_id(user_id)
    
    def create_user(self, user_data: UserData) -> User:
        """创建新用户"""
        user = User(**user_data)  # type: ignore
        self.repo.save(user)
        return user
```

###设计模式实现

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol
from datetime import datetime

# ---领模型 (Domain Model) ---
@dataclass(slots=True, frozen=True)
class PaymentRequest:
    """不可变的支付请求数据"""
    amount: float
    currency: str = "USD"
    timestamp: datetime | None = None

@dataclass(slots=True, frozen=True)
class PaymentResult:
    """不可变的支付结果数据"""
    success: bool
    transaction_id: str
    message: str = ""

# ---接口定义 (使用Protocol) ---
class PaymentProcessor(Protocol):
    """支付处理器接口 -接口隔离原则"""
    def process(self, request: PaymentRequest) -> PaymentResult: ...
    def refund(self, transaction_id: str) -> PaymentResult: ...

# ---具实现实现 (里氏替换原则) ---
class CreditCardProcessor:
    """信用卡支付处理器"""
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
    
    def process(self, request: PaymentRequest) -> PaymentResult:
        # 信用卡支付逻辑
        return PaymentResult(
            success=True,
            transaction_id=f"cc_{hash(request)}",
            message="Credit card payment processed"
        )
    
    def refund(self, transaction_id: str) -> PaymentResult:
        # 信用卡退款逻辑
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            message="Credit card refund processed"
        )

class PayPalProcessor:
    """PayPal支付处理器 -可替换实现"""
    def process(self, request: PaymentRequest) -> PaymentResult:
        # PayPal支付逻辑
        return PaymentResult(
            success=True,
            transaction_id=f"pp_{hash(request)}",
            message="PayPal payment processed"
        )
    
    def refund(self, transaction_id: str) -> PaymentResult:
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            message="PayPal refund processed"
        )

# ---模式 (开闭原则) ---
class PaymentContext:
    """支付上下文 -高层模块不依赖具体实现"""
    def __init__(self, processor: PaymentProcessor) -> None:
        self.processor = processor
    
    def execute_payment(self, amount: float, currency: str = "USD") -> PaymentResult:
        """执行支付 - 使用match-case处理结果 (Python 3.10+)"""
        request = PaymentRequest(amount=amount, currency=currency)
        result = self.processor.process(request)
        
        match result.success:
            case True:
                return result
            case False:
                return PaymentResult(
                    success=False,
                    transaction_id="",
                    message=f"Payment failed: {result.message}"
                )
```

##📋现类型注解规范

### Python 3.10+ 类型语法

```python
from __future__ import annotations
from typing import Annotated, TypeVar, Generic, Protocol
from datetime import datetime

#现联合类型语法 (推荐)
def calculate_total(items: list[float]) -> float:
    return sum(items)

def find_user(users: dict[int, str], user_id: int) -> str | None:
    return users.get(user_id)

def process_data(data: str | int) -> str:
    return str(data)

# 使用Annotated增强语义
from typing import Annotated
Email = Annotated[str, "Valid email address"]
UserId = Annotated[int, "Positive user identifier"]

@dataclass
class UserData:
    id: UserId
    email: Email
    created_at: datetime

#泛使用 (现代语法)
T = TypeVar('T')

@dataclass(slots=True)
class Container(Generic[T]):
    value: T
    
    def get_value(self) -> T:
        return self.value

# Protocol定义接口 (结构化类型)
class DataProcessor(Protocol):
    def process(self, data: list[float]) -> float: ...
    def validate(self, data: list[float]) -> bool: ...

# 使用示例
class AverageProcessor:
    def process(self, data: list[float]) -> float:
        return sum(data) / len(data) if data else 0.0
    
    def validate(self, data: list[float]) -> bool:
        return all(isinstance(x, (int, float)) for x in data)
```

###高类型特性 (Python 3.10+)

```python
from typing import Literal, Final, Never, Self
from enum import Enum

# Literal类型限制
Status = Literal["pending", "processing", "completed", "failed"]

# Final常量
class Config:
    API_VERSION: Final[str] = "1.0.0"
    MAX_RETRIES: Final[int] = 3

# Never类型 (表示函数永不返回)
def raise_error(message: str) -> Never:
    raise RuntimeError(message)

# Self类型 (方法返回自身类型)
class FluentBuilder:
    def __init__(self) -> None:
        self._data: dict[str, any] = {}
    
    def add_field(self, key: str, value: any) -> Self:
        self._data[key] = value
        return self
    
    def build(self) -> dict[str, any]:
        return self._data.copy()

# 使用示例
builder = FluentBuilder().add_field("name", "John").add_field("age", 30)
result = builder.build()
```

##📋工化代码检查清单

### 设计原则验证
- [ ] **SRP**:类/函数只做一件事
- [ ] **OCP**:核心逻辑对扩展开放，对修改关闭
- [ ] **LSP**:子类可替换父类
- [ ] **ISP**: 使用Protocol定义轻量级接口
- [ ] **DIP**:高层模块依赖抽象而非具体实现

###现Python特性
- [ ] 使用 `@dataclass(slots=True, frozen=True)` 优化数据类
- [ ] 使用 `|`联类型语法替代 `Union`
- [ ] 使用 `typing.Protocol`定接口
- [ ] 使用 `match-case`处理复杂分支逻辑
- [ ] 使用 `Annotated`类型强类型语义

### 代码质量标准
- [ ]所有函数参数都有类型注解
- [ ]所有函数返回值都有类型注解
- [ ]异常处理完整且具体
- [ ] 日志记录适当且结构化
- [ ] 代码通过mypy严格检查
- [ ]单元测试覆盖率≥80%

## 实用工具

- [类型检查脚本](scripts/type_check.py) -运行mypy严格检查
- [代码格式化脚本](scripts/format_code.py) - 自动格式化代码
- [质量评估脚本](scripts/quality_check.py) - 综合质量评估
- [依赖安装脚本](scripts/install_tools.py) - 一键安装工具链

## 📚参资源

- [typing模块官方文档](https://docs.python.org/3/library/typing.html)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 585 - Built-in Generic Types](https://www.python.org/dev/peps/pep-0585/)
- [PEP 604 - Allow writing union types as X | Y](https://www.python.org/dev/peps/pep-0604/)
- [mypy类型检查器](https://mypy.readthedocs.io/)
- [Python 3.10 What's New](https://docs.python.org/3/whatsnew/3.10.html)