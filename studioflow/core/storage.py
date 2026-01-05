"""
Storage tier management system
Ported from sfcore.py for optimized video production storage
"""

import shutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class StorageTierSystem:
    """6-tier storage management for video production workflow"""

    # Default storage tiers - can be overridden by config
    DEFAULT_TIERS = {
        "ingest": {
            "path": Path("/mnt/ingest"),
            "description": "SD card dumps, raw footage",
            "retention_days": 7,
            "auto_archive": True
        },
        "active": {
            "path": Path("/mnt/studio/PROJECTS"),
            "description": "Current editing projects",
            "retention_days": 30,
            "auto_archive": True
        },
        "render": {
            "path": Path("/mnt/render"),
            "description": "Export and render outputs",
            "retention_days": 14,
            "auto_archive": False
        },
        "studio": {
            "path": Path("/mnt/studio"),
            "description": "Resolve projects workspace, reusable assets, music, templates",
            "retention_days": None,  # Permanent
            "auto_archive": False
        },
        "archive": {
            "path": Path("/mnt/archive"),
            "description": "Long-term storage, completed projects",
            "retention_days": None,  # Permanent
            "auto_archive": False
        },
        "nas": {
            "path": Path("/mnt/nas"),
            "description": "Network backup, cloud sync",
            "retention_days": None,  # Permanent
            "auto_archive": False
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize storage tier system with optional config"""
        self.tiers = self.DEFAULT_TIERS.copy()

        # Load custom config if provided
        if config_path and config_path.exists():
            self._load_config(config_path)

        # Create tier directories if they don't exist
        self._initialize_tiers()

    def _load_config(self, config_path: Path):
        """Load custom tier configuration"""
        try:
            with open(config_path) as f:
                config = json.load(f)

            for tier_name, tier_config in config.get("storage_tiers", {}).items():
                if tier_name in self.tiers:
                    # Update existing tier
                    if "path" in tier_config:
                        self.tiers[tier_name]["path"] = Path(tier_config["path"])
                    if "retention_days" in tier_config:
                        self.tiers[tier_name]["retention_days"] = tier_config["retention_days"]
                    if "auto_archive" in tier_config:
                        self.tiers[tier_name]["auto_archive"] = tier_config["auto_archive"]
                else:
                    # Add new custom tier
                    self.tiers[tier_name] = {
                        "path": Path(tier_config["path"]),
                        "description": tier_config.get("description", "Custom tier"),
                        "retention_days": tier_config.get("retention_days"),
                        "auto_archive": tier_config.get("auto_archive", False)
                    }
        except Exception:
            pass  # Use defaults if config loading fails

    def _initialize_tiers(self):
        """Create tier directories if they don't exist"""
        for tier_name, tier_config in self.tiers.items():
            path = tier_config["path"]
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    # Skip if we don't have permissions
                    pass

    def get_tier_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all storage tiers"""
        status = {}

        for tier_name, tier_config in self.tiers.items():
            path = tier_config["path"]

            if path.exists():
                # Calculate disk usage
                total, used, free = shutil.disk_usage(path)

                # Count files and calculate total size
                file_count = 0
                total_size = 0
                try:
                    for item in path.rglob("*"):
                        if item.is_file():
                            file_count += 1
                            total_size += item.stat().st_size
                except PermissionError:
                    pass

                status[tier_name] = {
                    "exists": True,
                    "path": str(path),
                    "description": tier_config["description"],
                    "file_count": file_count,
                    "total_size_gb": round(total_size / (1024**3), 2),
                    "disk_total_gb": round(total / (1024**3), 2),
                    "disk_used_gb": round(used / (1024**3), 2),
                    "disk_free_gb": round(free / (1024**3), 2),
                    "disk_usage_percent": round((used / total) * 100, 1),
                    "retention_days": tier_config["retention_days"],
                    "auto_archive": tier_config["auto_archive"]
                }
            else:
                status[tier_name] = {
                    "exists": False,
                    "path": str(path),
                    "description": tier_config["description"],
                    "error": "Path does not exist"
                }

        return status

    def move_to_tier(self, source_path: Path, tier_name: str, preserve_structure: bool = True) -> Dict[str, Any]:
        """
        Move files to specified storage tier

        Args:
            source_path: Source file or directory
            tier_name: Target tier name
            preserve_structure: Keep directory structure

        Returns:
            Result dictionary with success status
        """
        if tier_name not in self.tiers:
            return {"success": False, "error": f"Unknown tier: {tier_name}"}

        target_tier = self.tiers[tier_name]
        target_base = target_tier["path"]

        if not target_base.exists():
            return {"success": False, "error": f"Tier path does not exist: {target_base}"}

        if not source_path.exists():
            return {"success": False, "error": f"Source does not exist: {source_path}"}

        try:
            if preserve_structure:
                # Keep relative path structure
                if source_path.is_file():
                    relative_path = source_path.name
                else:
                    relative_path = source_path.name

                target_path = target_base / relative_path
            else:
                # Flatten to tier root
                target_path = target_base / source_path.name

            # Create parent directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file/directory
            shutil.move(str(source_path), str(target_path))

            return {
                "success": True,
                "source": str(source_path),
                "destination": str(target_path),
                "tier": tier_name
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def archive_old_files(self, tier_name: str = "active", dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Archive old files based on retention policy

        Args:
            tier_name: Tier to check for old files
            dry_run: If True, only report what would be archived

        Returns:
            List of archived files
        """
        if tier_name not in self.tiers:
            return []

        tier_config = self.tiers[tier_name]
        if not tier_config["auto_archive"] or tier_config["retention_days"] is None:
            return []

        source_path = tier_config["path"]
        if not source_path.exists():
            return []

        archive_tier = self.tiers.get("archive")
        if not archive_tier:
            return []

        cutoff_date = datetime.now() - timedelta(days=tier_config["retention_days"])
        archived_files = []

        try:
            for item in source_path.rglob("*"):
                if item.is_file():
                    # Check modification time
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < cutoff_date:
                        file_info = {
                            "file": str(item),
                            "age_days": (datetime.now() - mtime).days,
                            "size_mb": round(item.stat().st_size / (1024**2), 2)
                        }

                        if not dry_run:
                            # Actually archive the file
                            result = self.move_to_tier(item, "archive", preserve_structure=True)
                            file_info["archived"] = result["success"]
                        else:
                            file_info["would_archive"] = True

                        archived_files.append(file_info)

        except Exception:
            pass

        return archived_files

    def optimize_storage(self) -> Dict[str, Any]:
        """
        Run storage optimization across all tiers

        Returns:
            Optimization results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "tiers_processed": [],
            "files_archived": 0,
            "space_freed_gb": 0,
            "errors": []
        }

        for tier_name, tier_config in self.tiers.items():
            if tier_config["auto_archive"]:
                try:
                    # Archive old files
                    archived = self.archive_old_files(tier_name, dry_run=False)

                    if archived:
                        results["tiers_processed"].append(tier_name)
                        results["files_archived"] += len(archived)

                        # Calculate space freed
                        space_freed = sum(f.get("size_mb", 0) for f in archived)
                        results["space_freed_gb"] += space_freed / 1024

                except Exception as e:
                    results["errors"].append({
                        "tier": tier_name,
                        "error": str(e)
                    })

        return results

    def suggest_tier(self, file_path: Path, file_type: Optional[str] = None) -> str:
        """
        Suggest appropriate storage tier for a file

        Args:
            file_path: File to analyze
            file_type: Optional file type hint

        Returns:
            Suggested tier name
        """
        if not file_path.exists():
            return "ingest"  # New files go to ingest

        # Check file extension
        ext = file_path.suffix.lower()

        # Media files
        if ext in [".mp4", ".mov", ".avi", ".mkv", ".mxf"]:
            # Check age
            age_days = (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days

            if age_days < 7:
                return "active"  # Recent files are active
            elif age_days < 30:
                return "render"  # Older renders
            else:
                return "archive"  # Old files to archive

        # Project files
        elif ext in [".drp", ".fcpxml", ".prproj", ".aep"]:
            return "active"  # Project files stay active

        # Assets
        elif ext in [".png", ".jpg", ".wav", ".mp3", ".cube", ".svg"]:
            return "studio"  # Reusable assets

        # Documents
        elif ext in [".txt", ".md", ".pdf", ".docx"]:
            return "studio"  # Documentation

        # Based on file type hint
        if file_type:
            if file_type in ["raw", "footage", "import"]:
                return "ingest"
            elif file_type in ["project", "edit", "working"]:
                return "active"
            elif file_type in ["export", "render", "output"]:
                return "render"
            elif file_type in ["asset", "template", "music"]:
                return "studio"
            elif file_type in ["backup", "old", "complete"]:
                return "archive"

        # Default
        return "ingest"

    def get_tier_path(self, tier_name: str) -> Optional[Path]:
        """Get path for a specific tier"""
        tier = self.tiers.get(tier_name)
        return tier["path"] if tier else None