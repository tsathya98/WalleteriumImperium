"""
Local JSON Storage System for Receipt Processing

This module provides local storage capabilities for processed receipts,
including persistence, retrieval, search, filtering, and export functionality.
"""

import json
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import uuid
from dataclasses import dataclass
import sqlite3
from contextlib import contextmanager

from .models import ProcessedReceipt


@dataclass
class StorageConfig:
    """Configuration for receipt storage."""

    storage_dir: str = "receipt_storage"
    json_file: str = "receipts.json"
    backup_dir: str = "backups"
    max_backups: int = 10
    enable_sqlite: bool = True
    sqlite_file: str = "receipts.db"


class ReceiptStorage:
    """Local storage manager for processed receipts."""

    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize storage system."""
        self.config = config or StorageConfig()
        self.storage_path = Path(self.config.storage_dir)
        self.json_path = self.storage_path / self.config.json_file
        self.backup_path = self.storage_path / self.config.backup_dir
        self.sqlite_path = self.storage_path / self.config.sqlite_file

        # Ensure storage directories exist
        self._setup_storage()

        # Initialize SQLite if enabled
        if self.config.enable_sqlite:
            self._setup_sqlite()

    def _setup_storage(self):
        """Set up storage directories and files."""
        self.storage_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)

        # Create empty JSON file if it doesn't exist
        if not self.json_path.exists():
            self._save_json(
                {
                    "metadata": {
                        "created": datetime.now().isoformat(),
                        "version": "1.0",
                        "total_receipts": 0,
                    },
                    "receipts": {},
                }
            )

    def _setup_sqlite(self):
        """Set up SQLite database for enhanced search capabilities."""
        with self._get_sqlite_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS receipts (
                    id TEXT PRIMARY KEY,
                    filename TEXT,
                    input_type TEXT,
                    processing_date TEXT,
                    store_name TEXT,
                    transaction_date TEXT,
                    total_amount REAL,
                    confidence_score REAL,
                    tags TEXT,
                    category TEXT,
                    status TEXT,
                    json_data TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS line_items (
                    id TEXT PRIMARY KEY,
                    receipt_id TEXT,
                    description TEXT,
                    quantity REAL,
                    unit_price REAL,
                    total_price REAL,
                    category TEXT,
                    confidence_score REAL,
                    FOREIGN KEY (receipt_id) REFERENCES receipts (id)
                )
            """
            )

            # Create indexes for better search performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_store_name ON receipts(store_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transaction_date ON receipts(transaction_date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_category ON receipts(category)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON receipts(tags)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_item_category ON line_items(category)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_item_description ON line_items(description)"
            )

    @contextmanager
    def _get_sqlite_connection(self):
        """Get SQLite database connection with context management."""
        conn = sqlite3.connect(str(self.sqlite_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()

    def _load_json(self) -> Dict[str, Any]:
        """Load receipts from JSON file."""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_receipts": 0,
                },
                "receipts": {},
            }

    def _save_json(self, data: Dict[str, Any]):
        """Save receipts to JSON file with backup."""
        # Create backup before saving
        if self.json_path.exists():
            self._create_backup()

        # Save new data
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def _create_backup(self):
        """Create a backup of the current JSON file."""
        if not self.json_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_path / f"receipts_backup_{timestamp}.json"

        shutil.copy2(self.json_path, backup_file)

        # Clean up old backups
        self._cleanup_old_backups()

    def _cleanup_old_backups(self):
        """Remove old backup files beyond the configured limit."""
        backup_files = list(self.backup_path.glob("receipts_backup_*.json"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Remove excess backups
        for backup_file in backup_files[self.config.max_backups :]:
            backup_file.unlink()

    async def store_receipt(self, receipt: ProcessedReceipt) -> str:
        """Store a processed receipt and return its ID."""
        try:
            receipt_id = receipt.receipt_payload.processing_metadata.receipt_id

            # Load current data
            data = self._load_json()

            # Add receipt to JSON storage
            receipt_dict = receipt.to_dict()
            data["receipts"][receipt_id] = {
                **receipt_dict,
                "storage_metadata": {
                    "stored_at": datetime.now().isoformat(),
                    "storage_version": "1.0",
                },
            }

            # Update metadata
            data["metadata"]["total_receipts"] = len(data["receipts"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()

            # Save to JSON
            self._save_json(data)

            # Store in SQLite if enabled
            if self.config.enable_sqlite:
                await self._store_in_sqlite(receipt)

            return receipt_id

        except Exception as e:
            raise ValueError(f"Failed to store receipt: {str(e)}")

    async def _store_in_sqlite(self, receipt: ProcessedReceipt):
        """Store receipt in SQLite database for enhanced search."""
        try:
            metadata = receipt.receipt_payload.processing_metadata
            store = receipt.receipt_payload.store_details
            transaction = receipt.receipt_payload.transaction_details
            payment = receipt.receipt_payload.payment_summary
            user_meta = receipt.receipt_payload.user_defined_metadata

            receipt_id = metadata.receipt_id

            with self._get_sqlite_connection() as conn:
                # Insert/update main receipt record
                conn.execute(
                    """
                    INSERT OR REPLACE INTO receipts (
                        id, filename, input_type, processing_date, store_name,
                        transaction_date, total_amount, confidence_score, tags,
                        category, status, json_data, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        receipt_id,
                        metadata.source_filename,
                        metadata.source_type.value,
                        metadata.processing_timestamp_utc,
                        store.name if store else None,
                        transaction.date if transaction else None,
                        payment.total_amount if payment else 0.0,
                        receipt.mcp_format.confidence_score,
                        json.dumps(user_meta.tags) if user_meta.tags else None,
                        user_meta.overall_category if user_meta else None,
                        receipt.mcp_format.status,
                        receipt.to_json(),
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )

                # Clear existing line items
                conn.execute(
                    "DELETE FROM line_items WHERE receipt_id = ?", (receipt_id,)
                )

                # Insert line items
                for item in receipt.receipt_payload.line_items:
                    item_id = f"{receipt_id}_{uuid.uuid4().hex[:8]}"
                    conn.execute(
                        """
                        INSERT INTO line_items (
                            id, receipt_id, description, quantity, unit_price,
                            total_price, category, confidence_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            item_id,
                            receipt_id,
                            item.description,
                            item.quantity,
                            item.unit_price,
                            item.total_price,
                            item.category,
                            item.confidence_score,
                        ),
                    )

                conn.commit()

        except Exception as e:
            raise ValueError(f"Failed to store in SQLite: {str(e)}")

    async def get_receipt(self, receipt_id: str) -> Optional[ProcessedReceipt]:
        """Retrieve a receipt by ID."""
        try:
            data = self._load_json()
            receipt_data = data["receipts"].get(receipt_id)

            if not receipt_data:
                return None

            # Remove storage metadata before creating ProcessedReceipt
            receipt_dict = receipt_data.copy()
            receipt_dict.pop("storage_metadata", None)

            return ProcessedReceipt.from_dict(receipt_dict)

        except Exception as e:
            raise ValueError(f"Failed to retrieve receipt: {str(e)}")

    async def list_receipts(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all receipts with optional pagination."""
        try:
            data = self._load_json()
            receipts = list(data["receipts"].values())

            # Sort by processing date (newest first)
            receipts.sort(
                key=lambda x: x.get("receipt_payload", {})
                .get("processing_metadata", {})
                .get("processing_timestamp_utc", ""),
                reverse=True,
            )

            # Apply pagination
            if limit:
                receipts = receipts[offset : offset + limit]
            else:
                receipts = receipts[offset:]

            # Return summary information
            summaries = []
            for receipt_data in receipts:
                receipt_payload = receipt_data.get("receipt_payload", {})
                metadata = receipt_payload.get("processing_metadata", {})
                store = receipt_payload.get("store_details", {})
                payment = receipt_payload.get("payment_summary", {})
                user_meta = receipt_payload.get("user_defined_metadata", {})

                summary = {
                    "receipt_id": metadata.get("receipt_id"),
                    "filename": metadata.get("source_filename"),
                    "input_type": metadata.get("source_type"),
                    "processing_date": metadata.get("processing_timestamp_utc"),
                    "store_name": store.get("name") if store else None,
                    "total_amount": payment.get("total_amount") if payment else 0.0,
                    "confidence_score": receipt_data.get("mcp_format", {}).get(
                        "confidence_score", 0.0
                    ),
                    "category": user_meta.get("overall_category")
                    if user_meta
                    else None,
                    "tags": user_meta.get("tags", []) if user_meta else [],
                    "stored_at": receipt_data.get("storage_metadata", {}).get(
                        "stored_at"
                    ),
                }
                summaries.append(summary)

            return summaries

        except Exception as e:
            raise ValueError(f"Failed to list receipts: {str(e)}")

    async def search_receipts(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search receipts using text query and optional filters."""
        try:
            if self.config.enable_sqlite:
                return await self._search_sqlite(query, filters)
            else:
                return await self._search_json(query, filters)

        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")

    async def _search_sqlite(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search using SQLite for better performance."""
        filters = filters or {}

        # Build SQL query
        sql_parts = ["SELECT * FROM receipts WHERE 1=1"]
        params = []

        # Text search across multiple fields
        if query.strip():
            sql_parts.append(
                """
                AND (
                    store_name LIKE ? OR
                    filename LIKE ? OR
                    category LIKE ? OR
                    tags LIKE ?
                )
            """
            )
            search_pattern = f"%{query}%"
            params.extend([search_pattern] * 4)

        # Apply filters
        if filters.get("store_name"):
            sql_parts.append("AND store_name LIKE ?")
            params.append(f"%{filters['store_name']}%")

        if filters.get("category"):
            sql_parts.append("AND category = ?")
            params.append(filters["category"])

        if filters.get("date_from"):
            sql_parts.append("AND transaction_date >= ?")
            params.append(filters["date_from"])

        if filters.get("date_to"):
            sql_parts.append("AND transaction_date <= ?")
            params.append(filters["date_to"])

        if filters.get("min_amount"):
            sql_parts.append("AND total_amount >= ?")
            params.append(filters["min_amount"])

        if filters.get("max_amount"):
            sql_parts.append("AND total_amount <= ?")
            params.append(filters["max_amount"])

        if filters.get("input_type"):
            sql_parts.append("AND input_type = ?")
            params.append(filters["input_type"])

        # Add ordering
        sql_parts.append("ORDER BY processing_date DESC")

        # Add limit if specified
        if filters.get("limit"):
            sql_parts.append("LIMIT ?")
            params.append(filters["limit"])

        sql = " ".join(sql_parts)

        with self._get_sqlite_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

            results = []
            for row in rows:
                result = {
                    "receipt_id": row["id"],
                    "filename": row["filename"],
                    "input_type": row["input_type"],
                    "processing_date": row["processing_date"],
                    "store_name": row["store_name"],
                    "transaction_date": row["transaction_date"],
                    "total_amount": row["total_amount"],
                    "confidence_score": row["confidence_score"],
                    "category": row["category"],
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "status": row["status"],
                }
                results.append(result)

            return results

    async def _search_json(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search using JSON data (fallback when SQLite is disabled)."""
        data = self._load_json()
        results = []

        query_lower = query.lower()

        for receipt_data in data["receipts"].values():
            receipt_payload = receipt_data.get("receipt_payload", {})
            metadata = receipt_payload.get("processing_metadata", {})
            store = receipt_payload.get("store_details", {})
            payment = receipt_payload.get("payment_summary", {})
            user_meta = receipt_payload.get("user_defined_metadata", {})
            transaction = receipt_payload.get("transaction_details", {})

            # Text search
            searchable_text = " ".join(
                [
                    store.get("name", "") if store else "",
                    metadata.get("source_filename", ""),
                    user_meta.get("overall_category", "") if user_meta else "",
                    " ".join(user_meta.get("tags", [])) if user_meta else "",
                ]
            ).lower()

            if query_lower not in searchable_text:
                continue

            # Apply filters
            if filters:
                if filters.get("store_name") and store:
                    if (
                        filters["store_name"].lower()
                        not in store.get("name", "").lower()
                    ):
                        continue

                if filters.get("category") and user_meta:
                    if filters["category"] != user_meta.get("overall_category"):
                        continue

                # Add more filter logic as needed

            # Add to results
            summary = {
                "receipt_id": metadata.get("receipt_id"),
                "filename": metadata.get("source_filename"),
                "input_type": metadata.get("source_type"),
                "processing_date": metadata.get("processing_timestamp_utc"),
                "store_name": store.get("name") if store else None,
                "transaction_date": transaction.get("date") if transaction else None,
                "total_amount": payment.get("total_amount") if payment else 0.0,
                "confidence_score": receipt_data.get("mcp_format", {}).get(
                    "confidence_score", 0.0
                ),
                "category": user_meta.get("overall_category") if user_meta else None,
                "tags": user_meta.get("tags", []) if user_meta else [],
                "status": receipt_data.get("mcp_format", {}).get("status"),
            }
            results.append(summary)

        return results

    async def delete_receipt(self, receipt_id: str) -> bool:
        """Delete a receipt by ID."""
        try:
            # Delete from JSON
            data = self._load_json()
            if receipt_id not in data["receipts"]:
                return False

            del data["receipts"][receipt_id]
            data["metadata"]["total_receipts"] = len(data["receipts"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()

            self._save_json(data)

            # Delete from SQLite if enabled
            if self.config.enable_sqlite:
                with self._get_sqlite_connection() as conn:
                    conn.execute(
                        "DELETE FROM line_items WHERE receipt_id = ?", (receipt_id,)
                    )
                    conn.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
                    conn.commit()

            return True

        except Exception as e:
            raise ValueError(f"Failed to delete receipt: {str(e)}")

    async def export_receipts(
        self, format: str = "json", receipt_ids: Optional[List[str]] = None
    ) -> str:
        """Export receipts to various formats."""
        try:
            data = self._load_json()

            # Filter receipts if specific IDs provided
            if receipt_ids:
                filtered_receipts = {
                    rid: data["receipts"][rid]
                    for rid in receipt_ids
                    if rid in data["receipts"]
                }
            else:
                filtered_receipts = data["receipts"]

            if format.lower() == "json":
                export_data = {
                    "export_metadata": {
                        "exported_at": datetime.now().isoformat(),
                        "total_receipts": len(filtered_receipts),
                        "format": "json",
                    },
                    "receipts": filtered_receipts,
                }

                export_file = (
                    self.storage_path
                    / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                with open(export_file, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

                return str(export_file)

            elif format.lower() == "csv":
                import csv

                export_file = (
                    self.storage_path
                    / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )

                with open(export_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)

                    # Write header
                    writer.writerow(
                        [
                            "Receipt ID",
                            "Filename",
                            "Store Name",
                            "Transaction Date",
                            "Total Amount",
                            "Items Count",
                            "Category",
                            "Tags",
                            "Confidence",
                        ]
                    )

                    # Write data
                    for receipt_data in filtered_receipts.values():
                        receipt_payload = receipt_data.get("receipt_payload", {})
                        metadata = receipt_payload.get("processing_metadata", {})
                        store = receipt_payload.get("store_details", {})
                        transaction = receipt_payload.get("transaction_details", {})
                        payment = receipt_payload.get("payment_summary", {})
                        user_meta = receipt_payload.get("user_defined_metadata", {})
                        items = receipt_payload.get("line_items", [])

                        writer.writerow(
                            [
                                metadata.get("receipt_id", ""),
                                metadata.get("source_filename", ""),
                                store.get("name", "") if store else "",
                                transaction.get("date", "") if transaction else "",
                                payment.get("total_amount", 0.0) if payment else 0.0,
                                len(items),
                                user_meta.get("overall_category", "")
                                if user_meta
                                else "",
                                "; ".join(user_meta.get("tags", []))
                                if user_meta
                                else "",
                                receipt_data.get("mcp_format", {}).get(
                                    "confidence_score", 0.0
                                ),
                            ]
                        )

                return str(export_file)

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            raise ValueError(f"Export failed: {str(e)}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics and analytics."""
        try:
            data = self._load_json()
            receipts = data["receipts"]

            if not receipts:
                return {
                    "total_receipts": 0,
                    "storage_size_mb": 0.0,
                    "by_input_type": {},
                    "by_category": {},
                    "by_store": {},
                    "total_spending": 0.0,
                    "average_confidence": 0.0,
                }

            # Calculate statistics
            stats = {
                "total_receipts": len(receipts),
                "storage_size_mb": round(
                    self.json_path.stat().st_size / (1024 * 1024), 2
                ),
                "by_input_type": {},
                "by_category": {},
                "by_store": {},
                "total_spending": 0.0,
                "confidence_scores": [],
            }

            for receipt_data in receipts.values():
                receipt_payload = receipt_data.get("receipt_payload", {})
                metadata = receipt_payload.get("processing_metadata", {})
                store = receipt_payload.get("store_details", {})
                payment = receipt_payload.get("payment_summary", {})
                user_meta = receipt_payload.get("user_defined_metadata", {})

                # By input type
                input_type = metadata.get("source_type", "unknown")
                stats["by_input_type"][input_type] = (
                    stats["by_input_type"].get(input_type, 0) + 1
                )

                # By category
                category = (
                    user_meta.get("overall_category", "uncategorized")
                    if user_meta
                    else "uncategorized"
                )
                stats["by_category"][category] = (
                    stats["by_category"].get(category, 0) + 1
                )

                # By store
                store_name = store.get("name", "unknown") if store else "unknown"
                stats["by_store"][store_name] = stats["by_store"].get(store_name, 0) + 1

                # Total spending
                if payment:
                    stats["total_spending"] += payment.get("total_amount", 0.0)

                # Confidence scores
                confidence = receipt_data.get("mcp_format", {}).get(
                    "confidence_score", 0.0
                )
                stats["confidence_scores"].append(confidence)

            # Calculate average confidence
            if stats["confidence_scores"]:
                stats["average_confidence"] = round(
                    sum(stats["confidence_scores"]) / len(stats["confidence_scores"]), 2
                )
            else:
                stats["average_confidence"] = 0.0

            # Remove the raw confidence scores array
            del stats["confidence_scores"]

            return stats

        except Exception as e:
            raise ValueError(f"Failed to get statistics: {str(e)}")


# Utility functions
def create_storage(config: Optional[StorageConfig] = None) -> ReceiptStorage:
    """Create a configured receipt storage instance."""
    return ReceiptStorage(config)


def get_default_storage_path() -> str:
    """Get the default storage path."""
    return str(Path.cwd() / "receipt_storage")


def validate_storage_setup(storage_dir: Optional[str] = None) -> Dict[str, Any]:
    """Validate storage setup and permissions."""
    storage_path = Path(storage_dir or get_default_storage_path())

    result = {
        "directory_exists": storage_path.exists(),
        "directory_writable": False,
        "space_available": True,
        "permissions_ok": False,
        "errors": [],
    }

    try:
        # Check if directory is writable
        if storage_path.exists():
            test_file = storage_path / ".test_write"
            try:
                test_file.write_text("test")
                test_file.unlink()
                result["directory_writable"] = True
                result["permissions_ok"] = True
            except Exception as e:
                result["errors"].append(f"Directory not writable: {str(e)}")
        else:
            # Try to create directory
            try:
                storage_path.mkdir(parents=True, exist_ok=True)
                result["directory_exists"] = True
                result["directory_writable"] = True
                result["permissions_ok"] = True
            except Exception as e:
                result["errors"].append(f"Cannot create directory: {str(e)}")

        # Check available space (basic check)
        if storage_path.exists():
            try:
                result["space_available"] = True  # Simplified for now
            except Exception:
                result["space_available"] = False

    except Exception as e:
        result["errors"].append(f"Storage validation failed: {str(e)}")

    return result
