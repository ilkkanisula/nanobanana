"""Google/Gemini provider for image generation."""

import os
from google import genai
from google.genai import types
from PIL import Image

from imggen.providers import Provider


GENERATE_MODEL = "gemini-3-pro-image-preview"


def calculate_google_image_cost(
    prompt_tokens: int,
    output_tokens: int,
    batch_mode: bool = False
) -> float:
    """Calculate cost from token counts.

    Args:
        prompt_tokens: Number of input tokens
        output_tokens: Number of output tokens (image generation)
        batch_mode: Whether using batch API (50% discount)

    Returns:
        Cost in USD for this image generation
    """
    if batch_mode:
        input_rate = 1.00 / 1_000_000
        output_rate = 60.00 / 1_000_000
    else:
        input_rate = 2.00 / 1_000_000
        output_rate = 120.00 / 1_000_000

    return (prompt_tokens * input_rate) + (output_tokens * output_rate)


class GoogleProvider(Provider):
    """Google/Gemini image generation provider."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "google"
        self.client = genai.Client(api_key=api_key)

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
        """Generate a single image using Gemini and save to disk.

        Args:
            prompt: Image generation prompt
            output_dir: Directory to save image
            filename: Filename for the image (with .png extension)
            aspect_ratio: Optional aspect ratio (e.g., "16:9")
            resolution: Optional resolution (e.g., "2K")
            quality: Unused (Google uses resolution)
            reference_images: Optional list of reference image paths (up to 14)
            model: Optional model name (defaults to gemini-3-pro-image-preview)
            input_fidelity: Unused (provided for interface compatibility with OpenAI)

        Returns:
            Dict with status and optional error info
            - {"status": "success", "filename": str}
            - {"status": "failed", "error": str, "rate_limited": bool}
        """
        try:
            # Validate reference images count
            if reference_images and len(reference_images) > 14:
                return {
                    "status": "failed",
                    "error": f"Too many reference images: {len(reference_images)}. Max 14 allowed",
                }

            # Build request content with optional parameters
            request_content = prompt

            if aspect_ratio or resolution:
                config_parts = []
                if aspect_ratio:
                    config_parts.append(f"aspect_ratio: {aspect_ratio}")
                if resolution:
                    config_parts.append(f"quality: {resolution}")

                request_content = f"{prompt}\n\n[{', '.join(config_parts)}]"

            # Build contents array: [prompt_text, Image, Image, ...]
            if reference_images and len(reference_images) > 0:
                contents = [request_content]
                try:
                    for ref_path in reference_images:
                        img = Image.open(ref_path)
                        contents.append(img)
                except FileNotFoundError as e:
                    return {
                        "status": "failed",
                        "error": f"Reference image not found: {e.filename}",
                    }

                response = self.client.models.generate_content(
                    model=model or GENERATE_MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"]
                    ),
                )
            else:
                response = self.client.models.generate_content(
                    model=model or GENERATE_MODEL,
                    contents=request_content,
                )

            # Extract and save the image
            if response.parts:
                for part in response.parts:
                    if part.inline_data and part.inline_data.data:
                        image_data = part.inline_data.data

                        image_path = os.path.join(output_dir, filename)
                        with open(image_path, "wb") as f:
                            f.write(image_data)

                        # Extract metadata from response
                        model_version = getattr(response, 'model_version', model or GENERATE_MODEL)
                        response_id = getattr(response, 'response_id', '')
                        finish_reason = 'UNKNOWN'
                        prompt_tokens = 0
                        output_tokens = 0

                        if response.candidates:
                            finish_reason = response.candidates[0].finish_reason or 'UNKNOWN'

                        if response.usage_metadata:
                            prompt_tokens = response.usage_metadata.prompt_token_count or 0
                            output_tokens = response.usage_metadata.candidates_token_count or 0

                        # Calculate cost from token counts
                        cost = calculate_google_image_cost(prompt_tokens, output_tokens)

                        return {
                            "status": "success",
                            "filename": filename,
                            "model_version": model_version,
                            "response_id": response_id,
                            "finish_reason": finish_reason,
                            "prompt_tokens": prompt_tokens,
                            "output_tokens": output_tokens,
                            "cost_usd": cost,
                        }

            return {"status": "failed", "error": "No image data in response"}

        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                return {
                    "status": "failed",
                    "error": "Rate limit exceeded",
                    "rate_limited": True,
                }
            return {"status": "failed", "error": error_str}

    def get_generate_model(self) -> str:
        """Return default model name for generation."""
        return GENERATE_MODEL
