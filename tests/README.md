# Test Organization

Tests follow Core Patterns (Factory Pattern, Separation of Concerns, Pre-flight Validation, Fail Fast). Each module has a dedicated test file with no mixed concerns.

## Quick Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_cli.py -v

# Count tests
uv run pytest tests/ --collect-only -q
```

## Test Organization

| Module | Test File | Tests | Coverage |
|--------|-----------|-------|----------|
| `providers/__init__.py` | `test_providers.py` | 17 | Factory, inference, interface, model listing |
| `providers/openai_provider.py` | `test_openai_provider.py` | 20 | Input fidelity, references, metadata, model parameter |
| `providers/google_provider.py` | `test_google_provider.py` | 17 | References, metadata, model parameter |
| `config.py` | `test_config.py` | 6 | Config migration, multi-key support |
| `pricing.py` | `test_pricing.py` | 10 | Cost calculations for all providers |
| `generator.py` | `test_generator.py` | 4 | File collision detection |
| `cli.py` | `test_cli.py` | 34 | Argument validation, prompt/reference loading |
| `conftest.py` | `conftest.py` | - | Shared fixtures and mock responses |
| **Total** | **8 files** | **118 tests** | **100% of modules** |

## Test Files

### conftest.py
Shared pytest configuration and fixtures for all tests.
- `temp_dir` - Temporary directory for test files
- `sample_prompts_file` - Sample prompts file
- `sample_batch_yaml` - Sample batch configuration
- `sample_image_data` - Minimal valid PNG image data
- `openai_mock_response` - Mock OpenAI API response
- `google_mock_response` - Mock Google API response
- `google_response_factory` - Factory for customizable Google responses

### test_providers.py (17 tests)
Provider factory pattern, inference, interface, and model listing tests.
- `TestProviderFactory` (3 tests) - Create Google and OpenAI providers
- `TestProviderInference` (5 tests) - Infer provider from model name
- `TestProviderInterface` (2 tests) - Verify required methods
- `TestModelListing` (7 tests) - Model availability and listing functions

### test_openai_provider.py (20 tests)
OpenAI provider-specific functionality tests.
- `TestOpenAIInputFidelity` (4 tests) - Input fidelity parameter handling
- `TestOpenAIProviderReferenceImages` (6 tests) - Reference image support
- `TestOpenAIMetadata` (8 tests) - Metadata extraction and cost calculation
- `TestOpenAIProviderModelParameter` (2 tests) - Model parameter handling

### test_google_provider.py (17 tests)
Google provider-specific functionality tests.
- `TestGoogleReferenceImages` (5 tests) - Reference image support
- `TestGoogleMetadata` (10 tests) - Metadata extraction and cost calculation
- `TestGoogleProviderModelParameter` (2 tests) - Model parameter handling

### test_config.py (6 tests)
Configuration management and multi-provider API key support.
- `TestConfigMigration` - Old format → new format
- `TestMultiProviderConfig` - Multi-provider API key storage

### test_pricing.py (10 tests)
Cost calculations for all providers and quality/resolution settings.
- `TestPricingCalculations` - OpenAI quality levels, Google resolutions

### test_generator.py (4 tests)
Image generation orchestration and pre-flight validation.
- `TestFileCollisionDetection` - Prevent file overwrites before API calls

### test_cli.py (34 tests)
CLI argument parsing and validation (Fail Fast pattern).
- `TestPromptLoading` (7 tests) - Load from text or file
- `TestReferenceLoading` (7 tests) - Load reference images
- `TestArgumentValidation` (20 tests) - Aspect ratio, quality, resolution, variations

## Feature-to-Test Mapping

| Feature | Test File(s) | Test Class |
|---------|-------------|-----------|
| Image generation from prompts | test_generator.py, test_cli.py | TestPromptLoading, TestGenerateImage |
| Multiple variations | test_generator.py, test_pricing.py | TestGenerateImage, TestPricingCalculations |
| Reference images (OpenAI) | test_openai_provider.py, test_cli.py | TestOpenAIProviderReferenceImages, TestReferenceLoading |
| Reference images (Google) | test_google_provider.py, test_cli.py | TestGoogleReferenceImages, TestReferenceLoading |
| Quality/resolution options | test_pricing.py, test_cli.py | TestPricingCalculations, TestArgumentValidation |
| Aspect ratio control | test_cli.py | TestArgumentValidation |
| Multiple providers | test_providers.py, test_pricing.py | TestProviderFactory, TestPricingCalculations |
| Cost estimation | test_pricing.py, test_openai_provider.py, test_google_provider.py | TestPricingCalculations, TestOpenAIMetadata, TestGoogleMetadata |
| API key management | test_config.py | TestConfigMigration, TestMultiProviderConfig |
| File collision prevention | test_generator.py | TestFileCollisionDetection |
| Input fidelity (OpenAI) | test_openai_provider.py | TestOpenAIInputFidelity |
| Metadata extraction | test_openai_provider.py, test_google_provider.py | TestOpenAIMetadata, TestGoogleMetadata |

## Verify Organization

Check test structure alignment:

```bash
# 1. No duplicate test names
grep -r "def test_" tests/ | cut -d: -f2 | sort | uniq -d

# 2. Total test count (should be 118)
uv run pytest tests/ --collect-only -q

# 3. All test files exist
ls -la tests/test_*.py

# 4. Module → test file mapping
for file in src/imggen/{cli,config,generator,pricing}.py src/imggen/providers/__init__.py src/imggen/providers/{openai_provider,google_provider}.py; do
  module=$(basename $file .py)
  test_file="tests/test_${module}.py"
  if [ -f "$test_file" ]; then echo "✓ $test_file"; else echo "✗ $test_file"; fi
done
```

## When Adding New Features

1. **Find related tests** - Check which test file covers the feature area
2. **Add TDD test first** - Write test in that test file before implementation
3. **Run that test file** - `uv run pytest tests/test_<module>.py -v`
4. **Implement** - Add feature code
5. **Run all tests** - Ensure no regressions
