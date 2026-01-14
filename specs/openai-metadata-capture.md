# imggen OpenAI Metadata Capture

## Overview

Capture and persist OpenAI API metadata alongside generated images. The OpenAI image API returns valuable metadata (revised_prompt, timestamp, etc.) that is currently discarded. This feature enables transparency into prompt enhancement and aids debugging.

## Metadata Fields

**Always available from OpenAI API (images.generate()):**
- `revised_prompt` - The prompt used by the model (user's prompt enhanced by OpenAI)
- `created` - Unix timestamp of generation (ISO 8601 format in storage)
- `quality` - Image quality tier (low, medium, high)
- `size` - Image dimensions (1024x1024, 1024x1536, 1536x1024)
- `cost_usd` - Cost of generation calculated from quality and size

**Partially available from images.edit():**
- `revised_prompt` - **NOT available** (always null) - see note below
- `created` - Unix timestamp of generation (ISO 8601 format in storage)
- `quality` - May be null - fallback to requested quality (see implementation details)
- `size` - May be null - fallback to requested size (see implementation details)
- `cost_usd` - Cost of generation calculated from quality and size

**Implementation scope:** Capture all fields above with graceful fallback handling for edit operations.

**Note on images.edit():** The `revised_prompt` field is intentionally null when using the images.edit() endpoint (image-to-image). This is by OpenAI architectural design since the prompt specifies modifications to an existing image rather than driving the entire generation. See [Research Summary](#research-findings-images-edit-behavior) below for detailed findings.

## Architecture

### Change 1: Update OpenAI Provider Response

Modify `src/imggen/providers/openai_provider.py` to return metadata alongside filename.

**Current response:**
```python
{"status": "success", "filename": "imggen_001.png"}
```

**New response (images.generate() - text-to-image):**
```python
{
    "status": "success",
    "filename": "imggen_001.png",
    "revised_prompt": "An intricately detailed, vibrant...",
    "created": "2025-01-13T15:30:00Z",
    "quality": "high",
    "size": "1024x1024",
    "cost_usd": 0.133
}
```

**New response (images.edit() - image-to-image with fallbacks applied):**
```python
{
    "status": "success",
    "filename": "imggen_001.png",
    "revised_prompt": "modify the colors",  # Falls back to original prompt (API returned null)
    "created": "2025-01-13T15:30:00Z",
    "quality": "high",  # Falls back to requested quality (API returned null)
    "size": "1024x1024",  # Falls back to calculated size (API returned null)
    "cost_usd": 0.133
}
```

### Change 2: Store Metadata as JSON Files

Save metadata alongside each image as a `.json` file.

**File structure:**
```
output/
├── imggen_001.png
├── imggen_001.json
├── imggen_002.png
├── imggen_002.json
└── imggen_003.png
└── imggen_003.json
```

**JSON file format - images.generate() (`imggen_001.json`):**
```json
{
  "original_prompt": "acrylic painting of a sunflower with bees",
  "revised_prompt": "An intricately detailed, vibrant acrylic painting...",
  "created": "2025-01-13T15:30:00Z",
  "quality": "high",
  "size": "1024x1024",
  "provider": "openai",
  "model": "gpt-image-1.5",
  "cost_usd": 0.133
}
```

**JSON file format - images.edit() with fallbacks (`imggen_001.json`):**
```json
{
  "original_prompt": "modify the colors to be more vibrant",
  "revised_prompt": "modify the colors to be more vibrant",
  "created": "2025-01-13T15:30:00Z",
  "quality": "high",
  "size": "1024x1024",
  "provider": "openai",
  "model": "gpt-image-1.5",
  "cost_usd": 0.133
}
```
Note: For image-to-image edits, `revised_prompt` is the same as `original_prompt` since the API returns null for edit responses.

### Change 3: Generator Functions

Update `src/imggen/generator.py` to handle metadata storage:

**`generate_single_image()`** - Already passes metadata through, no changes needed.

**`generate_from_prompt()`** - Save JSON files alongside images after successful generation.

## Implementation Details

### Step 1: Update OpenAI Provider (src/imggen/providers/openai_provider.py)

1. Extract `revised_prompt` from `response.data[0].revised_prompt` with fallback to original prompt
2. Extract `quality` and `size` from response with fallbacks to requested values
3. Convert `response.created` (Unix timestamp) to ISO 8601 string
4. Calculate cost from quality and size using pricing table
5. Return metadata in success response
6. Preserve error responses (no metadata needed)

**Important:** When using `images.edit()` endpoint (for reference images), the response will have null values for `revised_prompt`, `quality`, and `size`. The implementation must use graceful fallbacks:
- `revised_prompt` → falls back to the original prompt sent to the API
- `quality` → falls back to the quality parameter passed to the API call
- `size` → falls back to the calculated image_size based on aspect_ratio

**Cost calculation helper:**
```python
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
```

**Code changes:**
```python
# Around line 128-150 (after image decode/save)
import datetime

# After saving image:
image_path = os.path.join(output_dir, filename)
with open(image_path, "wb") as f:
    f.write(image_data)

# Extract metadata with fallbacks for images.edit() null values
# images.generate() returns full metadata, images.edit() returns nulls
revised_prompt = getattr(response.data[0], 'revised_prompt', None) or full_prompt
quality = getattr(response.data[0], 'quality', None) or openai_quality
size = getattr(response.data[0], 'size', None) or image_size
created = datetime.datetime.fromtimestamp(
    response.created, tz=datetime.timezone.utc
).isoformat()

# Calculate cost from quality and size (uses fallback values if needed)
cost = calculate_openai_image_cost(quality, size)

return {
    "status": "success",
    "filename": filename,
    "revised_prompt": revised_prompt,
    "created": created,
    "quality": quality,
    "size": size,
    "cost_usd": cost,
}
```

### Step 2: Update Generator (src/imggen/generator.py)

Add metadata storage after parallel generation completes.

**New helper function:**
```python
def save_metadata_file(
    output_dir: str,
    filename: str,
    original_prompt: str,
    provider: str,
    model: str,
    revised_prompt: str = None,
    created: str = None,
    quality: str = None,
    size: str = None,
    cost_usd: float = None,
    **kwargs  # Additional provider-specific fields
) -> None:
    """Save metadata JSON file alongside image."""
    import json

    # Remove .png extension to create .json filename
    base_name = os.path.splitext(filename)[0]
    metadata_path = os.path.join(output_dir, f"{base_name}.json")

    metadata = {
        "original_prompt": original_prompt,
        "provider": provider,
        "model": model,
        "revised_prompt": revised_prompt,
        "created": created,
        "quality": quality,
        "size": size,
        "cost_usd": cost_usd,
    }

    # Add any provider-specific fields (e.g., from Google provider)
    metadata.update(kwargs)

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
```

**In `generate_from_prompt()`:**
- After collecting results in the parallel generation loop
- For each successful result, call `save_metadata_file()` with data from result dict
- Collect model name from provider instance

**Code location:** Around line 225 in the results display loop, add metadata saving.

### Step 3: Update Provider Interface (optional)

No changes needed to `src/imggen/providers/__init__.py` - metadata fields are already included in return dict.

## CLI Display Behavior

For now, metadata is stored silently (no CLI changes). In future iterations, users could:
- Add `--show-revised-prompt` flag to display enhanced prompts
- Add `--save-metadata` flag to control behavior

This keeps initial implementation focused and reversible.

## Testing Strategy

**New test cases required in `tests/test_openai_provider.py`:**
1. Verify OpenAI provider returns `revised_prompt` and `created` in success response
2. Verify `quality` and `size` are returned in response (for images.generate())
3. Verify `cost_usd` is calculated correctly for all quality/size combinations
4. Test cost calculation with mocked quality/size combinations
5. Verify error responses still work (no metadata needed)
6. **NEW:** Verify graceful handling when `revised_prompt` is null (images.edit() case)
7. **NEW:** Verify fallback to original prompt when `revised_prompt` is null
8. **NEW:** Verify fallback to requested quality/size when response has nulls

**New test cases required in `tests/test_generator.py`:**
1. Verify JSON metadata file is created alongside image
2. Verify JSON contains all required fields with correct types
3. Verify `cost_usd` is persisted in JSON file
4. Verify JSON file uses correct naming scheme (`imggen_001.json`)
5. Verify metadata for multiple variations (all files created)
6. Verify Google provider metadata is handled with cost calculation

**Integration test:**
```bash
imggen -p "test prompt" --variations 2
# Check: imggen_001.png, imggen_001.json, imggen_002.png, imggen_002.json exist
# Check: JSON files contain valid JSON with expected structure
```

## Backwards Compatibility

✅ **No breaking changes:**
- New JSON files are optional metadata
- Existing code using only PNG files continues to work
- Return dict in provider includes new fields but doesn't remove existing ones

## Files to Modify

1. `src/imggen/providers/openai_provider.py` - Extract metadata
2. `src/imggen/generator.py` - Save metadata JSON files
3. `tests/test_openai_provider.py` - Add provider metadata tests
4. `tests/test_generator.py` - Add metadata file tests

## Future Enhancements (Out of Scope)

- CLI flags to control metadata display/storage
- Batch generation manifest with metadata
- Metadata query tools (e.g., `imggen show-metadata imggen_001.json`)
- Automatic comparison of original vs. revised prompts

## Cost Calculation

### Pricing Model (Verified January 2026)

OpenAI uses per-image pricing based on quality tier and resolution. These prices are verified current as of January 13, 2026.

**Official Source:** [https://platform.openai.com/docs/models/gpt-image-1.5](https://platform.openai.com/docs/models/gpt-image-1.5)

| Quality | 1024x1024 | 1024x1536 | 1536x1024 |
|---------|-----------|-----------|-----------|
| low     | $0.009    | $0.013    | $0.013    |
| medium  | $0.034    | $0.050    | $0.050    |
| high    | $0.133    | $0.200    | $0.200    |

**Pricing Notes:**
- All prices in USD per image
- Quality affects per-image cost significantly (low to high is 14.8x difference for 1024x1024)
- Rectangular resolutions (1024x1536, 1536x1024) cost 44% more than square
- Prices approximately 20% cheaper than GPT Image 1

### Calculation Method

Cost is calculated by looking up the quality and size returned in the API response against the pricing table above. The lookup is:
- **Deterministic** - No API calls needed, pricing table is static
- **Reliable** - OpenAI's API explicitly provides both quality and size in response
- **Accurate** - Exact per-image cost can be calculated from response metadata

**Pricing Formula:**
```python
def calculate_openai_image_cost(quality: str, size: str) -> float:
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
```

### Storage

The calculated `cost_usd` is stored in:
1. OpenAI provider response dict (already available for downstream processing)
2. JSON metadata file alongside the PNG image

### Implementation Verification

Cost calculation implementation can be verified against:
- Official pricing page: [https://platform.openai.com/docs/pricing](https://platform.openai.com/docs/pricing)
- Verification document: `docs/api_pricing_verification_2026.md`

## Related Documentation

- `docs/api_pricing_verification_2026.md` - Official pricing verification with source links
- `docs/cost_calculation_research.md` - Detailed pricing research on both OpenAI and Google
- `docs/openai_revised_prompt_field.md` - OpenAI API behavior and research
- `docs/RESEARCH_SUMMARY_openai_edit_revised_prompt.md` - Research findings on images.edit() behavior

## Research Findings: images.edit() Behavior

### Summary

The OpenAI `images.edit()` endpoint **does NOT return a revised_prompt field** unlike `images.generate()`. The field is present in the response object but set to `null`/`None`. This is **intentional architectural design**, not a bug or documentation gap.

### Key Findings (Verified January 2026)

**Endpoint Comparison:**

| Aspect | images.generate() | images.edit() |
|--------|------------------|---------------|
| `revised_prompt` | ✅ Full enhanced prompt text | ❌ Always null |
| `quality` | ✅ Populated | ⚠️ May be null |
| `size` | ✅ Populated | ⚠️ May be null |
| Prompt role | Primary input | Modification specifier |

**Why images.edit() Returns Null:**

1. **Architectural difference** - Image-to-image operations handle prompts differently than text-to-image
2. **Different workflow** - Existing image drives the generation; prompt specifies modifications only
3. **Different verification** - Users have both original and edited image to compare visually
4. **Design decision** - Consistent across all models: DALL-E 2, DALL-E 3, GPT Image 1, GPT Image 1.5

### Implications for Implementation

1. **When using text-to-image (no reference images):**
   - Use `images.generate()` endpoint
   - All fields including `revised_prompt` are fully populated
   - No fallback handling needed

2. **When using image-to-image (with reference images):**
   - Use `images.edit()` endpoint
   - `revised_prompt` will be null - use original prompt as fallback
   - `quality` and `size` may be null - use requested values as fallback
   - Metadata is still valid and valuable for cost tracking

3. **User communication:**
   - For text-to-image: Users see the enhanced prompt in metadata
   - For image-to-image: Users see the original modification prompt in metadata
   - Both are useful for understanding the generation process

### Workarounds

If `revised_prompt` data is critical for image-to-image workflows:
1. Test the modification instruction with `images.generate()` first using `image_prompt`
2. Observe the `revised_prompt` output to understand model interpretation
3. Apply that insight to the `images.edit()` call
4. Results must be verified visually (standard practice for image edits)

### Sources

- OpenAI API Reference: [https://platform.openai.com/docs/api-reference/images](https://platform.openai.com/docs/api-reference/images)
- OpenAI Image Generation Guide: [https://platform.openai.com/docs/guides/image-generation](https://platform.openai.com/docs/guides/image-generation)
- OpenAI Community Discussion: [https://community.openai.com/t/is-it-possible-to-get-the-revised-prompt-from-the-api-when-generating-images/1291440](https://community.openai.com/t/is-it-possible-to-get-the-revised-prompt-from-the-api-when-generating-images/1291440)
- Full research: See `docs/RESEARCH_SUMMARY_openai_edit_revised_prompt.md`

## Implementation Order

1. Write tests for OpenAI provider metadata extraction
2. Implement OpenAI provider changes
3. Write tests for metadata file storage
4. Implement generator metadata saving
5. Run full test suite
6. Manual integration test with real API
