# kicad-jlc-manager

**Project-local JLC component library manager for KiCad**

Bring the `.venv` / `node_modules` paradigm to KiCad component libraries. Manage JLCPCB components on a per-project basis with a declarative manifest file, just like `pyproject.toml` or `package.json`.

## Why?

Traditional KiCad workflows use globally configured component libraries, which creates several problems:

- **No project portability**: Libraries are configured per-machine, not per-project
- **Dependency hell**: Different projects can't use different versions of the same component
- **Git unfriendly**: No way to track which components a project actually uses
- **Team collaboration issues**: Everyone needs identical library configurations

`kicad-jlc-manager` solves this by creating **project-local component libraries** that live alongside your KiCad project, with a manifest file (`jlcproject.toml`) that tracks exactly which components your project uses.

## Features

- **Project-local libraries**: Components live in `jlclib/` (excluded from git, like `.venv`)
- **Declarative manifest**: `jlcproject.toml` tracks components (committed to git, like `pyproject.toml`)
- **Sync command**: Reproduce exact component set from manifest (like `uv sync` or `npm install`)
- **Component metadata**: Automatically fetches descriptions from JLC API
- **Explicit workflow**: UV-inspired design requires `init` before `add`
- **Portable paths**: Uses `${KIPRJMOD}` for KiCad path portability

## Installation

```bash
# From PyPI (once published)
pip install kicad-jlc-manager

# For development
git clone https://github.com/yourusername/kicad-jlc-manager.git
cd kicad-jlc-manager
uv sync --group dev
```

## Quick Start

```bash
# Start a new project (no KiCad files needed!)
mkdir my-board
cd my-board

# Initialize - creates minimal KiCad project files automatically
jlcmgr init

# Add JLC components to your project
jlcmgr add C194349  # 10k ohm 0402 resistor
jlcmgr add C23107   # 100nF 0402 capacitor

# Open in KiCad and start designing
kicad .  # On macOS with alias: alias kicad='open -a KiCad'
# Note: Once KiCad opens, use File > Open Project and select the .kicad_pro file

# View your project's components
jlcmgr list

# Sync components (useful after git clone or pulling jlcproject.toml changes)
jlcmgr sync
```

## Commands

### `jlcmgr init`

Initialize the project library structure. If no KiCad project exists in the current directory, creates minimal KiCad project files automatically (project name defaults to directory name, just like `uv`).

Creates:

- Minimal KiCad project files (if not present):
  - `<project-name>.kicad_pro` - Project configuration
  - `<project-name>.kicad_sch` - Empty schematic
  - `<project-name>.kicad_pcb` - Empty PCB layout
- `jlclib/` directory structure (symbol/ and footprint/ subdirectories)
- `jlcproject.toml` manifest file
- Library table entries (`sym-lib-table`, `fp-lib-table`)
- `.gitignore` entry to exclude `jlclib/`

Options:

- `--lib-dir`: Custom library directory (default: `jlclib`)
- `--lib-name`: Custom library name (default: `JLC_Project`)

```bash
jlcmgr init
jlcmgr init --lib-dir custom_lib --lib-name MyProject
```

### `jlcmgr add <part>`

Add a JLC component to the project. Downloads the component using JLC2KiCadLib and tracks it in `jlcproject.toml`.

```bash
jlcmgr add C194349
jlcmgr add C23107
```

### `jlcmgr list`

List all components tracked in `jlcproject.toml`.

Options:
- `--detailed`: Show detailed component information including JLC URLs

```bash
jlcmgr list
jlcmgr list --detailed
```

### `jlcmgr sync`

Synchronize the project library with `jlcproject.toml`. Performs a clean sync:
1. Removes existing `jlclib/` directory
2. Recreates library structure
3. Downloads all components from the manifest

This is similar to `uv sync` or `npm install` - it ensures your local library exactly matches the manifest.

```bash
jlcmgr sync
```

### `jlcmgr remove <part>`

Remove a component from the project (coming soon).

```bash
jlcmgr remove C194349
```

## Workflow

### Starting a New Project (Streamlined)

The fastest way to start a new KiCad project with JLC component management:

```bash
# Create and initialize in one flow
mkdir my-board
cd my-board
jlcmgr init

# Add components
jlcmgr add C194349  # 10kΩ 0402 resistor
jlcmgr add C23107   # 100nF 0402 capacitor
jlcmgr add C2040    # LED 0805 Red

# Open in KiCad - components are ready to use!
kicad .  # or: open -a KiCad .
# Once KiCad launches, go to File > Open Project and select my-board.kicad_pro
```

**On macOS**, add this to your `~/.zshrc` for the `kicad` command:

