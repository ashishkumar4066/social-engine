import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import type { Company, Subreddit, Summary } from '../types';
import './CompanyDetail.css';

const CompanyDetail = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const [company, setCompany] = useState<Company | null>(null);
  const [subreddits, setSubreddits] = useState<Subreddit[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!companyId) return;

      try {
        setLoading(true);
        const id = parseInt(companyId);
        const [companyData, subredditsData, summaryData] = await Promise.all([
          api.getCompany(id),
          api.getCompanySubreddits(id, 20),
          api.getCompanySummary(id),
        ]);
        setCompany(companyData);
        setSubreddits(subredditsData);
        setSummary(summaryData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch company details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [companyId]);

  const getCompanyInitial = (name: string) => name.charAt(0).toUpperCase();

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  if (loading) {
    return (
      <div className="company-detail">
        <div className="detail-loading">
          <div className="spinner"></div>
          <p className="detail-loading-text">Loading company data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="company-detail">
        <div className="detail-error">
          <p className="detail-error-text">Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="company-detail">
        <div className="detail-error">
          <p className="detail-error-text">Company not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="company-detail">
      {/* Header */}
      <header className="detail-header">
        <div className="detail-header-main">
          <div className="detail-logo">
            {getCompanyInitial(company.company_name)}
          </div>
          <div className="detail-info">
            <h1 className="detail-name">{company.company_name}</h1>
            <span className="detail-domain">{company.domain}</span>
            <div className="detail-meta">
              <span className="detail-badge">
                <span className="detail-badge-icon">&#127991;</span>
                {company.industry}
              </span>
              {company.technologies.length > 0 && (
                <span className="detail-badge">
                  <span className="detail-badge-icon">&#128187;</span>
                  {company.technologies.length} technologies
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="detail-actions">
          <Link to={`/companies/${companyId}/entities`} className="detail-btn detail-btn-primary">
            <span>&#128269;</span>
            Browse Entities
          </Link>
        </div>
      </header>

      {/* Description */}
      {company.description && (
        <section className="detail-description">
          <p className="detail-description-text">{company.description}</p>
        </section>
      )}

      {/* Stats */}
      {summary && (
        <section className="stats-section">
          <div className="section-header">
            <h2 className="section-title">Analytics Overview</h2>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">&#128194;</div>
              <div className="stat-value">{summary.subreddit_count}</div>
              <div className="stat-label">Subreddits</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">&#128101;</div>
              <div className="stat-value">{summary.entity_count}</div>
              <div className="stat-label">Entities</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">&#128172;</div>
              <div className="stat-value">{formatNumber(summary.mention_count)}</div>
              <div className="stat-label">Mentions</div>
            </div>
          </div>
        </section>
      )}

      {/* Subreddits */}
      <section className="subreddits-section">
        <div className="section-header">
          <h2 className="section-title">Top Subreddits ({subreddits.length})</h2>
        </div>
        <div className="subreddit-list">
          {subreddits.map((subreddit) => (
            <article key={subreddit.id} className="subreddit-card">
              <div className="subreddit-info">
                <h3 className="subreddit-name">
                  <a
                    href={`https://reddit.com/r/${subreddit.name}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="subreddit-name-link"
                  >
                    r/{subreddit.name}
                  </a>
                </h3>
                <p className="subreddit-description">{subreddit.description}</p>
              </div>
              <div className="subreddit-stats">
                <div className="subreddit-stat">
                  <span className="subreddit-stat-value">
                    {formatNumber(subreddit.subscribers)}
                  </span>
                  <span>members</span>
                </div>
                <span className="subreddit-score">
                  Score: {subreddit.business_value_score.toFixed(2)}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
};

export default CompanyDetail;
