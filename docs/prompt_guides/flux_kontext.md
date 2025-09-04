# FLUX Kontext 1 Image Editing Prompting Guide

## Model Overview
FLUX Kontext 1 is a precise image editing model that excels at controlled modifications while maintaining specified elements unchanged. It requires clear, structured prompts for accurate edits.

## Token Limit
- **Maximum tokens**: 512
- **Optimal range**: 50-150 tokens
- **Format**: Precise English descriptions with explicit preservation requirements

## Core Principles

### Key Rules
- Use **precise and specific descriptions** instead of vague terms
- Clearly specify colors, styles, actions, and details
- Avoid subjective terms like "make it look better"
- Explicitly state which elements should remain unchanged
- Break complex edits into **step-by-step prompts**
- All prompts must be in **English**
- Focus on one primary change per prompt

## Prompt Structure Templates

### Basic Object Modification
```
Change the [specific object]'s [attribute] to [specific value]
```
Example:
```
Change the car color to bright cherry red.
```

### Style Transfer
```
Convert to [specific style] while maintaining [elements to preserve]
```
Example:
```
Convert to pencil sketch with natural graphite lines, cross-hatching, and visible paper texture while maintaining the original composition.
```

### Background/Environment Change
```
Change the background to [new environment] while keeping the [subject] in the exact same position, scale, and pose. Maintain identical subject placement, camera angle, framing, and perspective.
```
Example:
```
Change the background to a snowy mountain landscape while keeping the person in the exact same position, scale, and pose. Maintain identical subject placement, camera angle, framing, and perspective.
```

### Character Consistency
```
[Change description] while preserving [character]'s exact facial features, [specific characteristics], and other identity markers.
```
Example:
```
Change hairstyle to short and curly while preserving the person's exact facial features, eye color, skin tone, and other identity markers.
```

### Text Editing
```
Replace '[original text]' with '[new text]'
```
Example:
```
Replace 'Hello' with 'Welcome' on the sign.
```

## Advanced Prompt Composition

### Formula
```
[Main Modification] + [Preservation Requirements] + [Detail Description]
```

### Examples
```
Change the background to a forest scene while keeping the person in exactly the same position and pose, maintaining the original lighting.
```

```
Transform to watercolor painting style while maintaining the original composition and all object positions, using soft color transitions.
```

```
Change the car to red and the sky to sunset colors while keeping the road and buildings in their original appearance.
```

## Prompt Priority Guide

| Priority | Content Type | Example |
|----------|-------------|---------|
| Highest | Keep Character Identity | "While maintaining the exact same facial features." |
| High | Main Modification Target | "Change the background to beach." |
| Medium | Style and Texture | "Using watercolor painting style." |
| Low | Detail Supplement | "Add soft lighting effects." |

## Best Practices

### Do's
- ✅ Specify exact colors (e.g., "bright cherry red" not "reddish")
- ✅ List all elements to preserve explicitly
- ✅ Use step-by-step prompts for complex edits
- ✅ Include position and scale preservation
- ✅ State camera angle and perspective maintenance

### Don'ts
- ❌ Use vague terms like "better" or "nice"
- ❌ Combine multiple major changes in one prompt
- ❌ Forget to specify what should remain unchanged
- ❌ Use subjective or ambiguous descriptions
- ❌ Mix conflicting style requirements

## Common Edit Types

### Color Changes
```
Change the [object] color to [specific color name]
```
Examples:
- "Change the car color to metallic silver."
- "Change the dress color to deep emerald green."
- "Change the sky to sunset orange and pink gradients."

### Style Transfers
```
Convert to [style] while preserving [composition/layout/positions]
```
Examples:
- "Convert to oil painting style while preserving the original layout."
- "Transform to anime art style while maintaining all character positions."
- "Apply impressionist painting style while keeping the original composition."

### Background Replacements
```
Change background to [new scene] while keeping [subject details] exactly the same
```
Examples:
- "Change background to tropical beach while keeping the subject's pose identical."
- "Replace background with office interior while maintaining subject scale and position."
- "Change to night cityscape background while preserving original subject lighting."

### Object Addition/Removal
```
Add/Remove [object] while maintaining [rest of scene]
```
Examples:
- "Add a red balloon to the child's hand while keeping everything else unchanged."
- "Remove the car from the street while maintaining the road and buildings."
- "Add sunglasses to the person while preserving all facial features."

### Clothing/Outfit Changes
```
Change [clothing item] to [new description] while keeping [body/pose/features]
```
Examples:
- "Change shirt to blue business suit while keeping the same pose and body proportions."
- "Replace casual clothes with formal evening wear while maintaining the person's identity."
- "Change to winter coat and scarf while preserving facial features and pose."

## Complex Edit Examples

### Multi-Step Edit
```
Step 1: Change the car color to red while keeping everything else the same.
Step 2: Change the background to sunset while maintaining the red car.
Step 3: Add reflections on the car surface while preserving all other elements.
```

### Detailed Character Edit
```
Change hairstyle to shoulder-length wavy blonde hair with subtle highlights while preserving the exact facial features, eye color, makeup, expression, head angle, body position, clothing, and background. Maintain the original lighting direction and intensity.
```

### Scene Transformation
```
Convert the entire scene to winter setting with snow on ground and rooftops, frost on windows, and bare trees, while maintaining all building structures, positions, perspectives, and the original composition. Keep the same time of day and lighting angle.
```

## Troubleshooting

### Issue: Unintended changes to preserved elements
**Solution**: Be more explicit about what to keep, listing each element specifically

### Issue: Incomplete or partial edits
**Solution**: Break down into smaller, focused prompts

### Issue: Loss of detail or quality
**Solution**: Specify "maintaining original detail level" or "preserving image quality"

### Issue: Style inconsistency
**Solution**: Include style preservation in every step of multi-step edits

## Tips for Success

1. **Start Simple**: Begin with single-element changes before attempting complex edits
2. **Be Explicit**: Over-specify rather than under-specify preservation requirements
3. **Use Exact Terms**: Replace general words with specific descriptions
4. **Test Incrementally**: For complex edits, test each step before proceeding
5. **Document Changes**: Keep track of successful prompt formulations for reuse

## Common Pitfalls to Avoid

- Using relative terms ("bigger", "smaller") without reference points
- Forgetting to specify lighting preservation
- Mixing multiple style changes in one prompt
- Using ambiguous color descriptions
- Neglecting to maintain perspective and scale