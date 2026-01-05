# GPU Usage Explanation

## What You're Seeing

```
Process: cursor (pytest)
GPU Memory: 958MiB / 1752MiB (55%)
Compute: 0%
Memory Usage: 6%
```

## Is This Expected?

### ✅ **YES - This is Normal During Test Setup**

**Why 0% Compute?**
- GPU compute only spikes **during active transcription**
- Between transcriptions, GPU is idle (model stays in memory)
- The test runs transcriptions sequentially, so GPU is idle between files

**Why 958MB Memory?**
- **Whisper base model**: ~280MB
- **CUDA context overhead**: ~100-200MB
- **Multiple model instances**: If model is loaded multiple times (not cached)
- **Cursor IDE**: May also use GPU for UI rendering
- **PyTorch overhead**: Additional memory for CUDA operations

### Expected GPU Usage Pattern

```
┌─────────────────────────────────────┐
│ Test Start                          │
│ GPU Memory: 0MB → 958MB (model load)│
│ Compute: 0%                         │
├─────────────────────────────────────┤
│ Transcription 1                     │
│ GPU Memory: 958MB                   │
│ Compute: 60-90% (active processing) │
├─────────────────────────────────────┤
│ Between Files                       │
│ GPU Memory: 958MB (model cached)    │
│ Compute: 0% (idle)                  │
├─────────────────────────────────────┤
│ Transcription 2                     │
│ GPU Memory: 958MB                   │
│ Compute: 60-90% (active processing) │
└─────────────────────────────────────┘
```

## How to Verify GPU is Actually Working

### 1. Monitor During Active Transcription

```bash
# In another terminal, watch GPU during test
watch -n 0.5 nvidia-smi
```

You should see:
- **Compute**: Spike to 60-90% during transcription
- **Memory**: Stay around 958MB
- **Power**: Increase during compute

### 2. Check Model Device

```python
from studioflow.core.transcription import TranscriptionService
service = TranscriptionService()
# Model should be on CUDA
```

### 3. Compare CPU vs GPU Speed

**CPU (expected)**: ~30-60 seconds per minute of audio
**GPU (expected)**: ~5-10 seconds per minute of audio

Your test took 89 seconds for 2 files, which suggests GPU is working.

## Why Memory Stays High

### Model Caching
Whisper caches loaded models in memory. If you load the same model twice, it reuses the cached version:

```python
model1 = whisper.load_model("base", device="cuda")  # Loads to GPU
model2 = whisper.load_model("base", device="cuda")  # Reuses cached model
# Same object in memory
```

### CUDA Context
PyTorch maintains a CUDA context that uses memory even when idle.

### Multiple Instances
If `TranscriptionService` creates new model instances each time (not cached), memory can accumulate.

## Optimization Opportunities

### 1. Model Caching in TranscriptionService

Currently, each `transcribe()` call loads the model. We could cache it:

```python
class TranscriptionService:
    _model_cache = {}  # Cache models by (model_name, device)
    
    def transcribe(self, ...):
        cache_key = (model, device)
        if cache_key not in self._model_cache:
            self._model_cache[cache_key] = whisper.load_model(model, device=device)
        model_obj = self._model_cache[cache_key]
```

### 2. Clear GPU Memory After Tests

```python
import torch
torch.cuda.empty_cache()  # Clear unused memory
```

### 3. Monitor Actual Compute Usage

The 0% you're seeing is likely between transcriptions. During active transcription, it should spike.

## What to Check

1. **During transcription**: Run `nvidia-smi` while test is actively transcribing
   - Should see compute at 60-90%
   - Memory should be ~958MB

2. **Test duration**: 89 seconds for 2 files suggests GPU is working
   - CPU would take 3-5x longer

3. **Model device**: Verify model is on CUDA
   ```python
   model = whisper.load_model("base", device="cuda")
   print(next(model.parameters()).device)  # Should be: cuda:0
   ```

## Summary

**Your GPU usage is expected:**
- ✅ Memory: 958MB (model + overhead)
- ✅ Compute: 0% (idle between transcriptions)
- ✅ Should spike to 60-90% during active transcription

**To verify it's working:**
- Monitor `nvidia-smi` during active transcription
- Check test duration (89s suggests GPU acceleration)
- Verify model device is CUDA

The 0% compute you're seeing is normal when GPU is idle between operations.

