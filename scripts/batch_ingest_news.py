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
BATCH_METADATA_FILE = BATCH_DIR / "batch_metadata.json"

# OpenAI Batch API limit: 50,000 requests per file
# We use 40,000 to be safe
BATCH_CHUNK_SIZE = 40000


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
    output_dir: Path,
    persist_dir: str = "./data/vector_db",
    skip_existing: bool = True,
    chunk_size: int = BATCH_CHUNK_SIZE
) -> Dict:
    """
    Read all CSVs and prepare batch request JSONL files (chunked).

    Args:
        news_dir: Directory containing news CSVs
        output_dir: Directory to write chunk files
        persist_dir: ChromaDB persist directory (for checking existing docs)
        skip_existing: If True, skip documents already in ChromaDB
        chunk_size: Max requests per chunk file (default 40,000)

    Returns metadata about the prepared batches.
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
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track documents
    doc_metadata = {}  # doc_id -> {symbol, date, title, source, price_changes...}
    total_docs = 0
    skipped_empty = 0
    skipped_existing = 0

    # Chunk tracking
    chunk_files = []
    current_chunk = 0
    current_chunk_count = 0
    current_file = None

    def safe_float(val):
        try:
            if val is None or str(val).lower() in ("", "nan"):
                return None
            return float(val)
        except:
            return None

    def open_new_chunk():
        nonlocal current_chunk, current_chunk_count, current_file
        if current_file:
            current_file.close()
        current_chunk += 1
        chunk_path = output_dir / f"batch_chunk_{current_chunk:03d}.jsonl"
        chunk_files.append(str(chunk_path))
        current_file = open(chunk_path, "w", encoding="utf-8")
        current_chunk_count = 0
        logger.info(f"Creating chunk file: {chunk_path.name}")
        return current_file

    # Open first chunk
    f = open_new_chunk()

    try:
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

                # Check if we need a new chunk
                if current_chunk_count >= chunk_size:
                    f = open_new_chunk()

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
                current_chunk_count += 1

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
    finally:
        if current_file:
            current_file.close()

    logger.info(f"New documents to embed: {total_docs}")
    logger.info(f"Skipped (empty): {skipped_empty}")
    logger.info(f"Skipped (existing in DB): {skipped_existing}")
    logger.info(f"Created {len(chunk_files)} chunk file(s)")

    # Save metadata
    metadata = {
        "total_documents": total_docs,
        "skipped_empty": skipped_empty,
        "skipped_existing": skipped_existing,
        "chunk_files": chunk_files,
        "chunk_size": chunk_size,
        "documents": doc_metadata,
        "batches": [],  # Will be populated during submit
    }

    return metadata


def submit_batch(metadata_file: Path, chunk_index: int = None) -> List[str]:
    """
    Upload batch file(s) and create batch job(s).

    Args:
        metadata_file: Path to metadata JSON file
        chunk_index: If specified, only submit this chunk (1-based index)

    Returns list of batch IDs.
    """
    if not metadata_file.exists():
        raise ValueError(f"Metadata file not found: {metadata_file}. Run 'prepare' first.")

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    chunk_files = metadata.get("chunk_files", [])
    if not chunk_files:
        raise ValueError("No chunk files found in metadata. Run 'prepare' first.")

    # Filter to specific chunk if requested
    if chunk_index is not None:
        if chunk_index < 1 or chunk_index > len(chunk_files):
            raise ValueError(f"Chunk index must be between 1 and {len(chunk_files)}")
        chunk_files = [chunk_files[chunk_index - 1]]
        logger.info(f"Submitting only chunk {chunk_index}")

    client = get_openai_client()
    batches = metadata.get("batches", [])
    submitted_files = {b["chunk_file"] for b in batches}

    batch_ids = []

    for chunk_file in chunk_files:
        # Skip if already submitted
        if chunk_file in submitted_files:
            logger.info(f"Skipping {Path(chunk_file).name} (already submitted)")
            continue

        chunk_path = Path(chunk_file)
        if not chunk_path.exists():
            logger.error(f"Chunk file not found: {chunk_file}")
            continue

        logger.info(f"Uploading {chunk_path.name}...")

        try:
            # Upload file
            with open(chunk_path, "rb") as f:
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
                    "description": f"Financial news embeddings - {chunk_path.name}"
                }
            )

            batch_id = batch.id
            logger.info(f"Batch created: {batch_id} (status: {batch.status})")

            # Record batch info
            batches.append({
                "chunk_file": chunk_file,
                "file_id": file_id,
                "batch_id": batch_id,
                "status": batch.status,
                "created_at": str(batch.created_at),
            })
            batch_ids.append(batch_id)

            # Save progress after each successful submission
            metadata["batches"] = batches
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error submitting {chunk_path.name}: {e}")
            # Save what we have so far
            metadata["batches"] = batches
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)
            raise

    logger.info(f"Submitted {len(batch_ids)} batch(es)")
    return batch_ids


def check_batch_status(metadata_file: Path) -> Dict:
    """Check status of all batch jobs."""
    if not metadata_file.exists():
        raise ValueError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    batches = metadata.get("batches", [])
    if not batches:
        raise ValueError("No batches found in metadata. Run 'submit' first.")

    client = get_openai_client()

    total_completed = 0
    total_failed = 0
    total_in_progress = 0
    total_requests = 0
    completed_requests = 0

    for batch_info in batches:
        batch_id = batch_info["batch_id"]
        batch = client.batches.retrieve(batch_id)

        # Update batch info
        batch_info["status"] = batch.status
        batch_info["completed_at"] = str(batch.completed_at) if batch.completed_at else None
        batch_info["failed_at"] = str(batch.failed_at) if batch.failed_at else None
        batch_info["output_file_id"] = batch.output_file_id
        batch_info["error_file_id"] = batch.error_file_id

        if batch.request_counts:
            batch_info["request_counts"] = {
                "total": batch.request_counts.total,
                "completed": batch.request_counts.completed,
                "failed": batch.request_counts.failed,
            }
            total_requests += batch.request_counts.total
            completed_requests += batch.request_counts.completed

        if batch.status == "completed":
            total_completed += 1
        elif batch.status == "failed":
            total_failed += 1
        else:
            total_in_progress += 1

    # Update metadata
    metadata["batches"] = batches
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    return {
        "total_batches": len(batches),
        "completed": total_completed,
        "failed": total_failed,
        "in_progress": total_in_progress,
        "total_requests": total_requests,
        "completed_requests": completed_requests,
        "batches": batches,
    }


def download_results(metadata_file: Path, output_dir: Path) -> int:
    """
    Download all completed batch results.

    Returns total number of results downloaded.
    """
    if not metadata_file.exists():
        raise ValueError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    batches = metadata.get("batches", [])
    if not batches:
        raise ValueError("No batches found in metadata.")

    client = get_openai_client()
    output_dir.mkdir(parents=True, exist_ok=True)

    total_downloaded = 0
    result_files = []

    for i, batch_info in enumerate(batches):
        batch_id = batch_info["batch_id"]
        output_file_id = batch_info.get("output_file_id")

        if not output_file_id:
            logger.warning(f"Batch {batch_id} has no output file (status: {batch_info.get('status')})")
            continue

        # Check if already downloaded
        result_file = output_dir / f"batch_result_{i+1:03d}.jsonl"
        if batch_info.get("downloaded") and result_file.exists():
            logger.info(f"Skipping {result_file.name} (already downloaded)")
            result_files.append(str(result_file))
            continue

        logger.info(f"Downloading results for batch {i+1}/{len(batches)}...")

        try:
            response = client.files.content(output_file_id)
            content = response.text

            with open(result_file, "w", encoding="utf-8") as f:
                f.write(content)

            line_count = content.count("\n")
            total_downloaded += line_count
            result_files.append(str(result_file))
            batch_info["downloaded"] = True
            batch_info["result_file"] = str(result_file)

            logger.info(f"Downloaded {line_count} results to {result_file.name}")

        except Exception as e:
            logger.error(f"Error downloading batch {batch_id}: {e}")

    # Update metadata
    metadata["batches"] = batches
    metadata["result_files"] = result_files
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info(f"Total downloaded: {total_downloaded} results from {len(result_files)} file(s)")
    return total_downloaded


def ingest_results(
    metadata_file: Path,
    persist_dir: str = "./data/vector_db"
) -> int:
    """
    Ingest all batch results into ChromaDB.

    Returns number of documents ingested.
    """
    if not metadata_file.exists():
        raise ValueError(f"Metadata file not found: {metadata_file}")

    # Load metadata
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    doc_metadata = metadata.get("documents", {})
    if not doc_metadata:
        raise ValueError("No document metadata found")

    result_files = metadata.get("result_files", [])
    if not result_files:
        raise ValueError("No result files found. Run 'download' first.")

    logger.info(f"Loading {len(doc_metadata)} document metadata...")
    logger.info(f"Processing {len(result_files)} result file(s)...")

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
        # Get all IDs in batches
        batch_size_check = 10000
        count = collection.count()
        for offset in range(0, count, batch_size_check):
            result = collection.get(limit=batch_size_check, offset=offset, include=[])
            existing_ids.update(result["ids"])
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

    for result_file in result_files:
        result_path = Path(result_file)
        if not result_path.exists():
            logger.error(f"Result file not found: {result_file}")
            continue

        logger.info(f"Processing {result_path.name}...")

        with open(result_path, "r", encoding="utf-8") as f:
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
                            # Add to existing_ids to avoid duplicates within this run
                            existing_ids.update(ids_batch)
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
        description="Batch API ingestion for financial news (chunked for large datasets)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps:
  1. prepare <news_dir>  - Prepare batch request files (auto-chunked)
  2. submit              - Upload and submit all batch jobs
  3. status              - Check all batch job statuses
  4. download            - Download all completed results
  5. ingest              - Ingest all embeddings into ChromaDB

Example workflow:
  python scripts/batch_ingest_news.py prepare ./data/news-yh-stock/
  python scripts/batch_ingest_news.py submit
  python scripts/batch_ingest_news.py status  # repeat until all complete
  python scripts/batch_ingest_news.py download
  python scripts/batch_ingest_news.py ingest

For large datasets (600K+ docs), files are split into 40K chunks automatically.
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Prepare command
    prepare_parser = subparsers.add_parser("prepare", help="Prepare batch request files")
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
    submit_parser = subparsers.add_parser("submit", help="Submit batch job(s)")
    submit_parser.add_argument(
        "--chunk",
        type=int,
        default=None,
        help="Submit only this chunk (1-based index)"
    )

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
            BATCH_DIR,
            persist_dir=args.persist_dir,
            skip_existing=not args.full
        )

        # Save metadata
        BATCH_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BATCH_METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info(f"Metadata saved to {BATCH_METADATA_FILE}")

        # Estimate cost
        total_docs = metadata["total_documents"]
        skipped_existing = metadata.get("skipped_existing", 0)
        chunk_files = metadata.get("chunk_files", [])
        # Rough estimate: 500 tokens per doc
        estimated_tokens = total_docs * 500
        estimated_cost = (estimated_tokens / 1_000_000) * 0.01  # Batch API price

        print(f"\n=== Batch Preparation Complete ===")
        print(f"New documents to embed: {total_docs:,}")
        if skipped_existing > 0:
            print(f"Skipped (already in DB): {skipped_existing:,}")
        print(f"Chunk files created: {len(chunk_files)}")
        print(f"Estimated tokens: ~{estimated_tokens:,}")
        print(f"Estimated cost: ~${estimated_cost:.2f} (Batch API)")
        if total_docs == 0:
            print(f"\nNo new documents to process!")
        else:
            print(f"\nNext step: python scripts/batch_ingest_news.py submit")

    elif args.command == "submit":
        batch_ids = submit_batch(BATCH_METADATA_FILE, chunk_index=args.chunk)
        print(f"\n=== Batch Submitted ===")
        print(f"Submitted {len(batch_ids)} batch(es)")
        for bid in batch_ids:
            print(f"  - {bid}")
        print(f"\nBatches will complete within 24 hours.")
        print(f"Check status: python scripts/batch_ingest_news.py status")

    elif args.command == "status":
        status = check_batch_status(BATCH_METADATA_FILE)
        print(f"\n=== Batch Status ===")
        print(f"Total batches: {status['total_batches']}")
        print(f"Completed: {status['completed']}")
        print(f"In progress: {status['in_progress']}")
        print(f"Failed: {status['failed']}")
        print(f"Requests: {status['completed_requests']:,}/{status['total_requests']:,}")

        print(f"\nDetails:")
        for i, b in enumerate(status['batches']):
            chunk_name = Path(b['chunk_file']).name
            print(f"  [{i+1}] {chunk_name}: {b['status']}")

        if status['in_progress'] == 0 and status['completed'] > 0:
            print(f"\n✅ All batches complete! Run: python scripts/batch_ingest_news.py download")
        elif status['failed'] > 0:
            print(f"\n⚠️ Some batches failed!")
        else:
            pct = status['completed_requests'] / status['total_requests'] * 100 if status['total_requests'] > 0 else 0
            print(f"\n⏳ In progress: {pct:.1f}% complete")

    elif args.command == "download":
        count = download_results(BATCH_METADATA_FILE, BATCH_DIR)
        print(f"\n=== Download Complete ===")
        print(f"Downloaded {count:,} results")
        print(f"\nNext step: python scripts/batch_ingest_news.py ingest")

    elif args.command == "ingest":
        count = ingest_results(
            BATCH_METADATA_FILE,
            args.persist_dir
        )
        print(f"\n=== Ingestion Complete ===")
        print(f"Ingested {count:,} documents")


if __name__ == "__main__":
    main()
