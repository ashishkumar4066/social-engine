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

      // First, try to fetch existing companies and filter
      const allCompanies = await api.getCompanies();
      const filtered = allCompanies.filter(company =>
        company.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        company.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
        company.industry.toLowerCase().includes(searchQuery.toLowerCase())
      );

      if (filtered.length > 0) {
        // Found existing companies
        setCompanies(filtered);
      } else {
        // No companies found - check if the search query looks like a domain
        const isDomain = searchQuery.includes('.') || searchQuery.match(/^[a-zA-Z0-9-]+$/);

        if (isDomain) {
          // Treat it as a domain and analyze it
          try {
            const result = await api.analyzeCompany({ domain: searchQuery });
            setCompanies([result.company]);

            // Show a message if company was newly analyzed
            if (!result.already_existed) {
              setError(null); // Clear any previous errors
            }
          } catch (analyzeErr) {
            // Failed to analyze - show error
            setCompanies([]);
            setError(
              analyzeErr instanceof Error
                ? analyzeErr.message
                : 'Failed to analyze company. Please check the domain and try again.'
            );
          }
        } else {
          // Not a domain, just show no results
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

  return (
    <div className="home">
      <div className="hero-section">
        <div className="neon-border"></div>
        <h1 className="neon-title">
          <span className="neon-text">Social Intelligence</span>
          <span className="neon-text-sub">Engine</span>
        </h1>
        <p className="tagline">Discover insights from Reddit conversations about your favorite companies</p>

        <form onSubmit={handleSearch} className="search-form">
          <div className="search-container">
            <input
              type="text"
              placeholder="Search existing companies or enter domain to analyze (e.g., stripe.com)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="search-button" disabled={loading}>
              {loading ? (
                <span className="loader-spinner"></span>
              ) : (
                <span>Search</span>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}
      </div>

      {loading && (
        <div className="loading-container">
          <div className="loading-animation">
            <div className="pulse-ring"></div>
            <div className="pulse-ring delay-1"></div>
            <div className="pulse-ring delay-2"></div>
          </div>
          <p className="loading-text">Analyzing data streams...</p>
        </div>
      )}

      {!loading && searched && companies.length > 0 && (
        <div className="results-section">
          <h2 className="results-title">
            Found <span className="highlight">{companies.length}</span> {companies.length === 1 ? 'company' : 'companies'}
          </h2>
          <div className="results-grid">
            {companies.map((company) => (
              <div
                key={company.id}
                className="result-card"
                onClick={() => handleCompanyClick(company.id)}
              >
                <div className="card-glow"></div>
                <div className="card-content">
                  <h3 className="company-name">{company.company_name}</h3>
                  <p className="company-domain">{company.domain}</p>
                  <p className="company-industry">{company.industry}</p>
                  <p className="company-description">{company.description}</p>

                  {company.technologies.length > 0 && (
                    <div className="tech-tags">
                      {company.technologies.slice(0, 4).map((tech, i) => (
                        <span key={i} className="tech-tag">{tech}</span>
                      ))}
                    </div>
                  )}

                  <div className="card-arrow">→</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && searched && companies.length === 0 && !error && (
        <div className="no-results">
          <div className="no-results-icon">🔍</div>
          <p>No companies found matching "{searchQuery}"</p>
          <p className="suggestion">Try searching with a different keyword or enter a domain (e.g., stripe.com) to analyze a new company</p>
        </div>
      )}

      {!searched && !loading && (
        <div className="features-section">
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>Discover</h3>
            <p>Find companies and their Reddit presence</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Analyze</h3>
            <p>View subreddit discussions and sentiment</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Explore</h3>
            <p>Browse entities and mentions in context</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;
