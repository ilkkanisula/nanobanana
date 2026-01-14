# Cost Calculation Research: OpenAI vs Google Image Generation APIs

## Executive Summary

Both OpenAI and Google provide sufficient metadata in API responses to calculate accurate costs of image generation calls. The key difference: OpenAI requires inference from image properties (quality, resolution) while Google provides direct token counts that can be converted to costs mathematically.

**Conclusion: YES, cost calculation is fully possible for both providers.**

## OpenAI GPT Image 1.5 Cost Model

### Pricing Structure

OpenAI uses **per-image pricing** based on two dimensions: quality and resolution.

#### Pricing Table

| Resolution | Quality | Cost per Image |
|-----------|---------|----------------|
| 1024x1024 | low | $0.009 |
| 1024x1024 | medium | $0.034 |
| 1024x1024 | high | $0.133 |
| 1024x1536 / 1536x1024 | low | $0.013 |
| 1024x1536 / 1536x1024 | medium | $0.050 |
| 1024x1536 / 1536x1024 | high | $0.200 |

### API Response Fields for Cost Calculation

OpenAI image generation responses include:
- `quality` - The quality tier (low, medium, high)
- `size` - The image dimensions (1024x1024, 1024x1536, 1536x1024)
- `revised_prompt` - The enhanced prompt (already captured in metadata spec)
- `created` - Unix timestamp (already captured in metadata spec)

### Cost Calculation Method

**Inference-based:** Look up quality + size in pricing table → retrieve cost

```python
def calculate_openai_cost(quality: str, size: str) -> float:
    """Calculate cost from image properties."""
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

### Accuracy Level

**High accuracy** - OpenAI's API explicitly returns quality and size, making inference deterministic and reliable. Pricing has been stable since GPT Image 1.5 release (January 2025).

### Implementation Complexity

**Low** - Simple dictionary lookup from two fields returned in response.

## Google Gemini 3 Pro Image Cost Model

### Pricing Structure

Google uses **token-based pricing** with separate rates for input and output tokens.

#### Input Costs
- Text input: **$2.00 per million tokens**
- Image input: **$0.0011 per image** (internally = 560 tokens)

#### Output Costs (Image Generation)
- 1K resolution (1024x1024): **1120 tokens** → **$0.134 per image**
- 2K resolution (2048x2048): **1120 tokens** → **$0.134 per image**
- 4K resolution (4096x4096): **2000 tokens** → **$0.24 per image**

#### Batch Mode (50% discount)
- Text input: $1.00 per million tokens
- Image output: 1K/2K: $0.067, 4K: $0.12

### API Response Fields for Cost Calculation

Google API returns comprehensive `usageMetadata`:
- `promptTokenCount` - Number of input tokens (text + reference images)
- `candidatesTokenCount` - Number of output tokens (generated image)
- `totalTokenCount` - Sum of both
- `cachedContentTokenCount` - Cached tokens (if caching used)

### Cost Calculation Method

**Direct mathematical calculation from response tokens:**

```python
def calculate_google_cost(
    prompt_tokens: int,
    output_tokens: int,
    batch_mode: bool = False,
    use_caching: bool = False
) -> float:
    """Calculate cost from token counts."""
    if batch_mode:
        input_rate = 1.00 / 1_000_000
        output_rate = 60.00 / 1_000_000  # For standard 1K/2K images
    else:
        input_rate = 2.00 / 1_000_000
        output_rate = 120.00 / 1_000_000  # For standard 1K/2K images

    input_cost = prompt_tokens * input_rate
    output_cost = output_tokens * output_rate
    return input_cost + output_cost
