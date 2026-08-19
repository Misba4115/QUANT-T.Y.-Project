"""Public, secret-free capability discovery."""
from fastapi import APIRouter

from core.capabilities import CapabilityRegistry, build_capability_registry
from core.config import get_settings

router = APIRouter()


@router.get("/", response_model=CapabilityRegistry)
def capabilities() -> CapabilityRegistry:
    return build_capability_registry(get_settings())
