# Production-Grade Fixture Footage Specification

## Purpose

This document describes a **comprehensive, production-like test fixture** that simulates real-world YouTube episode recording sessions. This fixture tests:

- **Long continuous recording sessions** (5-10 minutes)
- **Multiple takes** of the same scenes
- **Edge cases** (gaps, rapid markers, overlapping content)
- **Real-world patterns** (hooks, intros, main content, transitions, outros)
- **Complex segment organization** (scenes, steps, takes, effects)
- **Retroactive actions** throughout the recording
- **End-to-end production workflows**

## Target Duration

**5-10 minutes** of continuous footage simulating a complete YouTube episode recording session.

---

## Production Episode Structure

### Real-World YouTube Episode Pattern

A typical YouTube episode recording includes:

1. **Multiple Hook Attempts** (3-5 takes)
2. **Intro Scene** (1-2 takes)
3. **Main Content** (multiple scenes with steps)
4. **Transitions** (between content blocks)
5. **B-roll Markers** (for cutaways)
6. **Retroactive Scoring** (marking best takes)
7. **Outro/CTA** (final segments)

---

## Complete Production Test Sequence

### Phase 1: Hook Recording (Multiple Takes)

```
Time    Marker Command                         Expected Behavior
─────────────────────────────────────────────────────────────────────────
0:00    [Content: "Testing, one two three"]   (No marker - setup)
0:05    slate scene one take one done          → Segment 001 (Hook Take 1)
0:10    [Content: "Did you know that Python..."] (Hook attempt 1)
0:20    slate scene one take two done          → Segment 001 ENDS, Segment 002 (Hook Take 2)
0:25    [Content: "Python lists are amazing..."] (Hook attempt 2 - different approach)
0:35    slate scene one take three done        → Segment 002 ENDS, Segment 003 (Hook Take 3)
0:40    [Content: "In this video, I'll show..."] (Hook attempt 3 - question format)
0:50    slate apply best done                  → No segment, scores previous take
0:55    slate scene one take four done         → Segment 003 ENDS, Segment 004 (Hook Take 4)
1:00    [Content: "You're about to learn..."] (Hook attempt 4 - statement format)
1:10    slate apply skip done                  → No segment, marks take 4 to skip
1:15    slate scene one take five done         → Segment 004 ENDS, Segment 005 (Hook Take 5)
1:20    [Content: "Welcome! Today we're..."]  (Hook attempt 5 - welcome format)
1:30    slate apply good done                  → No segment, scores take 5 as "good"
```

**Expected**: 5 hook segments, with take 3 scored "best", take 4 marked "skip", take 5 scored "good"

### Phase 2: Intro Scene (With Steps)

```
1:35    slate scene two intro done            → Segment 005 ENDS, Segment 006 (Intro)
1:40    [Content: "Hey everyone, welcome back..."] (Channel intro)
1:50    slate step one branding done          → Segment 006 ENDS, Segment 007 (Branding step)
1:55    [Content: "If you're new here..."]     (Subscribe reminder)
2:05    slate step two preview done           → Segment 007 ENDS, Segment 008 (Preview step)
2:10    [Content: "In this video, we'll cover..."] (What's coming up)
2:20    slate apply hook done                 → No segment, marks preview as hook
```

**Expected**: 3 segments (intro, branding, preview), preview marked as hook

### Phase 3: Main Content (Multiple Scenes with Steps)

```
2:25    slate scene three main done           → Segment 008 ENDS, Segment 009 (Main content)
2:30    [Content: "Let's start with the basics..."] (Main content begins)
2:45    slate step one explanation done       → Segment 009 ENDS, Segment 010 (Explanation step)
2:50    [Content: "Python lists are ordered..."] (Teaching content)
3:10    slate step two example done           → Segment 010 ENDS, Segment 011 (Example step)
3:15    [Content: "Here's a simple example..."] (Code example)
3:30    slate broll screen done               → Segment 011 ENDS, Segment 012 (B-roll marker)
3:35    [Content: "As you can see on screen..."] (Screen recording content)
3:50    slate step three practice done        → Segment 012 ENDS, Segment 013 (Practice step)
3:55    [Content: "Now let's practice together..."] (Interactive content)
4:10    slate apply quote done                → No segment, marks practice as quotable
```

