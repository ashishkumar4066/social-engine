# subreddit_discovery_v2.py
"""
Subreddit Discovery with 3 Search Strategies

Strategy 1: Search subreddits by name (subreddits/search.json)
Strategy 2: Search posts and extract subreddits (search.json) ⭐ KEY
Strategy 3: Industry mapping (pre-defined seed list)

Usage:
    discovery = SubredditDiscovery()
    results = discovery.discover_subreddits('openai.com', top_n=20)
"""

import requests
import time
import math
from typing import List, Dict
from collections import defaultdict


class SubredditDiscovery:
    """
    Discover and rank relevant subreddits for a company using multiple strategies
    """
    
    # Pre-defined industry → subreddit mappings (Strategy 3)
    INDUSTRY_SUBREDDITS = {
        'AI & Machine Learning': [
            'MachineLearning', 'artificial', 'deeplearning', 'LocalLLaMA',
            'ChatGPT', 'OpenAI', 'singularity', 'ArtificialIntelligence',
            'learnmachinelearning', 'MLQuestions', 'LanguageTechnology',
            'GPT3', 'StableDiffusion', 'Futurology', 'ClaudeAI'
        ],
        'SaaS': [
            'SaaS', 'startups', 'Entrepreneur', 'smallbusiness',
            'marketing', 'digital_marketing', 'SEO', 'content_marketing',
            'sales', 'B2B_Sales', 'inbound_marketing'
        ],
        'Fintech': [
            'fintech', 'CryptoCurrency', 'Bitcoin', 'ethereum',
            'investing', 'stocks', 'personalfinance', 'FinancialPlanning',
            'payments', 'Banking', 'CreditCards'
        ],
        'E-commerce': [
            'ecommerce', 'shopify', 'FulfillmentByAmazon', 'AmazonSeller',
            'dropship', 'Entrepreneur', 'smallbusiness', 'retail'
        ],
        'Cloud & Infrastructure': [
            'aws', 'googlecloud', 'azure', 'devops', 'kubernetes',
            'docker', 'sysadmin', 'cloudcomputing', 'serverless'
        ],
        'Cybersecurity': [
            'cybersecurity', 'netsec', 'hacking', 'privacy',
            'security', 'InfoSecNews', 'AskNetsec'
        ],
        'Healthcare': [
            'HealthIT', 'healthcare', 'medicine', 'digitalhealth',
            'healthtech', 'nursing', 'pharmacy'
        ],
        'Developer Tools': [
            'programming', 'webdev', 'coding', 'learnprogramming',
            'softwareengineering', 'devops', 'github', 'vscode'
        ],
        'Technology': [
            'technology', 'tech', 'gadgets', 'programming',
            'software', 'startups', 'Futurology'
        ]
    }
    
    # Subreddits to exclude (too generic)
    BLACKLIST = {
        'askreddit', 'pics', 'funny', 'memes', 'news', 'worldnews',
        'todayilearned', 'tifu', 'showerthoughts', 'jokes', 'gaming',
        'movies', 'music', 'videos', 'gifs', 'aww', 'food', 'sports',
        'all', 'popular', 'home', 'announcements'
    }
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'SocialIntelligenceEngine/1.0 (Educational Project)'
        }
        self.base_url = "https://www.reddit.com"
        self.rate_limit_delay = 2  # seconds between requests
    
    def discover_subreddits(
        self, 
        domain: str, 
        top_n: int = 20,
        company_info: Dict = None
    ) -> List[Dict]:
        """
        Main method: Discover relevant subreddits using 3 strategies
        
        Args:
            domain: Company domain (e.g., 'openai.com')
            top_n: Number of top subreddits to return
            company_info: Pre-extracted company info (optional)
        
        Returns:
            List of top N subreddits with scores
        """
        print(f"\n{'='*80}")
        print(f"🔍 SUBREDDIT DISCOVERY FOR: {domain}")
        print(f"{'='*80}\n")
        
        # Step 1: Get company info if not provided
        if company_info is None:
            extractor = CompanyExtractor()
            company_info = extractor.extract(domain)
        
        # Step 2: Build search queries from keywords
        search_queries = self._build_search_queries(company_info)
        print(f"\n📝 Search Queries ({len(search_queries)}):")
        for q in search_queries[:8]:
            print(f"   • {q}")
        
        # Step 3: Run all 3 search strategies
        all_subreddits = {}  # Use dict to merge/deduplicate
        
        # Strategy 1: Search subreddits by name
        print(f"\n📌 Strategy 1: Subreddit Name Search...")
        strategy1_subs = self._strategy1_subreddit_search(search_queries)
        self._merge_subreddits(all_subreddits, strategy1_subs, "subreddit_search")
        print(f"   Found {len(strategy1_subs)} subreddits")
        
        # Strategy 2: Search posts and extract subreddits (MOST IMPORTANT)
        print(f"\n📌 Strategy 2: Post Search (finding where keywords are discussed)...")
        strategy2_subs = self._strategy2_post_search(search_queries)
        self._merge_subreddits(all_subreddits, strategy2_subs, "post_search")
        print(f"   Found {len(strategy2_subs)} subreddits from posts")
        
        # Strategy 3: Add industry-mapped subreddits
        industry = company_info.get('industry', 'Technology')
        print(f"\n📌 Strategy 3: Industry Mapping ({industry})...")
        strategy3_subs = self._strategy3_industry_mapping(industry)
        self._merge_subreddits(all_subreddits, strategy3_subs, "industry_mapping")
        print(f"   Added {len(strategy3_subs)} industry subreddits")
        
        print(f"\n📊 Total unique subreddits: {len(all_subreddits)}")
        
        # Step 4: Fetch full details for subreddits missing data
        print(f"\n📥 Fetching subreddit details...")
        self._enrich_subreddit_data(all_subreddits)
        
        # Step 5: Score and rank
        scored_subreddits = self._score_subreddits(
            list(all_subreddits.values()),
            company_info
        )
        
        # Step 6: Filter and return top N
        filtered = [s for s in scored_subreddits if (s.get('subscribers') or 0) >= 1000]
        top_subreddits = filtered[:top_n]
        
        self._print_results(top_subreddits)
        
        return top_subreddits
    
    def _build_search_queries(self, company_info: Dict) -> List[str]:
        """Build search queries from company info"""
        queries = []
        
        # Company name (highest priority)
        queries.append(company_info['company_name'])
        
        # Products
        queries.extend(company_info.get('products', [])[:5])
        
        # Keywords
        queries.extend(company_info.get('keywords', [])[:5])
        
        # Deduplicate and clean
        seen = set()
        clean_queries = []
        for q in queries:
            q_lower = q.lower().strip()
            if q_lower not in seen and len(q) > 2:
                seen.add(q_lower)
                clean_queries.append(q)
        
        return clean_queries[:12]  # Max 12 queries
    
    # =========================================================================
    # STRATEGY 1: Search subreddits by name/description
    # =========================================================================
    
    def _strategy1_subreddit_search(self, queries: List[str]) -> List[Dict]:
        """
        Search for subreddits whose name or description matches keywords
        
        API: reddit.com/subreddits/search.json
        """
        subreddits = {}
        
        for query in queries[:8]:  # Limit to avoid rate limits
            try:
                url = f"{self.base_url}/subreddits/search.json"
                params = {
                    'q': query,
                    'limit': 15,
                    'sort': 'relevance'
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('data', {}).get('children', []):
                    sub_data = item['data']
                    sub_name = sub_data['display_name']
                    sub_lower = sub_name.lower()
                    
                    # Skip blacklisted
                    if sub_lower in self.BLACKLIST:
                        continue
                    
                    if sub_lower not in subreddits:
                        subreddits[sub_lower] = {
                            'name': sub_name,
                            'subscribers': sub_data.get('subscribers', 0),
                            'description': sub_data.get('public_description', '')[:300],
                            'title': sub_data.get('title', ''),
                            'active_users': sub_data.get('active_user_count', 0),
                            'over_18': sub_data.get('over18', False),
                            'matched_queries': [query],
                            'discovery_methods': [],
                            'mention_count': 0
                        }
                    else:
                        # Add matched query
                        if query not in subreddits[sub_lower]['matched_queries']:
                            subreddits[sub_lower]['matched_queries'].append(query)
                
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f"   ⚠️ Error searching '{query}': {e}")
        
        return list(subreddits.values())
    
    # =========================================================================
    # STRATEGY 2: Search posts and extract subreddits (MOST IMPORTANT!)
    # =========================================================================
    
    def _strategy2_post_search(self, queries: List[str]) -> List[Dict]:
        """
        Search for POSTS containing keywords across ALL of Reddit,
        then extract which subreddits those posts are in.
        
        This finds relevant subreddits even when keywords have no dedicated subreddit!
        
        API: reddit.com/search.json (not /subreddits/search.json)
        
        Example: "GPT-4" has no r/GPT4, but posts about it are in:
                 r/OpenAI, r/ChatGPT, r/LocalLLaMA, r/MachineLearning
        """
        subreddit_mentions = defaultdict(lambda: {
            'name': '',
            'subscribers': 0,
            'description': '',
            'title': '',
            'active_users': 0,
            'over_18': False,
            'matched_queries': [],
            'discovery_methods': [],
            'mention_count': 0,
            'sample_posts': []
        })
        
        for query in queries[:8]:
            try:
                # Search posts across ALL of Reddit
                url = f"{self.base_url}/search.json"
                params = {
                    'q': query,
                    'limit': 50,           # Get more posts
                    'sort': 'relevance',
                    't': 'year',           # Last year
                    'type': 'link'         # Posts only
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('data', {}).get('children', []):
                    post = item['data']
                    sub_name = post.get('subreddit', '')
                    sub_lower = sub_name.lower()
                    
                    # Skip blacklisted
                    if sub_lower in self.BLACKLIST:
                        continue
                    
                    # Update subreddit data
                    sub = subreddit_mentions[sub_lower]
                    sub['name'] = sub_name
                    sub['mention_count'] += 1
                    
                    # Track which query found this
                    if query not in sub['matched_queries']:
                        sub['matched_queries'].append(query)
                    
                    # Store sample post titles (for context)
                    if len(sub['sample_posts']) < 3:
                        sub['sample_posts'].append({
                            'title': post.get('title', '')[:100],
                            'score': post.get('score', 0)
                        })
                
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f"   ⚠️ Error in post search for '{query}': {e}")
        
        # Convert to list, filtering empty
        return [s for s in subreddit_mentions.values() if s['name']]
    
    # =========================================================================
    # STRATEGY 3: Industry mapping (pre-defined seed list)
    # =========================================================================
    
    def _strategy3_industry_mapping(self, industry: str) -> List[Dict]:
        """
        Add pre-defined subreddits for the industry.
        This ensures we don't miss well-known relevant communities.
        """
        subreddits = []
        
        # Get subreddits for this industry
        industry_subs = self.INDUSTRY_SUBREDDITS.get(industry, [])
        
        # Always add Technology subreddits as fallback
        if industry != 'Technology':
            industry_subs = industry_subs + self.INDUSTRY_SUBREDDITS.get('Technology', [])
        
        # Deduplicate
        seen = set()
        for sub_name in industry_subs:
            if sub_name.lower() not in seen:
                seen.add(sub_name.lower())
                subreddits.append({
                    'name': sub_name,
                    'subscribers': 0,  # Will be fetched later
                    'description': '',
                    'title': '',
                    'active_users': 0,
                    'over_18': False,
                    'matched_queries': [industry],
                    'discovery_methods': [],
                    'mention_count': 0
                })
        
        return subreddits
    
    # =========================================================================
    # Helper methods
    # =========================================================================
    
    def _merge_subreddits(
        self, 
        all_subs: Dict, 
        new_subs: List[Dict], 
        method: str
    ):
        """Merge new subreddits into the master dict"""
        for sub in new_subs:
            key = sub['name'].lower()
            
            if key in all_subs:
                existing = all_subs[key]
                # Merge discovery methods
                if method not in existing['discovery_methods']:
                    existing['discovery_methods'].append(method)
                # Merge matched queries
                for q in sub.get('matched_queries', []):
                    if q not in existing['matched_queries']:
                        existing['matched_queries'].append(q)
                # Add mention counts
                existing['mention_count'] += sub.get('mention_count', 0)
                # Update subscriber count if better
                if sub.get('subscribers', 0) > existing.get('subscribers', 0):
                    existing['subscribers'] = sub['subscribers']
            else:
                sub['discovery_methods'] = [method]
                all_subs[key] = sub
    
    def _enrich_subreddit_data(self, all_subs: Dict):
        """Fetch full details for subreddits missing subscriber counts"""
        subs_to_fetch = [
            name for name, data in all_subs.items() 
            if data.get('subscribers', 0) == 0
        ]
        
        print(f"   Fetching details for {len(subs_to_fetch)} subreddits...")
        
        for sub_name in subs_to_fetch[:30]:  # Limit API calls
            try:
                sub_data = self.fetch_subreddit_data(all_subs[sub_name]['name'])
                
                if sub_data:
                    all_subs[sub_name]['subscribers'] = sub_data.get('subscribers', 0)
                    all_subs[sub_name]['active_users'] = sub_data.get('active_users', 0)
                    all_subs[sub_name]['description'] = sub_data.get('description', '')[:300]
                    all_subs[sub_name]['title'] = sub_data.get('title', '')
                
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                pass  # Skip errors silently
    
    def fetch_subreddit_data(self, subreddit_name: str) -> Dict:
        """
        Fetch subreddit data using simple .json endpoint
        
        URL: https://www.reddit.com/r/{subreddit}.json
        
        Returns subreddit info from the first listing
        """
        try:
            url = f"{self.base_url}/r/{subreddit_name}.json"
            params = {'limit': 1}  # We just need subreddit info, not many posts
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # The .json endpoint returns a listing with posts
            # Subreddit info is in each post's data
            if data.get('data', {}).get('children'):
                first_post = data['data']['children'][0]['data']
                
                return {
                    'name': first_post.get('subreddit', subreddit_name),
                    'subscribers': first_post.get('subreddit_subscribers', 0),
                    'subreddit_id': first_post.get('subreddit_id', ''),
                }
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error fetching r/{subreddit_name}: {e}")
            return None
    
    def fetch_subreddit_about(self, subreddit_name: str) -> Dict:
        """
        Fetch detailed subreddit info using /about.json endpoint
        
        URL: https://www.reddit.com/r/{subreddit}/about.json
        
        Returns full subreddit metadata including description, rules, etc.
        """
        try:
            url = f"{self.base_url}/r/{subreddit_name}/about.json"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json().get('data', {})
            
            return {
                'name': data.get('display_name', subreddit_name),
                'title': data.get('title', ''),
                'description': data.get('public_description', ''),
                'subscribers': data.get('subscribers', 0),
                'active_users': data.get('active_user_count', 0),
                'created_utc': data.get('created_utc', 0),
                'over_18': data.get('over18', False),
                'url': f"{self.base_url}/r/{subreddit_name}"
            }
            
        except Exception as e:
            print(f"   ⚠️ Error fetching r/{subreddit_name}/about: {e}")
            return None
    
    def fetch_subreddit_posts(
        self, 
        subreddit_name: str, 
        limit: int = 25,
        sort: str = 'hot'
    ) -> List[Dict]:
        """
        Fetch posts from a subreddit
        
        URL: https://www.reddit.com/r/{subreddit}.json
        
        Args:
            subreddit_name: Name of subreddit
            limit: Number of posts to fetch (max 100)
            sort: 'hot', 'new', 'top', 'rising'
        
        Returns:
            List of post data
        """
        try:
            url = f"{self.base_url}/r/{subreddit_name}/{sort}.json"
            params = {'limit': min(limit, 100)}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for item in data.get('data', {}).get('children', []):
                post = item['data']
                posts.append({
                    'id': post.get('id'),
                    'title': post.get('title'),
                    'author': post.get('author'),
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_utc': post.get('created_utc'),
                    'url': post.get('url'),
                    'selftext': post.get('selftext', '')[:500],  # Limit text length
                    'permalink': f"{self.base_url}{post.get('permalink', '')}"
                })
            
            return posts
            
        except Exception as e:
            print(f"   ⚠️ Error fetching posts from r/{subreddit_name}: {e}")
            return []
    
    def _score_subreddits(
        self, 
        subreddits: List[Dict],
        company_info: Dict
    ) -> List[Dict]:
        """
        Score subreddits based on business value.
        """
        print(f"\n📊 Scoring {len(subreddits)} subreddits...")
        
        if not subreddits:
            return []
        
        # ✅ BULLETPROOF: Helper function to safely get int values
        def safe_int(value):
            """Convert any value to int, defaulting to 0"""
            if value is None:
                return 0
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        
        # ✅ Calculate max values safely
        max_subscribers = 1
        max_mentions = 1
        max_active = 1
        
        for sub in subreddits:
            subs_count = safe_int(sub.get('subscribers'))
            mentions_count = safe_int(sub.get('mention_count'))
            active_count = safe_int(sub.get('active_users'))
            
            if subs_count > max_subscribers:
                max_subscribers = subs_count
            if mentions_count > max_mentions:
                max_mentions = mentions_count
            if active_count > max_active:
                max_active = active_count
        
        # Build keyword list for matching
        company_keywords = [company_info['company_name'].lower()]
        company_keywords += [kw.lower() for kw in company_info.get('keywords', [])[:10]]
        company_keywords += [p.lower() for p in company_info.get('products', [])[:5]]
        
        scored = []
        
        for sub in subreddits:
            # ✅ SAFE: Get all values with explicit None handling
            subscribers = safe_int(sub.get('subscribers'))
            mentions = safe_int(sub.get('mention_count'))
            active_users = safe_int(sub.get('active_users'))
            methods = sub.get('discovery_methods') or []
            name = str(sub.get('name') or '').lower()
            title = str(sub.get('title') or '').lower()
            description = str(sub.get('description') or '').lower()
            
            # 1. Topic Relevance (30%)
            text = name + ' ' + title + ' ' + description
            keyword_matches = sum(1 for kw in company_keywords if kw in text)
            topic_relevance = min(keyword_matches / 3, 1.0)
            
            # 2. Mention Frequency (25%)
            mention_score = mentions / max_mentions if max_mentions > 0 else 0
            
            # 3. Audience Size (20%) - Log scale
            if subscribers > 0 and max_subscribers > 0:
                import math
                audience_score = math.log10(subscribers + 1) / math.log10(max_subscribers + 1)
            else:
                audience_score = 0
            
            # 4. Engagement Quality (15%)
            if subscribers > 0:
                engagement_score = min(active_users / max(subscribers * 0.01, 1), 1.0)
            else:
                engagement_score = 0
            
            # 5. Discovery Methods (10%)
            method_score = min(len(methods) / 3, 1.0)
            
            # Calculate final score
            business_value = (
                0.30 * topic_relevance +
                0.25 * mention_score +
                0.20 * audience_score +
                0.15 * engagement_score +
                0.10 * method_score
            )
            
            # Store metrics
            sub['metrics'] = {
                'topic_relevance': round(topic_relevance, 3),
                'mention_score': round(mention_score, 3),
                'audience_score': round(audience_score, 3),
                'engagement_score': round(engagement_score, 3),
                'method_score': round(method_score, 3)
            }
            sub['business_value_score'] = round(business_value, 3)
            
            scored.append(sub)
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: x['business_value_score'], reverse=True)
        
        return scored
        
    def _calc_topic_relevance(self, sub: Dict, keywords: List[str]) -> float:
        """Calculate topic relevance based on name and title"""
        name = sub.get('name', '').lower()
        title = sub.get('title', '').lower()
        text = name + ' ' + title
        
        matches = sum(1 for kw in keywords if kw in text)
        return min(matches / 3, 1.0)
    
    def _calc_description_match(self, sub: Dict, keywords: List[str]) -> float:
        """Calculate description match score"""
        desc = sub.get('description', '').lower()
        if not desc:
            return 0.0
        
        matches = sum(1 for kw in keywords if kw in desc)
        return min(matches / 5, 1.0)
    
    def _print_results(self, top_subreddits: List[Dict]):
        """Print formatted results"""
        print(f"\n{'='*80}")
        print(f"🏆 TOP {len(top_subreddits)} SUBREDDITS")
        print(f"{'='*80}\n")
        
        print(f"{'Rank':<5} {'Subreddit':<25} {'Subscribers':>12} {'Score':>8} {'Found By'}")
        print("-" * 80)
        
        for i, sub in enumerate(top_subreddits, 1):
            methods = ", ".join(sub.get('discovery_methods', [])[:2])
            print(f"{i:<5} r/{sub['name']:<24} {sub['subscribers']:>12,} {sub['business_value_score']:>8.3f} {methods}")


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    # Test with mock company info (no Wikipedia API needed)
    mock_company_info = {
        'company_name': 'OpenAI',
        'keywords': ['artificial intelligence', 'machine learning', 'GPT', 'language model'],
        'products': ['ChatGPT', 'GPT-4', 'DALL-E', 'Codex', 'Whisper'],
        'industry': 'AI & Machine Learning',
        'description': 'OpenAI is an AI research company'
    }
    
    discovery = SubredditDiscovery()
    
    # Run discovery
    top_subreddits = discovery.discover_subreddits(
        domain='openai.com',
        top_n=20,
        company_info=mock_company_info
    )
    
    # Detailed results
    print("\n" + "="*80)
    print("📋 DETAILED RESULTS")
    print("="*80 + "\n")
    
    for i, sub in enumerate(top_subreddits[:10], 1):
        print(f"{i}. r/{sub['name']}")
        print(f"   Score: {sub['business_value_score']:.3f}")
        print(f"   Subscribers: {sub['subscribers']:,}")
        print(f"   Found by: {', '.join(sub['discovery_methods'])}")
        print(f"   Matched queries: {', '.join(sub['matched_queries'][:3])}")
        print(f"   Metrics: {sub['metrics']}")
        print()