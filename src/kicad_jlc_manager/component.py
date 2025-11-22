"""Component management utilities."""

import re
import shutil
from pathlib import Path


def get_installed_components(symbol_file: Path) -> set[str]:
    """
    Extract all JLC component IDs from the symbol library.

    Parses the symbol file to find all LCSC property values which contain
    the JLC part numbers (e.g., C194349).
    """
    if not symbol_file.exists():
        return set()

    content = symbol_file.read_text()
    jlc_ids = set()

    # Parse for LCSC property which contains the JLC ID
    # Format: (property "LCSC" "C194349" (id 5) (at 0 0 0)
    lcsc_pattern = r'\(property "LCSC" "([^"]+)"'
    matches = re.findall(lcsc_pattern, content)
    jlc_ids.update(matches)

    return jlc_ids


def get_installed_components_with_part_numbers(symbol_file: Path) -> dict[str, str]:
    """
    Extract JLC IDs mapped to their manufacturer part numbers from the symbol library.

    Returns:
        Dict mapping JLC IDs to part numbers, e.g., {"C194349": "LM2596S-5_0/TR"}
    """
    if not symbol_file.exists():
        return {}

    content = symbol_file.read_text()
    lines = content.splitlines()

    components = {}
    current_symbol = None
    current_lcsc = None

    for line in lines:
        # Look for symbol definition: (symbol "PART_NUMBER"
        symbol_match = re.search(r'\(symbol "([^"]+)"', line)
        if symbol_match:
            current_symbol = symbol_match.group(1)
            # Replace KiCad escape sequences
            current_symbol = current_symbol.replace("{slash}", "/")
            current_lcsc = None
            continue

        # Look for LCSC property: (property "LCSC" "C194349"
        lcsc_match = re.search(r'\(property "LCSC" "([^"]+)"', line)
        if lcsc_match and current_symbol:
            current_lcsc = lcsc_match.group(1)
            components[current_lcsc] = current_symbol
            continue

    return components


def get_component_details_from_symbol(symbol_file: Path) -> dict[str, dict[str, str]]:
    """
    Extract full component details from the symbol library.

    Returns:
        Dict mapping JLC IDs to component info:
        {
            "C194349": {
                "part_number": "LM2596S-5_0/TR",
                "value": "LM2596S-5.0",
                "description": "Buck converter..."
            }
        }
    """
    if not symbol_file.exists():
        return {}

    content = symbol_file.read_text()

    # Split into symbol blocks
    symbol_blocks = re.split(r'(?=[\t ]*\(symbol\s+"[^"]+")', content)[1:]

    components = {}

    for block in symbol_blocks:
        # Extract symbol name
        symbol_match = re.search(r'[\t ]*\(symbol\s+"([^"]+)"', block)
        if not symbol_match:
            continue

        symbol_name = symbol_match.group(1)

        # Skip sub-symbols
        if '_' in symbol_name and re.match(r'.*_\d+_\d+$', symbol_name):
            continue

        # Extract LCSC
        lcsc_match = re.search(r'\(property\s+"LCSC"\s+"([^"]+)"', block)
        if not lcsc_match:
            continue

        lcsc = lcsc_match.group(1)

        # Extract Value
        value_match = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block)
        value = value_match.group(1) if value_match else symbol_name

        # Replace KiCad escape sequences in value
        value = value.replace("{slash}", "/")

        # Extract Description
        desc_match = re.search(r'\(property\s+"Description"\s+"([^"]+)"', block)
        description = desc_match.group(1) if desc_match else ""

        components[lcsc] = {
            "part_number": symbol_name.replace("{slash}", "/"),
            "value": value,
            "description": description
        }

    return components


def remove_component_from_symbol_lib(symbol_file: Path, jlc_id: str) -> bool:
    """
    Remove a component's symbol entries from the symbol library file.

    Returns True if component was found and removed.
    """
    if not symbol_file.exists():
        return False

    # TODO: Implement proper symbol removal
    # This is complex and would require parsing the S-expression format
    # For MVP, we rebuild the entire library instead (see remove command in cli.py)

    return False


