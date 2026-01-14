# relationship_models.py
"""
Data models for Entity Relationships.

This file defines the structure for storing relationships between entities.

Example:
    EntityRelationship(
        source_entity="Sam Altman",
        relationship_type="ceo",
        target_entity="OpenAI",
        confidence=0.92,
        evidence=["Sam Altman announced...", "CEO Sam Altman said..."],
        source_posts=["post1", "post2"]
    )
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class EntityRelationship:
    """
    Represents a relationship between two entities.

    Example relationships:
    - (Sam Altman, ceo, OpenAI)
    - (Microsoft, investor, OpenAI)
    - (ChatGPT, product_of, OpenAI)
    """

    # The relationship triple
    source_entity: str          # "Sam Altman"
    relationship_type: str      # "ceo" (from standard types below)
    target_entity: str          # "OpenAI"

    # Confidence and evidence
    confidence: float           # 0.0 to 1.0 (how confident we are)
    evidence: List[str] = field(default_factory=list)  # Text snippets showing this relationship

    # Source tracking
    source_posts: List[str] = field(default_factory=list)  # Post IDs where found
    source_subreddits: List[str] = field(default_factory=list)  # Subreddits where found

    # Metadata
    extraction_method: str = ""  # "dependency_parse", "pattern_match", "co_occurrence"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def evidence_count(self) -> int:
        """Number of evidence snippets supporting this relationship"""
        return len(self.evidence)

    @property
    def mention_count(self) -> int:
        """Number of posts mentioning this relationship"""
        return len(self.source_posts)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON/API responses"""
        return {
            "source": self.source_entity,
            "relationship": self.relationship_type,
            "target": self.target_entity,
            "confidence": round(self.confidence, 2),
            "confidence_percent": f"{self.confidence:.0%}",
            "evidence_count": self.evidence_count,
            "mention_count": self.mention_count,
            "extraction_method": self.extraction_method,
            "evidence_sample": self.evidence[:3],  # First 3 pieces of evidence
            "subreddits": list(set(self.source_subreddits))[:5],  # Unique, first 5
        }


# =============================================================================
# Standard Relationship Types (Google Knowledge Graph compatible)
# =============================================================================

class RelationshipType:
    """
    Standard relationship types following Google Knowledge Graph conventions.

    These are the canonical relationship types we extract.
    """

    # Person → Organization
    FOUNDER = "founder"             # Person founded the organization
    CO_FOUNDER = "co_founder"       # Person co-founded the organization
    CEO = "ceo"                     # Person is CEO of organization
    CTO = "cto"                     # Person is CTO of organization
    EMPLOYEE = "employee"           # Person works at organization
    BOARD_MEMBER = "board_member"   # Person is on the board
    ADVISOR = "advisor"             # Person advises the organization
    ALUMNI_OF = "alumni_of"         # Person formerly worked there

    # Organization → Organization
    INVESTOR = "investor"           # Org invested in another org
    PARENT_COMPANY = "parent_company"  # Parent company relationship
    SUBSIDIARY = "subsidiary"       # Subsidiary relationship
    PARTNER = "partner"             # Partnership
    ACQUIRED_BY = "acquired_by"     # Acquisition relationship
    COMPETITOR = "competitor"       # Competitive relationship

    # Organization → Product
    PRODUCT_OF = "product_of"       # Product belongs to organization
    CREATED = "created"             # Organization created the product

    # Person → Person
    CO_WORKER = "co_worker"         # Work together
    OPPONENT = "opponent"           # Opposing/critical relationship

    # Sentiment relationships
    SUPPORTER = "supporter"         # Supports/advocates for
    CRITIC = "critic"              # Criticizes

    @classmethod
    def all_types(cls) -> List[str]:
        """Get all relationship types"""
        return [
            cls.FOUNDER, cls.CO_FOUNDER, cls.CEO, cls.CTO,
            cls.EMPLOYEE, cls.BOARD_MEMBER, cls.ADVISOR, cls.ALUMNI_OF,
            cls.INVESTOR, cls.PARENT_COMPANY, cls.SUBSIDIARY, cls.PARTNER,
            cls.ACQUIRED_BY, cls.COMPETITOR,
            cls.PRODUCT_OF, cls.CREATED,
            cls.CO_WORKER, cls.OPPONENT,
            cls.SUPPORTER, cls.CRITIC
        ]

    @classmethod
    def person_org_types(cls) -> List[str]:
        """Relationship types between person and organization"""
        return [
            cls.FOUNDER, cls.CO_FOUNDER, cls.CEO, cls.CTO,
            cls.EMPLOYEE, cls.BOARD_MEMBER, cls.ADVISOR, cls.ALUMNI_OF
        ]

    @classmethod
    def org_org_types(cls) -> List[str]:
        """Relationship types between organizations"""
        return [
            cls.INVESTOR, cls.PARENT_COMPANY, cls.SUBSIDIARY,
            cls.PARTNER, cls.ACQUIRED_BY, cls.COMPETITOR
        ]

    @classmethod
    def org_product_types(cls) -> List[str]:
        """Relationship types between organization and product"""
        return [cls.PRODUCT_OF, cls.CREATED]


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("Testing Relationship Models...")
    print("=" * 60)

    # Create a relationship
    rel = EntityRelationship(
        source_entity="Sam Altman",
        relationship_type=RelationshipType.CEO,
        target_entity="OpenAI",
        confidence=0.92,
        evidence=[
            "Sam Altman announced new features",
            "OpenAI CEO Sam Altman said in an interview",
            "Sam Altman, who leads OpenAI, tweeted"
        ],
        source_posts=["post1", "post2", "post3"],
        source_subreddits=["MachineLearning", "OpenAI", "technology"],
        extraction_method="pattern_match"
    )

    print(f"\nRelationship: {rel.source_entity} → {rel.relationship_type} → {rel.target_entity}")
    print(f"Confidence: {rel.confidence:.0%}")
    print(f"Evidence count: {rel.evidence_count}")
    print(f"Mention count: {rel.mention_count}")
    print(f"Method: {rel.extraction_method}")

    print(f"\nEvidence:")
    for i, evidence in enumerate(rel.evidence, 1):
        print(f"  {i}. {evidence}")

    print(f"\nAs dict:")
    import json
    print(json.dumps(rel.to_dict(), indent=2))

    print(f"\n\nAll relationship types ({len(RelationshipType.all_types())}):")
    for rel_type in RelationshipType.all_types():
        print(f"  • {rel_type}")

    print("\n✅ Relationship models working!")
