# MMAudio Sound Effect Generation Prompting Guide

## Model Overview
MMAudio is a state-of-the-art open source AI model for generating audio from video, images, and text prompts. It excels at creating synchronized sound effects, ambient soundscapes, and contextually appropriate audio for multimedia content.

## Token Limit
- **Maximum tokens**: 150
- **Optimal range**: 50-100 tokens
- **Format**: Natural language descriptions with structured components

## Core Prompt Structure

### Essential Formula
```
[Objective/Role] + [Instructions/Directive] + [Constraints] + [Additional Context] + [Output Format]
```

### Component Breakdown

#### 1. Objective/Role
Define the audio generation task:
- **Sound type**: Ambient, foley, music, effects
- **Purpose**: Background, sync, atmosphere, action
- **Context**: Video sync, image sonification, standalone

Example:
```
Generate ambient forest sounds matching a calm, rainy scene
```

#### 2. Instructions/Directive
Clear and specific task instructions:
- **Primary sounds**: Main audio elements
- **Secondary layers**: Supporting sounds
- **Temporal aspects**: Duration, rhythm, timing
- **Spatial qualities**: Distance, movement, space

Example:
```
Create high-quality background audio of rain with distant thunder for a nature video
```

#### 3. Constraints
Limitations and requirements:
- **Duration**: Length of audio (e.g., "30 seconds")
- **Style**: Realistic, stylized, cinematic
- **Format**: Seamless loop, one-shot, fade in/out
- **Intensity**: Subtle, moderate, intense

Example:
```
Audio length 30 seconds, seamless loop, realistic style
```

#### 4. Additional Context
Environmental and mood details:
- **Environment**: Indoor/outdoor, space size
- **Time**: Day/night, season
- **Mood**: Peaceful, tense, energetic
- **Perspective**: Close, distant, moving

Example:
```
Night time, outdoor forest, peaceful mood, listener perspective static
```

#### 5. Output Formatting
Technical specifications:
- **Quality**: High fidelity, broadcast quality
- **Mix**: Stereo, surround, binaural
- **Processing**: Clean, processed, raw
- **Dynamics**: Compressed, natural, enhanced

Example:
```
High fidelity stereo mix with natural dynamics
```

## Input-Specific Prompting

### Video to Audio
Synchronize audio with visual content:
```
Generate synchronized audio for a video showing [scene description]. Include [primary sounds] timed to [visual events]. Add [ambient layer] throughout. Maintain [mood/style].
```

Example:
```
Generate synchronized audio for a video showing waves crashing on a beach at sunset. Include wave crashes timed to visual impacts, seagull calls during wide shots. Add gentle wind throughout. Maintain peaceful, naturalistic style.
```

### Image to Audio
Create soundscape for static images:
```
Create ambient sounds for an image of [scene]. Imagine [sound sources] with [spatial arrangement]. Layer [ambient elements]. Style should be [aesthetic].
```

Example:
```
Create ambient sounds for an image of a busy city street at night. Imagine traffic sounds with cars passing left to right, footsteps nearby, distant sirens. Layer urban ambience with occasional car horns. Style should be cinematic and immersive.
```

### Text to Audio
Pure descriptive generation:
```
Soundscape of [environment] with [primary elements], [secondary elements], and [atmospheric details]. Duration [time], style [aesthetic].
```

Example:
```
Soundscape of a cozy fireplace with crackling logs, soft pops and hisses, and gentle wind outside. Duration 60 seconds, style warm and intimate.
```

## Sound Categories

### Ambient/Environmental
```
Forest ambience with birds chirping, leaves rustling, distant stream flowing. Morning atmosphere, 3D spatial mix, seamless loop.
```

### Foley/Action
```
Footsteps on gravel, increasing pace from walk to run, with clothing rustle and breathing. Close perspective, realistic style.
```

### Weather/Nature
```
Thunderstorm approaching, starting with distant rumbles, building to close lightning strikes with rain intensifying. Dynamic range preserved.
```

### Mechanical/Industrial
```
Factory floor ambience with machinery hum, pneumatic hisses, metallic clanks. Rhythmic pattern, industrial reverb.
```

