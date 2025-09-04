# Prompt Optimizer Node

## Overview

The Prompt Optimizer node uses Ollama and vision-language models to optimize prompts for various AI models. It transforms simple user prompts into detailed, model-specific prompts that maximize generation quality.

## Features

- **Multi-Model Support**: Optimizes prompts for 9+ different AI models
- **Vision Integration**: Can analyze input images to incorporate visual context
- **Positive & Negative Prompts**: Generates both where supported
- **Model-Specific Strategies**: Each model has tailored optimization rules
- **Few-Shot Learning**: Uses example prompts to guide optimization

## Supported Models

### Image Generation
- **FLUX.1 Dev** - Advanced text-to-image with detailed control
- **FLUX Dev 1 Krea** - Creative and artistic generation focus
- **FLUX Kontext** - Context and narrative-driven generation
- **ACE Step** - Step-by-step progressive generation

### Video Generation
- **WAN 2.2** - High-quality cinematic video (supports negative prompts)
- **WAN 2.1** - Video generation with motion control (supports negative prompts)

### Audio Generation
- **MMAudio** - Sound effect and ambient audio generation

### Other Models
- **Qwen Image Edit** - Precise image editing instructions
- **IndexTTS** - Text-to-speech with voice control

## Requirements

### System Requirements
- **Ollama Server**: Must be running locally or accessible via network
- **RAM**: ~8GB for model inference
- **Disk Space**: ~4-8GB per Ollama model

### Dependencies
```bash
pip install ollama>=0.1.0
pip install Pillow>=10.0.0  # For image handling
```

### Ollama Setup

1. **Install Ollama**:
```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download/windows
```

2. **Start Ollama Server**:
```bash
ollama serve  # Usually starts automatically
```

3. **Pull Recommended Model**:
```bash
ollama pull qwen2.5vl:7b  # Recommended for vision support
# Alternative models:
# ollama pull llama3.2-vision:11b  # Larger, more capable
# ollama pull llava:7b              # Lighter alternative
```

## Node Parameters

### Required Inputs
- **target_model**: Select which AI model to optimize for
- **prompt**: User's input prompt to optimize

### Optional Inputs
- **image**: Reference image for context (IMAGE type)
- **ollama_host**: Ollama server address (default: "localhost:11434")
- **ollama_model**: Which Ollama model to use (default: "qwen2.5vl:7b")

### Outputs
- **positive_prompt**: Optimized positive prompt
- **negative_prompt**: Optimized negative prompt (empty for models that don't support it)

## Usage

### Basic Text Optimization
1. Add the Prompt Optimizer node
2. Select your target model (e.g., "flux_dev")
3. Enter a simple prompt (e.g., "a dragon")
4. Connect outputs to text encoding nodes
5. Receive detailed optimized prompt

### With Image Context
1. Connect LoadImage node to the image input
2. Enter a prompt that relates to the image
3. The optimizer will analyze the image and incorporate visual elements
4. Output will include details from both prompt and image

### Example Transformations

**Input**: "a cat"
**Target**: flux_dev
**Output**: "A majestic tabby cat with emerald green eyes and silver-striped fur, sitting regally on an ornate velvet cushion in a sunlit Victorian parlor, warm afternoon light streaming through lace curtains creating dramatic shadows, rendered as a photorealistic digital painting with fine detail in the fur texture, shot from eye level with shallow depth of field emphasizing the cat's piercing gaze, ultra-detailed 8K resolution with ray-traced lighting"

**Input**: "dog running"
**Target**: wan22
**Positive Output**: "A golden retriever with flowing fur, sprinting joyfully through a sunlit meadow filled with wildflowers, slow motion tracking shot following alongside at dog's eye level, camera gradually pulling back to reveal the vast landscape, warm golden hour lighting with lens flares, shallow depth of field keeping dog in sharp focus while background softly blurs, cinematic nature documentary style, natural color grading with enhanced warm tones"
**Negative Output**: "--no motion blur --no shaky camera --no distorted proportions --no unnatural animal movement --no grainy texture --no compression artifacts --no text overlay --no watermark --no oversaturation --no lens distortion"

## Configuration

### Model Configuration File

The node uses `model_configs.json` to define optimization strategies for each model. This file contains:

- System prompts defining each model's requirements
- Few-shot examples for consistent output
- Model capabilities (e.g., negative prompt support)

### Customizing Models

To add or modify model configurations:

1. Edit `nodes/prompt_optimizer/model_configs.json`
2. Add new model entry with:
   - `name`: Display name
   - `supports_negative`: Boolean for negative prompt support
   - `positive_messages`: Chat history for positive prompts
   - `negative_messages`: Chat history for negative prompts (if supported)

Example structure:
```json
{
  "models": {
    "custom_model": {
      "name": "Custom Model",
      "supports_negative": false,
      "positive_messages": [
        {
          "role": "system",
          "content": "System prompt describing optimization rules..."
        },
        {
          "role": "user",
          "content": "example input"
        },
        {
          "role": "assistant",
          "content": "example optimized output"
        }
      ]
    }
  }
}
```

## Workflow Integration

### With Image Generation
```
[LoadImage] → [PromptOptimizer] → [CLIPTextEncode] → [KSampler] → [VAEDecode]
                      ↓
              [CLIPTextEncode] → (negative conditioning)
```

### With Video Generation
```
[PromptOptimizer] → [VideoGenerator]
         ↓
   (negative prompt for quality control)
```

## Performance Optimization

### Connection-Aware Processing
The node only processes outputs that are connected in the workflow:
- If only positive_prompt is connected, negative prompt generation is skipped
- Reduces unnecessary API calls to Ollama

### Caching
Consider implementing prompt caching for frequently used inputs to reduce latency.

### Model Selection
- **qwen2.5vl:7b**: Best balance of speed and quality
- **llama3.2-vision:11b**: Higher quality but slower
- **llava:7b**: Faster but less sophisticated

## Troubleshooting

### Common Issues

**Ollama Not Found**
```bash
# Check if Ollama is running
curl http://localhost:11434

# If not, start it
ollama serve
```

**Model Not Available**
```bash
# List available models
ollama list

# Pull required model
ollama pull qwen2.5vl:7b
```

**Empty or Original Prompt Returned**
- Check Ollama server is accessible
- Verify model is downloaded
- Check console for error messages
- Ensure prompt is not empty

**Image Not Processed**
- Verify image is properly connected
- Check image format (PNG, JPG supported)
- Ensure using vision-capable model

### Network Configuration

For remote Ollama servers:
```python
# In node settings
ollama_host: "192.168.1.100:11434"  # Replace with your server IP
```

## Best Practices

1. **Use Appropriate Models**: Select vision models when using image inputs
2. **Keep Prompts Concise**: Input prompts should be simple; let the optimizer expand them
3. **Check Model Support**: Not all models support negative prompts
4. **Monitor Performance**: Large models may be slow; consider using smaller alternatives
5. **Test Outputs**: Verify optimized prompts work well with your target model

## API Integration

The node can be extended to support other LLM APIs:

```python
# Example: Adding OpenAI support
def _optimize_with_openai(self, messages, prompt, image):
    # Implementation for OpenAI API
    pass
```

## Model Training Notes

Each model configuration uses few-shot learning with 3 examples to establish:
- Output format consistency
- Style and detail level
- Model-specific syntax (e.g., `--no` flags for WAN models)

## Future Enhancements

Planned improvements:
- Batch processing support
- Prompt history and favorites
- Custom model fine-tuning
- API key management for cloud services
- Prompt template library
- A/B testing capabilities