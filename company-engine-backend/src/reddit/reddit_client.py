# reddit_client.py
"""
Reddit JSON API Client (No Authentication Required)

Uses Reddit's public .json endpoints for data fetching.
No API keys needed - just add .json to any Reddit URL!

Endpoints:
- https://www.reddit.com/r/{subreddit}.json          → Subreddit posts
- https://www.reddit.com/r/{subreddit}/about.json   → Subreddit info
- https://www.reddit.com/r/{subreddit}/hot.json     → Hot posts
- https://www.reddit.com/r/{subreddit}/new.json     → New posts
- https://www.reddit.com/r/{subreddit}/top.json     → Top posts
- https://www.reddit.com/search.json?q=query        → Search posts
- https://www.reddit.com/subreddits/search.json     → Search subreddits

Usage:
    client = RedditClient()
    
    # Get subreddit info
    info = client.get_subreddit_info("OpenAI")
    
    # Get posts
    posts = client.get_subreddit_posts("OpenAI", limit=50)
    
    # Search across Reddit
    results = client.search_posts("ChatGPT", limit=100)
"""

import requests
import time
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SubredditInfo:
    """Subreddit metadata"""
    name: str
    title: str
    description: str
    subscribers: int
    active_users: int
    created_utc: float
    over_18: bool
    url: str


@dataclass
class RedditPost:
    """Reddit post data"""
    id: str
    subreddit: str
    title: str
    author: str
    score: int
    num_comments: int
    created_utc: float
    url: str
    selftext: str
    permalink: str