**Expected**: 5 segments (main, explanation, example, broll, practice), practice marked as quote

### Phase 4: Transition and Second Main Block

```
4:15    slate transition fade done            → Segment 013 ENDS, Segment 014 (Transition)
4:20    [Content: "Now that we understand..."] (Transition content)
4:30    slate scene four advanced done        → Segment 014 ENDS, Segment 015 (Advanced content)
4:35    [Content: "Let's dive deeper..."]      (Advanced concepts)
4:55    slate step one concepts done           → Segment 015 ENDS, Segment 016 (Concepts step)
5:00    [Content: "Advanced list operations..."] (Advanced teaching)
5:20    slate step two demonstration done     → Segment 016 ENDS, Segment 017 (Demo step)
5:25    [Content: "Watch how this works..."]   (Live demonstration)
5:45    slate effect zoom done                → Segment 017 ENDS, Segment 018 (Zoom effect)
5:50    [Content: "Notice the details here..."] (Zoomed content)
6:05    slate apply best done                 → No segment, scores demo as "best"
```

**Expected**: 4 segments (transition, advanced, concepts, demo, zoom), demo scored "best"

### Phase 5: Recap and Outro

```
6:10    slate scene five recap done          → Segment 018 ENDS, Segment 019 (Recap)
6:15    [Content: "Let's recap what we learned..."] (Summary)
6:30    slate step one summary done          → Segment 019 ENDS, Segment 020 (Summary step)
6:35    [Content: "Python lists are..."]      (Key points)
6:50    slate step two next steps done        → Segment 020 ENDS, Segment 021 (Next steps)
6:55    [Content: "In the next video, we'll..."] (Teaser for next video)
7:10    slate cta subscribe done             → Segment 021 ENDS, Segment 022 (CTA)
7:15    [Content: "If you found this helpful..."] (Subscribe call-to-action)
7:30    slate apply conclusion done          → No segment, marks CTA as conclusion
7:35    [Content: "Thanks for watching!"]     (Final words)
7:45    [Content: "See you next time!"]       (Sign off - continues to end)
```

**Expected**: 4 segments (recap, summary, next steps, CTA), CTA marked as conclusion

---

## Edge Cases to Test

### Edge Case 1: Rapid Markers (No Content Between)

```
7:50    slate mark done                       → Segment 022 ENDS, Segment 023 (Mark)
7:52    slate mark done                       → Segment 023 ENDS, Segment 024 (Mark - rapid)
7:54    slate mark done                       → Segment 024 ENDS, Segment 025 (Mark - very rapid)
7:56    [Content: "Quick marks for editing"]   (Content after rapid markers)
```

**Test**: System handles rapid markers without content gaps

### Edge Case 2: Multiple Retroactive Actions

```
8:00    slate scene six bonus done            → Segment 025 ENDS, Segment 026 (Bonus)
8:05    [Content: "Bonus tip for you..."]      (Bonus content)
8:15    slate apply best done                 → Scores as "best"
8:18    slate apply hook done                 → Also marks as "hook"
8:21    slate apply quote done                → Also marks as "quote"
```

**Test**: Multiple retroactive actions on same segment

### Edge Case 3: Decimal Scene Numbers

```
8:25    slate scene six point five extra done → Segment 026 ENDS, Segment 027 (Scene 6.5)
8:30    [Content: "One more thing..."]        (Extra content)
8:40    slate scene seven outro done          → Segment 027 ENDS, Segment 028 (Scene 7)
```

