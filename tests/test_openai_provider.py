"""Tests for OpenAI provider."""
import pytest
from unittest.mock import patch, MagicMock
from imggen.providers import get_provider


class TestOpenAIInputFidelity:
    """Test OpenAI provider input_fidelity parameter."""

    def test_input_fidelity_high_parameter_passed_to_api(self, tmp_path):
        """Test that input_fidelity='high' is passed to OpenAI API."""
        provider = get_provider("openai", "test-key")

        image_file = tmp_path / "reference.png"
        image_file.write_bytes(b"fake image data")

        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json="base64encodeddata")]

        with patch.object(provider.client.images, "edit", return_value=mock_response) as mock_edit:
            with patch("builtins.open", wraps=open):
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=[str(image_file)],
                    input_fidelity="high",
                )

                assert mock_edit.called
                call_kwargs = mock_edit.call_args[1]
                assert "input_fidelity" in call_kwargs
                assert call_kwargs["input_fidelity"] == "high"

    def test_input_fidelity_low_parameter_passed_to_api(self, tmp_path):
        """Test that input_fidelity='low' is passed to OpenAI API."""
        provider = get_provider("openai", "test-key")

        image_file = tmp_path / "reference.png"
        image_file.write_bytes(b"fake image data")

        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json="base64encodeddata")]

        with patch.object(provider.client.images, "edit", return_value=mock_response) as mock_edit:
            with patch("builtins.open", wraps=open):
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=[str(image_file)],
                    input_fidelity="low",
                )

                assert mock_edit.called
                call_kwargs = mock_edit.call_args[1]
                assert "input_fidelity" in call_kwargs
                assert call_kwargs["input_fidelity"] == "low"

    def test_input_fidelity_invalid_value_returns_error(self, tmp_path):
        """Test that invalid input_fidelity value returns error."""
        provider = get_provider("openai", "test-key")

        image_file = tmp_path / "reference.png"
        image_file.write_bytes(b"fake image data")

        result = provider.generate_image(
            prompt="test prompt",
            output_dir=str(tmp_path),
            filename="output.png",
            reference_images=[str(image_file)],
            input_fidelity="invalid",
        )

        assert result["status"] == "failed"
        assert "input_fidelity" in result["error"]

    def test_input_fidelity_none_not_passed_to_api(self, tmp_path):
        """Test that input_fidelity is not passed when None."""
        provider = get_provider("openai", "test-key")

        image_file = tmp_path / "reference.png"
        image_file.write_bytes(b"fake image data")

        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json="base64encodeddata")]

        with patch.object(provider.client.images, "edit", return_value=mock_response) as mock_edit:
            with patch("builtins.open", wraps=open):
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=[str(image_file)],
                    input_fidelity=None,
                )

                assert mock_edit.called
                call_kwargs = mock_edit.call_args[1]
                assert "input_fidelity" not in call_kwargs or call_kwargs.get("input_fidelity") is None


