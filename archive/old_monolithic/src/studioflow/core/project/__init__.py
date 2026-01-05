"""
StudioFlow Project Management Module
"""

from .generator import StudioFlowGenerator
from .validators import ProjectValidator

# Maintain backward compatibility
ProjectGenerator = StudioFlowGenerator

__all__ = [
    'StudioFlowGenerator',
    'ProjectGenerator',  # Backward compatibility
    'ProjectValidator'
]