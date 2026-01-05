# Decimal Precision Analysis for Scene Numbers

## Current Issue

The current implementation has a bug - it only parses a single digit after "point", not multiple digits. For example:
- `scene one point two five` → Currently parses as 1.2 (should be 1.25)
- `scene one point one two three` → Currently parses as 1.1 (should be 1.123)

## Real-World Requirements

### Typical Scene Counts
- **YouTube Episode**: 5-15 scenes
- **Documentary**: 10-30 scenes
- **Tutorial**: 5-10 scenes
- **Vlog**: 5-8 scenes

### Insertion Scenarios

**Scenario 1: Basic Insertion**
```
Scene 1
Scene 2
→ Insert between: Scene 1.5
```

**Scenario 2: Multiple Insertions**
```
Scene 1
Scene 1.5 (inserted)
Scene 2
→ Insert between 1 and 1.5: Scene 1.25
→ Insert between 1.5 and 2: Scene 1.75
```

**Scenario 3: Deep Insertions (Rare)**
```
Scene 1
Scene 1.5
Scene 1.25 (inserted between 1 and 1.5)
→ Insert between 1 and 1.25: Scene 1.125
→ Insert between 1.25 and 1.5: Scene 1.375
```

## Precision Requirements

### 1 Decimal Place (0.1 precision)
- **Granularity**: 10 positions between integers
- **Example**: 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0
- **Sufficient for**: Most use cases (5-15 scenes)
- **Limitation**: Can't insert between 1.1 and 1.2

### 2 Decimal Places (0.01 precision)
- **Granularity**: 100 positions between integers
- **Example**: 1.00, 1.01, 1.02, ..., 1.25, ..., 1.50, ..., 1.99, 2.00
- **Sufficient for**: All typical use cases
- **Can insert**: Between any two scenes with 1 decimal place
- **Recommendation**: **2 decimal places is ideal**

### 3 Decimal Places (0.001 precision)
- **Granularity**: 1000 positions between integers
- **Example**: 1.000, 1.001, ..., 1.125, ..., 1.375, ..., 1.999, 2.000
- **Sufficient for**: Complex documentaries with many insertions
- **Overkill for**: Most YouTube episodes
- **Use case**: Very long-form content (30+ scenes)

## Recommendation: 2 Decimal Places

**Why 2 decimal places?**
1. **Sufficient granularity**: 100 positions between any two scenes
2. **Easy to say**: "one point two five" (1.25) is natural
3. **Rarely needed deeper**: Most insertions are at 0.5 intervals
4. **Industry standard**: Film/TV typically uses 2 decimal places for scene numbers

**When you might need 3 decimal places:**
- Very long documentaries (30+ scenes)
- Complex narrative structures
- Multiple rounds of insertions

## Implementation Recommendation

1. **Parse up to 2 decimal places** (recommended)
   - `scene one point five` → 1.5
   - `scene one point two five` → 1.25
   - `scene one point one two` → 1.12

2. **Support 3 decimal places** (optional, for edge cases)
   - `scene one point one two five` → 1.125
   - `scene one point three seven five` → 1.375

3. **Limit to 3 decimal places maximum**
   - Beyond 3 places is impractical to say
   - Float precision is fine for 3 decimal places
   - No need for Decimal type (overkill)

## How to Say Decimal Numbers

### 1 Decimal Place
- `scene one point five` → 1.5
- `scene two point three` → 2.3

### 2 Decimal Places
- `scene one point two five` → 1.25
- `scene one point seven five` → 1.75
- `scene two point one two` → 2.12

### 3 Decimal Places (Rare)
- `scene one point one two five` → 1.125
- `scene one point three seven five` → 1.375

## Conclusion

**Current Implementation: 3 decimal places (0.001 precision)**
- ✅ Fixed parsing to handle multiple digits correctly
- ✅ Supports up to 3 decimal places
- ✅ Float precision is sufficient (Python float has ~15-17 decimal digits)
- ✅ Practical to say ("one point one two five")

**Recommended Usage:**
- **Most cases**: 1-2 decimal places (1.5, 1.25)
- **Complex cases**: 3 decimal places (1.125, 1.375)
- **Rarely needed**: More than 3 decimal places

**Why 3 decimal places is the limit:**
1. **Practical to say**: "one point one two five" is natural
2. **Sufficient granularity**: 1000 positions between any two scenes
3. **Float precision**: Python float handles 3 decimal places perfectly
4. **Real-world needs**: Even 30-scene documentaries rarely need deeper precision

**Example Scenarios:**
- **5-15 scenes (YouTube)**: 1-2 decimal places sufficient
- **10-30 scenes (Documentary)**: 2-3 decimal places sufficient
- **30+ scenes (Long-form)**: 3 decimal places sufficient

**Not needed: More than 3 decimal places**
- Impractical to say ("one point one two three four five")
- Unlikely to be needed (1000 positions is plenty)
- Overkill for any real-world scenario

