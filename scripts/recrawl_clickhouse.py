#!/usr/bin/env python3
"""
Re-crawl ClickHouse documentation with proper filters.

This script crawls only the English documentation, excluding:
- Foreign language versions (ru, zh, jp)
- Changelog/whats-new (massive files)
- Non-documentation pages (blog, legal, marketing)

Usage:
    python scripts/recrawl_clickhouse.py [--dry-run]
"""

import argparse
import json
import sys
import time

import requests

# Configuration
ARCHON_API_URL = "http://localhost:8181/api"
CRAWL_ENDPOINT = f"{ARCHON_API_URL}/knowledge-items/crawl"
PROGRESS_ENDPOINT = f"{ARCHON_API_URL}/crawl-progress"

# ClickHouse crawl configuration
CRAWL_CONFIG = {
    "url": "https://clickhouse.com/docs",
    "knowledge_type": "technical",
    "tags": ["clickhouse", "database", "analytics", "sql"],
    "update_frequency": 7,
    "max_depth": 3,  # Reasonable depth for docs
    "extract_code_examples": True,
    "strict_domain": True,  # Stay on clickhouse.com only

    # Exclude patterns (regex)
    "exclude_url_patterns": [
        # Foreign language documentation
        r"/docs/ru/",
        r"/docs/zh/",
        r"/docs/jp/",
        r"/docs/en/",  # Redundant English prefix pages

        # Changelog and release notes (massive, not useful for RAG)
        r"/docs/whats-new",
        r"/changelog",
        r"/releases",

        # Non-documentation paths
        r"/blog/",
        r"/legal/",
        r"/comparison/",
        r"/use-cases/",
        r"/pricing",
        r"/videos",
        r"/user-stories",
        r"/company/",
        r"/support/",
        r"/cloud/",
        r"/demos/",
        r"/learn/",
        r"/slack",
        r"/openhouse",

        # External domains that might be linked
        r"trust\.clickhouse\.com",
        r"clickgems\.clickhouse\.com",
    ],

    # HTML tags to exclude from content extraction
    "excluded_tags": [
        "nav",
        "footer",
        "advertisement",
        "sidebar",
    ],
}


def start_crawl(config: dict, dry_run: bool = False) -> str | None:
    """Start a crawl with the given configuration."""
    print(f"\n{'='*60}")
    print("ClickHouse Documentation Re-crawl")
    print(f"{'='*60}")
    print(f"\nTarget URL: {config['url']}")
    print(f"Max Depth: {config['max_depth']}")
    print(f"Tags: {', '.join(config['tags'])}")
    print(f"\nExclude patterns ({len(config['exclude_url_patterns'])}):")
    for pattern in config['exclude_url_patterns'][:10]:
        print(f"  - {pattern}")
    if len(config['exclude_url_patterns']) > 10:
        print(f"  ... and {len(config['exclude_url_patterns']) - 10} more")

    if dry_run:
        print("\n[DRY RUN] Would send crawl request with above configuration")
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
            log_msg = data.get("log", "")
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
                elif status == "failed" or status == "error":
                    error = data.get("error", log_msg)
                    print(f"\nCrawl failed: {error}")
                elif status == "cancelled":
                    print(f"\nCrawl was cancelled")
                break

        except requests.exceptions.RequestException as e:
            print(f"Error checking progress: {e}")

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="Re-crawl ClickHouse documentation with filters"
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
