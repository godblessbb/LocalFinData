#!/usr/bin/env python3
"""
Batch API ingestion for financial news using OpenAI Batch API.

This script uses OpenAI's Batch API which is 50% cheaper than real-time API.
The trade-off is that it takes up to 24 hours to complete.

Usage:
    # Step 1: Prepare batch request file
    python scripts/batch_ingest_news.py prepare D:/GitHub/LocalFinData/data/news-yh-stock/

    # Step 2: Submit batch job
    python scripts/batch_ingest_news.py submit

    # Step 3: Check status
    python scripts/batch_ingest_news.py status

    # Step 4: Download results and ingest (after batch completes)
    python scripts/batch_ingest_news.py ingest
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BATCH_DIR = DATA_DIR / "batch_embedding"
BATCH_REQUEST_FILE = BATCH_DIR / "batch_requests.jsonl"
BATCH_METADATA_FILE = BATCH_DIR / "batch_metadata.json"
BATCH_RESULT_FILE = BATCH_DIR / "batch_results.jsonl"


def load_env():
    """Load environment variables from .env file."""
    try:
        from dotenv import load_dotenv
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
    except ImportError:
        pass


def get_openai_client():
    """Get OpenAI client."""
    import os
    from openai import OpenAI

    load_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in .env file")

    base_url = os.environ.get("OPENAI_BASE_URL")
    return OpenAI(api_key=api_key, base_url=base_url)


def generate_doc_id(symbol: str, date: str, title: str, content: str) -> str:
    """Generate unique document ID."""
    return hashlib.md5(
        f"{symbol}_{date}_{title}_{content[:100]}".encode()
    ).hexdigest()


def get_existing_ids_from_db(persist_dir: str = "./data/vector_db") -> set:
    """Get all existing document IDs from ChromaDB."""
    import chromadb

    persist_path = Path(persist_dir)
    if not persist_path.exists():
        return set()

    try:
        chroma_client = chromadb.PersistentClient(path=str(persist_path))
        collection = chroma_client.get_or_create_collection(name="financial_news")
        count = collection.count()

        if count == 0:
            return set()

        logger.info(f"Found {count} existing documents in ChromaDB")

        # Get all IDs in batches
        existing_ids = set()
        batch_size = 10000
        for offset in range(0, count, batch_size):
            result = collection.get(limit=batch_size, offset=offset, include=[])
            existing_ids.update(result["ids"])

        return existing_ids
    except Exception as e:
        logger.warning(f"Could not read existing IDs from ChromaDB: {e}")
        return set()


def prepare_batch_requests(
    news_dir: str,
    output_file: Path,
    persist_dir: str = "./data/vector_db",
    skip_existing: bool = True
) -> Dict:
    """
    Read all CSVs and prepare batch request JSONL file.

    Args:
        news_dir: Directory containing news CSVs
        output_file: Path to output JSONL file
        persist_dir: ChromaDB persist directory (for checking existing docs)
        skip_existing: If True, skip documents already in ChromaDB

    Returns metadata about the prepared batch.
    """
    news_path = Path(news_dir)
    if not news_path.exists():
        raise ValueError(f"Directory not found: {news_path}")

    csv_files = sorted(news_path.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {news_path}")

    logger.info(f"Found {len(csv_files)} CSV files")

    # Get existing IDs from ChromaDB
    existing_ids = set()
    if skip_existing:
        existing_ids = get_existing_ids_from_db(persist_dir)
        if existing_ids:
            logger.info(f"Will skip {len(existing_ids)} existing documents")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Track documents
    doc_metadata = {}  # doc_id -> {symbol, date, title, source, price_changes...}
    total_docs = 0
    skipped_empty = 0
    skipped_existing = 0

    with open(output_file, "w", encoding="utf-8") as f:
        for csv_file in csv_files:
            logger.info(f"Processing {csv_file.name}...")

            try:
                df = pd.read_csv(csv_file, dtype=str)
            except Exception as e:
                logger.error(f"Error reading {csv_file}: {e}")
                continue

            for _, row in df.iterrows():
                title = str(row.get("news_title", "")).strip()
                content = str(row.get("news_content", "")).strip()
                symbol = str(row.get("symbol", "")).strip()
                date = str(row.get("news_date", "")).strip()

                # Skip empty content
                if not content or content.lower() == "nan":
                    skipped_empty += 1
                    continue

                # Generate document ID
                doc_id = generate_doc_id(symbol, date, title, content)

                # Skip if already processed (duplicate in this batch)
                if doc_id in doc_metadata:
                    continue

                # Skip if already exists in ChromaDB
                if doc_id in existing_ids:
                    skipped_existing += 1
                    continue

                # Prepare text for embedding
                text = f"{title}\n{content}"

                # Create batch request
                request = {
                    "custom_id": doc_id,
                    "method": "POST",
                    "url": "/v1/embeddings",
                    "body": {
                        "model": "text-embedding-3-small",
                        "input": text,
                    }
                }

                f.write(json.dumps(request, ensure_ascii=False) + "\n")

                # Store metadata for later
                def safe_float(val):
                    try:
                        if val is None or str(val).lower() in ("", "nan"):
                            return None
                        return float(val)
                    except:
                        return None

                doc_metadata[doc_id] = {
                    "symbol": symbol,
                    "news_date": date,
                    "source": str(row.get("source", "")),
                    "title": title,
                    "content": content,
                    "price_change_1d": safe_float(row.get("price_change_1d")),
                    "price_change_3d": safe_float(row.get("price_change_3d")),
                    "price_change_5d": safe_float(row.get("price_change_5d")),
                    "price_change_10d": safe_float(row.get("price_change_10d")),
                }

                total_docs += 1

                if total_docs % 10000 == 0:
                    logger.info(f"Processed {total_docs} documents...")

    logger.info(f"New documents to embed: {total_docs}")
    logger.info(f"Skipped (empty): {skipped_empty}")
    logger.info(f"Skipped (existing in DB): {skipped_existing}")
    logger.info(f"Batch request file: {output_file}")

    # Save metadata
    metadata = {
        "total_documents": total_docs,
        "skipped_empty": skipped_empty,
        "skipped_existing": skipped_existing,
        "request_file": str(output_file),
        "documents": doc_metadata,
    }

    return metadata


def submit_batch(request_file: Path, metadata_file: Path) -> str:
    """
    Upload batch file and create batch job.

    Returns batch ID.
    """
    client = get_openai_client()

    logger.info(f"Uploading batch file: {request_file}")

    # Upload file
    with open(request_file, "rb") as f:
        file_response = client.files.create(
            file=f,
            purpose="batch"
        )

    file_id = file_response.id
    logger.info(f"File uploaded: {file_id}")

    # Create batch
    batch = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/embeddings",
        completion_window="24h",
        metadata={
            "description": "Financial news embeddings"
        }
    )

    batch_id = batch.id
    logger.info(f"Batch created: {batch_id}")
    logger.info(f"Status: {batch.status}")

    # Update metadata file
    if metadata_file.exists():
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    metadata["batch_id"] = batch_id
    metadata["file_id"] = file_id
    metadata["status"] = batch.status
    metadata["created_at"] = batch.created_at

    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info(f"Metadata saved to {metadata_file}")

    return batch_id


def check_batch_status(metadata_file: Path) -> Dict:
    """Check batch job status."""
    if not metadata_file.exists():
        raise ValueError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    batch_id = metadata.get("batch_id")
    if not batch_id:
        raise ValueError("No batch_id found in metadata")

    client = get_openai_client()
    batch = client.batches.retrieve(batch_id)

    status_info = {
        "batch_id": batch_id,
        "status": batch.status,
        "created_at": batch.created_at,
        "completed_at": batch.completed_at,
        "failed_at": batch.failed_at,
        "expired_at": batch.expired_at,
        "request_counts": batch.request_counts,
        "output_file_id": batch.output_file_id,
        "error_file_id": batch.error_file_id,
    }

    # Update metadata
    metadata.update(status_info)
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    return status_info


def download_results(metadata_file: Path, output_file: Path) -> int:
    """
    Download batch results.

    Returns number of results downloaded.
    """
    if not metadata_file.exists():
        raise ValueError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    output_file_id = metadata.get("output_file_id")
    if not output_file_id:
        raise ValueError("No output_file_id found. Batch may not be complete.")

    client = get_openai_client()

    logger.info(f"Downloading results from {output_file_id}...")

    response = client.files.content(output_file_id)
    content = response.text

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    # Count results
    line_count = content.count("\n")
    logger.info(f"Downloaded {line_count} results to {output_file}")

    return line_count


def ingest_results(
    metadata_file: Path,
    result_file: Path,
    persist_dir: str = "./data/vector_db"
) -> int:
    """
    Ingest batch results into ChromaDB.

    Returns number of documents ingested.
    """
    from localfindata.vectordb.store import FinancialNewsStore, NewsDocument

    if not metadata_file.exists():
        raise ValueError(f"Metadata file not found: {metadata_file}")
    if not result_file.exists():
        raise ValueError(f"Result file not found: {result_file}")

    # Load metadata
    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    doc_metadata = metadata.get("documents", {})
    if not doc_metadata:
        raise ValueError("No document metadata found")

    logger.info(f"Loading {len(doc_metadata)} document metadata...")

    # Initialize store (without embedder since we have embeddings)
    import chromadb

    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)

    chroma_client = chromadb.PersistentClient(path=str(persist_path))
    collection = chroma_client.get_or_create_collection(
        name="financial_news",
        metadata={"hnsw:space": "cosine"}
    )

    logger.info(f"ChromaDB collection ready. Current count: {collection.count()}")

    # Get existing IDs to skip duplicates
    existing_ids = set()
    if collection.count() > 0:
        logger.info("Checking for existing documents...")
        # Get all IDs from the collection
        all_ids = list(doc_metadata.keys())
        for i in range(0, len(all_ids), 1000):
            batch_ids = all_ids[i:i+1000]
            try:
                result = collection.get(ids=batch_ids)
                existing_ids.update(result["ids"])
            except Exception:
                pass
        logger.info(f"Found {len(existing_ids)} existing documents to skip")

    # Process results
    batch_size = 500
    ids_batch = []
    embeddings_batch = []
    metadatas_batch = []
    documents_batch = []

    added_count = 0
    skipped_count = 0
    error_count = 0

    with open(result_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            if not line.strip():
                continue

            try:
                result = json.loads(line)
                custom_id = result["custom_id"]

                # Check for errors
                if result.get("error"):
                    error_count += 1
                    continue

                # Get embedding
                response = result.get("response", {})
                body = response.get("body", {})
                data = body.get("data", [])

                if not data:
                    error_count += 1
                    continue

                embedding = data[0].get("embedding")
                if not embedding:
                    error_count += 1
                    continue

                # Get document metadata
                doc_meta = doc_metadata.get(custom_id)
                if not doc_meta:
                    skipped_count += 1
                    continue

                # Skip if already exists in ChromaDB
                if custom_id in existing_ids:
                    skipped_count += 1
                    continue

                # Prepare for batch insert
                ids_batch.append(custom_id)
                embeddings_batch.append(embedding)
                documents_batch.append(doc_meta["content"])

                # Build metadata (ChromaDB doesn't support None values)
                meta = {
                    "symbol": doc_meta["symbol"],
                    "news_date": doc_meta["news_date"],
                    "source": doc_meta["source"],
                    "title": doc_meta["title"],
                }
                for key in ["price_change_1d", "price_change_3d", "price_change_5d", "price_change_10d"]:
                    if doc_meta.get(key) is not None:
                        meta[key] = doc_meta[key]

                metadatas_batch.append(meta)

                # Insert batch
                if len(ids_batch) >= batch_size:
                    try:
                        collection.add(
                            ids=ids_batch,
                            embeddings=embeddings_batch,
                            metadatas=metadatas_batch,
                            documents=documents_batch,
                        )
                        added_count += len(ids_batch)
                        logger.info(f"Ingested {added_count} documents...")
                    except Exception as e:
                        logger.error(f"Error inserting batch: {e}")
                        error_count += len(ids_batch)

                    ids_batch = []
                    embeddings_batch = []
                    metadatas_batch = []
                    documents_batch = []

            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                error_count += 1

    # Insert remaining
    if ids_batch:
        try:
            collection.add(
                ids=ids_batch,
                embeddings=embeddings_batch,
                metadatas=metadatas_batch,
                documents=documents_batch,
            )
            added_count += len(ids_batch)
        except Exception as e:
            logger.error(f"Error inserting final batch: {e}")
            error_count += len(ids_batch)

    logger.info(f"Ingestion complete!")
    logger.info(f"  Added: {added_count}")
    logger.info(f"  Skipped: {skipped_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"  Total in DB: {collection.count()}")

    return added_count


def main():
    parser = argparse.ArgumentParser(
        description="Batch API ingestion for financial news",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps:
  1. prepare <news_dir>  - Prepare batch request file from CSVs
  2. submit              - Upload and submit batch job
  3. status              - Check batch job status
  4. download            - Download results (after completion)
  5. ingest              - Ingest embeddings into ChromaDB

Example workflow:
  python scripts/batch_ingest_news.py prepare ./data/news-yh-stock/
  python scripts/batch_ingest_news.py submit
  python scripts/batch_ingest_news.py status  # repeat until complete
  python scripts/batch_ingest_news.py download
  python scripts/batch_ingest_news.py ingest
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Prepare command
    prepare_parser = subparsers.add_parser("prepare", help="Prepare batch request file")
    prepare_parser.add_argument("news_dir", help="Directory containing news CSVs")
    prepare_parser.add_argument(
        "--persist-dir",
        default="./data/vector_db",
        help="ChromaDB persist directory (for checking existing docs)"
    )
    prepare_parser.add_argument(
        "--full",
        action="store_true",
        help="Process all documents, ignoring existing ones in ChromaDB"
    )

    # Submit command
    subparsers.add_parser("submit", help="Submit batch job")

    # Status command
    subparsers.add_parser("status", help="Check batch status")

    # Download command
    subparsers.add_parser("download", help="Download batch results")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest results into ChromaDB")
    ingest_parser.add_argument(
        "--persist-dir",
        default="./data/vector_db",
        help="ChromaDB persist directory"
    )

    args = parser.parse_args()

    if args.command == "prepare":
        metadata = prepare_batch_requests(
            args.news_dir,
            BATCH_REQUEST_FILE,
            persist_dir=args.persist_dir,
            skip_existing=not args.full
        )

        # Save metadata
        BATCH_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BATCH_METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info(f"Metadata saved to {BATCH_METADATA_FILE}")

        # Estimate cost
        total_docs = metadata["total_documents"]
        skipped_existing = metadata.get("skipped_existing", 0)
        # Rough estimate: 500 tokens per doc
        estimated_tokens = total_docs * 500
        estimated_cost = (estimated_tokens / 1_000_000) * 0.01  # Batch API price

        print(f"\n=== Batch Preparation Complete ===")
        print(f"New documents to embed: {total_docs:,}")
        if skipped_existing > 0:
            print(f"Skipped (already in DB): {skipped_existing:,}")
        print(f"Request file: {BATCH_REQUEST_FILE}")
        print(f"Estimated tokens: ~{estimated_tokens:,}")
        print(f"Estimated cost: ~${estimated_cost:.2f} (Batch API)")
        if total_docs == 0:
            print(f"\nNo new documents to process!")
        else:
            print(f"\nNext step: python scripts/batch_ingest_news.py submit")

    elif args.command == "submit":
        batch_id = submit_batch(BATCH_REQUEST_FILE, BATCH_METADATA_FILE)
        print(f"\n=== Batch Submitted ===")
        print(f"Batch ID: {batch_id}")
        print(f"The batch will complete within 24 hours.")
        print(f"\nCheck status: python scripts/batch_ingest_news.py status")

    elif args.command == "status":
        status = check_batch_status(BATCH_METADATA_FILE)
        print(f"\n=== Batch Status ===")
        for key, value in status.items():
            print(f"  {key}: {value}")

        if status["status"] == "completed":
            print(f"\n✅ Batch complete! Run: python scripts/batch_ingest_news.py download")
        elif status["status"] == "failed":
            print(f"\n❌ Batch failed!")
        elif status["status"] == "in_progress":
            counts = status.get("request_counts", {})
            completed = counts.get("completed", 0)
            total = counts.get("total", 0)
            print(f"\n⏳ In progress: {completed}/{total} requests completed")

    elif args.command == "download":
        count = download_results(BATCH_METADATA_FILE, BATCH_RESULT_FILE)
        print(f"\n=== Download Complete ===")
        print(f"Downloaded {count} results")
        print(f"Result file: {BATCH_RESULT_FILE}")
        print(f"\nNext step: python scripts/batch_ingest_news.py ingest")

    elif args.command == "ingest":
        count = ingest_results(
            BATCH_METADATA_FILE,
            BATCH_RESULT_FILE,
            args.persist_dir
        )
        print(f"\n=== Ingestion Complete ===")
        print(f"Ingested {count} documents")


if __name__ == "__main__":
    main()
