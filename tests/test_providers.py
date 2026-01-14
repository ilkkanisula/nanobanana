"""Tests for provider factory and inference."""
import pytest
from imggen.providers import get_provider, infer_provider_from_model


class TestProviderFactory:
    """Test provider factory function."""

    def test_get_google_provider(self):
        """Test creating Google provider."""
        provider = get_provider("google", "test-key")
        assert provider.name == "google"
        assert provider.get_generate_model() == "gemini-3-pro-image-preview"

    def test_get_openai_provider(self):
        """Test creating OpenAI provider."""
        provider = get_provider("openai", "test-key")
        assert provider.name == "openai"
        assert provider.get_generate_model() == "gpt-image-1.5"

    def test_unknown_provider_raises_error(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("unknown", "test-key")


class TestProviderInference:
    """Test provider inference from model names."""

    def test_infer_google_from_gemini_prefix(self):
        """Test inferring Google from gemini- prefix."""
        assert infer_provider_from_model("gemini-2.0-flash") == "google"
        assert infer_provider_from_model("gemini-3-pro-image-preview") == "google"

    def test_infer_google_from_google_prefix(self):
        """Test inferring Google from google- prefix."""
        assert infer_provider_from_model("google-something") == "google"

    def test_infer_openai_from_gpt_prefix(self):
        """Test inferring OpenAI from gpt- prefix."""
        assert infer_provider_from_model("gpt-4.5-mini") == "openai"
        assert infer_provider_from_model("gpt-image-1.5") == "openai"
        assert infer_provider_from_model("gpt-4") == "openai"

    def test_infer_openai_from_dalle_prefix(self):
        """Test inferring OpenAI from dall-e- prefix."""
        assert infer_provider_from_model("dall-e-3") == "openai"
        assert infer_provider_from_model("dall-e-2") == "openai"

    def test_unknown_model_defaults_to_openai(self):
        """Test that unknown model defaults to OpenAI."""
        assert infer_provider_from_model("unknown-model") == "openai"
        assert infer_provider_from_model("custom-image-gen") == "openai"


class TestProviderInterface:
    """Test that providers implement required interface."""

    def test_google_provider_has_generate_image_method(self):
        """Test Google provider has generate_image method."""
        provider = get_provider("google", "test-key")
        assert hasattr(provider, "generate_image")
        assert callable(provider.generate_image)

    def test_openai_provider_has_generate_image_method(self):
        """Test OpenAI provider has generate_image method."""
        provider = get_provider("openai", "test-key")
        assert hasattr(provider, "generate_image")
        assert callable(provider.generate_image)


class TestModelListing:
    """Test model listing functionality."""

    def test_get_available_models_returns_dict(self):
        """Test get_available_models returns a dictionary."""
        from imggen.providers import get_available_models

        models = get_available_models()
        assert isinstance(models, dict)

    def test_get_available_models_has_providers(self):
        """Test available models contains provider keys."""
        from imggen.providers import get_available_models

        models = get_available_models()
        assert "openai" in models
        assert "google" in models

    def test_get_available_models_openai_contains_gpt_image(self):
        """Test OpenAI models list contains gpt-image-1.5."""
        from imggen.providers import get_available_models

        models = get_available_models()
        assert "gpt-image-1.5" in models["openai"]

    def test_get_available_models_google_contains_gemini(self):
        """Test Google models list contains gemini-3-pro-image-preview."""
        from imggen.providers import get_available_models

        models = get_available_models()
        assert "gemini-3-pro-image-preview" in models["google"]

    def test_get_models_for_provider_openai(self):
        """Test getting models for OpenAI provider."""
        from imggen.providers import get_models_for_provider

        models = get_models_for_provider("openai")
        assert isinstance(models, list)
        assert "gpt-image-1.5" in models

    def test_get_models_for_provider_google(self):
        """Test getting models for Google provider."""
        from imggen.providers import get_models_for_provider

        models = get_models_for_provider("google")
        assert isinstance(models, list)
        assert "gemini-3-pro-image-preview" in models

    def test_get_models_for_provider_unknown(self):
        """Test getting models for unknown provider returns empty list."""
        from imggen.providers import get_models_for_provider

        models = get_models_for_provider("unknown")
        assert models == []
