"""基础设施：应用生命周期钩子。"""

from src.infrastructure.lifecycle.lifespan import application_lifespan, empty_lifespan

__all__ = ["application_lifespan", "empty_lifespan"]
