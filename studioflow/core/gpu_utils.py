"""
GPU detection and acceleration utilities
"""

import subprocess
import logging
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class GPUDetector:
    """Detect available GPU hardware and acceleration capabilities"""
    
    def __init__(self):
        self.nvidia_available = self._check_nvidia()
        self.amd_available = self._check_amd()
        self.intel_available = self._check_intel()
        self.cuda_available = self._check_cuda()
        
    def _check_nvidia(self) -> bool:
        """Check for NVIDIA GPU and NVENC support"""
        try:
            # Check nvidia-smi
            result = subprocess.run(
                ["nvidia-smi", "-L"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and "GPU" in result.stdout:
                # Check FFmpeg for NVENC
                result = subprocess.run(
                    ["ffmpeg", "-hide_banner", "-encoders"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if "h264_nvenc" in result.stdout or "hevc_nvenc" in result.stdout:
                    logger.info("NVIDIA GPU with NVENC detected")
                    return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False
    
    def _check_amd(self) -> bool:
        """Check for AMD GPU and AMF support"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "h264_amf" in result.stdout or "hevc_amf" in result.stdout:
                logger.info("AMD GPU with AMF detected")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False
    
    def _check_intel(self) -> bool:
        """Check for Intel GPU and QuickSync support"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "h264_qsv" in result.stdout or "hevc_qsv" in result.stdout:
                logger.info("Intel GPU with QuickSync detected")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False
    
    def _check_cuda(self) -> bool:
        """Check for CUDA availability (for PyTorch/Whisper)"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def get_video_encoder(self) -> Tuple[str, str]:
        """
        Get best available video encoder
        
        Returns:
            (encoder_name, preset) tuple
        """
        if self.nvidia_available:
            return ("h264_nvenc", "p4")  # p4 = balanced quality/speed
        elif self.amd_available:
            return ("h264_amf", "balanced")
        elif self.intel_available:
            return ("h264_qsv", "medium")
        else:
            return ("libx264", "fast")  # CPU fallback
    
    def get_whisper_device(self) -> str:
        """
        Get device string for Whisper
        
        Returns:
            "cuda" if CUDA available, "cpu" otherwise
        """
        return "cuda" if self.cuda_available else "cpu"
    
    def get_gpu_info(self) -> Dict[str, bool]:
        """Get summary of GPU capabilities"""
        return {
            "nvidia_nvenc": self.nvidia_available,
            "amd_amf": self.amd_available,
            "intel_quicksync": self.intel_available,
            "cuda": self.cuda_available,
            "has_gpu": self.nvidia_available or self.amd_available or self.intel_available
        }


# Global detector instance
_gpu_detector: Optional[GPUDetector] = None


def get_gpu_detector() -> GPUDetector:
    """Get or create global GPU detector instance"""
    global _gpu_detector
    if _gpu_detector is None:
        _gpu_detector = GPUDetector()
    return _gpu_detector