**Test**: Decimal scene numbers (6.5) sort correctly between 6 and 7

### Edge Case 4: Long Content Gaps

```
8:45    slate mark done                       → Segment 028 ENDS, Segment 029 (Mark)
8:50    [Content: "Brief content"]
8:55    [Long pause - 10 seconds of silence]
9:05    [Content: "Content after gap"]
9:15    slate scene eight final done          → Segment 029 ENDS, Segment 030 (Final)
```

**Test**: Segments include gaps and silence correctly

### Edge Case 5: Order (Deprecated but Backwards Compatible)

```
9:20    slate order nine done                 → Segment 030 ENDS, Segment 031 (Order 9)
9:25    [Content: "Testing deprecated order"] (Backwards compatibility)
9:35    slate scene ten modern done           → Segment 031 ENDS, Segment 032 (Scene 10)
```

**Test**: Deprecated "order" still works and maps to scene_number

### Edge Case 6: Effects and Transitions Together

```
9:40    slate effect zoom done                → Segment 032 ENDS, Segment 033 (Effect)
9:45    [Content: "Zoom effect content"]
9:55    slate transition fade done            → Segment 033 ENDS, Segment 034 (Transition)
10:00   [Content: "Fade transition content"]
10:10   slate effect mtuber intro done        → Segment 034 ENDS, Segment 035 (Product effect)
10:15   [Content: "Product effect content"]
```

**Test**: Effects and transitions create separate segments correctly

### Edge Case 7: Title and Screen Markers

```
10:20   slate title Introduction done        → Segment 035 ENDS, Segment 036 (Title)
10:25   [Content: "Title card content"]
10:35   slate screen hud done                 → Segment 036 ENDS, Segment 037 (Screen)
10:40   [Content: "Screen recording with HUD"]
10:50   slate chapter lists done              → Segment 037 ENDS, Segment 038 (Chapter)
10:55   [Content: "Chapter marker content"]
```

**Test**: Title, screen, and chapter markers create segments

### Edge Case 8: Emotion and Energy Markers

```
11:00   slate emotion energetic done          → Segment 038 ENDS, Segment 039 (Emotion)
11:05   [Content: "High energy content"]
11:15   slate energy high done                → Segment 039 ENDS, Segment 040 (Energy)
11:20   [Content: "High energy delivery"]
11:30   slate emotion calm done               → Segment 040 ENDS, Segment 041 (Emotion change)
11:35   [Content: "Calm explanation"]
```

**Test**: Emotion and energy markers create segments

### Edge Case 9: Multiple Takes with Scoring

```
11:40   slate scene eleven outro take one done → Segment 041 ENDS, Segment 042 (Outro Take 1)
11:45   [Content: "Thanks for watching take 1"]
11:55   slate scene eleven outro take two done → Segment 042 ENDS, Segment 043 (Outro Take 2)
12:00   [Content: "Thanks for watching take 2"]
12:10   slate apply best done                 → Scores take 2 as "best"
12:13   slate scene eleven outro take three done → Segment 043 ENDS, Segment 044 (Outro Take 3)
12:18   [Content: "Thanks for watching take 3"]
12:28   slate apply good done                 → Scores take 3 as "good"
```

**Test**: Multiple takes with different scores, all grouped under same scene

### Edge Case 10: Complex Retroactive Chain

```
12:30   slate scene twelve bonus done        → Segment 044 ENDS, Segment 045 (Bonus)
12:35   [Content: "One final bonus tip"]
12:45   slate apply best done                 → Scores as "best"
12:48   slate apply hook done                 → Also marks as "hook"
12:51   slate apply quote done                 → Also marks as "quote"
12:54   slate apply conclusion done           → Also marks as "conclusion"
12:57   [Content: "That's a wrap!"]           (Final content)
13:00   [End of video]                        → Segment 045 ends naturally
```

**Test**: Multiple retroactive actions chain correctly

