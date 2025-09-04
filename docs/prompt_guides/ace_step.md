# ACE-Step V1 Music Generation Prompting Guide

## Model Overview
ACE-Step V1 is a 3.5-billion parameter open-source foundation model for music generation released in mid-2025. It produces high-quality, coherent music quickly and supports full-song generation, duration control, natural language descriptions, and flexible editing features like remixing and lyric editing.

## Token Limit
- **Tags**: 100 tokens (comma-separated keywords)
- **Lyrics**: 500 tokens (with structure tags)
- **Format**: Two-field system (Tags + Lyrics)

## Core Prompt Structure

ACE-Step uses a dual-prompt system:

### 1. Tags Field
Comma-separated keywords describing:
- **Genre**: pop, rock, jazz, classical, electronic, hip-hop
- **Mood**: upbeat, melancholic, energetic, chill, dramatic
- **Instrumentation**: piano, guitar, synth, drums, orchestra
- **Style descriptors**: modern, vintage, ambient, aggressive
- **Scene/Context**: summer, night, party, meditation

Example:
```
lofi hiphop, chill, summer vibe, instrumental, vinyl crackle, jazz samples
```

### 2. Lyrics Field
Structured song content with:
- **Structure tags**: `[verse]`, `[chorus]`, `[bridge]`, `[intro]`, `[outro]`
- **Language tags**: `[en]`, `[zh]`, `[ko]`, `[ja]`, `[es]`
- **Instrumental sections**: Instrument names for non-vocal parts
- **Vocal directions**: Optional performance hints

Example:
```
[intro]
[instrumental] Soft piano and strings

[verse]
[en] Walking down the sunny lanes,
Summer breeze calling my name

[chorus]
[en] Feel the rhythm in my soul,
Dancing free, losing control

[bridge]
[instrumental] Guitar solo

[outro]
[en] Fade into the sunset glow
```

## Control Parameters

### Essential Settings
- **Duration**: Length in seconds (10-180) or "random"
- **Inference steps**: Quality/speed tradeoff (default: 27)
- **Guidance scale**: Prompt adherence (default: 15)
- **Tag guidance**: Style tag influence (default: 5)
- **Lyric guidance**: Lyrical content focus (default: 1.5)
- **Seed**: Reproducibility control (-1 for random)

### Advanced Controls
- **Temperature**: Creativity vs consistency (0.7-1.0)
- **Top-p**: Sampling diversity (0.8-0.95)
- **Retake sections**: Re-generate specific parts
- **Extend track**: Continue generation from endpoint

## Genre-Specific Prompting

### Pop Music
```
Tags: pop, upbeat, catchy, radio-friendly, modern production, female vocal, dance
Lyrics: Simple, repetitive structure with memorable hooks
```

### Lo-fi Hip Hop
```
Tags: lofi hiphop, chill, study music, vinyl crackle, jazz samples, rain sounds, instrumental
Lyrics: [instrumental] or minimal vocal samples
```

### Electronic/EDM
```
Tags: electronic, edm, house, techno, synthesizer, bass drop, club, energetic
Lyrics: Often minimal, focus on rhythm and energy
```

### Classical
```
Tags: classical, orchestral, symphonic, baroque, romantic era, strings, piano
Lyrics: [instrumental] Full orchestra, movements specified
```

### Rock
```
Tags: rock, electric guitar, drums, bass, powerful vocals, distortion, energetic
Lyrics: Verse-chorus structure with guitar solos
```

### Jazz
```
Tags: jazz, swing, bebop, smooth jazz, saxophone, piano trio, improvisation
Lyrics: Can be vocal jazz or instrumental
```

## Advanced Techniques

### Multi-Language Songs
```
[verse]
[en] Starting in English here
[ko] 한국어로 계속해요
[ja] 日本語でも歌える
```

### Dynamic Structure
```
[intro - quiet]
[instrumental] Soft piano intro

[verse - building]
[en] Starting soft and gentle

[chorus - powerful]
[en] Exploding into energy

[bridge - minimal]
[instrumental] Strip back to basics

[final chorus - epic]
[en] Grand finale with full orchestra
```

