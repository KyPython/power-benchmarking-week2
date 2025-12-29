"""
Storage Service

Provides JSON-based storage for business data (clients, invoices, etc.).
Can be upgraded to database storage in the future.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """JSON-based storage service for business data."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize storage service.

        Args:
            storage_path: Path to storage directory (default: ~/.power_benchmarking/data)
        """
        if storage_path is None:
            storage_path = Path.home() / ".power_benchmarking" / "data"
        else:
            storage_path = Path(storage_path)

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Storage service initialized at: {self.storage_path}")

    def _get_file_path(self, collection: str) -> Path:
        """Get file path for a collection."""
        return self.storage_path / f"{collection}.json"

    def _load_collection(self, collection: str) -> List[Dict[str, Any]]:
        """Load a collection from JSON file."""
        file_path = self._get_file_path(collection)

        if not file_path.exists():
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading collection {collection}: {e}")
            return []

    def _save_collection(self, collection: str, data: List[Dict[str, Any]]) -> bool:
        """Save a collection to JSON file."""
        file_path = self._get_file_path(collection)

        try:
            # Create backup
            if file_path.exists():
                backup_path = file_path.with_suffix(".json.backup")
                file_path.rename(backup_path)

            # Write new data
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Remove backup if successful
            backup_path = file_path.with_suffix(".json.backup")
            if backup_path.exists():
                backup_path.unlink()

            return True
        except IOError as e:
            logger.error(f"Error saving collection {collection}: {e}")
            # Restore backup if available
            backup_path = file_path.with_suffix(".json.backup")
            if backup_path.exists():
                backup_path.rename(file_path)
            return False

    def create(self, collection: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new item in a collection.

        Args:
            collection: Collection name (e.g., 'clients', 'invoices')
            item: Item data (will be assigned an ID and timestamps)

        Returns:
            Created item with ID and timestamps
        """
        data = self._load_collection(collection)

        # Generate ID if not provided
        if "id" not in item:
            item["id"] = self._generate_id(collection)

        # Add timestamps
        now = datetime.utcnow().isoformat()
        item["createdAt"] = now
        item["updatedAt"] = now

        data.append(item)

        if self._save_collection(collection, data):
            logger.info(f"Created {collection} item: {item.get('id')}")
            return item
        else:
            raise IOError(f"Failed to save {collection}")

    def get(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item by ID."""
        data = self._load_collection(collection)
        for item in data:
            if item.get("id") == item_id:
                return item
        return None

    def get_all(
        self, collection: str, filter_func: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all items in a collection, optionally filtered.

        Args:
            collection: Collection name
            filter_func: Optional filter function (item) -> bool

        Returns:
            List of items
        """
        data = self._load_collection(collection)

        if filter_func:
            return [item for item in data if filter_func(item)]

        return data

    def update(
        self, collection: str, item_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an item."""
        data = self._load_collection(collection)

        for item in data:
            if item.get("id") == item_id:
                item.update(updates)
                item["updatedAt"] = datetime.utcnow().isoformat()

                if self._save_collection(collection, data):
                    logger.info(f"Updated {collection} item: {item_id}")
                    return item
                else:
                    raise IOError(f"Failed to save {collection}")

        return None

    def delete(self, collection: str, item_id: str) -> bool:
        """Delete an item."""
        data = self._load_collection(collection)

        original_length = len(data)
        data = [item for item in data if item.get("id") != item_id]

        if len(data) < original_length:
            if self._save_collection(collection, data):
                logger.info(f"Deleted {collection} item: {item_id}")
                return True
            else:
                raise IOError(f"Failed to save {collection}")

        return False

    def _generate_id(self, collection: str) -> str:
        """Generate a unique ID for a collection."""
        data = self._load_collection(collection)
        existing_ids = {item.get("id") for item in data if "id" in item}

        # Simple ID generation: collection prefix + timestamp + random
        import time
        import random

        while True:
            id_suffix = f"{int(time.time() * 1000)}{random.randint(100, 999)}"
            new_id = f"{collection[:3]}_{id_suffix}"

            if new_id not in existing_ids:
                return new_id