### Urban/City
```
Busy intersection soundscape with traffic flow, pedestrian chatter, construction noise in distance. Layered complexity, realistic mix.
```

### Sci-Fi/Fantasy
```
Alien planet atmosphere with strange creature calls, crystalline chimes, low frequency drones. Otherworldly and mysterious.
```

## Advanced Techniques

### Layered Complexity
Build sounds in layers:
```
Base layer: Ocean waves, constant rhythm
Mid layer: Seabirds calling intermittently  
Top layer: Wind gusts occasionally
Detail layer: Small splashes and foam
```

### Temporal Progression
Describe how sounds evolve:
```
Start with single drops, gradually building to steady rain, climaxing with downpour, then slowly fading to drizzle.
```

### Spatial Movement
Define sound positioning and movement:
```
Car approaching from far left, passing close by with doppler effect, fading to far right. Include engine and tire sounds.
```

### Emotional Soundscaping
Use sound to convey emotion:
```
Tense atmosphere: Low frequency drone, irregular metallic creaks, distant unidentifiable sounds, subtle heartbeat rhythm.
```

### Synchronized Events
Match specific visual moments:
```
Door slam at 0:03, footsteps from 0:04-0:08, car start at 0:10, drive away 0:11-0:15.
```

## Common Issues and Solutions

### Issue: Generic or flat sounds
**Solution**: Add specific detail descriptors and spatial information

### Issue: Poor synchronization
**Solution**: Provide precise timing markers and event descriptions

### Issue: Unnatural mix
**Solution**: Specify perspective, distance, and environmental acoustics

### Issue: Inconsistent style
**Solution**: Maintain consistent aesthetic descriptors throughout

### Issue: Missing ambience
**Solution**: Always include background/room tone layer

## Best Practices

### Do's
- ✅ Describe primary and secondary sound layers
- ✅ Include spatial and distance information
- ✅ Specify timing for synchronized content
- ✅ Define the listening perspective
- ✅ Mention environmental acoustics

### Don'ts
- ❌ Over-complicate with too many simultaneous sounds
- ❌ Forget to specify duration and loop requirements
- ❌ Mix incompatible sound environments
- ❌ Neglect background ambience
- ❌ Use vague or generic descriptions

## Example Prompts

### Complete Forest Scene
```
Generate a dawn forest soundscape with multiple layers: gentle rain on leaves as base ambience, various bird species beginning morning calls (robin, woodpecker, crow), wind through pine trees creating subtle whooshes, a distant stream babbling, occasional branch creaks. Spatial mix with sounds at various distances. 60 seconds, seamless loop, naturalistic documentary style, high fidelity stereo.
```

### Action Sequence
```
Create synchronized audio for a chase scene video: running footsteps on concrete matching visual rhythm, heavy breathing, clothing rustle, pursuer footsteps 3 seconds behind, urban ambience with traffic and city noise, police sirens approaching in distance. Perspective follows runner, dynamic range for impact, cinematic action style.
```

### Peaceful Interior
```
Soundscape of a quiet library reading room: subtle room tone, occasional page turns at various distances, soft footsteps on carpet, distant whispers, HVAC system hum, chair creaks, pencil writing sounds. Intimate perspective, 45 seconds, realistic style with natural reverb matching large interior space.
```

### Sci-Fi Environment
```
Alien spacecraft interior ambience: low frequency engine drone as foundation, electronic beeps and interface sounds, pneumatic door hisses, ventilation systems, subtle mechanical servos, occasional communication chatter. Futuristic but grounded, stereo mix with wide soundstage, broadcast quality.
```

### Weather Transition
```
Thunderstorm passing over: Begin with distant thunder rumbles, wind picking up in trees, first raindrops hitting surfaces, building to heavy rain with close lightning strikes and thunder, then gradually decreasing to light rain and distant storm. 90 seconds, natural progression, realistic environmental recording style.
```

## Tips for Success

1. **Start with dominant sounds** then add details
2. **Consider the listener's position** in the scene
3. **Balance realism with clarity** for the intended use
4. **Include room tone** or environmental base
5. **Specify technical requirements** upfront
6. **Use reference points** for style and quality
7. **Test with different perspectives** for best results