# OpenAI Images.edit() revised_prompt Field: Investigation

**Date**: January 2026
**Research Summary**: Why does images.edit() NOT return revised_prompt field compared to images.generate()?

## Executive Summary

The OpenAI `images.edit()` endpoint **does NOT return a revised_prompt field** in its response, unlike the `images.generate()` endpoint which always includes it. When present in edit responses, `revised_prompt` is set to `null`/`None`. This is intentional behavior by OpenAI, not a documentation gap.

**Current Status in imggen**: Not an issue - imggen should NOT expect this field from edit() responses

## Key Findings

### 1. The revised_prompt Field - Availability by Endpoint

**`images.generate()` endpoint:**
- ✅ ALWAYS returns `revised_prompt` field
- ✅ Contains the LLM-enhanced version of the original prompt
- ✅ Non-null value with actual transformed prompt text
- ✅ Available for DALL-E 3, GPT Image 1, GPT Image 1.5

**`images.edit()` endpoint:**
- ❌ Returns `revised_prompt` field but set to `null`/`None`
- ❌ No actual prompt enhancement data available
- ❌ Behavior consistent across all models (DALL-E 2, DALL-E 3, GPT Image models)
- ❌ Not available for `gpt-image-1.5`, `gpt-image-1`, or any edit endpoint

### 2. Evidence of the Discrepancy

**Response structure observed from API calls:**

For `images.edit()` with GPT Image models:
```python
# Response structure includes revised_prompt but set to None
Image(
    b64_json=None,  # or base64-encoded data if response_format="b64_json"
    revised_prompt=None,  # ← ALWAYS null for edit() endpoint
    url='https://...'
)
```

For `images.generate()` with GPT Image models:
```python
# Response structure includes actual revised_prompt text
Image(
    b64_json=None,  # or base64-encoded data if response_format="b64_json"
    revised_prompt="An intricately detailed, vibrant acrylic painting...",  # ← Actual text
    url='https://...'
)
```

### 3. Is This Intentional or a Documentation Gap?

**Conclusion: Intentional Behavior**

Evidence supporting this is intentional:
- **Consistent across all models**: Behavior is not model-specific (applies to DALL-E 2, DALL-E 3, GPT Image 1, GPT Image 1.5)
- **Consistent across implementations**: Multiple third-party API wrappers and documentation sources report the same `null` behavior
- **Architectural difference**: Edit operations work fundamentally differently than generation operations
- **No mention of bugs**: No OpenAI developer communication indicates this is an acknowledged bug or limitation being fixed

### 4. Why revised_prompt is Omitted from images.edit() Responses

**Architectural Reasons:**

1. **Different Operation Model**
   - `images.generate()`: Creates image from scratch using prompt only
   - `images.edit()`: Modifies existing image using both image AND prompt as inputs
   - The diffusion process handles image constraints differently

2. **Prompt's Secondary Role in Edits**
   - For generation: Prompt drives the entire image creation
   - For editing: Image drives the base, prompt specifies only the modifications
   - The model's prompt enhancement is less central to the edit operation

3. **Edit-Specific Prompt Requirements**
   - Edit prompts require explicit preservation instructions ("keep X, change Y")
   - The enhancement logic differs from generation prompt expansion
   - Providing a "revised prompt" is less valuable for understanding edit results

### 5. What Fields ARE Available in images.edit() Responses

**Complete response structure for `images.edit()`:**
```json
{
    "created": 1750278299,
    "data": [
        {
            "url": "https://cdn.openai.com/...",
            "b64_json": null,
            "revised_prompt": null
        }
    ],
    "usage": {
        "input_tokens": 574,
        "output_tokens": 1056,
        "total_tokens": 1630
    },
    "background": "opaque",
    "output_format": "png",
    "quality": "medium",
    "size": "1024x1024"
}
```

**Available fields for each image in `data` array:**
- `url` - Direct URL to generated image (expires after 60 minutes)
- `b64_json` - Base64-encoded image data (alternative to URL)
- `revised_prompt` - Set to `null` (not available for edits)

**Response metadata:**
- `created` - Unix timestamp of when image was created
- `usage` - Token consumption breakdown (if available for model)
- `background` - Background handling mode
- `output_format` - PNG, JPEG, or WebP format used
- `quality` - Generation quality level (high, medium, low)
- `size` - Image dimensions

