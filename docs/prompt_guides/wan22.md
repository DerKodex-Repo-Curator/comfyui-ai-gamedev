# WAN 2.2 Video Generation Prompting Guide

## Model Overview
WAN 2.2 (WanVideo 2.2) is an advanced AI video generation model that creates high-quality, cinematic videos from structured text prompts with enhanced control over content, motion, and style.

## Token Limit
- **Maximum tokens**: 250
- **Optimal range**: 150-200 tokens
- **Format**: Structured descriptions with cinematic terminology

## Prompt Structure Formulas

### Basic Formula
```
Subject + Scene + Movement
```
Focuses on core video elements simply:
- **Subject**: Main focus (person, creature, object, or entity)
- **Scene**: Environment including background/foreground
- **Movement**: Motion within the scene

Example:
```
A golden retriever running through a sunflower field, handheld camera, bright summer sunlight
```

### Advanced Formula
```
Subject (with Description) + Scene (with Description) + Movement + Aesthetic Control + Stylization
```
Adds rich detail about:
- Appearance attributes
- Environment specifics
- Motion characteristics
- Lighting and camera work
- Visual style and mood
- Negative prompts for exclusions

Example:
```
An astronaut floating inside a space station, zero-gravity movement, POV camera, ultra-realistic textures, cinematic lighting, dramatic shadows -no lens flare, -no text overlay
```

## Core Components

### 1. Subject Description
- **Physical attributes**: Size, color, texture, materials
- **Character details**: Clothing, expressions, pose
- **Object properties**: Shape, surface, condition
- **Fantasy elements**: Magical, surreal, or imaginative features

Examples:
- "A young woman in a red dress"
- "An ancient stone golem with moss-covered joints"
- "A chrome-plated robot with blue LED eyes"

### 2. Scene Description
- **Environment type**: Indoor/outdoor, real/fictional
- **Atmospheric conditions**: Weather, time of day, season
- **Background elements**: Architecture, nature, objects
- **Spatial relationships**: Foreground, midground, background

Examples:
- "bustling neon-lit city street at night"
- "dense tropical jungle with morning mist"
- "abandoned spaceship interior with flickering lights"

### 3. Movement Description
- **Motion type**: Walking, floating, transforming
- **Speed**: Slow motion, real-time, time-lapse
- **Direction**: Linear, circular, chaotic
- **Amplitude**: Subtle, moderate, dramatic

Examples:
- "slow motion tracking shot"
- "rapid orbital camera movement"
- "gentle swaying in the breeze"

### 4. Aesthetic Control
- **Lighting**: Natural, artificial, dramatic, soft
- **Color grading**: Warm, cool, desaturated, vibrant
- **Mood**: Mysterious, energetic, melancholic, triumphant
- **Technical specs**: Resolution, frame rate, aspect ratio

Examples:
- "cinematic lighting with dramatic shadows"
- "soft bokeh, shallow depth of field"
- "moody atmosphere with rim lighting"

### 5. Stylization
- **Visual style**: Realistic, animated, painterly, noir
- **Genre**: Cyberpunk, fantasy, documentary, horror
- **Artistic reference**: Specific film styles or directors
- **Technical style**: HDR, vintage film, digital art

Examples:
- "ultra-realistic textures"
- "Studio Ghibli animation style"
- "noir aesthetic with high contrast"

## Camera Movements

### Essential Camera Commands
- **Camera Push**: Moves closer to reveal subject details
- **Camera Pull**: Pulls back to reveal environment
- **Camera Pan**: Horizontal movement left or right
- **Camera Tilt**: Vertical movement up or down
- **Tracking Shot**: Follows subject movement
- **Orbital Shot**: Circles around the subject
- **Crane Shot**: Vertical movement with perspective change
- **Dolly Zoom**: Simultaneous zoom and movement

### Camera Movement Examples
```
"The camera pushes in for a close-up of his excited expression"
"Camera pulls back to reveal the vast landscape"
"Slow tracking shot following the character"
"Camera orbits around the dancing figure"
```

## Negative Prompts

Use `-no` format to exclude unwanted elements:
- `-no text overlay` - Prevents text in video
- `-no distorted faces` - Ensures facial clarity
- `-no lens flare` - Removes lens artifacts
- `-no grainy textures` - Maintains clean quality
- `-no shaky camera` - Ensures smooth movement
- `-no watermark` - Prevents branding
- `-no blur` - Maintains sharpness
- `-no artifacts` - Reduces generation errors

