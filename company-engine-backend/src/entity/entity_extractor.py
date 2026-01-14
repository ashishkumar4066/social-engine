# entity_extractor.py
"""
Entity Extractor - Extract and Resolve Entities from Reddit Posts

This module:
1. Takes Reddit posts as input
2. Extracts entity mentions using spaCy NER (or regex fallback)
3. Resolves mentions to canonical entities using EntityResolver
4. Returns structured entity data

Usage:
    extractor = EntityExtractor()

    # Process posts
    results = extractor.extract_from_posts(posts)

    # Get entities
    all_entities = results.get_all_entities()
    organizations = results.get_entities_by_type('ORG')
"""

import re
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# Import our modules (handle both relative and absolute imports)
try:
    from .entity_resolver import EntityResolver
    from .entity_models import CanonicalEntity, EntityMention
except ImportError:
    from entity_resolver import EntityResolver
    from entity_models import CanonicalEntity, EntityMention

# Try to load spaCy (optional - we have regex fallback)
SPACY_AVAILABLE = False
nlp = None

try:
    import spacy

    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    print("✅ spaCy loaded - using NER for entity extraction")
except (ImportError, OSError) as e:
    print(f"⚠️ spaCy not available - using regex fallback")
    print(
        f"   Install with: pip install spacy && python -m spacy download en_core_web_sm"
    )


