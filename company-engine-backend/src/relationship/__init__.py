# __init__.py
"""
Relationship Extraction Package

This package provides functionality for extracting and managing
relationships between entities.

Main components:
- RelationshipExtractor: Extract relationships from text
- EntityRelationship: Data model for relationships
- RelationshipType: Standard relationship types
"""

from .relationship_models import EntityRelationship, RelationshipType
from .relationship_extractor import RelationshipExtractor

__all__ = [
    "RelationshipExtractor",
    "EntityRelationship",
    "RelationshipType",
]
