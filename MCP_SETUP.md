# MCP Server Configuration

This workspace is configured to use the **Serper MCP Server** for Google Search integration.

## What is MCP?

MCP (Model Context Protocol) allows AI assistants like GitHub Copilot to access external tools and data sources.

## Configured Servers

### Serper (Google Search)

**Package**: `serper-search-scrape-mcp-server` (v0.1.2)  
**Purpose**: Provides Google search and web scraping capabilities

**Available Tools:**
- `web_search` - Search Google and get results
- `image_search` - Search Google Images
- `webpage_scrape` - Scrape content from web pages

## Setup

### Prerequisites
- Node.js ≥ 20 (currently using v20.19.0)
- Serper API key from https://serper.dev/

### Configuration

1. The `mcp.json` file is already configured (gitignored for security)
2. To create your own, copy the example:
   ```bash
   cp mcp.json.example mcp.json
   ```
3. Edit `mcp.json` and replace `your_serper_api_key_here` with your actual Serper API key

### Verification

Test that the MCP server works:
```bash
SERPER_API_KEY="your_key" npx -y serper-search-scrape-mcp-server
```

### Usage in VS Code

1. **Reload VS Code**: Developer → Reload Window
2. **Test in Copilot Chat**: Type `/mcp serper` to see available tools
3. **Use in queries**: Ask Copilot to search the web, e.g., "Search for the latest Python best practices"

## Security

⚠️ **Important**: 
- The `mcp.json` file contains your API key and is **gitignored**
- Never commit `mcp.json` to version control
- Use `mcp.json.example` as a template for documentation

## Troubleshooting

**Issue**: MCP server not showing up in Copilot  
**Solution**: Reload VS Code window (Cmd+Shift+P → "Developer: Reload Window")

**Issue**: API key errors  
**Solution**: Verify your Serper API key is valid at https://serper.dev/dashboard

**Issue**: Package not found  
**Solution**: Ensure Node.js ≥ 20 is installed (`node -v`)

## Links

- Serper API: https://serper.dev/
- Serper MCP Package: https://www.npmjs.com/package/serper-search-scrape-mcp-server
- MCP Documentation: https://modelcontextprotocol.io/

---

**Status**: ✅ Serper MCP configured and ready to use
