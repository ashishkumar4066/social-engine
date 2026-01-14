export interface Company {
  id: number;
  domain: string;
  company_name: string;
  industry: string;
  description: string;
  keywords: string[];
  products: string[];
  technologies: string[];
}

export interface Subreddit {
  id: number;
  name: string;
  title: string;
  description: string;
  subscribers: number;
  active_users: number;
  business_value_score: number;
  discovery_methods: string[];
}

export interface Entity {
  id: number;
  canonical_name: string;
  entity_type: string;
  aliases: string[];
  mention_count: number;
  avg_confidence: number;
  subreddits_found_in: string[];
}

export interface Mention {
  id: number;
  raw_text: string;
  confidence: number;
  match_method: string;
  context: string;
  subreddit: string;
}

export interface Summary {
  subreddit_count: number;
  post_count: number;
  entity_count: number;
  mention_count: number;
  entities_by_type: Record<string, number>;
}

export interface AnalyzeRequest {
  domain: string;
  top_n?: number;
  fetch_posts_from?: number;
}

export interface AnalyzeResponse {
  company_id: number;
  company: Company;
  message: string;
  already_existed: boolean;
}

export interface Relationship {
  id: number;
  source_entity: string;
  relationship_type: string;
  target_entity: string;
  confidence: number;
  evidence_count: number;
  evidence: string[];
  source_posts: string[];
  source_subreddits: string[];
  extraction_method: string;
}
