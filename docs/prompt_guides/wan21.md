# WAN 2.1 Video Generation Prompting Guide

## Model Overview
WAN 2.1 is a powerful AI model for generating short video clips from text prompts or images, with strong motion understanding and temporal consistency.

## Token Limit
- **Maximum tokens**: 200
- **Optimal range**: 100-150 tokens
- **Format**: Structured natural language with clear scene progression

## Core Prompt Structure

### Recommended Formula
```
[Subject & Scene Setup] + [Action & Motion] + [Camera Movement] + [Style & Atmosphere]
```

### Basic Formula
**Subject + Scene + Motion**  
Example: "A dog skateboarding in a colorful park with children playing nearby."

### Detailed Formula
**Subject (description) + Scene (description) + Action (description) + Camera Movement + Atmosphere + Style + Lighting + Shot Size**  
Example: "A futuristic city with neon lights + flying cars soaring through sunset skies + camera zooms in on a hovering billboard + moody cyberpunk atmosphere + vibrant colors + dusk lighting + wide shot."

## Key Elements

### 1. Subject & Scene Setup
Define who or what is in the video and where the scene takes place.
- Clear subject identification
- Environmental context
- Initial positioning
- Scene composition

### 2. Action & Motion
Specify what movement or activity occurs.
- Primary subject actions
- Secondary motions
- Environmental dynamics
- Temporal progression

### 3. Camera Movement
Include specific camera instructions:
- **Pan movements**: "camera pans left/right"
- **Tracking**: "tracking shot", "camera follows"
- **Zoom**: "zoom in/out", "push in", "pull back"
- **Orbit**: "camera orbits around"
- **Static**: "fixed camera", "locked shot"

### 4. Style & Atmosphere
Describe visual style and mood:
- **Lighting**: "cinematic lighting", "golden hour", "neon glow"
- **Mood**: "mysterious", "energetic", "peaceful"
- **Style**: "realistic", "animated", "cinematic", "documentary"
- **Color palette**: "vibrant colors", "muted tones", "high contrast"

## Motion & Camera Keywords

### Subject Motions
- **Basic**: walking, running, jumping, sitting, standing
- **Dynamic**: flying, dancing, rotating, spinning, flipping
- **Complex**: transforming, morphing, dissolving, materializing
- **Natural**: flowing, swaying, rippling, waving

### Camera Movements
- **Pan/Tilt**: pan left/right, tilt up/down
- **Zoom**: zoom in/out, crash zoom, dolly zoom
- **Tracking**: tracking shot, follow shot, parallel tracking
- **Orbital**: orbit around, 360 degree rotation
- **Complex**: crane shot, steadicam, handheld shake

### Shot Types
- **Distance**: close-up, medium shot, wide shot, extreme wide
- **Angle**: low angle, high angle, dutch angle, eye level
- **Perspective**: first-person view, bird's eye view, worm's eye view
- **Special**: drone shot, underwater shot, through-object shot

## Best Practices

### Do's
- ✅ Use **one scene per clip** to maintain focus
- ✅ Specify clear motion trajectories
- ✅ Include camera movement for dynamism
- ✅ Add atmospheric details for richness
- ✅ Be specific about timing ("slowly", "quickly", "gradually")

### Don'ts
- ❌ Avoid multiple unrelated scenes in one prompt
- ❌ Don't use contradictory motion descriptions
- ❌ Avoid overly complex camera movements
- ❌ Don't ignore physics unless intentionally stylized

## Negative Prompts
Use negative prompts to avoid unwanted artifacts:
```
-no blur, -no text, -no watermark, -no distortion, -no glitches, -no artifacts
```

## Example Prompts

### Fantasy Scene
```
A young mage in a forest clearing creates a glowing orb of energy, camera slowly orbits around her, magical sparkles float in the air, twilight lighting, mystical atmosphere, soft purple and blue color palette
```

### Sci-Fi Sequence
```
Close-up of an astronaut's face inside a spaceship, camera pulls back to reveal the star-filled galaxy outside, cool blue lighting, cinematic style, lens flares from distant stars, slow dramatic reveal
```

### Nature Documentary
```
A red fox running through snowy woods, camera follows at eye level, soft morning light filtering through the branches, naturalistic style, shallow depth of field, smooth tracking shot
```

### Urban Action
```
A parkour athlete leaps between rooftops in a neon-lit city, camera tracks alongside, cyberpunk atmosphere, rain-slicked surfaces reflecting lights, dynamic motion blur, high energy movement
```

### Artistic Abstract
```
Colorful paint drops falling into water, camera slowly pushes in, macro lens perspective, swirling patterns forming, high-speed capture effect, vibrant color explosions, mesmerizing fluid dynamics
```

## Advanced Techniques

### Temporal Progression
```
Start: Wide shot of empty beach at sunrise
Then: Waves gradually increase in size
Finally: Camera pulls back as storm clouds gather
```

### Multi-Stage Actions
```
A butterfly emerges from cocoon (2 seconds), spreads wings slowly (3 seconds), takes flight as camera follows upward (3 seconds)
```

### Environmental Storytelling
```
Abandoned spaceship corridor, lights flickering on sequentially, camera slowly advances forward, dust particles floating in light beams, eerie atmosphere building
```

## Common Issues and Solutions

### Issue: Static or Boring Videos
**Solution**: Always include specific camera movements and multiple layers of motion

### Issue: Inconsistent Motion
**Solution**: Use clear temporal markers like "then", "gradually", "simultaneously"

### Issue: Unclear Subject Focus
**Solution**: Start with clear subject identification before adding scene details

### Issue: Jarring Transitions
**Solution**: Use smooth camera movements and gradual changes

## Prompt Templates

### Action Sequence
```
[Character] in [location], [primary action], camera [movement type], [lighting condition], [style descriptor]
```

### Scenic Reveal
```
Start with [close detail], camera [pulls back/rises] to reveal [wider scene], [atmosphere], [time of day] lighting
```

### Transformation Scene
```
[Subject] [initial state], gradually [transformation action], camera [movement], [visual effects], [mood]
```

## Tips for Quality

1. **Clear Scene Setup**: Establish the scene before describing motion
2. **Logical Motion Flow**: Ensure actions follow natural progression
3. **Camera Purpose**: Every camera movement should enhance the story
4. **Atmospheric Details**: Add particles, lighting effects, weather
5. **Style Consistency**: Maintain consistent visual style throughout

## Resolution and Length Specifications
If your interface supports it:
- Specify video length: "5-second clip", "10-second sequence"
- Set resolution: "4K quality", "1080p", "vertical format"
- Frame rate: "smooth 60fps", "cinematic 24fps"