### Instrumental Specifications
```
[verse]
[instrumental] Acoustic guitar fingerpicking, violin countermelody

[chorus]
[instrumental] Full band enters: drums, bass, electric guitar, synthesizer pads
```

### Mood Progression
```
Tags: emotional journey, starts melancholic, builds to triumphant, orchestral dynamics
```

## Style Combinations

### Fusion Genres
```
Tags: jazz fusion, electronic elements, world music influences, experimental
```

### Era Mixing
```
Tags: 80s synthwave, modern production, retro futuristic, nostalgic yet fresh
```

### Cultural Blends
```
Tags: celtic folk, electronic beats, traditional instruments, modern arrangement
```

## Common Issues and Solutions

### Issue: Generic sound
**Solution**: Add specific instrument names and production styles

### Issue: Poor structure
**Solution**: Use clear structure tags and consistent sections

### Issue: Weak dynamics
**Solution**: Specify dynamic changes in tags and structure markers

### Issue: Language mixing errors
**Solution**: Clearly mark each language section with tags

### Issue: Tempo inconsistency
**Solution**: Include BPM in tags (e.g., "120 bpm")

## Best Practices

### Do's
- ✅ Use specific genre and subgenre tags
- ✅ Include mood and energy descriptors
- ✅ Structure lyrics with clear sections
- ✅ Specify instrumentation details
- ✅ Add production style keywords

### Don'ts
- ❌ Overload with contradicting genres
- ❌ Mix incompatible tempos/moods
- ❌ Forget structure tags in lyrics
- ❌ Use vague descriptions
- ❌ Ignore language tags for multilingual

## Example Prompts

### Complete Pop Song
```
Tags: pop, upbeat, summer hit, female vocalist, catchy hook, modern production, 128 bpm

Lyrics:
[intro]
[instrumental] Synth pad with finger snaps

[verse 1]
[en] Sunshine on my window pane
Another perfect summer day
Got that feeling, can't explain
Everything will be okay

[pre-chorus]
[en] Turn it up, feel the beat
Moving to the summer heat

[chorus]
[en] We're dancing in the golden light
Everything's gonna be alright
Summer love under starry skies
This moment's our paradise

[verse 2]
[en] Beach waves and ice cream cones
Making memories on our phones
Friends together, never alone
This summer's all our own

[chorus]
[en] We're dancing in the golden light
Everything's gonna be alright
Summer love under starry skies
This moment's our paradise

[bridge]
[instrumental] Guitar solo with vocal runs

[final chorus]
[en] We're dancing in the golden light (dancing, dancing)
Everything's gonna be alright (it's alright)
Summer love under starry skies (under the stars)
This moment's our paradise (our paradise)

[outro]
[en] Summer dreams that never fade
[instrumental] Fade out with acoustic guitar
```

### Cinematic Instrumental
```
Tags: cinematic, orchestral, epic, emotional, film score, Hans Zimmer style, building intensity

Lyrics:
[intro - mysterious]
[instrumental] Solo cello with ambient pads

[section 1 - awakening]
[instrumental] Strings section enters, subtle percussion

[section 2 - journey begins]
[instrumental] Full orchestra, french horns melody, timpani rolls

[section 3 - conflict]
[instrumental] Aggressive strings, brass stabs, intense percussion

[section 4 - resolution]
[instrumental] Triumphant brass, soaring strings, choir vocals

[outro - peace]
[instrumental] Solo piano with string quartet
```

### Lo-fi Study Session
```
Tags: lofi, study music, chill, rain ambience, vinyl crackle, jazz chords, 75 bpm, instrumental

Lyrics:
[full track]
[instrumental] Mellow piano chords, soft drum loop, occasional saxophone, rain sounds throughout
```

## Tips for Success

1. **Be specific** with genre and style tags
2. **Structure clearly** using section markers
3. **Layer complexity** gradually in arrangements
4. **Match mood** between tags and lyrical content
5. **Test variations** with different guidance scales
6. **Use references** to established artists/styles sparingly
7. **Maintain consistency** across all prompt elements