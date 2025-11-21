"""KiCad project detection and management."""

from pathlib import Path
from typing import Optional


class KiCadProject:
    """Represents a KiCad project with its associated files and structure."""

    def __init__(self, root_dir: Path):
        """Initialize with project root directory."""
        self.root_dir = root_dir
        self.project_file = self._find_project_file()

    def _find_project_file(self) -> Optional[Path]:
        """Find the .kicad_pro file in the project directory."""
        pro_files = list(self.root_dir.glob("*.kicad_pro"))
        if pro_files:
            return pro_files[0]
        return None

    @property
    def is_valid(self) -> bool:
        """Check if this is a valid KiCad project."""
        return self.project_file is not None

    @property
    def name(self) -> str:
        """Get the project name."""
        if self.project_file:
            return self.project_file.stem
        return "unknown"

    def get_lib_dir(self, custom_dir: Optional[str] = None) -> Path:
        """Get the library directory path (jlclib/ by default)."""
        if custom_dir:
            return self.root_dir / custom_dir
        return self.root_dir / "jlclib"

    def get_symbol_lib_path(self, lib_dir: Optional[Path] = None) -> Path:
        """Get the symbol library file path."""
        if lib_dir is None:
            lib_dir = self.get_lib_dir()
        return lib_dir / "symbol" / "jlc_project.kicad_sym"

    def get_footprint_lib_path(self, lib_dir: Optional[Path] = None) -> Path:
        """Get the footprint library directory path."""
        if lib_dir is None:
            lib_dir = self.get_lib_dir()
        return lib_dir / "footprint"

    def get_3dmodel_lib_path(self, lib_dir: Optional[Path] = None) -> Path:
        """Get the 3D model library directory path."""
        if lib_dir is None:
            lib_dir = self.get_lib_dir()
        return lib_dir / "3dmodels"

    def ensure_lib_structure(self, lib_dir: Optional[Path] = None):
        """Create the library directory structure if it doesn't exist."""
        if lib_dir is None:
            lib_dir = self.get_lib_dir()

        # Create directories
        symbol_dir = lib_dir / "symbol"
        footprint_dir = lib_dir / "footprint"
        model_dir = lib_dir / "3dmodels"

        symbol_dir.mkdir(parents=True, exist_ok=True)
        footprint_dir.mkdir(parents=True, exist_ok=True)
        model_dir.mkdir(parents=True, exist_ok=True)

        # Create empty symbol library if it doesn't exist
        symbol_file = self.get_symbol_lib_path(lib_dir)
        if not symbol_file.exists():
            symbol_file.write_text(
                "(kicad_symbol_lib (version 20210201) (generator kicad-jlc-manager)\n)\n"
            )


def find_kicad_project(start_dir: Optional[Path] = None) -> Optional[KiCadProject]:
    """
    Find a KiCad project by searching upward from the start directory.

    Args:
        start_dir: Directory to start searching from (default: current directory)

    Returns:
        KiCadProject if found, None otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    # Search upward through parent directories
    while current != current.parent:
        project = KiCadProject(current)
        if project.is_valid:
            return project
        current = current.parent

    # Check the root directory
    project = KiCadProject(current)
    if project.is_valid:
        return project

    return None
