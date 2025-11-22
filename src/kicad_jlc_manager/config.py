"""Configuration management for jlcproject.toml."""

import tomllib  # Python 3.11+
from pathlib import Path


class ProjectConfig:
    """Manages jlcproject.toml configuration file."""

    def __init__(self, project_root: Path):
        """Initialize with project root directory."""
        self.project_root = project_root
        self.config_file = project_root / "jlcproject.toml"
        self._config: dict | None = None

    def load(self) -> dict:
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

            # Convert to list if dict (for backward compatibility)
            if isinstance(components, dict):
                components = list(components.keys())

            for jlc_id in components:
                f.write(f'    "{jlc_id}",\n')
            f.write("]\n\n")

            f.write("[project]\n")
            # Only write project-specific keys
            for key, value in self._config.get("project", {}).items():
                if key != "components":  # Skip if accidentally included
                    f.write(f'{key} = "{value}"\n')

    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            "project": {
                "lib-dir": "jlclib",
                "lib-name": "JLC_Project",
            },
            "components": [],  # List of JLC IDs
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
        components = config.get("components", [])
        # Handle both list and dict format (dict for backward compatibility)
        if isinstance(components, dict):
            return list(components.keys())
        return components

    def get_components_with_descriptions(self) -> dict[str, str]:
        """
        Get components with their descriptions by parsing the TOML file.

        Returns dict of {jlc_id: description}. Description will be empty string
        if no inline comment exists.
        """
        if not self.config_file.exists():
            return {}

        components_dict = {}
        content = self.config_file.read_text()
        lines = content.splitlines()

        in_components_array = False
        for line in lines:
            stripped = line.strip()

            # Detect start of components array
            if stripped.startswith("components"):
                in_components_array = True
                continue

            # Detect end of components array
            if in_components_array and stripped.startswith("["):
                break

            # Parse component lines
            if in_components_array and stripped.startswith('"'):
                # Extract JLC ID
                if '"' in stripped:
                    parts = stripped.split('"')
                    if len(parts) >= 2:
                        jlc_id = parts[1]

                        # Extract description from inline comment
                        description = ""
                        if "#" in stripped:
                            comment_part = stripped.split("#", 1)[1].strip()
                            description = comment_part

                        components_dict[jlc_id] = description

        return components_dict

    def add_component(self, jlc_id: str):
        """Add a component to the configuration."""
        config = self.load()
        if "components" not in config:
            config["components"] = []

        # Convert dict to list if needed (backward compatibility)
        if isinstance(config["components"], dict):
            config["components"] = list(config["components"].keys())

        # Add component if not already present
        if jlc_id not in config["components"]:
            config["components"].append(jlc_id)

        self._config = config
        self.save()

    def remove_component(self, jlc_id: str) -> bool:
        """Remove a component from the configuration.

        Returns:
            True if component was found and removed, False otherwise
        """
        config = self.load()
        components = config.get("components", [])

        # Convert dict to list if needed (backward compatibility)
        if isinstance(components, dict):
            components = list(components.keys())

        found = jlc_id in components
        if found:
            components.remove(jlc_id)
            config["components"] = components
            self._config = config
            self.save()

        return found

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
