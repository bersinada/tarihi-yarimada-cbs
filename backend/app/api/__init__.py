"""
API Routes module
"""

from .assets import router as assets_router
from .segments import router as segments_router
from .notes import router as notes_router
from .ogc import router as ogc_router

__all__ = [
    "assets_router",
    "segments_router",
    "notes_router",
    "ogc_router"
]
