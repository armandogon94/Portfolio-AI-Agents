#!/usr/bin/env python3
"""Seed the Qdrant RAG knowledge base with domain-specific documents.

Usage:
    python scripts/seed_rag.py --domain healthcare
    python scripts/seed_rag.py --all
    python scripts/seed_rag.py --list
"""

import argparse
import sys
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

SEEDS_DIR = Path(__file__).parent.parent / "src" / "config" / "seeds"

AVAILABLE_DOMAINS = [
    p.stem for p in sorted(SEEDS_DIR.glob("*.yaml"))
]


def load_seed_documents(domain: str) -> list[dict]:
    """Load seed documents from YAML for the given domain."""
    import yaml

    seed_file = SEEDS_DIR / f"{domain}.yaml"
    if not seed_file.exists():
        print(f"  ERROR: No seed file found for domain '{domain}' at {seed_file}")
        return []

    data = yaml.safe_load(seed_file.read_text())
    return data.get("documents", [])


def seed_domain(domain: str, repo) -> int:
    """Seed documents for a single domain. Returns number of documents added."""
    print(f"\n  Seeding domain: {domain}")
    docs = load_seed_documents(domain)
    if not docs:
        print(f"  No documents found for '{domain}'")
        return 0

    added = 0
    for doc in docs:
        try:
            repo.add(
                doc_id=doc["id"],
                content=doc["content"],
                metadata=doc.get("metadata", {}),
            )
            print(f"    + {doc['id']}")
            added += 1
        except Exception as e:
            print(f"    ERROR seeding {doc['id']}: {e}")

    print(f"  Seeded {added}/{len(docs)} documents for '{domain}'")
    return added


def main():
    parser = argparse.ArgumentParser(
        description="Seed the Qdrant RAG knowledge base with domain-specific documents."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--domain",
        choices=AVAILABLE_DOMAINS,
        help="Seed a specific domain",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Seed all available domains",
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="List available seed domains",
    )
    args = parser.parse_args()

    if args.list:
        print("Available seed domains:")
        for d in AVAILABLE_DOMAINS:
            docs = load_seed_documents(d)
            print(f"  {d} ({len(docs)} documents)")
        return

    print("Connecting to Qdrant...")
    try:
        from src.repositories.qdrant_repo import QdrantRepository

        repo = QdrantRepository()
        print("  Connected.")
    except Exception as e:
        print(f"ERROR: Could not connect to Qdrant: {e}")
        print("Make sure Qdrant is running: docker compose -f docker-compose.dev.yml up -d")
        sys.exit(1)

    domains_to_seed = AVAILABLE_DOMAINS if args.all else [args.domain]
    total = 0
    for domain in domains_to_seed:
        total += seed_domain(domain, repo)

    print(f"\nDone. Total documents seeded: {total}")


if __name__ == "__main__":
    main()
