#!/usr/bin/env python3
"""
Premium Features Module

Handles premium feature checks, cloud sync, team collaboration, and advanced analytics.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import hashlib

PREMIUM_CONFIG_FILE = Path.home() / ".power_benchmarking" / "premium_config.json"
CLOUD_SYNC_DIR = Path.home() / ".power_benchmarking" / "cloud_sync"
TEAM_COLLAB_DIR = Path.home() / ".power_benchmarking" / "team_collab"

try:
    import requests  # server-side verification
except Exception:
    requests = None


class PremiumFeatures:
    """Premium features manager."""

    def __init__(self):
        self.config = self._load_config()
        self.tier = self.config.get("tier", "free")
        self.features = self.config.get("features", {})

    def _load_config(self) -> Dict:
        """Load premium configuration."""
        if PREMIUM_CONFIG_FILE.exists():
            try:
                with open(PREMIUM_CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"tier": "free", "features": {}}

    def is_premium(self) -> bool:
        """Check if user has premium subscription.
        Treat presence of Polar API key as entitled.
        """
        lic = (self.config or {}).get("licensing") or {}
        if lic.get("polar_api_key"):
            return True
        return self.tier == "premium"

    def verify_polar_entitlement(self) -> bool:
        """Verify entitlement against Polar API (non-blocking fallback to local state).
        Writes verification result back to config when successful.
        """
        lic = (self.config or {}).get("licensing") or {}
        token = lic.get("polar_api_key") or lic.get("polar_token")
        if not token or requests is None:
            return False
        try:
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            # Attempt subscriptions endpoint; treat any active subscription as premium
            url = "https://api.polar.sh/v1/subscriptions"
            resp = requests.get(url, params={"status": "active"}, headers=headers, timeout=8)
            if resp.status_code == 200 and isinstance(resp.json(), dict):
                data = resp.json()
                items = data.get("items") or data.get("data") or []
                if items:
                    # Persist verification
                    self.tier = "premium"
                    self.features = {
                        "cloud_sync": True,
                        "team_collaboration": True,
                        "advanced_analytics": True,
                    }
                    new_cfg = dict(self.config)
                    new_cfg["tier"] = self.tier
                    new_cfg["features"] = self.features
                    ver = new_cfg.setdefault("verification", {})
                    ver.update({"source": "polar", "verified": True, "verified_at": datetime.now().isoformat()})
                    with open(PREMIUM_CONFIG_FILE, "w") as f:
                        json.dump(new_cfg, f, indent=2)
                    self.config = new_cfg
                    return True
            return False
        except Exception:
            return False

    def has_feature(self, feature: str) -> bool:
        """Check if a specific premium feature is available."""
        if not self.is_premium():
            return False
        return self.features.get(feature, False)

    def cloud_sync_enabled(self) -> bool:
        """Check if cloud sync is enabled."""
        return self.has_feature("cloud_sync")

    def team_collaboration_enabled(self) -> bool:
        """Check if team collaboration is enabled."""
        return self.has_feature("team_collaboration")

    def advanced_analytics_enabled(self) -> bool:
        """Check if advanced analytics is enabled."""
        return self.has_feature("advanced_analytics")

    def sync_to_cloud(self, file_path: Path, metadata: Optional[Dict] = None) -> bool:
        """Sync a file to cloud storage (premium feature)."""
        if not self.cloud_sync_enabled():
            return False

        try:
            CLOUD_SYNC_DIR.mkdir(parents=True, exist_ok=True)

            # Create metadata
            file_metadata = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
                "sync_timestamp": datetime.now().isoformat(),
                "file_hash": self._calculate_file_hash(file_path) if file_path.exists() else None,
            }
            if metadata:
                file_metadata.update(metadata)

            # Save metadata
            metadata_file = CLOUD_SYNC_DIR / f"{file_path.stem}_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(file_metadata, f, indent=2)

            # Copy file to cloud sync directory (simplified - would use actual cloud storage in production)
            if file_path.exists():
                import shutil

                cloud_file = CLOUD_SYNC_DIR / file_path.name
                shutil.copy2(file_path, cloud_file)

            return True
        except Exception as e:
            print(f"⚠️  Cloud sync error: {e}")
            return False

    def get_team_shared_data(self, team_id: Optional[str] = None) -> List[Dict]:
        """Get team-shared data (premium feature)."""
        if not self.team_collaboration_enabled():
            return []

        try:
            TEAM_COLLAB_DIR.mkdir(parents=True, exist_ok=True)

            shared_files = []
            for file_path in TEAM_COLLAB_DIR.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        if team_id is None or data.get("team_id") == team_id:
                            shared_files.append(data)
                except Exception:
                    continue

            return shared_files
        except Exception:
            return []

    def share_with_team(self, data: Dict, team_id: str) -> bool:
        """Share data with team (premium feature)."""
        if not self.team_collaboration_enabled():
            return False

        try:
            TEAM_COLLAB_DIR.mkdir(parents=True, exist_ok=True)

            share_data = {
                "team_id": team_id,
                "shared_by": os.getenv("USER", "unknown"),
                "shared_timestamp": datetime.now().isoformat(),
                "data": data,
            }

            # Save shared data
            share_file = (
                TEAM_COLLAB_DIR / f"{team_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(share_file, "w") as f:
                json.dump(share_data, f, indent=2)

            return True
        except Exception as e:
            print(f"⚠️  Team share error: {e}")
            return False

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def get_premium_features() -> PremiumFeatures:
    """Get premium features instance."""
    return PremiumFeatures()

