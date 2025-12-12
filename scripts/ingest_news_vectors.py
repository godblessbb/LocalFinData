#!/usr/bin/env python3
"""
CLI script for ingesting financial news into the vector database.

Usage:
    # Ingest a single CSV file
    python scripts/ingest_news_vectors.py ./data/news/AAPL.csv

    # Ingest entire directory
    python scripts/ingest_news_vectors.py ./data/news-yh-stock/ --directory

    # With custom model path
    python scripts/ingest_news_vectors.py ./data/news/ --directory \
        --model-path D:/models/Qwen3-Embedding-4B

    # Without 4-bit quantization
    python scripts/ingest_news_vectors.py ./data/news/ --directory --no-4bit
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from localfindata.vectordb.store import FinancialNewsStore
from localfindata.vectordb.ingest import NewsIngester


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Ingest financial news CSVs into vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Ingest single file
    python scripts/ingest_news_vectors.py ./data/news/AAPL.csv

    # Ingest directory
    python scripts/ingest_news_vectors.py ./data/news-yh-stock/ -d

    # With custom embedding model
    python scripts/ingest_news_vectors.py ./data/news/ -d \\
        --model-path D:/models/Qwen3-Embedding-4B

    # Check stats only
    python scripts/ingest_news_vectors.py --stats
        """,
    )

    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to CSV file or directory",
    )

    parser.add_argument(
        "-d",
        "--directory",
        action="store_true",
        help="Treat input_path as directory and ingest all CSVs",
    )

    parser.add_argument(
        "--persist-dir",
        default="./data/vector_db",
        help="ChromaDB persist directory (default: ./data/vector_db)",
    )

    parser.add_argument(
        "--model-path",
        default=None,
        help="Path to local embedding model (e.g., D:/models/Qwen3-Embedding-4B)",
    )

    parser.add_argument(
        "--no-4bit",
        action="store_true",
        help="Disable 4-bit quantization (uses more VRAM)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for processing (default: 500)",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show vector store statistics and exit",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)

    # Initialize store
    logger.info("Initializing vector store...")
    store = FinancialNewsStore(
        persist_dir=args.persist_dir,
        model_path=args.model_path,
        use_4bit=not args.no_4bit,
    )

    # Stats mode
    if args.stats:
        stats = store.get_stats()
        print("\n=== Vector Store Statistics ===")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()
        return 0

    # Check input path
    if not args.input_path:
        parser.error("input_path is required (unless using --stats)")

    input_path = Path(args.input_path)

    if not input_path.exists():
        logger.error(f"Path not found: {input_path}")
        return 1

    # Create ingester
    ingester = NewsIngester(store, batch_size=args.batch_size)

    # Ingest
    if args.directory or input_path.is_dir():
        logger.info(f"Ingesting all CSVs from: {input_path}")
        results = ingester.ingest_directory(str(input_path))
        print("\n=== Ingestion Results ===")
        print(f"  Files processed: {results['files_processed']}")
        print(f"  Files failed: {results['files_failed']}")
        print(f"  Total documents: {results['total_documents']}")
    else:
        logger.info(f"Ingesting file: {input_path}")
        count = ingester.ingest_file(str(input_path))
        print(f"\n=== Ingested {count} documents ===")

    # Show final stats
    stats = store.get_stats()
    print(f"\nTotal documents in store: {stats['total_documents']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
