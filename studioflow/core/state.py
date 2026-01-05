"""
State Management for CLI Context
Tracks current project and session state
"""

from typing import Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime


class StateManager:
    """Manages CLI session state"""

    def __init__(self):
        self.state_file = Path.home() / ".studioflow" / ".state"
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_state(self):
        """Save state to file"""
        self.state_file.parent.mkdir(exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self._state, f, indent=2, default=str)

    @property
    def current_project(self) -> Optional[str]:
        """Get current project name"""
        return self._state.get("current_project")

    @current_project.setter
    def current_project(self, name: str):
        """Set current project"""
        self._state["current_project"] = name
        self._state["last_modified"] = datetime.now().isoformat()
        self._save_state()

    @property
    def last_import_path(self) -> Optional[Path]:
        """Get last import path"""
        path = self._state.get("last_import_path")
        return Path(path) if path else None

    @last_import_path.setter
    def last_import_path(self, path: Path):
        """Set last import path"""
        self._state["last_import_path"] = str(path)
        self._save_state()

    def add_recent_project(self, name: str):
        """Add to recent projects list"""
        recent = self._state.get("recent_projects", [])
        if name in recent:
            recent.remove(name)
        recent.insert(0, name)
        self._state["recent_projects"] = recent[:10]  # Keep last 10
        self._save_state()

    def get_recent_projects(self) -> list:
        """Get recent projects"""
        return self._state.get("recent_projects", [])