class RedditClient:
    """
    Reddit JSON API client using public endpoints.
    No authentication required!
    """
    
    BASE_URL = "https://www.reddit.com"
    
    def __init__(self, rate_limit_delay: float = 2.0):
        """
        Initialize Reddit client.
        
        Args:
            rate_limit_delay: Seconds to wait between requests (Reddit recommends 2s)
        """
        self.headers = {
            'User-Agent': 'SocialIntelligenceEngine/1.0 (Educational Project)'
        }
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    def _request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make a rate-limited request"""
        self._rate_limit()
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request error: {e}")
            return None
    
    # =========================================================================
    # Subreddit Info Methods
    # =========================================================================
    
    def get_subreddit_info(self, subreddit: str) -> Optional[SubredditInfo]:
        """
        Get subreddit metadata.
        
        URL: https://www.reddit.com/r/{subreddit}/about.json
        
        Args:
            subreddit: Subreddit name (without r/)
            
        Returns:
            SubredditInfo object or None
        """
        url = f"{self.BASE_URL}/r/{subreddit}/about.json"
        data = self._request(url)
        
        if not data or 'data' not in data:
            return None
        
        d = data['data']
        return SubredditInfo(
            name=d.get('display_name', subreddit),
            title=d.get('title', ''),
            description=d.get('public_description', ''),
            subscribers=d.get('subscribers', 0),
            active_users=d.get('active_user_count', 0),
            created_utc=d.get('created_utc', 0),
            over_18=d.get('over18', False),
            url=f"{self.BASE_URL}/r/{subreddit}"
        )
    
    def get_subreddit_info_quick(self, subreddit: str) -> Optional[Dict]:
        """
        Quick subreddit info from posts endpoint (less detailed but faster).
        
        URL: https://www.reddit.com/r/{subreddit}.json
        
        Args:
            subreddit: Subreddit name
            
        Returns:
            Dict with basic info or None
        """
        url = f"{self.BASE_URL}/r/{subreddit}.json"
        data = self._request(url, {'limit': 1})
        
        if not data:
            return None
        
        children = data.get('data', {}).get('children', [])
        if not children:
            return None
        
        post = children[0]['data']
        return {
            'name': post.get('subreddit'),
            'subscribers': post.get('subreddit_subscribers', 0),
            'subreddit_id': post.get('subreddit_id')
        }
    
    # =========================================================================
    # Post Fetching Methods
    # =========================================================================
    
    def get_subreddit_posts(
        self,
        subreddit: str,
        sort: str = 'hot',
        limit: int = 25,
        time_filter: str = None
    ) -> List[RedditPost]:
        """
        Get posts from a subreddit.
        
        URLs:
        - https://www.reddit.com/r/{subreddit}.json (default = hot)
        - https://www.reddit.com/r/{subreddit}/hot.json
        - https://www.reddit.com/r/{subreddit}/new.json
        - https://www.reddit.com/r/{subreddit}/top.json?t=week
        - https://www.reddit.com/r/{subreddit}/rising.json
        
        Args:
            subreddit: Subreddit name
            sort: 'hot', 'new', 'top', 'rising'
            limit: Number of posts (max 100)
            time_filter: For 'top' sort: 'hour', 'day', 'week', 'month', 'year', 'all'
            
        Returns:
            List of RedditPost objects
        """
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
        params = {'limit': min(limit, 100)}
        
        if sort == 'top' and time_filter:
            params['t'] = time_filter
        
        data = self._request(url, params)
        
        if not data:
            return []
        
        posts = []
        for item in data.get('data', {}).get('children', []):
            p = item['data']
            posts.append(RedditPost(
                id=p.get('id', ''),
                subreddit=p.get('subreddit', ''),
                title=p.get('title', ''),
                author=p.get('author', ''),
                score=p.get('score', 0),
                num_comments=p.get('num_comments', 0),
                created_utc=p.get('created_utc', 0),
                url=p.get('url', ''),
                selftext=p.get('selftext', '')[:1000],
                permalink=f"{self.BASE_URL}{p.get('permalink', '')}"
            ))
        
        return posts
    
    # =========================================================================
    # Search Methods
    # =========================================================================
    
    def search_posts(
        self,
        query: str,
        subreddit: str = None,
        sort: str = 'relevance',
        time_filter: str = 'year',
        limit: int = 50
    ) -> List[RedditPost]:
        """
        Search for posts across Reddit or within a subreddit.
        
        URLs:
        - https://www.reddit.com/search.json?q=query (all Reddit)
        - https://www.reddit.com/r/{subreddit}/search.json?q=query (specific sub)
        
        Args:
            query: Search query
            subreddit: Optional - limit to specific subreddit
            sort: 'relevance', 'hot', 'top', 'new', 'comments'
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
            limit: Number of results (max 100)
            
        Returns:
            List of RedditPost objects
        """
        if subreddit:
            url = f"{self.BASE_URL}/r/{subreddit}/search.json"
            params = {
                'q': query,
                'restrict_sr': 'true',  # Restrict to this subreddit
                'sort': sort,
                't': time_filter,
                'limit': min(limit, 100)
            }
        else:
            url = f"{self.BASE_URL}/search.json"
            params = {
                'q': query,
                'sort': sort,
                't': time_filter,
                'limit': min(limit, 100),
                'type': 'link'
            }
        
        data = self._request(url, params)
        
        if not data:
            return []
        
        posts = []
        for item in data.get('data', {}).get('children', []):
            p = item['data']
            posts.append(RedditPost(
                id=p.get('id', ''),
                subreddit=p.get('subreddit', ''),
                title=p.get('title', ''),
                author=p.get('author', ''),
                score=p.get('score', 0),
                num_comments=p.get('num_comments', 0),
                created_utc=p.get('created_utc', 0),
                url=p.get('url', ''),
                selftext=p.get('selftext', '')[:1000],
                permalink=f"{self.BASE_URL}{p.get('permalink', '')}"
            ))
        
        return posts
    
    def search_subreddits(
        self,
        query: str,
        limit: int = 25
    ) -> List[Dict]:
        """
        Search for subreddits by name/description.
        
        URL: https://www.reddit.com/subreddits/search.json?q=query
        
        Args:
            query: Search query
            limit: Number of results (max 100)
            
        Returns:
            List of subreddit info dicts
        """
        url = f"{self.BASE_URL}/subreddits/search.json"
        params = {
            'q': query,
            'limit': min(limit, 100),
            'sort': 'relevance'
        }
        
        data = self._request(url, params)
        
        if not data:
            return []
        
        subreddits = []
        for item in data.get('data', {}).get('children', []):
            s = item['data']
            subreddits.append({
                'name': s.get('display_name', ''),
                'title': s.get('title', ''),
                'description': s.get('public_description', '')[:300],
                'subscribers': s.get('subscribers', 0),
                'active_users': s.get('active_user_count', 0),
                'over_18': s.get('over18', False),
                'url': f"{self.BASE_URL}/r/{s.get('display_name', '')}"
            })
        
        return subreddits
    
    # =========================================================================
    # Discovery Helper Methods
    # =========================================================================
    
    def discover_subreddits_from_posts(
        self,
        queries: List[str],
        limit_per_query: int = 50
    ) -> Dict[str, Dict]:
        """
        Search posts for queries and extract which subreddits discuss them.
        
        This is the KEY method for finding relevant subreddits!
        
        Args:
            queries: List of search queries (keywords)
            limit_per_query: Posts to search per query
            
        Returns:
            Dict of subreddit_name -> {mention_count, matched_queries, sample_posts}
        """
        from collections import defaultdict
        
        subreddit_data = defaultdict(lambda: {
            'name': '',
            'mention_count': 0,
            'matched_queries': [],
            'sample_posts': []
        })
        
        print(f"🔍 Searching {len(queries)} queries across Reddit...")
        
        for query in queries:
            posts = self.search_posts(query, limit=limit_per_query)
            
            for post in posts:
                sub_name = post.subreddit
                sub_lower = sub_name.lower()
                
                # Update data
                subreddit_data[sub_lower]['name'] = sub_name
                subreddit_data[sub_lower]['mention_count'] += 1
                
                if query not in subreddit_data[sub_lower]['matched_queries']:
                    subreddit_data[sub_lower]['matched_queries'].append(query)
                
                if len(subreddit_data[sub_lower]['sample_posts']) < 3:
                    subreddit_data[sub_lower]['sample_posts'].append({
                        'title': post.title[:100],
                        'score': post.score
                    })
            
            print(f"   ✓ '{query}' → {len(posts)} posts")
        
        return dict(subreddit_data)
    
    def get_subreddit_with_posts(
        self,
        subreddit: str,
        post_limit: int = 25
    ) -> Dict:
        """
        Get subreddit info AND recent posts in one call.
        
        This is efficient because /r/{sub}.json returns both!
        
        Args:
            subreddit: Subreddit name
            post_limit: Number of posts to fetch
            
        Returns:
            Dict with 'info' and 'posts' keys
        """
        # Get detailed info
        info = self.get_subreddit_info(subreddit)
        
        # Get posts
        posts = self.get_subreddit_posts(subreddit, limit=post_limit)
        
        return {
            'info': info,
            'posts': posts
        }


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔍 REDDIT CLIENT TEST")
    print("="*70 + "\n")
    
    client = RedditClient(rate_limit_delay=2.0)
    
    # Test 1: Get subreddit info
    print("📌 Test 1: Get subreddit info (r/OpenAI)")
    print("-" * 50)
    info = client.get_subreddit_info("OpenAI")
    if info:
        print(f"   Name: r/{info.name}")
        print(f"   Title: {info.title}")
        print(f"   Subscribers: {info.subscribers:,}")
        print(f"   Active Users: {info.active_users:,}")
        print(f"   Description: {info.description[:100]}...")
    else:
        print("   ⚠️ Could not fetch (may be rate limited)")
    
    # Test 2: Get posts
    print(f"\n📌 Test 2: Get top posts from r/OpenAI")
    print("-" * 50)
    posts = client.get_subreddit_posts("OpenAI", sort="top", limit=5, time_filter="week")
    for i, post in enumerate(posts[:3], 1):
        print(f"   {i}. {post.title[:60]}...")
        print(f"      Score: {post.score}, Comments: {post.num_comments}")
    
    # Test 3: Search posts
    print(f"\n📌 Test 3: Search posts for 'GPT-4'")
    print("-" * 50)
    results = client.search_posts("GPT-4", limit=10)
    
    # Extract unique subreddits
    subreddits = {}
    for post in results:
        sub = post.subreddit
        if sub not in subreddits:
            subreddits[sub] = 0
        subreddits[sub] += 1
    
    print(f"   Found posts in {len(subreddits)} subreddits:")
    for sub, count in sorted(subreddits.items(), key=lambda x: -x[1])[:5]:
        print(f"   • r/{sub}: {count} posts")
    
    # Test 4: Search subreddits
    print(f"\n📌 Test 4: Search subreddits for 'artificial intelligence'")
    print("-" * 50)
    subs = client.search_subreddits("artificial intelligence", limit=5)
    for sub in subs[:3]:
        print(f"   • r/{sub['name']} ({sub['subscribers']:,} subscribers)")
    
    print("\n" + "="*70)
    print("✅ Tests complete!")
    print("="*70)