class EntityExtractor:
    """
    Extracts entities from Reddit posts and resolves them to canonical forms.

    Uses spaCy NER if available, otherwise falls back to regex patterns.
    """

    # Additional patterns to look for (beyond spaCy NER)
    ENTITY_PATTERNS = [
        # AI Products (with versions)
        r"\b(GPT-?\d+(?:\.\d+)?(?:\s*[Tt]urbo)?)\b",  # GPT-4, GPT-3.5, GPT4 Turbo
        r"\b(ChatGPT)\b",
        r"\b(DALL-?E(?:\s*\d)?)\b",  # DALL-E, DALLE, DALL-E 3
        r"\b(Claude(?:\s*\d)?(?:\s*(?:Opus|Sonnet|Haiku))?)\b",
        r"\b(Gemini(?:\s*(?:Pro|Ultra|Nano))?)\b",
        r"\b(Copilot)\b",
        r"\b(Midjourney|MidJourney)\b",
        r"\b(Stable\s*Diffusion|SDXL)\b",
        r"\b(LLaMA|Llama(?:\s*\d)?)\b",
        r"\b(Mistral(?:\s*\d+[Bb])?)\b",
        # Social handles
        r"(@\w{2,30})\b",  # @openai, @sama
        # Companies (explicit mentions)
        r"\b(OpenAI|Open\s*AI)\b",
        r"\b(Anthropic)\b",
        r"\b(DeepMind|Deep\s*Mind)\b",
        r"\b(Hugging\s*Face|HuggingFace)\b",
    ]

    def __init__(self, use_spacy: bool = True, company_context: dict = None):
        """
        Initialize the extractor.

        Args:
            use_spacy: Whether to use spaCy NER (if available)
            company_context: Dict with company info for relevance filtering:
                - company_name: Name of the company being analyzed
                - industry: Company's industry
                - keywords: List of relevant keywords
                - products: List of known products
        """
        self.resolver = EntityResolver()
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self.company_context = company_context or {}

        # Compile regex patterns
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.ENTITY_PATTERNS
        ]

        # Statistics
        self.stats = {
            "posts_processed": 0,
            "entities_found": 0,
            "spacy_extractions": 0,
            "regex_extractions": 0,
            "filtered_out": 0,
        }

    def extract_from_posts(self, posts: List[Dict]) -> EntityResolver:
        """
        Extract and resolve entities from a list of Reddit posts.

        Args:
            posts: List of post dicts with keys:
                   - 'id': Post ID
                   - 'title': Post title
                   - 'selftext' or 'body': Post body text
                   - 'subreddit': Subreddit name
                   - 'permalink' or 'url': Link to post

        Returns:
            EntityResolver with all resolved entities
        """
        print(f"\n{'='*60}")
        print(f"🔍 Entity Extraction")
        print(f"{'='*60}")
        print(f"   Posts to process: {len(posts)}")
        print(f"   Using: {'spaCy NER' if self.use_spacy else 'Regex patterns'}")

        for post in posts:
            self._process_post(post)

        # Print stats
        print(f"\n📊 Extraction Stats:")
        print(f"   Posts processed: {self.stats['posts_processed']}")
        print(f"   Total entities found: {self.stats['entities_found']}")
        if self.use_spacy:
            print(f"   From spaCy NER: {self.stats['spacy_extractions']}")
        print(f"   From regex: {self.stats['regex_extractions']}")
        if self.stats['filtered_out'] > 0:
            print(f"   Filtered as irrelevant: {self.stats['filtered_out']}")
        print(f"   Unique entities: {len(self.resolver.entities)}")

        return self.resolver

    def _process_post(self, post: Dict):
        """Process a single Reddit post"""
        self.stats["posts_processed"] += 1

        # Get text content
        title = post.get("title", "")
        body = post.get("selftext") or post.get("body") or ""
        full_text = f"{title} {body}"

        if not full_text.strip():
            return

        # Build source info
        source_info = {
            "post_id": post.get("id", ""),
            "post_title": title[:100],
            "subreddit": post.get("subreddit", ""),
            "url": post.get("permalink") or post.get("url", ""),
        }

        # Extract entities
        mentions = self._extract_entities(full_text)

        # Resolve each mention
        for entity_text, context in mentions:
            # Apply relevance filter before resolving
            if not self._is_relevant_entity(entity_text):
                self.stats["filtered_out"] += 1
                continue

            canonical, confidence = self.resolver.resolve(
                raw_text=entity_text, context=context, source_info=source_info
            )

            if canonical:
                self.stats["entities_found"] += 1

    def _extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract entity mentions from text.

        Returns list of (entity_text, context) tuples.
        """
        mentions = []

        # Method 1: spaCy NER (if available)
        if self.use_spacy:
            spacy_mentions = self._extract_with_spacy(text)
            mentions.extend(spacy_mentions)
            self.stats["spacy_extractions"] += len(spacy_mentions)

        # Method 2: Regex patterns (always run - catches things spaCy misses)
        regex_mentions = self._extract_with_regex(text)

        # Deduplicate (avoid adding same mention twice)
        seen = set(m[0].lower() for m in mentions)
        for mention in regex_mentions:
            if mention[0].lower() not in seen:
                mentions.append(mention)
                seen.add(mention[0].lower())
                self.stats["regex_extractions"] += 1

        return mentions

    def _extract_with_spacy(self, text: str) -> List[Tuple[str, str]]:
        """Extract entities using spaCy NER"""
        mentions = []

        # Limit text length for performance
        text = text[:10000]

        doc = nlp(text)

        for ent in doc.ents:
            # Only keep relevant entity types
            if ent.label_ in ["ORG", "PERSON", "PRODUCT", "WORK_OF_ART", "GPE"]:
                # Get context (surrounding text)
                start = max(0, ent.start_char - 50)
                end = min(len(text), ent.end_char + 50)
                context = f"...{text[start:end]}..."

                mentions.append((ent.text, context))

        return mentions

    def _extract_with_regex(self, text: str) -> List[Tuple[str, str]]:
        """Extract entities using regex patterns"""
        mentions = []
        seen_positions = set()  # Avoid overlapping matches

        for pattern in self._compiled_patterns:
            for match in pattern.finditer(text):
                # Check for overlap with existing matches
                match_range = set(range(match.start(), match.end()))
                if match_range & seen_positions:
                    continue

                seen_positions.update(match_range)

                entity_text = match.group(1) if match.groups() else match.group(0)

                # Get context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = f"...{text[start:end]}..."

                mentions.append((entity_text, context))

        return mentions

    def _is_relevant_entity(self, entity_text: str) -> bool:
        """
        Filter out irrelevant entities based on company context.

        Returns True if entity should be kept, False if it should be filtered out.
        """
        entity_lower = entity_text.lower().strip()

        # Always keep if no context provided (backward compatibility)
        if not self.company_context:
            return True

        # Filter 1: Exclude generic geographic locations (GPE entities)
        # These are rarely relevant for company intelligence
        geographic_noise = {
            "united states", "usa", "us", "uk", "united kingdom", "canada",
            "california", "new york", "texas", "florida", "washington",
            "san francisco", "los angeles", "seattle", "boston", "chicago",
            "europe", "asia", "africa", "america", "china", "india", "japan"
        }
        if entity_lower in geographic_noise:
            return False

        # Filter 2: Exclude very short entities (likely noise)
        if len(entity_text) <= 2:
            return False

        # Filter 3: Exclude common entertainment/pop culture that's not relevant
        # (unless it's in the company's industry)
        industry = self.company_context.get("industry", "").lower()
        entertainment_noise = {
            "pokemon", "pokémon", "stargate", "star wars", "marvel", "dc comics",
            "disney", "netflix", "hbo", "game of thrones", "lord of the rings"
        }

        # Only filter entertainment if NOT in entertainment/gaming/media industry
        if entity_lower in entertainment_noise:
            if not any(term in industry for term in ["entertainment", "gaming", "media", "content"]):
                return False

        # Filter 4: Exclude common noise words that spaCy sometimes flags
        noise_words = {
            "ps", "pps", "edit", "update", "tldr", "tl;dr",
            "ama", "eli5", "fyi", "btw", "imo", "imho",
            "reddit", "subreddit", "upvote", "downvote",
            "the catfather", "the power of the internet"
        }
        if entity_lower in noise_words:
            return False

        # Filter 5: Exclude random service platforms (unless analyzing them)
        company_name = self.company_context.get("company_name", "").lower()
        service_platforms = {
            "fiverr", "fivver", "upwork", "freelancer",
            "churu"  # Common cat treat brand that appears in random contexts
        }
        if entity_lower in service_platforms and entity_lower not in company_name:
            return False

        # Filter 6: Keep if entity is related to company context
        # Check against company keywords, products, etc.
        keywords = self.company_context.get("keywords", [])
        products = self.company_context.get("products", [])

        # Build relevance set (lowercase)
        relevance_set = set()
        relevance_set.add(company_name)
        relevance_set.update(kw.lower() for kw in keywords)
        relevance_set.update(p.lower() for p in products)

        # Known tech/AI companies and products - always relevant for tech analysis
        tech_entities = {
            "openai", "anthropic", "google", "microsoft", "meta", "apple",
            "amazon", "tesla", "nvidia", "intel", "amd",
            "chatgpt", "gpt", "claude", "gemini", "copilot", "dall-e",
            "github", "stackoverflow", "twitter", "x", "facebook", "instagram",
            "sam altman", "elon musk", "satya nadella", "sundar pichai",
            "mark zuckerberg", "jeff bezos", "tim cook", "jensen huang"
        }

        # Keep if it's a known tech entity (for tech companies)
        if "ai" in industry or "tech" in industry or "software" in industry:
            if any(te in entity_lower for te in tech_entities):
                return True

        # Keep if entity matches or contains company keywords
        for keyword in relevance_set:
            if keyword and (keyword in entity_lower or entity_lower in keyword):
                return True

        # Filter 7: For entities we haven't specifically whitelisted,
        # be more conservative - only keep if they appear to be companies/products
        # (i.e., proper capitalization, not common words)

        # If it's all lowercase, probably not a company/product
        if entity_text.islower():
            return False

        # Default: Keep the entity if it passed all filters
        return True

    # =========================================================================
    # Convenience methods that delegate to resolver
    # =========================================================================

    def get_all_entities(self) -> List[CanonicalEntity]:
        """Get all resolved entities"""
        return self.resolver.get_all_entities()

    def get_entities_by_type(self, entity_type: str) -> List[CanonicalEntity]:
        """Get entities by type (ORG, PERSON, PRODUCT)"""
        return self.resolver.get_entities_by_type(entity_type)

    def get_entity(self, name: str) -> Optional[CanonicalEntity]:
        """Get a specific entity by name"""
        return self.resolver.get_entity(name)

    def get_summary(self) -> dict:
        """Get extraction summary"""
        resolver_summary = self.resolver.get_summary()
        return {**resolver_summary, "extraction_stats": self.stats}


# =============================================================================
# Standalone function for easy use
# =============================================================================


def extract_entities(posts: List[Dict]) -> Dict:
    """
    Convenience function to extract entities from posts.

    Args:
        posts: List of Reddit post dicts

    Returns:
        Dict with 'entities', 'summary', and entity lists by type
    """
    extractor = EntityExtractor()
    extractor.extract_from_posts(posts)

    return {
        "all_entities": extractor.get_all_entities(),
        "organizations": extractor.get_entities_by_type("ORG"),
        "people": extractor.get_entities_by_type("PERSON"),
        "products": extractor.get_entities_by_type("PRODUCT"),
        "summary": extractor.get_summary(),
    }


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("\nTesting Entity Extractor...")
    print("=" * 60)

    # Sample Reddit posts (mock data)
    sample_posts = [
        {
            "id": "post1",
            "title": "OpenAI releases GPT-4 Turbo with improved capabilities",
            "selftext": "Sam Altman announced that OpenAI has released GPT-4 Turbo. The new model is faster and cheaper than the previous version. ChatGPT users will get access soon.",
            "subreddit": "MachineLearning",
            "permalink": "/r/MachineLearning/comments/post1",
        },
        {
            "id": "post2",
            "title": "Comparing ChatGPT vs Claude vs Gemini",
            "selftext": "I tested chat gpt, Claude 3, and Google Gemini Pro. The company behind ChatGPT (Open AI) seems to be ahead, but Anthropic is catching up fast.",
            "subreddit": "artificial",
            "permalink": "/r/artificial/comments/post2",
        },
        {
            "id": "post3",
            "title": "Elon Musk criticizes OpenAI again",
            "selftext": "@elonmusk tweeted about @OpenAI again. Musk says the company has strayed from its original mission. Altman has not responded yet.",
            "subreddit": "technology",
            "permalink": "/r/technology/comments/post3",
        },
        {
            "id": "post4",
            "title": "DALL-E 3 vs Midjourney vs Stable Diffusion",
            "selftext": "I compared DALLE 3, MidJourney, and SDXL for image generation. Each has its strengths.",
            "subreddit": "StableDiffusion",
            "permalink": "/r/StableDiffusion/comments/post4",
        },
        {
            "id": "post5",
            "title": "Microsoft Copilot now uses GPT-4",
            "selftext": "Satya Nadella confirmed that Microsoft Copilot is powered by GPT4. The integration with openai continues to deepen.",
            "subreddit": "OpenAI",
            "permalink": "/r/OpenAI/comments/post5",
        },
    ]

    # Extract entities
    extractor = EntityExtractor()
    resolver = extractor.extract_from_posts(sample_posts)

    # Display results
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)

    # Organizations
    print("\n🏢 ORGANIZATIONS:")
    for entity in extractor.get_entities_by_type("ORG")[:5]:
        print(f"   • {entity.canonical_name} ({entity.mention_count} mentions)")
        print(f"     Aliases: {entity.aliases[:3]}")

    # People
    print("\n👤 PEOPLE:")
    for entity in extractor.get_entities_by_type("PERSON")[:5]:
        print(f"   • {entity.canonical_name} ({entity.mention_count} mentions)")
        print(f"     Aliases: {entity.aliases[:3]}")

    # Products
    print("\n📦 PRODUCTS:")
    for entity in extractor.get_entities_by_type("PRODUCT")[:5]:
        print(f"   • {entity.canonical_name} ({entity.mention_count} mentions)")
        print(f"     Aliases: {entity.aliases[:3]}")

    # Show detailed mentions for top entity
    top_entity = (
        extractor.get_all_entities()[0] if extractor.get_all_entities() else None
    )
    if top_entity:
        print(f"\n{'='*60}")
        print(f"📋 DETAILED MENTIONS: {top_entity.canonical_name}")
        print("=" * 60)

        for mention in top_entity.mentions[:5]:
            print(f'\n   Mention: "{mention.raw_text}"')
            print(f"   Confidence: {mention.confidence:.0%}")
            print(f"   Method: {mention.match_method}")
            print(f"   Context: {mention.context[:100]}...")
            print(f"   Source: r/{mention.source_subreddit}")

    # Summary
    print(f"\n{'='*60}")
    print("📈 SUMMARY")
    print("=" * 60)
    summary = extractor.get_summary()
    print(f"   Total entities: {summary['total_entities']}")
    print(f"   Total mentions: {summary['total_mentions']}")
    print(f"   By type: {summary['by_type']}")

    print("\n✅ Entity extraction complete!")
