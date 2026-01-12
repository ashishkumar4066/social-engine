# entity_report.py
"""
Entity Report Generator - Creates HTML Reports

Generates a beautiful HTML report showing:
- Summary statistics
- Entities grouped by type (Organizations, People, Products)
- Detailed mentions with context and confidence scores
- Clickable links to Reddit posts

Usage:
    from entity_report import generate_html_report

    html = generate_html_report(resolver, company_name="OpenAI")

    # Save to file
    with open("entity_report.html", "w") as f:
        f.write(html)
"""

from typing import List, Dict
from datetime import datetime

try:
    from .entity_resolver import EntityResolver
    from .entity_models import CanonicalEntity
except ImportError:
    from entity_resolver import EntityResolver
    from entity_models import CanonicalEntity


def generate_html_report(
    resolver: EntityResolver,
    company_name: str = "Company",
    subreddits: List[Dict] = None,
    output_file: str = None,
) -> str:
    """
    Generate an HTML report of extracted entities.

    Args:
        resolver: EntityResolver with extracted entities
        company_name: Name of the company analyzed
        subreddits: List of subreddit dicts (optional)
        output_file: If provided, save to this file

    Returns:
        HTML string
    """

    # Get data
    summary = resolver.get_summary()
    all_entities = resolver.get_all_entities()
    orgs = resolver.get_entities_by_type("ORG")
    people = resolver.get_entities_by_type("PERSON")
    products = resolver.get_entities_by_type("PRODUCT")

    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Entity Report - {company_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 10px;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .section {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .entity-list {{
            display: grid;
            gap: 15px;
        }}
        
        .entity-card {{
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.2s;
        }}
        
        .entity-card:hover {{
            border-color: #667eea;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }}
        
        .entity-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .entity-name {{
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
        }}
        
        .entity-badges {{
            display: flex;
            gap: 8px;
        }}
        
        .badge {{
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 500;
        }}
        
        .badge-mentions {{
            background: #e3f2fd;
            color: #1565c0;
        }}
        
        .badge-confidence {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        
        .aliases {{
            font-size: 0.85em;
            color: #666;
            margin-bottom: 10px;
        }}
        
        .aliases span {{
            background: #f0f0f0;
            padding: 2px 8px;
            border-radius: 4px;
            margin-right: 5px;
            display: inline-block;
            margin-bottom: 4px;
        }}
        
        .mentions-container {{
            margin-top: 10px;
        }}
        
        .mention {{
            background: #fafafa;
            border-left: 3px solid #667eea;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 0 5px 5px 0;
        }}
        
        .mention-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }}
        
        .mention-raw {{
            font-weight: 500;
            color: #667eea;
        }}
        
        .mention-confidence {{
            font-size: 0.85em;
            color: #666;
        }}
        
        .mention-context {{
            font-size: 0.9em;
            color: #555;
            font-style: italic;
        }}
        
        .mention-source {{
            font-size: 0.8em;
            color: #888;
            margin-top: 5px;
        }}
        
        .mention-source a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .mention-source a:hover {{
            text-decoration: underline;
        }}
        
        .toggle-btn {{
            background: #f0f0f0;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.85em;
            color: #666;
            transition: all 0.2s;
        }}
        
        .toggle-btn:hover {{
            background: #e0e0e0;
        }}
        
        .hidden {{
            display: none;
        }}
        
        .subreddit-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .subreddit-tag {{
            background: #e3f2fd;
            color: #1565c0;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
        }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: #888;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .entity-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏷️ Entity Report</h1>
            <p>Social Intelligence Analysis for <strong>{company_name}</strong></p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </header>
        
        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{summary['total_entities']}</div>
                <div class="label">Unique Entities</div>
            </div>
            <div class="stat-card">
                <div class="number">{summary['total_mentions']}</div>
                <div class="label">Total Mentions</div>
            </div>
            <div class="stat-card">
                <div class="number">{summary['by_type'].get('ORG', 0)}</div>
                <div class="label">Organizations</div>
            </div>
            <div class="stat-card">
                <div class="number">{summary['by_type'].get('PERSON', 0)}</div>
                <div class="label">People</div>
            </div>
            <div class="stat-card">
                <div class="number">{summary['by_type'].get('PRODUCT', 0)}</div>
                <div class="label">Products</div>
            </div>
        </div>
        
        <!-- Organizations Section -->
        <div class="section">
            <h2>🏢 Organizations</h2>
            <div class="entity-list">
                {_generate_entity_cards(orgs[:15])}
            </div>
        </div>
        
        <!-- People Section -->
        <div class="section">
            <h2>👤 People</h2>
            <div class="entity-list">
                {_generate_entity_cards(people[:15])}
            </div>
        </div>
        
        <!-- Products Section -->
        <div class="section">
            <h2>📦 Products</h2>
            <div class="entity-list">
                {_generate_entity_cards(products[:15])}
            </div>
        </div>
        
        <footer>
            <p>Generated by Social Intelligence Engine</p>
            <p>Powered by Reddit API & Entity Resolution</p>
        </footer>
    </div>
    
    <script>
        function toggleMentions(id) {{
            const el = document.getElementById(id);
            const btn = document.getElementById('btn-' + id);
            if (el.classList.contains('hidden')) {{
                el.classList.remove('hidden');
                btn.textContent = 'Hide mentions';
            }} else {{
                el.classList.add('hidden');
                btn.textContent = 'Show mentions';
            }}
        }}
    </script>
</body>
</html>
    """

    # Save to file if requested
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Report saved to: {output_file}")

    return html


def _generate_entity_cards(entities: List[CanonicalEntity]) -> str:
    """Generate HTML for entity cards"""
    if not entities:
        return "<p style='color: #888; padding: 20px;'>No entities found in this category.</p>"

    cards_html = ""

    for i, entity in enumerate(entities):
        entity_id = f"entity-{i}-{entity.canonical_name.replace(' ', '-').lower()}"

        # Aliases HTML
        aliases_html = ""
        if entity.aliases:
            aliases_html = "<div class='aliases'>Aliases: "
            for alias in entity.aliases[:5]:
                aliases_html += f"<span>{_escape_html(alias)}</span>"
            if len(entity.aliases) > 5:
                aliases_html += f"<span>+{len(entity.aliases) - 5} more</span>"
            aliases_html += "</div>"

        # Subreddits HTML
        subreddits = entity.subreddits_mentioned_in[:5]
        subreddits_html = ""
        if subreddits:
            subreddits_html = "<div class='subreddit-list' style='margin-top: 10px;'>"
            for sub in subreddits:
                subreddits_html += f"<span class='subreddit-tag'>r/{sub}</span>"
            subreddits_html += "</div>"

        # Mentions HTML
        mentions_html = ""
        for j, mention in enumerate(entity.mentions[:5]):
            confidence_class = (
                "high"
                if mention.confidence >= 0.9
                else "medium" if mention.confidence >= 0.7 else "low"
            )

            source_link = ""
            if mention.source_subreddit:
                if mention.source_url:
                    source_link = f"<a href='https://reddit.com{mention.source_url}' target='_blank'>r/{mention.source_subreddit}</a>"
                else:
                    source_link = f"r/{mention.source_subreddit}"

            mentions_html += f"""
            <div class="mention">
                <div class="mention-header">
                    <span class="mention-raw">"{_escape_html(mention.raw_text)}"</span>
                    <span class="mention-confidence">{mention.confidence:.0%} confidence ({mention.match_method})</span>
                </div>
                <div class="mention-context">{_escape_html(mention.context[:150])}...</div>
                <div class="mention-source">Source: {source_link}</div>
            </div>
            """

        if len(entity.mentions) > 5:
            mentions_html += f"<p style='color: #888; font-size: 0.85em;'>... and {len(entity.mentions) - 5} more mentions</p>"

        # Build card
        cards_html += f"""
        <div class="entity-card">
            <div class="entity-header">
                <span class="entity-name">{_escape_html(entity.canonical_name)}</span>
                <div class="entity-badges">
                    <span class="badge badge-mentions">{entity.mention_count} mentions</span>
                    <span class="badge badge-confidence">{entity.avg_confidence:.0%} avg confidence</span>
                </div>
            </div>
            {aliases_html}
            {subreddits_html}
            <button class="toggle-btn" id="btn-{entity_id}" onclick="toggleMentions('{entity_id}')">
                Show mentions
            </button>
            <div id="{entity_id}" class="mentions-container hidden">
                {mentions_html}
            </div>
        </div>
        """

    return cards_html


def _escape_html(text: str) -> str:
    """Escape HTML special characters"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    from src.entity.entity_resolver import EntityResolver

    print("Generating test report...")

    # Create resolver with test data
    resolver = EntityResolver()

    test_data = [
        ("OpenAI", "...OpenAI announced new features today...", "MachineLearning"),
        ("Open AI", "...I think Open AI is great...", "technology"),
        ("openai", "...openai released an update...", "artificial"),
        ("ChatGPT", "...ChatGPT helped me write this...", "ChatGPT"),
        ("chat gpt", "...I use chat gpt every day...", "OpenAI"),
        ("Sam Altman", "...Sam Altman said in an interview...", "technology"),
        ("Altman", "...Altman tweeted about AI safety...", "singularity"),
        ("GPT-4", "...GPT-4 is very capable...", "LocalLLaMA"),
        ("Microsoft", "...Microsoft invested billions...", "technology"),
        ("Elon Musk", "...Elon Musk criticized OpenAI...", "technology"),
        ("Claude", "...Claude from Anthropic is good...", "artificial"),
        ("Anthropic", "...Anthropic released Claude 3...", "MachineLearning"),
    ]

    for raw_text, context, subreddit in test_data:
        resolver.resolve(
            raw_text,
            context,
            {"subreddit": subreddit, "post_id": "123", "url": "/r/test/comments/123"},
        )

    # Generate report
    html = generate_html_report(
        resolver, company_name="OpenAI", output_file="test_entity_report.html"
    )

    print(f"\n✅ Report generated! Open test_entity_report.html in your browser.")
