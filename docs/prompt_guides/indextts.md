# IndexTTS 1.5 Text-to-Speech Prompting Guide

## Model Overview
IndexTTS 1.5 is a state-of-the-art autoregressive zero-shot text-to-speech (TTS) model that excels in emotional expressiveness and precise speech duration control. **Important: IndexTTS requires reference audio for voice cloning - it cannot generate voices from text descriptions alone.** It supports voice cloning from audio samples with natural language emotional control.

## Token Limit
- **Text input**: 500 tokens
- **Emotion description**: 50 tokens
- **Duration control**: Explicit token count or free generation
- **Format**: Multi-modal (text + audio references + descriptions)

## Core Prompt Structure

### Input Components
1. **Text Input**: The content to synthesize
2. **Voice Reference** (REQUIRED): Audio sample for speaker identity cloning
3. **Style/Emotion Prompt**: Natural language description for emotional control
4. **Duration Control**: Optional token count for timing precision

### Generation Workflow
```
Text + Timbre + Emotion + Duration → Semantic Tokens → Mel-spectrograms → Audio
```

## Prompt Modes

### 1. Free Duration Mode
Let the model generate naturally:
```
Text: "Welcome to our presentation."
Voice: [speaker_reference.wav] (REQUIRED)
Emotion: "professional and confident"
Duration: auto
```

### 2. Explicit Duration Mode
Control exact timing for synchronization:
```
Text: "This is perfectly synchronized."
Voice: [speaker_reference.wav] (REQUIRED)
Emotion: "neutral"
Duration: 150 tokens (for 3-second output)
```

### 3. Emotional Control
Apply different emotions to the cloned voice:
```
Text: "I have important news to share."
Voice: [speaker_reference.wav] (REQUIRED)
Emotion: "speak with enthusiasm and energy"
Duration: auto
```

## Emotion Control

### Natural Language Descriptions
Use intuitive emotion prompts to control the cloned voice's expression:

#### Professional Tones
- "speak professionally with authority"
- "deliver with confidence and clarity"
- "present in a formal business tone"
- "explain patiently and clearly"

#### Emotional Expressions
- "express genuine happiness and joy"
- "convey deep sadness and melancholy"
- "show frustration and annoyance"
- "demonstrate surprise and amazement"

#### Conversational Styles
- "speak casually like talking to a friend"
- "whisper secretively and mysteriously"
- "narrate dramatically with suspense"
- "question with genuine curiosity"

### Voice Cloning Requirements
- **Must provide reference audio** for voice identity
- Reference should be 3-5+ seconds of clear speech
- High quality audio without background noise
- Consistent speaker throughout the sample
- Emotion is controlled separately via text descriptions

## Advanced Techniques

### Multi-Emotion Synthesis
Transition between emotions within speech:
```
Text: "At first I was confused. [pause] Then I understood! [pause] Now I'm excited!"
Emotion sequence:
- Part 1: "confused and uncertain"
- Part 2: "moment of realization"
- Part 3: "excited and enthusiastic"
```

### Prosody Control
Fine-tune speech characteristics:
```
Text: "This needs special emphasis HERE and also HERE."
Style: "emphasize capitalized words with increased pitch and volume"
```

### Speaking Rate Variation
Control pacing and rhythm:
```
Text: "Slowly... then faster, faster, FASTER!"
Style: "start very slow, gradually accelerate to rapid speech"
Duration: free (let emotion guide pacing)
```

### Breathing and Pauses
Natural speech patterns:
```
Text: "Let me think... [breath] Yes, that's the answer."
Style: "thoughtful with natural pauses and breathing"
```

## Use Case Examples

### 1. Audiobook Narration
```
Text: "Chapter One. It was a dark and stormy night."
Voice: [narrator_voice.wav] (REQUIRED reference audio)
Style: "narrative storytelling with dramatic atmosphere"
Duration: free
```

### 2. Voice Assistant
```
Text: "I've found three restaurants nearby. Would you like to hear the options?"
Voice: [assistant_voice.wav] (REQUIRED reference audio)
Style: "helpful and friendly assistant tone"
Duration: explicit (match UI animation timing)
```

### 3. Educational Content
```
Text: "Today we'll learn about photosynthesis."
Voice: [teacher_voice.wav] (REQUIRED reference audio)
Style: "engaging teacher explaining to students"
Duration: free
```

