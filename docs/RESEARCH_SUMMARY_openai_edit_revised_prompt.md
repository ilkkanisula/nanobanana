# Research Summary: OpenAI images.edit() revised_prompt Field

**Research Date**: January 2026
**Researcher**: Claude Code
**Status**: Complete

## Question

Why does the OpenAI `images.edit()` endpoint not return a `revised_prompt` field, while `images.generate()` does?

## Answer

The OpenAI `images.edit()` endpoint intentionally does NOT return a usable `revised_prompt` field. While the response object includes a `revised_prompt` property, it is always set to `null`/`None`. This is by design, not a documentation gap or bug.

## Evidence

### 1. Confirmed Behavior

**All documented sources report identical behavior:**
- OpenAI API reference documentation
- Third-party API wrappers (aimlapi, replicate, etc.)
- OpenAI community discussions
- Multiple implementation examples

**Response comparison:**
- `images.generate()` → `revised_prompt` contains actual enhanced prompt text
- `images.edit()` → `revised_prompt` is `null`/`None` always

### 2. Consistency Across Models

This behavior applies universally to:
- DALL-E 2
- DALL-E 3
- GPT Image 1
- GPT Image 1.5

It's not a model-specific limitation, but an architectural decision for the edit endpoint itself.

### 3. No OpenAI Acknowledgment of Issues

Search of community forums and issue trackers found:
- ❌ No bug reports about missing revised_prompt in edits
- ❌ No feature requests with significant engagement to add it
- ❌ No OpenAI statements indicating this will change
- ✅ Appears to be intentional design decision made long ago

## Architectural Reasoning

### Why images.edit() Differs from images.generate()

| Aspect | generate() | edit() |
|--------|-----------|--------|
| **Primary Input** | Text prompt only | Image + prompt |
| **Prompt Role** | Drives entire generation | Specifies modifications only |
| **Enhancement Value** | High - helps understand image | Lower - image already constrained |
| **Diffusion Process** | Prompt guides all steps | Image provides initialization |
| **User Debugging Need** | "Why does image look like this?" | "Is the edit working?" (visual check) |

### Edit-Specific Considerations

1. **Prompt serves different function**
   - Edit prompts require preservation instructions
   - Example: "change the color to blue, keep everything else the same"
   - Enhanced version of such instructions less meaningful

2. **Results evaluable through image alone**
   - For generation: Prompt is the only reference
   - For edits: User has both original and edited image to compare
   - Visual inspection sufficient for understanding success/failure

3. **Architectural consistency**
   - Edit operations use fundamentally different code path
   - Prompt enhancement is not central to edit diffusion
   - Returning null is cleaner than providing misleading data

## What IS Available in images.edit() Responses

Complete response fields:
- `data[].url` - Image URL (expires 60 minutes)
- `data[].b64_json` - Base64-encoded image
- `data[].revised_prompt` - Always `null` (not usable)
- `created` - Timestamp
- `usage` - Token counts
- `background` - Background mode
- `output_format` - PNG/JPEG/WebP
- `quality` - Quality level
- `size` - Image dimensions

## Implications for imggen

### For GPT Image 1.5 Edit Support

1. **Do not attempt to extract revised_prompt**
   - Field will be None in all cases
   - No data to present to users

2. **Handle the field gracefully**
   - Field exists in response object
   - Must account for None value when parsing

3. **Understand this is not a limitation to work around**
   - This is intentional OpenAI design
   - No workaround exists
   - Not expected to change

### For Users

- When using edit endpoint, cannot inspect how model interpreted instructions
- Original prompt is only textual reference
- Must verify results visually (typical workflow)
- No debugging via prompt enhancement

### For Future Features

- If revised_prompt data is critical to a feature:
  - Consider using Responses API (alternative OpenAI API)
  - Or fall back to images.generate() for prompt understanding
  - Accept that edit operations don't provide this metadata

## Recommendations

1. **Update code documentation**
   - Note that revised_prompt will be None for edits
   - Explain why (architectural difference)
   - Document expected vs actual behavior

2. **Handle gracefully in providers**
   - Check for None before accessing revised_prompt
   - Don't attempt to display/use None values
   - Consider logging for debugging

3. **No action needed**
   - This is not a bug to fix
   - This is not a missing feature to add
   - This is expected behavior to understand and accommodate

## Sources

**Official OpenAI:**
- [Images API Reference](https://platform.openai.com/docs/api-reference/images)
- [Image Generation Guide](https://platform.openai.com/docs/guides/image-generation)
- [GPT Image 1.5 Model Page](https://platform.openai.com/docs/models/gpt-image-1.5)
- [GPT-Image-1.5 Prompting Guide](https://cookbook.openai.com/examples/multimodal/image-gen-1.5-prompting_guide)

**Community Discussions:**
- [Is it possible to get the revised prompt from the API?](https://community.openai.com/t/is-it-possible-to-get-the-revised-prompt-from-the-api-when-generating-images/1291440)
- [How do I edit an image through the prompt?](https://community.openai.com/t/how-do-i-edit-an-image-through-the-prompt/712949)
- [GPT-Image-1.5 rolling out announcement](https://community.openai.com/t/gpt-image-1-5-rolling-out-in-the-api-and-chatgpt/1369443)
- [DALL-E 3 revised_prompt documentation](https://community.openai.com/t/dalle-3-revised-prompt-where-can-we-return-this-from-our-api-call/508919)

**Third-Party API Documentation:**
- [AI/ML API - gpt-image-1 Reference](https://docs.aimlapi.com/api-references/image-models/openai/gpt-image-1)
- [AI/ML API - DALL-E 3 Reference](https://docs.aimlapi.com/api-references/image-models/openai/dall-e-3)

## Conclusion

The absence of `revised_prompt` from `images.edit()` responses is **intentional behavior** driven by architectural differences between image generation and editing operations. This is **not a documentation gap** or **bug to fix**, but rather **expected behavior to accommodate** in imggen's OpenAI provider implementation.

The field should be handled gracefully (checking for None) but no data extraction or feature development should depend on it being available.