def remove_component_footprint(footprint_dir: Path, footprint_name: str) -> bool:
    """
    Remove a footprint file.

    Returns True if footprint was found and removed.
    """
    footprint_file = footprint_dir / f"{footprint_name}.kicad_mod"
    if footprint_file.exists():
        footprint_file.unlink()
        return True
    return False


def determine_component_type(api_details: dict) -> str:
    """Determine if component is resistor, capacitor, inductor, or active based on LCSC API data."""
    if not api_details:
        return "unknown"

    # Get category information from LCSC API
    description = api_details.get("productIntroEn", "").lower()
    parent_category = api_details.get("parentCatalogName", "").lower()
    category = api_details.get("catalogName", "").lower()

    # Passive components - check categories and description
    passive_categories = {
        'resistor': 'resistor',
        'capacitor': 'capacitor',
        'inductor': 'inductor',
        'coil': 'inductor',
        'choke': 'inductor'
    }

    for keyword, comp_type in passive_categories.items():
        if keyword in parent_category or keyword in category or keyword in description:
            return comp_type

    # Active components (transistors, ICs, etc.)
    active_keywords = [
        'transistor', 'mosfet', 'bjt', 'fet', 'thyristor',
        'logic', 'interface', 'power management', 'voltage regulator',
        'microcontroller', 'processor', 'memory', 'analog',
        'sensor', 'amplifier', 'switching controller', 'driver',
        'diode', 'led'
    ]

    for keyword in active_keywords:
        if keyword in parent_category or keyword in category or keyword in description:
            return "active"

    # Default to unknown
    return "unknown"


def extract_component_value(api_details: dict, comp_type: str) -> str | None:
    """Extract appropriate value for the KiCad Value field based on component type."""
    description = api_details.get("productIntroEn", "")
    model = api_details.get("productModel", "")

    if comp_type == "resistor":
        # Look for resistance values like "76.8kΩ", "120Ω", "10MΩ"
        resistance_pattern = r'(\d+(?:\.\d+)?(?:k|M|G)?Ω)'
        match = re.search(resistance_pattern, description)
        if match:
            return match.group(1)

    elif comp_type == "capacitor":
        # Look for capacitance values like "10uF", "100nF", "22pF"
        cap_pattern = r'(\d+(?:\.\d+)?(?:p|n|u|m)?F)'
        match = re.search(cap_pattern, description)
        if match:
            return match.group(1).replace('u', 'µ')  # Use proper micro symbol

    elif comp_type == "inductor":
        # Look for inductance values like "1uH", "100nH", "2.2mH"
        ind_pattern = r'(\d+(?:\.\d+)?(?:n|u|m)?H)'
        match = re.search(ind_pattern, description)
        if match:
            return match.group(1).replace('u', 'µ')  # Use proper micro symbol

    elif comp_type == "active":
        # For active components, use the model/part number
        if model:
            # Clean up model name - remove common suffixes
            clean_model = model
            clean_model = re.sub(r'[,_-][A-Z0-9]{1,4}$', '', clean_model)
            clean_model = re.sub(r'[_-]?C\d+$', '', clean_model)
            return clean_model

    # Fallback to model
    return model if model else None