## Complete Prompt Examples

### Cinematic Drama
```
A young woman in a red dress, standing in the rain, holding a glowing umbrella, in a bustling neon-lit city street at night, slow motion tracking shot, camera pans from left to right, cinematic lighting, shallow depth of field, soft bokeh, moody atmosphere -no text overlay, -no distorted faces, -no grainy textures
```

### Action Sequence
```
A samurai warrior in traditional armor, leaping through cherry blossoms, sword drawn mid-strike, in ancient Japanese temple courtyard, dynamic camera movement following the action, golden hour lighting, high-speed capture, epic cinematic style -no motion blur, -no shaky camera
```

### Sci-Fi Exploration
```
In the depths of a dense tropical jungle, an explorer in futuristic gear kneels brushing dirt from ancient alien fragments. The camera pushes in for a close-up of his excited expression, bioluminescent plants glowing softly, mysterious atmosphere, volumetric fog -no lens artifacts
```

### Fantasy Magic
```
A wizard casting a spell, magical energy swirling around hands, in a candlelit stone chamber, camera orbits slowly, particles floating in air, warm firelight with cool magical glow contrast, mystical atmosphere, fantasy film style -no modern elements
```

### Nature Documentary
```
A snow leopard stalking through Himalayan peaks, cautious movements, tracking shot at eye level, pristine mountain landscape, early morning light, documentary style, ultra-realistic fur textures, natural color grading -no artificial effects
```

## Best Practices

### Do's
- ✅ Start with clear subject identification
- ✅ Build scene description progressively
- ✅ Specify exact camera movements
- ✅ Include lighting and atmosphere details
- ✅ Use cinematic terminology
- ✅ Add negative prompts for quality control

### Don'ts
- ❌ Avoid contradictory descriptions
- ❌ Don't overload with too many elements
- ❌ Avoid vague or ambiguous terms
- ❌ Don't mix incompatible styles
- ❌ Avoid excessive camera movements

## Advanced Techniques

### Multi-Stage Sequences
```
[Opening] Wide establishing shot of cityscape at dusk
[Transition] Camera pushes through window
[Focus] Close-up on character's determined expression
[Action] Pull back as character stands and walks toward camera
```

### Emotional Progression
```
Start: Melancholic mood with desaturated colors
Middle: Building tension with increasing contrast
End: Triumphant resolution with warm golden light
```

### Environmental Storytelling
```
Abandoned classroom, dust particles in shaft of light, camera slowly pans across empty desks, stops on single flower growing through cracked floor, metaphorical rebirth theme
```

## Technical Specifications

### Quality Modifiers
- `ultra-realistic textures`
- `8K resolution`
- `60fps smooth motion`
- `HDR color range`
- `photorealistic rendering`

### Artistic Modifiers
- `cinematic color grading`
- `film grain texture`
- `anamorphic lens flares`
- `vintage film look`
- `digital art style`

## Common Issues and Solutions

### Issue: Inconsistent Subject Appearance
**Solution**: Provide detailed, specific subject descriptions early in prompt

### Issue: Jerky or Unnatural Motion
**Solution**: Specify motion type clearly (slow motion, smooth tracking, etc.)

### Issue: Poor Scene Composition
**Solution**: Define spatial relationships and use camera framing terms

### Issue: Unwanted Artifacts
**Solution**: Use comprehensive negative prompts

## Tips for Optimization

1. **Hierarchical Description**: Start broad, then add specific details
2. **Motion Clarity**: Be explicit about movement speed and direction
3. **Camera Purpose**: Every camera move should serve the narrative
4. **Lighting Consistency**: Maintain coherent lighting throughout
5. **Style Unity**: Keep visual style consistent across all elements
6. **Negative Precision**: Target specific unwanted elements with -no flags

## Prompt Template

### Standard Template
```
[Subject with attributes], [action/pose], in [scene description], [camera movement], [lighting setup], [visual style], [mood/atmosphere] -no [unwanted element 1], -no [unwanted element 2]
```

### Example Using Template
```
A robotic dancer with chrome limbs, performing fluid movements, in abandoned theater with red velvet seats, camera orbits dynamically, dramatic spotlight with dust particles, art deco style, nostalgic yet futuristic mood -no motion blur, -no lens distortion
```