```bash
# Allow 'kicad .' to open KiCad in current directory
alias kicad='open -a KiCad'
```

**Note**: The `kicad .` command opens the KiCad application but doesn't automatically load your project. After KiCad launches, you'll need to manually open the project file (`.kicad_pro`) via File > Open Project.

What happens during `jlcmgr init`:

1. **Creates minimal KiCad project files** (if none exist):
   - `my-board.kicad_pro` - Project config
   - `my-board.kicad_sch` - Empty schematic
   - `my-board.kicad_pcb` - Empty PCB
   - Project name automatically matches directory name
2. **Sets up library infrastructure**:
   - `jlclib/` directory for components
   - `jlcproject.toml` manifest
   - `sym-lib-table` and `fp-lib-table` configurations
   - `.gitignore` to exclude generated files

### Working with Existing Projects

If you already have a KiCad project:

```bash
# Navigate to existing project directory
cd ~/existing-project/

# Initialize jlcmgr (detects existing .kicad_pro)
jlcmgr init

# Add components as you design
jlcmgr add C194349
jlcmgr list
```

### Git Workflow

```bash
# After adding components, commit the manifest
git add jlcproject.toml sym-lib-table fp-lib-table .gitignore
git commit -m "Add JLC component library with resistors and capacitors"

# The jlclib/ directory is automatically excluded via .gitignore
# (just like .venv or node_modules)
```

### Cloning/Sharing Projects

```bash
# Clone a project with jlcproject.toml
git clone https://github.com/someone/cool-project.git
cd cool-project/

# Sync to download all components
jlcmgr sync

# Library is now populated, ready to open in KiCad
```

## File Structure

After running `jlcmgr init` and adding components, your project will look like:

```text
my-project/
├── .gitignore              # Updated to exclude jlclib/
├── jlcproject.toml         # Component manifest (committed to git)
├── sym-lib-table           # Symbol library configuration
├── fp-lib-table            # Footprint library configuration
├── my-project.kicad_pro    # KiCad project file
├── my-project.kicad_pcb    # KiCad PCB file
├── my-project.kicad_sch    # KiCad schematic file
└── jlclib/                 # Project-local library (excluded from git)
    ├── footprint/
    │   └── *.kicad_mod
    └── symbol/
        └── jlc_project.kicad_sym
```

## jlcproject.toml Format

The manifest file uses a simple TOML format with optional inline comments for descriptions:

```toml
components = [
    "C194349",  # 10kOhm 0402 resistor
    "C23107",   # 100nF 0402 capacitor
    "C2040",    # LED 0805 Red
]

[project]
lib-dir = "jlclib"
lib-name = "JLC_Project"
```

Comments are fetched automatically from the JLC API when you run `jlcmgr add`, but you can edit them manually.

## How It Works

### Library Tables

`kicad-jlc-manager` creates or updates two library table files in your project directory:

**`sym-lib-table`** - Configures the symbol library:
```lisp
(sym_lib_table
  (version 7)
  (lib (name "JLC_Project")
       (type "KiCad")
       (uri "${KIPRJMOD}/jlclib/symbol/jlc_project.kicad_sym")
       (options "")
       (descr "Project-local JLC components"))
)
```

**`fp-lib-table`** - Configures the footprint library:
```lisp
(fp_lib_table
  (version 7)
  (lib (name "JLC_Project")
       (type "KiCad")
       (uri "${KIPRJMOD}/jlclib/footprint")
       (options "")
       (descr "Project-local JLC component footprints"))
)
```

The `${KIPRJMOD}` variable ensures paths work correctly regardless of where the project is located.

### Component Generation

