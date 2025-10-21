"""Generate beautiful HTML reports from analysis data."""
from pathlib import Path
from typing import Optional
from datetime import datetime


def generate_html_report(report, listing, output_path: Path) -> None:
    """Generate an HTML report for a property analysis."""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property Analysis: {report.address}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .score-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 1.5em;
            font-weight: bold;
            margin-top: 20px;
        }}
        
        .property-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .detail-box {{
            text-align: center;
        }}
        
        .detail-label {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }}
        
        .detail-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .loopnet-link {{
            padding: 20px 40px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        
        .loopnet-link a {{
            color: #0066cc;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .loopnet-link a:hover {{
            text-decoration: underline;
        }}
        
        .agent-section {{
            padding: 40px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .agent-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .agent-icon {{
            font-size: 3em;
            margin-right: 20px;
        }}
        
        .agent-title {{
            flex: 1;
        }}
        
        .agent-title h2 {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .agent-score {{
            font-size: 2em;
            font-weight: bold;
            padding: 10px 25px;
            border-radius: 8px;
            background: #e8f5e9;
            color: #2e7d32;
        }}
        
        .agent-score.medium {{
            background: #fff3e0;
            color: #f57c00;
        }}
        
        .agent-score.low {{
            background: #ffebee;
            color: #c62828;
        }}
        
        .rationale {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }}
        
        .rationale h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .notes {{
            list-style: none;
            padding: 0;
        }}
        
        .notes li {{
            padding: 12px 20px;
            margin: 8px 0;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }}
        
        .notes li:before {{
            content: "→";
            color: #667eea;
            font-weight: bold;
            margin-right: 10px;
        }}
        
        .memo-section {{
            padding: 40px;
            background: #fafafa;
        }}
        
        .memo-section h2 {{
            font-size: 2em;
            color: #333;
            margin-bottom: 30px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .memo-content {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .footer {{
            padding: 20px 40px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            background: #f8f9fa;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 {report.address or "Property Analysis"}</h1>
            <div class="subtitle">Listing ID: {report.listing_id}</div>
            <div class="score-badge">Overall Score: {report.scores.overall}/100</div>
        </div>
        
        <div class="property-details">
            <div class="detail-box">
                <div class="detail-label">Asking Price</div>
                <div class="detail-value">{format_price(listing.ask_price)}</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">Cap Rate</div>
                <div class="detail-value">{listing.cap_rate:.1f}%</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">Units</div>
                <div class="detail-value">{listing.units or "N/A"}</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">Building Size</div>
                <div class="detail-value">{format_size(listing.building_size)}</div>
            </div>
            <div class="detail-box">
                <div class="detail-label">Year Built</div>
                <div class="detail-value">{listing.year_built or "N/A"}</div>
            </div>
        </div>
        
        <div class="loopnet-link">
            🔗 <strong>View on LoopNet:</strong> <a href="{build_loopnet_url(listing)}" target="_blank">{build_loopnet_url(listing)}</a>
        </div>
"""

    # Add agent sections
    agents = [
        ("💰", "Investment Agent", report.investment_output, report.scores.investment),
        ("📍", "Location Risk Agent", report.location_output, report.scores.location),
        ("📰", "News/Reddit Agent", report.news_output, report.scores.news_signal),
        ("📊", "VC Risk/Return Agent", report.vc_risk_output, report.scores.risk_return),
        ("🏗️", "Construction Agent", report.construction_output, report.scores.construction),
    ]
    
    for icon, name, output, score in agents:
        if output:
            score_class = "low" if score < 40 else "medium" if score < 70 else ""
            html += f"""
        <div class="agent-section">
            <div class="agent-header">
                <div class="agent-icon">{icon}</div>
                <div class="agent-title">
                    <h2>{name}</h2>
                </div>
                <div class="agent-score {score_class}">{score}/100</div>
            </div>
            
            <div class="rationale">
                <h3>Analysis</h3>
                <p>{output.rationale}</p>
            </div>
            
            <ul class="notes">
"""
            for note in output.notes:
                html += f"                <li>{note}</li>\n"
            
            html += """            </ul>
        </div>
"""

    # Add investment memo
    html += f"""
        <div class="memo-section">
            <h2>📝 Investment Memo</h2>
            <div class="memo-content">
                {markdown_to_html(report.memo_markdown)}
            </div>
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
        </div>
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        return f"${price/1_000_000:.2f}M"
    return f"${price:,.0f}"


def format_size(size: Optional[float]) -> str:
    """Format building size."""
    if size is None:
        return "N/A"
    return f"{size:,.0f} SF"


def build_loopnet_url(listing) -> str:
    """Build LoopNet URL from listing data."""
    listing_id = listing.listing_id
    
    if listing.address and listing.city and listing.state:
        street = listing.address.replace(' ', '-').replace(',', '')
        city_state = f"{listing.city}-{listing.state}".replace(' ', '-').replace(',', '')
        return f"https://www.loopnet.com/Listing/{street}-{city_state}/{listing_id}/"
    
    return f"https://www.loopnet.com/Listing/{listing_id}/"


def markdown_to_html(markdown: str) -> str:
    """Convert simple markdown to HTML (basic implementation)."""
    # Replace headers
    html = markdown.replace("### ", "<h3>").replace("\n\n", "</p><p>")
    html = html.replace("## ", "<h2>")
    
    # Replace bold
    import re
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # Replace bullet points
    lines = html.split('\n')
    in_list = False
    result = []
    
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{line.strip()[2:]}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    
    if in_list:
        result.append('</ul>')
    
    html = '\n'.join(result)
    html = f'<p>{html}</p>'
    
    return html
