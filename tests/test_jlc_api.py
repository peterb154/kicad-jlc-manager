"""Tests for jlc_api.py (JLC API client)."""

from unittest.mock import Mock, patch

import pytest

from kicad_jlc_manager.jlc_api import fetch_component_description, fetch_component_details


@pytest.fixture
def mock_api_response():
    """Mock API response with component data."""
    return {
        "result": {
            "productIntroEn": "10kΩ ±1% 1/8W 0805 Thick Film Resistors RoHS",
            "componentBrandEn": "UNI-ROYAL",
            "componentModelEn": "0805W8F1002T5E",
            "componentSpecificationEn": "10kΩ ±1% 1/8W 0805",
        }
    }


@pytest.fixture
def mock_empty_response():
    """Mock empty API response."""
    return {"result": None}


def test_fetch_component_description_success(mock_api_response):
    """Test successful component description fetch."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        description = fetch_component_description("C23107")

        assert description == "10kΩ ±1% 1/8W 0805 Thick Film Resistors"
        assert "RoHS" not in description


def test_fetch_component_description_removes_rohs(mock_api_response):
    """Test that RoHS suffix is removed from description."""
    mock_api_response["result"]["productIntroEn"] = "Component Description ROHS"

    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        description = fetch_component_description("C23107")

        assert "ROHS" not in description
        assert "RoHS" not in description


def test_fetch_component_description_truncates_long(mock_api_response):
    """Test that long descriptions are truncated."""
    mock_api_response["result"]["productIntroEn"] = "A" * 150

    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        description = fetch_component_description("C23107")

        assert len(description) <= 100
        assert description.endswith("...")


def test_fetch_component_description_empty_result(mock_empty_response):
    """Test handling empty API result."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_empty_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        description = fetch_component_description("C23107")

        assert description is None


def test_fetch_component_description_network_error():
    """Test handling network errors."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")

        description = fetch_component_description("C23107")

        assert description is None


def test_fetch_component_description_timeout():
    """Test handling timeout errors."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_get.side_effect = TimeoutError("Request timeout")

        description = fetch_component_description("C23107")

        assert description is None


def test_fetch_component_description_http_error():
    """Test handling HTTP errors."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        mock_get.return_value = mock_response

        description = fetch_component_description("C23107")

        assert description is None


def test_fetch_component_description_correct_url():
    """Test that correct URL is constructed."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"result": None}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetch_component_description("C194349")

        expected_url = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C194349"
        mock_get.assert_called_once()
        assert mock_get.call_args[0][0] == expected_url


def test_fetch_component_description_correct_headers():
    """Test that correct headers are sent."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"result": None}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetch_component_description("C194349")

        headers = mock_get.call_args[1]["headers"]
        assert "User-Agent" in headers
        assert "Accept" in headers


def test_fetch_component_details_success(mock_api_response):
    """Test successful component details fetch."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        details = fetch_component_details("C23107")

        assert details is not None
        assert details["productIntroEn"] == mock_api_response["result"]["productIntroEn"]
        assert details["componentBrandEn"] == "UNI-ROYAL"
        assert details["componentModelEn"] == "0805W8F1002T5E"


def test_fetch_component_details_empty_result(mock_empty_response):
    """Test fetch_component_details with empty result."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_empty_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        details = fetch_component_details("C23107")

        assert details is None


def test_fetch_component_details_network_error():
    """Test fetch_component_details handling network errors."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")

        details = fetch_component_details("C23107")

        assert details is None


def test_fetch_component_details_correct_url():
    """Test that fetch_component_details uses correct URL."""
    with patch("kicad_jlc_manager.jlc_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"result": None}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetch_component_details("C194349")

        expected_url = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C194349"
        mock_get.assert_called_once()
        assert mock_get.call_args[0][0] == expected_url
