# entity_models.py
"""
Data models for Entity Resolution.

This file defines the "shape" of our data - what information we store
about each entity and each mention.

Two main classes:
1. EntityMention - A single mention of an entity (e.g., "Open AI" in a post)
2. CanonicalEntity - The unified entity with all its mentions grouped together
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class EntityMention:
    """
    Represents a single mention of an entity in text.

    Example:
        In the post "I think Open AI is doing great work...",
        we found "Open AI" which refers to the company OpenAI.

        EntityMention(
            raw_text="Open AI",           # What we found in the text
            canonical_name="OpenAI",       # What it actually refers to
            confidence=0.90,               # How sure we are (90%)
            context="...I think Open AI is doing great work...",
            source_subreddit="MachineLearning",
            ...
        )
    """

    # What we found
    raw_text: str  # The exact text found: "Open AI", "@openai", etc.
    canonical_name: str  # The standardized name: "OpenAI"

    # How confident are we?
    confidence: float  # 0.0 to 1.0 (0% to 100%)
    match_method: str = ""  # How we matched: "exact", "alias", "fuzzy", "pattern"

    # Where we found it
    context: str = ""  # Surrounding text: "...I think Open AI is doing..."
    source_post_id: str = ""  # Reddit post ID
    source_post_title: str = ""  # Post title
    source_subreddit: str = ""  # Which subreddit
    source_url: str = ""  # Link to the post

    # When we found it
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary (useful for JSON/API responses)"""
        return {
            "raw_text": self.raw_text,
            "canonical_name": self.canonical_name,
            "confidence": self.confidence,
            "confidence_percent": f"{self.confidence:.0%}",
            "match_method": self.match_method,
            "context": self.context,
            "source": {
                "post_id": self.source_post_id,
                "post_title": self.source_post_title,
                "subreddit": self.source_subreddit,
                "url": self.source_url,
            },
        }


@dataclass
class CanonicalEntity:
    """
    Represents a unified entity with all its variations grouped together.

    Example:
        CanonicalEntity(
            canonical_name="OpenAI",
            entity_type="ORG",
            aliases=["openai", "open ai", "open-ai", "@openai"],
            mentions=[...list of EntityMention objects...],
        )

    This groups together:
    - "OpenAI" (exact match)
    - "Open AI" (space variation)
    - "openai" (lowercase)
    - "@openai" (social handle)

    All referring to the same company!
    """

    # Identity
    canonical_name: str  # The official/standardized name: "OpenAI"
    entity_type: str  # "ORG", "PERSON", "PRODUCT"

    # All the different ways people write this entity
    aliases: List[str] = field(default_factory=list)

    # All mentions found
    mentions: List[EntityMention] = field(default_factory=list)

    # Optional metadata
    description: str = ""  # Brief description
    related_entities: List[str] = field(
        default_factory=list
    )  # e.g., ["Sam Altman", "ChatGPT"]

    @property
    def mention_count(self) -> int:
        """Total number of times this entity was mentioned"""
        return len(self.mentions)

    @property
    def avg_confidence(self) -> float:
        """Average confidence across all mentions"""
        if not self.mentions:
            return 0.0
        return sum(m.confidence for m in self.mentions) / len(self.mentions)

    @property
    def subreddits_mentioned_in(self) -> List[str]:
        """List of subreddits where this entity was mentioned"""
        subreddits = set()
        for mention in self.mentions:
            if mention.source_subreddit:
                subreddits.add(mention.source_subreddit)
        return list(subreddits)

    def to_dict(self) -> dict:
        """Convert to dictionary (useful for JSON/API responses)"""
        return {
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "aliases": self.aliases,
            "mention_count": self.mention_count,
            "avg_confidence": round(self.avg_confidence, 2),
            "subreddits": self.subreddits_mentioned_in,
            "mentions": [
                m.to_dict() for m in self.mentions[:10]
            ],  # Limit to 10 for API
        }

    def get_mention_summary(self) -> dict:
        """Get summary of mentions by confidence level"""
        high_confidence = [m for m in self.mentions if m.confidence >= 0.9]
        medium_confidence = [m for m in self.mentions if 0.7 <= m.confidence < 0.9]
        low_confidence = [m for m in self.mentions if m.confidence < 0.7]

        return {
            "total": len(self.mentions),
            "high_confidence": len(high_confidence),
            "medium_confidence": len(medium_confidence),
            "low_confidence": len(low_confidence),
        }


# =============================================================================
# Helper function to create entities easily
# =============================================================================


def create_entity(
    name: str, entity_type: str = "ORG", aliases: List[str] = None
) -> CanonicalEntity:
    """
    Factory function to create a CanonicalEntity easily.

    Usage:
        openai = create_entity("OpenAI", "ORG", ["open ai", "openai", "@openai"])
    """
    return CanonicalEntity(
        canonical_name=name, entity_type=entity_type, aliases=aliases or [name.lower()]
    )


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    # Test creating entities
    print("Testing Entity Models...")

    # Create a canonical entity
    openai = CanonicalEntity(
        canonical_name="OpenAI",
        entity_type="ORG",
        aliases=["openai", "open ai", "@openai"],
    )

    # Add some mentions
    openai.mentions.append(
        EntityMention(
            raw_text="OpenAI",
            canonical_name="OpenAI",
            confidence=0.99,
            match_method="exact",
            context="...I think OpenAI is doing great work...",
            source_subreddit="MachineLearning",
        )
    )

    openai.mentions.append(
        EntityMention(
            raw_text="Open AI",
            canonical_name="OpenAI",
            confidence=0.90,
            match_method="alias",
            context="...Open AI just released a new model...",
            source_subreddit="technology",
        )
    )

    # Print info
    print(f"\nEntity: {openai.canonical_name}")
    print(f"Type: {openai.entity_type}")
    print(f"Aliases: {openai.aliases}")
    print(f"Mention count: {openai.mention_count}")
    print(f"Avg confidence: {openai.avg_confidence:.0%}")
    print(f"Subreddits: {openai.subreddits_mentioned_in}")
    print(f"\nMention summary: {openai.get_mention_summary()}")

    print("\n✅ Entity models working!")
