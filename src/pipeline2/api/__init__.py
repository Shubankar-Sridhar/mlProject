"""FastAPI routes and dependencies."""

from .routes import app
from .schemas import *
from .dependencies import *
from .health import health_check

__all__ = [
    'app',
    'health_check'
]