#!/usr/bin/env python3
"""
CrewAI Knowledge Base Cleanup Script for Archon
Generated: 2026-01-01

Deletes all Archon knowledge sources related to CrewAI:
- Title starting with "crewai" (case-insensitive)
- URL containing "crewai.com"

Useful for cleaning up before re-crawling with a new approach.
"""

import os
import sys

import httpx

# =============================================================================
# Configuration
# =============================================================================

ARCHON_URL = os.environ.get("ARCHON_URL", "http://localhost:8181")
REQUEST_TIMEOUT = 30  # seconds


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
    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching sources: {e.response.status_code}")
        print(f"Response: {e.response.text[:500]}")
        return []
    except Exception as e:
        print(f"Error fetching sources: {e}")
        return []


def filter_crewai_sources(sources: list[dict]) -> list[dict]:
    """Filter sources related to CrewAI (case-insensitive check on title/url)."""
    crewai_sources = []
    for source in sources:
        # Check title field (primary identifier)
        title = source.get("title") or ""
        # Check URL as fallback
        url = source.get("url") or ""

        # Case-insensitive match on "crewai"
        if title.lower().startswith("crewai") or "crewai.com" in url.lower():
            crewai_sources.append(source)
    return crewai_sources


def delete_source(source_id: str, display_name: str) -> bool:
    """Delete a single knowledge source."""
    try:
        response = httpx.delete(
            f"{ARCHON_URL}/api/knowledge-items/{source_id}",
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code in (200, 204):
            print(f"  [OK] Deleted: {display_name}")
            return True
        else:
            print(f"  [FAIL] {display_name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] {display_name}: {e}")
        return False


def main() -> int:
    """Main entry point."""
    print(f"\n{'='*60}")
    print("CrewAI Knowledge Base Cleanup")
    print(f"Archon URL: {ARCHON_URL}")
    print(f"{'='*60}\n")

    # Check Archon availability
    try:
        response = httpx.get(f"{ARCHON_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"Warning: Archon health check returned {response.status_code}")
    except Exception as e:
        print(f"Error: Cannot connect to Archon at {ARCHON_URL}")
        print(f"       {e}")
        print("\nMake sure Archon is running and try again.")
        return 1

    # Fetch all sources
    print("Fetching knowledge sources...")
    sources = get_knowledge_sources()

    if not sources:
        print("No knowledge sources found.")
        return 0

    print(f"Found {len(sources)} total sources.")

    # Filter CrewAI sources
    crewai_sources = filter_crewai_sources(sources)

    if not crewai_sources:
        print("\nNo CrewAI sources found (title starting with 'crewai' or URL containing 'crewai.com').")
        return 0

    # Preview sources to delete
    print(f"\nFound {len(crewai_sources)} CrewAI sources to delete:\n")
    print(f"{'ID':<40} {'Title':<40} {'URL'}")
    print("-" * 120)

    for source in crewai_sources:
        source_id = source.get("source_id") or source.get("id") or "?"
        title = source.get("title") or "?"
        url = source.get("url") or "?"
        # Truncate long values
        title_short = title[:38] + ".." if len(title) > 40 else title
        url_short = url[:38] + ".." if len(url) > 40 else url
        print(f"{source_id:<40} {title_short:<40} {url_short}")

    print("-" * 120)
    print(f"Total: {len(crewai_sources)} sources\n")

    # Confirm before deleting
    try:
        confirm = input("Delete these sources? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            return 0
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 0

    # Delete sources
    print("\nDeleting sources...")
    success_count = 0
    fail_count = 0

    for source in crewai_sources:
        source_id = source.get("source_id") or source.get("id")
        title = source.get("title") or source_id

        if not source_id:
            print(f"  [SKIP] Missing source_id for: {title}")
            fail_count += 1
            continue

        if delete_source(source_id, title):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Deleted: {success_count}/{len(crewai_sources)}")
    if fail_count > 0:
        print(f"Failed: {fail_count}")
    print(f"{'='*60}\n")

    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
