# imggen Features

End-user facing feature documentation with CLI examples.

## Core Features

### Image Generation from Text Prompts

Generate images directly from natural language descriptions.

**CLI Examples:**
```bash
# Simple prompt
imggen -p "a serene landscape at sunset"

# Prompt from file
imggen -f prompt.txt
```

### Multiple Image Variations

Generate multiple versions of the same prompt to explore different interpretations.

**CLI Examples:**
```bash
# Generate 4 variations
imggen -p "abstract art" --variations 4

# Generate 2 variations to custom output directory
imggen -p "modern architecture" --variations 2 --output ./my_images/
```

Variations are generated in parallel (up to 4 workers) for faster execution.

### Reference Image Support

Provide reference images to guide image generation. Each provider supports different reference image capabilities:

**OpenAI (gpt-image-1.5)** - Multiple reference images with identity control:
- Use `--input-fidelity high` to preserve facial details and identity
- Use `--input-fidelity low` to allow artistic reinterpretation
- Supports multiple reference images for blending styles, poses, and compositions
- Best for: pose control, style transfer, multi-element composition, background changes

**Google (gemini-3-pro-image-preview)** - Multiple reference images for complex compositions:
- Supports up to 14 reference images (5 humans + 6 objects)
- Use explicit role assignment in prompt: "Person 1 (first image): ...", "Person 2 (second image): ..."
- Best for: multi-person scenes, group compositions, product styling variations

**CLI Examples:**

OpenAI with identity preservation:
```bash
# Pose control with identity preservation
imggen -p "change pose to sitting, preserve facial features" portrait.jpg --input-fidelity high

# Style transfer with artistic freedom
imggen -p "reimagine in oil painting style" portrait.jpg --input-fidelity low

# Background change while keeping subject
imggen -p "same person at beach instead of office" office_photo.jpg --input-fidelity high

# Multiple references: blend styles and elements
imggen -p "Combine pose from first image, style from second, environment from third" pose.jpg style.jpg background.jpg --input-fidelity high
```

Google with multiple references:
```bash
# Single reference image
imggen -p "person sitting in cafe, warm lighting" person.jpg --model gemini-3-pro-image-preview

# Multiple references with explicit role assignment
imggen -p "
Person 1 (first image): standing on left, confident pose.
Person 2 (second image): sitting on right, relaxed pose.
Scene: modern office, natural lighting, both smiling." \
  person1.jpg person2.jpg --model gemini-3-pro-image-preview

# Reference images from file (one path per line)
imggen -f prompt.txt -r references.txt

# Multiple variations from references
imggen -p "blend these styles creatively" ref1.jpg ref2.jpg --variations 4 --model gemini-3-pro-image-preview
```

**For detailed prompting guidance, see:** `docs/prompting-with-references.md`
**For technical details, see:** `docs/reference-images-technical-guide.md`

### Quality and Resolution Options

Fine-tune output quality for your use case.

**OpenAI Quality Levels:**
- `low` - Faster, lower cost (default)
- `medium` - Balanced
- `high` - Best quality, higher cost

**Google Resolution Options:**
- `1K` - Standard (default)
- `2K` - High quality
- `4K` - Maximum quality

**CLI Examples:**
```bash
# OpenAI with high quality
imggen -p "professional portrait" --quality high

# Google with 4K resolution
imggen -p "landscape" --model gemini-3-pro-image-preview --resolution 4K

# Custom aspect ratio with quality
imggen -p "banner design" --aspect-ratio 16:9 --quality medium
```

### Aspect Ratio Control

Specify output image dimensions for different use cases.

**Available Ratios:**
- `1:1` - Square (default)
- `16:9` - Widescreen
- `9:16` - Portrait/vertical
- `4:3` - Standard
- `3:4` - Tall

**CLI Examples:**
```bash
# Widescreen format
imggen -p "landscape" --aspect-ratio 16:9

# Square images (default)
imggen -p "profile picture" --aspect-ratio 1:1

# Portrait format with 4 variations
imggen -p "book cover" --aspect-ratio 9:16 --variations 4
```

### Multiple AI Providers

