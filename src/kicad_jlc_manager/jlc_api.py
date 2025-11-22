"""JLC API client for fetching component information."""


import requests


def fetch_component_description(jlc_id: str) -> str | None:
    """
    Fetch component description from LCSC/JLCPCB API.

    Returns a human-readable description like:
    - "10uF 25V X5R ±10% 0805 Multilayer Ceramic Capacitors"
    - "76.8kOhm 0603 Resistor"
    - "LM2596S-5.0 Buck Converter"

    Returns None if fetch fails.
    """
    try:
        # LCSC API endpoint (LCSC is JLCPCB's component supplier)
        url = f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={jlc_id}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract description from the API response
        if "result" in data and data["result"]:
            result = data["result"]

            # Get the English introduction which has a nice concise description
            description = result.get("productIntroEn", "")

            if description:
                # Clean up the description
                description = description.strip()
                # Remove "RoHS" suffix if present
                description = description.replace(" RoHS", "").replace(" ROHS", "")
                # Limit length
                if len(description) > 100:
                    description = description[:97] + "..."

                return description if description else None

    except Exception:
        # Silently fail - description is optional
        return None


def fetch_component_details(jlc_id: str) -> dict | None:
    """
    Fetch full component details from LCSC/JLCPCB API.

    Returns dict with keys like:
    - productIntroEn: str (description)
    - componentBrandEn: str (manufacturer)
    - componentModelEn: str (model/part number)
    - componentSpecificationEn: str (specifications)
    - etc.
    """
    try:
        url = f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={jlc_id}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "result" in data and data["result"]:
            return data["result"]

    except Exception:
        return None
