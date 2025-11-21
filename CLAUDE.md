# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**kicad-jlc-manager** is a Python CLI tool that brings modern package management paradigms (like `.venv`, `node_modules`) to KiCad component libraries. It enables project-local component management with a declarative manifest file (`jlcproject.toml`).

### Core Philosophy

- **Project-local isolation**: Each KiCad project has its own component library (like virtual environments)
- **Declarative manifest**: `jlcproject.toml` tracks components (committed to git)
- **Generated artifacts excluded**: `jlclib/` directory is git-ignored (like `.venv` or `node_modules`)
- **Explicit workflow**: UV-inspired design - requires `jlcmgr init` before `jlcmgr add`
- **Reproducibility**: `jlcmgr sync` recreates exact library state from manifest

## Architecture

### Layer Structure

The project uses a **wrapper architecture** around existing tools:

1. **JLC2KiCadLib (Dependency)**:
   - Handles mechanical file generation (symbols, footprints, 3D models)
   - Fetches component data from JLCPCB API
   - Creates KiCad-compatible files

2. **kicad-jlc-manager (This Project)**:
   - Project detection and initialization
   - Manifest management (TOML format)
   - Library table configuration
   - Component tracking and sync operations

### Key Components

#### CLI Interface (`cli.py`)
- Uses Click framework for command-line interface
- Commands: `init`, `add`, `list`, `sync`, `remove`
- Entry point defined in `pyproject.toml`: `jlcmgr = "kicad_jlc_manager.cli:main"`

#### Project Management (`project.py`)
- `find_kicad_project()`: Searches upward for `.kicad_pro` files
- `KiCadProject` class: Represents a KiCad project with methods for library structure

#### Configuration (`config.py`)
- `ProjectConfig` class: Manages `jlcproject.toml` manifest
- **CRITICAL**: TOML structure requires components array at ROOT level BEFORE `[project]` section
- Handles both dict and list formats for backward compatibility

#### Library Tables (`library.py`)
- `LibraryTableManager`: Manages `sym-lib-table` and `fp-lib-table`
- Uses `${KIPRJMOD}` for portable paths
- Creates S-expression format library table entries

#### API Client (`jlc_api.py`)
- `fetch_component_description()`: Fetches component metadata from JLC API
- Silently fails if API unavailable (descriptions are optional)

#### Component Utilities (`component.py`)
- Component detection and management utilities
- Footprint/symbol file operations (partially implemented)

## Development Commands

### Environment Setup
```bash
# Install with dev dependencies
uv sync --group dev

# The virtual environment is automatically managed by UV
# CLI is available as: uv run jlcmgr
```

### Linting and Formatting
```bash
# Run linter (check only)
make lint

# Auto-fix linting issues
make lint-fix

# Run tests
make test

# Clean build artifacts
make clean
```

### Manual Testing
```bash
# Create a test KiCad project
cd /tmp
mkdir test-project
cd test-project
touch test.kicad_pro

# Test the CLI
uv run jlcmgr init
uv run jlcmgr add C194349
uv run jlcmgr list
uv run jlcmgr sync
```

## File Structure

```
kicad-jlc-manager/
├── src/
│   └── kicad_jlc_manager/
│       ├── cli.py              # Click-based CLI commands
│       ├── config.py           # TOML manifest management
│       ├── project.py          # KiCad project detection
│       ├── library.py          # Library table management
│       ├── jlc_api.py          # JLC API client
│       ├── component.py        # Component utilities
│       └── value_parser.py     # (Stub for future enhancement)
├── pyproject.toml              # Package metadata and dependencies
├── Makefile                    # Development automation
├── README.md                   # User-facing documentation
└── CLAUDE.md                   # This file
```

## Key Design Decisions

### 1. TOML Format Critical Detail

**PROBLEM**: Python's TOML parser groups root-level arrays under the nearest preceding section.

**SOLUTION**: Write `components = []` at the ROOT level BEFORE any `[section]` headers.

```toml
# CORRECT - components at root level first
components = [
    "C194349",  # 10kOhm resistor
    "C23107",   # 100nF capacitor
]

[project]
lib-dir = "jlclib"
lib-name = "JLC_Project"

# INCORRECT - components would be nested under [project]
[project]
lib-dir = "jlclib"
lib-name = "JLC_Project"

components = [...]  # DON'T DO THIS
```

See `config.py:save()` for implementation.

### 2. Explicit Initialization

Following UV's design philosophy, `jlcmgr add` **requires** prior initialization:

```python
# Check if project is initialized
config = ProjectConfig(project.root_dir)
if not config.config_file.exists():
    click.secho("✗ Project not initialized", fg="red")
    click.echo("  Run 'jlcmgr init' first")
    sys.exit(1)
```

This avoids implicit behavior and makes the workflow predictable.

### 3. Clean Sync Strategy

`jlcmgr sync` performs a **clean sync** (like `uv sync`):

1. Delete entire `jlclib/` directory
2. Recreate library structure
3. Download all components from manifest

This ensures the library exactly matches the manifest, avoiding drift.

### 4. Library Path Portability

Uses KiCad's `${KIPRJMOD}` variable for portable paths:

```lisp
(uri "${KIPRJMOD}/jlclib/symbol/jlc_project.kicad_sym")
```

This allows projects to work on any machine without path adjustments.

### 5. Optional Descriptions

Component descriptions are **optional** and fetched from JLC API:

- If API succeeds: description added as inline comment
- If API fails: component tracked without description
- Users can manually edit descriptions in TOML

## Common Workflows

