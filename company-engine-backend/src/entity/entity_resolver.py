# entity_resolver.py
"""
Entity Resolver - The Core Matching Logic

This is the "brain" of entity resolution. It takes raw text like "Open AI"
and figures out:
1. What canonical entity it refers to → "OpenAI"
2. How confident we are → 90%
3. Why we matched it → "alias match"

MATCHING STRATEGIES (in order of confidence):
1. Exact match: "OpenAI" → "OpenAI" (99% confidence)
2. Known alias: "Open AI" → "OpenAI" (90% confidence)
3. Fuzzy match: "OpenAl" → "OpenAI" (85% confidence)
4. Pattern match: "@openai" → "OpenAI" (85% confidence)
5. Semantic match: "company behind ChatGPT" → "OpenAI" (70% confidence)
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Import our models (handle both relative and absolute imports)
try:
    from .entity_models import EntityMention, CanonicalEntity
except ImportError:
    from entity_models import EntityMention, CanonicalEntity


class EntityResolver:
    """
    Resolves different text mentions to canonical entities.

    Usage:
        resolver = EntityResolver()

        # Process mentions
        canonical, confidence = resolver.resolve("Open AI", context="...", source_info={...})
        # Returns: ("OpenAI", 0.90)

        # Get all resolved entities
        entities = resolver.get_all_entities()
    """

    # =========================================================================
    # KNOWN ALIASES - Pre-defined mappings for common entities
    # =========================================================================
    # Format: 'canonical_name_lowercase': ['alias1', 'alias2', ...]

    KNOWN_ALIASES = {
        # AI Companies
        "openai": [
            "openai",
            "open ai",
            "open-ai",
            "open_ai",
            "@openai",
            "#openai",
            "company behind chatgpt",
            "chatgpt maker",
            "chatgpt company",
            "maker of chatgpt",
            "creators of chatgpt",
        ],
        "anthropic": [
            "anthropic",
            "@anthropic",
            "anthropic ai",
            "company behind claude",
            "claude maker",
            "claude company",
            "maker of claude",
            "creators of claude",
        ],
        "google": [
            "google",
            "alphabet",
            "@google",
            "googl",
            "google ai",
            "google deepmind",
            "deepmind",
        ],
        "microsoft": [
            "microsoft",
            "msft",
            "@microsoft",
            "ms",
            "microsoft ai",
            "msft ai",
        ],
        "meta": [
            "meta",
            "facebook",
            "fb",
            "@meta",
            "@facebook",
            "meta ai",
            "facebook ai",
        ],
        # AI Products
        "chatgpt": [
            "chatgpt",
            "chat gpt",
            "chat-gpt",
            "chat_gpt",
            "@chatgpt",
            "gpt chat",
            "chatgtp",  # common typo
        ],
        "gpt-4": [
            "gpt-4",
            "gpt4",
            "gpt 4",
            "gpt-4o",
            "gpt4o",
            "gpt-4 turbo",
            "gpt4 turbo",
        ],
        "gpt-3": ["gpt-3", "gpt3", "gpt 3", "gpt-3.5", "gpt3.5"],
        "dall-e": [
            "dall-e",
            "dalle",
            "dall e",
            "dall-e 2",
            "dall-e 3",
            "dalle2",
            "dalle3",
        ],
        "claude": [
            "claude",
            "claude ai",
            "claude 2",
            "claude 3",
            "claude sonnet",
            "claude opus",
            "claude haiku",
            "@claudeai",
        ],
        "gemini": [
            "gemini",
            "google gemini",
            "gemini pro",
            "gemini ultra",
            "bard",  # old name
        ],
        "copilot": [
            "copilot",
            "github copilot",
            "ms copilot",
            "microsoft copilot",
            "bing copilot",
            "windows copilot",
        ],
        "midjourney": ["midjourney", "mid journey", "mid-journey", "mj", "@midjourney"],
        "stable diffusion": [
            "stable diffusion",
            "stablediffusion",
            "sd",
            "sdxl",
            "sd xl",
            "stability ai",
        ],
        # People
        "sam altman": [
            "sam altman",
            "altman",
            "@sama",
            "sama",
            "openai ceo",
            "ceo of openai",
        ],
        "elon musk": [
            "elon musk",
            "elon",
            "musk",
            "@elonmusk",
            "tesla ceo",
            "spacex ceo",
        ],
        "satya nadella": [
            "satya nadella",
            "nadella",
            "satya",
            "microsoft ceo",
            "ceo of microsoft",
        ],
        "sundar pichai": [
            "sundar pichai",
            "pichai",
            "sundar",
            "google ceo",
            "ceo of google",
            "alphabet ceo",
        ],
        "mark zuckerberg": [
            "mark zuckerberg",
            "zuckerberg",
            "zuck",
            "meta ceo",
            "facebook ceo",
            "ceo of meta",
        ],
        "dario amodei": [
            "dario amodei",
            "dario",
            "amodei",
            "anthropic ceo",
            "ceo of anthropic",
        ],
    }

    # Entity type mapping
    ENTITY_TYPES = {
        "openai": "ORG",
        "anthropic": "ORG",
        "google": "ORG",
        "microsoft": "ORG",
        "meta": "ORG",
        "chatgpt": "PRODUCT",
        "gpt-4": "PRODUCT",
        "gpt-3": "PRODUCT",
        "dall-e": "PRODUCT",
        "claude": "PRODUCT",
        "gemini": "PRODUCT",
        "copilot": "PRODUCT",
        "midjourney": "PRODUCT",
        "stable diffusion": "PRODUCT",
        "sam altman": "PERSON",
        "elon musk": "PERSON",
        "satya nadella": "PERSON",
        "sundar pichai": "PERSON",
        "mark zuckerberg": "PERSON",
        "dario amodei": "PERSON",
    }

    # Proper capitalization for canonical names
    CANONICAL_NAMES = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google",
        "microsoft": "Microsoft",
        "meta": "Meta",
        "chatgpt": "ChatGPT",
        "gpt-4": "GPT-4",
        "gpt-3": "GPT-3",
        "dall-e": "DALL-E",
        "claude": "Claude",
        "gemini": "Gemini",
        "copilot": "Copilot",
        "midjourney": "Midjourney",
        "stable diffusion": "Stable Diffusion",
        "sam altman": "Sam Altman",
        "elon musk": "Elon Musk",
        "satya nadella": "Satya Nadella",
        "sundar pichai": "Sundar Pichai",
        "mark zuckerberg": "Mark Zuckerberg",
        "dario amodei": "Dario Amodei",
    }

    def __init__(self):
        """Initialize the resolver with empty entity storage"""
        # Storage for resolved entities: canonical_name_lower -> CanonicalEntity
        self.entities: Dict[str, CanonicalEntity] = {}

        # Build reverse lookup: alias -> canonical_name_lower
        self._alias_lookup: Dict[str, str] = {}
        for canonical, aliases in self.KNOWN_ALIASES.items():
            for alias in aliases:
                self._alias_lookup[alias.lower()] = canonical

    # =========================================================================
    # MAIN RESOLVE METHOD
    # =========================================================================

    def resolve(
        self, raw_text: str, context: str = "", source_info: dict = None
    ) -> Tuple[str, float]:
        """
        Resolve a raw text mention to a canonical entity.

        This is the main method you call!

        Args:
            raw_text: The mention text found (e.g., "Open AI", "@openai")
            context: Surrounding text for context
            source_info: Dict with 'post_id', 'post_title', 'subreddit', 'url'

        Returns:
            Tuple of (canonical_name, confidence_score)
            Example: ("OpenAI", 0.90)
        """
        if not raw_text or not raw_text.strip():
            return None, 0.0

        # Normalize the input
        normalized = self._normalize(raw_text)

        if not normalized:
            return None, 0.0

        # Try matching strategies in order of confidence

        # Strategy 1: Exact match in known aliases (highest confidence)
        if normalized in self._alias_lookup:
            canonical_key = self._alias_lookup[normalized]
            canonical_name = self.CANONICAL_NAMES.get(
                canonical_key, canonical_key.title()
            )
            confidence = self._calculate_confidence(raw_text, canonical_name, "alias")

            self._add_mention(
                canonical_key, raw_text, confidence, "alias", context, source_info
            )
            return canonical_name, confidence

        # Strategy 2: Fuzzy match against known entities
        best_match, fuzzy_score = self._fuzzy_match(normalized)
        if best_match and fuzzy_score >= 0.85:
            canonical_name = self.CANONICAL_NAMES.get(best_match, best_match.title())
            confidence = self._calculate_confidence(
                raw_text, canonical_name, "fuzzy", fuzzy_score
            )

            self._add_mention(
                best_match, raw_text, confidence, "fuzzy", context, source_info
            )
            return canonical_name, confidence

        # Strategy 3: Pattern matching (e.g., "@openai" format)
        pattern_match = self._pattern_match(raw_text)
        if pattern_match:
            canonical_key, confidence = pattern_match
            canonical_name = self.CANONICAL_NAMES.get(
                canonical_key, canonical_key.title()
            )

            self._add_mention(
                canonical_key, raw_text, confidence, "pattern", context, source_info
            )
            return canonical_name, confidence

        # Strategy 4: No match found - create new entity
        # Only create if it looks like an entity (capitalized, reasonable length)
        if self._looks_like_entity(raw_text):
            canonical_name = self._to_title_case(raw_text)
            canonical_key = canonical_name.lower()
            confidence = 0.60  # Lower confidence for new/unknown entities

            self._create_new_entity(canonical_key, canonical_name, raw_text)
            self._add_mention(
                canonical_key, raw_text, confidence, "new", context, source_info
            )
            return canonical_name, confidence

        return None, 0.0

    # =========================================================================
    # MATCHING STRATEGIES
    # =========================================================================

    def _normalize(self, text: str) -> str:
        """
        Normalize text for comparison.

        "Open AI" → "open ai"
        "@OpenAI" → "openai"
        "DALL-E" → "dall-e"
        """
        text = text.lower().strip()
        text = re.sub(r"^[@#]", "", text)  # Remove leading @ or #
        text = re.sub(r"[^\w\s-]", "", text)  # Remove punctuation except hyphen
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        return text.strip()

    def _fuzzy_match(self, normalized: str) -> Tuple[Optional[str], float]:
        """
        Find best fuzzy match among known entities.

        Uses SequenceMatcher to find similar strings.
        "openal" → "openai" with 0.91 similarity
        """
        best_match = None
        best_score = 0.0

        # Check against all known aliases
        for alias, canonical in self._alias_lookup.items():
            score = SequenceMatcher(None, normalized, alias).ratio()
            if score > best_score:
                best_score = score
                best_match = canonical

        return best_match, best_score

    def _pattern_match(self, raw_text: str) -> Optional[Tuple[str, float]]:
        """
        Match based on patterns like @mentions, hashtags, etc.

        "@openai" → ("openai", 0.85)
        "#ChatGPT" → ("chatgpt", 0.85)
        """
        # Pattern: @mention or #hashtag
        match = re.match(r"^[@#](\w+)$", raw_text.strip())
        if match:
            handle = match.group(1).lower()
            if handle in self._alias_lookup:
                return self._alias_lookup[handle], 0.85

        return None

    def _looks_like_entity(self, text: str) -> bool:
        """
        Check if text looks like an entity (worth creating a new one).

        Criteria:
        - At least 2 characters
        - Not all lowercase (entities usually have capitals)
        - Not a common word
        """
        if len(text) < 2:
            return False

        # Check if it has at least one capital letter
        if not any(c.isupper() for c in text):
            return False

        # Check if it's not a common word
        common_words = {
            "the",
            "this",
            "that",
            "what",
            "when",
            "where",
            "which",
            "who",
            "how",
            "why",
            "can",
            "could",
            "would",
            "should",
            "will",
            "just",
            "also",
            "than",
            "then",
            "now",
            "here",
            "there",
            "very",
            "really",
            "today",
            "yesterday",
            "tomorrow",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        }
        if text.lower() in common_words:
            return False

        return True

    def _to_title_case(self, text: str) -> str:
        """Convert to proper title case"""
        # Handle special cases
        special_cases = ["AI", "API", "CEO", "CTO", "US", "UK", "EU"]

        words = text.split()
        result = []

        for word in words:
            upper_word = word.upper()
            if upper_word in special_cases:
                result.append(upper_word)
            else:
                result.append(word.capitalize())

        return " ".join(result)

    # =========================================================================
    # CONFIDENCE CALCULATION
    # =========================================================================

    def _calculate_confidence(
        self, raw: str, canonical: str, method: str, fuzzy_score: float = None
    ) -> float:
        """
        Calculate confidence score based on how we matched.

        Confidence levels:
        - Exact match: 0.99
        - Known alias: 0.85-0.95 (depends on similarity)
        - Fuzzy match: 0.70-0.85 (depends on fuzzy score)
        - Pattern match: 0.85
        - New entity: 0.60
        """
        raw_norm = self._normalize(raw)
        canonical_norm = self._normalize(canonical)

        # Exact match
        if raw_norm == canonical_norm:
            return 0.99

        # Based on method
        if method == "alias":
            # Higher confidence if very similar to canonical
            similarity = SequenceMatcher(None, raw_norm, canonical_norm).ratio()
            return max(0.85, min(0.95, similarity + 0.1))

        if method == "fuzzy" and fuzzy_score:
            return round(fuzzy_score * 0.90, 2)  # Scale down slightly

        if method == "pattern":
            return 0.85

        if method == "new":
            return 0.60

        return 0.70  # Default

    # =========================================================================
    # ENTITY STORAGE
    # =========================================================================

    def _create_new_entity(
        self, canonical_key: str, canonical_name: str, first_mention: str
    ):
        """Create a new canonical entity"""
        entity_type = self.ENTITY_TYPES.get(
            canonical_key, self._guess_entity_type(canonical_name)
        )

        self.entities[canonical_key] = CanonicalEntity(
            canonical_name=canonical_name,
            entity_type=entity_type,
            aliases=[self._normalize(first_mention)],
        )

    def _add_mention(
        self,
        canonical_key: str,
        raw_text: str,
        confidence: float,
        match_method: str,
        context: str,
        source_info: dict,
    ):
        """Add a mention to an entity"""
        # Create entity if it doesn't exist
        if canonical_key not in self.entities:
            canonical_name = self.CANONICAL_NAMES.get(
                canonical_key, canonical_key.title()
            )
            entity_type = self.ENTITY_TYPES.get(canonical_key, "ORG")

            self.entities[canonical_key] = CanonicalEntity(
                canonical_name=canonical_name, entity_type=entity_type, aliases=[]
            )

        entity = self.entities[canonical_key]

        # Add alias if not already present
        normalized = self._normalize(raw_text)
        if normalized and normalized not in entity.aliases:
            entity.aliases.append(normalized)

        # Create mention
        source_info = source_info or {}
        mention = EntityMention(
            raw_text=raw_text,
            canonical_name=entity.canonical_name,
            confidence=confidence,
            match_method=match_method,
            context=context[:300] if context else "",
            source_post_id=source_info.get("post_id", ""),
            source_post_title=source_info.get("post_title", ""),
            source_subreddit=source_info.get("subreddit", ""),
            source_url=source_info.get("url", ""),
        )

        entity.mentions.append(mention)

    def _guess_entity_type(self, name: str) -> str:
        """Guess entity type based on name patterns"""
        name_lower = name.lower()

        # Product indicators
        product_indicators = ["gpt", "ai", "bot", "app", "api", "sdk", "model"]
        if any(indicator in name_lower for indicator in product_indicators):
            return "PRODUCT"

        # Person indicators (First Last pattern)
        words = name.split()
        if len(words) == 2:
            if all(word[0].isupper() and word[1:].islower() for word in words if word):
                return "PERSON"

        return "ORG"  # Default to organization

    # =========================================================================
    # RETRIEVAL METHODS
    # =========================================================================

    def get_all_entities(self) -> List[CanonicalEntity]:
        """Get all resolved entities, sorted by mention count"""
        entities = list(self.entities.values())
        entities.sort(key=lambda e: e.mention_count, reverse=True)
        return entities

    def get_entities_by_type(self, entity_type: str) -> List[CanonicalEntity]:
        """Get entities filtered by type (ORG, PERSON, PRODUCT)"""
        return [
            e
            for e in self.get_all_entities()
            if e.entity_type.upper() == entity_type.upper()
        ]

    def get_entity(self, name: str) -> Optional[CanonicalEntity]:
        """Get a specific entity by name"""
        normalized = self._normalize(name)

        # Direct lookup
        if normalized in self.entities:
            return self.entities[normalized]

        # Check aliases
        if normalized in self._alias_lookup:
            canonical_key = self._alias_lookup[normalized]
            return self.entities.get(canonical_key)

        return None

    def get_summary(self) -> dict:
        """Get summary statistics"""
        entities = self.get_all_entities()

        total_mentions = sum(e.mention_count for e in entities)
        by_type = defaultdict(int)
        for e in entities:
            by_type[e.entity_type] += 1

        return {
            "total_entities": len(entities),
            "total_mentions": total_mentions,
            "by_type": dict(by_type),
            "top_entities": [
                {"name": e.canonical_name, "mentions": e.mention_count}
                for e in entities[:10]
            ],
        }


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("Testing Entity Resolver...")
    print("=" * 60)

    resolver = EntityResolver()

    # Test cases
    test_cases = [
        ("OpenAI", "...OpenAI announced new features..."),
        ("Open AI", "...I think Open AI is great..."),
        ("openai", "...openai released an update..."),
        ("@openai", "...check out @openai on Twitter..."),
        ("the company behind ChatGPT", "...the company behind ChatGPT is hiring..."),
        ("ChatGPT", "...ChatGPT helped me write this..."),
        ("chat gpt", "...I use chat gpt every day..."),
        ("Sam Altman", "...Sam Altman said in an interview..."),
        ("Altman", "...Altman tweeted about AI safety..."),
        ("GPT-4", "...GPT-4 is very capable..."),
        ("gpt4", "...I tested gpt4 yesterday..."),
        ("Unknown Company", "...Unknown Company launched today..."),  # New entity
    ]

    print("\nResolving entities:")
    print("-" * 60)

    for raw_text, context in test_cases:
        canonical, confidence = resolver.resolve(
            raw_text, context, {"subreddit": "test"}
        )
        print(f"  '{raw_text}'")
        print(f"    → {canonical} (confidence: {confidence:.0%})")
        print()

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    summary = resolver.get_summary()
    print(f"Total entities: {summary['total_entities']}")
    print(f"Total mentions: {summary['total_mentions']}")
    print(f"By type: {summary['by_type']}")

    print("\nTop entities:")
    for item in summary["top_entities"]:
        print(f"  • {item['name']}: {item['mentions']} mentions")

    # Show details for OpenAI
    openai = resolver.get_entity("OpenAI")
    if openai:
        print(f"\n\nDetails for '{openai.canonical_name}':")
        print(f"  Type: {openai.entity_type}")
        print(f"  Aliases: {openai.aliases}")
        print(f"  Mentions: {openai.mention_count}")
        print(f"  Avg confidence: {openai.avg_confidence:.0%}")

    print("\n✅ Entity resolver working!")
