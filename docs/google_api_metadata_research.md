# Google Gemini 3 Pro Image API Metadata Research

## Overview

Investigated whether Google Gemini 3 Pro Image API provides metadata equivalent to OpenAI's `revised_prompt` and `created` timestamp fields. The research reveals Google takes a fundamentally different approach to response metadata.

## Key Findings

### No Prompt Revision Equivalent

Unlike OpenAI, Google **does not provide a `revised_prompt` field**. Gemini 3 Pro Image does not automatically enhance or rewrite user prompts before generation. The model works directly with the user's prompt as provided.

**Note**: Google's Imagen models available through Vertex AI do include a prompt rewriter feature that returns a rewritten prompt, but this is not part of Gemini 3 Pro Image's standard response.

### No Creation Timestamp

Google **does not return a `created` Unix timestamp** like OpenAI. The API prioritizes version tracking and response identification over temporal information.

### Available Metadata in GenerateContentResponse

The Google API returns comprehensive metadata in alternative fields:

#### 1. **modelVersion** (Recommended for capture)
- Exact model version string (e.g., `gemini-3-pro-image-preview-001`)
- Identifies the specific model version that generated the image
- Critical for reproducibility and debugging

#### 2. **responseId** (Recommended for capture)
- Unique identifier for each API response
- Enables tracking and linking of multi-turn interactions
- Useful for correlating API calls with logs

#### 3. **finishReason** (Recommended for capture)
- Indicates why generation completed
- Values:
  - `STOP` - successful completion
  - `MAX_TOKENS` - hit token limit
  - `IMAGE_SAFETY` - content safety filter blocked generation
  - `IMAGE_PROHIBITED_CONTENT` - explicit content policy violation
  - Other safety-related reasons
- Provides debugging information when generation fails or is restricted

#### 4. **usageMetadata** (Optional for capture)
- `promptTokenCount` - input tokens consumed
- `candidatesTokenCount` - output tokens consumed
- `totalTokenCount` - sum of prompt and candidate tokens
- `promptTokensDetails` - per-modality breakdown (text, images)
- `thoughtsTokenCount` - tokens consumed by reasoning (if thinking enabled)
- Enables transparent cost calculation

#### 5. **safetyRatings** (Optional for capture)
- Granular safety assessment for potential harm categories
- Each rating includes:
  - `category` - type of harm (harassment, hate speech, dangerous content)
  - `probability` - assessment (NEGLIGIBLE to HIGH)
  - `blocked` - whether this category caused blocking
- Provides transparency on content filtering decisions

#### 6. **thoughtSignature** (For multi-turn image editing)
- Encrypted representation of model's reasoning
- Required for maintaining context in multi-turn conversations
- Not human-readable metadata, but essential for stateful interactions

## Comparison with OpenAI

| Aspect | OpenAI | Google |
|--------|--------|--------|
| Revised Prompt | ✅ Provided (`revised_prompt`) | ❌ Not provided |
| Creation Timestamp | ✅ Provided (`created`) | ❌ Not provided |
| Model Version | ❌ Not explicitly tracked | ✅ Provided (`modelVersion`) |
| Response ID | ❌ Not provided | ✅ Provided (`responseId`) |
| Finish Reason | ❌ Not detailed | ✅ Detailed (`finishReason`) |
| Token Usage | ❌ Not provided | ✅ Detailed (`usageMetadata`) |
| Safety Ratings | ❌ Not provided | ✅ Detailed (`safetyRatings`) |

## Implementation Implications

### For Google Metadata Capture Feature

1. **Should capture:**
   - `modelVersion` - for reproducibility
   - `responseId` - for tracking
   - `finishReason` - for debugging failures and safety blocks
   - `usageMetadata.totalTokenCount` - for cost transparency

2. **Could capture (optional):**
   - `usageMetadata.promptTokenCount` and `candidatesTokenCount`
   - `safetyRatings` - if blocked content needs investigation
   - `usageMetadata.thoughtsTokenCount` - if using reasoning models

3. **Should NOT capture:**
   - Client-side timestamp - tempting but unreliable (could implement later if needed)
   - `thoughtSignature` - internal use only, not for persistence

### Architectural Approach

Google metadata differs fundamentally enough from OpenAI that:
- Both providers should capture their native metadata fields
- JSON schema can use optional fields (some fields null for Google, some for OpenAI)
- This maintains clean provider separation without forcing artificial equivalence
- Future providers can follow same pattern

## Conclusion

Google provides rich metadata for debugging, cost tracking, and reproducibility, but through completely different fields than OpenAI. Both APIs are metadata-rich, just in different ways. A unified metadata capture system should embrace these differences rather than force artificial equivalence.