### Adding Components
```bash
# User workflow
jlcmgr init                    # One-time setup
jlcmgr add C194349            # Add components as needed
jlcmgr list                   # View what's installed

# Internal flow
1. Check project initialized (config.config_file.exists())
2. Run JLC2KiCadLib subprocess to generate files
3. Fetch description from JLC API (optional)
4. Add component to manifest with description
5. Save updated manifest
```

### Syncing After Clone
```bash
# User workflow
git clone <project>
cd <project>
jlcmgr sync                   # Recreate library from manifest

# Internal flow
1. Load components from jlcproject.toml
2. Delete existing jlclib/ directory
3. Recreate library structure
4. Download each component via JLC2KiCadLib
5. Report success/failure counts
```

## Testing Strategy

### Manual Testing Checklist

1. **Project Detection**:
   - Run from project root
   - Run from subdirectory
   - Run outside project (should fail gracefully)

2. **Initialization**:
   - Fresh project (no existing files)
   - Project with existing library tables
   - Custom lib-dir and lib-name options

3. **Adding Components**:
   - Valid JLC part numbers (C194349, C23107)
   - Invalid part numbers (error handling)
   - Duplicate additions (should work idempotently)

4. **Sync Operations**:
   - Empty manifest
   - Multiple components
   - After manual jlclib/ deletion

5. **List Command**:
   - Empty project
   - With components
   - Detailed flag

### Test Project Location
Standard test project: `/Users/brianpeterson/Projects/personal/kicad-local-lib-test`

## Known Issues and TODOs

### Implemented
- ✅ Project detection and initialization
- ✅ Component addition with API descriptions
- ✅ Manifest management (TOML format)
- ✅ Library table configuration
- ✅ List command with optional details
- ✅ Sync command with clean sync strategy
- ✅ Ruff linting configuration
- ✅ Makefile for development automation

### TODO
- ⏳ `jlcmgr remove` command implementation
- ⏳ Value parser for smarter component descriptions
- ⏳ Unit tests with pytest
- ⏳ PyPI publication
- ⏳ More robust error handling for JLC2KiCadLib failures

## Dependencies

### Runtime Dependencies
- `click>=8.3.1`: CLI framework
- `jlc2kicadlib>=1.0.36`: Component file generator
- `requests>=2.32.4`: HTTP client for JLC API

### Development Dependencies
- `ruff>=0.14.6`: Linting and formatting
- `pytest>=7.0.0`: Testing framework (optional-dependencies)
- `pytest-cov>=4.0.0`: Coverage reports (optional-dependencies)

## Code Style

### Ruff Configuration
See `pyproject.toml` for ruff settings:
- Line length: 100
- Target: Python 3.12
- Enabled rules: pycodestyle, pyflakes, isort, bugbear, comprehensions, pyupgrade

### Conventions
- Use type hints (`str | None` style)
- Click decorators for CLI commands
- Path objects from pathlib (not strings)
- Early returns for error conditions
- Descriptive variable names

## Error Handling Patterns

### Expected Errors (Graceful)
- No KiCad project found → user-friendly message
- Project not initialized → suggest `jlcmgr init`
- JLC2KiCadLib not found → installation instructions
- API fetch fails → continue without description

### Unexpected Errors (Let Fail)
- TOML parsing errors → stack trace
- File permission errors → stack trace
- Subprocess errors (non-zero exit) → captured stderr shown

## Related Projects

- **Parent Project**: [jlc-kicad-manager](../README.md) - The original library generation system
- **JLC2KiCadLib**: [GitHub](https://github.com/TousstNicolas/JLC2KiCad_lib) - Component file generator
- **JLCPCB**: [Website](https://jlcpcb.com/) - Component library source

## Contributing Guidelines

When making changes:

1. **Read existing code first**: Always use Read tool before Edit/Write
2. **Run linter**: `make lint-fix` before committing
3. **Test manually**: Use test project to verify changes
4. **Update documentation**: Keep README.md and CLAUDE.md in sync
5. **Follow conventions**: Match existing code style

### Common Patterns to Follow

**CLI Commands**:
```python
@main.command()
@click.argument("part_number")
@click.option("--flag", help="Description")
def command_name(part_number: str, flag: bool):
    """Command description for --help."""
    # 1. Detect project
    # 2. Check initialization
    # 3. Perform operation
    # 4. Provide feedback
```

**Error Messages**:
```python
click.secho("✗ Error message", fg="red")
click.echo("  Suggestion or help text")
sys.exit(1)
```

**Success Messages**:
```python
click.secho("✓ Success message", fg="green")
click.echo(f"  Additional info: {detail}")
```

## Future Enhancements

### Short Term
- Implement `remove` command with smart footprint handling
- Add unit tests for core functionality
- Publish to PyPI

### Long Term
- Value parser for extracting electrical values from part numbers
- Support for multiple library sources (not just JLC)
- Component search/browse functionality
- Integration with KiCad BOM generation
- GUI interface (optional)

## Debugging Tips

### Common Issues

**TOML components not saving**:
- Check that components are written at root level before `[project]`
- Verify file is being written correctly with `cat jlcproject.toml`

**Library not showing in KiCad**:
- Check `sym-lib-table` and `fp-lib-table` exist
- Verify paths use `${KIPRJMOD}` variable
- Ensure `jlclib/` structure is correct

**JLC2KiCadLib not found**:
- Check virtual environment: `uv run which JLC2KiCadLib`
- Reinstall: `uv sync`

**Component downloads failing**:
- Test JLC2KiCadLib directly: `JLC2KiCadLib C194349 -dir /tmp/test`
- Check network connectivity to JLCPCB
- Verify part number exists on JLCPCB website

## Version History

- **v0.1.0** (Current): Initial MVP release
  - init, add, list, sync commands
  - TOML manifest management
  - Library table configuration
  - JLC API integration
