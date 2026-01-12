import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';
import type { Entity, Mention } from '../types';
import './EntityBrowser.css';

const EntityBrowser = () => {
  const { companyId } = useParams<{ companyId: string }>();
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
        const data = await api.getCompanyEntities(id, undefined, 100);
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

  if (loading) return <div className="entity-browser loading">Loading entities...</div>;
  if (error) return <div className="entity-browser error">Error: {error}</div>;

  return (
    <div className="entity-browser">
      <h1>Entity Browser</h1>

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
          <h2>Entities ({filteredEntities.length})</h2>
          {filteredEntities.map((entity) => (
            <div
              key={entity.id}
              className={`entity-item ${selectedEntity?.id === entity.id ? 'active' : ''}`}
              onClick={() => handleEntityClick(entity)}
            >
              <div className="entity-name">{entity.canonical_name}</div>
              <div className="entity-meta">
                <span className="entity-type">{entity.entity_type}</span>
                <span className="mention-count">{entity.mention_count} mentions</span>
              </div>
            </div>
          ))}
        </div>

        <div className="mention-panel">
          {selectedEntity ? (
            <>
              <h2>{selectedEntity.canonical_name}</h2>
              <div className="entity-details">
                <p><strong>Type:</strong> {selectedEntity.entity_type}</p>
                <p><strong>Mentions:</strong> {selectedEntity.mention_count}</p>
                <p><strong>Avg Confidence:</strong> {selectedEntity.avg_confidence.toFixed(2)}</p>
                {selectedEntity.aliases.length > 0 && (
                  <p><strong>Aliases:</strong> {selectedEntity.aliases.join(', ')}</p>
                )}
              </div>

              <h3>Mentions</h3>
              <div className="mention-list">
                {mentions.map((mention) => (
                  <div key={mention.id} className="mention-item">
                    <div className="mention-header">
                      <span className="subreddit">r/{mention.subreddit}</span>
                      <span className="confidence">Confidence: {mention.confidence.toFixed(2)}</span>
                    </div>
                    <p className="context">{mention.context}</p>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state">Select an entity to view mentions</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EntityBrowser;
