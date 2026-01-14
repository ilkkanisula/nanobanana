"""Tests for Google provider."""
import pytest
from unittest.mock import patch, MagicMock
from imggen.providers import get_provider


class TestGoogleReferenceImages:
    """Test Google provider reference image support."""

    def test_single_reference_image_included_in_contents(self, tmp_path):
        """Test that single reference image is included in contents array."""
        provider = get_provider("google", "test-key")

        image_file = tmp_path / "reference.png"
        image_file.write_bytes(b"fake image data")

        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response) as mock_gen:
            with patch("PIL.Image.open") as mock_pil_open:
                mock_pil_open.return_value = MagicMock()
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=[str(image_file)],
                )

                assert mock_gen.called
                call_kwargs = mock_gen.call_args[1]
                assert "contents" in call_kwargs
                assert len(call_kwargs["contents"]) >= 2

    def test_multiple_reference_images_included_in_contents(self, tmp_path):
        """Test that multiple reference images are included in contents array."""
        provider = get_provider("google", "test-key")

        image_files = []
        for i in range(3):
            image_file = tmp_path / f"reference{i}.png"
            image_file.write_bytes(b"fake image data")
            image_files.append(str(image_file))

        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response) as mock_gen:
            with patch("PIL.Image.open") as mock_pil_open:
                mock_pil_open.return_value = MagicMock()
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=image_files,
                )

                call_kwargs = mock_gen.call_args[1]
                assert "contents" in call_kwargs
                assert len(call_kwargs["contents"]) == 4

    def test_exceeding_14_reference_limit_returns_error(self, tmp_path):
        """Test that exceeding 14 reference image limit returns error."""
        provider = get_provider("google", "test-key")

        image_files = []
        for i in range(15):
            image_file = tmp_path / f"reference{i}.png"
            image_file.write_bytes(b"fake image data")
            image_files.append(str(image_file))

        result = provider.generate_image(
            prompt="test prompt",
            output_dir=str(tmp_path),
            filename="output.png",
            reference_images=image_files,
        )

        assert result["status"] == "failed"
        assert "reference" in result["error"].lower()
        assert "14" in result["error"]

    def test_reference_image_file_not_found_returns_error(self, tmp_path):
        """Test that missing reference image file returns error."""
        provider = get_provider("google", "test-key")

        result = provider.generate_image(
            prompt="test prompt",
            output_dir=str(tmp_path),
            filename="output.png",
            reference_images=["/nonexistent/image.png"],
        )

        assert result["status"] == "failed"
        assert "Reference image" in result["error"]

    def test_response_modalities_configured_with_references(self, tmp_path):
        """Test that response_modalities includes IMAGE when references provided."""
        provider = get_provider("google", "test-key")

        image_file = tmp_path / "reference.png"
        image_file.write_bytes(b"fake image data")

        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response) as mock_gen:
            with patch("PIL.Image.open") as mock_pil_open:
                mock_pil_open.return_value = MagicMock()
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=[str(image_file)],
                )

                call_kwargs = mock_gen.call_args[1]
                assert "config" in call_kwargs
                config = call_kwargs["config"]
                assert config.response_modalities == ["TEXT", "IMAGE"]