---

## Complete Timeline Summary

### Total Duration: ~13 minutes

### Segments Created: 45+ segments

1. **Hook Takes** (5 segments): Scene 1, Takes 1-5
2. **Intro Sequence** (3 segments): Scene 2 with steps
3. **Main Content Block 1** (5 segments): Scene 3 with steps and broll
4. **Transition** (1 segment): Scene 4 transition
5. **Main Content Block 2** (4 segments): Scene 4 advanced with steps
6. **Recap Sequence** (4 segments): Scene 5 with steps
7. **Edge Cases** (23+ segments): Various edge case tests
8. **Final Segments** (5+ segments): Outro takes and bonus

### Retroactive Actions: 15+ actions

- Multiple "apply best" markers
- Multiple "apply good" markers
- "apply skip" markers
- "apply hook" markers
- "apply quote" markers
- "apply conclusion" markers
- Multiple retroactive actions on same segment

---

## Expected Segment Organization

### By Scene Number (Primary Sort)

```
Scene 1 (Hook): Segments 001-005 (5 takes)
Scene 2 (Intro): Segments 006-008 (with steps)
Scene 3 (Main): Segments 009-013 (with steps)
Scene 4 (Advanced): Segments 014-018 (with steps)
Scene 5 (Recap): Segments 019-022 (with steps)
Scene 6 (Bonus): Segment 026
Scene 6.5 (Extra): Segment 027
Scene 7 (Final): Segment 030
Scene 8 (Final): Segment 030
Scene 9 (Order): Segment 031 (deprecated)
Scene 10 (Modern): Segment 032
Scene 11 (Outro): Segments 042-044 (3 takes)
Scene 12 (Bonus): Segment 045
```

### By Take (Within Same Scene)

Within Scene 1:
- Take 1: Segment 001
- Take 2: Segment 002
- Take 3: Segment 003 (scored "best")
- Take 4: Segment 004 (marked "skip")
- Take 5: Segment 005 (scored "good")

Within Scene 11:
- Take 1: Segment 042
- Take 2: Segment 043 (scored "best")
- Take 3: Segment 044 (scored "good")

---

## Edge Cases Covered

### ✅ Rapid Markers
- Multiple markers in quick succession
- Markers with minimal content between

### ✅ Long Gaps
- Content with long pauses
- Silence between markers

### ✅ Multiple Retroactive Actions
- Multiple "apply" markers on same segment
- Chained retroactive actions

### ✅ Decimal Scene Numbers
- Scene 6.5 between Scene 6 and Scene 7
- Proper sorting of decimal scenes

### ✅ Deprecated Features
- "order" marker (backwards compatible)
- Proper mapping to scene_number

### ✅ Complex Marker Types
- Effects, transitions, titles, screens
- Emotion, energy, chapter markers
- B-roll markers

### ✅ Multiple Takes
- Same scene with multiple takes
- Different scores for different takes
- Proper grouping under same scene

### ✅ Segment Boundaries
- Segments ending at next marker's "slate"
- Last segment extending to video end
- No explicit end markers needed

### ✅ Real-World Patterns
- Hook recording (multiple takes)
- Intro with steps
- Main content with teaching steps
- Transitions between blocks
- Recap and outro
- CTA segments

---

## Recording Script (Full Production Episode)

