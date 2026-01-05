#!/usr/bin/env python3
"""
StudioFlow SIMPLIFIED - Production Ready Video Project Manager
Refactored for immediate use - All core features, zero bloat
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# ==========================================
# CORE CONFIGURATION (Edit these for your setup)
# ==========================================

STORAGE_TIERS = {
    "ingest": Path("/mnt/ingest"),      # Hot - Camera dumps
    "active": Path("/mnt/resolve"),     # Active - Working projects
    "render": Path("/mnt/render"),      # Output - Final renders
    "library": Path("/mnt/library"),    # Assets - LUTs, templates
    "archive": Path("/mnt/archive")     # Cold - Completed projects
}

PROJECT_TEMPLATES = {
    "youtube": {
        "dirs": [
            "01_INGEST/FOOTAGE", "01_INGEST/AUDIO", "01_INGEST/GRAPHICS",
            "02_EDIT/TIMELINES", "02_EDIT/CACHE",
            "03_ASSETS/MUSIC", "03_ASSETS/SFX", "03_ASSETS/LUTS",
            "04_EXPORTS/DRAFTS", "04_EXPORTS/FINAL", "04_EXPORTS/THUMBNAILS",
            "05_DOCUMENTS/SCRIPTS", "05_DOCUMENTS/NOTES"
        ]
    },
    "ai_comparison": {
        "dirs": [
            "01_CAPTURES/ChatGPT", "01_CAPTURES/Claude", "01_CAPTURES/Gemini",
            "02_SCREEN_RECORDINGS", "03_COMPARISONS/GRIDS",
            "04_EDIT/TIMELINES", "05_EXPORTS/FINAL",
            "06_METADATA/SCORES", "06_METADATA/ANALYSIS"
        ]
    },
    "tutorial": {
        "dirs": [
            "01_SCREEN_CAPTURES/STEPS", "02_NARRATION/VO",
            "03_EDIT/TIMELINE", "04_GRAPHICS/OVERLAYS",
            "05_EXPORTS/CHAPTERS", "05_EXPORTS/FINAL"
        ]
    },
    "minimal": {
        "dirs": ["FOOTAGE", "EDIT", "EXPORT"]
    }
}

# ==========================================
# SIMPLIFIED PROJECT MANAGER
# ==========================================

class StudioFlow:
    """Simplified StudioFlow - Just what you need, nothing more"""

    def __init__(self):
        self.projects_dir = STORAGE_TIERS["active"] / "Projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, name: str, template: str = "youtube") -> Path:
        """Create a new project with template"""
        # Clean project name
        clean_name = "".join(c for c in name if c.isalnum() or c in " -_").strip()
        clean_name = clean_name.replace(" ", "_")

        # Add date prefix for organization
        date_prefix = datetime.now().strftime("%Y%m%d")
        project_name = f"{date_prefix}_{clean_name}"

        # Create project directory
        project_path = self.projects_dir / project_name
        if project_path.exists():
            print(f"⚠️  Project {project_name} already exists!")
            return project_path

        project_path.mkdir(parents=True)

        # Apply template
        template_config = PROJECT_TEMPLATES.get(template, PROJECT_TEMPLATES["minimal"])
        for dir_path in template_config["dirs"]:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Create project metadata
        metadata = {
            "name": clean_name,
            "created": datetime.now().isoformat(),
            "template": template,
            "storage_tier": "active",
            "status": "in_progress"
        }

        with open(project_path / ".studioflow.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # Create README
        with open(project_path / "README.md", "w") as f:
            f.write(f"# {name}\n\n")
            f.write(f"Created: {metadata['created']}\n")
            f.write(f"Template: {template}\n\n")
            f.write("## Notes\n\n")
            f.write("## Tasks\n- [ ] Import footage\n- [ ] Edit timeline\n- [ ] Export final\n")

        # Initialize git
        try:
            subprocess.run(["git", "init"], cwd=project_path, capture_output=True)

            # Create .gitignore
            gitignore = """
