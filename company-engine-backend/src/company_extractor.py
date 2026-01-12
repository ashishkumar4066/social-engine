# company_extractor.py
"""
Combined company information extraction.
Uses Wikipedia for data + spaCy for keyword extraction.

Usage:
    extractor = CompanyExtractor()
    result = extractor.extract("openai.com")
    
    print(result.keywords)  # Use these for Reddit search
"""

from dataclasses import dataclass, field
from typing import Optional

from src.keyword_extractor import KeywordExtractor
from src.wikipedia_extractor import WikipediaExtractor

@dataclass
class CompanyInfo:
    """Complete company information for subreddit discovery."""
    
    # Basic info
    domain: str
    company_name: str
    
    # From Wikipedia
    description: str
    page_url: str
    categories: list[str]
    
    # From Keyword Extraction
    keywords: list[str]           # Final keywords for Reddit search
    products: list[str]           # Product names
    technologies: list[str]       # Technology terms
    entities: list[dict]          # Named entities with types
    industry: str                 # Classified industry
    
    # Metadata
    source: str                   # 'wikipedia', 'heuristic', etc.
    success: bool
    error_message: Optional[str] = None


class CompanyExtractor:
    """
    Extracts comprehensive company information from a domain.
    Combines Wikipedia data with NLP keyword extraction.
    """
    
    def __init__(self):
        self.wiki_extractor = WikipediaExtractor()
        self.keyword_extractor = KeywordExtractor()
    
    def extract(self, domain: str) -> CompanyInfo:
        """
        Extract company information from domain.
        
        Args:
            domain: Company domain (e.g., 'openai.com')
            
        Returns:
            CompanyInfo with keywords ready for Reddit search
        """
        # Clean domain
        domain = domain.lower().replace('https://', '').replace('http://', '')
        domain = domain.replace('www.', '').strip('/')
        
        print(f"\n{'#'*60}")
        print(f"# COMPANY EXTRACTION: {domain}")
        print(f"{'#'*60}")
        
        # Step 1: Get Wikipedia data
        wiki_result = self.wiki_extractor.extract(domain)
        
        if wiki_result.success:
            # Step 2: Extract keywords from Wikipedia text
            keywords_result = self.keyword_extractor.extract(
                text=wiki_result.full_text,
                company_name=wiki_result.company_name,
                categories=wiki_result.categories
            )
            
            return CompanyInfo(
                domain=domain,
                company_name=wiki_result.company_name,
                description=wiki_result.description,
                page_url=wiki_result.page_url,
                categories=wiki_result.categories,
                keywords=keywords_result.all_keywords,
                products=keywords_result.products,
                technologies=keywords_result.technologies,
                entities=keywords_result.entities,
                industry=keywords_result.industry,
                source='wikipedia',
                success=True
            )
        
        # Fallback: Use heuristic extraction
        print(f"\n⚠️ Wikipedia failed, using heuristic fallback")
        return self._heuristic_extraction(domain, wiki_result.company_name)
    
    def _heuristic_extraction(self, domain: str, company_name: str) -> CompanyInfo:
        """
        Fallback extraction when Wikipedia is unavailable.
        Uses domain patterns and predefined industry mappings.
        """
        
        domain_lower = domain.lower()
        name_lower = company_name.lower()
        
        # Industry patterns
        industry_patterns = {
            'AI & Machine Learning': ['ai', 'ml', 'openai', 'anthropic', 'deepmind', 'neural', 'gpt', 'llm'],
            'Cloud & Infrastructure': ['cloud', 'aws', 'azure', 'host', 'server', 'infra'],
            'E-commerce': ['shop', 'store', 'buy', 'sell', 'commerce', 'market', 'retail'],
            'Fintech': ['pay', 'bank', 'fin', 'wallet', 'credit', 'stripe', 'money'],
            'Social Media': ['social', 'chat', 'message', 'connect', 'friend'],
            'Developer Tools': ['git', 'code', 'dev', 'build', 'deploy', 'api'],
            'Productivity': ['notion', 'slack', 'asana', 'monday', 'task', 'project'],
        }
        
        # Find matching industry
        industry = 'Technology'
        combined = domain_lower + ' ' + name_lower
        
        for ind_name, patterns in industry_patterns.items():
            if any(p in combined for p in patterns):
                industry = ind_name
                break
        
        # Generate basic keywords
        keywords = [company_name]
        
        # Add industry-related keywords
        industry_keywords = {
            'AI & Machine Learning': ['artificial intelligence', 'machine learning', 'AI'],
            'Cloud & Infrastructure': ['cloud', 'infrastructure', 'platform'],
            'E-commerce': ['ecommerce', 'online shopping', 'marketplace'],
            'Fintech': ['fintech', 'payments', 'financial technology'],
            'Social Media': ['social media', 'social network', 'platform'],
            'Developer Tools': ['developer tools', 'software development', 'API'],
            'Productivity': ['productivity', 'collaboration', 'software'],
            'Technology': ['technology', 'software', 'platform'],
        }
        
        keywords.extend(industry_keywords.get(industry, ['technology', 'software']))
        
        return CompanyInfo(
            domain=domain,
            company_name=company_name,
            description=f"{company_name} is a company in the {industry} sector.",
            page_url="",
            categories=[],
            keywords=keywords,
            products=[],
            technologies=[],
            entities=[],
            industry=industry,
            source='heuristic',
            success=True,
            error_message="Wikipedia unavailable, used heuristic extraction"
        )


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    extractor = CompanyExtractor()
    
    test_domains = [
        'openai.com',
        'hubspot.com',
        'stripe.com',
        'anthropic.com',
    ]
    
    for domain in test_domains:
        result = extractor.extract(domain)
        
        print(f"\n{'#'*60}")
        print(f"# FINAL RESULT: {domain}")
        print(f"{'#'*60}")
        print(f"   Company: {result.company_name}")
        print(f"   Industry: {result.industry}")
        print(f"   Source: {result.source}")
        print(f"   Success: {result.success}")
        print(f"\n   📦 Products: {', '.join(result.products[:5]) if result.products else 'None'}")
        print(f"   💻 Technologies: {', '.join(result.technologies[:5]) if result.technologies else 'None'}")
        
        print(f"\n   🔑 KEYWORDS FOR REDDIT SEARCH:")
        for i, kw in enumerate(result.keywords[:10], 1):
            print(f"      {i:2}. {kw}")
        
        print(f"\n   📝 Description: {result.description[:150]}...")
        print()