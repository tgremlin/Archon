---
name: analyze-docs-url
description: Analyze documentation URL structure and generate Archon crawl or fetch scripts
arguments:
  - name: url
    description: Documentation base URL to analyze (e.g., https://docs.example.com)
    required: true
tools_enabled:
  - WebFetch
  - AskUserQuestion
---

# Analyze Documentation URL for Archon Script Generation

Analyze a documentation website's structure, identify optimal crawl settings, filter out non-documentation pages, and generate a ready-to-run script for direct fetch or crawling via Archon's REST API.

## Execution Workflow

**IMPORTANT WORKFLOW:**
1. **Check for llms-full.txt, llms.txt, llms-ctx.txt FIRST** (PHASE 0) - This is the best source when available
2. Analyze site structure (PHASE 1-3)
3. Present findings with recommendations (PHASE 4)
4. Ask user questions (PHASE 4)
5. **DEFAULT: Generate and save the appropriate script** (PHASE 5-6)
6. Present usage instructions

**The script generation is the DEFAULT final step** - always create the script file unless user explicitly requests otherwise.

### PHASE 0: Check for LLM-Friendly Files (CRITICAL FIRST STEP)

**ALWAYS check for llms-full.txt, llms.txt, and llms-ctx.txt before any other analysis.** These are curated documentation files maintained by site owners.

Use `WebFetch` with a lightweight HEAD request first to check existence and size:

**Files to check (in order):**
1. `llms-full.txt` - Complete documentation in one file (BEST)
2. `llms.txt` - Navigation index with curated links
3. `llms-ctx.txt` - Context-optimized variant (if provided)

For each check:
- Do a HEAD request first (donNOt download yet)
- Read the `Content-Length` header when available
- Report size estimates in KB

**HEAD Check Template:**
```
URL: {base_domain}/llms-full.txt
Prompt: "Do a HEAD request to verify this file exists. If it exists, return status code and Content-Length."
```

**If any LLM-friendly file is found:**
- Present a clear status summary with size estimates
- Follow the decision tree below
- Generate a direct fetch/chunk script by default (only fall back to crawl if user chooses option 2 for llms.txt)

**Benefits of llms-full.txt/llms.txt/llms-ctx.txt:**
- Curated by site owner - exactly what should be indexed
- No crawling needed
- Clean, filtered content
- Optimized for LLM consumption
- Predictable ingestion size

### Decision Tree (after HEAD checks)

**If llms-full.txt exists:**
```
OK Found: {base_domain}/llms-full.txt ({size} KB)

This site provides LLM-optimized documentation in a single file.
No crawling needed!

Recommended: Fetch this file directly and chunk it for your KB.
Generate script? [Y/n]
Generate scriptFAIL [Y/n]
```

**If llms-ctx.txt exists (no llms-full.txt):**
```
OK Found: {base_domain}/llms-ctx.txt ({size} KB)
NO llms-full.txt available

This site provides a context-optimized documentation file.
No crawling needed!

Recommended: Fetch this file directly and chunk it for your KB.
Generate scriptFAIL [Y/n]
```


**If only llms.txt exists (no llms-full.txt or llms-ctx.txt):**
```
OK Found: {base_domain}/llms.txt (navigation index)
NO llms-full.txt or llms-ctx.txt available

The llms.txt file contains links to documentation files.
We can parse it to get a curated list of URLs to fetch.

Options:
1. Parse llms.txt and fetch only the linked files (recommended)
2. Fall back to full site crawl with filtering

Choose [1/2]:
```

**If neither exists:**
```
NO llms.txt, llms-full.txt, or llms-ctx.txt found

This site doesn't support the llms.txt standard (including llms-full/ctx).
Falling back to traditional crawl analysis...
```


### PHASE 1: Site Structure Discovery

**Only proceed here if llms-full.txt/llms.txt/llms-ctx.txt NOT found.**

Use `WebFetch` to analyze the provided URL:

**Fetch 1 - Landing Page Analysis:**
```
URL: {user_provided_url}
Prompt: "Analyze this documentation page structure. List:
1. All navigation sections and their URLs
2. Identify sidebar/header navigation structure
3. Note any links to non-documentation pages (About, Careers, Blog, Company, Contact, Support Portal, etc.)
4. Identify separate documentation paths (e.g., /docs, /api, /cli as siblings not nested)
5. Estimate the hierarchy depth (how many levels deep does content goNO)
6. Note if there's a sitemap.xml or llms.txt file mentioned
7. **IMPORTANT: Identify the exact domain (e.g., docs.example.com) and note any links to OTHER subdomains (e.g., www.example.com, blog.example.com)**"
```

**Fetch 2 - Sample Content Pages:**
Pick 2-3 URLs from different sections and fetch them:
```
Prompt: "What is the URL depth of this pageNO How many path segments from the domainNO
Does this page contain substantial documentation content or is it just a navigation pageNO
List any child pages linked from here.
**Note any links to different subdomains than the starting URL.**"
```

### PHASE 2: Link Classification & Exclusion Guidance

Based on the fetched data, classify all discovered links into categories:

**Documentation Content:**
- `/docs/*` - Conceptual documentation
- `/api/*` or `/api-docs/*` - API reference
- `/cli/*` or `/commands/*` - CLI documentation
- `/guides/*` or `/tutorials/*` - How-to guides
- `/reference/*` - Technical reference

**Non-Documentation (AUTOMATICALLY EXCLUDED by Archon):**

Archon's backend filtering automatically excludes URLs matching these patterns:
```
# Company/corporate pages
/careers, /jobs, /hiring, /join-us
/about, /about-us, /team, /company, /leadership

# Commercial pages
/pricing, /plans, /enterprise, /demo, /trial
/contact, /sales, /request-demo

# Authentication pages
/signup, /sign-up, /login, /sign-in, /register
/dashboard, /account, /settings

# Legal pages
/legal, /privacy, /terms, /cookie, /gdpr
/tos, /eula, /compliance

# Blog and news
/blog, /news, /press, /media, /announcements

# Community/forum
/forum, /community, /discuss, /support/tickets

# Status pages
/status, /uptime, /incidents

# Marketing tracking
NOutm_*

# Social/misc
/share, /tweet, /social
/app, /product, /features
/subscribe, /newsletter, /webinar, /events
```

**Ambiguous (Ask User):**
- `/examples`, `/samples` - May contain useful code
- `/changelog`, `/releases` - Version history
- `/glossary`, `/faq` - Reference material
- `/integrations`, `/plugins` - Extension documentation

### PHASE 3: Depth Analysis & Crawl Strategy

**CRITICAL INSIGHT:** Recursive crawls follow ALL internal links, including navigation links that go UP the hierarchy (parent pages, breadcrumbs, home links). This often results in crawling the entire site instead of the intended section.

**PREFERRED STRATEGY:** Use **individual depth-1 crawls** for specific pages instead of recursive crawls.

#### Strategy Decision Tree:

**Option A: Multiple Depth-1 Crawls (RECOMMENDED)**
-  **When to use:** You have a list of specific documentation pages
-  **Advantage:** Crawls ONLY the pages you want, no hierarchy traversal
-  **Example:**
  ```
  /docs/installation          Depth 1 (only this page)
  /docs/configuration         Depth 1 (only this page)
  /docs/api/authentication    Depth 1 (only this page)
  ```
-  **Result:** 3 targeted pages, nothing else

**Option B: Recursive Crawl with Depth > 1 (USE WITH CAUTION)**
-   **When to use:** Site has clean hierarchy with no upward navigation links
-   **Risk:** Will follow ALL internal links including parent/home/breadcrumb links
-   **Example:**
  ```
  /docs/guides/authentication  Depth 3
  ```
-   **Result:** May crawl /docs (parent), / (home), /docs/guides (parent), and siblings

**Option C: Sitemap or llms.txt (BEST IF AVAILABLE)**
-  **When to use:** Site provides sitemap.xml or llms.txt
-  **Advantage:** Site owner has curated the exact pages to crawl
-  **Result:** Perfect coverage with zero over-crawling

#### Depth Analysis Heuristics:

**For Recursive Crawls (if used):**
```
Depth 1: Crawls ONLY the provided URL
   Use when: You want a single specific page
   Example: /docs/api/users  crawls just that one page

Depth 2: Crawls URL + immediate child pages (one hop)
   Use when: You want a section and its direct children
   Risk: Will also follow navigation links to siblings/parents
   Example: /docs/guides  may also crawl /docs, /docs/api, etc.

Depth 3+: Crawls URL + children + grandchildren (two+ hops)
   Use when: Very deep nested content (rare)
   Risk: HIGH - will crawl extensively, often beyond intended scope
   Warning: Usually results in crawling parent pages and entire site
```

**Red Flags for Over-Crawling:**
-  Navigation links point UP the hierarchy (parent/home links)
-  Breadcrumb links (these go backwards to parents)
-  Pagination links (creates duplicate content)
-  Version switchers (multiplies pages unnecessarily)
-  Cross-section navigation (sidebar links to other doc areas)

#### Recommendation Logic:

1. **Check for llms-full.txt first**  BEST option - single file with all curated content
2. **Check for llms.txt**  GOOD option - curated URL list from site owner
3. **Check for sitemap.xml**  Use if available
4. **If you have specific page URLs**  Use multiple depth-1 crawls
5. **If you need to discover pages**  Use depth 2 carefully with strict domain filtering
6. **Never use depth 3+** unless absolutely certain about site structure

### PHASE 4: User Interaction

Use `AskUserQuestion` to present findings:

- If llms-full.txt or llms-ctx.txt is found, skip questions and generate the direct fetch script.
- If llms.txt is found (no llms-full/ctx), only ask the llms.txt option question (parse vs crawl).

**Question 1 - Content Selection (skip if llms files found):**
```yaml
question: "Which documentation sections should be crawledNO"
header: "Content Sections"
multiSelect: true
options:
  - label: "Main Documentation (/docs)"
    description: "Conceptual guides and getting started - Estimated: X pages at depth Y"
  - label: "API Reference (/api)"
    description: "REST/GraphQL API documentation - Estimated: X pages at depth Y"
  - label: "CLI Documentation (/cli)"
    description: "Command-line interface reference - Estimated: X pages at depth Y"
  # ... (dynamically generated based on discovered sections)
```

**Question 2 - Crawl Strategy:**
```yaml
question: "Which crawl strategy should we useNO"
header: "Strategy"
multiSelect: false
options:
  - label: "Use llms-full.txt (Recommended)"  # Only show if found in PHASE 0
    description: "Single file with ALL documentation content. Curated by site owner, perfect coverage."
  - label: "Use llms.txt Index (Recommended)"  # Only show if found in PHASE 0
    description: "Parse llms.txt and fetch linked files (curated by site owner)."
  - label: "Multiple Depth-1 Crawls"
    description: "Create individual crawls for each specific page URL. Most precise, avoids over-crawling."
  - label: "Recursive Crawl with Depth 2-3"
    description: "Fallback when no llms files are usable; may crawl parent/sibling pages unintentionally."
```

**Question 3 - Ambiguous Content:**
```yaml
question: "Include these additional sectionsNO"
header: "Optional Sections"
multiSelect: true
options:
  - label: "Examples/Samples"
    description: "Code examples - may contain valuable snippets"
  - label: "Changelog"
    description: "Version history - useful for understanding changes"
  # ... (only show if ambiguous sections found)
```

**REMOVED:** Script format question - generate the appropriate script by default (llms fetch vs crawl).

### PHASE 5: Generate Script (DEFAULT FINAL STEP)

**IMPORTANT:** After completing user questions, ALWAYS generate a ready-to-run script by default. Use the user's answers to configure the script appropriately.

Based on user selections, generate a complete, ready-to-run script with the correct implementation (direct fetch or crawl).

#### Priority Order for Script Generation:
1. **If llms-full.txt found** -> Generate Archon crawl script pointing to llms-full.txt (Archon handles parsing automatically!)
2. **If llms.txt found** -> Parse llms.txt for URLs, then use Archon crawl API
3. **Otherwise** -> Use standard depth-1 or recursive crawl script with strict domain filtering enabled by default

**CRITICAL INSIGHT:** Archon has **built-in support** for llms-full.txt files. When you point Archon's crawl endpoint at an llms-full.txt URL, it automatically:
- Detects the file type
- Parses H1 sections (`# Header`) into separate "pages"
- Creates embeddings for each section
- Extracts and indexes code examples
- Stores everything in a single KB source

**DO NOT manually chunk llms-full.txt files** - use Archon's API!

---

#### Python Script Template for llms-full.txt (USE ARCHON API):

```python
#!/usr/bin/env python3
"""
{site_name} Documentation Crawl Script for Archon
Generated: {current_date}

Uses llms-full.txt for efficient ingestion:
- Single HTTP request to fetch complete documentation
- Archon automatically parses H1 sections into separate "pages"
- Creates one KB source with all content properly organized

This is much cleaner than crawling individual URLs because:
1. One source instead of many separate ones
2. Built-in parsing of llms-full.txt format
3. No rate limiting or timeouts
4. Faster (seconds instead of minutes)
"""

import os
import sys
import time

import httpx

# =============================================================================
# Configuration
# =============================================================================

ARCHON_URL = os.environ.get("ARCHON_URL", "http://localhost:8181")
LLMS_FULL_URL = "{llms_full_url}"

POLL_INTERVAL = 3  # seconds between progress checks
REQUEST_TIMEOUT = 60  # seconds for API requests

# Tags for the knowledge source
TAGS = {tags_list}


def check_archon_health() -> bool:
    """Check if Archon is available."""
    try:
        response = httpx.get(f"{ARCHON_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error connecting to Archon: {e}")
        return False


def start_crawl() -> str | None:
    """Start crawling the llms-full.txt file and return progress ID."""
    payload = {
        "url": LLMS_FULL_URL,
        "max_depth": 1,  # Not needed for single file, but required by API
        "knowledge_type": "technical",
        "tags": TAGS,
        "extract_code_examples": True,
        "strict_domain": True,
    }

    try:
        print(f"Starting crawl: {LLMS_FULL_URL}")
        response = httpx.post(
            f"{ARCHON_URL}/api/knowledge-items/crawl",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        progress_id = data.get("progressId")
        print(f"Crawl started with progress ID: {progress_id}")
        return progress_id
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code}")
        print(f"Response: {e.response.text[:500]}")
        return None
    except Exception as e:
        print(f"Error starting crawl: {e}")
        return None


def poll_progress(progress_id: str) -> dict:
    """Poll crawl progress until completion."""
    print("\nTracking progress:")
    start_time = time.time()

    while True:
        try:
            response = httpx.get(
                f"{ARCHON_URL}/api/crawl-progress/{progress_id}",
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 404:
                time.sleep(POLL_INTERVAL)
                continue

            response.raise_for_status()
            data = response.json()

            status = str(data.get("status", "unknown"))
            progress_value = data.get("progress", 0)
            log_msg = str(data.get("log", ""))
            total_pages = data.get("totalPages", 0)
            processed_pages = data.get("processedPages", 0)

            try:
                progress_int = int(float(progress_value))
            except (TypeError, ValueError):
                progress_int = 0

            elapsed = int(time.time() - start_time)
            pages_info = f"[{processed_pages}/{total_pages}]" if total_pages > 0 else ""
            print(
                f"\r  [{progress_int:3d}%] {status:12s} {pages_info:10s} | {log_msg[:50]:<50} ({elapsed}s)",
                end="",
            )

            if status in ["completed", "error", "cancelled", "failed"]:
                print()
                return data

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user!")
            raise
        except Exception as e:
            print(f"\n  Poll error: {e}")
            time.sleep(POLL_INTERVAL)


def print_summary(result: dict) -> None:
    """Print crawl summary."""
    print(f"\n{'='*60}")
    print("CRAWL SUMMARY")
    print(f"{'='*60}\n")

    status = result.get("status", "unknown")
    source_id = result.get("sourceId", "N/A")
    chunks_stored = result.get("chunksStored", 0)
    code_examples = result.get("codeExamplesFound", 0)
    total_pages = result.get("totalPages", 0)

    print(f"Status:        {status}")
    print(f"Source ID:     {source_id}")
    print(f"Sections:      {total_pages}")
    print(f"Chunks stored: {chunks_stored}")
    print(f"Code examples: {code_examples}")

    if status == "completed":
        print("\nThe documentation is now available in Archon!")
        print("You can search it using:")
        print(f'  rag_search_knowledge_base(query="your query", source_id="{source_id}")')
    elif status == "error":
        error_msg = result.get("error") or result.get("log", "Unknown error")
        print(f"\nError: {error_msg}")

    print(f"\n{'='*60}")


def main() -> int:
    """Main entry point."""
    print(f"\n{'#'*60}")
    print("# {site_name} Documentation Crawl for Archon")
    print("# Using llms-full.txt for efficient ingestion")
    print(f"# Target: {LLMS_FULL_URL}")
    print(f"# Archon: {ARCHON_URL}")
    print(f"{'#'*60}\n")

    if not check_archon_health():
        print(f"Error: Cannot connect to Archon at {ARCHON_URL}")
        print("\nMake sure Archon is running and try again.")
        return 1

    print("Archon is healthy.\n")

    print("This will crawl the llms-full.txt file and create a single")
    print("knowledge source with all documentation sections.")
    print(f"Tags: {', '.join(TAGS)}\n")

    try:
        input("Press Enter to start (Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 0

    progress_id = start_crawl()
    if not progress_id:
        print("Failed to start crawl.")
        return 1

    try:
        result = poll_progress(progress_id)
    except KeyboardInterrupt:
        print("\n\nCrawl interrupted by user!")
        return 1

    print_summary(result)

    return 0 if result.get("status") == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
```

---

#### Python Script Template for Cleanup (Delete Existing Sources):

When re-crawling, users may want to delete existing sources first. Include this companion script:

```python
#!/usr/bin/env python3
"""
{site_name} Knowledge Base Cleanup Script for Archon
Generated: {current_date}

Deletes all Archon knowledge sources related to {site_name}:
- Title starting with "{site_prefix}" (case-insensitive)
- URL containing "{domain}"
"""

import os
import sys

import httpx

ARCHON_URL = os.environ.get("ARCHON_URL", "http://localhost:8181")
REQUEST_TIMEOUT = 30


def get_knowledge_sources() -> list[dict]:
    """Fetch all knowledge sources from Archon."""
    try:
        response = httpx.get(
            f"{ARCHON_URL}/api/knowledge-items/summary",
            params={"page": 1, "per_page": 500},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        print(f"Error fetching sources: {e}")
        return []


def filter_sources(sources: list[dict]) -> list[dict]:
    """Filter sources related to {site_name}."""
    matched = []
    for source in sources:
        title = source.get("title") or ""
        url = source.get("url") or ""
        if title.lower().startswith("{site_prefix_lower}") or "{domain}" in url.lower():
            matched.append(source)
    return matched


def delete_source(source_id: str, title: str) -> bool:
    """Delete a single knowledge source."""
    try:
        response = httpx.delete(
            f"{ARCHON_URL}/api/knowledge-items/{source_id}",
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code in (200, 204):
            print(f"  [OK] Deleted: {title}")
            return True
        else:
            print(f"  [FAIL] {title}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] {title}: {e}")
        return False


def main() -> int:
    print(f"\n{'='*60}")
    print("{site_name} Knowledge Base Cleanup")
    print(f"Archon URL: {ARCHON_URL}")
    print(f"{'='*60}\n")

    try:
        response = httpx.get(f"{ARCHON_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"Warning: Archon health check returned {response.status_code}")
    except Exception as e:
        print(f"Error: Cannot connect to Archon at {ARCHON_URL}")
        return 1

    print("Fetching knowledge sources...")
    sources = get_knowledge_sources()

    if not sources:
        print("No knowledge sources found.")
        return 0

    matched = filter_sources(sources)

    if not matched:
        print("\nNo {site_name} sources found.")
        return 0

    print(f"\nFound {len(matched)} sources to delete:\n")
    for source in matched:
        source_id = source.get("source_id") or source.get("id") or "?"
        title = source.get("title") or "?"
        print(f"  {source_id}: {title}")

    try:
        confirm = input("\nDelete these sources? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            return 0
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 0

    print("\nDeleting sources...")
    success = sum(1 for s in matched if delete_source(
        s.get("source_id") or s.get("id"),
        s.get("title") or "?"
    ))

    print(f"\nDeleted: {success}/{len(matched)}")
    return 0 if success == len(matched) else 1


if __name__ == "__main__":
    sys.exit(main())
```

---

#### Python Script Template:


```python
#!/usr/bin/env python3
"""
Archon Documentation Crawl Script
Generated for: {site_name}
Date: {current_date}

This script crawls selected documentation sections via Archon's REST API.
"""

import requests
import time
import json
from typing import Dict, List

# Archon Configuration
ARCHON_URL = "http://localhost:8181"
POLL_INTERVAL = 2  # seconds

# Crawl Configuration
# Strategy: Multiple depth-1 crawls for precise targeting
# Each crawl creates a SEPARATE knowledge base source with its own source_id
# The source_display_name is automatically extracted from the URL
#
# Example: Crawling these URLs creates 3 separate knowledge bases:
#   - https://docs.example.com/api      "Example Api"
#   - https://docs.example.com/guides   "Example Guides"
#   - https://docs.example.com/cli      "Example Cli"
#
CRAWL_TARGETS = [
    {
        "url": "{url_1}",
        "max_depth": 1,  # Depth 1: crawls only this specific page
        "tags": ["{section_tag}", "{site_tag}"],  # Tags help filter in RAG queries
        "knowledge_type": "technical",
        "description": "{description_1}"  # Human-readable description for progress
    },
    {
        "url": "{url_2}",
        "max_depth": 1,  # Depth 1: crawls only this specific page
        "tags": ["{section_tag}", "{site_tag}"],
        "knowledge_type": "technical",
        "description": "{description_2}"
    },
    # Add more specific pages as needed
    # NOTE: Use depth > 1 only if you're certain the page has no
    # navigation links pointing back to parent/sibling pages
]

# IMPORTANT: Each URL above will create a SEPARATE knowledge base entry
# You'll see them as distinct sources in Archon's UI after crawling
# Use tags to group related sources for easier searching

def start_crawl(target: Dict) -> str:
    """Start a crawl and return progress_id"""
    print(f"\\n{'='*60}")
    print(f"Starting crawl: {target['description']}")
    print(f"URL: {target['url']}")
    print(f"Depth: {target['max_depth']}")
    print(f"{'='*60}\\n")

    response = requests.post(
        f"{ARCHON_URL}/api/knowledge-items/crawl",
        json={
            "url": target["url"],
            "knowledge_type": target["knowledge_type"],
            "tags": target["tags"],
            "max_depth": target["max_depth"],
            "extract_code_examples": True,
            "strict_domain": True
        }
    )
    response.raise_for_status()
    data = response.json()
    return data['progressId']

def poll_progress(progress_id: str) -> Dict:
    """Poll crawl progress until complete"""
    print("Monitoring progress...")

    while True:
        try:
            response = requests.get(
                f"{ARCHON_URL}/api/crawl-progress/{progress_id}"
            )

            if response.status_code == 404:
                time.sleep(POLL_INTERVAL)
                continue

            response.raise_for_status()
            data = response.json()

            status = data.get('status', 'unknown')
            progress = data.get('progress', 0)
            log = data.get('log', '')

            print(f"[{progress:3d}%] {status:15s} | {log}")

            if status in ['completed', 'error', 'cancelled']:
                return data

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\\n\\nCrawl interrupted by user!")
            response = requests.post(
                f"{ARCHON_URL}/api/knowledge-items/stop/{progress_id}"
            )
            print("Crawl stopped.")
            return {"status": "cancelled"}

def main():
    """Execute all crawls sequentially"""
    results = []

    print(f"\\n{'#'*60}")
    print(f"# Archon Documentation Crawl")
    print(f"# Target: {CRAWL_TARGETS[0]['url'].split('/')[2]}")
    print(f"# Sections: {len(CRAWL_TARGETS)}")
    print(f"{'#'*60}\\n")

    for i, target in enumerate(CRAWL_TARGETS, 1):
        print(f"\\nCrawl {i}/{len(CRAWL_TARGETS)}")

        try:
            progress_id = start_crawl(target)
            result = poll_progress(progress_id)

            results.append({
                "target": target,
                "result": result,
                "success": result.get('status') == 'completed'
            })

            if result.get('status') == 'completed':
                print(f"\\n SUCCESS")
                print(f"  Chunks stored: {result.get('chunksStored', 'N/A')}")
                print(f"  Code examples: {result.get('codeExamplesFound', 'N/A')}")
                print(f"  Source ID: {result.get('sourceId', 'N/A')}")
            else:
                print(f"\\n FAILED: {result.get('status')}")

        except Exception as e:
            print(f"\\n ERROR: {str(e)}")
            results.append({
                "target": target,
                "error": str(e),
                "success": False
            })

    # Summary
    print(f"\\n{'='*60}")
    print("CRAWL SUMMARY")
    print(f"{'='*60}")
    successful = sum(1 for r in results if r.get('success'))
    print(f"Total crawls: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    # Save results
    with open('crawl_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\\nDetailed results saved to: crawl_results.json")

if __name__ == "__main__":
    main()
```

#### Bash Script Template (CORRECT ARCHON API):

```bash
#!/bin/bash

# {Site Name} Documentation Crawl Script
# Crawls {description of what this covers}
# Generated: {current_date}

set -e  # Exit on error

# Colors for output
GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m' # No Color

# Configuration
ARCHON_API_BASE="${ARCHON_API_BASE:-http://localhost:8181}"
CRAWL_API="${ARCHON_API_BASE}/api/knowledge-items/crawl"

echo -e "${BLUE}======================================"
echo "{Site Name} Documentation Crawl"
echo -e "======================================${NC}\\n"

# Function to start a crawl
start_crawl() {
    local name="$1"
    local url="$2"
    local depth="$3"
    local tags="$4"
    local description="$5"

    echo -e "${YELLOW}Starting crawl: ${name}${NC}"
    echo "  URL: ${url}"
    echo "  Depth: ${depth}"
    echo "  Tags: ${tags}"
    echo ""

    response=$(curl -s -X POST "${CRAWL_API}" \\
        -H "Content-Type: application/json" \\
        -d "{
            \\"url\\": \\"${url}\\",
            \\"max_depth\\": ${depth},
            \\"knowledge_type\\": \\"technical\\",
            \\"tags\\": ${tags},
            \\"extract_code_examples\\": true,
            \\"update_frequency\\": 7
        }")

    if echo "$response" | grep -q '"progressId"'; then
        progress_id=$(echo "$response" | grep -o '"progressId":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo -e "${GREEN} Crawl started successfully${NC}"
        echo "  Progress ID: ${progress_id}"
        echo ""
        return 0
    else
        echo -e "${RED} Failed to start crawl${NC}"
        echo "  Response: ${response}"
        echo ""
        return 1
    fi
}

# Crawl 1: {Section Name}
# Captures: {description of content}
start_crawl \\
    "{Display Name 1}" \\
    "{url_1}" \\
    {depth_1} \\
    '["{tag1}", "{tag2}", "{tag3}"]' \\
    "{Human readable description 1}"

# Wait between crawls to avoid rate limiting
echo "Waiting 3 seconds before next crawl..."
sleep 3

# Crawl 2: {Section Name}
# Captures: {description of content}
start_crawl \\
    "{Display Name 2}" \\
    "{url_2}" \\
    {depth_2} \\
    '["{tag1}", "{tag2}"]' \\
    "{Human readable description 2}"

# Add more crawls as needed...

echo -e "${BLUE}======================================"
echo "Crawl jobs submitted!"
echo -e "======================================${NC}\\n"
echo "Monitor progress at: ${ARCHON_API_BASE}/knowledge"
echo ""
echo "Expected totals:"
echo "  - {Section 1}: ~{count} pages"
echo "  - {Section 2}: ~{count} pages"
echo "  - Total: ~{total} pages"
echo ""
```

**CRITICAL IMPLEMENTATION NOTES:**

1. **Correct API Endpoint:** `/api/knowledge-items/crawl` (NOT `/api/knowledge/crawl`)

2. **Required Request Fields:**
   - `url` (string) - The URL to crawl
   - `max_depth` (int) - Crawl depth (1-5)
   - `knowledge_type` (string) - Usually "technical"
   - `tags` (array) - List of tag strings
   - `extract_code_examples` (bool) - Usually true
   - `strict_domain` (bool) - Defaults to true
   - `update_frequency` (int) - Days between updates, usually 7

3. **Response Format:**
   - Success: `{"success": true, "progressId": "uuid", "message": "...", "estimatedDuration": "..."}`
   - Field name is `progressId` (camelCase), NOT `progress_id`

4. **Line Endings:**
   - Scripts must use Unix line endings (LF)
   - Use `dos2unix` or `sed -i 's/\r$//'` if needed
   - Write tool automatically handles this on Linux systems

5. **File Location:**
   - Save to: `scripts/archon-kb-crawls/{site-name}-docs-crawl.sh`
   - Use kebab-case for filename
   - Make executable with `chmod +x`

### PHASE 6: Create Script File & Output Presentation

**IMPORTANT:** Use the Write tool to create the actual script files in the correct location:

1. **Create the script files:**
   ```
   If llms-full.txt was found:
     Main script: scripts/archon-kb-crawls/{site-name}-docs-crawl.py
     Cleanup script: scripts/archon-kb-crawls/cleanup-{site-name}-kb.py

   If traditional crawling was used:
     Main script: scripts/archon-kb-crawls/{site-name}-docs-crawl.py
     (No cleanup script needed - each URL creates separate source)

   Use kebab-case for {site-name}
   All scripts are Python (not bash) for better cross-platform compatibility
   ```

2. **Script naming conventions:**
   - `{site-name}-docs-crawl.py` - Main crawl script using Archon API
   - `cleanup-{site-name}-kb.py` - Cleanup script for deleting existing sources

3. **Template variable replacements:**
   - `{site_name}` - Human readable name (e.g., "CrewAI")
   - `{llms_full_url}` - Full URL to llms-full.txt
   - `{tags_list}` - Python list literal (e.g., `["crewai", "ai-agents", "documentation"]`)
   - `{current_date}` - Today's date (YYYY-MM-DD)
   - `{site_prefix}` - Prefix for title matching (e.g., "crewai")
   - `{site_prefix_lower}` - Lowercase version for case-insensitive matching
   - `{domain}` - Domain for URL matching (e.g., "crewai.com")

Then present the generated script with:


**If using llms-full.txt or llms-ctx.txt (simplified output):**
```
OPTIMAL SOURCE FOUND: {llms_file_name}

Site: {domain}
Source: {llms_file_url}
Format: Single curated file (Archon handles parsing automatically)

Why llms-full.txt is better:
  - Single HTTP request instead of crawling many pages
  - Archon automatically parses H1 sections into separate "pages"
  - Code examples are extracted and indexed
  - Fast (seconds instead of minutes)
  - Creates ONE KB source with all content organized

Generated scripts:
  scripts/archon-kb-crawls/{site-name}-docs-crawl.py     # Main crawl script
  scripts/archon-kb-crawls/cleanup-{site-name}-kb.py    # Cleanup script (optional)

Usage:
  # First time - just run the crawl
  python scripts/archon-kb-crawls/{site-name}-docs-crawl.py

  # Re-crawling - delete old sources first
  python scripts/archon-kb-crawls/cleanup-{site-name}-kb.py
  python scripts/archon-kb-crawls/{site-name}-docs-crawl.py
```

**If using llms.txt (index file):**
```
Found: {llms_index_url}
NO llms-full.txt or llms-ctx.txt available

The llms.txt file contains curated links to documentation files.
You can parse it to get URLs, then use Archon's crawl API for each.

Note: This is less optimal than llms-full.txt. Consider asking the
site maintainers to add llms-full.txt support.
```

**If using standard crawling (original output):**

1. **Summary of Analysis:**
   ```
   Site: {domain}
   Documentation Sections Found: {count}
   Non-Documentation Pages Excluded: {count} (automatically filtered)
   Estimated Total Pages: ~{estimate}
   Knowledge Base Sources: {count} (one per URL crawled)
   Strict Domain Filtering: enabled (default)
   ```

2. **Knowledge Base Structure:**
   ```
   This script will create {count} separate knowledge base sources:

   1. {source_display_name_1} (from {url_1})
      - Tags: {tags}
      - Estimated pages: {count}

   2. {source_display_name_2} (from {url_2})
      - Tags: {tags}
      - Estimated pages: {count}

   Each source appears as a separate entry in Archon's UI.
   Use tags to search across multiple sources.
   ```

3. **Crawl Plan:**
   ```
   | Source Name | URL | Depth | Est. Pages | Tags |
   |-------------|-----|-------|------------|------|
   | ...         | ... | ...   | ...        | ...  |
   ```

4. **Generated Script:**
   -  Already saved to: `scripts/archon-kb-crawls/{site-name}-docs-crawl.sh`
   -  Made executable and line endings fixed
   - Show file location and brief content summary

5. **Usage Instructions:**
   ```
   To run this script:

   1. Ensure Archon is running on http://localhost:8181
      (or set ARCHON_API_BASE environment variable)

   2. Run the script:
      ./scripts/archon-kb-crawls/{site-name}-docs-crawl.sh

      Or with custom Archon URL:
      ARCHON_API_BASE=http://localhost:8080 ./scripts/archon-kb-crawls/{site-name}-docs-crawl.sh

   3. Monitor progress in terminal
      - Shows progress ID for each crawl
      - Sequential execution with 3-second delays

   4. Check Archon UI for results:
      http://localhost:8181/knowledge

   After crawling, you'll see {count} separate sources in Archon's UI.

   To search the crawled content, use Archon MCP tools:
   - rag_get_available_sources() - List all sources with their IDs
   - rag_search_knowledge_base(query="...", source_id=None) - Search all sources
   - rag_search_knowledge_base(query="...", source_id="src_abc123") - Search specific source
   ```

6. **Searching Your Crawled Content:**
   ```python
   # Example: Search across all Packer documentation
   from archon_mcp_tools import rag_search_knowledge_base

   # Search all sources (no source_id specified)
   results = rag_search_knowledge_base(
       query="hyperv configuration",
       match_count=10
   )

   # Or search a specific source
   results = rag_search_knowledge_base(
       query="iso builder options",
       source_id="src_abc123",  # From rag_get_available_sources()
       match_count=5
   )
   ```

## Important Notes

- **Check for llms-full.txt, llms.txt, llms-ctx.txt FIRST:** This is the absolute best option when available
- **Use HEAD checks** to verify existence and estimate size before fetching
- **Prefer llms-full.txt, then llms.txt, then llms-ctx.txt** when present
- **Prefer depth-1 strategy:** Multiple targeted crawls beat one recursive crawl
- **Strict domain filtering is enabled by default** to prevent subdomain expansion
- **Respect crawl limits:** Archon limits to 3 concurrent crawl operations
- **Sequential crawls:** Generated script runs crawls one at a time
- **Progress monitoring:** Script polls every 2 seconds
- **Cancellation support:** Ctrl+C will stop current crawl
- **Results saved:** JSON output includes all crawl results
- **Source IDs:** Captured for later RAG queries

## Example: Strategy Hierarchy

**Scenario:** User wants to crawl documentation for a framework

### BEST - Use llms-full.txt with Archon API:
```python
# Point Archon directly at the llms-full.txt file
# Archon automatically parses H1 sections into separate "pages"
import httpx

payload = {
    "url": "https://docs.example.com/llms-full.txt",
    "max_depth": 1,
    "knowledge_type": "technical",
    "tags": ["example", "documentation"],
    "extract_code_examples": True,
    "strict_domain": True,
}

response = httpx.post(
    "http://localhost:8181/api/knowledge-items/crawl",
    json=payload,
    timeout=60,
)
progress_id = response.json()["progressId"]
# Poll /api/crawl-progress/{progress_id} until completed
```

### GOOD - Use llms.txt (curated URL list):
```python
# Parse llms.txt for URLs, then crawl each with Archon
# Less optimal than llms-full.txt but still curated content
```
###  OK - Multiple Depth-1 Crawls (when no llms files exist):
```python
# Precise targeting - crawls only what you specify
CRAWL_TARGETS = [
    {
        "url": "https://docs.example.com/getting-started",
        "max_depth": 1,
        "tags": ["example-framework", "getting-started"],
        "description": "Getting Started Guide"
    },
    {
        "url": "https://docs.example.com/api-reference",
        "max_depth": 1,
        "tags": ["example-framework", "api"],
        "description": "API Reference"
    },
]
```

###  RISKY - Recursive Crawl (use strict domain filtering!):
```python
# Will follow ALL internal links - use with caution
# Strict domain filtering is enabled by default to prevent subdomain expansion
CRAWL_TARGETS = [
    {
        "url": "https://docs.example.com/guides",
        "max_depth": 2,  # RISKY: May crawl unexpected pages
        "tags": ["example-framework"],
    }
]
# Risk: May crawl www.example.com, blog.example.com, etc.
# Mitigation: Archon now has strict domain filtering enabled by default
```

###  WRONG - Deep Recursive without domain filtering:
```python
# DON'T DO THIS - will crawl entire internet
CRAWL_TARGETS = [
    {
        "url": "https://docs.example.com",
        "max_depth": 5,  # VERY BAD: Will follow nav links everywhere
        "tags": ["example"],
    }
]
# Result: Thousands of pages, most not documentation
```

## Error Handling

- WebFetch failures  Suggest manual URL inspection
- Ambiguous structure  Ask more clarifying questions
- Missing sections  Note in generated script comments
- Rate limiting detected  Add delays in script

## BEGIN EXECUTION

Start by analyzing: {{url}}
