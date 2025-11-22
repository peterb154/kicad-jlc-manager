"""CLI interface for kicad-jlc-manager using Click."""

import subprocess
import sys
from pathlib import Path

import click

from .component import update_symbol_in_file
from .config import ProjectConfig
from .jlc_api import fetch_component_details
from .library import LibraryTableManager
from .project import find_kicad_project


def get_project_or_cwd():
    """Get KiCad project if found, otherwise use current directory."""
    project = find_kicad_project()

    if project:
        return project, project.root_dir
    else:
        # No KiCad project yet - use current directory
        root_dir = Path.cwd()
        from .project import KiCadProject
        return KiCadProject(root_dir), root_dir


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
    # Get project (or current directory)
    project, root_dir = get_project_or_cwd()

    # Check if project is initialized
    config = ProjectConfig(root_dir)
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
        subprocess.run(
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

        # Fetch full details from JLC API
        click.echo("  Fetching component details from LCSC API...")
        api_details = fetch_component_details(part_number)

        # Update symbol file with better descriptions and values
        if api_details:
            click.echo("  Updating symbol with improved descriptions and values...")
            symbol_file = project.get_symbol_lib_path(lib_path)
            if update_symbol_in_file(symbol_file, part_number, api_details):
                click.echo("  ✓ Symbol updated with component details")
            else:
                click.echo("  ◦ Symbol already has content or no API data")

        # Track component in config
        config.add_component(part_number)

    except subprocess.CalledProcessError as e:
        click.secho(f"✗ Failed to generate component: {e.stderr}", fg="red")
        sys.exit(1)
    except FileNotFoundError:
        click.secho("✗ JLC2KiCadLib not found. Make sure it's installed:", fg="red")
        click.echo("  pip install JLC2KiCadLib")
        sys.exit(1)

    click.secho(f"✓ Component {part_number} added to project", fg="green")
    click.echo("  Tracked in jlcproject.toml")


@main.command()
@click.argument("part_number")
def remove(part_number: str):
    """Remove a JLC component from the project library."""
    # Get project (or current directory)
    project, root_dir = get_project_or_cwd()

    # Check if project is initialized
    config = ProjectConfig(root_dir)
    if not config.config_file.exists():
        click.secho("✗ Project not initialized", fg="red")
        click.echo("  Run 'jlcmgr init' first")
        sys.exit(1)

    # Remove component from config
    click.echo(f"Removing component {part_number}...")
    if not config.remove_component(part_number):
        click.secho(f"✗ Component {part_number} not found in jlcproject.toml", fg="red")
        sys.exit(1)

    click.echo("  Updated jlcproject.toml")

    # Rebuild library to remove the component files
    # This is simpler and safer than trying to edit the symbol file directly
    click.echo("  Rebuilding library...")

    lib_dir = config.get_lib_dir()
    lib_name = config.get_lib_name()
    components = config.get_components()

    lib_path = project.get_lib_dir(lib_dir)
    if lib_path.exists():
        import shutil
        shutil.rmtree(lib_path)

    # Recreate library structure
    project.ensure_lib_structure(lib_path)

    # Ensure library tables are configured
    lib_manager = LibraryTableManager(project.root_dir)
    lib_manager.ensure_symbol_library(lib_name, lib_dir)
    lib_manager.ensure_footprint_library(lib_name, lib_dir)

    # Re-download remaining components and update their symbols
    if components:
        symbol_file = project.get_symbol_lib_path(lib_path)
        for comp in components:
            try:
                # Generate component with JLC2KiCadLib
                subprocess.run(
                    [
                        "JLC2KiCadLib",
                        comp,
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

                # Update symbol with better descriptions and values
                api_details = fetch_component_details(comp)
                if api_details:
                    update_symbol_in_file(symbol_file, comp, api_details)

            except (subprocess.CalledProcessError, FileNotFoundError):
                pass  # Ignore errors during rebuild

    click.secho(f"✓ Component {part_number} removed", fg="green")


@main.command()
@click.option("--detailed", is_flag=True, help="Show detailed component information")
def list(detailed: bool):
    """List all components installed in the symbol library."""
    from .component import get_component_details_from_symbol

    # Get project (or current directory)
    project, root_dir = get_project_or_cwd()

    # Check if project is initialized
    config = ProjectConfig(root_dir)
    if not config.config_file.exists():
        click.secho("✗ Project not initialized", fg="red")
        click.echo("  Run 'jlcmgr init' first")
        sys.exit(1)

    # Get installed components from symbol file (source of truth)
    lib_dir = config.get_lib_dir()
    symbol_file = project.get_symbol_lib_path(project.get_lib_dir(lib_dir))
    components = get_component_details_from_symbol(symbol_file)

    if not components:
        click.echo("No components in library")
        return

    click.echo(f"Components in {project.name} ({len(components)}):\n")

    for jlc_id, info in components.items():
        value = info.get("value", "")
        description = info.get("description", "")

        # Build single-line output: JLC ID, value, description
        line_parts = [f"  • {jlc_id}"]
        if value:
            line_parts.append(value)
        if description:
            line_parts.append(f"- {description}")

        click.echo("  ".join(line_parts))

        if detailed:
            # Show JLC URL for detailed view
            click.echo(f"    https://jlcpcb.com/partdetail/{jlc_id}")


@main.command()
def sync():
    """Sync/update all components from jlcproject.toml (like 'uv sync')."""
    # Get project (or current directory)
    project, root_dir = get_project_or_cwd()

    # Check if project is initialized
    config = ProjectConfig(root_dir)
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
        click.echo("  Cleaning existing library...")
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
    symbol_file = project.get_symbol_lib_path(lib_path)

    for part_number in components:
        try:
            click.echo(f"  • {part_number}...", nl=False)

            # Generate component with JLC2KiCadLib
            subprocess.run(
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

            # Update symbol with better descriptions and values
            api_details = fetch_component_details(part_number)
            if api_details:
                update_symbol_in_file(symbol_file, part_number, api_details)

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
    """Initialize project library structure before or after creating KiCad project."""
    # Get project (or current directory)
    project, root_dir = get_project_or_cwd()

    if project.is_valid:
        click.echo(f"Found KiCad project: {project.name}")
    else:
        # Create minimal KiCad project files
        project_name = root_dir.name
        click.echo(f"No KiCad project found - creating minimal project: {project_name}")
        project.create_minimal_project(project_name)
        click.echo(f"  Created {project_name}.kicad_pro, .kicad_sch, .kicad_pcb")

    # Create/load configuration
    config = ProjectConfig(root_dir)
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
    lib_manager = LibraryTableManager(root_dir)
    lib_manager.ensure_symbol_library(lib_name, lib_dir)
    lib_manager.ensure_footprint_library(lib_name, lib_dir)

    # Save initial configuration
    config.save()

    click.secho("✓ Project library initialized", fg="green")
    click.echo(f"  Library: {lib_name} → {lib_dir}/")
    click.echo("  Use 'jlcmgr add <part>' to add components")


if __name__ == "__main__":
    main()
