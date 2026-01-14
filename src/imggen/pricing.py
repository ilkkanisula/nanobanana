"""Pricing calculations for multi-provider image generation."""

from typing import Optional

# Google pricing (per image at 1024x1024 base)
GOOGLE_PRICING = {
    "1K": 0.134,
    "2K": 0.134,
    "4K": 0.24,
}

# OpenAI GPT Image 1.5 pricing (per image at 1024x1024)
OPENAI_PRICING = {
    "low": 0.009,
    "medium": 0.034,
    "high": 0.133,
}

# Defaults
DEFAULT_PROVIDER = "openai"
DEFAULT_RESOLUTION = "1K"
DEFAULT_QUALITY = "low"


def get_image_cost(provider: Optional[str] = None, resolution: Optional[str] = None, quality: Optional[str] = None) -> float:
    """Get cost per image for a given provider and settings.

    Args:
        provider: Provider name ("google" or "openai"), defaults to DEFAULT_PROVIDER
        resolution: Resolution string for Google ("1K", "2K", "4K")
        quality: Quality tier for OpenAI ("low", "medium", "high")

    Returns:
        Cost per image as float
    """
    provider = provider or DEFAULT_PROVIDER

    if provider == "google":
        resolution = resolution or DEFAULT_RESOLUTION
        return GOOGLE_PRICING.get(resolution, GOOGLE_PRICING[DEFAULT_RESOLUTION])
    elif provider == "openai":
        quality = quality or DEFAULT_QUALITY
        return OPENAI_PRICING.get(quality, OPENAI_PRICING[DEFAULT_QUALITY])
    else:
        return 0.0


def calculate_image_cost(provider: Optional[str] = None, quality: Optional[str] = None, resolution: Optional[str] = None) -> float:
    """Calculate cost per image for direct generation.

    Args:
        provider: Provider name ("google" or "openai"), defaults to DEFAULT_PROVIDER
        quality: Quality tier for OpenAI ("low", "medium", "high")
        resolution: Resolution string for Google ("1K", "2K", "4K")

    Returns:
        Cost per image as float
    """
    return get_image_cost(provider, resolution, quality)


def calculate_total_cost(images: list, default_provider: Optional[str] = None) -> float:
    """Calculate total cost for a list of image configs with multi-provider support.

    Args:
        images: List of image config dicts
        default_provider: Default provider if not specified per-image

    Returns:
        Total cost as float
    """
    from imggen.providers import infer_provider_from_model

    default_provider = default_provider or DEFAULT_PROVIDER
    total_cost = 0.0

    for img in images:
        # Determine provider for this image
        if "model" in img:
            provider = infer_provider_from_model(img["model"])
        else:
            provider = default_provider

        # Get cost parameters
        resolution = img.get("resolution")
        quality = img.get("quality")
        variations = img.get("variations", 4)

        cost_per_image = get_image_cost(provider, resolution, quality)
        total_cost += cost_per_image * variations

    return total_cost
