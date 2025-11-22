"""Pytest configuration and shared fixtures."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary KiCad project directory."""
    project_name = "test_project"
    project_dir = tmp_path / project_name

    # Create project directory
    project_dir.mkdir()

    # Create minimal .kicad_pro file
    pro_file = project_dir / f"{project_name}.kicad_pro"
    pro_content = {"meta": {"filename": f"{project_name}.kicad_pro", "version": 3}}
    pro_file.write_text(json.dumps(pro_content, indent=2) + "\n")

    return project_dir


@pytest.fixture
def tmp_project_with_lib(tmp_project):
    """Create a temporary KiCad project with library structure."""
    # Create library structure
    lib_dir = tmp_project / "jlclib"
    symbol_dir = lib_dir / "symbol"
    footprint_dir = lib_dir / "footprint"
    model_dir = lib_dir / "3dmodels"

    symbol_dir.mkdir(parents=True)
    footprint_dir.mkdir(parents=True)
    model_dir.mkdir(parents=True)

    # Create empty symbol library
    symbol_file = symbol_dir / "jlc_project.kicad_sym"
    symbol_file.write_text(
        "(kicad_symbol_lib (version 20210201) (generator kicad-jlc-manager)\n)\n"
    )

    return tmp_project


@pytest.fixture
def sample_toml_config(tmp_project):
    """Create a sample jlcproject.toml file."""
    config_file = tmp_project / "jlcproject.toml"
    config_content = """components = [
    "C194349",
    "C23107",
]

[project]
lib-dir = "jlclib"
lib-name = "JLC_Project"
"""
    config_file.write_text(config_content)
    return tmp_project


@pytest.fixture
def sample_symbol_lib(tmp_project_with_lib):
    """Create a sample symbol library with test components."""
    symbol_file = tmp_project_with_lib / "jlclib" / "symbol" / "jlc_project.kicad_sym"
    symbol_content = """(kicad_symbol_lib (version 20210201) (generator kicad-jlc-manager)
  (symbol "LM2596S-5.0/TR"
    (property "Reference" "U" (id 0) (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "LM2596S-5.0" (id 1) (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "LCSC" "C194349" (id 5) (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Description" "Buck converter" (id 6) (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )
  (symbol "0805W8F1002T5E"
    (property "Reference" "R" (id 0) (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "10kΩ" (id 1) (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "LCSC" "C23107" (id 5) (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )
)
"""
    symbol_file.write_text(symbol_content)
    return tmp_project_with_lib
