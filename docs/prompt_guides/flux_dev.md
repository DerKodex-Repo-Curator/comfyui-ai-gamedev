# FLUX.1 Dev Prompting Guide

## Model Overview
FLUX.1 Dev is an advanced text-to-image model with enhanced capabilities for detailed artistic control and creative expression. Released in 2024, it excels at complex compositions and nuanced prompting.

## Token Limit
- **Maximum tokens**: 256
- **Optimal range**: 100-200 tokens
- **Format**: Natural language with structured components

## Core Principles

### Key Elements
1. **Subject clarity**: Define main subjects with specific details
2. **Style direction**: Artistic style, medium, and technique
3. **Composition**: Layout, framing, and perspective
4. **Atmosphere**: Mood, lighting, and emotional tone
5. **Technical quality**: Resolution, detail level, and rendering

## Prompt Structure

### Essential Formula
```
[Subject + Details] + [Environment/Setting] + [Style/Medium] + [Lighting/Mood] + [Composition] + [Quality Tags]
```

### Building Blocks

#### 1. Subject Description
- **Physical attributes**: Size, color, texture, material
- **Pose/Action**: What the subject is doing
- **Expression/Emotion**: For characters and creatures
- **Distinctive features**: Unique identifying characteristics

Example:
```
A majestic phoenix with iridescent feathers transitioning from deep crimson to brilliant gold, wings spread wide in mid-flight
```

#### 2. Environment and Setting
- **Location**: Specific place or type of environment
- **Time**: Time of day, season, era
- **Weather**: Atmospheric conditions
- **Background elements**: Supporting details

Example:
```
soaring above ancient mountain peaks shrouded in morning mist, dawn light breaking through storm clouds
```

#### 3. Artistic Style
- **Medium**: Oil painting, digital art, watercolor, pencil sketch
- **Artist reference**: "in the style of" (use sparingly)
- **Art movement**: Impressionism, art nouveau, cyberpunk
- **Technique**: Brushwork, line art, cell shading

Example:
```
rendered as a luminous digital painting with particle effects and dynamic brushstrokes
```

#### 4. Lighting and Atmosphere
- **Light source**: Natural, artificial, magical
- **Light quality**: Soft, harsh, diffused, dramatic
- **Color temperature**: Warm, cool, neutral
- **Mood**: Ethereal, ominous, peaceful, energetic

Example:
```
dramatic backlighting with golden hour warmth, volumetric light rays piercing through
```

#### 5. Composition and Framing
- **Camera angle**: Eye level, low angle, bird's eye, Dutch angle
- **Shot type**: Close-up, wide shot, medium shot
- **Focus**: Shallow/deep depth of field, bokeh
- **Perspective**: One-point, two-point, isometric

Example:
```
captured from a low angle perspective emphasizing grandeur, shallow depth of field with background bokeh
```

#### 6. Quality Enhancement Tags
- **Resolution**: 4K, 8K, highly detailed, ultra-detailed
- **Rendering**: Photorealistic, hyperrealistic, stylized
- **Quality markers**: Masterpiece, best quality, award-winning
- **Technical**: Ray tracing, global illumination, subsurface scattering

Example:
```
ultra-detailed 8K resolution, photorealistic rendering with ray-traced lighting, masterpiece quality
```

## Advanced Techniques

### Weighted Prompting
Use parentheses to emphasize important elements:
```
A (majestic:1.3) dragon with (intricate scale patterns:1.2), breathing (ethereal blue flames:1.4)
```

### Negative Space Control
Explicitly describe empty areas and composition balance:
```
minimalist composition with vast empty sky occupying upper two-thirds, single tree in lower third
```

### Multi-Subject Scenes
Clearly separate and relate multiple subjects:
```
A knight in gleaming armor facing a towering dragon, separated by a narrow stone bridge over a bottomless chasm, tension visible in their poses
```

### Temporal Elements
Suggest movement and time:
```
cherry blossoms falling in slow motion, petals caught mid-drift in golden afternoon light
```

## Style Variations

### Photorealistic
```
Photorealistic portrait, natural skin texture with visible pores, catchlight in eyes, shot with 85mm lens, shallow depth of field, soft studio lighting
```

### Fantasy Art
```
Epic fantasy illustration, vibrant magical effects, dynamic action pose, rich saturated colors, detailed armor and weapons, atmospheric perspective
```

### Anime/Manga
```
Anime art style, cel shaded, clean line art, expressive eyes, dynamic hair movement, vibrant colors, studio quality animation
```

### Abstract/Surreal
```
Surrealist composition, impossible geometry, floating elements, dreamlike atmosphere, fluid transitions between forms, symbolic imagery
```

### Concept Art
```
Professional concept art, industrial design, clean presentation, multiple angles shown, technical annotations, neutral background
```

## Common Issues and Solutions

### Issue: Lack of detail
**Solution**: Add specific descriptors and "highly detailed", "intricate", "fine details"

### Issue: Wrong style interpretation
**Solution**: Be more explicit about medium and technique, add style references

### Issue: Poor composition
**Solution**: Specify exact framing, rule of thirds, focal points

### Issue: Inconsistent lighting
**Solution**: Define primary light source clearly, describe shadows and highlights

### Issue: Unwanted elements
**Solution**: Use negative prompts effectively, be specific about exclusions

## Negative Prompting for FLUX Dev

Essential negative prompt components:
```
blurry, low quality, distorted, deformed, ugly, grainy, noisy, oversaturated, underexposed, amateur, poorly drawn
```

Anatomy-specific (for characters):
```
extra limbs, missing limbs, distorted hands, incorrect proportions, asymmetrical features
```

Style-specific:
```
cartoon (when wanting realistic), photorealistic (when wanting artistic), flat colors, no depth
```

## Best Practices

### Do's
- ✅ Use natural, flowing language
- ✅ Be specific about materials and textures
- ✅ Include atmospheric elements
- ✅ Describe lighting thoroughly
- ✅ Specify camera/viewing angle

### Don'ts
- ❌ Overload with conflicting styles
- ❌ Use too many artist references
- ❌ Forget about composition
- ❌ Neglect background elements
- ❌ Skip quality tags

## Example Prompts

### Portrait
```
Professional portrait of a wise elderly woman with silver hair in an elegant bun, wearing vintage emerald jewelry, warm smile with laugh lines, soft Rembrandt lighting from window, shot with 85mm lens, shallow depth of field focusing on expressive hazel eyes, photorealistic, highly detailed skin texture, 8K resolution
```

### Landscape
```
Mystical forest at twilight, ancient twisted trees with bioluminescent mushrooms growing on bark, fireflies creating light trails, misty atmosphere with volumetric fog, moonlight filtering through canopy, fantasy art style, highly detailed vegetation, atmospheric perspective, magical realism, ultra-wide angle composition
```

### Action Scene
```
Dynamic battle scene of a samurai deflecting an arrow mid-flight, motion blur on the arrow, intense focus in warrior's eyes, cherry blossoms scattering from the force, dramatic low angle, frozen moment in time, cinematic lighting with rim light, highly detailed armor with battle wear, epic composition
```

### Product/Object
```
Futuristic holographic smartphone floating in space, transparent glass design with visible internal components, neon circuit patterns glowing softly, clean minimalist background, studio lighting with reflections, product photography style, octane render, 8K resolution, photorealistic materials
```

## Tips for Success

1. **Start with the main subject** and build outward
2. **Layer details progressively** from general to specific
3. **Balance description length** across all elements
4. **Use quality tags consistently** at the end
5. **Test variations** to find optimal phrasing
6. **Keep a prompt library** of successful combinations
7. **Study generated results** to refine technique