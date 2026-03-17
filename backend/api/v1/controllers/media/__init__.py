# backend/api/v1/controllers/media/__init__.py
from litestar import Controller
from litestar.di import Provide
from backend.database.repositories import provide_media_repo

from .base import MediaBaseController
from .bulk import MediaBulkController
from .tools import MediaToolsController

class MediaController(MediaBaseController, MediaBulkController, MediaToolsController, Controller):
    """
    Unified Media Controller (Elite V2.2).
    Inherits from base, bulk, and tools modules.
    """
    path = "/api/v1/media"
    dependencies = {"media_repo": Provide(provide_media_repo)}

__all__ = ["MediaController"]