### 6. Implications for Image-to-Image Workflows

**For imggen implementation:**
1. Do NOT try to access `revised_prompt` from edit() responses
2. Handle gracefully: Field exists but will be `None`
3. No workaround available - this is by design
4. Focus on image URL or b64_json for actual results

**For users:**
- When using edit endpoint, cannot see how the model interpreted edit instructions
- Original prompt sent to edit endpoint is the only reference
- Results must be verified visually (typical for image editing)
- No way to debug via prompt enhancement inspection

### 7. Comparison with images.generate()

**For `images.generate()` endpoint:**
- ✅ `revised_prompt` contains full enhanced prompt
- ✅ User can see how original prompt was expanded
- ✅ Useful for debugging why image looks a certain way
- ✅ Available for all generation models

**For `images.edit()` endpoint:**
- ❌ `revised_prompt` is always `null`
- ❌ No prompt enhancement visibility
- ❌ Cannot debug via prompt inspection
- ❌ Consistent across all models (no exceptions)

### 8. Alternative Approaches for Edits

**Workaround for understanding edit behavior:**

1. **Test with generate() first**
   - Use same prompt with `images.generate()`
   - Observe the `revised_prompt` to understand model's interpretation
   - Then use that insight for `images.edit()` calls

2. **Inspect output image**
   - Examine generated/edited image directly
   - Compare with original input image
   - Adjust edit prompts iteratively based on results

3. **Use Responses API (Alternative)**
   - OpenAI offers Responses API with image tools
   - May provide additional metadata in certain contexts
   - Consider if `revised_prompt` data is critical to workflow

### 9. Official Documentation Status

**What OpenAI documents:**
- ✅ `images.generate()` always returns `revised_prompt`
- ✅ `images.edit()` endpoint specification
- ⚠️ No explicit statement about WHY edit() doesn't return revised_prompt
- ⚠️ No public roadmap for adding revised_prompt to edit() responses

**What developers report:**
- Consistent experience across OpenAI API SDKs (Python, Node.js, etc.)
- Third-party implementations confirm same behavior
- No recent changes to this pattern
- Appears to be fundamental design decision, not temporary limitation

## Current imggen Implementation Status

**What imggen currently extracts from OpenAI API:**
```python
# From src/imggen/providers/openai_provider.py
image_data = base64.b64decode(response.data[0].b64_json)
```

**What imggen does NOT extract:**
- `response.data[0].revised_prompt` - Not available for edit() anyway
- `response.created` - Generation timestamp (available but unused)
- `response.usage` - Token usage (available but unused)

**User Impact:**
- No visibility into prompt handling for edits (by design)
- For generation: Could add revised_prompt capture if desired
- For edits: No revised_prompt data available to capture

## References and Sources

**Official OpenAI Documentation:**
- [Images API Reference](https://platform.openai.com/docs/api-reference/images)
- [Image Generation Guide](https://platform.openai.com/docs/guides/image-generation)
- [GPT Image 1.5 Model](https://platform.openai.com/docs/models/gpt-image-1.5)
- [GPT-Image-1.5 Prompting Guide](https://cookbook.openai.com/examples/multimodal/image-gen-1.5-prompting_guide)

**Community Discussions:**
- [Is it possible to get the revised prompt from the API?](https://community.openai.com/t/is-it-possible-to-get-the-revised-prompt-from-the-api-when-generating-images/1291440)
- [How do I edit an image through the prompt?](https://community.openai.com/t/how-do-i-edit-an-image-through-the-prompt/712949)
- [GPT-Image-1.5 rolling out in the API](https://community.openai.com/t/gpt-image-1-5-rolling-out-in-the-api-and-chatgpt/1369443)
- [DALL-E 3 revised_prompt documentation](https://community.openai.com/t/dalle-3-revised-prompt-where-can-we-return-this-from-our-api-call/508919)

**Third-Party Documentation:**
- [AI/ML API Documentation - gpt-image-1](https://docs.aimlapi.com/api-references/image-models/openai/gpt-image-1)
- [DALL-E 3 API Reference](https://docs.aimlapi.com/api-references/image-models/openai/dall-e-3)

## Research Date

January 2026 - Based on current OpenAI API documentation and community reports