### 4. Advertisement Voiceover
```
Text: "Introducing the all-new product that will change your life!"
Voice: [announcer_voice.wav] (REQUIRED reference audio)
Style: "enthusiastic commercial announcer with energy"
Duration: explicit (fit 15-second slot)
```

### 5. Character Dialogue
```
Text: "I can't believe you would do this to me!"
Voice: [character_voice.wav] (REQUIRED reference audio)
Style: "angry and betrayed, emotional outburst"
Duration: free
```

### 6. News Broadcasting
```
Text: "Breaking news from the capital tonight."
Voice: [anchor_voice.wav] (REQUIRED reference audio)
Style: "serious news anchor, urgent but composed"
Duration: explicit (match video footage)
```

## Style Descriptors

### Energy Levels
- **High**: "energetic, enthusiastic, animated, vibrant"
- **Medium**: "conversational, friendly, engaging, warm"
- **Low**: "calm, soothing, relaxed, gentle"

### Emotional Tones
- **Positive**: "happy, excited, optimistic, cheerful"
- **Negative**: "sad, angry, frustrated, disappointed"
- **Neutral**: "balanced, informative, factual, objective"

### Speaking Styles
- **Formal**: "professional, authoritative, academic, official"
- **Casual**: "relaxed, informal, conversational, friendly"
- **Dramatic**: "theatrical, expressive, dynamic, emphatic"

### Voice Qualities
- **Clear**: "articulate, precise, crisp, well-pronounced"
- **Soft**: "gentle, whispered, intimate, tender"
- **Strong**: "powerful, commanding, assertive, bold"

## Duration Control Guidelines

### Token-to-Duration Mapping
- ~50 tokens = 1 second of speech (approximate)
- Adjust based on speaking rate and style
- Emotional content may affect timing

### Synchronization Tips
1. Start with estimated token count
2. Fine-tune based on output
3. Account for pauses and emphasis
4. Consider emotional pacing changes

## Best Practices

### Do's
- ✅ Always provide reference audio for voice cloning
- ✅ Use clear, high-quality reference samples (3-5+ seconds)
- ✅ Use specific emotion descriptions for expression control
- ✅ Test different duration settings for sync tasks
- ✅ Keep a library of reference voices for consistency

### Don'ts
- ❌ Attempt to generate voices without reference audio
- ❌ Use low-quality or noisy reference samples
- ❌ Mix conflicting emotional instructions
- ❌ Over-constrain duration for emotional speech
- ❌ Ignore that voice generation requires audio input

## Common Issues and Solutions

### Issue: Emotion not expressing correctly
**Solution**: Use more specific descriptions or combine with reference audio

### Issue: Voice identity shifting
**Solution**: Provide longer, clearer reference audio samples (5+ seconds recommended)

### Issue: Unnatural pacing
**Solution**: Use free duration mode or adjust token counts

### Issue: Inconsistent emotion
**Solution**: Break text into segments with separate emotion prompts

### Issue: Poor synchronization
**Solution**: Fine-tune duration tokens and account for emotional pacing

## Example Prompts

### Corporate Presentation
```
Text: "Our quarterly results exceeded all expectations, with a 40% increase in revenue."
Voice: [executive_voice.wav] (REQUIRED reference audio)
Style: "confident business presentation with subtle enthusiasm"
Duration: explicit (match slide transitions)
```

### Children's Story
```
Text: "Once upon a time, in a magical forest, lived a tiny mouse named Max."
Voice: [storyteller_voice.wav] (REQUIRED reference audio)
Style: "warm, engaging storytelling for children with wonder and magic"
Duration: free
```

### Emergency Announcement
```
Text: "Attention: Please evacuate the building immediately using the nearest exit."
Voice: [announcement_voice.wav] (REQUIRED reference audio)
Style: "urgent but calm, clear emergency instructions"
Duration: explicit (loop every 10 seconds)
```

### Meditation Guide
```
Text: "Breathe in slowly... hold... and release..."
Voice: [meditation_voice.wav] (REQUIRED reference audio)
Style: "extremely calm, soothing, slow-paced meditation guidance"
Duration: free (with extended pauses)
```

## Tips for Success

1. **Start with quality references** - Clean audio improves all outputs
2. **Layer emotion gradually** - Build complexity step by step
3. **Test duration settings** - Find the sweet spot for your use case
4. **Use natural language** - Describe emotions as you would to a person
5. **Preserve speaker identity** - Keep voice references consistent
6. **Account for context** - Match emotion to content appropriately
7. **Iterate and refine** - Fine-tune based on initial outputs