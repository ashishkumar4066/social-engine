# src/database/models.py
"""
Database Models for Social Intelligence Engine

Uses SQLite for simplicity (can be in-memory or file-based).
For production, you could switch to PostgreSQL.

Tables:
1. companies - Company info extracted from domain
2. subreddits - Discovered subreddits with scores
3. posts - Fetched Reddit posts
4. entities - Canonical entities (resolved)
5. mentions - Individual entity mentions with context
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


# =============================================================================
# Data Classes (for type safety)
# =============================================================================


@dataclass
class CompanyRecord:
    id: Optional[int] = None
    domain: str = ""
    company_name: str = ""
    industry: str = ""
    description: str = ""
    keywords: List[str] = None
    products: List[str] = None
    technologies: List[str] = None
    created_at: str = ""


@dataclass
class SubredditRecord:
    id: Optional[int] = None
    company_id: int = 0
    name: str = ""
    title: str = ""
    description: str = ""
    subscribers: int = 0
    active_users: int = 0
    business_value_score: float = 0.0
    discovery_methods: List[str] = None
    matched_queries: List[str] = None
    created_at: str = ""


@dataclass
class PostRecord:
    id: Optional[int] = None
    subreddit_id: int = 0
    reddit_id: str = ""
    title: str = ""
    body: str = ""
    score: int = 0
    num_comments: int = 0
    permalink: str = ""
    created_at: str = ""


@dataclass
class EntityRecord:
    id: Optional[int] = None
    company_id: int = 0
    canonical_name: str = ""
    entity_type: str = ""  # ORG, PERSON, PRODUCT
    aliases: List[str] = None
    mention_count: int = 0
    avg_confidence: float = 0.0
    subreddits_found_in: List[str] = None
    created_at: str = ""


@dataclass
class MentionRecord:
    id: Optional[int] = None
    entity_id: int = 0
    post_id: int = 0
    raw_text: str = ""
    confidence: float = 0.0
    match_method: str = ""
    context: str = ""
    subreddit: str = ""
    created_at: str = ""


# =============================================================================
# Database Class
# =============================================================================


class Database:
    """
    SQLite database for storing Social Intelligence Engine data.

    Usage:
        # In-memory database (resets on restart)
        db = Database(":memory:")

        # File-based database (persists)
        db = Database("data/social_intel.db")

        # Initialize tables
        db.init_tables()

        # Insert data
        company_id = db.insert_company(company_data)

        # Query data
        entities = db.get_entities_by_company(company_id)
    """

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self.cursor = self.conn.cursor()

    def init_tables(self):
        """Create all tables if they don't exist"""

        # Companies table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                company_name TEXT,
                industry TEXT,
                description TEXT,
                keywords TEXT,  -- JSON array
                products TEXT,  -- JSON array
                technologies TEXT,  -- JSON array
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Subreddits table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subreddits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                title TEXT,
                description TEXT,
                subscribers INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                business_value_score REAL DEFAULT 0.0,
                discovery_methods TEXT,  -- JSON array
                matched_queries TEXT,  -- JSON array
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                UNIQUE(company_id, name)
            )
        """
        )

        # Posts table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subreddit_id INTEGER NOT NULL,
                reddit_id TEXT UNIQUE,
                title TEXT,
                body TEXT,
                score INTEGER DEFAULT 0,
                num_comments INTEGER DEFAULT 0,
                permalink TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subreddit_id) REFERENCES subreddits(id)
            )
        """
        )

        # Entities table (canonical entities)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                canonical_name TEXT NOT NULL,
                entity_type TEXT,  -- ORG, PERSON, PRODUCT
                aliases TEXT,  -- JSON array
                mention_count INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0.0,
                subreddits_found_in TEXT,  -- JSON array
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                UNIQUE(company_id, canonical_name)
            )
        """
        )

        # Mentions table (individual mentions with context)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                post_id INTEGER,
                raw_text TEXT,
                confidence REAL DEFAULT 0.0,
                match_method TEXT,
                context TEXT,
                subreddit TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id),
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        """
        )

        # Relationships table (entity relationships)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                source_entity TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                evidence_count INTEGER DEFAULT 0,
                evidence TEXT,  -- JSON array of evidence snippets
                source_posts TEXT,  -- JSON array of post IDs
                source_subreddits TEXT,  -- JSON array of subreddit names
                extraction_method TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                UNIQUE(company_id, source_entity, relationship_type, target_entity)
            )
        """
        )

        # Create indexes for faster queries
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_subreddits_company ON subreddits(company_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_company ON entities(company_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_mentions_entity ON mentions(entity_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_relationships_company ON relationships(company_id)"
        )

        self.conn.commit()
        print("Database tables initialized")

    # =========================================================================
    # Company Methods
    # =========================================================================

    def insert_company(self, data: dict) -> int:
        """Insert a company and return its ID"""
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO companies 
            (domain, company_name, industry, description, keywords, products, technologies)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.get("domain", ""),
                data.get("company_name", ""),
                data.get("industry", ""),
                data.get("description", ""),
                json.dumps(data.get("keywords", [])),
                json.dumps(data.get("products", [])),
                json.dumps(data.get("technologies", [])),
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_company(self, domain: str) -> Optional[dict]:
        """Get company by domain"""
        self.cursor.execute("SELECT * FROM companies WHERE domain = ?", (domain,))
        row = self.cursor.fetchone()
        if row:
            result = dict(row)
            result["keywords"] = json.loads(result["keywords"] or "[]")
            result["products"] = json.loads(result["products"] or "[]")
            result["technologies"] = json.loads(result["technologies"] or "[]")
            return result
        return None

    def get_company_by_id(self, company_id: int) -> Optional[dict]:
        """Get company by ID"""
        self.cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
        row = self.cursor.fetchone()
        if row:
            result = dict(row)
            result["keywords"] = json.loads(result["keywords"] or "[]")
            result["products"] = json.loads(result["products"] or "[]")
            result["technologies"] = json.loads(result["technologies"] or "[]")
            return result
        return None

    # =========================================================================
    # Subreddit Methods
    # =========================================================================

    def insert_subreddit(self, company_id: int, data: dict) -> int:
        """Insert a subreddit and return its ID"""
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO subreddits 
            (company_id, name, title, description, subscribers, active_users, 
             business_value_score, discovery_methods, matched_queries)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                company_id,
                data.get("name", ""),
                data.get("title", ""),
                data.get("description", ""),
                data.get("subscribers", 0),
                data.get("active_users", 0),
                data.get("business_value_score", 0.0),
                json.dumps(data.get("discovery_methods", [])),
                json.dumps(data.get("matched_queries", [])),
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_subreddits_bulk(
        self, company_id: int, subreddits: List[dict]
    ) -> List[int]:
        """Insert multiple subreddits"""
        ids = []
        for sub in subreddits:
            sub_id = self.insert_subreddit(company_id, sub)
            ids.append(sub_id)
        return ids

    def get_subreddits_by_company(self, company_id: int) -> List[dict]:
        """Get all subreddits for a company, ordered by score"""
        self.cursor.execute(
            """
            SELECT * FROM subreddits 
            WHERE company_id = ? 
            ORDER BY business_value_score DESC
        """,
            (company_id,),
        )

        results = []
        for row in self.cursor.fetchall():
            result = dict(row)
            result["discovery_methods"] = json.loads(
                result["discovery_methods"] or "[]"
            )
            result["matched_queries"] = json.loads(result["matched_queries"] or "[]")
            results.append(result)
        return results

    def get_subreddit_by_name(self, company_id: int, name: str) -> Optional[dict]:
        """Get subreddit by name"""
        self.cursor.execute(
            "SELECT * FROM subreddits WHERE company_id = ? AND name = ?",
            (company_id, name),
        )
        row = self.cursor.fetchone()
        if row:
            result = dict(row)
            result["discovery_methods"] = json.loads(
                result["discovery_methods"] or "[]"
            )
            result["matched_queries"] = json.loads(result["matched_queries"] or "[]")
            return result
        return None

    # =========================================================================
    # Post Methods
    # =========================================================================

    def insert_post(self, subreddit_id: int, data: dict) -> int:
        """Insert a post and return its ID"""
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO posts 
            (subreddit_id, reddit_id, title, body, score, num_comments, permalink)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                subreddit_id,
                data.get("id", data.get("reddit_id", "")),
                data.get("title", ""),
                data.get("selftext", data.get("body", "")),
                data.get("score", 0),
                data.get("num_comments", 0),
                data.get("permalink", ""),
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_posts_bulk(self, subreddit_id: int, posts: List[dict]) -> List[int]:
        """Insert multiple posts"""
        ids = []
        for post in posts:
            post_id = self.insert_post(subreddit_id, post)
            ids.append(post_id)
        return ids

    def get_posts_by_subreddit(self, subreddit_id: int, limit: int = 50) -> List[dict]:
        """Get posts for a subreddit"""
        self.cursor.execute(
            """
            SELECT * FROM posts 
            WHERE subreddit_id = ? 
            ORDER BY score DESC
            LIMIT ?
        """,
            (subreddit_id, limit),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def get_all_posts_by_company(self, company_id: int) -> List[dict]:
        """Get all posts for a company (across all subreddits)"""
        self.cursor.execute(
            """
            SELECT p.*, s.name as subreddit_name
            FROM posts p
            JOIN subreddits s ON p.subreddit_id = s.id
            WHERE s.company_id = ?
            ORDER BY p.score DESC
        """,
            (company_id,),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # =========================================================================
    # Entity Methods
    # =========================================================================

    def insert_entity(self, company_id: int, data: dict) -> int:
        """Insert an entity and return its ID"""
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO entities 
            (company_id, canonical_name, entity_type, aliases, mention_count, 
             avg_confidence, subreddits_found_in)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                company_id,
                data.get("canonical_name", ""),
                data.get("entity_type", "ORG"),
                json.dumps(data.get("aliases", [])),
                data.get("mention_count", 0),
                data.get("avg_confidence", 0.0),
                json.dumps(data.get("subreddits_found_in", [])),
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_entities_from_resolver(self, company_id: int, resolver) -> List[int]:
        """Insert all entities from an EntityResolver"""
        ids = []
        for entity in resolver.get_all_entities():
            entity_data = {
                "canonical_name": entity.canonical_name,
                "entity_type": entity.entity_type,
                "aliases": entity.aliases,
                "mention_count": entity.mention_count,
                "avg_confidence": entity.avg_confidence,
                "subreddits_found_in": entity.subreddits_mentioned_in,
            }
            entity_id = self.insert_entity(company_id, entity_data)
            ids.append(entity_id)

            # Insert mentions for this entity
            for mention in entity.mentions:
                self.insert_mention(
                    entity_id,
                    {
                        "raw_text": mention.raw_text,
                        "confidence": mention.confidence,
                        "match_method": mention.match_method,
                        "context": mention.context,
                        "subreddit": mention.source_subreddit,
                    },
                )

        return ids

    def get_entities_by_company(
        self, company_id: int, entity_type: str = None
    ) -> List[dict]:
        """Get entities for a company, optionally filtered by type"""
        if entity_type:
            self.cursor.execute(
                """
                SELECT * FROM entities 
                WHERE company_id = ? AND entity_type = ?
                ORDER BY mention_count DESC
            """,
                (company_id, entity_type),
            )
        else:
            self.cursor.execute(
                """
                SELECT * FROM entities 
                WHERE company_id = ?
                ORDER BY mention_count DESC
            """,
                (company_id,),
            )

        results = []
        for row in self.cursor.fetchall():
            result = dict(row)
            result["aliases"] = json.loads(result["aliases"] or "[]")
            result["subreddits_found_in"] = json.loads(
                result["subreddits_found_in"] or "[]"
            )
            results.append(result)
        return results

    def get_entity_by_name(
        self, company_id: int, canonical_name: str
    ) -> Optional[dict]:
        """Get entity by canonical name"""
        self.cursor.execute(
            "SELECT * FROM entities WHERE company_id = ? AND canonical_name = ?",
            (company_id, canonical_name),
        )
        row = self.cursor.fetchone()
        if row:
            result = dict(row)
            result["aliases"] = json.loads(result["aliases"] or "[]")
            result["subreddits_found_in"] = json.loads(
                result["subreddits_found_in"] or "[]"
            )
            return result
        return None

    # =========================================================================
    # Mention Methods
    # =========================================================================

    def insert_mention(self, entity_id: int, data: dict, post_id: int = None) -> int:
        """Insert a mention and return its ID"""
        self.cursor.execute(
            """
            INSERT INTO mentions 
            (entity_id, post_id, raw_text, confidence, match_method, context, subreddit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entity_id,
                post_id,
                data.get("raw_text", ""),
                data.get("confidence", 0.0),
                data.get("match_method", ""),
                data.get("context", ""),
                data.get("subreddit", ""),
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_mentions_by_entity(self, entity_id: int, limit: int = 50) -> List[dict]:
        """Get mentions for an entity"""
        self.cursor.execute(
            """
            SELECT * FROM mentions 
            WHERE entity_id = ?
            ORDER BY confidence DESC
            LIMIT ?
        """,
            (entity_id, limit),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # =========================================================================
    # Relationship Methods
    # =========================================================================

    def insert_relationship(self, company_id: int, data: dict) -> int:
        """Insert a relationship"""
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO relationships
            (company_id, source_entity, relationship_type, target_entity,
             confidence, evidence_count, evidence, source_posts,
             source_subreddits, extraction_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                company_id,
                data.get("source_entity", ""),
                data.get("relationship_type", ""),
                data.get("target_entity", ""),
                data.get("confidence", 0.0),
                data.get("evidence_count", 0),
                json.dumps(data.get("evidence", [])),
                json.dumps(data.get("source_posts", [])),
                json.dumps(data.get("source_subreddits", [])),
                data.get("extraction_method", ""),
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_relationships_bulk(self, company_id: int, relationships: List) -> int:
        """
        Bulk insert relationships from RelationshipExtractor.

        Args:
            company_id: Company ID
            relationships: List of EntityRelationship objects

        Returns:
            Number of relationships inserted
        """
        count = 0
        for rel in relationships:
            data = {
                "source_entity": rel.source_entity,
                "relationship_type": rel.relationship_type,
                "target_entity": rel.target_entity,
                "confidence": rel.confidence,
                "evidence_count": len(rel.evidence),
                "evidence": rel.evidence,
                "source_posts": rel.source_posts,
                "source_subreddits": rel.source_subreddits,
                "extraction_method": rel.extraction_method,
            }
            self.insert_relationship(company_id, data)
            count += 1

        return count

    def get_relationships_by_company(self, company_id: int, min_confidence: float = 0.5) -> List[dict]:
        """Get all relationships for a company"""
        self.cursor.execute(
            """
            SELECT * FROM relationships
            WHERE company_id = ? AND confidence >= ?
            ORDER BY confidence DESC
        """,
            (company_id, min_confidence),
        )
        rows = self.cursor.fetchall()

        # Parse JSON fields
        relationships = []
        for row in rows:
            rel_dict = dict(row)
            rel_dict["evidence"] = json.loads(rel_dict.get("evidence", "[]"))
            rel_dict["source_posts"] = json.loads(rel_dict.get("source_posts", "[]"))
            rel_dict["source_subreddits"] = json.loads(
                rel_dict.get("source_subreddits", "[]")
            )
            relationships.append(rel_dict)

        return relationships

    def get_relationships_by_entity(self, company_id: int, entity_name: str) -> List[dict]:
        """Get all relationships involving a specific entity (as source or target)"""
        self.cursor.execute(
            """
            SELECT * FROM relationships
            WHERE company_id = ? AND (source_entity = ? OR target_entity = ?)
            ORDER BY confidence DESC
        """,
            (company_id, entity_name, entity_name),
        )
        rows = self.cursor.fetchall()

        # Parse JSON fields
        relationships = []
        for row in rows:
            rel_dict = dict(row)
            rel_dict["evidence"] = json.loads(rel_dict.get("evidence", "[]"))
            rel_dict["source_posts"] = json.loads(rel_dict.get("source_posts", "[]"))
            rel_dict["source_subreddits"] = json.loads(
                rel_dict.get("source_subreddits", "[]")
            )
            relationships.append(rel_dict)

        return relationships

    def get_relationships_by_type(
        self, company_id: int, relationship_type: str
    ) -> List[dict]:
        """Get all relationships of a specific type"""
        self.cursor.execute(
            """
            SELECT * FROM relationships
            WHERE company_id = ? AND relationship_type = ?
            ORDER BY confidence DESC
        """,
            (company_id, relationship_type),
        )
        rows = self.cursor.fetchall()

        # Parse JSON fields
        relationships = []
        for row in rows:
            rel_dict = dict(row)
            rel_dict["evidence"] = json.loads(rel_dict.get("evidence", "[]"))
            rel_dict["source_posts"] = json.loads(rel_dict.get("source_posts", "[]"))
            rel_dict["source_subreddits"] = json.loads(
                rel_dict.get("source_subreddits", "[]")
            )
            relationships.append(rel_dict)

        return relationships

    # =========================================================================
    # Summary Methods
    # =========================================================================

    def get_summary(self, company_id: int) -> dict:
        """Get summary statistics for a company"""
        self.cursor.execute(
            "SELECT COUNT(*) FROM subreddits WHERE company_id = ?", (company_id,)
        )
        subreddit_count = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            SELECT COUNT(*) FROM posts p
            JOIN subreddits s ON p.subreddit_id = s.id
            WHERE s.company_id = ?
        """,
            (company_id,),
        )
        post_count = self.cursor.fetchone()[0]

        self.cursor.execute(
            "SELECT COUNT(*) FROM entities WHERE company_id = ?", (company_id,)
        )
        entity_count = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            SELECT COUNT(*) FROM mentions m
            JOIN entities e ON m.entity_id = e.id
            WHERE e.company_id = ?
        """,
            (company_id,),
        )
        mention_count = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            SELECT entity_type, COUNT(*) as count 
            FROM entities WHERE company_id = ?
            GROUP BY entity_type
        """,
            (company_id,),
        )
        entities_by_type = {
            row["entity_type"]: row["count"] for row in self.cursor.fetchall()
        }

        return {
            "subreddit_count": subreddit_count,
            "post_count": post_count,
            "entity_count": entity_count,
            "mention_count": mention_count,
            "entities_by_type": entities_by_type,
        }

    def close(self):
        """Close database connection"""
        self.conn.close()


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("Testing Database...")

    # Create in-memory database
    db = Database(":memory:")
    db.init_tables()

    # Insert test company
    company_id = db.insert_company(
        {
            "domain": "openai.com",
            "company_name": "OpenAI",
            "industry": "Artificial Intelligence",
            "description": "AI research company",
            "keywords": ["AI", "GPT", "ChatGPT"],
            "products": ["ChatGPT", "GPT-4", "DALL-E"],
            "technologies": ["Python", "PyTorch"],
        }
    )
    print(f"✅ Inserted company with ID: {company_id}")

    # Insert test subreddit
    sub_id = db.insert_subreddit(
        company_id,
        {
            "name": "OpenAI",
            "title": "OpenAI",
            "subscribers": 500000,
            "business_value_score": 0.95,
            "discovery_methods": ["direct_search", "post_search"],
        },
    )
    print(f"✅ Inserted subreddit with ID: {sub_id}")

    # Insert test entity
    entity_id = db.insert_entity(
        company_id,
        {
            "canonical_name": "OpenAI",
            "entity_type": "ORG",
            "aliases": ["openai", "open ai"],
            "mention_count": 10,
            "avg_confidence": 0.95,
        },
    )
    print(f"✅ Inserted entity with ID: {entity_id}")

    # Insert test mention
    mention_id = db.insert_mention(
        entity_id,
        {
            "raw_text": "Open AI",
            "confidence": 0.90,
            "match_method": "alias",
            "context": "...I think Open AI is great...",
            "subreddit": "technology",
        },
    )
    print(f"✅ Inserted mention with ID: {mention_id}")

    # Get summary
    summary = db.get_summary(company_id)
    print(f"\n📊 Summary: {summary}")

    # Get company
    company = db.get_company("openai.com")
    print(f"\n🏢 Company: {company['company_name']}")
    print(f"   Keywords: {company['keywords']}")

    db.close()
    print("\n✅ Database test complete!")
