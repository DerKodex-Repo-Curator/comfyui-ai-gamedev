# Qwen Image Edit Prompting Guide

## Model Overview
Qwen-Image-Edit is a 20 billion parameter image editing model that excels at precise, flexible image editing with exceptional text rendering capabilities. Latest version: Qwen-Image-Edit (2025).

## Token Limit
- **Maximum tokens**: 300
- **Optimal range**: 100-200 tokens
- **Format**: Structured preservation and modification instructions

## Core Prompt Structure

### Essential Formula
```
[What to Keep] + [What to Change] + [Style/Lighting] + [Consistency Requirements]
```

### Key Principles
1. **Start with preservation**: Clearly define what should remain unchanged
2. **Specify changes precisely**: Be explicit and detailed about modifications
3. **Maintain consistency**: Preserve proportions, perspective, and identity
4. **Include style objectives**: Maintain or transform style coherently

## Prompt Components

### 1. Preservation Instructions
Always begin by listing what should NOT change:
- Facial features and identity
- Body proportions and pose
- Background elements
- Lighting conditions
- Color schemes
- Style and quality

Example:
```
Keep all facial features, eye color, body proportions, pose, outfit, lighting, and background the same.
```

### 2. Modification Instructions
Clearly describe what needs to be edited:
- **Specific changes**: Exact descriptions of modifications
- **Detailed attributes**: Colors, textures, styles
- **Positional information**: Where changes should occur
- **Extent of changes**: How much should be modified

Example:
```
Change hairstyle to twin-tails updo with pink-blonde gradient color, high on both sides, smooth and slightly curled at the ends.
```

### 3. Style and Lighting
Optionally specify style maintenance or transformation:
- Photorealistic vs. artistic
- Lighting conditions
- Rendering quality
- Artistic style

Example:
```
Preserve photorealistic style, soft natural sunlight, and cinematic Vogue-style lighting.
```

### 4. Consistency Requirements
Explicitly state what aspects need to remain consistent:
- Character identity
- Scene coherence
- Perspective and scale
- Color harmony
- Style unity

## Common Edit Types

### Hairstyle Changes
```
Keep all facial features, eye color, body proportions, pose, outfit, lighting, and background the same. Change hairstyle to [detailed description]. Preserve photorealistic style and original lighting conditions.
```

Example:
```
Keep all facial features, eye color, body proportions, pose, outfit, lighting, and background the same. Change hairstyle to a twin-tails updo with pink-blonde gradient color, high on both sides, smooth and slightly curled at the ends. Preserve photorealistic style, soft natural sunlight, and cinematic Vogue-style lighting.
```

### Outfit Changes
```
Keep all facial features, body proportions, pose, hairstyle, background, eye color, and lighting the same. Change the outfit to [detailed description]. Maintain [style] detail and [lighting type].
```

Example:
```
Keep all facial features, body proportions, pose, hairstyle, background, eye color, and lighting the same. Change the outfit to a modern edgy schoolgirl style with a cropped blouse, black pleated mini skirt, and thigh-high stockings in dark tones. Maintain photorealistic detail and cinematic lighting.
```

### Text Modification
```
Change the [location] text to '[new text]'. Retain the font, color, and perspective. Do not modify the [other elements].
```

Example:
```
Change the sign text to 'GRAND OPENING'. Retain the font, color, and perspective. Do not modify the background or sign structure.
```

### Object Removal
```
Remove [specific objects/elements]. Keep [everything else]. Maintain [scene coherence].
```

Example:
```
Remove all UI text elements from the image. Keep the feeling that the characters and scene are in water. Also, remove the green UI elements at the bottom.
```

### Expression Changes
```
Keep all facial features, hairstyle, body position, clothing, and background identical. Change facial expression to [emotion/expression]. Maintain original lighting and skin texture.
```

Example:
```
Keep all facial features, hairstyle, body position, clothing, and background identical. Change facial expression to a warm, genuine smile with slightly raised eyebrows showing happiness. Maintain original lighting and skin texture.
```

### Background Replacement
```
Keep the [subject] exactly the same including [list specifics]. Replace background with [new background description]. Maintain original lighting on subject.
```

Example:
```
Keep the person exactly the same including pose, outfit, hairstyle, and facial features. Replace background with a modern office interior with glass walls and city view. Maintain original lighting on subject.
```

## Best Practices

### Do's
- ✅ List preservation requirements first
- ✅ Be extremely specific about changes
- ✅ Include style and quality maintenance
- ✅ Specify exact colors and textures
- ✅ Maintain scene coherence instructions

### Don'ts
- ❌ Use vague descriptions
- ❌ Forget to specify what to keep
- ❌ Mix conflicting style requirements
- ❌ Overlook lighting consistency
- ❌ Neglect identity preservation

## Advanced Techniques

### Multi-Element Edit
```
Keep facial features, body proportions, and pose unchanged. Change: 1) Hairstyle to shoulder-length wavy blonde, 2) Outfit to business suit in navy blue, 3) Background to modern office. Maintain photorealistic quality, original lighting direction, and color harmony.
```

### Style Transfer with Preservation
```
Keep all structural elements, composition, and subject positions the same. Transform entire image to oil painting style with visible brushstrokes and impressionist color palette. Preserve original scene layout and proportions.
```

### Complex Identity Preservation
```
Keep the person's exact facial structure, eye shape and color, nose shape, mouth shape, facial proportions, age appearance, and skin tone identical. Change only the hairstyle and clothing while maintaining their unique identity markers and expression.
```

## Common Issues and Solutions

### Issue: Loss of facial identity
**Solution**: Explicitly list all facial features to preserve: "exact facial structure, eye shape, nose, mouth, facial proportions"

### Issue: Inconsistent lighting
**Solution**: Add "Maintain original lighting direction, intensity, and color temperature"

### Issue: Style degradation
**Solution**: Include "Preserve original image quality and style consistency"

### Issue: Unintended changes
**Solution**: Be more explicit about every element that should remain unchanged

## Prompt Templates

### Standard Edit Template
```
Keep [list all unchanged elements]. Change [specific modification]. Preserve [style/quality attributes]. Maintain [consistency requirements].
```

### Character Modification Template
```
Keep all facial features, body proportions, pose, and background the same. Change [specific element] to [detailed description]. Preserve [style type] style, [lighting type] lighting, and [quality level] quality.
```

### Scene Edit Template
```
Keep [subject details] exactly the same. Modify [environment/background] to [new description]. Maintain [lighting consistency], [perspective], and [style coherence].
```

## Tips for Success

1. **Preservation First**: Always start with what shouldn't change
2. **Specific Details**: Use exact descriptions, not general terms
3. **Coherence Focus**: Emphasize maintaining scene and style coherence
4. **Identity Protection**: Be explicit about preserving character identity
5. **Quality Maintenance**: Include quality preservation in every prompt

## Integration Notes

- Supports prompt rewriting/polishing for improved stability
- Multi-language support available
- Compatible with ComfyUI and Qwen pipeline
- Can be used via Python API or UI workflows
- Continuous improvements in 2025 versions