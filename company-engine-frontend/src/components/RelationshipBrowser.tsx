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
    return <div className="relationship-browser loading">Loading relationships...</div>;
  }

  if (error) {
    return <div className="relationship-browser error">Error: {error}</div>;
  }

  // Get unique relationship types
  const relationshipTypes = [...new Set(relationships.map((r) => r.relationship))];

  // Filter relationships
  const filteredRelationships = filterType
    ? relationships.filter((r) => r.relationship === filterType)
    : relationships;

  return (
    <div className="relationship-browser">
      <div className="filter-section">
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
          <div className="empty-state">
            No relationships found. Relationships are extracted from posts during analysis.
          </div>
        ) : (
          filteredRelationships.map((rel, index) => (
            <div key={index} className="relationship-card">
              <div className="relationship-header">
                <span className="relationship-type">{rel.relationship}</span>
                <span className="confidence">Confidence: {(rel.confidence * 100).toFixed(0)}%</span>
              </div>

              <div className="relationship-content">
                <div className="entities-section">
                  <div className="entity-group">
                    <div className="entity-label">Source Entities ({rel.pKey.length})</div>
                    <div className="entity-list">
                      {rel.pKey.map((entity, i) => (
                        <span key={i} className="entity-tag source">
                          {entity}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="arrow">→</div>

                  <div className="entity-group">
                    <div className="entity-label">Target Entity</div>
                    <div className="entity-list">
                      <span className="entity-tag target">{rel.fKey}</span>
                    </div>
                  </div>
                </div>

                <div className="relationship-meta">
                  <span className="evidence-count">
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