Under the hood, `kicad-jlc-manager` uses [JLC2KiCadLib](https://github.com/TousstNicolas/JLC2KiCad_lib) to fetch component data from JLCPCB and generate KiCad-compatible symbol and footprint files.

## Requirements

- Python >= 3.12
- KiCad 7.0 or later
- JLC2KiCadLib >= 1.0.36 (installed automatically)

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/kicad-jlc-manager.git
cd kicad-jlc-manager

# Install with dev dependencies
uv sync --group dev

# Run linter
make lint

# Auto-fix linting issues
make lint-fix

# Run tests
make test
```

## Design Philosophy

This tool is inspired by modern package managers like `uv` and `npm`:

- **Explicit initialization**: Requires `jlcmgr init` before adding components (no auto-magic)
- **Clean separation**: Library files excluded from git, manifest committed
- **Reproducible**: `jlcmgr sync` creates identical library state from manifest
- **Project-scoped**: Each project has its own isolated component library

## Comparison to Global Libraries

| Aspect | Global Libraries | kicad-jlc-manager |
|--------|-----------------|-------------------|
| Configuration | Per-machine | Per-project |
| Portability | Manual setup on each machine | Automatic via manifest |
| Git tracking | No component tracking | Explicit manifest |
| Version control | Implicit/manual | Declarative in TOML |
| Team collaboration | Manual sync required | Git handles sync |
| Isolation | Shared across projects | Isolated per project |

## Related Projects

- [JLC2KiCadLib](https://github.com/TousstNicolas/JLC2KiCad_lib) - Component file generator (used internally)
- [JLCPCB](https://jlcpcb.com/) - PCB manufacturer with component library

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/kicad-jlc-manager.git
cd kicad-jlc-manager

# Install with dev dependencies
uv sync --group dev

# Verify installation
uv run jlcmgr --help
```

### Running Tests and Linting

```bash
# Run linter (check only)
make lint

# Run linter with auto-fix
make lint-fix

# Run tests with coverage
make test

# Run tests with detailed coverage report
make test-cov

# Run tests without coverage (faster)
make test-quick

# View all available commands
make help
```

### Semantic Versioning

This project uses [Python Semantic Release](https://python-semantic-release.readthedocs.io/) for automated versioning and releases. Versions are determined automatically based on commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

#### Commit Message Format

Use these prefixes to control version bumping:

- `feat:` - New feature (bumps **minor** version: 0.1.0 → 0.2.0)
- `fix:` - Bug fix (bumps **patch** version: 0.1.0 → 0.1.1)
- `perf:` - Performance improvement (bumps **patch** version)
- `docs:` - Documentation changes (no version bump)
- `style:` - Code style changes (no version bump)
- `refactor:` - Code refactoring (no version bump)
- `test:` - Test changes (no version bump)
- `chore:` - Build/tooling changes (no version bump)
- `ci:` - CI/CD changes (no version bump)

For breaking changes, add `!` after the type or include `BREAKING CHANGE:` in the commit body (bumps **major** version: 0.1.0 → 1.0.0).

#### Commit Examples

```bash
# Feature (minor version bump)
git commit -m "feat: add component search functionality"

# Bug fix (patch version bump)
git commit -m "fix: resolve sync error with missing files"

# Bug fix with more detail
git commit -m "fix: handle empty component descriptions in API response

Previously the tool would crash if JLC API returned null description.
Now it gracefully handles missing descriptions."

# Breaking change (major version bump)
git commit -m "feat!: redesign library structure

BREAKING CHANGE: Library directory structure has changed from flat
to nested. Users need to run 'jlcmgr sync' after upgrading."

# Non-versioned changes
git commit -m "docs: update installation instructions"
git commit -m "chore: update dependencies"
```

#### Local Version Checking

```bash
# Preview what the next version would be (dry-run)
make version

# Create a release locally (updates version, creates tag)
make release

# After local release, push with tags
git push --follow-tags
```

#### Automated Release Process

When you push to the `main` branch:

1. **PR Workflow** (`.github/workflows/pr-checks.yaml`)
   - Runs `make lint` and `make test` in parallel
   - Must pass before merging

2. **Publish Workflow** (`.github/workflows/publish.yaml`)
   - Runs `make lint` and `make test` in parallel
   - Analyzes commits since last release
   - Determines next version based on conventional commits
   - Updates `pyproject.toml` version and `CHANGELOG.md`
   - Creates git tag (e.g., `v0.2.0`)
   - Builds package with `uv build`
   - Publishes to PyPI using trusted publisher
   - Pushes version bump commit and tag back to repo

**Note**: Only commits following the conventional format will trigger version bumps. Regular commits (without conventional prefixes) won't create new releases.

### Pull Request Workflow

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with conventional commits:

   ```bash
   git commit -m "feat: add new awesome feature"
   git commit -m "test: add tests for awesome feature"
   git commit -m "docs: document awesome feature"
   ```

4. Push to your fork (`git push origin feature/amazing-feature`)
5. Open a Pull Request
   - The PR checks workflow will run tests and linting
   - Ensure all checks pass before requesting review
6. After merge to `main`, the release workflow will automatically:
   - Determine the new version from your commits
   - Publish to PyPI if version was bumped
   - Create a GitHub release with changelog

### Code Style

- Python 3.12+
- Line length: 100 characters
- Use type hints (`str | None` style)
- Follow ruff linting rules (see `pyproject.toml`)
- Write tests for new features
- Update documentation as needed

## Support

- Issues: https://github.com/yourusername/kicad-jlc-manager/issues
- Discussions: https://github.com/yourusername/kicad-jlc-manager/discussions
