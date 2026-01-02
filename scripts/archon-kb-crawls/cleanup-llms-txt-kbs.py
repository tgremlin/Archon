#!/usr/bin/env python3
"""
Cleanup Script for KB Re-crawl with llms.txt
Updated: 2026-01-01

Deletes existing KB sources that will be re-crawled using llms.txt files.
Run this BEFORE running the individual crawl scripts.

Sources to delete:
- Pydantic AI (473e7956a86382e6) -> Will re-crawl from llms-full.txt
- Temporal (4b6d4df01eaaa81c) -> Will re-crawl from llms-full.txt
- Langfuse (959af590c689deac) -> Will re-crawl from llms.txt
- Redis (c96cbb09b23070da) -> Will re-crawl from llms.txt
- Astral UV (a24165001d3bbc04) -> Will re-crawl from llms.txt
"""

import os
import sys

import httpx

# =============================================================================
# Configuration
# =============================================================================

ARCHON_URL = os.environ.get("ARCHON_URL", "http://localhost:8181")
REQUEST_TIMEOUT = 30  # seconds for API requests

# Sources to delete (source_id, name, new_llms_url)
SOURCES_TO_DELETE = [
    ("473e7956a86382e6", "Pydantic AI", "https://ai.pydantic.dev/llms-full.txt"),
    ("4b6d4df01eaaa81c", "Temporal", "https://docs.temporal.io/llms-full.txt"),
    ("959af590c689deac", "Langfuse", "https://langfuse.com/llms.txt"),
    ("c96cbb09b23070da", "Redis", "https://redis.io/llms.txt"),
    ("a24165001d3bbc04", "Astral UV", "https://docs.astral.sh/uv/llms.txt"),
]


def check_archon_health() -> bool:
    """Check if Archon is available."""
    try:
        response = httpx.get(f"{ARCHON_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error connecting to Archon: {e}")
        return False


def delete_source(source_id: str, name: str) -> bool:
    """Delete a knowledge source."""
    try:
        print(f"  Deleting {name} ({source_id})...", end=" ")
        response = httpx.delete(
            f"{ARCHON_URL}/api/knowledge-items/{source_id}",
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            print("OK")
            return True
        elif response.status_code == 404:
            print("NOT FOUND (already deleted?)")
            return True  # Consider success if not found
        else:
            print(f"FAILED ({response.status_code})")
            print(f"    Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main() -> int:
    """Main entry point."""
    print(f"\n{'#'*60}")
    print("# KB Cleanup Script for llms.txt Re-crawl")
    print(f"# Archon: {ARCHON_URL}")
    print(f"{'#'*60}\n")

    # Check Archon availability
    if not check_archon_health():
        print(f"Error: Cannot connect to Archon at {ARCHON_URL}")
        print("\nMake sure Archon is running and try again.")
        return 1

    print("Archon is healthy.\n")

    # Show what will be deleted
    print("The following KB sources will be DELETED:\n")
    print(f"{'Source ID':<20} {'Name':<15} {'New URL'}")
    print("-" * 80)
    for source_id, name, new_url in SOURCES_TO_DELETE:
        print(f"{source_id:<20} {name:<15} {new_url}")
    print()

    # Confirm before deleting
    print("WARNING: This action cannot be undone!")
    print("After deletion, run the individual crawl scripts to re-populate.\n")

    try:
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("\nCancelled.")
            return 0
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 0

    # Delete sources
    print("\nDeleting sources:\n")
    success_count = 0
    fail_count = 0

    for source_id, name, _ in SOURCES_TO_DELETE:
        if delete_source(source_id, name):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print(f"\n{'='*60}")
    print("CLEANUP SUMMARY")
    print(f"{'='*60}\n")
    print(f"Successfully deleted: {success_count}")
    print(f"Failed:               {fail_count}")

    if fail_count == 0:
        print("\nAll sources deleted successfully!")
        print("\nNext steps - run the crawl scripts:")
        print("  python pydantic-ai-docs-crawl.py")
        print("  python temporal-docs-crawl.py")
        print("  python langfuse-docs-crawl.py")
        print("  python redis-docs-crawl.py")
        print("  python astral-uv-docs-crawl.py")
    else:
        print(f"\n{fail_count} source(s) failed to delete. Check the errors above.")

    print(f"\n{'='*60}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