Choose between leading AI providers by selecting a model:
- **OpenAI** (default) - Model: `gpt-image-1.5`
- **Google Gemini** - Model: `gemini-3-pro-image-preview`

Each provider offers different capabilities, pricing, and quality characteristics.

**CLI Examples:**
```bash
# Use OpenAI (default)
imggen -p "modern design"

# Select Google model
imggen -p "creative art" --model gemini-3-pro-image-preview

# Select OpenAI model explicitly
imggen -p "photo-realistic" --model gpt-image-1.5
```

## Utility Features

### Available Models

List available image generation models and select one for generation.

**CLI Examples:**
```bash
# List all available models
imggen list-models

# Generate using a specific model
imggen -p "landscape" --model gpt-image-1.5
imggen -p "portrait" --model gemini-3-pro-image-preview
```

**Available Models:**
- `gpt-image-1.5`
- `gemini-3-pro-image-preview`

### Cost Estimation (Dry-run)

Preview the estimated cost before generating images without making API calls.

**CLI Examples:**
```bash
# Estimate cost for 4 variations
imggen -p "test prompt" --variations 4 --dry-run

# Estimate cost with high quality
imggen -p "landscape" --quality high --variations 2 --dry-run
```

Output shows prompt, settings, and estimated cost. Run without `--dry-run` to actually generate.

### API Key Management

Interactive setup wizard for configuring API keys for supported providers.

**CLI Examples:**
```bash
# First-time setup
imggen setup

# Setup will prompt for:
# - Google Gemini API key (optional)
# - OpenAI API key (optional)
# - Default provider selection
```

API keys are securely stored in `~/.config/imggen/config.json`.

### Version Management

Check for updates and upgrade to the latest version.

**CLI Examples:**
```bash
# Show current version
imggen --version
imggen -v

# Check for available updates
imggen check-update

# Update to latest version
imggen update
```

### Custom Output Filenames

Specify custom filenames for generated images instead of just directories.

**Behavior:**
| Command | Result |
|---------|--------|
| `--output ./images/` | `imggen_001.png`, `imggen_002.png` (default naming) |
| `--output sunset.png` | `sunset.png` (single image) |
| `--output sunset.png -n 4` | `sunset_1.png`, `sunset_2.png`, `sunset_3.png`, `sunset_4.png` |
| `--output ./images/sunset.png -n 2` | `./images/sunset_1.png`, `./images/sunset_2.png` |

**Detection logic:**
- File extension present (`.png`, `.jpg`, `.jpeg`) → filename mode
- No extension or trailing slash → directory mode (default naming)

**CLI Examples:**
```bash
# Custom filename for single image
imggen -p "mountain sunset" --output sunset.png

# Custom filename with multiple variations
imggen -p "abstract art" --output art.png --variations 4

# Custom filename in subdirectory
imggen -p "product photo" --output ./renders/product.png -n 2
```

### File Collision Prevention

Prevents accidental overwriting of existing images before API calls are made, saving cost.

By default, generated files are named `imggen_001.png`, `imggen_002.png`, etc. Custom filenames follow the same collision protection.

**Behavior:**
- Pre-flight check detects colliding files before generation
- Clear error message with instructions (delete files or use different directory)
- No API calls made when collision detected (zero cost)

**Example:**
```bash
# If imggen_001.png exists in current directory:
$ imggen -p "landscape"
Error: File collision detected
The following files already exist in .:
  - imggen_001.png

Please:
  1. Delete or rename these files, OR
  2. Use a different --output directory

No API calls were made (no charges incurred).
```

## Advanced Usage

### Combining Features

**Example: Create 4 high-quality portrait variations with custom style:**
```bash
imggen -f description.txt \
  reference_style.jpg \
  --model gpt-image-1.5 \
  --quality high \
  --aspect-ratio 9:16 \
  --variations 4 \
  --output ./portraits/
```

**Example: Generate with Google using dry-run:**
```bash
imggen -p "abstract painting" \
  --model gemini-3-pro-image-preview \
  --resolution 4K \
  --variations 3 \
  --dry-run
```