class TestGoogleMetadata:
    """Test Google provider metadata extraction."""

    def test_success_response_includes_metadata_fields(self, tmp_path, google_mock_response):
        """Test that successful response includes all metadata fields."""
        provider = get_provider("google", "test-key")

        with patch.object(provider.client.models, "generate_content", return_value=google_mock_response):
            result = provider.generate_image(
                prompt="test prompt",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["status"] == "success"
            assert result["model_version"] == "gemini-3-pro-image-preview-001"
            assert result["response_id"] == "abc123xyz789"
            assert result["finish_reason"] == "STOP"
            assert result["prompt_tokens"] == 125
            assert result["output_tokens"] == 1120
            assert "cost_usd" in result

    def test_model_version_extracted_from_response(self, tmp_path, google_response_factory):
        """Test model_version is extracted from response."""
        provider = get_provider("google", "test-key")
        mock_response = google_response_factory()

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["model_version"] == "gemini-3-pro-image-preview-001"

    def test_response_id_extracted_from_response(self, tmp_path):
        """Test response_id is extracted from response."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_response.model_version = "gemini-3-pro-image-preview-001"
        mock_response.response_id = "response-id-12345"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=1000,
        )

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["response_id"] == "response-id-12345"

    def test_finish_reason_extracted_from_response(self, tmp_path):
        """Test finish_reason is extracted from response."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_response.model_version = "gemini-3-pro-image-preview-001"
        mock_response.response_id = "test-id"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=1000,
        )

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["finish_reason"] == "STOP"

    def test_prompt_tokens_extracted_from_usage_metadata(self, tmp_path):
        """Test prompt_tokens are extracted from usageMetadata."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_response.model_version = "gemini-3-pro-image-preview-001"
        mock_response.response_id = "test-id"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=250,
            candidates_token_count=1000,
        )

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["prompt_tokens"] == 250

    def test_output_tokens_extracted_from_usage_metadata(self, tmp_path):
        """Test output_tokens are extracted from usageMetadata."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_response.model_version = "gemini-3-pro-image-preview-001"
        mock_response.response_id = "test-id"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=1500,
        )

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["output_tokens"] == 1500

    def test_cost_calculation_with_token_counts(self, tmp_path):
        """Test cost is calculated as (prompt_tokens * 2/1M) + (output_tokens * 120/1M)."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_response.model_version = "gemini-3-pro-image-preview-001"
        mock_response.response_id = "test-id"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=125,
            candidates_token_count=1120,
        )

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            expected_cost = (125 * 2.00 / 1_000_000) + (1120 * 120.00 / 1_000_000)
            assert result["cost_usd"] == pytest.approx(expected_cost, rel=1e-6)

    def test_cost_calculation_various_combinations(self, tmp_path, google_response_factory):
        """Test cost calculation with various token combinations."""
        provider = get_provider("google", "test-key")

        test_cases = [
            (100, 1000),
            (0, 1120),
            (1000, 2000),
        ]

        for i, (prompt_tokens, output_tokens) in enumerate(test_cases):
            expected_cost = (prompt_tokens * 2.00 / 1_000_000) + (output_tokens * 120.00 / 1_000_000)
            mock_response = google_response_factory(prompt_tokens=prompt_tokens, output_tokens=output_tokens)

            with patch.object(provider.client.models, "generate_content", return_value=mock_response):
                result = provider.generate_image(
                    prompt="test",
                    output_dir=str(tmp_path),
                    filename=f"test_{i}.png",
                )

                assert result["cost_usd"] == pytest.approx(expected_cost, rel=1e-6)

    def test_error_response_no_image_data(self, tmp_path):
        """Test error response when no image data in response."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_response.model_version = "gemini-3-pro-image-preview-001"
        mock_response.response_id = "test-id"
        mock_response.candidates = [MagicMock(finish_reason="IMAGE_SAFETY")]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=0,
        )
        mock_response.parts = []

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["status"] == "failed"
            assert "No image data" in result["error"]

    def test_finish_reason_various_values(self, tmp_path, google_response_factory):
        """Test finish_reason is captured with various values."""
        provider = get_provider("google", "test-key")

        finish_reasons = ["STOP", "IMAGE_SAFETY", "IMAGE_PROHIBITED_CONTENT"]

        for reason in finish_reasons:
            mock_response = google_response_factory(finish_reason=reason)

            with patch.object(provider.client.models, "generate_content", return_value=mock_response):
                result = provider.generate_image(
                    prompt="test",
                    output_dir=str(tmp_path),
                    filename=f"test_{reason}.png",
                )

                assert result["finish_reason"] == reason

    def test_missing_usage_metadata_defaults_to_zero(self, tmp_path):
        """Test that missing usage_metadata defaults to zero tokens."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_response.model_version = "gemini-3-pro-image-preview-001"
        mock_response.response_id = "test-id"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_response.usage_metadata = None

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["prompt_tokens"] == 0
            assert result["output_tokens"] == 0
            assert result["cost_usd"] == 0.0


class TestGoogleProviderModelParameter:
    """Test Google provider model parameter handling."""

    def test_google_provider_accepts_model_parameter(self, tmp_path):
        """Test Google provider accepts model parameter."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
                model="gemini-3-pro-image-preview",
            )
            assert result["status"] == "success"

    def test_google_provider_uses_default_model_when_none(self, tmp_path):
        """Test Google provider uses default model when no model specified."""
        provider = get_provider("google", "test-key")

        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake image data"
        mock_response.parts = [mock_part]

        with patch.object(provider.client.models, "generate_content", return_value=mock_response) as mock_gen:
            provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )
            call_args = mock_gen.call_args
            assert call_args[1]["model"] == "gemini-3-pro-image-preview"
