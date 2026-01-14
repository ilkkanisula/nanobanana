# API Pricing Verification - January 2026

## Overview

This document verifies current pricing for image generation APIs used by imggen as of January 2026. Pricing is sourced exclusively from official OpenAI and Google documentation.

**Last Updated:** January 13, 2026
**Verification Status:** ✅ Current pricing confirmed from official sources

---

## OpenAI GPT Image 1.5 Pricing

### Official Source
**Primary:** [https://platform.openai.com/docs/models/gpt-image-1.5](https://platform.openai.com/docs/models/gpt-image-1.5)
**Pricing Page:** [https://platform.openai.com/docs/pricing](https://platform.openai.com/docs/pricing)

### Image Generation Pricing by Quality and Resolution

| Resolution | Low Quality | Medium Quality | High Quality |
|-----------|-------------|----------------|--------------|
| 1024x1024 | $0.009 | $0.034 | $0.133 |
| 1024x1536 | $0.013 | $0.050 | $0.200 |
| 1536x1024 | $0.013 | $0.050 | $0.200 |

**Source Citation:** Platform.openai.com GPT Image 1.5 Model Documentation

### Token-Based Pricing for Prompts and Image Inputs

**Text Tokens:** $5.00 per million tokens (input)
**Text Tokens:** $40.00 per million tokens (output)
**Image Tokens:** $8.00 per million tokens (input)
**Image Tokens (cached):** $2.00 per million tokens

**Notes:**
- Image inputs for reference/editing use token-based pricing
- Standard per-image costs (table above) apply to image generation
- When using Responses API with image_generation tool, the usage field reports text token consumption from the mainline model
- Image generation costs must be inferred from response metadata (quality + size)

**Source Citation:** Platform.openai.com Pricing Documentation

### Pricing Changes Since GPT Image 1

GPT Image 1.5 pricing is approximately 20% cheaper than GPT Image 1:

| Resolution | GPT Image 1 | GPT Image 1.5 | Savings |
|-----------|------------|--------------|---------|
| 1024x1024 (Low) | $0.011 | $0.009 | 18% |
| 1024x1024 (Medium) | $0.042 | $0.034 | 19% |
| 1024x1024 (High) | $0.167 | $0.133 | 20% |
| 1024x1536 (High) | $0.250 | $0.200 | 20% |

---

## Google Gemini 3 Pro Image Pricing

### Official Sources
**API Documentation:** [https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)
**Vertex AI Pricing:** [https://cloud.google.com/vertex-ai/generative-ai/pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

### Token-Based Pricing Structure

**Interactive Mode (Real-time):**
- Text input: $2.00 per million tokens
- Image input: $0.0011 per image (560 tokens internally)
- Image output (1K/2K): 1120 tokens → $0.134 per image
- Image output (4K): 2000 tokens → $0.24 per image

**Batch Mode (Asynchronous, 50% discount):**
- Text input: $1.00 per million tokens
- Image input: $0.0006 per image (560 tokens)
- Image output (1K/2K): $0.067 per image
- Image output (4K): $0.12 per image

**Source Citation:** ai.google.dev Gemini API Pricing Documentation

### Output Resolution Categories

| Resolution | Output Tokens | Interactive Cost | Batch Mode Cost |
|-----------|---------------|-----------------|-----------------|
| 1024x1024 (1K) | 1120 | $0.134 | $0.067 |
| 2048x2048 (2K) | 1120 | $0.134 | $0.067 |
| 4096x4096 (4K) | 2000 | $0.24 | $0.12 |

**Notes:**
- 1K and 2K resolutions share identical pricing despite resolution difference
- 4K resolution carries 79% premium over 2K
- Batch API provides 50% cost reduction on all tokens
- Cost calculation is mathematically deterministic from token counts in response

**Source Citation:** ai.google.dev and Google Cloud Pricing Documentations

### Advanced Features with Additional Costs

**Grounding with Google Search:**
- 1,500 free grounded requests per day
- Additional grounding: $35 per 1,000 queries ($0.035 per query after free quota)

**Context Caching:**
- Cache write: $1.00 per million tokens per hour
- Cache hit (read): Reduced rate (details in official documentation)

**Provisioned Throughput (Vertex AI):**
- $1,200 - $2,000 per month depending on commitment duration
- For sustained high-volume workloads (50+ images daily)

**Source Citation:** ai.google.dev and Cloud.google.com Pricing Documentations

---

## Pricing Comparison Summary

### Cost per Image (Standard Quality, 1K Resolution)

| Provider | Interactive Mode | Batch Mode | Difference |
|----------|-----------------|-----------|-----------|
| OpenAI (Medium) | $0.034 | N/A | No batch API for images |
| Google (1K) | $0.134 | $0.067 | 50% savings in batch |

**Notes:**
- OpenAI's least expensive option (low quality, 1024x1024) = $0.009
- Google's least expensive option (1K interactive) = ~$0.13 (minimum from token costs)
- Direct cost comparison difficult: OpenAI uses per-image, Google uses token-based

### Cost Calculation Methodology

**OpenAI:**
- Lookup quality + size in pricing table
- Cost is deterministic and fixed regardless of prompt length
- Determinism: ✅ High (pricing table is static)

**Google:**
- Calculate from token counts: `(prompt_tokens × input_rate) + (output_tokens × output_rate)`
- Cost varies with prompt length (input tokens)
- Determinism: ✅ Very High (mathematical formula is exact)

---

## Verification of Previously Documented Costs

### OpenAI Pricing (Previously Documented vs. Current)

**Previous Documentation:**
```
1024x1024: low=$0.009, medium=$0.034, high=$0.133
1024x1536/1536x1024: low=$0.013, medium=$0.050, high=$0.200
```

**Current Verification:** ✅ **CONFIRMED** - No changes detected

**Source:** platform.openai.com GPT Image 1.5 Documentation

### Google Pricing (Previously Documented vs. Current)

**Previous Documentation:**
```
Text input: $2.00/M tokens
Image output (1K/2K): 1120 tokens = $0.134
Image output (4K): 2000 tokens = $0.24
Batch mode: 50% discount on all costs
```

**Current Verification:** ✅ **CONFIRMED** - No changes detected

**Source:** ai.google.dev Gemini API Pricing Documentation

---

## Cost Calculation Formulas (VERIFIED)

### OpenAI Cost Formula

```
cost = pricing_table[(quality, size)]
```

**Example:**
- Quality: "high", Size: "1024x1024"
- Cost: $0.133

**Pricing Table Reference:**
```python
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
```

### Google Cost Formula (Interactive Mode)

```
cost_usd = (prompt_tokens × 2.00 / 1,000,000) + (output_tokens × 120.00 / 1,000,000)
```

**Example Calculation:**
- Text prompt: 125 tokens
- Image output (2K): 1120 tokens
- Input cost: 125 × $2.00 / 1,000,000 = $0.00025
- Output cost: 1120 × $120.00 / 1,000,000 = $0.1344
- **Total cost: $0.13465**

### Google Cost Formula (Batch Mode - 50% Discount)

```
cost_usd = (prompt_tokens × 1.00 / 1,000,000) + (output_tokens × 60.00 / 1,000,000)
```

**Same Example in Batch Mode:**
- Input cost: 125 × $1.00 / 1,000,000 = $0.000125
- Output cost: 1120 × $60.00 / 1,000,000 = $0.0672
- **Total cost: $0.0673** (50% savings)

---

## Status of Current Implementation

### ✅ Pricing in Cost Calculation Specs is ACCURATE

The pricing tables in the following specs match official documentation:
- `specs/openai-metadata-capture.md` - OpenAI pricing table (VERIFIED)
- `specs/google-metadata-capture.md` - Google pricing table (VERIFIED)
- `docs/cost_calculation_research.md` - Both pricing tables (VERIFIED)

### ✅ Cost Formulas are CORRECT

- OpenAI inference method: Deterministic lookup (CORRECT)
- Google calculation method: Token-based formula (CORRECT)
- Both formulas enable accurate per-image cost tracking (VERIFIED)

### No Updates Required

The pricing documented in implementation specs is current and accurate as of January 13, 2026. No pricing changes detected since initial research.

---

## Official Documentation References

### OpenAI Official Sources
1. **GPT Image 1.5 Model:** https://platform.openai.com/docs/models/gpt-image-1.5
2. **API Pricing:** https://platform.openai.com/docs/pricing
3. **Image Generation Guide:** https://platform.openai.com/docs/guides/image-generation

### Google Official Sources
1. **Gemini API Pricing:** https://ai.google.dev/gemini-api/docs/pricing
2. **Vertex AI Pricing:** https://cloud.google.com/vertex-ai/generative-ai/pricing
3. **Gemini 3 Pro Documentation:** https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro-image

---

## Implementation Notes

### For imggen v1.1.0 Release

**OpenAI Provider Implementation:**
- Use pricing table from verified sources above
- Quality and size from `response.data[0]` (guaranteed in response)
- Cost calculation: deterministic lookup, no API calls needed

**Google Provider Implementation:**
- Use token-based formula from verified sources above
- Token counts from `response.usage_metadata` (guaranteed in response)
- Cost calculation: simple arithmetic, no external lookups needed

**JSON Metadata Storage:**
- Both providers store `cost_usd` in same format
- Enables unified cost analysis across providers
- No provider-specific cost tracking needed

---

## Conclusion

All pricing used in imggen cost calculation specifications is current and verified against official OpenAI and Google documentation as of January 13, 2026. No updates to pricing tables or formulas are required for v1.1.0 release.

**Verification Date:** January 13, 2026
**Status:** ✅ VERIFIED - Ready for implementation
