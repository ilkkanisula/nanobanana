"""OpenAI provider for image generation."""

import base64
import datetime
import os
import time
from openai import OpenAI, APIError, RateLimitError

from imggen.providers import Provider


GENERATE_MODEL = "gpt-image-1.5"


def calculate_openai_image_cost(quality: str, size: str) -> float:
    """Calculate cost from image quality and size.

    Args:
        quality: Image quality (low, medium, high)
        size: Image size string (1024x1024, 1024x1536, 1536x1024)

    Returns:
        Cost in USD for this image generation
    """
    pricing = {
        ("low", "1024x1024"): 0.009,
        ("medium", "1024x1024"): 0.034,
        ("high", "1024x1024"): 0.133,
        ("low", "1024x1536"): 0.013,
        ("low", "1536x1024"): 0.013,
        ("medium", "1024x1536"): 0.050,
        ("medium", "1536x1024"): 0.050,
        ("high", "1024x1536"): 0.200,
        ("high", "1536x1024"): 0.200,
    }
    return pricing.get((quality, size), 0.0)


class OpenAIProvider(Provider):
    """OpenAI image generation provider."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "openai"
        self.client = OpenAI(api_key=api_key)

    def generate_image(
        self,
        prompt: str,
        output_dir: str,
        filename: str,
        aspect_ratio: str = None,
        resolution: str = None,
        quality: str = None,
        reference_images: list = None,
        model: str = None,
        input_fidelity: str = None,
    ) -> dict:
        """Generate a single image using OpenAI and save to disk.

        Args:
            prompt: Image generation prompt
            output_dir: Directory to save image
            filename: Filename for the image (with .png extension)
            aspect_ratio: Optional aspect ratio (e.g., "16:9")
            resolution: Unused (OpenAI uses quality)
            quality: Optional quality tier (low/medium/high), defaults to "low"
            reference_images: Optional list of reference image paths (multiple images supported)
            model: Optional model name (defaults to gpt-image-1.5)
            input_fidelity: Optional input fidelity for reference images ("high"/"low")

        Returns:
            Dict with status and optional error info
            - {"status": "success", "filename": str}
            - {"status": "failed", "error": str, "rate_limited": bool}
        """
        quality = quality or "low"

        # Validate input_fidelity if provided
        if input_fidelity is not None and input_fidelity not in ["high", "low"]:
            return {
                "status": "failed",
                "error": f"Invalid input_fidelity: {input_fidelity}. Valid values: high, low",
            }

        # Build the prompt with optional aspect ratio
        full_prompt = prompt
        if aspect_ratio:
            full_prompt = f"{prompt}\n\n[aspect_ratio: {aspect_ratio}]"

        # Map quality to OpenAI API parameter
        # OpenAI API accepts: low, medium, high, auto
        quality_map = {"low": "low", "medium": "medium", "high": "high"}
        openai_quality = quality_map.get(quality, "low")

        # Map aspect ratio to OpenAI's supported sizes
        size_map = {
            "1:1": "1024x1024",
            "16:9": "1792x1024",
            "9:16": "1024x1792",
            "4:3": "1360x1024",
            "3:4": "1024x1360",
        }
        image_size = size_map.get(aspect_ratio, "1024x1024")

        # Retry logic for transient 403 errors
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                # Build base API request parameters
                base_params = {
                    "model": model or GENERATE_MODEL,
                    "prompt": full_prompt,
                    "size": image_size,
                    "quality": openai_quality,
                    "n": 1,
                }

                # Use image editing endpoint if reference images provided, otherwise generate
                if reference_images and len(reference_images) > 0:
                    # Image-to-image: Use images.edit() with reference images
                    image_files = []
                    try:
                        # Open all reference images as file objects
                        try:
                            for ref_path in reference_images:
                                image_files.append(open(ref_path, "rb"))

                            edit_params = {
                                **base_params,
                                "image": image_files,
                            }
                            # Add input_fidelity if provided
                            if input_fidelity is not None:
                                edit_params["input_fidelity"] = input_fidelity
                            response = self.client.images.edit(**edit_params)
                        finally:
                            # Close all opened files
                            for f in image_files:
                                f.close()
                    except FileNotFoundError as e:
                        return {
                            "status": "failed",
                            "error": f"Reference image not found: {e.filename}",
                        }
                else:
                    # Text-to-image: Use standard generation
                    response = self.client.images.generate(**base_params)

                # Extract base64 image data
                if response.data and len(response.data) > 0:
                    image_data = base64.b64decode(response.data[0].b64_json)

                    # Save to disk
                    image_path = os.path.join(output_dir, filename)
                    with open(image_path, "wb") as f:
                        f.write(image_data)

                    # Extract metadata from response
                    # Note: images.edit() returns null for revised_prompt; use fallback
                    revised_prompt = getattr(response.data[0], 'revised_prompt', None) or full_prompt
                    quality_value = getattr(response.data[0], 'quality', None) or openai_quality
                    size_value = getattr(response.data[0], 'size', None) or image_size
                    created_iso = datetime.datetime.fromtimestamp(
                        response.created, tz=datetime.timezone.utc
                    ).isoformat()

                    # Calculate cost from quality and size
                    cost = calculate_openai_image_cost(quality_value, size_value)

                    return {
                        "status": "success",
                        "filename": filename,
                        "revised_prompt": revised_prompt,
                        "created": created_iso,
                        "quality": quality_value,
                        "size": size_value,
                        "cost_usd": cost,
                    }

                return {"status": "failed", "error": "No image data in response"}

            except RateLimitError:
                return {
                    "status": "failed",
                    "error": "Rate limit exceeded",
                    "rate_limited": True,
                }
            except APIError as e:
                error_str = str(e)
                # Retry on 403 errors (transient access issues)
                if "Error code: 403" in error_str or "status_code=403" in error_str:
                    if attempt < max_retries:
                        print(f"    (retry {attempt}/{max_retries - 1}, waiting {retry_delay}s...)", end=" ")
                        time.sleep(retry_delay)
                        continue
                return {"status": "failed", "error": error_str}
            except Exception as e:
                error_str = str(e)
                return {"status": "failed", "error": error_str}

        return {"status": "failed", "error": "Max retries exceeded"}

    def get_generate_model(self) -> str:
        """Return default model name for generation."""
        return GENERATE_MODEL