```
[Setup: "Testing, one two three"]

=== PHASE 1: HOOK RECORDING ===
[Slate] Scene one take one [Done]
Did you know that Python lists are one of the most powerful data structures? In this video, I'll show you everything you need to know.

[Slate] Scene one take two [Done]
Python lists are amazing. They're ordered, mutable, and incredibly versatile. Let me show you how to master them.

[Slate] Scene one take three [Done]
In this video, I'll show you how to use Python lists like a pro. Are you ready to level up your Python skills?

[Slate] Apply best [Done]
[Slate] Scene one take four [Done]
You're about to learn everything about Python lists. This is going to change how you write Python code.

[Slate] Apply skip [Done]
[Slate] Scene one take five [Done]
Welcome! Today we're diving deep into Python lists. This is going to be a game-changer for your coding.

[Slate] Apply good [Done]

=== PHASE 2: INTRO ===
[Slate] Scene two intro [Done]
Hey everyone, welcome back to the channel. I'm excited to share this with you today.

[Slate] Step one branding [Done]
If you're new here, make sure to subscribe and hit that notification bell. We post new Python tutorials every week.

[Slate] Step two preview [Done]
In this video, we'll cover list creation, manipulation, slicing, and advanced techniques. Let's get started!

[Slate] Apply hook [Done]

=== PHASE 3: MAIN CONTENT ===
[Slate] Scene three main [Done]
Let's start with the basics. Python lists are ordered collections of items.

[Slate] Step one explanation [Done]
Python lists are ordered, which means items have a specific position. They're also mutable, so you can change them after creation.

[Slate] Step two example [Done]
Here's a simple example. We can create a list like this: my_list equals open bracket one, two, three close bracket.

[Slate] Broll screen [Done]
As you can see on screen, when we print this list, we get the exact items in order.

[Slate] Step three practice [Done]
Now let's practice together. Try creating a list with your favorite programming languages.

[Slate] Apply quote [Done]

=== PHASE 4: TRANSITION AND ADVANCED ===
[Slate] Transition fade [Done]
Now that we understand the basics, let's dive deeper into advanced operations.

[Slate] Scene four advanced [Done]
Let's explore some advanced list operations that will make your code more powerful.

[Slate] Step one concepts [Done]
Advanced list operations include list comprehensions, slicing with steps, and nested lists.

[Slate] Step two demonstration [Done]
Watch how this works. We can use list comprehensions to create lists in a single line.

[Slate] Effect zoom [Done]
Notice the details here. The syntax is clean and Pythonic.

[Slate] Apply best [Done]

=== PHASE 5: RECAP ===
[Slate] Scene five recap [Done]
Let's recap what we learned today about Python lists.

[Slate] Step one summary [Done]
Python lists are ordered, mutable collections. We can create them, modify them, and use them in powerful ways.

[Slate] Step two next steps [Done]
In the next video, we'll explore dictionaries and how they compare to lists.

[Slate] CTA subscribe [Done]
If you found this helpful, please subscribe and give this video a thumbs up. It really helps the channel.

[Slate] Apply conclusion [Done]
Thanks for watching! See you next time!

=== EDGE CASES ===
[Slate] Mark [Done]
[Slate] Mark [Done]
[Slate] Mark [Done]
Quick marks for editing reference.

[Slate] Scene six bonus [Done]
Bonus tip for you. You can use negative indexing to access items from the end of a list.

[Slate] Apply best [Done]
[Slate] Apply hook [Done]
[Slate] Apply quote [Done]

[Slate] Scene six point five extra [Done]
One more thing. Always remember that lists are mutable, so changes affect the original.

[Slate] Scene seven outro [Done]
That wraps up our discussion on Python lists.

[Slate] Mark [Done]
Brief content here.

[Long pause - 10 seconds]

Content after the gap.

[Slate] Scene eight final [Done]
Final thoughts on Python lists.

[Slate] Order nine [Done]
Testing deprecated order marker for backwards compatibility.

[Slate] Scene ten modern [Done]
Modern scene numbering works great.

[Slate] Effect zoom [Done]
Zoom effect content here.

[Slate] Transition fade [Done]
Fade transition content.

[Slate] Effect mtuber intro [Done]
Product effect content.

[Slate] Title Introduction [Done]
Title card content here.

[Slate] Screen hud [Done]
Screen recording with HUD overlay.

[Slate] Chapter lists [Done]
Chapter marker for YouTube chapters.

[Slate] Emotion energetic [Done]
High energy content delivery here.

[Slate] Energy high [Done]
High energy explanation.

[Slate] Emotion calm [Done]
Calm and clear explanation of concepts.

[Slate] Scene eleven outro take one [Done]
Thanks for watching! Take one of the outro.

[Slate] Scene eleven outro take two [Done]
Thanks for watching! Take two of the outro.

[Slate] Apply best [Done]
[Slate] Scene eleven outro take three [Done]
Thanks for watching! Take three of the outro.

[Slate] Apply good [Done]

[Slate] Scene twelve bonus [Done]
One final bonus tip before we wrap up.

[Slate] Apply best [Done]
[Slate] Apply hook [Done]
[Slate] Apply quote [Done]
[Slate] Apply conclusion [Done]

That's a wrap! Thanks for watching!
```

