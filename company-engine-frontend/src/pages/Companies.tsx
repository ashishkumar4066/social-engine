import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import type { Company } from '../types';
import './Companies.css';

const Companies = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        setLoading(true);
        const data = await api.getCompanies();
        setCompanies(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch companies');
      } finally {
        setLoading(false);
      }
    };

    fetchCompanies();
  }, []);

  const getCompanyInitial = (name: string) => name.charAt(0).toUpperCase();

  if (loading) {
    return (
      <div className="companies">
        <div className="companies-loading">
          <div className="spinner"></div>
          <p className="companies-loading-text">Loading companies...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="companies">
        <div className="companies-error">
          <p className="companies-error-text">Error: {error}</p>
        </div>
      </div>
    );
  }

  if (companies.length === 0) {
    return (
      <div className="companies">
        <div className="companies-empty">
          <div className="companies-empty-icon">&#128194;</div>
          <h3 className="companies-empty-title">No companies yet</h3>
          <p className="companies-empty-text">
            Start by analyzing a company domain to build your intelligence database.
          </p>
          <Link to="/" className="companies-empty-link">
            <span>&#128269;</span>
            Analyze a Company
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="companies">
      <header className="companies-header">
        <h1 className="companies-title">Companies</h1>
        <span className="companies-count">{companies.length} analyzed</span>
      </header>

      <div className="companies-grid">
        {companies.map((company) => (
          <Link
            key={company.id}
            to={`/companies/${company.id}`}
            className="company-card-link"
          >
            <article className="company-card-item">
              <div className="company-card-top">
                <div className="company-card-logo">
                  {getCompanyInitial(company.company_name)}
                </div>
                <div className="company-card-details">
                  <h3 className="company-card-title">{company.company_name}</h3>
                  <p className="company-card-domain-text">{company.domain}</p>
                </div>
              </div>

              <span className="company-card-badge">{company.industry}</span>
              <p className="company-card-desc">{company.description}</p>

              {company.technologies.length > 0 && (
                <div className="company-card-tech">
                  {company.technologies.slice(0, 3).map((tech, i) => (
                    <span key={i} className="company-card-tech-tag">{tech}</span>
                  ))}
                </div>
              )}

              <div className="company-card-arrow">&#8594;</div>
            </article>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Companies;
