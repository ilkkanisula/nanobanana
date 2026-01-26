#!/usr/bin/env python3
"""imggen - Generate images using AI providers"""

import os
import sys
import argparse

from imggen.config import (
    get_api_key_for_provider,
    load_config,
    setup_interactive,
    DEFAULT_PROVIDER,
)
from imggen.version import get_current_version
from imggen.generator import generate_from_prompt
from imggen.providers import infer_provider_from_model


# Whitelists for validation
ASPECT_RATIO_WHITELIST = ["1:1", "16:9", "9:16", "4:3", "3:4"]
RESOLUTION_WHITELIST = ["1K", "2K", "4K"]
QUALITY_LEVELS = ["low", "medium", "high"]
INPUT_FIDELITY_LEVELS = ["high", "low"]


def load_prompt(prompt_text=None, prompt_file=None):
    """Load prompt from text or file.

    Args:
        prompt_text: Inline prompt text
        prompt_file: Path to file containing prompt

    Returns:
        The prompt text

    Raises:
        ValueError: If file not found or empty
    """
    if prompt_text:
        return prompt_text

    if prompt_file:
        if not os.path.exists(prompt_file):
            raise ValueError(f"Prompt file not found: {prompt_file}")
        with open(prompt_file, 'r') as f:
            content = f.read().strip()
        if not content:
            raise ValueError(f"Prompt file is empty: {prompt_file}")
        return content

    raise ValueError("Must provide either --prompt or --file")


def load_references(reference_paths=None, reference_file=None):
    """Load reference image paths from args or file.

    Args:
        reference_paths: List of reference image file paths
        reference_file: Path to file containing reference image paths (one per line)

    Returns:
        List of reference image paths (or empty list)

    Raises:
        ValueError: If file not found or paths don't exist
    """
    if reference_paths and reference_file:
        raise ValueError("Cannot specify both positional reference images and --references file")

    if reference_file:
        if not os.path.exists(reference_file):
            raise ValueError(f"References file not found: {reference_file}")
        with open(reference_file, 'r') as f:
            paths = [line.strip() for line in f if line.strip()]
        if not paths:
            raise ValueError(f"References file is empty: {reference_file}")
        return paths

    return reference_paths or []


def validate_arguments(args):
    """Validate CLI arguments.

    Raises:
        ValueError: If arguments are invalid
    """
    # Validate aspect ratio
    if args.aspect_ratio and args.aspect_ratio not in ASPECT_RATIO_WHITELIST:
        raise ValueError(
            f"Invalid aspect ratio: {args.aspect_ratio}\n"
            f"Valid options: {', '.join(ASPECT_RATIO_WHITELIST)}"
        )

    # Validate quality (OpenAI only)
    if args.quality and args.quality not in QUALITY_LEVELS:
        raise ValueError(
            f"Invalid quality level: {args.quality}\n"
            f"Valid options: {', '.join(QUALITY_LEVELS)}"
        )

    # Validate resolution (Google only)
    if args.resolution and args.resolution not in RESOLUTION_WHITELIST:
        raise ValueError(
            f"Invalid resolution: {args.resolution}\n"
            f"Valid options: {', '.join(RESOLUTION_WHITELIST)}"
        )

    # Validate variations
    if args.variations < 1 or args.variations > 4:
        raise ValueError(f"Variations must be between 1 and 4, got {args.variations}")

    # Validate that at least one prompt source is specified
    if not args.prompt and not args.file:
        raise ValueError("Must provide either --prompt or --file")

    # Validate that only one prompt source is specified
    if args.prompt and args.file:
        raise ValueError("Cannot specify both --prompt and --file")

    # Validate that reference images don't specify both positional and file
    if args.reference_images and args.references:
        raise ValueError(
            "Cannot specify both positional reference images and --references file"
        )

    # Validate input_fidelity (OpenAI only)
    if hasattr(args, 'input_fidelity') and args.input_fidelity and args.input_fidelity not in INPUT_FIDELITY_LEVELS:
        raise ValueError(
            f"Invalid input_fidelity: {args.input_fidelity}\n"
            f"Valid options: {', '.join(INPUT_FIDELITY_LEVELS)}"
        )