```

### Example Calculations

**Single 2K image with 500-char prompt:**
- Text prompt: ~125 tokens
- Reference image: 560 tokens
- Input total: 685 tokens
- Output (2K image): 1120 tokens
- Cost: (685 × $2.00 / 1M) + (1120 × $120.00 / 1M) = $0.00137 + $0.1344 = **$0.1358**

**Same request in batch mode:**
- Cost: (685 × $1.00 / 1M) + (1120 × $60.00 / 1M) = $0.000685 + $0.0672 = **$0.0679** (50% savings)

### Accuracy Level

**Very high accuracy** - Google's API explicitly returns token counts, enabling exact cost calculation. The formula is deterministic and can be verified against Google's published rates.

### Implementation Complexity

**Low** - Simple arithmetic operation using two fields returned in response.

## Comparison and Unified Approach

| Aspect | OpenAI | Google |
|--------|--------|--------|
| Cost Visibility | Inference from response fields | Direct token counts in response |
| Accuracy | High (deterministic mapping) | Very high (mathematical formula) |
| Pricing Stability | Stable since Jan 2025 | Defined until changed |
| Implementation | Dictionary lookup | Arithmetic calculation |
| Maintainability | Need pricing table updates | Self-documenting (formula) |
| Batching | ❌ No batch API for images | ✅ Native batch mode |

## Unified JSON Response Format

Both providers can return a unified cost calculation in the metadata JSON file:

```json
{
  "original_prompt": "a serene landscape at sunset",

  // OpenAI-specific
  "revised_prompt": "An intricately detailed, vibrant acrylic painting...",
  "created": "2025-01-13T15:30:00Z",
  "quality": "high",
  "size": "1024x1024",

  // Google-specific
  "model_version": "gemini-3-pro-image-preview-001",
  "response_id": "abc123xyz789",
  "finish_reason": "STOP",
  "prompt_tokens": 125,
  "output_tokens": 1120,

  // Unified across both providers
  "provider": "openai",
  "model": "gpt-image-1.5",
  "cost_usd": 0.133,
  "batch_mode": false
}
```

## Cost Field Implementation

### OpenAI Cost Calculation

In `openai_provider.py`:

```python
def calculate_openai_image_cost(quality: str, size: str) -> float:
    """Calculate cost from image properties."""
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

Return cost in response:
```python
return {
    "status": "success",
    "filename": filename,
    "revised_prompt": revised_prompt,
    "created": created,
    "quality": response.data[0].quality,
    "size": response.data[0].size,
    "cost_usd": calculate_openai_image_cost(
        response.data[0].quality,
        response.data[0].size
    )
}
```

### Google Cost Calculation

In `google_provider.py`:

```python
def calculate_google_image_cost(
    prompt_tokens: int,
    output_tokens: int,
    batch_mode: bool = False
) -> float:
    """Calculate cost from token counts."""
    input_rate = (1.00 if batch_mode else 2.00) / 1_000_000
    output_rate = (60.00 if batch_mode else 120.00) / 1_000_000
    return (prompt_tokens * input_rate) + (output_tokens * output_rate)
```

Return cost in response:
```python
cost = calculate_google_image_cost(
    response.usage_metadata.prompt_token_count,
    response.usage_metadata.candidates_token_count,
    batch_mode=False
)

return {
    "status": "success",
    "filename": filename,
    "model_version": model_version,
    "response_id": response_id,
    "finish_reason": finish_reason,
    "prompt_tokens": response.usage_metadata.prompt_token_count,
    "output_tokens": response.usage_metadata.candidates_token_count,
    "cost_usd": cost
}
```

## Storage in JSON Metadata Files

The `save_metadata_file()` helper should accept cost information:

```python
def save_metadata_file(
    output_dir: str,
    filename: str,
    original_prompt: str,
    provider: str,
    model: str,
    cost_usd: float = None,
    **kwargs  # Provider-specific fields (revised_prompt, model_version, etc.)
) -> None:
    """Save metadata JSON file alongside image."""
    import json

    base_name = os.path.splitext(filename)[0]
    metadata_path = os.path.join(output_dir, f"{base_name}.json")

    metadata = {
        "original_prompt": original_prompt,
        "provider": provider,
        "model": model,
        "cost_usd": cost_usd,
    }

    # Add provider-specific fields
    metadata.update(kwargs)

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
```

## Recommendations

1. **Store cost in response** - Both providers can calculate cost from response data
2. **Include cost_usd in JSON metadata** - Enables cost analysis and auditing
3. **Maintain provider pricing tables** - Store in `src/imggen/pricing.py` (already exists)
4. **Add cost to cost calculation feature** - Update pricing module with both calculation functions
5. **Enable cost tracking** - Users can analyze costs across provider usage patterns

## Future Enhancement Opportunities

1. **Cost estimation before generation** - Calculate costs from prompt length before API call
2. **Cost aggregation** - Sum costs across multiple images for user reporting
3. **Cost comparison** - Show user cost difference between providers for same request
4. **Cost optimization suggestions** - Flag when higher quality tier used for identical visual output
5. **Rate limiting by cost** - Prevent expensive requests via cost thresholds
