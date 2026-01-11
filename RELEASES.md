# Release History

## v1.0.0 - 2024-01-11

### Features
- Image generation from natural language prompts
- Multi-provider support: OpenAI (gpt-image-1.5) and Google (Gemini 3 Pro)
- Multiple reference image support with input_fidelity control (OpenAI)
- Reference images for composition guidance (Google, up to 14 images)
- Multiple image variations with parallel processing
- Cost estimation and dry-run mode
- API key management with auto-prompting
- Quality and resolution controls
- Aspect ratio support (1:1, 16:9, 9:16, 4:3, 3:4)
- File collision prevention
- Version management with update checking
- Comprehensive test suite (99 tests)

### Documentation
- Technical reference guide for providers
- User prompting guide with examples
- Feature documentation (specs/)
- Implementation principles and architecture guide

### Providers
- **OpenAI**: Multiple reference images, input_fidelity parameter ("high"/"low")
- **Google**: Up to 14 reference images (5 humans + 6 objects), explicit role assignment
