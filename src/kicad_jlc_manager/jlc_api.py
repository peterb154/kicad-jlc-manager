"""JLC API client for fetching component information."""

import requests
from typing import Optional


def fetch_component_description(jlc_id: str) -> Optional[str]:
    """
    Fetch component description from JLC API.

    Returns a human-readable description like:
    - "76.8kOhm 0603 Resistor"
    - "LM2596S-5.0 Buck Converter"
    - "10uF 25V Capacitor 0805"

    Returns None if fetch fails.
    """
    try:
        # JLC API endpoint (this is the endpoint JLC2KiCadLib uses)
        url = f"https://yun.easyeda.com/api/products/{jlc_id}/components?version=6.5.43"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract useful description from the API response
        if "result" in data and data["result"]:
            component = data["result"]

            # Try to build a nice description from available fields
            description = component.get("description", "")

            # Clean up the description (remove excessive details)
            if description:
                # Take first line if multi-line
                description = description.split('\n')[0].strip()
                # Limit length
                if len(description) > 80:
                    description = description[:77] + "..."

            return description if description else None

    except Exception:
        # Silently fail - description is optional
        return None


def fetch_component_details(jlc_id: str) -> Optional[dict]:
    """
    Fetch full component details from JLC API.

    Returns dict with keys like:
    - description: str
    - manufacturer: str
    - mfr_part: str
    - package: str
    - price: str
    - stock: int
    """
    try:
        url = f"https://yun.easyeda.com/api/products/{jlc_id}/components?version=6.5.43"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "result" in data and data["result"]:
            return data["result"]

    except Exception:
        return None
