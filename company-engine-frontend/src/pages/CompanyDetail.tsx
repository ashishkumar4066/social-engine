import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import type { Company, Subreddit, Summary, Relationship } from '../types';
import RelationshipGraph from '../components/RelationshipGraph';
import './CompanyDetail.css';

const CompanyDetail = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const [company, setCompany] = useState<Company | null>(null);
  const [subreddits, setSubreddits] = useState<Subreddit[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!companyId) return;

      try {
        setLoading(true);
        const id = parseInt(companyId);
        const [companyData, subredditsData, summaryData, relationshipsData] = await Promise.all([
          api.getCompany(id),
          api.getCompanySubreddits(id, 20),
          api.getCompanySummary(id),
          api.getCompanyRelationships(id, 0.6), // Min confidence 60%
        ]);
        setCompany(companyData);
        setSubreddits(subredditsData);
        setSummary(summaryData);
        setRelationships(relationshipsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch company details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [companyId]);

  if (loading) return <div className="company-detail loading">Loading...</div>;
  if (error) return <div className="company-detail error">Error: {error}</div>;
  if (!company) return <div className="company-detail error">Company not found</div>;

  return (
    <div className="company-detail">
      <div className="header">
        <div className="header-content">
          <h1>{company.company_name}</h1>
          <a href={`https://${company.domain}`} target="_blank" rel="noopener noreferrer" className="domain-link">
            {company.domain}
          </a>
        </div>
        <Link to={`/companies/${companyId}/entities`} className="btn-primary">
          Browse Entities
        </Link>
      </div>

      <div className="info-section">
        <p><strong>Industry:</strong> {company.industry}</p>
        <p><strong>Description:</strong> {company.description}</p>
      </div>

      {summary && (
        <div className="summary-section">
          <h2>Summary Statistics</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{summary.subreddit_count}</div>
              <div className="stat-label">Subreddits</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{summary.entity_count}</div>
              <div className="stat-label">Entities</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{summary.mention_count}</div>
              <div className="stat-label">Mentions</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{relationships.length}</div>
              <div className="stat-label">Relationships</div>
            </div>
          </div>
        </div>
      )}

      <RelationshipGraph
        relationships={relationships}
        centerEntity={company?.company_name}
      />

      <div className="subreddits-section">
        <h2>Top Subreddits ({subreddits.length})</h2>
        <div className="subreddit-list">
          {subreddits.map((subreddit) => (
            <div key={subreddit.id} className="subreddit-card">
              <h3>r/{subreddit.name}</h3>
              <p>{subreddit.description}</p>
              <div className="subreddit-stats">
                <span>👥 {subreddit.subscribers.toLocaleString()} subscribers</span>
                <span>📊 Score: {subreddit.business_value_score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CompanyDetail;
