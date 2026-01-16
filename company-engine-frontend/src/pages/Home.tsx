import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import type { Company } from '../types';
import './Home.css';

const Home = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!searchQuery.trim()) {
      setError('Please enter a company name or domain');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSearched(true);

      const allCompanies = await api.getCompanies();
      const filtered = allCompanies.filter(company =>
        company.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        company.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
        company.industry.toLowerCase().includes(searchQuery.toLowerCase())
      );

      if (filtered.length > 0) {
        setCompanies(filtered);
      } else {
        const isDomain = searchQuery.includes('.') || searchQuery.match(/^[a-zA-Z0-9-]+$/);

        if (isDomain) {
          try {
            const result = await api.analyzeCompany({ domain: searchQuery });
            setCompanies([result.company]);
            if (!result.already_existed) {
              setError(null);
            }
          } catch (analyzeErr) {
            setCompanies([]);
            setError(
              analyzeErr instanceof Error
                ? analyzeErr.message
                : 'Failed to analyze company. Please check the domain and try again.'
            );
          }
        } else {
          setCompanies([]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search companies');
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCompanyClick = (companyId: number) => {
    navigate(`/companies/${companyId}`);
  };

  const getCompanyInitial = (name: string) => {
    return name.charAt(0).toUpperCase();
  };

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-grid"></div>
        </div>
        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot"></span>
            Reddit Intelligence Platform
          </div>
          <h1 className="hero-title">
            <span className="hero-title-gradient">Discover What People</span>
            <br />
            <span className="hero-title-gradient">Say About Companies</span>
          </h1>
          <p className="hero-subtitle">
            Analyze Reddit conversations, extract entities, and uncover insights
            about any company's online presence and reputation.
          </p>

          <div className="search-wrapper">
            <form onSubmit={handleSearch} className="search-form">
              <div className="search-container">
                <span className="search-icon">&#128269;</span>
                <input
                  type="text"
                  placeholder="Enter company domain (e.g., stripe.com)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
                <button type="submit" className="search-button" disabled={loading}>
                  {loading ? (
                    <span className="spinner"></span>
                  ) : (
                    'Analyze'
                  )}
                </button>
              </div>
            </form>
            <p className="search-hint">
              Try: <code>openai.com</code>, <code>stripe.com</code>, or <code>notion.so</code>
            </p>
          </div>

          {error && (
            <div className="error-message">
              <span className="error-icon">!</span>
              {error}
            </div>
          )}
        </div>
      </section>

      {/* Loading State */}
      {loading && (
        <section className="loading-section">
          <div className="loading-content">
            <div className="loading-spinner"></div>
            <p className="loading-text">Analyzing company data...</p>
            <p className="loading-subtext">Searching Reddit, extracting entities, building insights</p>
          </div>
        </section>
      )}

      {/* Results Section */}
      {!loading && searched && companies.length > 0 && (
        <section className="results-section">
          <div className="results-header">
            <h2 className="results-title">
              Found <span className="results-count">{companies.length}</span> {companies.length === 1 ? 'company' : 'companies'}
            </h2>
          </div>
          <div className="results-grid">
            {companies.map((company) => (
              <article
                key={company.id}
                className="company-card"
                onClick={() => handleCompanyClick(company.id)}
              >
                <div className="company-card-header">
                  <div className="company-card-icon">
                    {getCompanyInitial(company.company_name)}
                  </div>
                  <div className="company-card-info">
                    <h3 className="company-card-name">{company.company_name}</h3>
                    <p className="company-card-domain">{company.domain}</p>
                  </div>
                </div>
                <span className="company-card-industry">{company.industry}</span>
                <p className="company-card-description">{company.description}</p>

                {company.technologies.length > 0 && (
                  <div className="company-card-tags">
                    {company.technologies.slice(0, 4).map((tech, i) => (
                      <span key={i} className="company-card-tag">{tech}</span>
                    ))}
                  </div>
                )}

                <div className="company-card-arrow">&#8594;</div>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* No Results */}
      {!loading && searched && companies.length === 0 && !error && (
        <section className="no-results">
          <div className="no-results-icon">&#128269;</div>
          <h3 className="no-results-title">No companies found</h3>
          <p className="no-results-text">
            Try searching with a different keyword or enter a domain to analyze a new company.
          </p>
        </section>
      )}

      {/* Features Section */}
      {!searched && !loading && (
        <section className="features-section">
          <div className="features-header">
            <span className="features-label">How it works</span>
            <h2 className="features-title">Powerful Company Intelligence</h2>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">&#127919;</div>
              <h3 className="feature-title">Discover</h3>
              <p className="feature-description">
                Find relevant subreddits where your target company is being discussed by real users.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">&#128202;</div>
              <h3 className="feature-title">Analyze</h3>
              <p className="feature-description">
                Extract entities, relationships, and sentiment from thousands of Reddit conversations.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">&#128161;</div>
              <h3 className="feature-title">Insights</h3>
              <p className="feature-description">
                Get actionable intelligence about products, competitors, and market perception.
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};

export default Home;
