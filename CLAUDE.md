# imggen Tool

This repo is imggen - a tool to generate images from natural language prompts using AI providers.

## Supported Providers

- **OpenAI** - GPT Image 1.5 (default) - Model: `gpt-image-1.5`
- **Google** - Gemini 3 Pro Image - Model: `gemini-3-pro-image-preview`

## Implementation Principles

- Keep It Simple Stupid (KISS)
- Omit needless words and code comments
- Do not over-engineer
- Don't do defensive programming unless really needed
- Separate concerns into clearly defined functionalities
- Keep implementation focused on main functionalities
- Maintain software version in the repo for `imggen update`
- Always use TDD for changes
- When implementing changes always find first existing related tests

## Architecture

### Core Patterns

- **Factory Pattern**: Providers abstracted behind factory (`get_provider()`, `infer_provider_from_model()`) with unified interface. Enables adding new providers without modifying CLI or generation logic.
- **Separation of Concerns**: CLI (cli.py), Config (config.py), Generation (generator.py), Providers (providers/), Pricing (pricing.py) are isolated modules with clear dependencies
- **Pre-flight Validation**: File collision detection before API calls prevents wasted cost
- **Fail Fast**: Configuration auto-prompts for missing keys; invalid arguments rejected early

### Feature Organization

**Provider Features** (`src/imggen/providers/`)
- Each provider implements: `generate_image()`, `get_generate_model()`
- Example: Add new provider by creating new class inheriting from `Provider` abstract base, implement interface, add to factory

**CLI & Config** (`src/imggen/cli.py`, `src/imggen/config.py`)
- CLI parses arguments and delegates to generator
- Config stores multi-key API support with auto-migration
- New CLI options map directly to provider parameters

**Quality & Cost** (`src/imggen/pricing.py`)
- Provider-specific pricing data and cost calculation functions
- Add new provider: include pricing data in this module

**Feature Documentation** (`specs/features.md`)
- User-facing feature descriptions and CLI examples
- Update this file whenever implementing new features or changing user-facing behavior

## Documentation Standards

- **docs/...**: Research results and technical investigations. Omit needless words, focus only on topics related to imggen
- **specs/...**: Plans for implemented features. Omit needless words, focus only on topics related to imggen

## Testing

See `tests/README.md` for complete test organization and feature mapping.

### Quick Commands

```bash
# Run all tests (64 tests across 5 files)
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_cli.py -v

# Count tests
uv run pytest tests/ --collect-only -q
```

### When Adding Features

1. Find the test file for that module (see feature mapping in `tests/README.md`)
2. Write test first (TDD)
3. Run `uv run pytest tests/test_<module>.py -v`
4. Implement feature
5. Run full test suite to verify no regressions

### Install and Test

```bash
# Install from git
uv tool install git+https://github.com/ilkkanisula/imggen.git

# Or install locally for development
uv pip install -e .

# Run full test suite
uv run pytest tests/

# Test installed tool
imggen setup
imggen --version
imggen --help
```

### Test with Real Providers

```bash
# Setup API keys
imggen setup

# Test OpenAI provider (default)
imggen -p "a serene landscape at sunset"

# Test with variations
imggen -p "test prompt" --variations 4 --output ./test_output/

# Test Google provider
imggen -p "landscape" --provider google --resolution 4K

# Dry run (estimate cost without generating)
imggen -p "landscape" --variations 4 --dry-run
```

## Versioning and Release

See `.claude/skills/release.md` for complete release process instructions.

Key points:
- Update `pyproject.toml` and `src/imggen/version.py`
- Update `RELEASES.md` (new release at top)
- Create git tag and push to remote
- Tags required for `imggen check-update` functionality


