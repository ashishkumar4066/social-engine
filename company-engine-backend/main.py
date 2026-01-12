#!/usr/bin/env python3
# main.py
"""
Social Intelligence Engine - Complete Pipeline

This is the main entry point that runs the complete pipeline:
1. Extract company info from domain (Wikipedia/web)
2. Discover relevant subreddits (Reddit search)
3. Fetch posts from top subreddits
4. Extract and resolve entities from posts
5. Save everything to database
6. Display results

Usage:
    python main.py                      # Default: openai.com
    python main.py stripe.com           # Specify domain
    python main.py hubspot.com --top 10 # Limit subreddits

Docker:
    docker-compose up
"""

import os
import sys
import argparse
from dataclasses import asdict
from typing import List, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from src.company_extractor import CompanyExtractor
from src.reddit.subreddit_discovery import SubredditDiscovery
from src.reddit.reddit_client import RedditClient
from src.entity.entity_extractor import EntityExtractor
from src.entity.entity_report import generate_html_report
from src.database.models import Database


def main(domain: str, top_n: int = 20, fetch_posts_from: int = 5, db_path: str = None):
    """
    Run the complete Social Intelligence Engine pipeline.

    Args:
        domain: Company domain (e.g., 'openai.com')
        top_n: Number of top subreddits to return
        fetch_posts_from: Number of top subreddits to fetch posts from
        db_path: Path to SQLite database (default: from env or data/social_intel.db)
    """

    # Initialize database
    db_path = db_path or os.environ.get("DATABASE_PATH", "data/social_intel.db")

    # Create data directory if needed
    data_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "data"
    os.makedirs(data_dir, exist_ok=True)

    print("\n" + "#" * 70)
    print("#" + " " * 68 + "#")
    print("#" + "   SOCIAL INTELLIGENCE ENGINE   ".center(68) + "#")
    print("#" + " " * 68 + "#")
    print("#" * 70)
    print(f"\n📁 Database: {db_path}")

    # Initialize database
    db = Database(db_path)
    db.init_tables()

    # =========================================================================
    # STEP 1: Extract Company Information
    # =========================================================================

    print(f"\n{'='*70}")
    print("📚 STEP 1: EXTRACT COMPANY INFORMATION")
    print("=" * 70)

    extractor = CompanyExtractor()
    company_info = extractor.extract(domain)

    print(f"\n   Company: {company_info.company_name}")
    print(f"   Industry: {company_info.industry}")
    print(f"   Source: {company_info.source}")
    print(f"   Success: {company_info.success}")

    if company_info.products:
        print(f"\n   📦 Products: {', '.join(company_info.products[:5])}")

    if company_info.technologies:
        print(f"   💻 Technologies: {', '.join(company_info.technologies[:5])}")

    print(f"\n   🔑 Keywords for Reddit Search:")
    for i, kw in enumerate(company_info.keywords[:8], 1):
        print(f"      {i}. {kw}")

    # Save company to database
    company_dict = {
        "domain": domain,
        "company_name": company_info.company_name,
        "industry": company_info.industry,
        "description": company_info.description,
        "keywords": company_info.keywords,
        "products": company_info.products,
        "technologies": company_info.technologies,
    }
    company_id = db.insert_company(company_dict)
    print(f"\n   💾 Saved to database (company_id: {company_id})")

    # =========================================================================
    # STEP 2: Discover Relevant Subreddits
    # =========================================================================

    print(f"\n{'='*70}")
    print("🔍 STEP 2: DISCOVER RELEVANT SUBREDDITS")
    print("=" * 70)

    discovery = SubredditDiscovery()

    # Convert dataclass to dict for the discovery module
    company_info_dict = asdict(company_info)

    top_subreddits = discovery.discover_subreddits(
        domain=domain, top_n=top_n, company_info=company_info_dict
    )

    print(f"\n   Found {len(top_subreddits)} relevant subreddits")

    # Display top subreddits
    print(f"\n   {'Rank':<5} {'Subreddit':<25} {'Subscribers':>12} {'Score':>8}")
    print("   " + "-" * 55)

    for i, sub in enumerate(top_subreddits[:top_n], 1):
        name = sub.get("name", "Unknown")
        subscribers = sub.get("subscribers") or 0
        score = sub.get("business_value_score", 0)
        print(f"   {i:<5} r/{name:<24} {subscribers:>12,} {score:>8.3f}")

    # Save subreddits to database
    db.insert_subreddits_bulk(company_id, top_subreddits)
    print(f"\n   💾 Saved {len(top_subreddits)} subreddits to database")

    # =========================================================================
    # STEP 3: Fetch Posts from Top Subreddits
    # =========================================================================

    print(f"\n{'='*70}")
    print(f"📥 STEP 3: FETCH POSTS FROM TOP {fetch_posts_from} SUBREDDITS")
    print("=" * 70)

    reddit_client = RedditClient(rate_limit_delay=2.0)
    all_posts = []

    for i, sub in enumerate(top_subreddits[:fetch_posts_from], 1):
        sub_name = sub.get("name", "")
        if not sub_name:
            continue

        print(f"\n   [{i}/{fetch_posts_from}] Fetching from r/{sub_name}...")

        try:
            # Fetch recent posts
            posts = reddit_client.get_subreddit_posts(
                subreddit=sub_name, sort="hot", limit=25
            )

            # Get subreddit ID from database
            sub_record = db.get_subreddit_by_name(company_id, sub_name)
            subreddit_id = sub_record["id"] if sub_record else None

            # Convert to dict format and save
            for post in posts:
                post_dict = {
                    "id": post.id,
                    "title": post.title,
                    "selftext": post.selftext,
                    "subreddit": post.subreddit,
                    "permalink": post.permalink,
                    "score": post.score,
                    "num_comments": post.num_comments,
                }
                all_posts.append(post_dict)

                # Save to database
                if subreddit_id:
                    db.insert_post(subreddit_id, post_dict)

            print(f"      ✓ Fetched {len(posts)} posts")

        except Exception as e:
            print(f"      ⚠️ Error: {e}")

    print(f"\n   📊 Total posts fetched: {len(all_posts)}")
    print(f"   💾 Saved to database")

    # =========================================================================
    # STEP 4: Extract and Resolve Entities
    # =========================================================================

    print(f"\n{'='*70}")
    print("🏷️  STEP 4: EXTRACT AND RESOLVE ENTITIES")
    print("=" * 70)

    entity_extractor = EntityExtractor()
    resolver = entity_extractor.extract_from_posts(all_posts)

    # Save entities to database
    db.insert_entities_from_resolver(company_id, resolver)

    # =========================================================================
    # STEP 5: Display Results
    # =========================================================================

    print(f"\n{'='*70}")
    print("📊 STEP 5: RESULTS")
    print("=" * 70)

    # Organizations
    orgs = entity_extractor.get_entities_by_type("ORG")
    print(f"\n🏢 ORGANIZATIONS ({len(orgs)} found):")
    for entity in orgs[:10]:
        print(f"   • {entity.canonical_name} ({entity.mention_count} mentions)")
        if entity.aliases:
            print(f"     Aliases: {', '.join(entity.aliases[:3])}")

    # People
    people = entity_extractor.get_entities_by_type("PERSON")
    print(f"\n👤 PEOPLE ({len(people)} found):")
    for entity in people[:10]:
        print(f"   • {entity.canonical_name} ({entity.mention_count} mentions)")
        if entity.aliases:
            print(f"     Aliases: {', '.join(entity.aliases[:3])}")

    # Products
    products = entity_extractor.get_entities_by_type("PRODUCT")
    print(f"\n📦 PRODUCTS ({len(products)} found):")
    for entity in products[:10]:
        print(f"   • {entity.canonical_name} ({entity.mention_count} mentions)")
        if entity.aliases:
            print(f"     Aliases: {', '.join(entity.aliases[:3])}")

    # =========================================================================
    # Show detailed mentions for top entity
    # =========================================================================

    all_entities = entity_extractor.get_all_entities()
    if all_entities:
        top_entity = all_entities[0]

        print(f"\n{'='*70}")
        print(f"🔎 DETAILED VIEW: {top_entity.canonical_name}")
        print("=" * 70)

        print(f"\n   Type: {top_entity.entity_type}")
        print(f"   Total mentions: {top_entity.mention_count}")
        print(f"   Average confidence: {top_entity.avg_confidence:.0%}")
        print(f"   Aliases found: {', '.join(top_entity.aliases[:5])}")
        print(
            f"   Mentioned in subreddits: {', '.join(top_entity.subreddits_mentioned_in[:5])}"
        )

        print(f"\n   📋 Sample mentions:")
        for i, mention in enumerate(top_entity.mentions[:5], 1):
            print(f'\n   [{i}] "{mention.raw_text}"')
            print(
                f"       Confidence: {mention.confidence:.0%} ({mention.match_method})"
            )
            print(f"       Context: {mention.context[:80]}...")
            print(f"       Source: r/{mention.source_subreddit}")

    # =========================================================================
    # Generate HTML Report
    # =========================================================================

    print(f"\n{'='*70}")
    print("📄 GENERATING HTML REPORT")
    print("=" * 70)

    report_path = f"{data_dir}/{domain.replace('.', '_')}_report.html"
    generate_html_report(
        resolver, company_name=company_info.company_name, output_file=report_path
    )

    # =========================================================================
    # Summary
    # =========================================================================

    print(f"\n{'='*70}")
    print("✅ PIPELINE COMPLETE")
    print("=" * 70)

    summary = db.get_summary(company_id)

    print(f"\n   📊 Summary:")
    print(f"      • Company analyzed: {company_info.company_name}")
    print(f"      • Subreddits discovered: {summary['subreddit_count']}")
    print(f"      • Posts analyzed: {summary['post_count']}")
    print(f"      • Unique entities found: {summary['entity_count']}")
    print(f"      • Total mentions: {summary['mention_count']}")
    print(f"      • Organizations: {summary['entities_by_type'].get('ORG', 0)}")
    print(f"      • People: {summary['entities_by_type'].get('PERSON', 0)}")
    print(f"      • Products: {summary['entities_by_type'].get('PRODUCT', 0)}")

    print(f"\n   📁 Data saved to: {db_path}")
    print(f"   📄 Report saved to: {report_path}")
    print(f"\n   🌐 To browse entities via API:")
    print(f"      1. Run: uvicorn api.main:app --reload")
    print(f"      2. Open: http://localhost:8000/ui/entities/{company_id}")

    print("\n" + "#" * 70)
    print("#" + "   DONE   ".center(68) + "#")
    print("#" * 70 + "\n")

    # Close database
    db.close()

    # Return data for further processing
    return {
        "company_id": company_id,
        "company_info": company_dict,
        "subreddits": top_subreddits,
        "posts": all_posts,
        "summary": summary,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Social Intelligence Engine - Discover what people say about a company on Reddit"
    )
    parser.add_argument(
        "domain",
        nargs="?",
        default="openai.com",
        help="Company domain to analyze (default: openai.com)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top subreddits to return (default: 20)",
    )
    parser.add_argument(
        "--fetch-from",
        type=int,
        default=5,
        help="Number of subreddits to fetch posts from (default: 5)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Database path (default: data/social_intel.db)",
    )

    args = parser.parse_args()

    # Remove common suffixes from domain
    domain = (
        args.domain.replace("https://", "").replace("http://", "").replace("www.", "")
    )

    # Run the pipeline
    results = main(
        domain=domain, top_n=args.top, fetch_posts_from=args.fetch_from, db_path=args.db
    )
