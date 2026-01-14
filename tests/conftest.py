"""Pytest configuration and shared fixtures."""
import os
import sys
import json
import tempfile
from unittest.mock import MagicMock
import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_prompts_file(temp_dir):
    """Create a sample natural language prompts file."""
    prompts_path = os.path.join(temp_dir, "prompts.txt")
    content = """Create 4 versions of a serene mountain landscape at sunset

I need 6 variations of a futuristic city scene

Generate 2 versions of a cozy winter cabin"""

    with open(prompts_path, "w") as f:
        f.write(content)

    return prompts_path


@pytest.fixture
def sample_batch_yaml(temp_dir):
    """Create a sample batch.yaml file."""
    yaml_path = os.path.join(temp_dir, "batch.yaml")
    output_folder = os.path.join(temp_dir, "batch_output")
    content = f"""images:
  - prompt: "serene mountain landscape at sunset"
    variations: 4
  - prompt: "futuristic city scene"
    variations: 4
  - prompt: "cozy winter cabin"
    variations: 2
    aspect_ratio: "16:9"

global_style_references: []
output_folder: {output_folder}
"""
    with open(yaml_path, "w") as f:
        f.write(content)

    return yaml_path


@pytest.fixture
def sample_image_data():
    """Create sample PNG image data (minimal valid PNG)."""
    # Minimal valid PNG file (1x1 transparent pixel)
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
        0x42, 0x60, 0x82
    ])


@pytest.fixture
def mock_gemini_client(sample_image_data):
    """Mock the Gemini client for testing."""
    mock_client = MagicMock()

    # Mock parse response
    parse_response = MagicMock()
    parse_response.text = json.dumps({
        "images": [
            {"prompt": "serene mountain landscape at sunset", "variations": 4},
            {"prompt": "futuristic city scene", "variations": 6},
            {"prompt": "cozy winter cabin", "variations": 2}
        ],
        "global_style_references": []
    })

    # Mock image response
    image_response = MagicMock()
    image_part = MagicMock()
    image_part.inline_data = MagicMock()
    image_part.inline_data.data = sample_image_data
    image_response.parts = [image_part]

    mock_client.models.generate_content = MagicMock(side_effect=[
        parse_response,  # First call for parse
        image_response,  # Subsequent calls for image generation
    ])

    return mock_client


@pytest.fixture
def output_dir(temp_dir):
    """Create output directory path."""
    output = os.path.join(temp_dir, "output")
    os.makedirs(output, exist_ok=True)
    return output


@pytest.fixture
def monkeypatch_output_dir(monkeypatch, output_dir):
    """Monkeypatch the OUTPUT_DIR constant."""
    from imggen import cli
    monkeypatch.setattr(cli, "output_dir", output_dir)
    return output_dir


@pytest.fixture
def mock_google_provider(sample_image_data):
    """Mock Google provider for testing."""
    from unittest.mock import MagicMock
    from imggen.providers.google_provider import GoogleProvider

    provider = MagicMock(spec=GoogleProvider)
    provider.name = "google"
    provider.get_parse_model = MagicMock(return_value="gemini-2.0-flash")
    provider.get_generate_model = MagicMock(return_value="gemini-3-pro-image-preview")

    # Mock parse response
    provider.parse = MagicMock(return_value={
        "images": [
            {"prompt": "serene mountain landscape at sunset", "variations": 4},
            {"prompt": "futuristic city scene", "variations": 6},
            {"prompt": "cozy winter cabin", "variations": 2}
        ],
        "global_style_references": []
    })

    # Mock image generation response
    provider.generate_image = MagicMock(return_value={
        "status": "success",
        "filename": "test_001.png"
    })

    return provider


@pytest.fixture
def mock_openai_provider(sample_image_data):
    """Mock OpenAI provider for testing."""
    from unittest.mock import MagicMock
    from imggen.providers.openai_provider import OpenAIProvider

    provider = MagicMock(spec=OpenAIProvider)
    provider.name = "openai"
    provider.get_parse_model = MagicMock(return_value="gpt-4.5-mini")
    provider.get_generate_model = MagicMock(return_value="gpt-image-1.5")

    # Mock parse response
    provider.parse = MagicMock(return_value={
        "images": [
            {"prompt": "serene mountain landscape at sunset", "variations": 4},
            {"prompt": "futuristic city scene", "variations": 6},
            {"prompt": "cozy winter cabin", "variations": 2}
        ],
        "global_style_references": []
    })

    # Mock image generation response
    provider.generate_image = MagicMock(return_value={
        "status": "success",
        "filename": "test_001.png"
    })

    return provider


# Provider response fixtures
@pytest.fixture
def openai_mock_response():
    """Create a mock OpenAI image generation response."""
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(
            b64_json="base64encodeddata",
            revised_prompt="An intricately detailed landscape",
            quality="high",
            size="1024x1024",
        )
    ]
    mock_response.created = 1705080600
    return mock_response


@pytest.fixture
def google_mock_response():
    """Create a mock Google image generation response."""
    mock_response = MagicMock()
    mock_response.model_version = "gemini-3-pro-image-preview-001"
    mock_response.response_id = "abc123xyz789"
    mock_response.candidates = [MagicMock(finish_reason="STOP")]
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=125,
        candidates_token_count=1120,
    )

    mock_part = MagicMock()
    mock_part.inline_data = MagicMock()
    mock_part.inline_data.data = b"fake image data"
    mock_response.parts = [mock_part]

    return mock_response


@pytest.fixture
def google_response_factory():
    """Factory fixture for creating Google responses with custom metadata."""
    def _make_response(prompt_tokens=100, output_tokens=1000, finish_reason="STOP", include_image=True):
        mock_response = MagicMock()
        mock_response.model_version = "gemini-3-pro-image-preview-001"
        mock_response.response_id = "test-id"
        mock_response.candidates = [MagicMock(finish_reason=finish_reason)]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=prompt_tokens,
            candidates_token_count=output_tokens,
        )

        if include_image:
            mock_part = MagicMock()
            mock_part.inline_data = MagicMock()
            mock_part.inline_data.data = b"fake image data"
            mock_response.parts = [mock_part]
        else:
            mock_response.parts = []

        return mock_response
    return _make_response
