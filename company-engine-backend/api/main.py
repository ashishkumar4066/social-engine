# api/main.py
"""
FastAPI Application for Social Intelligence Engine

Provides REST API endpoints to:
- Analyze new companies (runs full pipeline if not exists)
- Browse companies
- View discovered subreddits
- Browse entities and their mentions
- Get summary statistics

Run with:
    uvicorn api.main:app --reload --port 8000
"""

import os
import sys
from typing import List, Optional, Dict
from dataclasses import asdict
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import Database
from src.company_extractor import CompanyExtractor
from src.reddit.subreddit_discovery import SubredditDiscovery
from src.reddit.reddit_client import RedditClient
from src.entity.entity_extractor import EntityExtractor

# =============================================================================
# Pydantic Models (for API responses)
# =============================================================================


class CompanyResponse(BaseModel):
    id: int
    domain: str
    company_name: str
    industry: str
    description: str
    keywords: List[str]
    products: List[str]
    technologies: List[str]


class SubredditResponse(BaseModel):
    id: int
    name: str
    title: str
    description: str
    subscribers: int
    active_users: int
    business_value_score: float
    discovery_methods: List[str]


class EntityResponse(BaseModel):
    id: int
    canonical_name: str
    entity_type: str
    aliases: List[str]
    mention_count: int
    avg_confidence: float
    subreddits_found_in: List[str]


class MentionResponse(BaseModel):
    id: int
    raw_text: str
    confidence: float
    match_method: str
    context: str
    subreddit: str


class SummaryResponse(BaseModel):
    subreddit_count: int
    post_count: int
    entity_count: int
    mention_count: int
    entities_by_type: dict


class RelationshipResponse(BaseModel):
    id: int
    source_entity: str
    relationship_type: str
    target_entity: str
    confidence: float
    evidence_count: int
    evidence: List[str]
    source_posts: List[str]
    source_subreddits: List[str]
    extraction_method: str


class AnalyzeRequest(BaseModel):
    domain: str
    top_n: int = 20
    fetch_posts_from: int = 5


class AnalyzeResponse(BaseModel):
    company_id: int
    company: CompanyResponse
    message: str
    already_existed: bool


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Social Intelligence Engine API",
    description="API for browsing Reddit entity analysis results",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DB_PATH = os.environ.get("DATABASE_PATH", "data/social_intel.db")
db = None


def get_db():
    """Get or create database connection"""
    global db
    if db is None:
        # Create data directory if needed
        data_dir = os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else "data"
        os.makedirs(data_dir, exist_ok=True)

        db = Database(DB_PATH)
        db.init_tables()  # Ensure tables are created
    return db


# =============================================================================
# Pipeline Function
# =============================================================================


async def run_pipeline(domain: str, top_n: int = 20, fetch_posts_from: int = 5) -> Dict:
    """
    Run the complete Social Intelligence Engine pipeline.

    Args:
        domain: Company domain (e.g., 'openai.com')
        top_n: Number of top subreddits to return
        fetch_posts_from: Number of top subreddits to fetch posts from

    Returns:
        Dict containing company_id, company_info, subreddits, posts, and summary
    """
    db = get_db()

    # =========================================================================
    # STEP 1: Extract Company Information
    # =========================================================================

    extractor = CompanyExtractor()
    company_info = extractor.extract(domain)

    if not company_info.success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract company information for {domain}"
        )

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

    # =========================================================================
    # STEP 2: Discover Relevant Subreddits
    # =========================================================================

    discovery = SubredditDiscovery()
    company_info_dict = asdict(company_info)

    top_subreddits = discovery.discover_subreddits(
        domain=domain, top_n=top_n, company_info=company_info_dict
    )

    # Save subreddits to database
    db.insert_subreddits_bulk(company_id, top_subreddits)

    # =========================================================================
    # STEP 3: Fetch Posts from Top Subreddits
    # =========================================================================

    reddit_client = RedditClient(rate_limit_delay=2.0)
    all_posts = []

    for sub in top_subreddits[:fetch_posts_from]:
        sub_name = sub.get("name", "")
        if not sub_name:
            continue

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

        except Exception as e:
            # Continue even if one subreddit fails
            print(f"Warning: Failed to fetch posts from r/{sub_name}: {e}")
            continue

    # =========================================================================
    # STEP 4: Extract and Resolve Entities
    # =========================================================================

    entity_extractor = EntityExtractor()
    resolver = entity_extractor.extract_from_posts(all_posts)

    # Save entities to database
    db.insert_entities_from_resolver(company_id, resolver)

    # =========================================================================
    # Get Summary
    # =========================================================================

    summary = db.get_summary(company_id)

    return {
        "company_id": company_id,
        "company_info": company_dict,
        "subreddits": top_subreddits,
        "posts": all_posts,
        "summary": summary,
    }


