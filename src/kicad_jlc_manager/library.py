"""KiCad library table management (sym-lib-table and fp-lib-table)."""

from pathlib import Path


class LibraryTableManager:
    """Manages KiCad library table files."""

    def __init__(self, project_root: Path):
        """Initialize with project root directory."""
        self.project_root = project_root
        self.sym_lib_table = project_root / "sym-lib-table"
        self.fp_lib_table = project_root / "fp-lib-table"

    def ensure_symbol_library(
        self, lib_name: str = "JLC_Project", lib_dir: str = "jlclib"
    ):
        """Ensure the symbol library is registered in sym-lib-table."""
        lib_path = f"${{KIPRJMOD}}/{lib_dir}/symbol/jlc_project.kicad_sym"

        if not self.sym_lib_table.exists():
            # Create new sym-lib-table
            content = self._generate_sym_lib_table(lib_name, lib_path)
            self.sym_lib_table.write_text(content)
        else:
            # Check if library already exists
            existing_content = self.sym_lib_table.read_text()
            if lib_name not in existing_content:
                # Add library to existing table
                self._add_to_sym_lib_table(lib_name, lib_path)

    def ensure_footprint_library(
        self, lib_name: str = "JLC_Project", lib_dir: str = "jlclib"
    ):
        """Ensure the footprint library is registered in fp-lib-table."""
        lib_path = f"${{KIPRJMOD}}/{lib_dir}/footprint"

        if not self.fp_lib_table.exists():
            # Create new fp-lib-table
            content = self._generate_fp_lib_table(lib_name, lib_path)
            self.fp_lib_table.write_text(content)
        else:
            # Check if library already exists
            existing_content = self.fp_lib_table.read_text()
            if lib_name not in existing_content:
                # Add library to existing table
                self._add_to_fp_lib_table(lib_name, lib_path)

    def _generate_sym_lib_table(self, lib_name: str, lib_path: str) -> str:
        """Generate a new sym-lib-table file content."""
        return f"""(sym_lib_table
  (version 7)
  (lib (name "{lib_name}")(type "KiCad")(uri "{lib_path}")(options "")(descr "Project-local JLC components"))
)
"""

    def _generate_fp_lib_table(self, lib_name: str, lib_path: str) -> str:
        """Generate a new fp-lib-table file content."""
        return f"""(fp_lib_table
  (version 7)
  (lib (name "{lib_name}")(type "KiCad")(uri "{lib_path}")(options "")(descr "Project-local JLC component footprints"))
)
"""

    def _add_to_sym_lib_table(self, lib_name: str, lib_path: str):
        """Add a library entry to existing sym-lib-table."""
        content = self.sym_lib_table.read_text()

        # Find the closing parenthesis
        insert_pos = content.rfind(")")

        if insert_pos == -1:
            # Malformed file, create new one
            content = self._generate_sym_lib_table(lib_name, lib_path)
            self.sym_lib_table.write_text(content)
            return

        # Insert new library entry before the closing parenthesis
        lib_entry = f'  (lib (name "{lib_name}")(type "KiCad")(uri "{lib_path}")(options "")(descr "Project-local JLC components"))\n'
        new_content = content[:insert_pos] + lib_entry + content[insert_pos:]
        self.sym_lib_table.write_text(new_content)

    def _add_to_fp_lib_table(self, lib_name: str, lib_path: str):
        """Add a library entry to existing fp-lib-table."""
        content = self.fp_lib_table.read_text()

        # Find the closing parenthesis
        insert_pos = content.rfind(")")

        if insert_pos == -1:
            # Malformed file, create new one
            content = self._generate_fp_lib_table(lib_name, lib_path)
            self.fp_lib_table.write_text(content)
            return

        # Insert new library entry before the closing parenthesis
        lib_entry = f'  (lib (name "{lib_name}")(type "KiCad")(uri "{lib_path}")(options "")(descr "Project-local JLC component footprints"))\n'
        new_content = content[:insert_pos] + lib_entry + content[insert_pos:]
        self.fp_lib_table.write_text(new_content)