def update_symbol_in_file(
    symbol_file: Path,
    jlc_id: str,
    api_details: dict | None
) -> bool:
    """
    Update a component's symbol in the symbol file with better descriptions and values.

    Args:
        symbol_file: Path to the .kicad_sym file
        jlc_id: JLC part number (e.g., "C194349")
        api_details: Dict from LCSC API with component details

    Returns:
        True if symbol was found and updated
    """
    if not symbol_file.exists() or not api_details:
        return False

    try:
        # Create backup
        backup_file = symbol_file.with_suffix('.kicad_sym.bak')
        shutil.copy2(symbol_file, backup_file)

        content = symbol_file.read_text(encoding='utf-8')

        # Split into symbol blocks
        symbol_blocks = re.split(r'(?=[\t ]*\(symbol\s+"[^"]+")', content)
        header = symbol_blocks[0]
        symbol_blocks = symbol_blocks[1:]

        updated = False
        new_blocks = []

        for block in symbol_blocks:
            # Extract symbol name and LCSC number
            symbol_match = re.search(r'[\t ]*\(symbol\s+"([^"]+)"', block)
            if not symbol_match:
                new_blocks.append(block)
                continue

            symbol_name = symbol_match.group(1)

            # Skip sub-symbols
            if '_' in symbol_name and re.match(r'.*_\d+_\d+$', symbol_name):
                new_blocks.append(block)
                continue

            # Find LCSC number for this symbol
            lcsc_match = re.search(r'\(property\s+"LCSC"\s+"([^"]+)"', block)
            if not lcsc_match or lcsc_match.group(1) != jlc_id:
                new_blocks.append(block)
                continue

            # This is the symbol we want to update
            new_block = block
            comp_type = determine_component_type(api_details)

            # Update Value field with appropriate electrical value or part number
            extracted_value = extract_component_value(api_details, comp_type)
            if extracted_value:
                value_match = re.search(r'(property\s+"Value"\s+)"([^"]+)"', new_block)
                if value_match:
                    current_value = value_match.group(2)
                    # Replace if current value looks like a manufacturer part number
                    if len(current_value) > 6 and re.match(r'^[A-Z0-9_,-]+$', current_value, re.IGNORECASE):
                        new_block = re.sub(
                            r'(property\s+"Value"\s+)"([^"]+)"',
                            rf'\1"{extracted_value}"',
                            new_block,
                            count=1
                        )
                        updated = True

            # Update Description field with technical specifications
            description = api_details.get("productIntroEn", "")
            if description:
                # Clean up description
                description = description.strip().replace(" RoHS", "").replace(" ROHS", "")
                desc_match = re.search(r'(\(property\s+"Description"\s+)"([^"]*)"', new_block)
                if desc_match:
                    # Update existing Description
                    new_block = re.sub(
                        r'(\(property\s+"Description"\s+)"([^"]*)"',
                        rf'\1"{description}"',
                        new_block,
                        count=1
                    )
                    updated = True
                else:
                    # Add Description property after Datasheet if it doesn't exist
                    # Match the complete Datasheet property, handling multi-line and nested parentheses
                    datasheet_pattern = r'(\(property\s+"Datasheet"[^\(]*(?:\([^\)]*\)[^\(]*)*\))'
                    datasheet_match = re.search(datasheet_pattern, new_block, re.DOTALL)
                    if datasheet_match:
                        # Insert Description after Datasheet property
                        insert_pos = datasheet_match.end()
                        desc_property = f'\n    (property "Description" "{description}" (id 6) (at 0 0 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )'
                        new_block = new_block[:insert_pos] + desc_property + new_block[insert_pos:]
                        updated = True

            # Update ki_keywords with searchable terms
            keywords = [jlc_id]
            model = api_details.get("productModel", "")
            brand = api_details.get("brandNameEn", "")
            if brand:
                keywords.append(brand)
            if model:
                keywords.append(model)

            if len(keywords) > 1:
                keyword_string = ' '.join(keywords)
                keywords_match = re.search(r'(\(property\s+"ki_keywords"\s+)"([^"]*)"', new_block)
                if keywords_match and keywords_match.group(2).strip() == jlc_id:
                    new_block = re.sub(
                        r'(\(property\s+"ki_keywords"\s+)"([^"]*)"',
                        rf'\1"{keyword_string}"',
                        new_block,
                        count=1
                    )
                    updated = True

            new_blocks.append(new_block)

        # Write updated content
        if updated:
            new_content = header + ''.join(new_blocks)
            symbol_file.write_text(new_content, encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"Error updating symbol: {e}")
        return False