# =============================================================================
# API Endpoints
# =============================================================================


@app.get("/")
async def root():
    """Root endpoint - returns API information"""
    return {
        "title": "Social Intelligence Engine API",
        "description": "API for browsing Reddit entity analysis results",
        "version": "1.0.0",
        "endpoints": [
            {
                "method": "POST",
                "path": "/companies/analyze",
                "description": "Analyze a company by domain (auto-creates if not exists)"
            },
            {
                "method": "GET",
                "path": "/companies",
                "description": "List all analyzed companies"
            },
            {
                "method": "GET",
                "path": "/companies/{company_id}",
                "description": "Get company details"
            },
            {
                "method": "GET",
                "path": "/companies/{company_id}/subreddits",
                "description": "Get discovered subreddits for a company"
            },
            {
                "method": "GET",
                "path": "/companies/{company_id}/entities",
                "description": "Get resolved entities for a company"
            },
            {
                "method": "GET",
                "path": "/entities/{entity_id}/mentions",
                "description": "Get mentions for an entity with context"
            },
            {
                "method": "GET",
                "path": "/companies/{company_id}/summary",
                "description": "Get summary statistics"
            },
            {
                "method": "GET",
                "path": "/companies/{company_id}/relationships",
                "description": "Get relationships for a company"
            },
            {
                "method": "GET",
                "path": "/companies/{company_id}/relationships/entity/{entity_name}",
                "description": "Get relationships for a specific entity"
            }
        ],
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.post("/companies/analyze", response_model=AnalyzeResponse)
async def analyze_company(request: AnalyzeRequest):
    """
    Analyze a company by domain. If the company doesn't exist in the database,
    runs the full pipeline to extract company info, discover subreddits, fetch posts,
    and extract entities. If it already exists, returns the existing data.

    Args:
        request: AnalyzeRequest with domain and optional parameters

    Returns:
        AnalyzeResponse with company_id, company data, and status
    """
    db = get_db()

    # Clean the domain
    domain = (
        request.domain.replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .strip()
    )

    # Check if company already exists
    db.cursor.execute("SELECT * FROM companies WHERE domain = ?", (domain,))
    existing = db.cursor.fetchone()

    if existing:
        # Company already exists, return existing data
        import json

        company_data = {
            "id": existing["id"],
            "domain": existing["domain"],
            "company_name": existing["company_name"],
            "industry": existing["industry"],
            "description": existing["description"] or "",
            "keywords": json.loads(existing["keywords"] or "[]"),
            "products": json.loads(existing["products"] or "[]"),
            "technologies": json.loads(existing["technologies"] or "[]"),
        }

        return {
            "company_id": existing["id"],
            "company": company_data,
            "message": f"Company {existing['company_name']} already exists in database",
            "already_existed": True,
        }

    # Company doesn't exist, run the pipeline
    try:
        result = await run_pipeline(
            domain=domain,
            top_n=request.top_n,
            fetch_posts_from=request.fetch_posts_from,
        )

        company_info = result["company_info"]
        company_data = {
            "id": result["company_id"],
            "domain": company_info["domain"],
            "company_name": company_info["company_name"],
            "industry": company_info["industry"],
            "description": company_info["description"],
            "keywords": company_info["keywords"],
            "products": company_info["products"],
            "technologies": company_info["technologies"],
        }

        return {
            "company_id": result["company_id"],
            "company": company_data,
            "message": f"Successfully analyzed {company_info['company_name']}",
            "already_existed": False,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze company {domain}: {str(e)}"
        )


@app.get("/companies", response_model=List[CompanyResponse])
async def list_companies():
    """List all analyzed companies"""
    db = get_db()
    db.cursor.execute("SELECT * FROM companies ORDER BY created_at DESC")
    rows = db.cursor.fetchall()

    results = []
    for row in rows:
        import json

        results.append(
            {
                "id": row["id"],
                "domain": row["domain"],
                "company_name": row["company_name"],
                "industry": row["industry"],
                "description": row["description"] or "",
                "keywords": json.loads(row["keywords"] or "[]"),
                "products": json.loads(row["products"] or "[]"),
                "technologies": json.loads(row["technologies"] or "[]"),
            }
        )

    return results


@app.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int):
    """Get company details by ID"""
    db = get_db()
    company = db.get_company_by_id(company_id)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company


