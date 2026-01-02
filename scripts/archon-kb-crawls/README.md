# Archon Knowledge Base Crawl Scripts

This directory contains scripts for crawling documentation into Archon's knowledge base using the llms.txt/llms-full.txt standard.

## Quick Start

```bash
# 1. Clean up existing sources that will be re-crawled
python scripts/archon-kb-crawls/cleanup-llms-txt-kbs.py

# 2. Run individual crawl scripts
python scripts/archon-kb-crawls/pydantic-ai-docs-crawl.py
python scripts/archon-kb-crawls/temporal-docs-crawl.py
python scripts/archon-kb-crawls/langfuse-docs-crawl.py
python scripts/archon-kb-crawls/redis-docs-crawl.py
python scripts/archon-kb-crawls/astral-uv-docs-crawl.py
python scripts/archon-kb-crawls/crewai-docs-crawl.py
```

## Available Scripts

### Cleanup Scripts

| Script | Description |
|--------|-------------|
| `cleanup-llms-txt-kbs.py` | Deletes 5 KB sources to prepare for llms.txt re-crawl |
| `cleanup-crewai-kb.py` | Deletes all CrewAI-related sources |

### Crawl Scripts (llms-full.txt)

| Script | URL | Tags |
|--------|-----|------|
| `pydantic-ai-docs-crawl.py` | ai.pydantic.dev/llms-full.txt | pydantic-ai, ai-agents, llm |
| `temporal-docs-crawl.py` | docs.temporal.io/llms-full.txt | temporal, workflows, orchestration |
| `crewai-docs-crawl.py` | docs.crewai.com/llms-full.txt | crewai, ai-agents |

### Crawl Scripts (llms.txt)

| Script | URL | Tags |
|--------|-----|------|
| `langfuse-docs-crawl.py` | langfuse.com/llms.txt | langfuse, llm-observability, tracing |
| `redis-docs-crawl.py` | redis.io/llms.txt | redis, database, cache |
| `astral-uv-docs-crawl.py` | docs.astral.sh/uv/llms.txt | uv, python, package-manager, astral |

## Why Use llms.txt / llms-full.txt?

Many documentation sites provide these files following the [llmstxt.org](https://llmstxt.org) standard:

- **llms.txt** - Index file with links and descriptions
- **llms-full.txt** - Complete documentation in a single file with H1 headers

**Benefits:**

- **Single HTTP request** - Fetches all content at once
- **Automatic section parsing** - Each H1 header becomes a separate "page"
- **Synthetic URLs** - Creates anchored URLs like `llms-full.txt#section-0-agents`
- **Code extraction** - Identifies and indexes code examples
- **Fast** - Seconds instead of minutes compared to crawling individual URLs
- **Clean** - One source instead of 50+ separate ones

## Configuration

All scripts support the `ARCHON_URL` environment variable:

```bash
# Default is http://localhost:8181
export ARCHON_URL=http://your-archon-host:8181

# Then run any script
python scripts/archon-kb-crawls/pydantic-ai-docs-crawl.py
```

## Creating New Crawl Scripts

To check if a documentation site has llms.txt:

```bash
# Check for llms-full.txt (preferred - contains full content)
curl -I https://docs.example.com/llms-full.txt

# Check for llms.txt (index only)
curl -I https://docs.example.com/llms.txt
```

If it returns 200, copy one of the existing scripts and modify:

1. Update `LLMS_URL` or `LLMS_FULL_URL`
2. Update `TAGS` list
3. Update the print statements for the doc name

## Documentation Sites with llms.txt

Sites we've verified have llms.txt files available:

| Site | llms.txt | llms-full.txt |
|------|----------|---------------|
| ai.pydantic.dev | Yes | Yes |
| docs.temporal.io | Yes | Yes |
| docs.crewai.com | Yes | Yes |
| langfuse.com | Yes | No |
| redis.io | Yes | No |
| docs.astral.sh/uv | Yes | No |

Sites we've verified do NOT have llms.txt:
- developer.hashicorp.com
- docs.pydantic.dev
- fastapi.tiangolo.com
- clickhouse.com
- postgresql.org
- keycloak.org
- docs.min.io
- hatch.pypa.io
- docs.coqui.ai
- python-sounddevice.readthedocs.io

## Best Practices

1. **Check for llms-full.txt first** - It contains complete content, not just an index
2. **Fall back to llms.txt** - If no llms-full.txt, the index version still works
3. **Use appropriate tags** - Helps with filtering when searching
4. **Clean up before re-crawling** - Use cleanup scripts to remove old sources
5. **One source per documentation set** - Don't create separate sources for the same docs
