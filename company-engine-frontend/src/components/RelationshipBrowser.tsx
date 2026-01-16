import { useEffect, useState } from 'react';
import api from '../api';
import type { GroupedRelationship } from '../types';
import './RelationshipBrowser.css';

interface RelationshipBrowserProps {
  companyId: number;
}

const RelationshipBrowser = ({ companyId }: RelationshipBrowserProps) => {
  const [relationships, setRelationships] = useState<GroupedRelationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('');

  useEffect(() => {
    const fetchRelationships = async () => {
      try {
        setLoading(true);
        const data = await api.getGroupedRelationships(companyId, 0.5);
        setRelationships(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch relationships');
      } finally {
        setLoading(false);
      }
    };

    fetchRelationships();
  }, [companyId]);

  if (loading) {
    return (
      <div className="relationship-browser">
        <div className="relationship-browser-loading">
          <div className="spinner"></div>
          <p className="relationship-browser-loading-text">Loading relationships...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="relationship-browser">
        <div className="relationship-browser-error">
          <p className="relationship-browser-error-text">Error: {error}</p>
        </div>
      </div>
    );
  }

  // Get unique relationship types
  const relationshipTypes = [...new Set(relationships.map((r) => r.relationship))];

  // Filter relationships
  const filteredRelationships = filterType
    ? relationships.filter((r) => r.relationship === filterType)
    : relationships;

  return (
    <div className="relationship-browser">
      <div className="relationship-filter">
        <label>Filter by relationship type:</label>
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="">All Types ({relationships.length})</option>
          {relationshipTypes.map((type) => (
            <option key={type} value={type}>
              {type} ({relationships.filter((r) => r.relationship === type).length})
            </option>
          ))}
        </select>
      </div>

      <div className="relationship-list">
        {filteredRelationships.length === 0 ? (
          <div className="relationship-empty">
            <div className="relationship-empty-icon">&#128279;</div>
            <p className="relationship-empty-text">
              No relationships found. Relationships are extracted from posts during analysis.
            </p>
          </div>
        ) : (
          filteredRelationships.map((rel, index) => (
            <div key={index} className="relationship-card">
              <div className="relationship-header">
                <span className="relationship-type">{rel.relationship}</span>
                <span className="relationship-confidence">
                  {(rel.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>

              <div className="relationship-content">
                <div className="entities-section">
                  <div className="entity-group">
                    <div className="entity-label">Source Entities ({rel.pKey.length})</div>
                    <div className="entity-tags">
                      {rel.pKey.map((entity, i) => (
                        <span key={i} className="entity-tag source">
                          {entity}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="relationship-arrow">&#8594;</div>

                  <div className="entity-group">
                    <div className="entity-label">Target Entity</div>
                    <div className="entity-tags">
                      <span className="entity-tag target">{rel.fKey}</span>
                    </div>
                  </div>
                </div>

                <div className="relationship-meta">
                  <span className="evidence-count">
                    <span className="evidence-count-icon">&#128196;</span>
                    {rel.evidence_count} piece{rel.evidence_count !== 1 ? 's' : ''} of evidence
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default RelationshipBrowser;
