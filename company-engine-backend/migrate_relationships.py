#!/usr/bin/env python3
"""
Migration Script: Extract relationships for existing companies

This script extracts relationships from existing posts for companies
that were analyzed before the relationship extraction feature was added.
"""

import sys
from src.database.models import Database
from src.entity.entity_models import CanonicalEntity
from src.relationship import RelationshipExtractor


def migrate_company_relationships(company_id: int):
    """Extract relationships for a specific company"""

    db = Database("data/social_intel.db")

    # Get company info
    company = db.get_company_by_id(company_id)
    if not company:
        print(f"Company {company_id} not found")
        return

    print(f"\nProcessing: {company['company_name']} (ID: {company_id})")
    print("=" * 60)

    # Get all posts for this company
    db.cursor.execute("""
        SELECT p.id, p.title, p.body, s.name as subreddit
        FROM posts p
        JOIN subreddits s ON p.subreddit_id = s.id
        WHERE s.company_id = ?
    """, (company_id,))

    posts = []
    for row in db.cursor.fetchall():
        posts.append({
            'id': row['id'],
            'title': row['title'] or '',
            'selftext': row['body'] or '',
            'subreddit': row['subreddit']
        })

    print(f"Found {len(posts)} posts")

    if not posts:
        print("No posts to process")
        return

    # Get all entities for this company
    entity_dicts = db.get_entities_by_company(company_id)
    print(f"Found {len(entity_dicts)} entities")

    if not entity_dicts:
        print("No entities to process")
        return

    # Convert database entities to CanonicalEntity objects
    entities = []
    for entity_dict in entity_dicts:
        canonical_entity = CanonicalEntity(
            canonical_name=entity_dict['canonical_name'],
            entity_type=entity_dict['entity_type'],
            aliases=entity_dict['aliases'],
            mentions=[]  # We don't need mentions for relationship extraction
        )
        entities.append(canonical_entity)

    # Extract relationships
    print("\nExtracting relationships...")
    relationship_extractor = RelationshipExtractor()
    relationships = relationship_extractor.extract_relationships(
        entities=entities,
        posts=posts
    )

    print(f"Extracted {len(relationships)} relationships")

    # Save to database
    if relationships:
        db.insert_relationships_bulk(company_id, relationships)
        print(f"Saved {len(relationships)} relationships to database")

        # Show sample relationships
        print("\nSample relationships:")
        for rel in relationships[:5]:
            print(f"  - {rel.source_entity} --[{rel.relationship_type}]--> {rel.target_entity} (confidence: {rel.confidence:.2f})")

    print("\nDone!")


def migrate_all_companies():
    """Extract relationships for all companies"""

    db = Database("data/social_intel.db")

    # Get all companies
    db.cursor.execute("SELECT id, company_name FROM companies ORDER BY id")
    companies = db.cursor.fetchall()

    print(f"Found {len(companies)} companies")

    for company in companies:
        try:
            migrate_company_relationships(company['id'])
        except Exception as e:
            print(f"ERROR processing {company['company_name']}: {e}")
            continue


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Migrate specific company
        company_id = int(sys.argv[1])
        migrate_company_relationships(company_id)
    else:
        # Migrate all companies
        print("Migrating relationships for all companies...")
        print("=" * 60)
        migrate_all_companies()
