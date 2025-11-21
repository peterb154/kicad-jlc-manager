"""Configuration management for jlcproject.toml."""

from pathlib import Path
from typing import Dict, Optional
import tomllib  # Python 3.11+
import json


class ProjectConfig:
    """Manages jlcproject.toml configuration file."""

    def __init__(self, project_root: Path):
        """Initialize with project root directory."""
        self.project_root = project_root
        self.config_file = project_root / "jlcproject.toml"
        self._config: Optional[Dict] = None

    def load(self) -> Dict:
        """Load configuration from jlcproject.toml."""
        if not self.config_file.exists():
            self._config = self._get_default_config()
            return self._config

        # Always reload from disk to get latest changes
        with open(self.config_file, "rb") as f:
            self._config = tomllib.load(f)
        return self._config

    def save(self):
        """Save configuration to jlcproject.toml."""
        if self._config is None:
            return

        # Simple TOML writing
        # Write components at root level FIRST, before any sections
        with open(self.config_file, "w") as f:
            f.write("components = [\n")
            components = self._config.get("components", {})
            for jlc_id, description in components.items():
                if description:
                    # Write with inline comment
                    f.write(f'    "{jlc_id}",  # {description}\n')
                else:
                    # No description
                    f.write(f'    "{jlc_id}",\n')
            f.write("]\n\n")

            f.write("[project]\n")
            # Only write project-specific keys
            for key, value in self._config.get("project", {}).items():
                if key != "components":  # Skip if accidentally included
                    f.write(f'{key} = "{value}"\n')

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "project": {
                "lib-dir": "jlclib",
                "lib-name": "JLC_Project",
            },
            "components": {},  # Dict of jlc_id -> optional description
        }

    def get_lib_dir(self) -> str:
        """Get configured library directory."""
        config = self.load()
        return config.get("project", {}).get("lib-dir", "jlclib")

    def get_lib_name(self) -> str:
        """Get configured library name."""
        config = self.load()
        return config.get("project", {}).get("lib-name", "JLC_Project")

    def get_components(self) -> list[str]:
        """Get list of component JLC IDs."""
        config = self.load()
        components = config.get("components", {})
        # Handle both old list format and new dict format
        if isinstance(components, list):
            return components
        return list(components.keys())

    def add_component(self, jlc_id: str, description: str = ""):
        """Add a component to the configuration with optional description."""
        config = self.load()
        if "components" not in config:
            config["components"] = {}
        # Handle old list format - convert to dict
        if isinstance(config["components"], list):
            old_list = config["components"]
            config["components"] = {comp: "" for comp in old_list}

        config["components"][jlc_id] = description
        self._config = config
        self.save()

    def remove_component(self, jlc_id: str):
        """Remove a component from the configuration."""
        config = self.load()
        components = config.get("components", {})
        # Handle both list and dict format
        if isinstance(components, list):
            if jlc_id in components:
                components.remove(jlc_id)
        elif isinstance(components, dict):
            if jlc_id in components:
                del components[jlc_id]

        config["components"] = components
        self._config = config
        self.save()

    def ensure_gitignore(self):
        """Ensure .gitignore excludes jlclib/ directory."""
        gitignore = self.project_root / ".gitignore"
        lib_dir = self.get_lib_dir()

        # Read existing .gitignore or create new content
        if gitignore.exists():
            content = gitignore.read_text()
            lines = content.splitlines()
        else:
            lines = []

        # Check if jlclib is already ignored
        if lib_dir not in lines and f"{lib_dir}/" not in lines:
            # Add with helpful comment
            if lines and lines[-1] != "":
                lines.append("")  # Add blank line
            lines.append("# JLC component libraries (generated)")
            lines.append(f"{lib_dir}/")
            gitignore.write_text("\n".join(lines) + "\n")
