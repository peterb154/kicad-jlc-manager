"""Component management utilities."""

import re
from pathlib import Path
from typing import Set


def get_installed_components(symbol_file: Path) -> Set[str]:
    """
    Extract all JLC component IDs from the symbol library.

    Looks for comments in the symbol file that contain JLC part numbers.
    JLC2KiCadLib typically adds comments like:
    ; JLC Part: C194349
    """
    if not symbol_file.exists():
        return set()

    content = symbol_file.read_text()

    # Look for JLC part numbers in comments
    # Pattern: C followed by digits
    jlc_pattern = r'C\d{5,7}'
    matches = re.findall(jlc_pattern, content)

    return set(matches)


def remove_component_from_symbol_lib(symbol_file: Path, jlc_id: str) -> bool:
    """
    Remove a component's symbol entries from the symbol library file.

    Returns True if component was found and removed.
    """
    if not symbol_file.exists():
        return False

    content = symbol_file.read_text()
    lines = content.splitlines()

    # Find all symbol definitions for this component
    # A symbol looks like: (symbol "SYMBOL_NAME" ...
    # We need to find the symbol that corresponds to this JLC ID
    # This is tricky because JLC2KiCadLib doesn't always store the JLC ID in an obvious place

    # For now, we'll use a simpler approach: look for the JLC ID in comments
    # and remove the entire symbol block that contains it

    # TODO: Implement proper symbol removal
    # This is complex and would require parsing the S-expression format
    # For MVP, we'll skip this and just warn the user

    return False


def remove_component_footprint(footprint_dir: Path, footprint_name: str) -> bool:
    """
    Remove a footprint file.

    Returns True if footprint was found and removed.
    """
    footprint_file = footprint_dir / f"{footprint_name}.kicad_mod"
    if footprint_file.exists():
        footprint_file.unlink()
        return True
    return False