---

## Validation Checklist

### Transcription Quality
- [ ] All "slate" words detected (50+ markers)
- [ ] All "done" words detected
- [ ] Marker commands transcribed accurately
- [ ] Handles rapid markers correctly
- [ ] Handles long gaps correctly

### Marker Detection
- [ ] All 45+ markers detected
- [ ] Marker types classified correctly
- [ ] Commands parsed correctly
- [ ] Decimal scene numbers parsed (scene six point five)
- [ ] Deprecated "order" still works

### Segment Extraction
- [ ] 45+ segments created correctly
- [ ] Segments start/end at correct timestamps
- [ ] Segments end at next marker's "slate" (not "done")
- [ ] Last segment extends to video end
- [ ] Rapid markers handled correctly
- [ ] Long gaps included in segments

### Retroactive Actions
- [ ] 15+ retroactive actions applied correctly
- [ ] Multiple retroactive actions on same segment work
- [ ] Scores applied correctly (best, good, skip)
- [ ] Hooks, quotes, conclusions applied correctly
- [ ] Chained retroactive actions work

### Segment Organization
- [ ] Segments sorted by scene_number (primary)
- [ ] Takes grouped under same scene
- [ ] Decimal scenes sort correctly (6.5 between 6 and 7)
- [ ] Chronological order within same scene/take
- [ ] Scene 1 has 5 takes (001-005)
- [ ] Scene 11 has 3 takes (042-044)

### Edge Cases
- [ ] Rapid markers (3 marks in 4 seconds) handled
- [ ] Long gaps (10+ seconds) included correctly
- [ ] Multiple retroactive actions on segment 045 work
- [ ] Decimal scene 6.5 sorts correctly
- [ ] Deprecated "order" maps to scene_number
- [ ] All marker types create segments correctly

### Production Workflow
- [ ] Hook recording pattern works (multiple takes)
- [ ] Intro with steps works
- [ ] Main content with teaching steps works
- [ ] Transitions between blocks work
- [ ] Recap and outro work
- [ ] CTA segment marked as conclusion

---

## File Naming

**Recommended:** `PRODUCTION-FIXTURE-comprehensive-episode.MP4`

- `PRODUCTION-FIXTURE` - Identifies as production-grade test fixture
- `comprehensive-episode` - Describes full episode simulation
- `.MP4` - Standard video format

---

## Benefits

- **Production-like testing** - Simulates real YouTube episode recording
- **Comprehensive coverage** - Tests all features in realistic patterns
- **Edge case testing** - Handles rapid markers, gaps, complex scenarios
- **Long-form validation** - Tests system with 10+ minute recordings
- **Multiple takes** - Tests take organization and scoring
- **Real-world patterns** - Matches actual production workflows

---

## Notes

- This fixture is **5-10 minutes** (vs. 30-60 seconds for basic fixture)
- Designed for **comprehensive end-to-end testing**
- Tests **production workflows** not just individual features
- Includes **many edge cases** that occur in real recording sessions
- Validates **segment organization** with 45+ segments
- Tests **retroactive actions** throughout long recording

