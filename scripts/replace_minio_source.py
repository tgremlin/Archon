#!/usr/bin/env python3
"""
Replace bloated MinIO documentation with focused Python SDK README.

This script:
1. Deletes the existing MinIO source (~401K words of enterprise docs)
2. Downloads the minio-py GitHub README (~900 words)
3. Uploads it to Archon as a focused knowledge source

Usage:
    python scripts/replace_minio_source.py [--dry-run]
    python scripts/replace_minio_source.py --delete-only
    python scripts/replace_minio_source.py --upload-only
"""

import argparse
import json
import tempfile
from pathlib import Path

import requests

# Configuration
ARCHON_API_URL = "http://localhost:8181/api"
DELETE_ENDPOINT = f"{ARCHON_API_URL}/knowledge-items"
UPLOAD_ENDPOINT = f"{ARCHON_API_URL}/documents/upload"

# GitHub raw content URL for minio-py README
MINIO_README_URL = "https://raw.githubusercontent.com/minio/minio-py/master/README.md"

# Existing bloated source to delete
SOURCE_TO_DELETE = {
    "id": "a8349e1a7aa3e8c5",
    "name": "Min Documentation (AIStor Enterprise)",
    "words": "401K",
}

# Upload configuration
UPLOAD_CONFIG = {
    "title": "MinIO Python SDK",
    "knowledge_type": "technical",
    "tags": ["minio", "python", "s3", "object-storage", "sdk"],
}


def delete_source(source: dict, dry_run: bool = False) -> bool:
    """Delete the existing bloated MinIO source."""
    print(f"\n{'='*60}")
    print("Deleting Bloated MinIO Source")
    print(f"{'='*60}")
    print(f"\nSource to delete:")
    print(f"  - {source['name']}: {source['words']} words (ID: {source['id']})")

    if dry_run:
        print("\n[DRY RUN] Would delete the above source")
        return True

    print("\nDeleting source...")

    try:
        response = requests.delete(
            f"{DELETE_ENDPOINT}/{source['id']}",
            timeout=30
        )

        if response.status_code in (200, 204):
            print(f"  ✓ Deleted: {source['name']}")
            return True
        elif response.status_code == 404:
            print(f"  ⚠ Not found (already deleted?): {source['name']}")
            return True
        else:
            print(f"  ✗ Failed to delete: {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error deleting: {e}")
        return False


def download_readme() -> str | None:
    """Download the minio-py README from GitHub."""
    print(f"\n{'='*60}")
    print("Downloading MinIO Python SDK README")
    print(f"{'='*60}")
    print(f"\nSource: {MINIO_README_URL}")

    try:
        response = requests.get(MINIO_README_URL, timeout=30)
        response.raise_for_status()

        content = response.text
        word_count = len(content.split())
        print(f"  ✓ Downloaded: {word_count} words")
        return content

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error downloading: {e}")
        return None


def upload_readme(content: str, config: dict, dry_run: bool = False) -> bool:
    """Upload the README to Archon."""
    print(f"\n{'='*60}")
    print("Uploading to Archon Knowledge Base")
    print(f"{'='*60}")
    print(f"\nTitle: {config['title']}")
    print(f"Tags: {', '.join(config['tags'])}")
    print(f"Type: {config['knowledge_type']}")

    if dry_run:
        print("\n[DRY RUN] Would upload README with above configuration")
        return True

    print("\nUploading...")

    # Create a temporary file to upload
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.md',
        prefix='minio-python-sdk-',
        delete=False
    ) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        with open(temp_path, 'rb') as f:
            files = {
                'file': ('MinIO-Python-SDK-README.md', f, 'text/markdown')
            }
            data = {
                'knowledge_type': config['knowledge_type'],
                'tags': json.dumps(config['tags']),  # Must be JSON array
                'extract_code_examples': 'true',
            }

            response = requests.post(
                UPLOAD_ENDPOINT,
                files=files,
                data=data,
                timeout=60
            )

        if response.status_code in (200, 201):
            result = response.json()
            source_id = result.get('sourceId', result.get('source_id', 'unknown'))
            print(f"  ✓ Uploaded successfully!")
            print(f"    Source ID: {source_id}")
            return True
        else:
            print(f"  ✗ Upload failed: {response.status_code}")
            print(f"    Response: {response.text[:300]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error uploading: {e}")
        return False

    finally:
        # Clean up temp file
        temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Replace bloated MinIO docs with focused Python SDK README"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes"
    )
    parser.add_argument(
        "--delete-only",
        action="store_true",
        help="Only delete existing source, don't upload new"
    )
    parser.add_argument(
        "--upload-only",
        action="store_true",
        help="Only upload README, don't delete existing source"
    )

    args = parser.parse_args()

    # Step 1: Delete existing source (unless --upload-only)
    if not args.upload_only:
        delete_success = delete_source(SOURCE_TO_DELETE, dry_run=args.dry_run)
        if not delete_success and not args.dry_run:
            print("\nWarning: Source failed to delete. Continuing anyway...")

    # Step 2: Download and upload README (unless --delete-only)
    if not args.delete_only:
        # Download
        if args.dry_run:
            print(f"\n[DRY RUN] Would download README from: {MINIO_README_URL}")
            content = "[DRY RUN - content not downloaded]"
        else:
            content = download_readme()
            if not content:
                print("\nError: Failed to download README. Aborting upload.")
                return

        # Upload
        upload_readme(content, UPLOAD_CONFIG, dry_run=args.dry_run)

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    if args.dry_run:
        print("This was a dry run. No changes were made.")
        print("\nTo execute for real, run without --dry-run:")
        print("  python scripts/replace_minio_source.py")
    else:
        print("MinIO knowledge base replacement complete!")
        print(f"\nReduction: ~401K words → ~900 words (99.8% smaller)")
        print("Content: Focused Python SDK documentation")


if __name__ == "__main__":
    main()