@app.get("/companies/{company_id}/subreddits", response_model=List[SubredditResponse])
async def get_company_subreddits(company_id: int, limit: int = Query(20, ge=1, le=100)):
    """Get discovered subreddits for a company"""
    db = get_db()
    subreddits = db.get_subreddits_by_company(company_id)

    return subreddits[:limit]


@app.get("/companies/{company_id}/entities", response_model=List[EntityResponse])
async def get_company_entities(
    company_id: int,
    entity_type: Optional[str] = Query(
        None, description="Filter by type: ORG, PERSON, PRODUCT"
    ),
    limit: int = Query(50, ge=1, le=200),
):
    """Get resolved entities for a company"""
    db = get_db()
    entities = db.get_entities_by_company(company_id, entity_type)

    return entities[:limit]


@app.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: int):
    """Get entity details by ID"""
    db = get_db()
    db.cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
    row = db.cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Entity not found")

    import json

    return {
        "id": row["id"],
        "canonical_name": row["canonical_name"],
        "entity_type": row["entity_type"],
        "aliases": json.loads(row["aliases"] or "[]"),
        "mention_count": row["mention_count"],
        "avg_confidence": row["avg_confidence"],
        "subreddits_found_in": json.loads(row["subreddits_found_in"] or "[]"),
    }


@app.get("/entities/{entity_id}/mentions", response_model=List[MentionResponse])
async def get_entity_mentions(entity_id: int, limit: int = Query(50, ge=1, le=200)):
    """Get mentions for an entity with context"""
    db = get_db()
    mentions = db.get_mentions_by_entity(entity_id, limit)

    return mentions


@app.get("/companies/{company_id}/summary", response_model=SummaryResponse)
async def get_company_summary(company_id: int):
    """Get summary statistics for a company"""
    db = get_db()
    summary = db.get_summary(company_id)

    return summary


@app.get("/companies/{company_id}/relationships", response_model=List[RelationshipResponse])
async def get_company_relationships(
    company_id: int,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence score")
):
    """
    Get all relationships for a company with optional confidence filtering.

    Args:
        company_id: The company ID
        min_confidence: Minimum confidence score (0.0 to 1.0)

    Returns:
        List of relationships involving entities related to the company
    """
    db = get_db()
    relationships = db.get_relationships_by_company(company_id, min_confidence)

    return relationships


@app.get("/companies/{company_id}/relationships/entity/{entity_name}", response_model=List[RelationshipResponse])
async def get_entity_relationships(
    company_id: int,
    entity_name: str
):
    """
    Get all relationships involving a specific entity.

    Args:
        company_id: The company ID
        entity_name: The name of the entity

    Returns:
        List of relationships where the entity is either source or target
    """
    db = get_db()
    relationships = db.get_relationships_by_entity(company_id, entity_name)

    return relationships


# =============================================================================
# Health Check
# =============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": DB_PATH}


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
