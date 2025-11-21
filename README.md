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
# 1. Navigate to your KiCad project directory
cd ~/my-kicad-project

# 2. Initialize project-local library structure
jlcmgr init

# 3. Add JLC components to your project
jlcmgr add C194349  # 10k ohm 0402 resistor
jlcmgr add C23107   # 100nF 0402 capacitor

# 4. View your project's components
jlcmgr list

# 5. Sync components (useful after git clone or pulling jlcproject.toml changes)
jlcmgr sync
```

## Commands

### `jlcmgr init`

Initialize the project library structure. Creates:
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

### Typical Development Workflow

```bash
# Start a new KiCad project
kicad-cli pcb new my-project.kicad_pro
cd my-project/

# Initialize jlcmgr
jlcmgr init

# Add components as you design
jlcmgr add C194349  # Resistor
jlcmgr add C23107   # Capacitor
jlcmgr add C2040    # LED

# Check what's in your project
jlcmgr list

# Open KiCad and use the JLC_Project library
# Components are now available in the symbol/footprint picker

# Commit the manifest (library files are excluded via .gitignore)
git add jlcproject.toml sym-lib-table fp-lib-table
git commit -m "Add JLC components"
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

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- Issues: https://github.com/yourusername/kicad-jlc-manager/issues
- Discussions: https://github.com/yourusername/kicad-jlc-manager/discussions