def main():
    """Main entry point for imggen CLI."""
    # Handle commands before argparse
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            if setup_interactive():
                sys.exit(0)
            else:
                sys.exit(1)

        if sys.argv[1] == "update":
            from imggen.update import update_imggen
            update_imggen()
            return

        if sys.argv[1] in ["--version", "-v", "version"]:
            print(f"imggen {get_current_version()}")
            sys.exit(0)

        if sys.argv[1] == "check-update":
            from imggen.version import check_for_updates
            has_update, latest, message = check_for_updates(verbose=True)
            if has_update:
                print(message)
            sys.exit(0)

        if sys.argv[1] == "list-models":
            from imggen.providers import get_available_models
            models = get_available_models()
            print("Available image generation models:")
            print()
            for provider, model_list in models.items():
                print(f"{provider.title()}:")
                for model in model_list:
                    print(f"  - {model}")
            print()
            print("Use --model <model_name> to select a specific model")
            sys.exit(0)

    # Check for help early
    if len(sys.argv) <= 1 or sys.argv[1] in ["--help", "-h", "help"]:
        print("usage: imggen (-p PROMPT | -f FILE) [reference_images] [options]")
        print()
        print("Generate images using AI providers (OpenAI, Google)")
        print()
        print("Prompt source (required, choose one):")
        print("  -p, --prompt PROMPT   Inline prompt text")
        print("  -f, --file FILE       Path to file containing prompt")
        print()
        print("Reference images (optional):")
        print("  reference_images      One or more reference image file paths")
        print("  -r, --references FILE Path to file containing reference image paths (one per line)")
        print()
        print("Optional arguments:")
        print("  --output PATH         Output dir or filename (default: current dir)")
        print("  --variations N        Number of variations (1-4, default: 1)")
        print("  --model MODEL         Model name: gpt-image-1.5 or gemini-3-pro-image-preview")
        print("  --quality QUALITY     OpenAI quality: low, medium, high (default: low)")
        print("  --resolution RES      Google resolution: 1K, 2K, 4K (default: 1K)")
        print("  --aspect-ratio RATIO  Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4 (default: 1:1)")
        print("  --input-fidelity IF   OpenAI input fidelity: high, low (for reference images)")
        print("  --dry-run             Show cost estimate without generating")
        print("  -h, --help            Show this help message")
        print()
        print("Commands:")
        print("  imggen setup          Configure API keys")
        print("  imggen list-models    List available models")
        print("  imggen update         Update to latest version")
        print("  imggen check-update   Check for available updates")
        print("  imggen --version      Show version")
        print()
        print("Examples:")
        print("  imggen -p \"a serene landscape\"")
        print("  imggen -p \"sunset\" --output landscape.png")
        print("  imggen -p \"art\" --output art.png -n 4")
        print("  imggen -f prompt.txt --variations 4 --output ./images/")
        print("  imggen -p \"test\" ref1.jpg ref2.jpg --output ./images/")
        sys.exit(0 if len(sys.argv) > 1 else 1)

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generate images using AI providers",
        add_help=False  # Disable default help to use our custom one
    )

    # Prompt source (mutually exclusive)
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument("-p", "--prompt", help="Inline prompt text")
    prompt_group.add_argument("-f", "--file", help="Path to file containing prompt")

    # Reference images
    parser.add_argument(
        "reference_images",
        nargs="*",
        help="Reference image file paths",
        default=[]
    )
    parser.add_argument(
        "-r", "--references",
        help="Path to file containing reference image paths (one per line)"
    )

    # Generation options
    parser.add_argument(
        "--output", "--out-dir",
        default=".",
        help="Output directory or filename (default: current directory)"
    )
    parser.add_argument(
        "--variations", "-n",
        type=int,
        default=1,
        help="Number of variations (1-4, default: 1)"
    )
    parser.add_argument(
        "--model", "-m",
        help="Model name (auto-infers provider, default: gpt-image-1.5)"
    )
    parser.add_argument(
        "--quality", "-q",
        help="OpenAI quality: low, medium, high"
    )
    parser.add_argument(
        "--resolution",
        help="Google resolution: 1K, 2K, 4K"
    )
    parser.add_argument(
        "--aspect-ratio", "-a",
        help="Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4"
    )
    parser.add_argument(
        "--input-fidelity",
        help="OpenAI input fidelity: high (preserve facial details), low (allow reinterpretation)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show cost estimate without generating"
    )

    args = parser.parse_args()

    # Validate arguments
    try:
        validate_arguments(args)
        prompt = load_prompt(args.prompt, args.file)
        references = load_references(args.reference_images, args.references)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Determine provider
    provider_name = None
    if args.model:
        provider_name = infer_provider_from_model(args.model)
    else:
        config = load_config()
        provider_name = config.get("default_provider", DEFAULT_PROVIDER)

    # Get API key
    try:
        api_key = get_api_key_for_provider(provider_name)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    from imggen.generator import parse_output_path
    output_dir, _ = parse_output_path(args.output)
    os.makedirs(output_dir, exist_ok=True)

    # Generate images
    try:
        generate_from_prompt(
            prompt=prompt,
            reference_images=references,
            output_dir=args.output,
            variations=args.variations,
            provider_name=provider_name,
            api_key=api_key,
            aspect_ratio=args.aspect_ratio,
            quality=args.quality,
            resolution=args.resolution,
            model=args.model,
            input_fidelity=getattr(args, 'input_fidelity', None),
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
