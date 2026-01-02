#!/usr/bin/env python3
"""
Re-crawl Hashicorp Packer documentation with proper filters.

This script:
1. Deletes the existing bloated Packer source (~878K words)
2. Re-crawls only current docs, excluding:
   - Version archives (v1.5.x through v1.13.x) - each is a full copy
   - HCP Packer docs (different product)
   - External domains
   - Non-essential pages (partnerships, community-tools, tutorials)

Note: The 3 small Packer HyperV sources (9K, 8K, 332 words) are NOT deleted.

Usage:
    python scripts/recrawl_packer.py [--dry-run]
    python scripts/recrawl_packer.py --delete-only
    python scripts/recrawl_packer.py --crawl-only
"""

import argparse
import time

import requests

# Configuration
ARCHON_API_URL = "http://localhost:8181/api"
CRAWL_ENDPOINT = f"{ARCHON_API_URL}/knowledge-items/crawl"
PROGRESS_ENDPOINT = f"{ARCHON_API_URL}/crawl-progress"
DELETE_ENDPOINT = f"{ARCHON_API_URL}/knowledge-items"

# Existing Packer source to delete (bloated with version archives)
# Note: NOT deleting the 3 small HyperV sources which are fine:
#   - 293b6694a7ee490e: Packer-HyperV-ISO (9K words)
#   - 606ecfee282cb02f: Packer-HyperV-Main (332 words)
#   - b22ced473f4d8f2a: Packer-VMCX (8K words)
SOURCES_TO_DELETE = [
    {"id": "ee0700ccde9671c7", "name": "Hashicorp-Packer (main docs)", "words": "878K"},
]

# Packer crawl configuration
CRAWL_CONFIG = {
    "url": "https://developer.hashicorp.com/packer/docs",
    "knowledge_type": "technical",
    "tags": ["packer", "hashicorp", "image-builder", "ami", "vmware", "virtualbox"],
    "update_frequency": 14,
    "max_depth": 3,
    "extract_code_examples": True,
    "strict_domain": True,

    # Exclude patterns (regex)
    "exclude_url_patterns": [
        # VERSION ARCHIVES - Critical exclusion (each is a full copy of docs)
        # Matches: /docs/v1.5.x/, /docs/v1.13.x/, etc.
        r"/docs/v\d+\.\d+\.x",
        r"/v\d+\.\d+\.x/",

        # HCP PACKER - Different product (HashiCorp Cloud Platform)
        r"/hcp/",
        r"/hcp$",

        # Tutorials (verbose, learning-focused content)
        r"/tutorials/",
        r"/tutorials$",

        # Non-essential sections
        r"/partnerships",
        r"/community-tools",
        r"/sandbox",
        r"/faq$",
        r"/install$",

        # Release/changelog content
        r"/release-notes",
        r"/changelog",

        # Enterprise-specific
        r"/enterprise$",

        # External integrations pages (keep /integrations but skip deep dives)
        # We want the overview but not every cloud provider's full docs
        r"/integrations/hashicorp/[^/]+/latest/components/",

        # Generic non-doc paths
        r"/blog/",
        r"/legal/",
        r"/pricing",
        r"/support/",
        r"/community/",
        r"/events/",
        r"/careers/",
        r"/about/",
    ],

    # HTML tags to exclude from content extraction
    "excluded_tags": [
        "nav",
        "footer",
        "advertisement",
        "sidebar",
    ],
}


def delete_sources(sources: list[dict], dry_run: bool = False) -> bool:
    """Delete the specified knowledge sources."""
    print(f"\n{'='*60}")
    print("Deleting Existing Packer Source")
    print(f"{'='*60}")

    print(f"\nSource to delete:")
    for source in sources:
        print(f"  - {source['name']}: {source['words']} words (ID: {source['id']})")

    print(f"\nKeeping small HyperV sources (not deleting):")
    print(f"  - Packer-HyperV-ISO: 9K words")
    print(f"  - Packer-HyperV-Main: 332 words")
    print(f"  - Packer-VMCX: 8K words")

    if dry_run:
        print("\n[DRY RUN] Would delete the above source")
        return True

    print("\nDeleting source...")
    all_success = True

    for source in sources:
        try:
            response = requests.delete(
                f"{DELETE_ENDPOINT}/{source['id']}",
                timeout=30
            )

            if response.status_code in (200, 204):
                print(f"  ✓ Deleted: {source['name']}")
            elif response.status_code == 404:
                print(f"  ⚠ Not found (already deleted?): {source['name']}")
            else:
                print(f"  ✗ Failed to delete {source['name']}: {response.status_code}")
                all_success = False

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error deleting {source['name']}: {e}")
            all_success = False

    return all_success


def start_crawl(config: dict, dry_run: bool = False) -> str | None:
    """Start a crawl with the given configuration."""
    print(f"\n{'='*60}")
    print("Hashicorp Packer Documentation Re-crawl")
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
                    print(f"\nExpected reduction: ~878K words → ~100-150K words")
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
        description="Re-crawl Hashicorp Packer documentation with filters"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show configuration without making changes"
    )
    parser.add_argument(
        "--delete-only",
        action="store_true",
        help="Only delete existing source, don't crawl"
    )
    parser.add_argument(
        "--crawl-only",
        action="store_true",
        help="Only crawl, don't delete existing source"
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

    # Step 1: Delete existing source (unless --crawl-only)
    if not args.crawl_only:
        delete_success = delete_sources(SOURCES_TO_DELETE, dry_run=args.dry_run)
        if not delete_success and not args.dry_run:
            print("\nWarning: Source failed to delete. Continuing anyway...")

    # Step 2: Start new crawl (unless --delete-only)
    if not args.delete_only:
        progress_id = start_crawl(CRAWL_CONFIG, dry_run=args.dry_run)

        if progress_id and not args.no_monitor:
            monitor_progress(progress_id, poll_interval=args.poll_interval)
        elif progress_id:
            print(f"\nCrawl started. Monitor with:")
            print(f"  curl {PROGRESS_ENDPOINT}/{progress_id}")

    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    if args.dry_run:
        print("This was a dry run. No changes were made.")
        print("\nTo execute for real, run without --dry-run:")
        print("  python scripts/recrawl_packer.py")
    else:
        print("Packer knowledge base cleanup complete!")
        print("Bloated source deleted, filtered re-crawl initiated.")
        print("\nNote: HyperV sources (17K words total) were preserved.")


if __name__ == "__main__":
    main()