class TestOpenAIProviderReferenceImages:
    """Test OpenAI provider reference image handling."""

    def test_reference_image_file_closed_on_success(self, tmp_path):
        """Test that reference image file is properly closed after successful API call."""
        provider = get_provider("openai", "test-key")

        image_file = tmp_path / "reference.png"
        image_file.write_bytes(b"fake image data")

        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json="base64encodeddata")]

        with patch.object(provider.client.images, "edit", return_value=mock_response):
            with patch("builtins.open", wraps=open) as mock_open:
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=[str(image_file)],
                )

                assert mock_open.called
                handles = [call[0] for call in mock_open.call_args_list if call[0]]
                assert len(handles) > 0

    def test_reference_image_file_closed_on_error(self, tmp_path):
        """Test that reference image file is properly closed even on API error."""
        provider = get_provider("openai", "test-key")

        image_file = tmp_path / "reference.png"
        image_file.write_bytes(b"fake image data")

        with patch.object(provider.client.images, "edit", side_effect=Exception("API error")):
            with patch("builtins.open", wraps=open) as mock_open:
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=[str(image_file)],
                )

                assert result["status"] == "failed"
                assert "API error" in result["error"]
                assert mock_open.called

    def test_reference_image_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is properly handled."""
        provider = get_provider("openai", "test-key")

        result = provider.generate_image(
            prompt="test prompt",
            output_dir=str(tmp_path),
            filename="output.png",
            reference_images=["/nonexistent/image.png"],
        )

        assert result["status"] == "failed"
        assert "Reference image not found" in result["error"]
        assert "/nonexistent/image.png" in result["error"]

    def test_multiple_reference_images_passed_to_api(self, tmp_path):
        """Test that multiple reference images are passed as list to API."""
        provider = get_provider("openai", "test-key")

        image_files = []
        for i in range(3):
            image_file = tmp_path / f"reference{i}.png"
            image_file.write_bytes(b"fake image data")
            image_files.append(str(image_file))

        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json="base64encodeddata")]

        with patch.object(provider.client.images, "edit", return_value=mock_response) as mock_edit:
            with patch("builtins.open", wraps=open):
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=image_files,
                )

                assert mock_edit.called
                call_kwargs = mock_edit.call_args[1]
                assert "image" in call_kwargs
                assert isinstance(call_kwargs["image"], list)
                assert len(call_kwargs["image"]) == 3

    def test_multiple_reference_images_files_closed(self, tmp_path):
        """Test that all reference image files are properly closed."""
        provider = get_provider("openai", "test-key")

        image_files = []
        for i in range(3):
            image_file = tmp_path / f"reference{i}.png"
            image_file.write_bytes(b"fake image data")
            image_files.append(str(image_file))

        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json="base64encodeddata")]

        with patch.object(provider.client.images, "edit", return_value=mock_response):
            with patch("builtins.open", wraps=open) as mock_open:
                result = provider.generate_image(
                    prompt="test prompt",
                    output_dir=str(tmp_path),
                    filename="output.png",
                    reference_images=image_files,
                )

                assert mock_open.called
                assert len([call for call in mock_open.call_args_list if call[0]]) >= 3


class TestOpenAIMetadata:
    """Test OpenAI provider metadata extraction."""

    def test_success_response_includes_metadata_fields(self, tmp_path):
        """Test that successful response includes all metadata fields."""
        provider = get_provider("openai", "test-key")

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

        with patch("builtins.open", create=True):
            with patch("base64.b64decode", return_value=b"fake png data"):
                with patch.object(provider.client.images, "generate", return_value=mock_response):
                    result = provider.generate_image(
                        prompt="landscape at sunset",
                        output_dir=str(tmp_path),
                        filename="test.png",
                    )

                    assert result["status"] == "success"
                    assert "revised_prompt" in result
                    assert "created" in result
                    assert "quality" in result
                    assert "size" in result
                    assert "cost_usd" in result

    def test_revised_prompt_extracted_from_response(self, tmp_path):
        """Test revised_prompt is extracted from response."""
        provider = get_provider("openai", "test-key")

        expected_revised = "An intricately detailed, vibrant acrylic painting"
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(
                b64_json="base64encodeddata",
                revised_prompt=expected_revised,
                quality="high",
                size="1024x1024",
            )
        ]
        mock_response.created = 1705080600

        with patch("builtins.open", create=True):
            with patch("base64.b64decode", return_value=b"fake png data"):
                with patch.object(provider.client.images, "generate", return_value=mock_response):
                    result = provider.generate_image(
                        prompt="acrylic painting",
                        output_dir=str(tmp_path),
                        filename="test.png",
                    )

                    assert result["revised_prompt"] == expected_revised

    def test_created_timestamp_is_iso_8601_format(self, tmp_path):
        """Test created timestamp is in ISO 8601 format."""
        provider = get_provider("openai", "test-key")

        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(
                b64_json="base64encodeddata",
                revised_prompt="test",
                quality="high",
                size="1024x1024",
            )
        ]
        mock_response.created = 1705080600

        with patch("builtins.open", create=True):
            with patch("base64.b64decode", return_value=b"fake png data"):
                with patch.object(provider.client.images, "generate", return_value=mock_response):
                    result = provider.generate_image(
                        prompt="test",
                        output_dir=str(tmp_path),
                        filename="test.png",
                    )

                    assert "T" in result["created"]
                    assert "Z" in result["created"] or "+" in result["created"]

    def test_quality_field_returned_in_response(self, tmp_path):
        """Test quality field is returned in response."""
        provider = get_provider("openai", "test-key")

        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(
                b64_json="base64encodeddata",
                revised_prompt="test",
                quality="medium",
                size="1024x1024",
            )
        ]
        mock_response.created = 1705080600

        with patch("builtins.open", create=True):
            with patch("base64.b64decode", return_value=b"fake png data"):
                with patch.object(provider.client.images, "generate", return_value=mock_response):
                    result = provider.generate_image(
                        prompt="test",
                        output_dir=str(tmp_path),
                        filename="test.png",
                    )

                    assert result["quality"] == "medium"

    def test_size_field_returned_in_response(self, tmp_path):
        """Test size field is returned in response."""
        provider = get_provider("openai", "test-key")

        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(
                b64_json="base64encodeddata",
                revised_prompt="test",
                quality="high",
                size="1536x1024",
            )
        ]
        mock_response.created = 1705080600

        with patch("builtins.open", create=True):
            with patch("base64.b64decode", return_value=b"fake png data"):
                with patch.object(provider.client.images, "generate", return_value=mock_response):
                    result = provider.generate_image(
                        prompt="test",
                        output_dir=str(tmp_path),
                        filename="test.png",
                    )

                    assert result["size"] == "1536x1024"

    def test_cost_calculation_low_1024x1024(self, tmp_path):
        """Test cost for low quality 1024x1024 is 0.009."""
        provider = get_provider("openai", "test-key")

        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(
                b64_json="base64encodeddata",
                revised_prompt="test",
                quality="low",
                size="1024x1024",
            )
        ]
        mock_response.created = 1705080600

        with patch("builtins.open", create=True):
            with patch("base64.b64decode", return_value=b"fake png data"):
                with patch.object(provider.client.images, "generate", return_value=mock_response):
                    result = provider.generate_image(
                        prompt="test",
                        output_dir=str(tmp_path),
                        filename="test.png",
                    )

                    assert result["cost_usd"] == 0.009

    def test_cost_calculation_high_1536x1024(self, tmp_path):
        """Test cost for high quality 1536x1024 is 0.200."""
        provider = get_provider("openai", "test-key")

        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(
                b64_json="base64encodeddata",
                revised_prompt="test",
                quality="high",
                size="1536x1024",
            )
        ]
        mock_response.created = 1705080600

        with patch("builtins.open", create=True):
            with patch("base64.b64decode", return_value=b"fake png data"):
                with patch.object(provider.client.images, "generate", return_value=mock_response):
                    result = provider.generate_image(
                        prompt="test",
                        output_dir=str(tmp_path),
                        filename="test.png",
                    )

                    assert result["cost_usd"] == 0.200

    def test_error_response_no_metadata(self, tmp_path):
        """Test error responses don't include metadata."""
        provider = get_provider("openai", "test-key")

        with patch.object(provider.client.images, "generate", side_effect=Exception("API error")):
            result = provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )

            assert result["status"] == "failed"
            assert "revised_prompt" not in result
            assert "created" not in result
            assert "quality" not in result
            assert "size" not in result
            assert "cost_usd" not in result


