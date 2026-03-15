"""V1 API package - route aggregation."""

from fastapi import APIRouter

from src.api.v1.auth_routes import router as auth_router
from src.api.v1.rbac_routes import router as rbac_router
from src.api.v1.user_routes import router as user_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth_router)
v1_router.include_router(user_router)
v1_router.include_router(rbac_router)

__all__ = ["v1_router"]
