"""
StudioFlow - Modern Video Production Pipeline
A Git-style CLI for automated video workflows
"""

__version__ = "2.0.0"
__author__ = "StudioFlow Team"

from .core.config import Config
from .core.project import Project

__all__ = ["Config", "Project", "__version__"]