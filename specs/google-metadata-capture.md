# imggen Google Metadata Capture

## Overview

Capture and persist Google Gemini API metadata alongside generated images. The Google image API returns valuable metadata (model version, response ID, finish reason, token usage) that is currently discarded. This feature enables transparency into generation success/failure reasons, cost tracking, and reproducibility.

## Metadata Fields

**Always available from Google API:**
- `model_version` - The specific model version used (e.g., `gemini-3-pro-image-preview-001`)
- `response_id` - Unique identifier for the API response
- `finish_reason` - Why generation completed (STOP, MAX_TOKENS, IMAGE_SAFETY, IMAGE_PROHIBITED_CONTENT, etc.)
- `prompt_tokens` - Input tokens consumed (from usageMetadata.promptTokenCount)
- `output_tokens` - Output tokens consumed (from usageMetadata.candidatesTokenCount)
- `cost_usd` - Cost of generation calculated from token counts

**Implementation scope:** Capture all fields above for debugging, reproducibility, transparency into safety/failure reasons, and accurate cost tracking.

## Architecture

### Change 1: Update Google Provider Response

Modify `src/imggen/providers/google_provider.py` to return metadata alongside filename.

**Current response:**
```python
{"status": "success", "filename": "imggen_001.png"}
```

**New response:**
```python
{
    "status": "success",
    "filename": "imggen_001.png",
    "model_version": "gemini-3-pro-image-preview-001",
    "response_id": "abc123xyz789",
    "finish_reason": "STOP",
    "prompt_tokens": 125,
    "output_tokens": 1120,
    "cost_usd": 0.1358
}
```

**For failed responses:** Include `finish_reason` when available to indicate why generation failed (e.g., safety blocks):
```python
{
    "status": "failed",
    "error": "Content filter blocked generation",
    "finish_reason": "IMAGE_SAFETY",
    "rate_limited": False
}
```

### Change 2: Store Metadata as JSON Files

Save metadata alongside each image as a `.json` file (same as OpenAI implementation).

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

**JSON file format (`imggen_001.json`):**
```json
{
  "original_prompt": "a serene landscape at sunset",
  "model_version": "gemini-3-pro-image-preview-001",
  "response_id": "abc123xyz789",
  "finish_reason": "STOP",
  "prompt_tokens": 125,
  "output_tokens": 1120,
  "provider": "google",
  "model": "gemini-3-pro-image-preview",
  "cost_usd": 0.1358
}
```

### Change 3: Generator Functions

Update `src/imggen/generator.py` to handle metadata storage (same as OpenAI):

**`generate_single_image()`** - Already passes metadata through, no changes needed.

**`generate_from_prompt()`** - Save JSON files alongside images after successful generation.

## Implementation Details

### Step 1: Update Google Provider (src/imggen/providers/google_provider.py)

Extract metadata from the response object and calculate cost:

1. Extract `response.model_version` or fallback to model parameter
2. Extract `response.response_id`
3. Extract `response.candidates[0].finish_reason`
4. Extract `response.usage_metadata.prompt_token_count`
5. Extract `response.usage_metadata.candidates_token_count`
6. Calculate cost from token counts
7. Return metadata in success response
8. For errors, include `finish_reason` if available

**Cost calculation helper:**
```python
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
        output_rate = 60.00 / 1_000_000  # For standard 1K/2K images
    else:
        input_rate = 2.00 / 1_000_000
        output_rate = 120.00 / 1_000_000  # For standard 1K/2K images

    return (prompt_tokens * input_rate) + (output_tokens * output_rate)
```

**Code changes:**
```python
# Around line 98-125 (after extracting image data)

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
```

### Step 2: Update Generator (src/imggen/generator.py)

Use existing `save_metadata_file()` helper (from OpenAI implementation) with Google-specific fields.

**In `generate_from_prompt()`:**
- After collecting results in the parallel generation loop
- For each successful result, call `save_metadata_file()` with Google fields
- Collect model name from provider instance

## CLI Display Behavior

For now, metadata is stored silently (no CLI changes). In future iterations, users could:
- Add `--show-metadata` flag to display model version and token usage
- Add `--save-metadata` flag to control behavior
- Display safety block reasons when generation fails

This keeps initial implementation focused and reversible.

## Testing Strategy

**New test cases required in `tests/test_google_provider.py`:**
1. Verify Google provider returns all metadata fields in success response
2. Verify `prompt_tokens` and `output_tokens` are extracted from usageMetadata
3. Verify `cost_usd` is calculated correctly from token counts
4. Test cost calculation with various token combinations
5. Verify `finish_reason` is captured in error responses
6. Mock Google API response with various finish_reason values (STOP, IMAGE_SAFETY, etc.)

**Reuse existing tests from `tests/test_generator.py`:**
- Metadata file creation tests can be shared (same file format)
- Verify JSON files contain all Google-specific fields including cost_usd

