# relationship_extractor.py
"""
Relationship Extractor - Extract relationships between entities using spaCy

This module extracts relationships from text using:
1. Dependency parsing (spaCy's syntactic analysis)
2. Pattern matching (regex patterns for common relationship expressions)
3. Co-occurrence analysis (entities mentioned together)

Usage:
    extractor = RelationshipExtractor()
    relationships = extractor.extract_relationships(entities, posts)
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# Import relationship models
try:
    from .relationship_models import EntityRelationship, RelationshipType
except ImportError:
    from relationship_models import EntityRelationship, RelationshipType

# Try to load spaCy
SPACY_AVAILABLE = False
nlp = None

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    print("WARNING: spaCy not available for relationship extraction")


class RelationshipExtractor:
    """
    Extracts relationships between entities from text.

    Uses multiple strategies:
    1. Pattern matching - regex patterns for common phrases
    2. Dependency parsing - spaCy's syntactic analysis (if available)
    3. Co-occurrence - entities mentioned together (weak signal)
    """

    def __init__(self, use_spacy: bool = True):
        """
        Initialize the relationship extractor.

        Args:
            use_spacy: Whether to use spaCy for dependency parsing
        """
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self._compile_patterns()

        # Statistics
        self.stats = {
            "posts_processed": 0,
            "relationships_found": 0,
            "pattern_matches": 0,
            "dependency_matches": 0,
            "co_occurrence_matches": 0,
        }

    def _compile_patterns(self):
        """
        Compile regex patterns for relationship extraction.

        Patterns use placeholders {PERSON}, {ORG}, {PRODUCT} that will be
        replaced with actual entity names.
        """
        self.patterns = {
            # CEO relationships
            RelationshipType.CEO: [
                r"{PERSON} (?:is|was|became|serves as) (?:the )?CEO (?:of|at) {ORG}",
                r"{ORG}'?s? CEO {PERSON}",
                r"CEO {PERSON}(?: of| at)? {ORG}",
                r"{PERSON},? (?:who )?(?:leads|runs) {ORG}",
            ],

            # Founder relationships
            RelationshipType.FOUNDER: [
                r"{PERSON} founded {ORG}",
                r"{PERSON} (?:is|was) (?:the )?founder of {ORG}",
                r"{ORG} founder {PERSON}",
                r"{ORG},? founded by {PERSON}",
            ],

            RelationshipType.CO_FOUNDER: [
                r"{PERSON} co-?founded {ORG}",
                r"{PERSON} (?:is|was) (?:a )?co-?founder of {ORG}",
                r"{ORG} co-?founder {PERSON}",
            ],

            # Employee relationships
            RelationshipType.EMPLOYEE: [
                r"{PERSON} works (?:at|for) {ORG}",
                r"{PERSON} (?:is|was) (?:an? )?employee (?:of|at) {ORG}",
                r"{PERSON} joined {ORG}",
            ],

            # CTO relationships
            RelationshipType.CTO: [
                r"{PERSON} (?:is|was) (?:the )?CTO (?:of|at) {ORG}",
                r"{ORG}'?s? CTO {PERSON}",
            ],

            # Investment relationships
            RelationshipType.INVESTOR: [
                r"{ORG1} invested in {ORG2}",
                r"{ORG1} (?:is|was) (?:an? )?investor in {ORG2}",
                r"{ORG2} received investment from {ORG1}",
                r"{ORG1} funded {ORG2}",
                r"{ORG1}'?s? (?:\$[\d.]+[BMK]? )?investment in {ORG2}",
            ],

            # Acquisition relationships
            RelationshipType.ACQUIRED_BY: [
                r"{ORG1} acquired {ORG2}",
                r"{ORG2} (?:was )?acquired by {ORG1}",
                r"{ORG1} bought {ORG2}",
            ],

            # Product relationships
            RelationshipType.PRODUCT_OF: [
                r"{ORG} (?:created|built|developed|released|launched|announced) {PRODUCT}",
                r"{PRODUCT} (?:by|from) {ORG}",
                r"{ORG}'?s? {PRODUCT}",
                r"{PRODUCT},? (?:a product|made) by {ORG}",
            ],

            # Partnership
            RelationshipType.PARTNER: [
                r"{ORG1} partnered with {ORG2}",
                r"{ORG1} and {ORG2} (?:are )?partners",
                r"{ORG1}'?s? partnership with {ORG2}",
            ],

            # Competitor
            RelationshipType.COMPETITOR: [
                r"{ORG1} (?:competes with|competing with) {ORG2}",
                r"{ORG1} (?:and|vs\.?) {ORG2}",  # Weak signal
                r"{ORG1} rival {ORG2}",
            ],

            # Sentiment - Opponent/Critic
            RelationshipType.OPPONENT: [
                r"{PERSON} criticized {ORG}",
                r"{PERSON} (?:opposed|opposes) {ORG}",
                r"{PERSON} (?:slammed|blasted|attacked) {ORG}",
            ],

            # Sentiment - Supporter
            RelationshipType.SUPPORTER: [
                r"{PERSON} (?:supports|supported|endorses|endorsed) {ORG}",
                r"{PERSON} praised {ORG}",
            ],
        }

    def extract_relationships(
        self, entities: List, posts: List[Dict]
    ) -> List[EntityRelationship]:
        """
        Extract relationships from posts given a list of entities.

        Args:
            entities: List of CanonicalEntity objects
            posts: List of post dicts with 'id', 'title', 'selftext', 'subreddit'

        Returns:
            List of EntityRelationship objects
        """
        print(f"\n{'='*60}")
        print(f"Relationship Extraction")
        print(f"{'='*60}")
        print(f"   Entities: {len(entities)}")
        print(f"   Posts: {len(posts)}")
        print(f"   Method: {'spaCy + Patterns' if self.use_spacy else 'Patterns only'}")

        # Build entity lookup by type for efficient matching
        entity_map = self._build_entity_map(entities)

        # Storage for relationships
        # Key: (source, rel_type, target) -> EntityRelationship
        relationships = {}

        # Process each post
        total_posts = len(posts)
        for idx, post in enumerate(posts, 1):
            self.stats["posts_processed"] += 1

            # Progress logging every 10 posts
            if idx % 10 == 0 or idx == total_posts:
                print(f"   Processing post {idx}/{total_posts} ({idx*100//total_posts}%)...", end='\r')

            # Get full text
            title = post.get("title", "")
            body = post.get("selftext") or post.get("body") or ""
            full_text = f"{title} {body}"

            if not full_text.strip():
                continue

            # Build post info
            post_info = {
                "post_id": post.get("id", ""),
                "subreddit": post.get("subreddit", ""),
                "title": title[:100],
            }

            # Strategy 1: Pattern matching
            pattern_rels = self._extract_with_patterns(
                full_text, entity_map, post_info
            )
            self._merge_relationships(relationships, pattern_rels)

            # Strategy 2: Dependency parsing (if spaCy available)
            if self.use_spacy:
                dep_rels = self._extract_with_dependencies(
                    full_text, entity_map, post_info
                )
                self._merge_relationships(relationships, dep_rels)

        print()  # New line after progress

        # Convert to list and filter by confidence
        final_relationships = [
            rel for rel in relationships.values()
            if rel.confidence >= 0.5  # Only keep relationships with >= 50% confidence
        ]

        # Sort by confidence
        final_relationships.sort(key=lambda r: r.confidence, reverse=True)

        # Print stats
        print(f"\nRelationship Extraction Stats:")
        print(f"   Posts processed: {self.stats['posts_processed']}")
        print(f"   Relationships found: {len(final_relationships)}")
        print(f"   From patterns: {self.stats['pattern_matches']}")
        if self.use_spacy:
            print(f"   From dependencies: {self.stats['dependency_matches']}")

        return final_relationships

    def _build_entity_map(self, entities: List) -> Dict[str, List]:
        """Build a map of entities by type for efficient lookup"""
        entity_map = {
            "PERSON": [],
            "ORG": [],
            "PRODUCT": [],
        }

        for entity in entities:
            entity_type = entity.entity_type.upper()
            if entity_type in entity_map:
                entity_map[entity_type].append(entity)

        return entity_map

    def _find_entities_in_text(self, text: str, entity_map: Dict) -> Dict[str, List]:
        """
        Find which entities from entity_map are actually mentioned in this text.

        This is a critical optimization that reduces pattern matching from O(entities²)
        to O(entities_in_post²), which can be 100x faster for large entity sets.

        Returns:
            Dict with same structure as entity_map but only containing entities
            that appear in the text
        """
        text_lower = text.lower()
        entities_in_text = {
            "PERSON": [],
            "ORG": [],
            "PRODUCT": [],
        }

        for entity_type, entities in entity_map.items():
            for entity in entities:
                # Check if canonical name appears in text
                if entity.canonical_name.lower() in text_lower:
                    entities_in_text[entity_type].append(entity)
                    continue

                # Check if any alias appears in text
                found = False
                for alias in entity.aliases:
                    if alias.lower() in text_lower:
                        entities_in_text[entity_type].append(entity)
                        found = True
                        break

                if found:
                    continue

        return entities_in_text

    def _extract_with_patterns(
        self, text: str, entity_map: Dict, post_info: Dict
    ) -> List[EntityRelationship]:
        """Extract relationships using regex pattern matching"""
        relationships = []

        # OPTIMIZATION: First find which entities are mentioned in this post
        # This reduces complexity from O(entities²) to O(entities_in_post²)
        entities_in_post = self._find_entities_in_text(text, entity_map)

        # Skip if too few entities (need at least 2 for a relationship)
        if sum(len(entities) for entities in entities_in_post.values()) < 2:
            return relationships

        # For each relationship type and its patterns
        for rel_type, patterns in self.patterns.items():
            for pattern_template in patterns:
                # Try different entity type combinations based on pattern
                # But only with entities that actually appear in this post
                matches = self._match_pattern(
                    pattern_template, text, entities_in_post, rel_type
                )

                for match in matches:
                    source, target, evidence, confidence = match

                    relationships.append(
                        EntityRelationship(
                            source_entity=source,
                            relationship_type=rel_type,
                            target_entity=target,
                            confidence=confidence,
                            evidence=[evidence],
                            source_posts=[post_info["post_id"]],
                            source_subreddits=[post_info["subreddit"]],
                            extraction_method="pattern_match",
                        )
                    )
                    self.stats["pattern_matches"] += 1

        return relationships

    def _match_pattern(
        self, pattern_template: str, text: str, entity_map: Dict, rel_type: str
    ) -> List[Tuple[str, str, str, float]]:
        """
        Match a pattern template against text with actual entities.

        Returns list of (source_entity, target_entity, evidence, confidence)
        """
        matches = []

        # Determine which entity types this pattern expects
        if "{PERSON}" in pattern_template and "{ORG}" in pattern_template:
            # PERSON → ORG relationship
            for person in entity_map["PERSON"]:
                for org in entity_map["ORG"]:
                    match = self._try_pattern_match(
                        pattern_template, text,
                        {"PERSON": person.canonical_name, "ORG": org.canonical_name}
                    )
                    if match:
                        matches.append((person.canonical_name, org.canonical_name, match, 0.85))

        elif "{ORG1}" in pattern_template and "{ORG2}" in pattern_template:
            # ORG → ORG relationship
            for org1 in entity_map["ORG"]:
                for org2 in entity_map["ORG"]:
                    if org1.canonical_name == org2.canonical_name:
                        continue  # Skip self-relationships

                    match = self._try_pattern_match(
                        pattern_template, text,
                        {"ORG1": org1.canonical_name, "ORG2": org2.canonical_name}
                    )
                    if match:
                        matches.append((org1.canonical_name, org2.canonical_name, match, 0.80))

        elif "{ORG}" in pattern_template and "{PRODUCT}" in pattern_template:
            # ORG → PRODUCT relationship
            for org in entity_map["ORG"]:
                for product in entity_map["PRODUCT"]:
                    match = self._try_pattern_match(
                        pattern_template, text,
                        {"ORG": org.canonical_name, "PRODUCT": product.canonical_name}
                    )
                    if match:
                        matches.append((org.canonical_name, product.canonical_name, match, 0.90))

        return matches

    def _try_pattern_match(
        self, pattern_template: str, text: str, replacements: Dict[str, str]
    ) -> Optional[str]:
        """
        Try to match a pattern with entity replacements.

        Returns the matched text snippet if found, None otherwise.
        """
        # Replace placeholders with actual entity names
        pattern = pattern_template
        for placeholder, entity_name in replacements.items():
            # Escape special regex characters in entity name
            escaped_name = re.escape(entity_name)
            pattern = pattern.replace(f"{{{placeholder}}}", escaped_name)

        # Try to find the pattern in text (case-insensitive)
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            # Return the matched snippet
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            return text[start:end].strip()

        return None

    def _extract_with_dependencies(
        self, text: str, entity_map: Dict, post_info: Dict
    ) -> List[EntityRelationship]:
        """
        Extract relationships using spaCy dependency parsing.

        This is more advanced and can catch relationships that patterns miss.
        """
        relationships = []

        # Limit text length for performance
        text = text[:10000]

        try:
            doc = nlp(text)

            # Look for specific dependency patterns
            # Example: "Sam Altman is CEO of OpenAI"
            # Dependency tree will show: Altman <-nsubj- is -attr-> CEO -prep-> of -pobj-> OpenAI

            for token in doc:
                # Pattern: X is CEO of Y
                if token.text.lower() in ["ceo", "founder", "cto", "employee"]:
                    rel_type = self._role_to_relationship_type(token.text.lower())

                    # Look for subject (person)
                    subject = None
                    for child in token.head.children:
                        if child.dep_ == "nsubj" and child.ent_type_ == "PERSON":
                            subject = child.text

                    # Look for object (organization)
                    obj = None
                    for child in token.children:
                        if child.dep_ == "prep" and child.text.lower() in ["of", "at"]:
                            for pobj in child.children:
                                if pobj.dep_ == "pobj" and pobj.ent_type_ == "ORG":
                                    obj = pobj.text

                    if subject and obj:
                        # Verify these entities are in our entity list
                        if self._entity_exists(subject, entity_map["PERSON"]) and \
                           self._entity_exists(obj, entity_map["ORG"]):

                            relationships.append(
                                EntityRelationship(
                                    source_entity=subject,
                                    relationship_type=rel_type,
                                    target_entity=obj,
                                    confidence=0.75,
                                    evidence=[token.sent.text],
                                    source_posts=[post_info["post_id"]],
                                    source_subreddits=[post_info["subreddit"]],
                                    extraction_method="dependency_parse",
                                )
                            )
                            self.stats["dependency_matches"] += 1

        except Exception as e:
            # Silently skip if dependency parsing fails
            pass

        return relationships

    def _role_to_relationship_type(self, role: str) -> str:
        """Map role word to relationship type"""
        mapping = {
            "ceo": RelationshipType.CEO,
            "cto": RelationshipType.CTO,
            "founder": RelationshipType.FOUNDER,
            "employee": RelationshipType.EMPLOYEE,
        }
        return mapping.get(role, RelationshipType.EMPLOYEE)

    def _entity_exists(self, name: str, entity_list: List) -> bool:
        """Check if an entity name exists in the entity list"""
        name_lower = name.lower()
        for entity in entity_list:
            if entity.canonical_name.lower() == name_lower:
                return True
            if name_lower in [alias.lower() for alias in entity.aliases]:
                return True
        return False

    def _merge_relationships(
        self, relationships: Dict, new_relationships: List[EntityRelationship]
    ):
        """
        Merge new relationships into existing relationships dict.

        If a relationship already exists, merge evidence and increase confidence.
        """
        for new_rel in new_relationships:
            # Create key for deduplication
            key = (
                new_rel.source_entity.lower(),
                new_rel.relationship_type,
                new_rel.target_entity.lower(),
            )

            if key in relationships:
                # Relationship already exists - merge evidence
                existing_rel = relationships[key]
                existing_rel.evidence.extend(new_rel.evidence)
                existing_rel.source_posts.extend(new_rel.source_posts)
                existing_rel.source_subreddits.extend(new_rel.source_subreddits)

                # Increase confidence (but cap at 0.99)
                existing_rel.confidence = min(0.99, existing_rel.confidence + 0.05)

            else:
                # New relationship
                relationships[key] = new_rel
                self.stats["relationships_found"] += 1


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("\nTesting Relationship Extractor...")
    print("=" * 60)

    # Mock entities
    from dataclasses import dataclass

    @dataclass
    class MockEntity:
        canonical_name: str
        entity_type: str
        aliases: list

    entities = [
        MockEntity("OpenAI", "ORG", ["openai", "open ai"]),
        MockEntity("Microsoft", "ORG", ["microsoft", "msft"]),
        MockEntity("ChatGPT", "PRODUCT", ["chatgpt", "chat gpt"]),
        MockEntity("Sam Altman", "PERSON", ["altman", "sama"]),
        MockEntity("Elon Musk", "PERSON", ["elon", "musk"]),
    ]

    # Mock posts
    posts = [
        {
            "id": "post1",
            "title": "Sam Altman is CEO of OpenAI",
            "selftext": "Sam Altman announced new features for ChatGPT today.",
            "subreddit": "MachineLearning",
        },
        {
            "id": "post2",
            "title": "Microsoft invested billions in OpenAI",
            "selftext": "Microsoft's $10B investment in OpenAI shows their commitment to AI.",
            "subreddit": "technology",
        },
        {
            "id": "post3",
            "title": "OpenAI created ChatGPT",
            "selftext": "ChatGPT by OpenAI has revolutionized conversational AI.",
            "subreddit": "OpenAI",
        },
        {
            "id": "post4",
            "title": "Elon Musk criticized OpenAI",
            "selftext": "Elon Musk slammed OpenAI for straying from its mission.",
            "subreddit": "technology",
        },
    ]

    # Extract relationships
    extractor = RelationshipExtractor()
    relationships = extractor.extract_relationships(entities, posts)

    # Display results
    print(f"\n{'='*60}")
    print("RESULTS")
    print("=" * 60)

    print(f"\nRELATIONSHIPS ({len(relationships)} found):")
    for rel in relationships:
        print(f"\n   {rel.source_entity} → {rel.relationship_type} → {rel.target_entity}")
        print(f"      Confidence: {rel.confidence:.0%}")
        print(f"      Evidence: {rel.evidence_count} mentions")
        print(f"      Method: {rel.extraction_method}")
        if rel.evidence:
            print(f"      Example: \"{rel.evidence[0][:80]}...\"")

    print("\n✅ Relationship extraction complete!")
