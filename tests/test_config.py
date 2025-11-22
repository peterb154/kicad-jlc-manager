"""Tests for config.py (ProjectConfig)."""

from pathlib import Path

from kicad_jlc_manager.config import ProjectConfig


def test_project_config_init(tmp_project):
    """Test ProjectConfig initialization."""
    config = ProjectConfig(tmp_project)
    assert config.project_root == tmp_project
    assert config.config_file == tmp_project / "jlcproject.toml"
    assert config._config is None


def test_load_default_config(tmp_project):
    """Test loading default config when file doesn't exist."""
    config = ProjectConfig(tmp_project)
    data = config.load()

    assert data["project"]["lib-dir"] == "jlclib"
    assert data["project"]["lib-name"] == "JLC_Project"
    assert data["components"] == []


def test_load_existing_config(sample_toml_config):
    """Test loading existing config from file."""
    config = ProjectConfig(sample_toml_config)
    data = config.load()

    assert data["project"]["lib-dir"] == "jlclib"
    assert data["project"]["lib-name"] == "JLC_Project"
    assert "C194349" in data["components"]
    assert "C23107" in data["components"]


def test_save_config(tmp_project):
    """Test saving config to file."""
    config = ProjectConfig(tmp_project)
    config._config = {
        "project": {"lib-dir": "jlclib", "lib-name": "JLC_Project"},
        "components": ["C194349", "C23107"],
    }
    config.save()

    assert config.config_file.exists()
    content = config.config_file.read_text()

    # Verify components are at root level
    assert 'components = [' in content
    assert '"C194349"' in content
    assert '"C23107"' in content
    assert '[project]' in content


def test_save_with_dict_components(tmp_project):
    """Test saving config with dict format components (backward compatibility)."""
    config = ProjectConfig(tmp_project)
    config._config = {
        "project": {"lib-dir": "jlclib", "lib-name": "JLC_Project"},
        "components": {"C194349": "", "C23107": ""},
    }
    config.save()

    content = config.config_file.read_text()
    assert '"C194349"' in content
    assert '"C23107"' in content


def test_get_lib_dir(sample_toml_config):
    """Test getting library directory."""
    config = ProjectConfig(sample_toml_config)
    assert config.get_lib_dir() == "jlclib"


def test_get_lib_dir_default(tmp_project):
    """Test getting library directory with default value."""
    config = ProjectConfig(tmp_project)
    assert config.get_lib_dir() == "jlclib"


def test_get_lib_name(sample_toml_config):
    """Test getting library name."""
    config = ProjectConfig(sample_toml_config)
    assert config.get_lib_name() == "JLC_Project"


def test_get_lib_name_default(tmp_project):
    """Test getting library name with default value."""
    config = ProjectConfig(tmp_project)
    assert config.get_lib_name() == "JLC_Project"


def test_get_components(sample_toml_config):
    """Test getting components list."""
    config = ProjectConfig(sample_toml_config)
    components = config.get_components()

    assert isinstance(components, list)
    assert "C194349" in components
    assert "C23107" in components
    assert len(components) == 2


def test_get_components_empty(tmp_project):
    """Test getting components from empty config."""
    config = ProjectConfig(tmp_project)
    components = config.get_components()
    assert components == []


def test_get_components_dict_format(tmp_project):
    """Test getting components from dict format (backward compatibility)."""
    # Create a TOML file with dict format
    config_file = tmp_project / "jlcproject.toml"
    config_content = """[components]
C194349 = "desc"
C23107 = "desc2"

[project]
lib-dir = "jlclib"
"""
    config_file.write_text(config_content)

    config = ProjectConfig(tmp_project)
    components = config.get_components()
    assert isinstance(components, list)
    assert "C194349" in components
    assert "C23107" in components


def test_get_components_with_descriptions(tmp_project):
    """Test getting components with descriptions from TOML comments."""
    config_file = tmp_project / "jlcproject.toml"
    config_content = """components = [
    "C194349",  # Buck converter
    "C23107",  # 10kOhm resistor
]

[project]
lib-dir = "jlclib"
"""
    config_file.write_text(config_content)

    config = ProjectConfig(tmp_project)
    components_dict = config.get_components_with_descriptions()

    assert components_dict["C194349"] == "Buck converter"
    assert components_dict["C23107"] == "10kOhm resistor"


def test_get_components_with_descriptions_no_comments(sample_toml_config):
    """Test getting components with descriptions when no comments exist."""
    config = ProjectConfig(sample_toml_config)
    components_dict = config.get_components_with_descriptions()

    assert components_dict["C194349"] == ""
    assert components_dict["C23107"] == ""


def test_add_component(tmp_project):
    """Test adding a component."""
    config = ProjectConfig(tmp_project)
    config.load()
    config.add_component("C194349")

    components = config.get_components()
    assert "C194349" in components


def test_add_component_duplicate(tmp_project):
    """Test adding a duplicate component (should not add twice)."""
    config = ProjectConfig(tmp_project)
    config.load()
    config.add_component("C194349")
    config.add_component("C194349")

    components = config.get_components()
    assert components.count("C194349") == 1


def test_add_component_multiple(tmp_project):
    """Test adding multiple components."""
    config = ProjectConfig(tmp_project)
    config.load()
    config.add_component("C194349")
    config.add_component("C23107")

    components = config.get_components()
    assert len(components) == 2
    assert "C194349" in components
    assert "C23107" in components


def test_remove_component(sample_toml_config):
    """Test removing a component."""
    config = ProjectConfig(sample_toml_config)
    result = config.remove_component("C194349")

    assert result is True
    components = config.get_components()
    assert "C194349" not in components
    assert "C23107" in components


def test_remove_component_not_found(sample_toml_config):
    """Test removing a component that doesn't exist."""
    config = ProjectConfig(sample_toml_config)
    result = config.remove_component("C99999")

    assert result is False
    components = config.get_components()
    assert len(components) == 2


def test_ensure_gitignore_new_file(tmp_project):
    """Test creating new .gitignore file."""
    config = ProjectConfig(tmp_project)
    config.load()
    config.ensure_gitignore()

    gitignore = tmp_project / ".gitignore"
    assert gitignore.exists()

    content = gitignore.read_text()
    assert "jlclib/" in content
    assert "# JLC component libraries (generated)" in content


def test_ensure_gitignore_existing_file(tmp_project):
    """Test updating existing .gitignore file."""
    gitignore = tmp_project / ".gitignore"
    gitignore.write_text("*.bak\n")

    config = ProjectConfig(tmp_project)
    config.load()
    config.ensure_gitignore()

    content = gitignore.read_text()
    assert "*.bak" in content
    assert "jlclib/" in content


def test_ensure_gitignore_already_exists(tmp_project):
    """Test .gitignore when jlclib is already ignored."""
    gitignore = tmp_project / ".gitignore"
    gitignore.write_text("jlclib/\n")

    config = ProjectConfig(tmp_project)
    config.load()
    config.ensure_gitignore()

    content = gitignore.read_text()
    # Should not duplicate
    assert content.count("jlclib/") == 1


def test_ensure_gitignore_custom_lib_dir(tmp_project):
    """Test .gitignore with custom library directory."""
    config = ProjectConfig(tmp_project)
    config._config = {
        "project": {"lib-dir": "custom_lib", "lib-name": "JLC_Project"},
        "components": [],
    }
    config.save()
    config.ensure_gitignore()

    gitignore = tmp_project / ".gitignore"
    content = gitignore.read_text()
    assert "custom_lib/" in content
