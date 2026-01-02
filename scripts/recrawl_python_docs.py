#!/usr/bin/env python3
"""
Re-crawl Python documentation with proper filters.

This script crawls only the high-value reference sections:
- /library/ - Standard library reference (core value)
- /reference/ - Language syntax reference

Excludes:
- Tutorials and HOWTOs (verbose learning content)
- C API and extending docs (niche)
- Setup/packaging guides
- Release notes and meta pages

Usage:
    python scripts/recrawl_python_docs.py [--dry-run]
"""

import argparse
import time

import requests

# Configuration
ARCHON_API_URL = "http://localhost:8181/api"
CRAWL_ENDPOINT = f"{ARCHON_API_URL}/knowledge-items/crawl"
PROGRESS_ENDPOINT = f"{ARCHON_API_URL}/crawl-progress"

# Python docs crawl configuration
CRAWL_CONFIG = {
    "url": "https://docs.python.org/3/",
    "knowledge_type": "technical",
    "tags": ["python", "stdlib", "reference", "programming"],
    "update_frequency": 30,  # Python docs don't change frequently
    "max_depth": 4,  # Library has nested module docs
    "extract_code_examples": True,
    "strict_domain": True,

    # Exclude patterns (regex)
    "exclude_url_patterns": [
        # Verbose learning content (not reference)
        r"/tutorial/",
        r"/tutorial$",
        r"/howto/",
        r"/howto$",

        # C/C++ focused sections (niche audience)
        r"/c-api/",
        r"/c-api$",
        r"/extending/",
        r"/extending$",

        # Setup and packaging (not code reference)
        r"/using/",
        r"/using$",
        r"/installing/",
        r"/installing$",
        r"/distributing/",
        r"/distributing$",

        # Release and meta content
        r"/whatsnew/",
        r"/whatsnew$",
        r"/deprecations/",
        r"/deprecations$",
        r"/faq/",
        r"/faq$",

        # Static/meta pages
        r"/download\.html",
        r"/bugs\.html",
        r"/license\.html",
        r"/about\.html",
        r"/copyright\.html",
        r"/genindex\.html",
        r"/search\.html",
        r"/contents\.html",

        # Old Python versions (prevent version sprawl)
        r"docs\.python\.org/2",
        r"docs\.python\.org/3\.\d+/",

        # External links
        r"github\.com",
        r"pypi\.org",
        r"wiki\.python\.org",
    ],

    # HTML tags to exclude from content extraction
    "excluded_tags": [
        "nav",
        "footer",
        "sidebar",
    ],
}


def start_crawl(config: dict, dry_run: bool = False) -> str | None:
    """Start a crawl with the given configuration."""
    print(f"\n{'='*60}")
    print("Python Documentation Re-crawl")
    print(f"{'='*60}")
    print(f"\nTarget URL: {config['url']}")
    print(f"Max Depth: {config['max_depth']}")
    print(f"Tags: {', '.join(config['tags'])}")
    print(f"\nExclude patterns ({len(config['exclude_url_patterns'])}):")
    for pattern in config['exclude_url_patterns'][:12]:
        print(f"  - {pattern}")
    if len(config['exclude_url_patterns']) > 12:
        print(f"  ... and {len(config['exclude_url_patterns']) - 12} more")

    if dry_run:
        print("\n[DRY RUN] Would send crawl request with above configuration")
        print("\nSections to be crawled:")
        print("  + /library/   - Standard library reference")
        print("  + /reference/ - Language syntax reference")
        print("  + /glossary.html - Term definitions")
        return None

    print("\nStarting crawl...")

    try:
        response = requests.post(
            CRAWL_ENDPOINT,
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        progress_id = result.get("progressId")

        if progress_id:
            print(f"Crawl started! Progress ID: {progress_id}")
            return progress_id
        else:
            print(f"Error: No progress ID returned. Response: {result}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error starting crawl: {e}")
        return None


def monitor_progress(progress_id: str, poll_interval: int = 5):
    """Monitor crawl progress until completion."""
    print(f"\nMonitoring progress (polling every {poll_interval}s)...")
    print("-" * 60)

    last_status = None
    last_progress = -1

    while True:
        try:
            response = requests.get(
                f"{PROGRESS_ENDPOINT}/{progress_id}",
                timeout=10
            )

            if response.status_code == 404:
                print("\nProgress tracking ended (404)")
                break

            response.raise_for_status()
            data = response.json()

            status = data.get("status", "unknown")
            progress = data.get("progress", 0)
            total_pages = data.get("totalPages", 0)
            processed_pages = data.get("processedPages", 0)
            current_url = data.get("currentUrl", "")

            # Only print if something changed
            if status != last_status or progress != last_progress:
                # Truncate URL for display
                display_url = current_url[:50] + "..." if len(current_url) > 50 else current_url
                print(f"[{status.upper():12}] {progress:3}% | Pages: {processed_pages}/{total_pages} | {display_url}")
                last_status = status
                last_progress = progress

            # Check for terminal states
            if status in ("completed", "failed", "cancelled", "error"):
                print("-" * 60)
                if status == "completed":
                    source_id = data.get("sourceId", "unknown")
                    print(f"\nCrawl completed successfully!")
                    print(f"Source ID: {source_id}")
                    print(f"Total pages processed: {processed_pages}")
                elif status in ("failed", "error"):
                    error = data.get("error", data.get("log", ""))
                    print(f"\nCrawl failed: {error}")
                elif status == "cancelled":
                    print("\nCrawl was cancelled")
                break

        except requests.exceptions.RequestException as e:
            print(f"Error checking progress: {e}")

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="Re-crawl Python documentation with filters"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show configuration without starting crawl"
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="Start crawl but don't monitor progress"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Progress poll interval in seconds (default: 5)"
    )

    args = parser.parse_args()

    # Start the crawl
    progress_id = start_crawl(CRAWL_CONFIG, dry_run=args.dry_run)

    if progress_id and not args.no_monitor:
        monitor_progress(progress_id, poll_interval=args.poll_interval)
    elif progress_id:
        print(f"\nCrawl started. Monitor with:")
        print(f"  curl {PROGRESS_ENDPOINT}/{progress_id}")


if __name__ == "__main__":
    main()
