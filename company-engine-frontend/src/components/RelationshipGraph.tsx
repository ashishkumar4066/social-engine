import { useEffect, useRef, useState } from 'react';
import type { Relationship } from '../types';
import './RelationshipGraph.css';

interface Node {
  id: string;
  label: string;
  type: 'ORG' | 'PERSON' | 'PRODUCT' | 'UNKNOWN';
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface Link {
  source: string;
  target: string;
  relationshipType: string;
  confidence: number;
}

interface Props {
  relationships: Relationship[];
  centerEntity?: string;
}

const RelationshipGraph = ({ relationships, centerEntity }: Props) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const animationFrameRef = useRef<number>();

  // Build graph from relationships
  useEffect(() => {
    if (!relationships.length) return;

    const nodeMap = new Map<string, Node>();
    const linkList: Link[] = [];

    // Extract all unique entities and create nodes
    relationships.forEach((rel) => {
      if (!nodeMap.has(rel.source_entity)) {
        nodeMap.set(rel.source_entity, {
          id: rel.source_entity,
          label: rel.source_entity,
          type: guessEntityType(rel.source_entity),
          x: Math.random() * 800,
          y: Math.random() * 600,
          vx: 0,
          vy: 0,
        });
      }

      if (!nodeMap.has(rel.target_entity)) {
        nodeMap.set(rel.target_entity, {
          id: rel.target_entity,
          label: rel.target_entity,
          type: guessEntityType(rel.target_entity),
          x: Math.random() * 800,
          y: Math.random() * 600,
          vx: 0,
          vy: 0,
        });
      }

      linkList.push({
        source: rel.source_entity,
        target: rel.target_entity,
        relationshipType: rel.relationship_type,
        confidence: rel.confidence,
      });
    });

    // If center entity is specified, position it in the center
    if (centerEntity && nodeMap.has(centerEntity)) {
      const centerNode = nodeMap.get(centerEntity)!;
      centerNode.x = 400;
      centerNode.y = 300;
    }

    setNodes(Array.from(nodeMap.values()));
    setLinks(linkList);
  }, [relationships, centerEntity]);

