# keyword_extractor.py
"""
Keyword extraction using spaCy NLP (with regex fallback).
Extracts named entities, noun phrases, and technology terms from text.

Usage:
    from keyword_extractor import KeywordExtractor
    from wikipedia_extractor import WikipediaExtractor
    
    wiki = WikipediaExtractor()
    wiki_result = wiki.extract("openai.com")
    
    kw_extractor = KeywordExtractor()
    keywords = kw_extractor.extract(
        text=wiki_result.full_text,
        company_name=wiki_result.company_name,
        categories=wiki_result.categories
    )
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from collections import Counter

# Try to load spaCy, but work without it if unavailable
SPACY_AVAILABLE = False
nlp = None

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    print("✅ spaCy loaded successfully")
except (ImportError, OSError) as e:
    print(f"⚠️ spaCy not available, using regex fallback: {e}")


@dataclass
class ExtractedKeywords:
    """Structured keyword extraction results."""
    company_name: str
    
    # Different types of keywords
    entities: list[dict] = field(default_factory=list)       # Named entities (ORG, PRODUCT, PERSON)
    products: list[str] = field(default_factory=list)        # Product names
    technologies: list[str] = field(default_factory=list)    # Tech terms (AI, ML, API, etc.)
    concepts: list[str] = field(default_factory=list)        # Key noun phrases
    
    # Combined and ranked
    all_keywords: list[str] = field(default_factory=list)    # Final merged list for Reddit search
    
    # Industry classification
    industry: str = "Technology"


class KeywordExtractor:
    """
    Extracts keywords from text using spaCy NLP.
    Optimized for generating Reddit search queries.
    """
    
    # Technology patterns (regex)
    TECH_PATTERNS = [
        # AI/ML specific
        r'\bGPT-?\d*\b',
        r'\bChatGPT\b',
        r'\bDALL-E\b',
        r'\bClaude\b',
        r'\bGemini\b',
        r'\bLLaMA\b',
        r'\bMidjourney\b',
        r'\bStable\s*Diffusion\b',
        r'\bCopilot\b',
        
        # General tech acronyms
        r'\b(?:AI|ML|NLP|API|SDK|AGI|LLM|GPU|CPU|SaaS|PaaS|IaaS)\b',
        
        # Compound tech terms
        r'\b(?:machine learning|deep learning|artificial intelligence)\b',
        r'\b(?:neural network|language model|generative ai)\b',
        r'\b(?:natural language processing|computer vision)\b',
        r'\b(?:reinforcement learning|transformer model)\b',
        r'\b(?:cloud computing|edge computing|quantum computing)\b',
        r'\b(?:blockchain|cryptocurrency|smart contract)\b',
        r'\b(?:data science|big data|data analytics)\b',
    ]
    
    # Words to exclude from results
    STOP_ENTITIES = {
        'the', 'a', 'an', 'this', 'that', 'these', 'those',
        'it', 'its', 'they', 'their', 'we', 'our', 'you', 'your',
        'first', 'second', 'third', 'one', 'two', 'three',
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    }
    
    # Industry classification keywords
    INDUSTRY_KEYWORDS = {
        'AI & Machine Learning': [
            'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'language model', 'chatbot', 'nlp', 'computer vision',
            'generative ai', 'llm', 'transformer'
        ],
        'Cloud & Infrastructure': [
            'cloud computing', 'aws', 'azure', 'google cloud', 'infrastructure',
            'kubernetes', 'docker', 'serverless', 'devops'
        ],
        'E-commerce': [
            'ecommerce', 'e-commerce', 'online shopping', 'marketplace',
            'retail', 'shopping', 'merchant', 'storefront'
        ],
        'Fintech': [
            'financial', 'banking', 'payment', 'fintech', 'cryptocurrency',
            'investment', 'trading', 'insurance', 'lending'
        ],
        'SaaS': [
            'software as a service', 'saas', 'subscription', 'enterprise software',
            'business software', 'productivity', 'collaboration'
        ],
        'Social Media': [
            'social media', 'social network', 'social networking',
            'content sharing', 'messaging', 'community'
        ],
        'Healthcare': [
            'healthcare', 'medical', 'health', 'medicine', 'clinical',
            'patient', 'diagnosis', 'treatment', 'pharmaceutical'
        ],
        'Cybersecurity': [
            'security', 'cybersecurity', 'encryption', 'authentication',
            'privacy', 'firewall', 'threat detection'
        ],
    }
    
    def __init__(self, max_text_length: int = 15000):
        """
        Initialize keyword extractor.
        
        Args:
            max_text_length: Maximum text length to process (for performance)
        """
        self.max_text_length = max_text_length
    
    def extract(
        self,
        text: str,
        company_name: str,
        categories: Optional[list[str]] = None
    ) -> ExtractedKeywords:
        """
        Extract keywords from text.
        
        Args:
            text: Full text to extract keywords from (e.g., Wikipedia article)
            company_name: Company name to exclude from results
            categories: Optional Wikipedia categories for industry classification
            
        Returns:
            ExtractedKeywords with categorized keywords
        """
        print(f"\n{'='*60}")
        print(f"🔑 Keyword Extractor")
        print(f"{'='*60}")
        print(f"   Company: {company_name}")
        print(f"   Text length: {len(text)} chars")
        print(f"   Using: {'spaCy NLP' if SPACY_AVAILABLE else 'Regex fallback'}")
        
        if not text or len(text) < 50:
            print(f"   ⚠️ Text too short")
            return ExtractedKeywords(
                company_name=company_name,
                all_keywords=[company_name.lower()]
            )
        
        # Truncate text for performance
        text = text[:self.max_text_length]
        
        company_lower = company_name.lower()
        company_words = set(company_lower.split())
        
        result = ExtractedKeywords(company_name=company_name)
        
        if SPACY_AVAILABLE and nlp:
            # Use spaCy for better extraction
            doc = nlp(text)
            result.entities = self._extract_entities(doc, company_lower, company_words)
            result.concepts = self._extract_concepts(doc, company_lower, company_words)
        else:
            # Use regex fallback
            result.entities = self._extract_entities_regex(text, company_lower)
            result.concepts = self._extract_concepts_regex(text, company_lower)
        
        print(f"   ✅ Entities: {len(result.entities)}")
        
        # Extract Products (subset of entities)
        result.products = self._extract_products(result.entities)
        print(f"   ✅ Products: {len(result.products)}")
        
        # Extract Technology Terms (always use regex)
        result.technologies = self._extract_technologies(text, company_lower)
        print(f"   ✅ Technologies: {len(result.technologies)}")
        
        print(f"   ✅ Concepts: {len(result.concepts)}")
        
        # Classify Industry
        result.industry = self._classify_industry(text, categories or [])
        print(f"   ✅ Industry: {result.industry}")
        
        # Merge and rank all keywords
        result.all_keywords = self._merge_keywords(result, company_name)
        print(f"   ✅ Final keywords: {len(result.all_keywords)}")
        
        return result
    
    def _extract_entities_regex(self, text: str, company_lower: str) -> list[dict]:
        """
        Extract named entities using regex patterns (fallback when spaCy unavailable).
        Looks for capitalized words/phrases that are likely entity names.
        """
        entities = []
        seen = set()
        
        # Pattern 1: Product names (often contain version numbers or special chars)
        product_patterns = [
            r'\b(GPT-\d+)\b',
            r'\b(ChatGPT)\b',
            r'\b(DALL-E(?:\s*\d*)?)\b',
            r'\b(Codex)\b',
            r'\b(Whisper)\b',
            r'\b(Sora)\b',
            r'\b(Claude)\b',
            r'\b(Gemini)\b',
            r'\b(GitHub\s*Copilot)\b',
            r'\b([A-Z][a-z]+\s+(?:Hub|API|SDK|Pro|Plus|Enterprise))\b',
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                match_lower = match.lower()
                if match_lower not in seen and company_lower not in match_lower:
                    seen.add(match_lower)
                    entities.append({
                        'text': match,
                        'type': 'PRODUCT',
                        'label': 'Product'
                    })
        
        # Pattern 2: Person names (First Last pattern, possibly with title)
        person_pattern = r'\b([A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+)\b'
        person_matches = re.findall(person_pattern, text)
        
        # Common non-person phrases to skip
        non_persons = {
            'San Francisco', 'New York', 'Los Angeles', 'United States',
            'Fortune 500', 'The Company', 'The Hustle', 'The Wall',
        }
        
        freq = Counter(person_matches)
        for match, count in freq.most_common(20):
            match_lower = match.lower()
            if (match_lower not in seen and 
                match not in non_persons and
                company_lower not in match_lower and
                count >= 2):
                seen.add(match_lower)
                entities.append({
                    'text': match,
                    'type': 'PERSON',
                    'label': 'Person'
                })
        
        # Pattern 3: Organization names (capitalized sequences)
        org_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        org_matches = re.findall(org_pattern, text)
        
        # Skip common words
        skip_words = {
            'The', 'This', 'That', 'These', 'Those', 'It', 'Its', 'They',
            'In', 'On', 'At', 'For', 'By', 'With', 'From', 'To', 'As',
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
            'According', 'However', 'Although', 'While', 'Since', 'Because',
        }
        
        freq = Counter(org_matches)
        for match, count in freq.most_common(30):
            # Skip if starts with common word
            first_word = match.split()[0]
            if first_word in skip_words:
                continue
                
            match_lower = match.lower()
            if (match_lower not in seen and
                company_lower not in match_lower and
                len(match) > 3 and
                count >= 2):
                seen.add(match_lower)
                entities.append({
                    'text': match,
                    'type': 'ORG',
                    'label': 'Organization'
                })
        
        return entities[:20]
    
    def _extract_concepts_regex(self, text: str, company_lower: str) -> list[str]:
        """
        Extract key concepts using regex (fallback when spaCy unavailable).
        Extracts common noun phrases and important terms.
        """
        concepts = []
        seen = set()
        text_lower = text.lower()
        
        # Extract meaningful phrases (2-3 word combinations)
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        
        # Get bigrams and trigrams
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        
        all_phrases = bigrams + trigrams
        freq = Counter(all_phrases)
        
        # Stop words to filter out
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 
                      'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
                      'have', 'been', 'were', 'they', 'this', 'that', 'with',
                      'from', 'which', 'their', 'will', 'would', 'there', 'what',
                      'also', 'more', 'some', 'such', 'than', 'into', 'over'}
        
        # Skip generic phrases
        skip_phrases = {'the company', 'the companies', 'the product', 'the service',
                        'the system', 'the platform', 'the software', 'the application'}
        
        for phrase, count in freq.most_common(50):
            words_in_phrase = phrase.split()
            
            # Skip generic phrases
            if phrase in skip_phrases:
                continue
            
            # Skip if first or last word is a stop word
            if words_in_phrase[0] in stop_words or words_in_phrase[-1] in stop_words:
                continue
            
            # Must have meaningful words
            non_stop = [w for w in words_in_phrase if w not in stop_words and len(w) > 2]
            if len(non_stop) < 1:
                continue
            
            if (phrase not in seen and
                company_lower not in phrase and
                count >= 2 and
                len(phrase) > 5):
                
                seen.add(phrase)
                concepts.append(phrase)
        
        return concepts[:20]
    
    def _extract_entities(
        self,
        doc,
        company_lower: str,
        company_words: set
    ) -> list[dict]:
        """Extract named entities (ORG, PRODUCT, PERSON)."""
        
        entities = []
        seen = set()
        
        for ent in doc.ents:
            ent_text = ent.text.strip()
            ent_lower = ent_text.lower()
            
            # Skip if:
            # - Already seen
            # - Is the company name
            # - Too short
            # - In stop list
            # - Contains company name words
            if (ent_lower in seen or
                ent_lower == company_lower or
                len(ent_text) < 2 or
                ent_lower in self.STOP_ENTITIES or
                any(word in ent_lower for word in company_words if len(word) > 3)):
                continue
            
            # Only keep relevant entity types
            if ent.label_ in ['ORG', 'PRODUCT', 'WORK_OF_ART', 'PERSON', 'GPE']:
                seen.add(ent_lower)
                entities.append({
                    'text': ent_text,
                    'type': ent.label_,
                    'label': self._get_entity_label(ent.label_)
                })
        
        # Sort by type priority (PRODUCT > ORG > PERSON > GPE)
        priority = {'PRODUCT': 0, 'WORK_OF_ART': 1, 'ORG': 2, 'PERSON': 3, 'GPE': 4}
        entities.sort(key=lambda x: priority.get(x['type'], 5))
        
        return entities[:20]  # Limit to top 20
    
    def _get_entity_label(self, spacy_label: str) -> str:
        """Convert spaCy label to readable label."""
        labels = {
            'ORG': 'Organization',
            'PRODUCT': 'Product',
            'WORK_OF_ART': 'Product',
            'PERSON': 'Person',
            'GPE': 'Location',
        }
        return labels.get(spacy_label, spacy_label)
    
    def _extract_products(self, entities: list[dict]) -> list[str]:
        """Extract product names from entities."""
        products = []
        for ent in entities:
            if ent['type'] in ['PRODUCT', 'WORK_OF_ART']:
                products.append(ent['text'])
        return products[:10]
    
    def _extract_technologies(self, text: str, company_lower: str) -> list[str]:
        """Extract technology-specific terms using regex patterns."""
        
        technologies = []
        seen = set()
        
        for pattern in self.TECH_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                match_lower = match.lower().strip()
                if match_lower not in seen and company_lower not in match_lower:
                    seen.add(match_lower)
                    technologies.append(match)
        
        return list(set(technologies))[:15]
    
    def _extract_concepts(
        self,
        doc,
        company_lower: str,
        company_words: set
    ) -> list[str]:
        """Extract key concepts from noun chunks."""
        
        concepts = []
        seen = set()
        
        # Words to skip at the start of chunks
        skip_starters = {'the', 'a', 'an', 'this', 'that', 'its', 'their', 'our', 'his', 'her'}
        
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            chunk_lower = chunk_text.lower()
            words = chunk_lower.split()
            
            # Skip if:
            # - Already seen
            # - Too short or too long
            # - Starts with determiner
            # - Contains company name
            if (chunk_lower in seen or
                len(chunk_text) < 4 or
                len(words) > 4 or
                words[0] in skip_starters or
                company_lower in chunk_lower or
                any(word in chunk_lower for word in company_words if len(word) > 3)):
                continue
            
            # Skip if mostly stop words
            non_stop_words = [w for w in words if w not in skip_starters and len(w) > 2]
            if len(non_stop_words) == 0:
                continue
            
            seen.add(chunk_lower)
            concepts.append(chunk_lower)
        
        return concepts[:20]
    
    def _classify_industry(self, text: str, categories: list[str]) -> str:
        """Classify industry based on text and categories."""
        
        text_lower = text.lower()
        categories_text = ' '.join(categories).lower()
        combined = text_lower + ' ' + categories_text
        
        scores = {}
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            scores[industry] = score
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return "Technology"
    
    def _merge_keywords(self, result: ExtractedKeywords, company_name: str) -> list[str]:
        """
        Merge all keywords into a single ranked list.
        Priority: company_name > entities > technologies > concepts
        """
        
        merged = []
        seen = set()
        
        # 1. Company name first (always include)
        merged.append(company_name)
        seen.add(company_name.lower())
        
        # 2. Products (high value for Reddit search)
        for product in result.products:
            if product.lower() not in seen:
                merged.append(product)
                seen.add(product.lower())
        
        # 3. Entity names (ORG, PERSON)
        for ent in result.entities:
            if ent['text'].lower() not in seen:
                merged.append(ent['text'])
                seen.add(ent['text'].lower())
        
        # 4. Technologies
        for tech in result.technologies:
            if tech.lower() not in seen:
                merged.append(tech)
                seen.add(tech.lower())
        
        # 5. Concepts (fill remaining slots)
        for concept in result.concepts:
            if concept.lower() not in seen and len(merged) < 20:
                merged.append(concept)
                seen.add(concept.lower())
        
        return merged[:20]  # Limit to 20 keywords


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    # Test with sample text (simulating Wikipedia article)
    sample_text = """
    OpenAI is an American artificial intelligence research organization founded in 
    December 2015, headquartered in San Francisco. Its mission is to develop "safe 
    and beneficial" artificial general intelligence (AGI). OpenAI has developed 
    several large language models, including the GPT series, as well as advanced 
    image generation models like DALL-E, and Codex, an AI trained to write code.
    
    Sam Altman is the CEO of OpenAI. The company has partnerships with Microsoft, 
    which has invested billions of dollars into the company. OpenAI's ChatGPT 
    became one of the fastest-growing consumer applications in history, reaching 
    100 million users within two months of its launch.
    
    The company focuses on deep learning, reinforcement learning, and natural 
    language processing. OpenAI conducts research in machine learning with a 
    focus on developing AI systems that can understand and generate human-like text.
    """
    
    extractor = KeywordExtractor()
    result = extractor.extract(
        text=sample_text,
        company_name="OpenAI",
        categories=["Artificial intelligence companies", "Machine learning"]
    )
    
    print(f"\n{'='*60}")
    print(f"📊 EXTRACTION RESULTS")
    print(f"{'='*60}")
    
    print(f"\n🏷️  Named Entities:")
    for ent in result.entities[:10]:
        print(f"   - {ent['text']} ({ent['label']})")
    
    print(f"\n📦 Products:")
    for product in result.products:
        print(f"   - {product}")
    
    print(f"\n💻 Technologies:")
    for tech in result.technologies:
        print(f"   - {tech}")
    
    print(f"\n💡 Concepts:")
    for concept in result.concepts[:10]:
        print(f"   - {concept}")
    
    print(f"\n🏭 Industry: {result.industry}")
    
    print(f"\n🔑 FINAL KEYWORDS (for Reddit search):")
    for i, kw in enumerate(result.all_keywords, 1):
        print(f"   {i:2}. {kw}")