import type {
  Company,
  Subreddit,
  Entity,
  Mention,
  Summary,
  AnalyzeRequest,
  AnalyzeResponse,
} from './types';

const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchJson<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, options);
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    return response.json();
  }

  async getCompanies(): Promise<Company[]> {
    return this.fetchJson<Company[]>('/companies');
  }

  async getCompany(companyId: number): Promise<Company> {
    return this.fetchJson<Company>(`/companies/${companyId}`);
  }

  async getCompanySubreddits(
    companyId: number,
    limit: number = 20
  ): Promise<Subreddit[]> {
    return this.fetchJson<Subreddit[]>(
      `/companies/${companyId}/subreddits?limit=${limit}`
    );
  }

  async getCompanyEntities(
    companyId: number,
    entityType?: string,
    limit: number = 50
  ): Promise<Entity[]> {
    const typeParam = entityType ? `&entity_type=${entityType}` : '';
    return this.fetchJson<Entity[]>(
      `/companies/${companyId}/entities?limit=${limit}${typeParam}`
    );
  }

  async getCompanySummary(companyId: number): Promise<Summary> {
    return this.fetchJson<Summary>(`/companies/${companyId}/summary`);
  }

  async getEntity(entityId: number): Promise<Entity> {
    return this.fetchJson<Entity>(`/entities/${entityId}`);
  }

  async getEntityMentions(
    entityId: number,
    limit: number = 50
  ): Promise<Mention[]> {
    return this.fetchJson<Mention[]>(
      `/entities/${entityId}/mentions?limit=${limit}`
    );
  }

  async healthCheck(): Promise<{ status: string; database: string }> {
    return this.fetchJson('/health');
  }

  async analyzeCompany(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    return this.fetchJson<AnalyzeResponse>('/companies/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
  }
}

const api = new ApiService();
export default api;
