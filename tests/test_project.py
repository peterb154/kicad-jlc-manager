"""Tests for project.py (KiCadProject and project detection)."""

import json
from pathlib import Path

from kicad_jlc_manager.project import KiCadProject, find_kicad_project


def test_kicad_project_init(tmp_project):
    """Test KiCadProject initialization."""
    project = KiCadProject(tmp_project)
    assert project.root_dir == tmp_project
    assert project.project_file is not None


def test_kicad_project_is_valid(tmp_project):
    """Test is_valid property with valid project."""
    project = KiCadProject(tmp_project)
    assert project.is_valid is True


def test_kicad_project_is_not_valid(tmp_path):
    """Test is_valid property without project file."""
    project = KiCadProject(tmp_path)
    assert project.is_valid is False


def test_kicad_project_name(tmp_project):
    """Test getting project name."""
    project = KiCadProject(tmp_project)
    assert project.name == "test_project"


def test_kicad_project_name_unknown(tmp_path):
    """Test getting project name when no project file exists."""
    project = KiCadProject(tmp_path)
    assert project.name == "unknown"


def test_get_lib_dir_default(tmp_project):
    """Test getting default library directory."""
    project = KiCadProject(tmp_project)
    lib_dir = project.get_lib_dir()
    assert lib_dir == tmp_project / "jlclib"


def test_get_lib_dir_custom(tmp_project):
    """Test getting custom library directory."""
    project = KiCadProject(tmp_project)
    lib_dir = project.get_lib_dir("custom_lib")
    assert lib_dir == tmp_project / "custom_lib"


def test_get_symbol_lib_path(tmp_project):
    """Test getting symbol library path."""
    project = KiCadProject(tmp_project)
    symbol_path = project.get_symbol_lib_path()
    expected = tmp_project / "jlclib" / "symbol" / "jlc_project.kicad_sym"
    assert symbol_path == expected


def test_get_symbol_lib_path_custom_dir(tmp_project):
    """Test getting symbol library path with custom directory."""
    project = KiCadProject(tmp_project)
    custom_lib = tmp_project / "custom_lib"
    symbol_path = project.get_symbol_lib_path(custom_lib)
    expected = custom_lib / "symbol" / "jlc_project.kicad_sym"
    assert symbol_path == expected


def test_get_footprint_lib_path(tmp_project):
    """Test getting footprint library path."""
    project = KiCadProject(tmp_project)
    fp_path = project.get_footprint_lib_path()
    expected = tmp_project / "jlclib" / "footprint"
    assert fp_path == expected


def test_get_footprint_lib_path_custom_dir(tmp_project):
    """Test getting footprint library path with custom directory."""
    project = KiCadProject(tmp_project)
    custom_lib = tmp_project / "custom_lib"
    fp_path = project.get_footprint_lib_path(custom_lib)
    expected = custom_lib / "footprint"
    assert fp_path == expected


def test_get_3dmodel_lib_path(tmp_project):
    """Test getting 3D model library path."""
    project = KiCadProject(tmp_project)
    model_path = project.get_3dmodel_lib_path()
    expected = tmp_project / "jlclib" / "3dmodels"
    assert model_path == expected


def test_get_3dmodel_lib_path_custom_dir(tmp_project):
    """Test getting 3D model library path with custom directory."""
    project = KiCadProject(tmp_project)
    custom_lib = tmp_project / "custom_lib"
    model_path = project.get_3dmodel_lib_path(custom_lib)
    expected = custom_lib / "3dmodels"
    assert model_path == expected


def test_ensure_lib_structure(tmp_project):
    """Test creating library structure."""
    project = KiCadProject(tmp_project)
    project.ensure_lib_structure()

    lib_dir = tmp_project / "jlclib"
    assert (lib_dir / "symbol").exists()
    assert (lib_dir / "footprint").exists()
    assert (lib_dir / "3dmodels").exists()

    symbol_file = lib_dir / "symbol" / "jlc_project.kicad_sym"
    assert symbol_file.exists()
    content = symbol_file.read_text()
    assert "kicad_symbol_lib" in content


def test_ensure_lib_structure_idempotent(tmp_project):
    """Test that ensure_lib_structure can be called multiple times."""
    project = KiCadProject(tmp_project)
    project.ensure_lib_structure()
    project.ensure_lib_structure()

    lib_dir = tmp_project / "jlclib"
    assert (lib_dir / "symbol").exists()
    assert (lib_dir / "footprint").exists()


def test_ensure_lib_structure_custom_dir(tmp_project):
    """Test creating library structure with custom directory."""
    project = KiCadProject(tmp_project)
    custom_lib = tmp_project / "custom_lib"
    project.ensure_lib_structure(custom_lib)

    assert (custom_lib / "symbol").exists()
    assert (custom_lib / "footprint").exists()
    assert (custom_lib / "3dmodels").exists()


def test_create_minimal_project(tmp_path):
    """Test creating minimal KiCad project files."""
    project = KiCadProject(tmp_path)
    project.create_minimal_project("new_project")

    # Check project file
    pro_file = tmp_path / "new_project.kicad_pro"
    assert pro_file.exists()
    pro_data = json.loads(pro_file.read_text())
    assert pro_data["meta"]["filename"] == "new_project.kicad_pro"

    # Check schematic file
    sch_file = tmp_path / "new_project.kicad_sch"
    assert sch_file.exists()
    sch_content = sch_file.read_text()
    assert "kicad_sch" in sch_content
    assert "uuid" in sch_content

    # Check PCB file
    pcb_file = tmp_path / "new_project.kicad_pcb"
    assert pcb_file.exists()
    pcb_content = pcb_file.read_text()
    assert "kicad_pcb" in pcb_content

    # Verify project_file is updated
    assert project.project_file == pro_file
    assert project.is_valid


def test_find_kicad_project_current_dir(tmp_project):
    """Test finding KiCad project in current directory."""
    project = find_kicad_project(tmp_project)
    assert project is not None
    assert project.root_dir == tmp_project


def test_find_kicad_project_parent_dir(tmp_project):
    """Test finding KiCad project in parent directory."""
    subdir = tmp_project / "subdir"
    subdir.mkdir()

    project = find_kicad_project(subdir)
    assert project is not None
    assert project.root_dir == tmp_project


def test_find_kicad_project_nested(tmp_project):
    """Test finding KiCad project from nested subdirectory."""
    nested_dir = tmp_project / "sub1" / "sub2" / "sub3"
    nested_dir.mkdir(parents=True)

    project = find_kicad_project(nested_dir)
    assert project is not None
    assert project.root_dir == tmp_project


def test_find_kicad_project_not_found(tmp_path):
    """Test finding KiCad project when none exists."""
    project = find_kicad_project(tmp_path)
    assert project is None


def test_find_kicad_project_default_cwd(tmp_project, monkeypatch):
    """Test finding KiCad project using current working directory."""
    monkeypatch.chdir(tmp_project)
    project = find_kicad_project()
    assert project is not None
    assert project.root_dir == tmp_project


def test_find_project_file_multiple_projects(tmp_project):
    """Test finding project when multiple .kicad_pro files exist."""
    # Create second project file
    second_pro = tmp_project / "another.kicad_pro"
    second_pro.write_text('{"meta": {"filename": "another.kicad_pro", "version": 3}}')

    project = KiCadProject(tmp_project)
    # Should find one of them (first one found)
    assert project.is_valid
    assert project.project_file is not None
