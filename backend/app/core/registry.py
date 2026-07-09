"""Module auto-discovery. Adding a feature module requires ZERO core changes:

drop a package under app/modules/<name>/ with a `router.py` exposing `router`
(an APIRouter) and optionally a `models.py` with SQLAlchemy models.
"""

import importlib
import logging
import pkgutil

from fastapi import APIRouter

import app.modules

logger = logging.getLogger(__name__)


def _module_names() -> list[str]:
    return [m.name for m in pkgutil.iter_modules(app.modules.__path__) if m.ispkg]


def import_all_models() -> None:
    """Import every module's models so Base.metadata sees all tables."""
    for name in _module_names():
        try:
            importlib.import_module(f"app.modules.{name}.models")
        except ModuleNotFoundError:
            pass  # module has no models — fine


def collect_routers() -> list[APIRouter]:
    routers = []
    for name in _module_names():
        try:
            mod = importlib.import_module(f"app.modules.{name}.router")
        except ModuleNotFoundError:
            continue
        router = getattr(mod, "router", None)
        if isinstance(router, APIRouter):
            routers.append(router)
        else:
            logger.warning("module %s has router.py without a `router` APIRouter", name)
    return routers
