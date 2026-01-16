import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import type { Entity, Mention } from '../types';
import RelationshipBrowser from '../components/RelationshipBrowser';
import './EntityBrowser.css';

type Tab = 'entities' | 'relationships';

const EntityBrowser = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const [activeTab, setActiveTab] = useState<Tab>('entities');
  const [entities, setEntities] = useState<Entity[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [mentions, setMentions] = useState<Mention[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('');

  useEffect(() => {
    const fetchEntities = async () => {
      if (!companyId) return;

      try {
        setLoading(true);
        const id = parseInt(companyId);
        const data = await api.getCompanyEntities(id, undefined, 200);
        setEntities(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch entities');
      } finally {
        setLoading(false);
      }
    };

    fetchEntities();
  }, [companyId]);

  const handleEntityClick = async (entity: Entity) => {
    setSelectedEntity(entity);
    try {
      const mentionData = await api.getEntityMentions(entity.id, 50);
      setMentions(mentionData);
    } catch (err) {
      console.error('Failed to fetch mentions:', err);
    }
  };

  const filteredEntities = entities.filter((entity) =>
    filter ? entity.entity_type === filter : true
  );

  const entityTypes = [...new Set(entities.map((e) => e.entity_type))];

  const getEntityTypeClass = (type: string) => {
    const typeMap: Record<string, string> = {
      'ORG': 'entity-type-ORG',
      'PERSON': 'entity-type-PERSON',
      'PRODUCT': 'entity-type-PRODUCT',
    };
    return typeMap[type] || '';
  };

  if (loading) {
    return (
      <div className="entity-browser">
        <div className="entity-browser-loading">
          <div className="spinner"></div>
          <p className="entity-browser-loading-text">Loading entities...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="entity-browser">
        <div className="entity-browser-error">
          <p className="entity-browser-error-text">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="entity-browser">
      <header className="entity-browser-header">
        <h1 className="entity-browser-title">Entity Browser</h1>
        <Link to={`/companies/${companyId}`} className="entity-browser-back">
          <span>&#8592;</span>
          Back to Company
        </Link>
      </header>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'entities' ? 'active' : ''}`}
          onClick={() => setActiveTab('entities')}
        >
          Entities
        </button>
        <button
          className={`tab ${activeTab === 'relationships' ? 'active' : ''}`}
          onClick={() => setActiveTab('relationships')}
        >
          Relationships
        </button>
      </div>

      {activeTab === 'entities' ? (
        <>
          <div className="filter-section">
            <label>Filter by type:</label>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">All Types</option>
              {entityTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div className="browser-layout">
            <div className="entity-list">
              <div className="entity-list-header">
                <h2 className="entity-list-title">Entities ({filteredEntities.length})</h2>
              </div>
              <div className="entity-list-content">
                {filteredEntities.map((entity) => (
                  <div
                    key={entity.id}
                    className={`entity-item ${selectedEntity?.id === entity.id ? 'active' : ''}`}
                    onClick={() => handleEntityClick(entity)}
                  >
                    <div className="entity-name">{entity.canonical_name}</div>
                    <div className="entity-meta">
                      <span className={`entity-type ${getEntityTypeClass(entity.entity_type)}`}>
                        {entity.entity_type}
                      </span>
                      <span className="mention-count">{entity.mention_count} mentions</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mention-panel">
              {selectedEntity ? (
                <>
                  <div className="mention-panel-header">
                    <h2 className="mention-panel-title">{selectedEntity.canonical_name}</h2>
                    <div className="entity-details">
                      <div className="entity-detail-item">
                        <div className="entity-detail-label">Type</div>
                        <div className="entity-detail-value">{selectedEntity.entity_type}</div>
                      </div>
                      <div className="entity-detail-item">
                        <div className="entity-detail-label">Mentions</div>
                        <div className="entity-detail-value">{selectedEntity.mention_count}</div>
                      </div>
                      <div className="entity-detail-item">
                        <div className="entity-detail-label">Confidence</div>
                        <div className="entity-detail-value">{selectedEntity.avg_confidence.toFixed(2)}</div>
                      </div>
                    </div>
                    {selectedEntity.aliases.length > 0 && (
                      <div className="entity-aliases">
                        <div className="entity-aliases-label">Aliases</div>
                        <div className="entity-aliases-list">
                          {selectedEntity.aliases.map((alias, i) => (
                            <span key={i} className="entity-alias-tag">{alias}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="mention-panel-content">
                    <h3 className="mention-section-title">Recent Mentions</h3>
                    <div className="mention-list">
                      {mentions.map((mention) => (
                        <div key={mention.id} className="mention-item">
                          <div className="mention-header">
                            <span className="subreddit">r/{mention.subreddit}</span>
                            <span className="confidence">{(mention.confidence * 100).toFixed(0)}%</span>
                          </div>
                          <p className="context">{mention.context}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="empty-state">
                  <div className="empty-state-icon">&#128269;</div>
                  <p className="empty-state-text">Select an entity to view mentions</p>
                </div>
              )}
            </div>
          </div>
        </>
      ) : (
        <RelationshipBrowser companyId={parseInt(companyId!)} />
      )}
    </div>
  );
};

export default EntityBrowser;
