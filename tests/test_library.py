"""Tests for library.py (LibraryTableManager)."""

from pathlib import Path

from kicad_jlc_manager.library import LibraryTableManager


def test_library_table_manager_init(tmp_project):
    """Test LibraryTableManager initialization."""
    manager = LibraryTableManager(tmp_project)
    assert manager.project_root == tmp_project
    assert manager.sym_lib_table == tmp_project / "sym-lib-table"
    assert manager.fp_lib_table == tmp_project / "fp-lib-table"


def test_ensure_symbol_library_new_file(tmp_project):
    """Test creating new sym-lib-table file."""
    manager = LibraryTableManager(tmp_project)
    manager.ensure_symbol_library()

    sym_table = tmp_project / "sym-lib-table"
    assert sym_table.exists()

    content = sym_table.read_text()
    assert "sym_lib_table" in content
    assert "JLC_Project" in content
    assert "${KIPRJMOD}/jlclib/symbol/jlc_project.kicad_sym" in content
    assert "Project-local JLC components" in content


def test_ensure_symbol_library_custom_params(tmp_project):
    """Test creating sym-lib-table with custom parameters."""
    manager = LibraryTableManager(tmp_project)
    manager.ensure_symbol_library(lib_name="Custom_Lib", lib_dir="custom_dir")

    content = tmp_project / "sym-lib-table"
    assert content.exists()

    text = content.read_text()
    assert "Custom_Lib" in text
    assert "${KIPRJMOD}/custom_dir/symbol/jlc_project.kicad_sym" in text


def test_ensure_symbol_library_existing_file_no_entry(tmp_project):
    """Test adding to existing sym-lib-table without the entry."""
    sym_table = tmp_project / "sym-lib-table"
    sym_table.write_text("""(sym_lib_table
  (version 7)
  (lib (name "Other_Lib")(type "KiCad")(uri "/path/to/other.kicad_sym")(options "")(descr ""))
)
""")

    manager = LibraryTableManager(tmp_project)
    manager.ensure_symbol_library()

    content = sym_table.read_text()
    assert "Other_Lib" in content
    assert "JLC_Project" in content
    assert content.count("(lib ") == 2


def test_ensure_symbol_library_existing_file_with_entry(tmp_project):
    """Test that existing entry is not duplicated."""
    sym_table = tmp_project / "sym-lib-table"
    sym_table.write_text("""(sym_lib_table
  (version 7)
  (lib (name "JLC_Project")(type "KiCad")(uri "${KIPRJMOD}/jlclib/symbol/jlc_project.kicad_sym")(options "")(descr ""))
)
""")

    manager = LibraryTableManager(tmp_project)
    manager.ensure_symbol_library()

    content = sym_table.read_text()
    assert content.count("JLC_Project") == 1


def test_ensure_symbol_library_malformed_file(tmp_project):
    """Test handling malformed sym-lib-table file."""
    sym_table = tmp_project / "sym-lib-table"
    sym_table.write_text("malformed content without closing paren")

    manager = LibraryTableManager(tmp_project)
    manager.ensure_symbol_library()

    content = sym_table.read_text()
    assert "sym_lib_table" in content
    assert "JLC_Project" in content


def test_ensure_footprint_library_new_file(tmp_project):
    """Test creating new fp-lib-table file."""
    manager = LibraryTableManager(tmp_project)
    manager.ensure_footprint_library()

    fp_table = tmp_project / "fp-lib-table"
    assert fp_table.exists()

    content = fp_table.read_text()
    assert "fp_lib_table" in content
    assert "JLC_Project" in content
    assert "${KIPRJMOD}/jlclib/footprint" in content
    assert "Project-local JLC component footprints" in content


def test_ensure_footprint_library_custom_params(tmp_project):
    """Test creating fp-lib-table with custom parameters."""
    manager = LibraryTableManager(tmp_project)
    manager.ensure_footprint_library(lib_name="Custom_FP", lib_dir="custom_fp_dir")

    content = tmp_project / "fp-lib-table"
    assert content.exists()

    text = content.read_text()
    assert "Custom_FP" in text
    assert "${KIPRJMOD}/custom_fp_dir/footprint" in text


def test_ensure_footprint_library_existing_file_no_entry(tmp_project):
    """Test adding to existing fp-lib-table without the entry."""
    fp_table = tmp_project / "fp-lib-table"
    fp_table.write_text("""(fp_lib_table
  (version 7)
  (lib (name "Other_FP")(type "KiCad")(uri "/path/to/other.pretty")(options "")(descr ""))
)
""")

    manager = LibraryTableManager(tmp_project)
    manager.ensure_footprint_library()

    content = fp_table.read_text()
    assert "Other_FP" in content
    assert "JLC_Project" in content
    assert content.count("(lib ") == 2


def test_ensure_footprint_library_existing_file_with_entry(tmp_project):
    """Test that existing footprint entry is not duplicated."""
    fp_table = tmp_project / "fp-lib-table"
    fp_table.write_text("""(fp_lib_table
  (version 7)
  (lib (name "JLC_Project")(type "KiCad")(uri "${KIPRJMOD}/jlclib/footprint")(options "")(descr ""))
)
""")

    manager = LibraryTableManager(tmp_project)
    manager.ensure_footprint_library()

    content = fp_table.read_text()
    assert content.count("JLC_Project") == 1


def test_ensure_footprint_library_malformed_file(tmp_project):
    """Test handling malformed fp-lib-table file."""
    fp_table = tmp_project / "fp-lib-table"
    fp_table.write_text("malformed content")

    manager = LibraryTableManager(tmp_project)
    manager.ensure_footprint_library()

    content = fp_table.read_text()
    assert "fp_lib_table" in content
    assert "JLC_Project" in content


def test_generate_sym_lib_table(tmp_project):
    """Test generating sym-lib-table content."""
    manager = LibraryTableManager(tmp_project)
    content = manager._generate_sym_lib_table("Test_Lib", "${KIPRJMOD}/test/lib.kicad_sym")

    assert "sym_lib_table" in content
    assert "(version 7)" in content
    assert 'name "Test_Lib"' in content
    assert 'uri "${KIPRJMOD}/test/lib.kicad_sym"' in content


def test_generate_fp_lib_table(tmp_project):
    """Test generating fp-lib-table content."""
    manager = LibraryTableManager(tmp_project)
    content = manager._generate_fp_lib_table("Test_FP", "${KIPRJMOD}/test/footprints")

    assert "fp_lib_table" in content
    assert "(version 7)" in content
    assert 'name "Test_FP"' in content
    assert 'uri "${KIPRJMOD}/test/footprints"' in content


def test_ensure_both_libraries(tmp_project):
    """Test ensuring both symbol and footprint libraries."""
    manager = LibraryTableManager(tmp_project)
    manager.ensure_symbol_library()
    manager.ensure_footprint_library()

    assert (tmp_project / "sym-lib-table").exists()
    assert (tmp_project / "fp-lib-table").exists()

    sym_content = (tmp_project / "sym-lib-table").read_text()
    assert "JLC_Project" in sym_content

    fp_content = (tmp_project / "fp-lib-table").read_text()
    assert "JLC_Project" in fp_content