**Integration test:**
```bash
imggen -p "test prompt" --provider google --variations 2
# Check: imggen_001.png, imggen_001.json, imggen_002.png, imggen_002.json exist
# Check: JSON files contain model_version, response_id, finish_reason, prompt_tokens, output_tokens, cost_usd
```

## Backwards Compatibility

✅ **No breaking changes:**
- New JSON files are optional metadata
- Existing code using only PNG files continues to work
- Return dict in provider includes new fields but doesn't remove existing ones

## Files to Modify

1. `src/imggen/providers/google_provider.py` - Extract metadata from response
2. `src/imggen/generator.py` - Already handles metadata storage via existing helper
3. `tests/test_google_provider.py` - Add metadata extraction tests
4. `tests/test_generator.py` - Add tests for Google metadata storage (reuse existing helpers)

## Cost Calculation

### Pricing Model (Verified January 2026)

Google uses token-based pricing for image generation. These prices are verified current as of January 13, 2026.

**Official Sources:**
- [https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [https://cloud.google.com/vertex-ai/generative-ai/pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

#### Interactive Mode (Real-time)
| Category | Rate |
|----------|------|
| Text input | $2.00 per million tokens |
| Image input | $0.0011 per image (560 tokens internally) |
| Image output (1K/2K) | 1120 tokens → $0.134 per image |
| Image output (4K) | 2000 tokens → $0.24 per image |

#### Batch Mode (Asynchronous, 50% Discount)
| Category | Rate |
|----------|------|
| Text input | $1.00 per million tokens |
| Image input | $0.0006 per image (560 tokens) |
| Image output (1K/2K) | $0.067 per image |
| Image output (4K) | $0.12 per image |

**Pricing Notes:**
- Token-based pricing allows cost variation based on prompt length
- 1K and 2K resolutions share identical pricing ($0.134) despite resolution difference
- 4K resolution carries 79% cost premium over 2K ($0.24 vs $0.134)
- Batch mode provides 50% cost reduction on all token costs
- Cost calculation is mathematically deterministic from token counts

### Calculation Method

Cost is calculated directly from token counts returned in the API response:

**Interactive Mode Formula:**
```python
cost_usd = (prompt_tokens × 2.00 / 1_000_000) + (output_tokens × 120.00 / 1_000_000)
```

**Batch Mode Formula:**
```python
cost_usd = (prompt_tokens × 1.00 / 1_000_000) + (output_tokens × 60.00 / 1_000_000)
```

**Properties:**
- **Mathematically exact** - Derived directly from token counts in response
- **Verifiable** - Output tokens × $120/M matches published rates
- **Deterministic** - No external lookups needed, formula is universal

### Cost Calculation Function

```python
def calculate_google_image_cost(
    prompt_tokens: int,
    output_tokens: int,
    batch_mode: bool = False
) -> float:
    """Calculate cost from token counts.

    Args:
        prompt_tokens: Number of input tokens (text + images)
        output_tokens: Number of output tokens (generated image)
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
```

### Example Calculations

**Interactive Mode - 2K Image:**
- Text prompt: 125 tokens
- Reference image: 560 tokens
- Total input: 685 tokens
- Image output (2K): 1120 tokens
- Calculation:
  - Input cost: 685 × $2.00 / 1,000,000 = $0.00137
  - Output cost: 1120 × $120.00 / 1,000,000 = $0.1344
  - **Total: $0.13577**

**Batch Mode - Same Request:**
- Input cost: 685 × $1.00 / 1,000,000 = $0.000685
- Output cost: 1120 × $60.00 / 1,000,000 = $0.0672
- **Total: $0.0679** (50% savings)

**4K Image Generation:**
- Assuming same token counts as above
- Output tokens: 2000 (for 4K)
- Interactive cost: $0.00137 + (2000 × $120.00 / 1M) = $0.24137
- Batch cost: $0.000685 + (2000 × $60.00 / 1M) = $0.12069

### Storage

The calculated `cost_usd` is stored in:
1. Google provider response dict (already available for downstream processing)
2. JSON metadata file alongside the PNG image

### Implementation Verification

Cost calculation implementation can be verified against:
- Official Gemini API pricing: [https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Vertex AI pricing: [https://cloud.google.com/vertex-ai/generative-ai/pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- Verification document: `docs/api_pricing_verification_2026.md`

## Related Documentation

- `docs/api_pricing_verification_2026.md` - Official pricing verification with source links
- `docs/cost_calculation_research.md` - Detailed pricing research on both OpenAI and Google
- `docs/google_api_metadata_research.md` - Research on Google API metadata capabilities and comparison with OpenAI

## Implementation Order

1. Write tests for Google provider metadata extraction
2. Implement Google provider changes
3. Verify metadata file storage works for Google (reuse from OpenAI tests)
4. Run full test suite
5. Manual integration test with real API

## Future Enhancements (Out of Scope)

- CLI flags to control metadata display/storage
- Safety block notifications when `IMAGE_SAFETY` or `IMAGE_PROHIBITED_CONTENT` returned
- Token usage analytics across multiple generations
- Batch generation manifest with metadata
