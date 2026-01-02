#!/usr/bin/env python3
"""
Temporal Documentation Crawl Script for Archon
Updated: 2026-01-01

Uses llms-full.txt for efficient ingestion:
- Single HTTP request to fetch complete documentation
- Archon automatically parses H1 sections into separate "pages"
- Creates one KB source with all content properly organized
"""

import os
import sys
import time

import httpx

# =============================================================================
# Configuration
# =============================================================================

ARCHON_URL = os.environ.get("ARCHON_URL", "http://localhost:8181")
LLMS_FULL_URL = "https://docs.temporal.io/llms-full.txt"

POLL_INTERVAL = 3  # seconds between progress checks
REQUEST_TIMEOUT = 60  # seconds for API requests

# Tags for the knowledge source
TAGS = ["temporal", "workflows", "orchestration", "documentation"]


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
                # Progress not yet available
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

            # Print progress update (overwrite line)
            elapsed = int(time.time() - start_time)
            pages_info = f"[{processed_pages}/{total_pages}]" if total_pages > 0 else ""
            print(
                f"\r  [{progress_int:3d}%] {status:12s} {pages_info:10s} | {log_msg[:50]:<50} ({elapsed}s)",
                end="",
            )

            if status in ["completed", "error", "cancelled", "failed"]:
                print()  # New line after completion
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
        print("\nThe Temporal documentation is now available in Archon!")
        print("You can search it using:")
        print(f'  rag_search_knowledge_base(query="your query", source_id="{source_id}")')
    elif status == "error":
        error_msg = result.get("error") or result.get("log", "Unknown error")
        print(f"\nError: {error_msg}")

    print(f"\n{'='*60}")


def main() -> int:
    """Main entry point."""
    print(f"\n{'#'*60}")
    print("# Temporal Documentation Crawl for Archon")
    print("# Using llms-full.txt for efficient ingestion")
    print(f"# Target: {LLMS_FULL_URL}")
    print(f"# Archon: {ARCHON_URL}")
    print(f"{'#'*60}\n")

    # Check Archon availability
    if not check_archon_health():
        print(f"Error: Cannot connect to Archon at {ARCHON_URL}")
        print("\nMake sure Archon is running and try again.")
        return 1

    print("Archon is healthy.\n")

    # Confirm before starting
    print("This will crawl the Temporal llms-full.txt file and create a single")
    print("knowledge source with all documentation sections.")
    print(f"Tags: {', '.join(TAGS)}\n")

    try:
        input("Press Enter to start (Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 0

    # Start the crawl
    progress_id = start_crawl()
    if not progress_id:
        print("Failed to start crawl.")
        return 1

    # Poll for progress
    try:
        result = poll_progress(progress_id)
    except KeyboardInterrupt:
        print("\n\nCrawl interrupted by user!")
        return 1

    # Print summary
    print_summary(result)

    return 0 if result.get("status") == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
