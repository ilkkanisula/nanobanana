"""Image generation functionality for imggen."""

import json
import os
import sys
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from imggen.pricing import calculate_image_cost
from imggen.providers import get_provider, infer_provider_from_model
from imggen.config import get_api_key_for_provider


def save_metadata_file(
    output_dir: str,
    filename: str,
    original_prompt: str,
    provider: str,
    model: str,
    revised_prompt: Optional[str] = None,
    created: Optional[str] = None,
    quality: Optional[str] = None,
    size: Optional[str] = None,
    cost_usd: Optional[float] = None,
    **kwargs,
) -> None:
    """Save metadata JSON file alongside image.

    Args:
        output_dir: Directory where image is saved
        filename: Image filename (with .png extension)
        original_prompt: Original prompt text
        provider: Provider name (openai or google)
        model: Model name used
        revised_prompt: Optional revised prompt (OpenAI)
        created: Optional ISO 8601 timestamp (OpenAI)
        quality: Optional quality tier (OpenAI)
        size: Optional image dimensions (OpenAI)
        cost_usd: Optional cost in USD
        **kwargs: Additional provider-specific fields
    """
    # Remove .png extension and add .json
    base_name = filename.rsplit(".", 1)[0]
    json_filename = f"{base_name}.json"
    json_path = os.path.join(output_dir, json_filename)

    # Build metadata dict
    metadata = {
        "original_prompt": original_prompt,
        "provider": provider,
        "model": model,
    }

    # Add optional fields in consistent order (skip if None or if revised_prompt equals original_prompt)
    if revised_prompt is not None and revised_prompt != original_prompt:
        metadata["revised_prompt"] = revised_prompt
    if created is not None:
        metadata["created"] = created
    if quality is not None:
        metadata["quality"] = quality
    if size is not None:
        metadata["size"] = size
    if cost_usd is not None:
        metadata["cost_usd"] = cost_usd

    # Add provider-specific fields (only if not None)
    for key, value in kwargs.items():
        if value is not None:
            metadata[key] = value

    # Write JSON file
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)


def check_file_collisions(output_dir: str, variations: int) -> tuple[bool, list[str]]:
    """Check if files imggen_001.png through imggen_{variations}.png exist.

    Args:
        output_dir: Directory to check
        variations: Number of expected images

    Returns:
        (has_collision, list_of_existing_files)
    """
    collisions = []
    for i in range(1, variations + 1):
        filename = f"imggen_{i:03d}.png"
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            collisions.append(filename)
    return len(collisions) > 0, collisions


def format_collision_error(collisions: list[str], output_dir: str) -> str:
    """Format collision error message.

    Args:
        collisions: List of existing filenames
        output_dir: Output directory path

    Returns:
        Formatted error message
    """
    lines = ["Error: File collision detected", ""]
    lines.append(f"The following files already exist in {output_dir}:")
    for filename in collisions:
        lines.append(f"  - {filename}")
    lines.append("")
    lines.append("Please:")
    lines.append("  1. Delete or rename these files, OR")
    lines.append("  2. Use a different --output directory")
    lines.append("")
    lines.append("No API calls were made (no charges incurred).")
    return "\n".join(lines)


