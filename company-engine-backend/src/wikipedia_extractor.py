# wikipedia_extractor.py
"""
Wikipedia API client for extracting company information.
Uses the official MediaWiki API (not scraping).

Usage:
    extractor = WikipediaExtractor()
    result = extractor.extract("openai.com")
    
    if result.success:
        print(result.full_text)  # Pass this to KeywordExtractor
"""

import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class WikipediaResult:
    """Data class for Wikipedia extraction results."""
    company_name: str
    description: str          # First 500 chars (intro)
    full_text: str            # Full article text (for keyword extraction)
    categories: list[str]     # Wikipedia categories
    page_title: str
    page_url: str
    success: bool
    error_message: Optional[str] = None


class WikipediaExtractor:
    """
    Extracts company information from Wikipedia using the official API.
    """
    
    BASE_URL = "https://en.wikipedia.org/w/api.php"
    
    # Known company name mappings (domain -> Wikipedia search term)
    COMPANY_NAME_MAP = {
        'openai': 'OpenAI',
        'anthropic': 'Anthropic',
        'huggingface': 'Hugging Face',
        'deepmind': 'DeepMind',
        'linkedin': 'LinkedIn',
        'github': 'GitHub',
        'youtube': 'YouTube',
        'facebook': 'Meta Platforms',
        'meta': 'Meta Platforms',
        'instagram': 'Instagram',
        'tiktok': 'TikTok',
        'netflix': 'Netflix',
        'spotify': 'Spotify',
        'shopify': 'Shopify',
        'salesforce': 'Salesforce',
        'stripe': 'Stripe',
        'paypal': 'PayPal',
        'airbnb': 'Airbnb',
        'uber': 'Uber',
        'lyft': 'Lyft',
        'doordash': 'DoorDash',
        'hubspot': 'HubSpot',
        'slack': 'Slack Technologies',
        'zoom': 'Zoom Video Communications',
        'dropbox': 'Dropbox',
        'atlassian': 'Atlassian',
        'twilio': 'Twilio',
        'cloudflare': 'Cloudflare',
        'datadog': 'Datadog',
        'snowflake': 'Snowflake Inc.',
        'palantir': 'Palantir Technologies',
        'databricks': 'Databricks',
        'notion': 'Notion (productivity software)',
        'figma': 'Figma',
        'canva': 'Canva',
        'airtable': 'Airtable',
        'asana': 'Asana (software)',
        'monday': 'Monday.com',
        'google': 'Google',
        'microsoft': 'Microsoft',
        'amazon': 'Amazon (company)',
        'apple': 'Apple Inc.',
        'tesla': 'Tesla, Inc.',
        'nvidia': 'Nvidia',
        'intel': 'Intel',
        'amd': 'AMD',
        'oracle': 'Oracle Corporation',
        'ibm': 'IBM',
        'adobe': 'Adobe Inc.',
        'twitter': 'Twitter',
        'x': 'Twitter',  # X.com -> Twitter
    }
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the Wikipedia extractor.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SocialIntelligenceEngine/1.0 (Educational Project)'
        })
    
    def get_company_name_from_domain(self, domain: str) -> str:
        """
        Extract and normalize company name from domain.
        
        Args:
            domain: Company domain (e.g., 'openai.com')
            
        Returns:
            Normalized company name for Wikipedia search
        """
        # Clean domain
        name = domain.lower().replace('www.', '').split('.')[0]
        
        # Check known mappings
        if name in self.COMPANY_NAME_MAP:
            return self.COMPANY_NAME_MAP[name]
        
        # Default: capitalize
        return name.capitalize()
    
    def extract(self, domain: str) -> WikipediaResult:
        """
        Extract company information from Wikipedia.
        
        Args:
            domain: Company domain (e.g., 'openai.com')
            
        Returns:
            WikipediaResult with extracted data
        """
        company_name = self.get_company_name_from_domain(domain)
        
        print(f"\n{'='*60}")
        print(f"🔍 Wikipedia Extractor")
        print(f"{'='*60}")
        print(f"   Domain: {domain}")
        print(f"   Searching for: {company_name}")
        
        # Try different search variations
        search_variations = [
            company_name,
            f"{company_name} (company)",
            f"{company_name} (software)",
            f"{company_name} Inc.",
            f"{company_name} Corporation",
        ]
        
        for search_term in search_variations:
            result = self._search_and_extract(search_term, company_name)
            if result.success:
                print(f"   ✅ Found: '{result.page_title}'")
                print(f"   📄 Text length: {len(result.full_text)} chars")
                print(f"   🏷️  Categories: {len(result.categories)}")
                return result
        
        # All variations failed
        print(f"   ❌ No Wikipedia page found")
        return WikipediaResult(
            company_name=company_name,
            description="",
            full_text="",
            categories=[],
            page_title="",
            page_url="",
            success=False,
            error_message="No Wikipedia page found for this company"
        )
    
    def _search_and_extract(self, search_term: str, company_name: str) -> WikipediaResult:
        """
        Search Wikipedia and extract page content.
        """
        try:
            # Step 1: Search for the page
            page_title = self._search_page(search_term)
            if not page_title:
                return self._empty_result(company_name, "Page not found")
            
            # Step 2: Get page content
            content = self._get_page_content(page_title)
            if not content:
                return self._empty_result(company_name, "Could not fetch content")
            
            # Step 3: Validate content is about a company
            extract = content['extract']
            if len(extract) < 100:
                return self._empty_result(company_name, "Content too short")
            
            # Extract first 5 lines for description, but truncate at last full stop
            lines = extract.split('\n')
            description = '\n'.join(lines[:5]).strip()
            description = self._truncate_at_last_sentence(description)

            return WikipediaResult(
                company_name=company_name,
                description=description,
                full_text=extract,
                categories=content['categories'],
                page_title=page_title,
                page_url=f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
                success=True
            )
            
        except requests.exceptions.Timeout:
            return self._empty_result(company_name, "Request timeout")
        except requests.exceptions.RequestException as e:
            return self._empty_result(company_name, f"Request error: {e}")
        except Exception as e:
            return self._empty_result(company_name, f"Error: {e}")
    
    def _search_page(self, search_term: str) -> Optional[str]:
        """
        Search for a Wikipedia page title.
        
        Returns:
            Page title if found, None otherwise
        """
        params = {
            'action': 'opensearch',
            'search': search_term,
            'limit': 1,
            'format': 'json'
        }
        
        response = self.session.get(
            self.BASE_URL,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        
        # opensearch returns: [search_term, [titles], [descriptions], [urls]]
        if data and len(data) > 1 and data[1]:
            return data[1][0]
        
        return None
    
    def _get_page_content(self, page_title: str) -> Optional[dict]:
        """
        Get Wikipedia page content (full text + categories).
        
        Returns:
            Dict with 'extract' and 'categories', or None
        """
        params = {
            'action': 'query',
            'titles': page_title,
            'prop': 'extracts|categories',
            'format': 'json',
            'explaintext': True,       # Plain text (no HTML)
            'exsectionformat': 'plain',
            'redirects': 1,            # Follow redirects
            'cllimit': 30,             # Max categories
        }
        
        response = self.session.get(
            self.BASE_URL,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        
        if not pages:
            return None
        
        # Get the first page
        page_id = list(pages.keys())[0]
        
        # -1 means page not found
        if page_id == '-1':
            return None
        
        page_data = pages[page_id]
        extract = page_data.get('extract', '')
        
        if not extract:
            return None
        
        # Extract categories (remove "Category:" prefix)
        categories = []
        for cat in page_data.get('categories', []):
            cat_title = cat.get('title', '').replace('Category:', '')
            if cat_title and not cat_title.startswith('Articles'):  # Skip meta categories
                categories.append(cat_title)
        
        return {
            'extract': extract,
            'categories': categories
        }
    
    def _truncate_at_last_sentence(self, text: str) -> str:
        """
        Truncate text at the last complete sentence (ending with a period).

        Args:
            text: The text to truncate

        Returns:
            Text truncated at the last full stop, or original text if no full stop found
        """
        if not text:
            return text

        # Find the last period that ends a sentence (not part of abbreviations like Inc. or Co.)
        last_period_idx = text.rfind('.')

        if last_period_idx == -1:
            # No period found, return original text
            return text

        # Return text up to and including the last period
        return text[:last_period_idx + 1].strip()

    def _empty_result(self, company_name: str, error_message: str) -> WikipediaResult:
        """Create an empty result with error message."""
        return WikipediaResult(
            company_name=company_name,
            description="",
            full_text="",
            categories=[],
            page_title="",
            page_url="",
            success=False,
            error_message=error_message
        )


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    extractor = WikipediaExtractor()
    
    test_domains = [
        'openai.com',
        'hubspot.com',
        'stripe.com',
    ]
    
    for domain in test_domains:
        result = extractor.extract(domain)
        
        print(f"\n{'='*60}")
        print(f"📊 RESULT: {domain}")
        print(f"{'='*60}")
        print(f"   Success: {result.success}")
        print(f"   Company: {result.company_name}")
        print(f"   Page: {result.page_title}")
        print(f"   URL: {result.page_url}")
        print(f"   Text length: {len(result.full_text)} chars")
        print(f"   Categories: {result.categories[:5]}")
        print(f"   Description: {result.description[:200]}...")