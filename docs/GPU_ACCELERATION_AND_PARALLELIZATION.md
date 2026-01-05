# GPU Acceleration and Parallelization

## Overview

The pipeline now uses GPU acceleration and parallel processing wherever possible to maximize performance and minimize CPU load.

## GPU Acceleration

### Detection
- **NVIDIA NVENC**: Hardware video encoding (h264_nvenc, hevc_nvenc)
- **AMD AMF**: AMD hardware encoding (h264_amf, hevc_amf)
- **Intel QuickSync**: Intel hardware encoding (h264_qsv, hevc_qsv)
- **CUDA**: For PyTorch/Whisper GPU acceleration

### Where GPU is Used

#### 1. FFmpeg Video Encoding
- **Location**: `studioflow/core/ffmpeg.py`
- **Operations**: Video cutting, concatenation, export
- **Encoder Selection**:
  - NVIDIA GPU → `h264_nvenc` (preset: p4)
  - AMD GPU → `h264_amf` (quality: balanced)
  - Intel GPU → `h264_qsv` (preset: medium)
  - No GPU → `libx264` (CPU, preset: fast)

#### 2. Whisper Transcription
- **Location**: `studioflow/core/transcription.py`
- **Device**: Automatically uses CUDA if available, falls back to CPU
- **FP16**: Enabled on GPU for 2x speed, FP32 on CPU for accuracy
- **Model Loading**: `whisper.load_model(model, device="cuda")` if CUDA available

## Parallel Processing

### Where Parallelization is Used

#### 1. Audio Normalization
- **Location**: `studioflow/core/unified_import.py::_normalize_media()`
- **Method**: `ThreadPoolExecutor` with max 4 workers
- **Why**: FFmpeg normalization is I/O bound, can run multiple in parallel
- **Benefit**: 2-4x faster for multiple files

#### 2. Transcription
- **Location**: `studioflow/core/unified_import.py::_transcribe_media()`
- **Method**: GPU-aware parallel processing
  - **GPU available**: 1 worker (to avoid VRAM issues)
  - **CPU only**: 2 workers (can run 2 in parallel)
- **Why**: Whisper on GPU uses significant VRAM, CPU can handle 2 concurrent jobs
- **Benefit**: 2x faster on CPU, optimal GPU utilization

#### 3. Proxy Generation
- **Location**: `studioflow/core/auto_import.py`
- **Method**: `ThreadPoolExecutor` with max 4 workers
- **Already implemented**: Uses parallel processing for proxy generation

## Performance Impact

### Before Optimization
- **Normalization**: Sequential (1 file at a time)
- **Transcription**: Sequential (1 file at a time, CPU only)
- **Video Encoding**: CPU only (libx264)
- **Result**: High CPU usage, slow processing, high CPU fan activity

### After Optimization
- **Normalization**: Parallel (up to 4 files simultaneously)
- **Transcription**: GPU-accelerated (CUDA) or parallel CPU (2 workers)
- **Video Encoding**: GPU-accelerated (NVENC/AMF/QSV)
- **Result**: 
  - GPU handles video encoding (reduces CPU load)
  - GPU handles transcription (reduces CPU load)
  - Parallel processing speeds up batch operations
  - Lower CPU fan activity, higher GPU utilization

## Monitoring

### Check GPU Status
```python
from studioflow.core.gpu_utils import get_gpu_detector

gpu = get_gpu_detector()
print(gpu.get_gpu_info())
# Output: {'nvidia_nvenc': True, 'amd_amf': False, 'intel_quicksync': True, 'cuda': True, 'has_gpu': True}
```

### Check GPU Usage
```bash
# NVIDIA GPU
nvidia-smi

# General GPU monitoring
nvtop  # Should show activity during pipeline
```

### Expected Behavior
- **nvtop**: Should show GPU activity during:
  - Video encoding (normalization, cutting, export)
  - Transcription (Whisper on GPU)
- **CPU fan**: Should run lower during GPU-accelerated operations
- **CPU usage**: Should be lower overall due to GPU offloading

## Troubleshooting

### GPU Not Detected
1. **Check NVIDIA drivers**: `nvidia-smi` should work
2. **Check FFmpeg encoders**: `ffmpeg -encoders | grep nvenc`
3. **Check CUDA**: `python3 -c "import torch; print(torch.cuda.is_available())"`

### GPU Detected But Not Used
1. **Check logs**: Pipeline logs GPU status on initialization
2. **Verify imports**: Ensure `gpu_utils` is imported correctly
3. **Check fallback**: System falls back to CPU if GPU unavailable

### High CPU Usage Still
- **Normalization**: May still use CPU if GPU encoding fails
- **Transcription**: Falls back to CPU if CUDA unavailable
- **Other operations**: File I/O, marker detection still use CPU

## Configuration

### Adjust Parallel Workers
Edit `studioflow/core/unified_import.py`:

```python
# Normalization: max_workers = min(4, len(files_to_process))
# Transcription (CPU): max_workers = min(2, len(files_to_process))
# Transcription (GPU): max_workers = 1
```

### Force CPU Mode
```python
# In gpu_utils.py, modify get_video_encoder() to always return CPU encoder
return ("libx264", "fast")  # Force CPU
```

## Future Improvements

1. **Hardware Decoding**: Use GPU for video decoding (nvdec, etc.)
2. **Batch Transcription**: Process multiple files on GPU with batching
3. **Dynamic Worker Count**: Adjust based on available VRAM/CPU cores
4. **GPU Memory Management**: Monitor VRAM and adjust batch sizes