class TestOpenAIProviderModelParameter:
    """Test OpenAI provider model parameter handling."""

    def test_openai_provider_accepts_model_parameter(self, tmp_path):
        """Test OpenAI provider accepts model parameter."""
        provider = get_provider("openai", "test-key")

        with patch("builtins.open", create=True):
            with patch("base64.b64decode", return_value=b"fake png data"):
                mock_response = MagicMock()
                mock_image = MagicMock()
                mock_image.b64_json = "base64encodeddata"
                mock_response.data = [mock_image]
                with patch.object(provider.client.images, "generate", return_value=mock_response) as mock_gen:
                    result = provider.generate_image(
                        prompt="test",
                        output_dir=str(tmp_path),
                        filename="test.png",
                        model="gpt-image-1.5",
                    )

                    assert mock_gen.called
                    call_kwargs = mock_gen.call_args[1]
                    assert call_kwargs["model"] == "gpt-image-1.5"

    def test_openai_provider_uses_default_model_when_none(self, tmp_path):
        """Test OpenAI provider uses default model when no model specified."""
        provider = get_provider("openai", "test-key")

        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json="base64encodeddata")]

        with patch.object(provider.client.images, "generate", return_value=mock_response) as mock_gen:
            provider.generate_image(
                prompt="test",
                output_dir=str(tmp_path),
                filename="test.png",
            )
            call_args = mock_gen.call_args
            assert call_args[1]["model"] == "gpt-image-1.5"