def generate_single_image(
    provider,
    prompt: str,
    output_dir: str,
    filename: str,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    quality: Optional[str] = None,
    reference_images: Optional[list[str]] = None,
    model: Optional[str] = None,
    input_fidelity: Optional[str] = None,
) -> dict:
    """Generate a single image and save it.

    Args:
        provider: Provider instance
        prompt: Image generation prompt
        output_dir: Output directory
        filename: Output filename (with .png extension)
        aspect_ratio: Optional aspect ratio (e.g., "16:9")
        resolution: Optional resolution for Google (e.g., "2K")
        quality: Optional quality for OpenAI (e.g., "medium")
        reference_images: Optional list of reference image paths
        model: Optional model name
        input_fidelity: Optional OpenAI input fidelity ("high"/"low")

    Returns:
        Dict with status and optional error
        - {"status": "success", "filename": str}
        - {"status": "failed", "error": str, "rate_limited": bool}
    """
    try:
        result = provider.generate_image(
            prompt,
            output_dir,
            filename,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            reference_images=reference_images,
            model=model,
            input_fidelity=input_fidelity,
        )
        return result
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def generate_from_prompt(
    prompt: str,
    reference_images: list[str],
    output_dir: str,
    variations: int,
    provider_name: str,
    api_key: str,
    aspect_ratio: Optional[str] = None,
    quality: Optional[str] = None,
    resolution: Optional[str] = None,
    model: Optional[str] = None,
    input_fidelity: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Generate images from prompt and save to disk.

    Args:
        prompt: Image generation prompt
        reference_images: List of reference image paths
        output_dir: Output directory
        variations: Number of variations to generate (1-4)
        provider_name: Provider name ("openai" or "google")
        api_key: API key for provider
        aspect_ratio: Optional aspect ratio
        quality: Optional quality (OpenAI)
        resolution: Optional resolution (Google)
        model: Optional model override
        input_fidelity: Optional OpenAI input fidelity ("high"/"low")
        dry_run: If True, show cost estimate and exit

    Raises:
        ValueError: If file collisions detected or other errors
    """
    # Normalize output directory path
    output_dir = output_dir.rstrip(os.sep)

    # Check file collisions BEFORE any API calls
    has_collision, collisions = check_file_collisions(output_dir, variations)
    if has_collision:
        raise ValueError(format_collision_error(collisions, output_dir))

    # Determine provider
    if model:
        provider_name = infer_provider_from_model(model)
        api_key = get_api_key_for_provider(provider_name)

    provider = get_provider(provider_name, api_key)

    # Calculate cost estimate
    cost_per_image = calculate_image_cost(provider_name, quality, resolution)
    estimated_cost = cost_per_image * variations

    # Display pre-generation info
    print(f"Generating {variations} image{'s' if variations > 1 else ''} with {provider_name.title()} ({provider.get_generate_model()})")
    print()
    print("Configuration:")
    print(f"  Prompt: \"{prompt}\"")
    if quality:
        print(f"  Quality: {quality}")
    if resolution:
        print(f"  Resolution: {resolution}")
    if aspect_ratio:
        print(f"  Aspect ratio: {aspect_ratio}")
    if input_fidelity:
        print(f"  Input fidelity: {input_fidelity}")
    if reference_images:
        print(f"  Reference images: {', '.join(reference_images)}")
    print(f"  Variations: {variations}")
    print(f"  Output: {output_dir}/imggen_001.png ... {output_dir}/imggen_{variations:03d}.png")
    print()
    print(f"Estimated cost: ${estimated_cost:.2f}")

    # If dry run, exit here
    if dry_run:
        print()
        print("Run without --dry-run to generate images.")
        return

    # Generate images in parallel
    print()
    successful = 0
    failed = 0
    errors = []
    rate_limited = False

    # Use up to 4 parallel workers
    max_workers = min(4, variations)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all generation tasks
        futures = {}
        for i in range(1, variations + 1):
            filename = f"imggen_{i:03d}.png"
            future = executor.submit(
                generate_single_image,
                provider,
                prompt,
                output_dir,
                filename,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                quality=quality,
                reference_images=reference_images,
                model=model,
                input_fidelity=input_fidelity,
            )
            futures[future] = (i, filename)

        # Collect results and display them in order
        results = {}
        for future in as_completed(futures):
            i, filename = futures[future]
            result = future.result()
            results[i] = (filename, result)

            if result.get("rate_limited"):
                rate_limited = True
                # Cancel remaining tasks
                executor.shutdown(wait=False)
                break

        # Display results in sequential order
        for i in range(1, variations + 1):
            if i in results:
                filename, result = results[i]
                if result["status"] == "success":
                    print(f"  [{i}/{variations}] Generating {filename}... ✓")
                    successful += 1

                    # Save metadata file for successful generation
                    save_metadata_file(
                        output_dir=output_dir,
                        filename=filename,
                        original_prompt=prompt,
                        provider=provider.name,
                        model=provider.get_generate_model(),
                        revised_prompt=result.get("revised_prompt"),
                        created=result.get("created"),
                        quality=result.get("quality"),
                        size=result.get("size"),
                        cost_usd=result.get("cost_usd"),
                        # Pass any additional provider-specific fields
                        model_version=result.get("model_version"),
                        response_id=result.get("response_id"),
                        finish_reason=result.get("finish_reason"),
                        prompt_tokens=result.get("prompt_tokens"),
                        output_tokens=result.get("output_tokens"),
                    )
                else:
                    print(f"  [{i}/{variations}] Generating {filename}... ✗")
                    failed += 1
                    errors.append(f"  - {filename}: {result.get('error', 'Unknown error')}")

    # Calculate actual cost based on successful images
    actual_cost = cost_per_image * successful

    # Summary
    print()
    print("=" * 50)
    print("Generation complete!")
    print(f"  Successful: {successful}/{successful + failed}")
    if failed > 0:
        print(f"  Failed: {failed}/{successful + failed}")
        print()
        print("Errors:")
        for error in errors:
            print(error)
    print()
    print(f"Actual cost: ${actual_cost:.2f}")
    print(f"Output directory: {output_dir}")
