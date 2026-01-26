"""Tests for image generation and file collision detection."""
import json
from unittest.mock import MagicMock


class TestOutputPathParsing:
    """Tests for parse_output_path() function."""

    def test_directory_with_trailing_slash(self):
        """Test directory path with trailing slash."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("./images/")
        assert output_dir == "./images"
        assert basename is None

    def test_directory_without_extension(self):
        """Test directory path without extension."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("./images")
        assert output_dir == "./images"
        assert basename is None

    def test_filename_png_in_current_dir(self):
        """Test .png filename in current directory."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("sunset.png")
        assert output_dir == "."
        assert basename == "sunset"

    def test_filename_jpg_in_current_dir(self):
        """Test .jpg filename in current directory."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("photo.jpg")
        assert output_dir == "."
        assert basename == "photo"

    def test_filename_jpeg_in_current_dir(self):
        """Test .jpeg filename in current directory."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("image.jpeg")
        assert output_dir == "."
        assert basename == "image"

    def test_filename_in_subdirectory(self):
        """Test filename with directory path."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("./images/sunset.png")
        assert output_dir == "./images"
        assert basename == "sunset"

    def test_filename_in_nested_directory(self):
        """Test filename in deeply nested directory."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("./project/output/renders/final.png")
        assert output_dir == "./project/output/renders"
        assert basename == "final"

    def test_absolute_path_directory(self):
        """Test absolute directory path."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("/tmp/images")
        assert output_dir == "/tmp/images"
        assert basename is None

    def test_absolute_path_filename(self):
        """Test absolute path with filename."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path("/tmp/images/output.png")
        assert output_dir == "/tmp/images"
        assert basename == "output"

    def test_dot_current_dir(self):
        """Test current directory with dot."""
        from imggen.generator import parse_output_path

        output_dir, basename = parse_output_path(".")
        assert output_dir == "."
        assert basename is None


class TestFilenameGeneration:
    """Tests for generate_filename() function."""

    def test_default_single_image(self):
        """Test default naming for single image."""
        from imggen.generator import generate_filename

        filename = generate_filename(None, 1, 1)
        assert filename == "imggen_001.png"

    def test_default_multiple_images(self):
        """Test default naming for multiple images."""
        from imggen.generator import generate_filename

        assert generate_filename(None, 1, 4) == "imggen_001.png"
        assert generate_filename(None, 2, 4) == "imggen_002.png"
        assert generate_filename(None, 3, 4) == "imggen_003.png"
        assert generate_filename(None, 4, 4) == "imggen_004.png"

    def test_custom_basename_single_image(self):
        """Test custom basename for single image."""
        from imggen.generator import generate_filename

        filename = generate_filename("sunset", 1, 1)
        assert filename == "sunset.png"

    def test_custom_basename_multiple_images(self):
        """Test custom basename for multiple images."""
        from imggen.generator import generate_filename

        assert generate_filename("sunset", 1, 4) == "sunset_1.png"
        assert generate_filename("sunset", 2, 4) == "sunset_2.png"
        assert generate_filename("sunset", 3, 4) == "sunset_3.png"
        assert generate_filename("sunset", 4, 4) == "sunset_4.png"

    def test_custom_basename_two_images(self):
        """Test custom basename for two images."""
        from imggen.generator import generate_filename

        assert generate_filename("photo", 1, 2) == "photo_1.png"
        assert generate_filename("photo", 2, 2) == "photo_2.png"


class TestFileCollisionDetection:
    """Tests for file collision detection."""

    def test_check_file_collisions_no_collision(self, tmp_path):
        """Test collision detection when no files exist."""
        from imggen.generator import check_file_collisions

        has_collision, collisions = check_file_collisions(str(tmp_path), 4)
        assert has_collision is False
        assert collisions == []

    def test_check_file_collisions_with_collision(self, tmp_path):
        """Test collision detection when files exist."""
        from imggen.generator import check_file_collisions

        # Create some files
        (tmp_path / "imggen_001.png").touch()
        (tmp_path / "imggen_002.png").touch()

        has_collision, collisions = check_file_collisions(str(tmp_path), 4)
        assert has_collision is True
        assert "imggen_001.png" in collisions
        assert "imggen_002.png" in collisions
        assert "imggen_003.png" not in collisions

    def test_check_file_collisions_partial_collision(self, tmp_path):
        """Test when only some files exist."""
        from imggen.generator import check_file_collisions

        (tmp_path / "imggen_003.png").touch()

        has_collision, collisions = check_file_collisions(str(tmp_path), 4)
        assert has_collision is True
        assert "imggen_003.png" in collisions
        assert "imggen_001.png" not in collisions

    def test_format_collision_error(self):
        """Test collision error message formatting."""
        from imggen.generator import format_collision_error

        collisions = ["imggen_001.png", "imggen_002.png"]
        message = format_collision_error(collisions, "./output")

        assert "Error: File collision detected" in message
        assert "imggen_001.png" in message
        assert "imggen_002.png" in message
        assert "No API calls were made" in message

    def test_check_file_collisions_custom_basename_single(self, tmp_path):
        """Test collision detection with custom basename for single image."""
        from imggen.generator import check_file_collisions

        (tmp_path / "sunset.png").touch()

        has_collision, collisions = check_file_collisions(str(tmp_path), 1, basename="sunset")
        assert has_collision is True
        assert "sunset.png" in collisions

    def test_check_file_collisions_custom_basename_no_collision(self, tmp_path):
        """Test no collision with custom basename."""
        from imggen.generator import check_file_collisions

        has_collision, collisions = check_file_collisions(str(tmp_path), 1, basename="sunset")
        assert has_collision is False
        assert collisions == []

    def test_check_file_collisions_custom_basename_multiple(self, tmp_path):
        """Test collision detection with custom basename for multiple images."""
        from imggen.generator import check_file_collisions

        (tmp_path / "sunset_2.png").touch()
        (tmp_path / "sunset_3.png").touch()

        has_collision, collisions = check_file_collisions(str(tmp_path), 4, basename="sunset")
        assert has_collision is True
        assert "sunset_2.png" in collisions
        assert "sunset_3.png" in collisions
        assert "sunset_1.png" not in collisions
        assert "sunset_4.png" not in collisions

    def test_check_file_collisions_default_when_basename_none(self, tmp_path):
        """Test that default naming is used when basename is None."""
        from imggen.generator import check_file_collisions

        (tmp_path / "imggen_001.png").touch()

        has_collision, collisions = check_file_collisions(str(tmp_path), 1, basename=None)
        assert has_collision is True
        assert "imggen_001.png" in collisions


class TestModelParameter:
    """Test model parameter passing through generation flow."""

    def test_generate_single_image_passes_model_to_provider(self, tmp_path):
        """Test that generate_single_image passes model to provider."""
        from imggen.generator import generate_single_image

        mock_provider = MagicMock()
        mock_provider.generate_image.return_value = {"status": "success", "filename": "test.png"}

        generate_single_image(
            mock_provider,
            "test prompt",
            str(tmp_path),
            "test.png",
            model="gpt-image-1.5",
        )

        # Verify model was passed to provider
        mock_provider.generate_image.assert_called_once()
        call_kwargs = mock_provider.generate_image.call_args[1]
        assert call_kwargs["model"] == "gpt-image-1.5"

    def test_generate_single_image_accepts_none_model(self, tmp_path):
        """Test that generate_single_image handles None model."""
        from imggen.generator import generate_single_image
        from unittest.mock import MagicMock

        mock_provider = MagicMock()
        mock_provider.generate_image.return_value = {"status": "success", "filename": "test.png"}

        generate_single_image(
            mock_provider,
            "test prompt",
            str(tmp_path),
            "test.png",
        )

        # Verify model was passed (as None)
        mock_provider.generate_image.assert_called_once()
        call_kwargs = mock_provider.generate_image.call_args[1]
        assert call_kwargs["model"] is None


class TestMetadataFileStorage:
    """Tests for metadata JSON file storage alongside generated images."""

    def test_metadata_json_created_alongside_image(self, tmp_path):
        """Test that JSON metadata file is created alongside generated image."""
        from imggen.generator import save_metadata_file

        image_filename = "imggen_001.png"
        save_metadata_file(
            output_dir=str(tmp_path),
            filename=image_filename,
            original_prompt="a serene landscape",
            provider="openai",
            model="gpt-image-1.5",
            revised_prompt="a serene landscape at sunset",
            created="2025-01-14T10:00:00+00:00",
            quality="high",
            size="1024x1024",
            cost_usd=0.133,
        )

        # Verify JSON file was created
        json_path = tmp_path / "imggen_001.json"
        assert json_path.exists()
        assert json_path.is_file()

    def test_metadata_contains_required_fields(self, tmp_path):
        """Test that JSON contains all required fields."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            original_prompt="test prompt",
            provider="openai",
            model="gpt-image-1.5",
            revised_prompt="revised test prompt",
            created="2025-01-14T10:00:00+00:00",
            quality="high",
            size="1024x1024",
            cost_usd=0.133,
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # Verify required fields are present
        assert "original_prompt" in metadata
        assert "provider" in metadata
        assert "model" in metadata
        assert "revised_prompt" in metadata
        assert "created" in metadata
        assert "quality" in metadata
        assert "size" in metadata
        assert "cost_usd" in metadata

    def test_metadata_field_values_correct(self, tmp_path):
        """Test that metadata contains correct values."""
        from imggen.generator import save_metadata_file

        test_data = {
            "original_prompt": "a serene landscape",
            "revised_prompt": "a serene landscape at sunset",
            "created": "2025-01-14T10:00:00+00:00",
            "quality": "high",
            "size": "1024x1024",
            "cost_usd": 0.133,
            "provider": "openai",
            "model": "gpt-image-1.5",
        }

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            **test_data,
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        assert metadata["original_prompt"] == test_data["original_prompt"]
        assert metadata["revised_prompt"] == test_data["revised_prompt"]
        assert metadata["created"] == test_data["created"]
        assert metadata["quality"] == test_data["quality"]
        assert metadata["size"] == test_data["size"]
        assert metadata["cost_usd"] == test_data["cost_usd"]
        assert metadata["provider"] == test_data["provider"]
        assert metadata["model"] == test_data["model"]

    def test_metadata_field_data_types(self, tmp_path):
        """Test that metadata fields have correct data types."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            original_prompt="a test prompt",
            provider="openai",
            model="gpt-image-1.5",
            revised_prompt="revised prompt",
            created="2025-01-14T10:00:00+00:00",
            quality="high",
            size="1024x1024",
            cost_usd=0.133,
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # Verify data types
        assert isinstance(metadata["original_prompt"], str)
        assert isinstance(metadata["provider"], str)
        assert isinstance(metadata["model"], str)
        assert isinstance(metadata["revised_prompt"], str)
        assert isinstance(metadata["created"], str)
        assert isinstance(metadata["quality"], str)
        assert isinstance(metadata["size"], str)
        assert isinstance(metadata["cost_usd"], (int, float))

    def test_metadata_multiple_variations(self, tmp_path):
        """Test that multiple images create corresponding metadata files."""
        from imggen.generator import save_metadata_file

        for i in range(1, 5):
            filename = f"imggen_{i:03d}.png"
            save_metadata_file(
                output_dir=str(tmp_path),
                filename=filename,
                original_prompt="test prompt",
                provider="openai",
                model="gpt-image-1.5",
                revised_prompt=f"revised prompt {i}",
                created="2025-01-14T10:00:00+00:00",
                quality="high",
                size="1024x1024",
                cost_usd=0.133,
            )

        # Verify all JSON files exist
        for i in range(1, 5):
            json_path = tmp_path / f"imggen_{i:03d}.json"
            assert json_path.exists()
            with open(json_path) as f:
                metadata = json.load(f)
                # Each should have unique revised_prompt
                assert metadata["revised_prompt"] == f"revised prompt {i}"

    def test_metadata_optional_fields_omitted_when_none(self, tmp_path):
        """Test that optional fields are omitted when None."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            original_prompt="test prompt",
            provider="openai",
            model="gpt-image-1.5",
            revised_prompt=None,
            created=None,
            quality=None,
            size=None,
            cost_usd=None,
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # Verify optional fields are not present
        assert "revised_prompt" not in metadata
        assert "created" not in metadata
        assert "quality" not in metadata
        assert "size" not in metadata
        assert "cost_usd" not in metadata

        # But required fields should be present
        assert "original_prompt" in metadata
        assert "provider" in metadata
        assert "model" in metadata

    def test_metadata_google_provider_fields(self, tmp_path):
        """Test that Google provider metadata is properly persisted."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            original_prompt="test prompt",
            provider="google",
            model="gemini-3-pro-image-preview",
            cost_usd=0.0052,
            model_version="gemini-3-pro-image-preview-001",
            response_id="abc123xyz789",
            finish_reason="STOP",
            prompt_tokens=125,
            output_tokens=1120,
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # Verify Google-specific fields
        assert metadata["model_version"] == "gemini-3-pro-image-preview-001"
        assert metadata["response_id"] == "abc123xyz789"
        assert metadata["finish_reason"] == "STOP"
        assert metadata["prompt_tokens"] == 125
        assert metadata["output_tokens"] == 1120

    def test_metadata_google_fields_are_strings_and_numbers(self, tmp_path):
        """Test that Google metadata fields have correct types."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            original_prompt="test prompt",
            provider="google",
            model="gemini-3-pro-image-preview",
            cost_usd=0.0052,
            model_version="gemini-3-pro-image-preview-001",
            response_id="abc123xyz789",
            finish_reason="STOP",
            prompt_tokens=125,
            output_tokens=1120,
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        assert isinstance(metadata["model_version"], str)
        assert isinstance(metadata["response_id"], str)
        assert isinstance(metadata["finish_reason"], str)
        assert isinstance(metadata["prompt_tokens"], int)
        assert isinstance(metadata["output_tokens"], int)

    def test_cost_calculation_persisted_openai(self, tmp_path):
        """Test that OpenAI cost calculation is correctly persisted."""
        from imggen.generator import save_metadata_file

        costs = [
            (0.009, "low", "1024x1024"),
            (0.034, "medium", "1024x1024"),
            (0.133, "high", "1024x1024"),
            (0.200, "high", "1024x1536"),
        ]

        for idx, (cost, quality, size) in enumerate(costs, 1):
            filename = f"test_{idx:03d}.png"
            save_metadata_file(
                output_dir=str(tmp_path),
                filename=filename,
                original_prompt="test",
                provider="openai",
                model="gpt-image-1.5",
                quality=quality,
                size=size,
                cost_usd=cost,
            )

            json_path = tmp_path / f"test_{idx:03d}.json"
            with open(json_path) as f:
                metadata = json.load(f)
                assert metadata["cost_usd"] == cost

    def test_cost_calculation_persisted_google(self, tmp_path):
        """Test that Google cost calculation is correctly persisted."""
        from imggen.generator import save_metadata_file

        costs = [
            (0.00025, 100, 1000),  # Low tokens: 100 prompt, 1000 output
            (0.00140, 500, 5000),  # Medium tokens
            (0.00280, 1000, 10000),  # High tokens
        ]

        for idx, (cost, prompt_tokens, output_tokens) in enumerate(costs, 1):
            filename = f"google_test_{idx:03d}.png"
            save_metadata_file(
                output_dir=str(tmp_path),
                filename=filename,
                original_prompt="test",
                provider="google",
                model="gemini-3-pro-image-preview",
                cost_usd=cost,
                prompt_tokens=prompt_tokens,
                output_tokens=output_tokens,
            )

            json_path = tmp_path / f"google_test_{idx:03d}.json"
            with open(json_path) as f:
                metadata = json.load(f)
                assert metadata["cost_usd"] == cost
                assert metadata["prompt_tokens"] == prompt_tokens
                assert metadata["output_tokens"] == output_tokens

    def test_metadata_json_filename_conversion(self, tmp_path):
        """Test that .png filename is correctly converted to .json."""
        from imggen.generator import save_metadata_file

        test_cases = [
            "imggen_001.png",
            "imggen_099.png",
            "image.png",
            "my_test_image.png",
        ]

        for filename in test_cases:
            save_metadata_file(
                output_dir=str(tmp_path),
                filename=filename,
                original_prompt="test",
                provider="openai",
                model="gpt-image-1.5",
            )

            expected_json = filename.replace(".png", ".json")
            json_path = tmp_path / expected_json
            assert json_path.exists()

    def test_metadata_json_valid_json_format(self, tmp_path):
        """Test that saved metadata is valid JSON."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="test.png",
            original_prompt="test prompt with special chars: 中文 🎨",
            provider="openai",
            model="gpt-image-1.5",
        )

        json_path = tmp_path / "test.json"

        # This will raise JSONDecodeError if invalid
        with open(json_path) as f:
            metadata = json.load(f)
            assert metadata is not None

    def test_metadata_json_formatting(self, tmp_path):
        """Test that JSON is formatted with indentation."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="test.png",
            original_prompt="test",
            provider="openai",
            model="gpt-image-1.5",
        )

        json_path = tmp_path / "test.json"

        # Read raw content and check for indentation
        with open(json_path) as f:
            content = f.read()

        # Should have newlines and indentation (indent=2 was used)
        assert "\n" in content
        assert "  " in content  # 2-space indentation

    def test_generate_single_image_saves_metadata_on_success(self, tmp_path):
        """Test that generate_single_image saves metadata for successful generation."""
        from imggen.generator import generate_single_image

        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.get_generate_model.return_value = "gpt-image-1.5"
        mock_provider.generate_image.return_value = {
            "status": "success",
            "filename": "imggen_001.png",
            "revised_prompt": "revised prompt",
            "created": "2025-01-14T10:00:00+00:00",
            "quality": "high",
            "size": "1024x1024",
            "cost_usd": 0.133,
        }

        result = generate_single_image(
            mock_provider,
            "test prompt",
            str(tmp_path),
            "imggen_001.png",
        )

        assert result["status"] == "success"

        # Metadata file should be created (but we won't call save_metadata_file in this test
        # as the full generator flow does it)

    def test_metadata_with_empty_optional_fields(self, tmp_path):
        """Test metadata creation with empty strings for optional fields."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="test.png",
            original_prompt="test",
            provider="openai",
            model="gpt-image-1.5",
            revised_prompt="",
            created="",
            quality="",
            size="",
            cost_usd=0.0,
        )

        json_path = tmp_path / "test.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # Empty strings should still be stored
        assert "revised_prompt" in metadata
        assert "created" in metadata
        assert "quality" in metadata
        assert "size" in metadata
        assert "cost_usd" in metadata
        assert metadata["cost_usd"] == 0.0

    def test_metadata_preserves_iso8601_timestamp(self, tmp_path):
        """Test that ISO 8601 timestamps are preserved exactly."""
        from imggen.generator import save_metadata_file

        iso_timestamp = "2025-01-14T10:30:45.123456+00:00"

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="test.png",
            original_prompt="test",
            provider="openai",
            model="gpt-image-1.5",
            created=iso_timestamp,
        )

        json_path = tmp_path / "test.json"
        with open(json_path) as f:
            metadata = json.load(f)

        assert metadata["created"] == iso_timestamp

    def test_metadata_provider_specific_kwargs(self, tmp_path):
        """Test that additional provider-specific kwargs are stored."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="test.png",
            original_prompt="test",
            provider="google",
            model="gemini-3-pro-image-preview",
            custom_field_1="custom_value",
            custom_field_2=42,
            custom_field_3=True,
        )

        json_path = tmp_path / "test.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # Custom kwargs should be in metadata
        assert metadata["custom_field_1"] == "custom_value"
        assert metadata["custom_field_2"] == 42
        assert metadata["custom_field_3"] is True

    def test_metadata_multiple_variations_all_files_valid(self, tmp_path):
        """Test that all metadata files from multiple variations are valid JSON."""
        from imggen.generator import save_metadata_file

        variations = 4
        for i in range(1, variations + 1):
            save_metadata_file(
                output_dir=str(tmp_path),
                filename=f"imggen_{i:03d}.png",
                original_prompt="test prompt",
                provider="openai",
                model="gpt-image-1.5",
                revised_prompt=f"revised {i}",
                cost_usd=0.133 * i,
            )

        # Verify all files can be read as valid JSON
        for i in range(1, variations + 1):
            json_path = tmp_path / f"imggen_{i:03d}.json"
            with open(json_path) as f:
                metadata = json.load(f)
                assert metadata["cost_usd"] == 0.133 * i

    def test_metadata_revised_prompt_omitted_when_identical_to_original(self, tmp_path):
        """Test that revised_prompt is omitted when identical to original_prompt."""
        from imggen.generator import save_metadata_file

        original = "a serene landscape at sunset"
        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            original_prompt=original,
            provider="openai",
            model="gpt-image-1.5",
            revised_prompt=original,  # Identical to original
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # revised_prompt should not be present since it's identical to original
        assert "revised_prompt" not in metadata
        assert metadata["original_prompt"] == original

    def test_metadata_null_provider_fields_filtered_out(self, tmp_path):
        """Test that null provider-specific fields are not included in JSON."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            original_prompt="test prompt",
            provider="openai",
            model="gpt-image-1.5",
            # Pass None values for Google provider fields
            model_version=None,
            response_id=None,
            finish_reason=None,
            prompt_tokens=None,
            output_tokens=None,
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # None values should not appear in the JSON
        assert "model_version" not in metadata
        assert "response_id" not in metadata
        assert "finish_reason" not in metadata
        assert "prompt_tokens" not in metadata
        assert "output_tokens" not in metadata

    def test_metadata_only_non_null_provider_fields_included(self, tmp_path):
        """Test that only non-null provider-specific fields are included."""
        from imggen.generator import save_metadata_file

        save_metadata_file(
            output_dir=str(tmp_path),
            filename="imggen_001.png",
            original_prompt="test prompt",
            provider="google",
            model="gemini-3-pro-image-preview",
            # Mix of None and non-None provider fields
            model_version="gemini-3-pro-image-preview-001",  # Include this
            response_id=None,  # Exclude this
            finish_reason="STOP",  # Include this
            prompt_tokens=None,  # Exclude this
            output_tokens=1120,  # Include this
        )

        json_path = tmp_path / "imggen_001.json"
        with open(json_path) as f:
            metadata = json.load(f)

        # Only non-null fields should be present
        assert metadata["model_version"] == "gemini-3-pro-image-preview-001"
        assert "response_id" not in metadata
        assert metadata["finish_reason"] == "STOP"
        assert "prompt_tokens" not in metadata
        assert metadata["output_tokens"] == 1120
