# backend/api/v1/controllers/content/__init__.py
from .base import ContentBaseController
from .analysis import ContentAnalysisController

class ContentController(ContentBaseController, ContentAnalysisController):
    """
    Unified Content Controller (Elite V2.2).
    Inherits from base CRUD and analysis modules.
    """
    pass

__all__ = ["ContentController"]
