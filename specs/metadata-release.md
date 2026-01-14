# imggen Metadata Capture Release (v1.1.0)

## Overview

Release metadata capture feature for both OpenAI and Google providers. This is a minor version bump (1.0.1 → 1.1.0) adding backwards-compatible metadata persistence alongside generated images.

## Feature Summary

### OpenAI Metadata Capture
- Capture `revised_prompt` (prompt enhanced by OpenAI)
- Capture `created` timestamp (ISO 8601 format)
- Capture `quality` and `size` (quality tier and image dimensions)
- **Calculate and capture `cost_usd`** (inferred from quality + size)
- Store as JSON files alongside PNG images

### Google Metadata Capture
- Capture `model_version` (exact model version used)
- Capture `response_id` (unique API response identifier)
- Capture `finish_reason` (STOP, MAX_TOKENS, IMAGE_SAFETY, etc.)
- Capture `prompt_tokens` and `output_tokens` (token counts from usageMetadata)
- **Calculate and capture `cost_usd`** (from token counts)
- Store as JSON files alongside PNG images using same format

### Cost Calculation
- **OpenAI:** Infer cost from quality and size (dictionary lookup from pricing table)
- **Google:** Calculate cost mathematically from token counts (deterministic formula)
- Both providers enable accurate per-image cost tracking
- Unified `cost_usd` field in JSON files enables cost analysis across providers

### Unified Implementation
- Both providers use same JSON file naming and structure
- Both include `cost_usd` field for transparent cost tracking
- Optional metadata fields allow provider-specific data
- Zero impact on existing users (metadata files are optional)
- Same helper functions used for both providers

## Related Specifications

- `specs/openai-metadata-capture.md` - OpenAI implementation details (includes cost calculation)
- `specs/google-metadata-capture.md` - Google implementation details (includes cost calculation)
- `docs/google_api_metadata_research.md` - Research findings on Google API metadata capabilities
- `docs/cost_calculation_research.md` - Detailed cost calculation research for both providers

## Files to Modify

### Core Implementation
1. `src/imggen/providers/openai_provider.py` - Extract OpenAI metadata
2. `src/imggen/providers/google_provider.py` - Extract Google metadata
3. `src/imggen/generator.py` - Unified metadata file storage (helper function)

### Tests
1. `tests/test_openai_provider.py` - Add OpenAI metadata extraction tests
2. `tests/test_google_provider.py` - Add Google metadata extraction tests
3. `tests/test_generator.py` - Add metadata file creation and storage tests

### Version & Release
1. `pyproject.toml` - Update version to 1.1.0
2. `src/imggen/version.py` - Update __version__ to 1.1.0
3. `RELEASES.md` - Add v1.1.0 release notes

## Implementation Order

1. **Write tests first (TDD):**
   - OpenAI cost calculation function tests
   - OpenAI provider metadata extraction tests (including cost)
   - Google cost calculation function tests
   - Google provider metadata extraction tests (including cost)
   - Metadata file storage tests with cost fields (shared helper)

2. **Implement cost calculation functions:**
   - Add `calculate_openai_image_cost(quality, size)` to openai_provider.py
   - Add `calculate_google_image_cost(prompt_tokens, output_tokens)` to google_provider.py

3. **Implement OpenAI provider changes:**
   - Extract revised_prompt, created, quality, size from response
   - Calculate cost using helper function
   - Return metadata (including cost_usd) in success responses
   - Handle error responses (no metadata needed)

4. **Implement Google provider changes:**
   - Extract model_version, response_id, finish_reason, prompt_tokens, output_tokens from response
   - Calculate cost using helper function
   - Return metadata (including cost_usd) in success responses
   - Include finish_reason in error responses for debugging

5. **Implement generator metadata storage:**
   - Create/update `save_metadata_file()` helper function to accept cost_usd
   - Call helper for each successful image generation
   - Handle both OpenAI and Google provider responses

6. **Run full test suite:**
   - All tests must pass
   - No regressions in existing functionality
   - Verify metadata files are created correctly with cost_usd

7. **Manual integration testing:**
   - Test with real OpenAI API, verify cost_usd accuracy
   - Test with real Google API, verify cost_usd accuracy
   - Verify JSON files contain correct cost values
   - Verify backwards compatibility (PNG-only usage still works)
   - Calculate total cost from metadata files across multiple generations

## Release Steps

### Pre-Release
```bash
uv run pytest tests/ -v
# All tests must pass
```

### Version Updates
1. Update `pyproject.toml` version to 1.1.0
2. Update `src/imggen/version.py` __version__ to 1.1.0
3. Add release notes to top of `RELEASES.md`:
   ```markdown
   ## v1.1.0 - YYYY-MM-DD

   ### Features
   - Metadata capture for OpenAI: revised_prompt, created timestamp, quality, size
   - Metadata capture for Google: model_version, response_id, finish_reason, token counts
   - **Cost calculation for both providers:**
     - OpenAI: Inferred from quality and image size
     - Google: Calculated from token counts
   - JSON metadata files stored alongside generated images
   - Provider-specific metadata with optional fields for future expansion

   ### Technical Details
   - No breaking changes; metadata files are optional
   - Existing code continues to work without modification
   - Accurate per-image cost tracking for both OpenAI and Google
   - Token usage tracking for transparency and optimization
   - Enhanced debugging with finish_reason for safety blocks
   - Unified cost_usd field enables cost analysis across providers
   ```

### Git Commit and Tag
```bash
git add .
git commit -m "Bump version to 1.1.0"
git tag v1.1.0
git push origin main
git push origin v1.1.0
```

### Verification
```bash
git tag -l  # Should show v1.1.0
imggen --version  # Should show 1.1.0
```

## Backwards Compatibility

✅ **Fully backwards compatible:**
- New JSON files are optional metadata (do not affect existing workflows)
- Existing code using only PNG files continues to work unchanged
- Return dictionaries include new fields but don't remove existing ones
- Zero CLI changes; metadata stored silently

## Testing Checklist

- [ ] All existing tests pass
- [ ] OpenAI cost calculation function tested with all quality/size combinations
- [ ] Google cost calculation function tested with various token counts
- [ ] OpenAI provider tests verify metadata extraction (including quality, size, cost)
- [ ] Google provider tests verify metadata extraction (including token counts, cost)
- [ ] Cost values are calculated correctly in both providers
- [ ] Generator tests verify JSON file creation with cost fields
- [ ] JSON files contain correct field names, values, and cost_usd
- [ ] Both provider responses work with metadata helper
- [ ] Error responses handled correctly
- [ ] Safety failure modes captured in finish_reason (Google)
- [ ] Integration test: real OpenAI API generates images with accurate cost_usd
- [ ] Integration test: real Google API generates images with accurate cost_usd
- [ ] Backwards compatibility: PNG-only usage works without metadata files
- [ ] Cost accumulation: multiple images tracked with individual costs

## Future Enhancements (Out of Scope)

- CLI flags to display or hide metadata
- Cost reporting and aggregation tools (--show-costs, cost summary after generation)
- Metadata query and analysis tools (search by cost range, provider, etc.)
- Batch generation manifests with cost totals
- Automatic prompt comparison tools (original vs revised for OpenAI)
- Safety violation notifications
- Cost optimization suggestions based on quality/resolution trade-offs
- Integration with cost tracking/billing systems
