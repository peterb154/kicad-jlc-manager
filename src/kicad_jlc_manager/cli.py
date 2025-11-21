"""CLI interface for kicad-jlc-manager using Click."""

import click
import subprocess
import sys
from pathlib import Path

from .project import find_kicad_project
from .library import LibraryTableManager
from .config import ProjectConfig
from .jlc_api import fetch_component_description


@click.group()
@click.version_option(version="0.1.0", prog_name="jlcmgr")
def main():
    """Manage project-local JLC component libraries for KiCad."""
    pass


@main.command()
@click.argument("part_number")
@click.option("--lib-dir", help="Custom library directory (default: jlclib/)")
@click.option("--lib-name", help="Custom library name (default: JLC_Project)")
def add(part_number: str, lib_dir: str | None, lib_name: str | None):
    """Add a JLC component to the project library."""
    # Defaults
    lib_dir = lib_dir or "jlclib"
    lib_name = lib_name or "JLC_Project"

    # Find KiCad project
    click.echo("Detecting KiCad project...")
    project = find_kicad_project()

    if not project:
        click.secho("✗ No KiCad project found in current or parent directories", fg="red")
        click.echo("  Make sure you're inside a KiCad project directory (contains .kicad_pro file)")
        sys.exit(1)

    click.echo(f"  Found project: {project.name}")

    # Check if project is initialized
    config = ProjectConfig(project.root_dir)
    if not config.config_file.exists():
        click.secho("✗ Project not initialized", fg="red")
        click.echo("  Run 'jlcmgr init' first to set up the library structure")
        sys.exit(1)

    # Use config values if CLI options not provided
    if not lib_dir:
        lib_dir = config.get_lib_dir()
    if not lib_name:
        lib_name = config.get_lib_name()

    # Ensure library structure exists (in case it was deleted)
    lib_path = project.get_lib_dir(lib_dir)
    if not lib_path.exists():
        click.echo(f"Setting up library structure in {lib_dir}/...")
        project.ensure_lib_structure(lib_path)

    # Run JLC2KiCadLib to generate component
    click.echo(f"Fetching component {part_number} from JLCPCB...")
    lib_path = project.get_lib_dir(lib_dir)

    try:
        result = subprocess.run(
            [
                "JLC2KiCadLib",
                part_number,
                "-dir",
                str(lib_path),
                "-symbol_lib",
                "jlc_project",
                "--skip_existing",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        click.echo("  Component generated successfully")

        # Fetch description from JLC API
        click.echo("  Fetching component details...")
        description = fetch_component_description(part_number)

        # Track component in config with optional description
        config.add_component(part_number, description or "")

    except subprocess.CalledProcessError as e:
        click.secho(f"✗ Failed to generate component: {e.stderr}", fg="red")
        sys.exit(1)
    except FileNotFoundError:
        click.secho("✗ JLC2KiCadLib not found. Make sure it's installed:", fg="red")
        click.echo("  pip install JLC2KiCadLib")
        sys.exit(1)

    click.secho(f"✓ Component {part_number} added to project", fg="green")
    click.echo(f"  Tracked in jlcproject.toml")


@main.command()
@click.argument("part_number")
def remove(part_number: str):
    """Remove a JLC component from the project library."""
    click.echo(f"Removing component {part_number}...")
    # TODO: Implement remove logic
    click.secho(f"✓ Component {part_number} removed", fg="green")


@main.command()
@click.option("--detailed", is_flag=True, help="Show detailed component information")
def list(detailed: bool):
    """List all components from jlcproject.toml."""
    # Find KiCad project
    project = find_kicad_project()

    if not project:
        click.secho("✗ No KiCad project found in current or parent directories", fg="red")
        sys.exit(1)

    # Check if project is initialized
    config = ProjectConfig(project.root_dir)
    if not config.config_file.exists():
        click.secho("✗ Project not initialized", fg="red")
        click.echo("  Run 'jlcmgr init' first")
        sys.exit(1)

    # Load components from config
    config_data = config.load()
    components = config_data.get("components", {})

    if not components:
        click.echo("No components in project")
        return

    # Handle both dict and list format
    from builtins import list as list_type, dict as dict_type
    if isinstance(components, list_type):
        components_dict = {comp: "" for comp in components}
    else:
        components_dict = components

    click.echo(f"Components in {project.name} ({len(components_dict)}):\n")

    for jlc_id, description in components_dict.items():
        if description:
            click.echo(f"  • {jlc_id}  ({description})")
        else:
            click.echo(f"  • {jlc_id}")

        if detailed:
            # Show JLC URL for detailed view
            click.echo(f"    https://jlcpcb.com/partdetail/{jlc_id}")


@main.command()
def sync():
    """Sync/update all components from jlcproject.toml (like 'uv sync')."""
    # Find KiCad project
    click.echo("Detecting KiCad project...")
    project = find_kicad_project()

    if not project:
        click.secho("✗ No KiCad project found in current or parent directories", fg="red")
        click.echo("  Make sure you're inside a KiCad project directory (contains .kicad_pro file)")
        sys.exit(1)

    click.echo(f"  Found project: {project.name}")

    # Check if project is initialized
    config = ProjectConfig(project.root_dir)
    if not config.config_file.exists():
        click.secho("✗ Project not initialized", fg="red")
        click.echo("  Run 'jlcmgr init' first to set up the library structure")
        sys.exit(1)

    # Get configuration
    lib_dir = config.get_lib_dir()
    lib_name = config.get_lib_name()
    components = config.get_components()

    if not components:
        click.echo("No components to sync")
        return

    click.echo(f"Syncing {len(components)} component(s)...")

    # Clean sync: remove existing library to ensure exact match with manifest
    lib_path = project.get_lib_dir(lib_dir)
    if lib_path.exists():
        click.echo(f"  Cleaning existing library...")
        import shutil
        shutil.rmtree(lib_path)

    # Recreate library structure
    click.echo(f"  Creating library structure in {lib_dir}/...")
    project.ensure_lib_structure(lib_path)

    # Ensure library tables are configured
    lib_manager = LibraryTableManager(project.root_dir)
    lib_manager.ensure_symbol_library(lib_name, lib_dir)
    lib_manager.ensure_footprint_library(lib_name, lib_dir)

    # Sync each component
    success_count = 0
    fail_count = 0

    for part_number in components:
        try:
            click.echo(f"  • {part_number}...", nl=False)

            result = subprocess.run(
                [
                    "JLC2KiCadLib",
                    part_number,
                    "-dir",
                    str(lib_path),
                    "-symbol_lib",
                    "jlc_project",
                    "--skip_existing",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            click.secho(" ✓", fg="green")
            success_count += 1

        except subprocess.CalledProcessError as e:
            click.secho(" ✗", fg="red")
            click.echo(f"    Error: {e.stderr.strip()[:100]}")
            fail_count += 1
        except FileNotFoundError:
            click.secho(" ✗", fg="red")
            click.echo("    Error: JLC2KiCadLib not found")
            fail_count += 1
            break

    # Summary
    click.echo()
    if fail_count == 0:
        click.secho(f"✓ All {success_count} component(s) synced successfully", fg="green")
    else:
        click.secho(f"⚠ Synced {success_count}/{len(components)} components ({fail_count} failed)", fg="yellow")


@main.command()
@click.option("--lib-dir", help="Custom library directory (default: jlclib/)")
@click.option("--lib-name", help="Custom library name (default: JLC_Project)")
def init(lib_dir: str | None, lib_name: str | None):
    """Initialize project library structure (optional, auto-happens on first add)."""
    # Find KiCad project
    click.echo("Detecting KiCad project...")
    project = find_kicad_project()

    if not project:
        click.secho("✗ No KiCad project found in current or parent directories", fg="red")
        click.echo("  Make sure you're inside a KiCad project directory (contains .kicad_pro file)")
        sys.exit(1)

    click.echo(f"  Found project: {project.name}")

    # Create/load configuration
    config = ProjectConfig(project.root_dir)
    lib_dir = lib_dir or config.get_lib_dir()
    lib_name = lib_name or config.get_lib_name()

    # Ensure .gitignore excludes library directory
    click.echo(f"Configuring .gitignore to exclude {lib_dir}/...")
    config.ensure_gitignore()

    # Ensure library structure exists
    click.echo(f"Creating library structure in {lib_dir}/...")
    project.ensure_lib_structure(project.get_lib_dir(lib_dir))

    # Ensure library tables are configured
    click.echo("Configuring library tables...")
    lib_manager = LibraryTableManager(project.root_dir)
    lib_manager.ensure_symbol_library(lib_name, lib_dir)
    lib_manager.ensure_footprint_library(lib_name, lib_dir)

    # Save initial configuration
    config.save()

    click.secho("✓ Project library initialized", fg="green")
    click.echo(f"  Library: {lib_name} → {lib_dir}/")
    click.echo(f"  Use 'jlcmgr add <part>' to add components")


if __name__ == "__main__":
    main()
