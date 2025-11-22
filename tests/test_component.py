"""Tests for component.py (component utilities)."""

from pathlib import Path

import pytest

from kicad_jlc_manager.component import (
    determine_component_type,
    extract_component_value,
    get_component_details_from_symbol,
    get_installed_components,
    get_installed_components_with_part_numbers,
    remove_component_footprint,
)


def test_get_installed_components_empty(tmp_project_with_lib):
    """Test getting components from empty symbol library."""
    symbol_file = tmp_project_with_lib / "jlclib" / "symbol" / "jlc_project.kicad_sym"
    components = get_installed_components(symbol_file)
    assert components == set()


def test_get_installed_components_nonexistent_file(tmp_project):
    """Test getting components from nonexistent file."""
    symbol_file = tmp_project / "nonexistent.kicad_sym"
    components = get_installed_components(symbol_file)
    assert components == set()


def test_get_installed_components(sample_symbol_lib):
    """Test getting components from symbol library."""
    symbol_file = sample_symbol_lib / "jlclib" / "symbol" / "jlc_project.kicad_sym"
    components = get_installed_components(symbol_file)

    assert "C194349" in components
    assert "C23107" in components
    assert len(components) == 2


def test_get_installed_components_with_part_numbers(sample_symbol_lib):
    """Test getting components with part numbers."""
    symbol_file = sample_symbol_lib / "jlclib" / "symbol" / "jlc_project.kicad_sym"
    components = get_installed_components_with_part_numbers(symbol_file)

    assert components["C194349"] == "LM2596S-5.0/TR"
    assert components["C23107"] == "0805W8F1002T5E"


def test_get_installed_components_with_part_numbers_empty(tmp_project_with_lib):
    """Test getting components with part numbers from empty library."""
    symbol_file = tmp_project_with_lib / "jlclib" / "symbol" / "jlc_project.kicad_sym"
    components = get_installed_components_with_part_numbers(symbol_file)
    assert components == {}


def test_get_installed_components_with_part_numbers_nonexistent(tmp_project):
    """Test getting components with part numbers from nonexistent file."""
    symbol_file = tmp_project / "nonexistent.kicad_sym"
    components = get_installed_components_with_part_numbers(symbol_file)
    assert components == {}


def test_get_component_details_from_symbol(sample_symbol_lib):
    """Test getting full component details from symbol library."""
    symbol_file = sample_symbol_lib / "jlclib" / "symbol" / "jlc_project.kicad_sym"
    details = get_component_details_from_symbol(symbol_file)

    assert "C194349" in details
    assert details["C194349"]["part_number"] == "LM2596S-5.0/TR"
    assert details["C194349"]["value"] == "LM2596S-5.0"
    assert details["C194349"]["description"] == "Buck converter"

    assert "C23107" in details
    assert details["C23107"]["part_number"] == "0805W8F1002T5E"
    assert details["C23107"]["value"] == "10kΩ"


def test_get_component_details_from_symbol_empty(tmp_project_with_lib):
    """Test getting details from empty symbol library."""
    symbol_file = tmp_project_with_lib / "jlclib" / "symbol" / "jlc_project.kicad_sym"
    details = get_component_details_from_symbol(symbol_file)
    assert details == {}


def test_remove_component_footprint(tmp_project_with_lib):
    """Test removing a component footprint."""
    footprint_dir = tmp_project_with_lib / "jlclib" / "footprint"
    footprint_file = footprint_dir / "TEST_FOOTPRINT.kicad_mod"
    footprint_file.write_text("(module TEST_FOOTPRINT)")

    result = remove_component_footprint(footprint_dir, "TEST_FOOTPRINT")

    assert result is True
    assert not footprint_file.exists()


def test_remove_component_footprint_not_found(tmp_project_with_lib):
    """Test removing a footprint that doesn't exist."""
    footprint_dir = tmp_project_with_lib / "jlclib" / "footprint"

    result = remove_component_footprint(footprint_dir, "NONEXISTENT")

    assert result is False


def test_determine_component_type_resistor():
    """Test determining resistor component type."""
    api_details = {
        "productIntroEn": "10kΩ ±1% 1/8W 0805 Thick Film Resistors",
        "parentCatalogName": "Resistors",
        "catalogName": "Chip Resistor",
    }

    comp_type = determine_component_type(api_details)
    assert comp_type == "resistor"


def test_determine_component_type_capacitor():
    """Test determining capacitor component type."""
    api_details = {
        "productIntroEn": "100nF 50V X7R ±10% 0805 Multilayer Ceramic Capacitors",
        "parentCatalogName": "Capacitors",
        "catalogName": "MLCC",
    }

    comp_type = determine_component_type(api_details)
    assert comp_type == "capacitor"