  // Simple force-directed layout simulation
  useEffect(() => {
    if (!nodes.length || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const simulate = () => {
      // Apply forces
      const updatedNodes = nodes.map((node) => ({ ...node }));

      // Repulsion between nodes
      for (let i = 0; i < updatedNodes.length; i++) {
        for (let j = i + 1; j < updatedNodes.length; j++) {
          const dx = updatedNodes[j].x - updatedNodes[i].x;
          const dy = updatedNodes[j].y - updatedNodes[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 500 / (dist * dist);

          updatedNodes[i].vx -= (dx / dist) * force;
          updatedNodes[i].vy -= (dy / dist) * force;
          updatedNodes[j].vx += (dx / dist) * force;
          updatedNodes[j].vy += (dy / dist) * force;
        }
      }

      // Attraction along links
      links.forEach((link) => {
        const sourceNode = updatedNodes.find((n) => n.id === link.source);
        const targetNode = updatedNodes.find((n) => n.id === link.target);

        if (sourceNode && targetNode) {
          const dx = targetNode.x - sourceNode.x;
          const dy = targetNode.y - sourceNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = dist * 0.01;

          sourceNode.vx += (dx / dist) * force;
          sourceNode.vy += (dy / dist) * force;
          targetNode.vx -= (dx / dist) * force;
          targetNode.vy -= (dy / dist) * force;
        }
      });

      // Update positions with damping
      updatedNodes.forEach((node) => {
        // Don't move center entity
        if (centerEntity && node.id === centerEntity) {
          node.vx = 0;
          node.vy = 0;
          return;
        }

        node.x += node.vx;
        node.y += node.vy;
        node.vx *= 0.85; // damping
        node.vy *= 0.85;

        // Keep within bounds
        node.x = Math.max(50, Math.min(canvas.width - 50, node.x));
        node.y = Math.max(50, Math.min(canvas.height - 50, node.y));
      });

      setNodes(updatedNodes);

      // Draw
      draw(ctx, canvas, updatedNodes);

      animationFrameRef.current = requestAnimationFrame(simulate);
    };

    animationFrameRef.current = requestAnimationFrame(simulate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [nodes.length, links, centerEntity]);

  const draw = (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement, currentNodes: Node[]) => {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw links
    ctx.strokeStyle = '#cbd5e0';
    ctx.lineWidth = 1.5;

    links.forEach((link) => {
      const sourceNode = currentNodes.find((n) => n.id === link.source);
      const targetNode = currentNodes.find((n) => n.id === link.target);

      if (sourceNode && targetNode) {
        ctx.beginPath();
        ctx.moveTo(sourceNode.x, sourceNode.y);
        ctx.lineTo(targetNode.x, targetNode.y);
        ctx.stroke();

        // Draw relationship label
        const midX = (sourceNode.x + targetNode.x) / 2;
        const midY = (sourceNode.y + targetNode.y) / 2;

        ctx.fillStyle = '#666';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(link.relationshipType, midX, midY - 5);
      }
    });

    // Draw nodes
    currentNodes.forEach((node) => {
      const isSelected = selectedNode === node.id;
      const isHovered = hoveredNode === node.id;
      const isCenterEntity = centerEntity === node.id;

      // Node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, isCenterEntity ? 25 : 20, 0, 2 * Math.PI);
      ctx.fillStyle = getNodeColor(node.type, isSelected || isHovered, isCenterEntity);
      ctx.fill();
      ctx.strokeStyle = isSelected || isHovered ? '#2563eb' : '#fff';
      ctx.lineWidth = isSelected || isHovered ? 3 : 2;
      ctx.stroke();

      // Node label
      ctx.fillStyle = '#1a202c';
      ctx.font = isCenterEntity ? 'bold 13px sans-serif' : '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(node.label, node.x, node.y + (isCenterEntity ? 40 : 35));
    });
  };

  const getNodeColor = (type: string, highlighted: boolean, isCenter: boolean): string => {
    if (isCenter) return '#fbbf24'; // Yellow for center

    const colors = {
      ORG: highlighted ? '#3b82f6' : '#60a5fa',
      PERSON: highlighted ? '#8b5cf6' : '#a78bfa',
      PRODUCT: highlighted ? '#10b981' : '#34d399',
      UNKNOWN: highlighted ? '#6b7280' : '#9ca3af',
    };

    return colors[type as keyof typeof colors] || colors.UNKNOWN;
  };

  const guessEntityType = (name: string): 'ORG' | 'PERSON' | 'PRODUCT' | 'UNKNOWN' => {
    // Simple heuristic - this should ideally come from the entity data
    const lowerName = name.toLowerCase();

    // Check for known people indicators
    const peopleNames = ['altman', 'musk', 'nadella', 'pichai', 'zuckerberg', 'bezos', 'cook', 'huang'];
    if (peopleNames.some(p => lowerName.includes(p))) return 'PERSON';

    // Check for product indicators
    const productIndicators = ['gpt', 'chatgpt', 'gemini', 'claude', 'copilot', 'dall-e'];
    if (productIndicators.some(p => lowerName.includes(p))) return 'PRODUCT';

    // Check for org indicators (usually single capitalized words or known companies)
    const orgIndicators = ['openai', 'microsoft', 'google', 'meta', 'anthropic', 'apple'];
    if (orgIndicators.some(o => lowerName.includes(o))) return 'ORG';

    return 'UNKNOWN';
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find clicked node
    const clickedNode = nodes.find((node) => {
      const dist = Math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2);
      return dist < 20;
    });

    setSelectedNode(clickedNode ? clickedNode.id : null);
  };

  const handleCanvasMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find hovered node
    const hovered = nodes.find((node) => {
      const dist = Math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2);
      return dist < 20;
    });

    setHoveredNode(hovered ? hovered.id : null);
    canvas.style.cursor = hovered ? 'pointer' : 'default';
  };

  if (!relationships.length) {
    return (
      <div className="relationship-graph-empty">
        <p>No relationships found</p>
      </div>
    );
  }

  return (
    <div className="relationship-graph">
      <div className="graph-header">
        <h3>Relationship Graph</h3>
        <div className="graph-legend">
          <span className="legend-item">
            <span className="legend-dot" style={{ background: '#60a5fa' }}></span>
            Organization
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: '#a78bfa' }}></span>
            Person
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: '#34d399' }}></span>
            Product
          </span>
        </div>
      </div>

      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        onClick={handleCanvasClick}
        onMouseMove={handleCanvasMouseMove}
        className="graph-canvas"
      />

      {selectedNode && (
        <div className="node-details">
          <h4>{selectedNode}</h4>
          <div className="node-relationships">
            <p><strong>Relationships:</strong></p>
            <ul>
              {links
                .filter((link) => link.source === selectedNode || link.target === selectedNode)
                .map((link, idx) => (
                  <li key={idx}>
                    {link.source === selectedNode ? (
                      <>
                        <strong>{link.relationshipType}</strong> → {link.target}
                      </>
                    ) : (
                      <>
                        {link.source} → <strong>{link.relationshipType}</strong>
                      </>
                    )}
                    <span className="confidence"> ({(link.confidence * 100).toFixed(0)}%)</span>
                  </li>
                ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default RelationshipGraph;
