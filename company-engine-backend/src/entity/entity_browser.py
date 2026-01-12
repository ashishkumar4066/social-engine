# entity_browser.py
"""
Entity Browser - Simple CLI UI to Browse Entities

A simple command-line interface to browse and explore extracted entities.
Shows entities grouped by type, with ability to view detailed mentions.

Usage:
    browser = EntityBrowser(resolver)
    browser.run()  # Interactive mode

    # Or non-interactive
    browser.show_summary()
    browser.show_entity("OpenAI")
"""

from typing import List, Optional

try:
    from .entity_extractor import EntityExtractor
    from .entity_resolver import EntityResolver
    from .entity_models import CanonicalEntity
except ImportError:
    from entity_extractor import EntityExtractor
    from entity_resolver import EntityResolver
    from entity_models import CanonicalEntity


class EntityBrowser:
    """
    Simple CLI browser for exploring extracted entities.
    """

    def __init__(self, resolver: EntityResolver):
        """
        Initialize browser with a resolver containing entities.

        Args:
            resolver: EntityResolver with extracted entities
        """
        self.resolver = resolver

    def run(self):
        """Run interactive browser"""
        while True:
            self._show_menu()
            choice = input("\nEnter choice: ").strip().lower()

            if choice == "1":
                self.show_summary()
            elif choice == "2":
                self.show_organizations()
            elif choice == "3":
                self.show_people()
            elif choice == "4":
                self.show_products()
            elif choice == "5":
                self.show_all_entities()
            elif choice == "6":
                name = input("Enter entity name: ").strip()
                self.show_entity(name)
            elif choice == "7":
                self.show_top_mentions()
            elif choice in ["q", "quit", "exit", "0"]:
                print("\nGoodbye! 👋")
                break
            else:
                print("Invalid choice. Try again.")

    def _show_menu(self):
        """Show main menu"""
        print("\n" + "=" * 50)
        print("🏷️  ENTITY BROWSER")
        print("=" * 50)
        print("\n  1. Show Summary")
        print("  2. Browse Organizations")
        print("  3. Browse People")
        print("  4. Browse Products")
        print("  5. Show All Entities")
        print("  6. Search Entity by Name")
        print("  7. Show Top Mentions")
        print("  0. Exit")

    def show_summary(self):
        """Show summary statistics"""
        summary = self.resolver.get_summary()

        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)

        print(f"\n  Total entities: {summary['total_entities']}")
        print(f"  Total mentions: {summary['total_mentions']}")

        print("\n  By type:")
        for entity_type, count in summary["by_type"].items():
            icon = {"ORG": "🏢", "PERSON": "👤", "PRODUCT": "📦"}.get(entity_type, "•")
            print(f"    {icon} {entity_type}: {count}")

        print("\n  Top 5 entities:")
        for i, item in enumerate(summary["top_entities"][:5], 1):
            print(f"    {i}. {item['name']} ({item['mentions']} mentions)")

    def show_organizations(self):
        """Show all organizations"""
        self._show_entities_by_type("ORG", "🏢 ORGANIZATIONS")

    def show_people(self):
        """Show all people"""
        self._show_entities_by_type("PERSON", "👤 PEOPLE")

    def show_products(self):
        """Show all products"""
        self._show_entities_by_type("PRODUCT", "📦 PRODUCTS")

    def _show_entities_by_type(self, entity_type: str, title: str):
        """Show entities filtered by type"""
        entities = self.resolver.get_entities_by_type(entity_type)

        print(f"\n{'='*50}")
        print(title)
        print("=" * 50)

        if not entities:
            print("\n  No entities found.")
            return

        print(f"\n  {'#':<4} {'Entity':<25} {'Mentions':>10} {'Confidence':>12}")
        print("  " + "-" * 55)

        for i, entity in enumerate(entities[:20], 1):
            print(
                f"  {i:<4} {entity.canonical_name:<25} {entity.mention_count:>10} {entity.avg_confidence:>11.0%}"
            )

        if len(entities) > 20:
            print(f"\n  ... and {len(entities) - 20} more")

        # Ask if user wants to see details
        print("\n  Enter entity number for details (or Enter to go back): ", end="")
        choice = input().strip()

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(entities):
                self._show_entity_details(entities[idx])

    def show_all_entities(self):
        """Show all entities"""
        entities = self.resolver.get_all_entities()

        print(f"\n{'='*50}")
        print("📋 ALL ENTITIES")
        print("=" * 50)

        if not entities:
            print("\n  No entities found.")
            return

        print(f"\n  {'#':<4} {'Entity':<25} {'Type':<10} {'Mentions':>10}")
        print("  " + "-" * 55)

        for i, entity in enumerate(entities[:30], 1):
            icon = {"ORG": "🏢", "PERSON": "👤", "PRODUCT": "📦"}.get(
                entity.entity_type, "•"
            )
            print(
                f"  {i:<4} {entity.canonical_name:<25} {icon} {entity.entity_type:<7} {entity.mention_count:>10}"
            )

        if len(entities) > 30:
            print(f"\n  ... and {len(entities) - 30} more")

    def show_entity(self, name: str):
        """Show details for a specific entity"""
        entity = self.resolver.get_entity(name)

        if not entity:
            print(f"\n  ⚠️ Entity '{name}' not found.")
            print("  Try one of these:")
            for e in self.resolver.get_all_entities()[:5]:
                print(f"    • {e.canonical_name}")
            return

        self._show_entity_details(entity)

    def _show_entity_details(self, entity: CanonicalEntity):
        """Show detailed information about an entity"""
        icon = {"ORG": "🏢", "PERSON": "👤", "PRODUCT": "📦"}.get(
            entity.entity_type, "•"
        )

        print(f"\n{'='*60}")
        print(f"{icon} {entity.canonical_name}")
        print("=" * 60)

        print(f"\n  Type: {entity.entity_type}")
        print(f"  Total mentions: {entity.mention_count}")
        print(f"  Average confidence: {entity.avg_confidence:.0%}")

        # Aliases
        if entity.aliases:
            print(f"\n  📝 Aliases ({len(entity.aliases)}):")
            for alias in entity.aliases[:10]:
                print(f"     • {alias}")
            if len(entity.aliases) > 10:
                print(f"     ... and {len(entity.aliases) - 10} more")

        # Subreddits
        subreddits = entity.subreddits_mentioned_in
        if subreddits:
            print(f"\n  📍 Mentioned in subreddits ({len(subreddits)}):")
            for sub in subreddits[:5]:
                print(f"     • r/{sub}")

        # Mention breakdown
        summary = entity.get_mention_summary()
        print(f"\n  📊 Confidence breakdown:")
        print(f"     High (≥90%): {summary['high_confidence']}")
        print(f"     Medium (70-90%): {summary['medium_confidence']}")
        print(f"     Low (<70%): {summary['low_confidence']}")

        # Sample mentions
        print(f"\n  📋 Sample mentions:")
        for i, mention in enumerate(entity.mentions[:5], 1):
            print(f'\n  [{i}] "{mention.raw_text}"')
            print(
                f"      Confidence: {mention.confidence:.0%} ({mention.match_method})"
            )
            print(f"      Context: ...{mention.context[:60]}...")
            print(f"      Source: r/{mention.source_subreddit}")

        if len(entity.mentions) > 5:
            print(f"\n  ... and {len(entity.mentions) - 5} more mentions")

    def show_top_mentions(self):
        """Show top mentions with highest confidence"""
        print(f"\n{'='*60}")
        print("🔝 TOP MENTIONS (Highest Confidence)")
        print("=" * 60)

        # Collect all mentions
        all_mentions = []
        for entity in self.resolver.get_all_entities():
            for mention in entity.mentions:
                all_mentions.append((entity, mention))

        # Sort by confidence
        all_mentions.sort(key=lambda x: x[1].confidence, reverse=True)

        print(f"\n  {'Entity':<20} {'Mention':<20} {'Confidence':>12} {'Source'}")
        print("  " + "-" * 70)

        for entity, mention in all_mentions[:15]:
            raw = (
                mention.raw_text[:18] + ".."
                if len(mention.raw_text) > 20
                else mention.raw_text
            )
            source = (
                f"r/{mention.source_subreddit}"[:15]
                if mention.source_subreddit
                else "N/A"
            )
            print(
                f"  {entity.canonical_name:<20} {raw:<20} {mention.confidence:>11.0%} {source}"
            )


def browse_entities(resolver: EntityResolver):
    """
    Convenience function to start the entity browser.

    Args:
        resolver: EntityResolver with extracted entities
    """
    browser = EntityBrowser(resolver)
    browser.run()


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("Entity Browser Test")
    print("=" * 50)

    # Create a resolver with some test data
    from src.entity.entity_resolver import EntityResolver

    resolver = EntityResolver()

    # Add some test mentions
    test_data = [
        ("OpenAI", "OpenAI released GPT-4..."),
        ("Open AI", "I think Open AI is great..."),
        ("openai", "Check out openai's blog..."),
        ("ChatGPT", "ChatGPT is amazing..."),
        ("chat gpt", "I use chat gpt daily..."),
        ("Sam Altman", "Sam Altman announced..."),
        ("Altman", "Altman said in interview..."),
        ("GPT-4", "GPT-4 is very capable..."),
        ("Microsoft", "Microsoft invested in OpenAI..."),
        ("Elon Musk", "Elon Musk criticized..."),
    ]

    for raw_text, context in test_data:
        resolver.resolve(raw_text, context, {"subreddit": "test", "post_id": "123"})

    # Run browser
    browser = EntityBrowser(resolver)
    browser.show_summary()
    browser.show_entity("OpenAI")