*.cache
*.tmp
*_cache/
CACHE/
*.mov
*.mp4
*.mkv
*.avi
*.wav
*.aif
"""
            with open(project_path / ".gitignore", "w") as f:
                f.write(gitignore)

            subprocess.run(["git", "add", "."], cwd=project_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial project setup"],
                         cwd=project_path, capture_output=True)
        except:
            pass  # Git optional

        # Create DaVinci Resolve project file
        resolve_file = project_path / f"{clean_name}.drp"
        resolve_file.touch()

        # Create symlinks for quick access
        self._create_symlinks(project_path)

        print(f"✅ Created project: {project_name}")
        print(f"📁 Location: {project_path}")
        print(f"📋 Template: {template}")

        return project_path

    def _create_symlinks(self, project_path: Path):
        """Create helpful symlinks"""
        # Link to shared assets
        luts_link = project_path / "03_ASSETS" / "SHARED_LUTS"
        if not luts_link.exists() and (project_path / "03_ASSETS").exists():
            try:
                luts_link.symlink_to(STORAGE_TIERS["library"] / "LUTs")
            except:
                pass

    def list_projects(self, status: Optional[str] = None):
        """List all projects"""
        projects = []

        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / ".studioflow.json"
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        if not status or metadata.get("status") == status:
                            projects.append({
                                "name": project_dir.name,
                                "created": metadata.get("created", "Unknown"),
                                "template": metadata.get("template", "Unknown"),
                                "status": metadata.get("status", "Unknown")
                            })

        # Sort by creation date (newest first)
        projects.sort(key=lambda x: x["created"], reverse=True)

        print("\n📂 StudioFlow Projects")
        print("=" * 60)
        for p in projects[:10]:  # Show last 10
            status_icon = "🟢" if p["status"] == "in_progress" else "✅"
            print(f"{status_icon} {p['name']}")
            print(f"   Template: {p['template']} | Created: {p['created'][:10]}")

        if len(projects) > 10:
            print(f"\n   ...and {len(projects) - 10} more projects")

    def quick_capture(self, name: Optional[str] = None):
        """Quick screenshot capture"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png" if name else f"{timestamp}.png"

        capture_dir = STORAGE_TIERS["ingest"] / "captures" / "today"
        capture_dir.mkdir(parents=True, exist_ok=True)

        filepath = capture_dir / filename

        # Use gnome-screenshot
        subprocess.run(["gnome-screenshot", "-f", str(filepath)])
        print(f"📸 Captured: {filepath}")

        return filepath

    def organize_captures(self, project_name: Optional[str] = None):
        """Move today's captures to project"""
        if not project_name:
            # Use most recent project
            projects = sorted(self.projects_dir.iterdir(), key=lambda x: x.stat().st_mtime)
            if projects:
                project_name = projects[-1].name
            else:
                print("❌ No projects found")
                return

        project_path = self.projects_dir / project_name
        if not project_path.exists():
            print(f"❌ Project {project_name} not found")
            return

        source = STORAGE_TIERS["ingest"] / "captures" / "today"
        if not source.exists():
            print("❌ No captures to organize")
            return

        # Find appropriate destination
        dest = project_path / "01_INGEST" / "CAPTURES"
        if not dest.exists():
            dest = project_path / "01_CAPTURES"
            if not dest.exists():
                dest = project_path / "CAPTURES"
                if not dest.exists():
                    dest = project_path

        moved = 0
        for file in source.glob("*"):
            if file.is_file():
                shutil.move(str(file), dest / file.name)
                moved += 1

        print(f"✅ Moved {moved} captures to {project_name}")

    def status(self):
        """Show system status"""
        print("\n🎬 StudioFlow Status")
        print("=" * 60)

        # Storage status
        print("\n💾 Storage Tiers:")
        for tier, path in STORAGE_TIERS.items():
            if path.exists():
                # Get disk usage
                stat = shutil.disk_usage(path)
                used_gb = (stat.used / (1024**3))
                total_gb = (stat.total / (1024**3))
                percent = (stat.used / stat.total) * 100

                icon = "🟢" if percent < 70 else "🟡" if percent < 90 else "🔴"
                print(f"  {icon} {tier:10} {used_gb:6.1f}/{total_gb:6.1f} GB ({percent:3.0f}%)")

        # Project count
        project_count = len(list(self.projects_dir.iterdir()))
        print(f"\n📁 Projects: {project_count} total")

        # Recent activity
        recent = sorted(self.projects_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        if recent:
            print("\n🕐 Recent Projects:")
            for p in recent:
                print(f"  • {p.name}")

# ==========================================
# CLI INTERFACE
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="StudioFlow SIMPLIFIED - Video Project Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  studioflow create "My YouTube Video"
  studioflow create "AI Comparison" --template ai_comparison
  studioflow list
  studioflow capture
  studioflow organize
  studioflow status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--template", "-t", default="youtube",
                              choices=list(PROJECT_TEMPLATES.keys()),
                              help="Project template")

    # List command
    list_parser = subparsers.add_parser("list", help="List projects")
    list_parser.add_argument("--status", help="Filter by status")

    # Capture command
    capture_parser = subparsers.add_parser("capture", help="Quick capture")
    capture_parser.add_argument("name", nargs="?", help="Capture name")

    # Organize command
    org_parser = subparsers.add_parser("organize", help="Organize captures")
    org_parser.add_argument("project", nargs="?", help="Target project")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show status")

    args = parser.parse_args()

    # Initialize StudioFlow
    sf = StudioFlow()

    # Execute command
    if args.command == "create":
        sf.create_project(args.name, args.template)
    elif args.command == "list":
        sf.list_projects(args.status)
    elif args.command == "capture":
        sf.quick_capture(args.name)
    elif args.command == "organize":
        sf.organize_captures(args.project)
    elif args.command == "status":
        sf.status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()