def test_determine_component_type_inductor():
    """Test determining inductor component type."""
    api_details = {
        "productIntroEn": "1uH ±20% 3A 0805 Power Inductors",
        "parentCatalogName": "Inductors",
        "catalogName": "Power Inductor",
    }

    comp_type = determine_component_type(api_details)
    assert comp_type == "inductor"


def test_determine_component_type_active():
    """Test determining active component type."""
    api_details = {
        "productIntroEn": "Buck Converter IC 3.5V-40V 3A TO-263",
        "parentCatalogName": "Power Management",
        "catalogName": "Voltage Regulator",
    }

    comp_type = determine_component_type(api_details)
    assert comp_type == "active"


def test_determine_component_type_transistor():
    """Test determining transistor as active type."""
    api_details = {
        "productIntroEn": "N-Channel MOSFET 30V 5A SOT-23",
        "parentCatalogName": "Transistors",
        "catalogName": "MOSFET",
    }

    comp_type = determine_component_type(api_details)
    assert comp_type == "active"


def test_determine_component_type_unknown():
    """Test determining unknown component type."""
    api_details = {
        "productIntroEn": "Some unknown component",
        "parentCatalogName": "Other",
        "catalogName": "Misc",
    }

    comp_type = determine_component_type(api_details)
    assert comp_type == "unknown"


def test_determine_component_type_none():
    """Test determining component type with None input."""
    comp_type = determine_component_type(None)
    assert comp_type == "unknown"


def test_extract_component_value_resistor():
    """Test extracting resistor value."""
    api_details = {
        "productIntroEn": "10kΩ ±1% 1/8W 0805 Thick Film Resistors",
        "productModel": "0805W8F1002T5E",
    }

    value = extract_component_value(api_details, "resistor")
    assert value == "10kΩ"


def test_extract_component_value_resistor_mega_ohm():
    """Test extracting mega-ohm resistor value."""
    api_details = {
        "productIntroEn": "1MΩ ±5% 1/4W 1206 Thick Film Resistors",
        "productModel": "1206W4F1004T5E",
    }

    value = extract_component_value(api_details, "resistor")
    assert value == "1MΩ"


def test_extract_component_value_capacitor():
    """Test extracting capacitor value."""
    api_details = {
        "productIntroEn": "100nF 50V X7R ±10% 0805 Multilayer Ceramic Capacitors",
        "productModel": "CL21B104KBFNNNE",
    }

    value = extract_component_value(api_details, "capacitor")
    assert value == "100nF"


def test_extract_component_value_capacitor_micro():
    """Test extracting micro-farad capacitor value."""
    api_details = {
        "productIntroEn": "10uF 25V X5R ±10% 0805 Multilayer Ceramic Capacitors",
        "productModel": "CL21A106KPFNNNE",
    }

    value = extract_component_value(api_details, "capacitor")
    assert value == "10µF"


def test_extract_component_value_inductor():
    """Test extracting inductor value."""
    api_details = {
        "productIntroEn": "1uH ±20% 3A 0805 Power Inductors",
        "productModel": "SWPA4018S1R0MT",
    }

    value = extract_component_value(api_details, "inductor")
    assert value == "1µH"


def test_extract_component_value_active():
    """Test extracting active component value (model number)."""
    api_details = {
        "productIntroEn": "Buck Converter IC 3.5V-40V 3A TO-263",
        "productModel": "LM2596S-5.0/TR",
    }

    value = extract_component_value(api_details, "active")
    assert value == "LM2596S-5.0/TR"


def test_extract_component_value_active_with_suffix():
    """Test extracting active component value with common suffix removed."""
    api_details = {
        "productIntroEn": "Operational Amplifier",
        "productModel": "LM358DR-C15",
    }

    value = extract_component_value(api_details, "active")
    # Should remove -C15 suffix
    assert value == "LM358DR"


def test_extract_component_value_no_match():
    """Test extracting value when no pattern matches."""
    api_details = {
        "productIntroEn": "Some component without value",
        "productModel": "TEST123",
    }

    value = extract_component_value(api_details, "resistor")
    # Should fall back to model
    assert value == "TEST123"


def test_extract_component_value_empty_model():
    """Test extracting value with empty model."""
    api_details = {
        "productIntroEn": "Component description",
        "productModel": "",
    }

    value = extract_component_value(api_details, "unknown")
    assert value is None


def test_extract_component_value_unknown_type():
    """Test extracting value for unknown component type."""
    api_details = {
        "productIntroEn": "Unknown component",
        "productModel": "ABC123",
    }

    value = extract_component_value(api_details, "unknown")
    assert value == "ABC123"
