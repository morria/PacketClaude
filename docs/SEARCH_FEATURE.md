# Web Search Feature

PacketClaude now supports web search capability, allowing Claude to search the internet for current information when answering queries.

## How It Works

When web search is enabled, Claude has access to a `web_search` tool that can search DuckDuckGo for current information. Claude will automatically decide when to use this tool based on your query.

For example:
- "What's the current weather?" - Claude may search for weather information
- "Latest news about amateur radio" - Claude will search for current news
- "What happened today in technology?" - Claude will search for today's tech news

## Configuration

Web search is controlled in `config/config.yaml`:

```yaml
search:
  # Enable/disable web search capability
  enabled: true

  # Maximum number of search results to return
  max_results: 5
```

### Options:

- **enabled**: Set to `true` to enable web search, `false` to disable
- **max_results**: Number of search results Claude can retrieve (1-10 recommended)

## Usage

Once enabled, there's nothing special you need to do! Just ask Claude questions that might benefit from current information:

**Examples:**
```
> What's the latest news about SpaceX?
> Current weather in Seattle
> Recent AI developments
> Latest amateur radio regulations
```

Claude will automatically:
1. Recognize when current information is needed
2. Search the internet using DuckDuckGo
3. Analyze the search results
4. Provide a concise answer based on the findings

## Technical Details

- **Search Engine**: DuckDuckGo (no API key required)
- **Package**: `ddgs` Python library
- **Tool Integration**: Uses Anthropic's tool calling API
- **Max Iterations**: Claude can make up to 5 tool calls per response

## Performance Considerations

- Search queries add latency to responses (typically 1-3 seconds per search)
- Each search uses additional tokens in the API call
- Over packet radio, this means longer transmission times
- Consider adjusting `max_results` to balance information vs. speed

## Disabling Search

To disable web search:

1. Edit `config/config.yaml`
2. Set `search.enabled: false`
3. Restart PacketClaude

When disabled, Claude will rely only on its training data.

## Privacy & Rate Limiting

- Searches are performed via DuckDuckGo (privacy-focused)
- No search history is stored beyond the current conversation session
- Rate limiting still applies to the overall query (including search results)
- Search queries are logged in PacketClaude's activity logs

## Troubleshooting

**Search not working:**
- Check that `search.enabled: true` in config
- Verify internet connectivity
- Check logs for error messages
- Ensure `ddgs` package is installed: `pip install ddgs`

**Slow responses:**
- Reduce `max_results` to 2-3
- Check network latency
- Consider disabling search for faster responses

**No search results:**
- DuckDuckGo may be rate limiting
- Try a different search query
- Check firewall/proxy settings
