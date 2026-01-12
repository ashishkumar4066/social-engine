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

  if (loading) return <div className="companies loading">Loading companies...</div>;
  if (error) return <div className="companies error">Error: {error}</div>;

  return (
    <div className="companies">
      <h1>Companies</h1>
      <div className="company-grid">
        {companies.map((company) => (
          <Link key={company.id} to={`/companies/${company.id}`} className="company-card">
            <h3>{company.company_name}</h3>
            <p className="domain">{company.domain}</p>
            <p className="industry">{company.industry}</p>
            <p className="description">{company.description}</p>
            {company.technologies.length > 0 && (
              <div className="tags">
                {company.technologies.slice(0, 3).map((tech, i) => (
                  <span key={i} className="tag">{tech}</span>
                ))}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Companies;
