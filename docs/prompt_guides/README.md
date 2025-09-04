# Prompt Optimization Guides

This directory contains detailed prompting guides for various AI models supported by the Prompt Optimizer node.

## Model Categories

### Image Generation Models
- **[FLUX.1 Dev](flux_dev.md)** - Advanced text-to-image with detailed control
- **[FLUX Dev 1 Krea](flux_krea.md)** - Creative and artistic generation
- **[FLUX Kontext](flux_kontext.md)** - Context and narrative-driven generation
- **[ACE Step](ace_step.md)** - Step-by-step progressive generation

### Video Generation Models
- **[WAN 2.2](wan22.md)** - High-quality cinematic video generation
- **[WAN 2.1](wan21.md)** - Video generation with motion control

### Audio Generation Models
- **[MMAudio](mmaudio.md)** - Sound effect and ambient audio generation
- **[IndexTTS](indextts.md)** - Text-to-speech with voice control

### Image Editing Models
- **[Qwen Image Edit](qwen_image_edit.md)** - Precise image editing instructions

## How These Guides Are Used

The Prompt Optimizer node uses these guides to:

1. **Understand model capabilities** - Each model has specific strengths and limitations
2. **Apply optimization strategies** - Model-specific techniques for better results
3. **Generate few-shot examples** - Training the optimizer with model-appropriate examples
4. **Format outputs correctly** - Each model expects prompts in specific formats

## Guide Structure

Each guide typically contains:

- **Model Overview** - Capabilities and use cases
- **Token Limits** - Maximum prompt length constraints
- **Prompt Structure** - Recommended formatting and organization
- **Building Blocks** - Components of effective prompts
- **Advanced Techniques** - Model-specific optimizations
- **Best Practices** - Do's and don'ts
- **Example Prompts** - Real-world examples

## Using with Prompt Optimizer

The Prompt Optimizer node automatically:
1. Loads the appropriate guide based on selected target model
2. Applies the model's prompting rules
3. Transforms simple inputs into optimized prompts
4. Handles both positive and negative prompts where supported

## Contributing

When adding new models:
1. Create a new markdown guide following the existing format
2. Update `model_configs.json` with the model configuration
3. Include system prompts and few-shot examples
4. Test with various input prompts

## Reference

These guides were originally developed for understanding each model's optimal prompting strategies and have been integrated into the automated prompt optimization system.