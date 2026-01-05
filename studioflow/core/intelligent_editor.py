"""
Intelligent video editing automation
AI-powered rough cuts and story structure
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import timedelta
import subprocess

from .resolve_ai import MediaAnalysis
from .ffmpeg import FFmpegProcessor


@dataclass
class StoryBeat:
    """Story structure element"""
    name: str
    type: str  # hook, intro, main, transition, outro
    duration_target: float  # Target duration in seconds
    clips: List[MediaAnalysis] = field(default_factory=list)
    actual_duration: float = 0.0
    notes: str = ""


@dataclass
class EditPoint:
    """Edit decision point"""
    timecode: float
    clip: MediaAnalysis
    in_point: float
    out_point: float
    transition: str = "cut"  # cut, dissolve, wipe
    audio_fade: bool = False
    speed_ramp: Optional[float] = None
    effects: List[str] = field(default_factory=list)


@dataclass
class RoughCut:
    """Complete rough cut structure"""
    name: str
    style: str  # youtube, documentary, vlog, tutorial
    story_beats: List[StoryBeat]
    edit_points: List[EditPoint]
    total_duration: float
    music_track: Optional[Path] = None
    narration_track: Optional[Path] = None
    target_duration: Optional[float] = None


class IntelligentEditor:
    """AI-powered video editing automation"""

    STORY_TEMPLATES = {
        "youtube_episode": [
            ("hook", 5, "Attention grabber"),
            ("intro", 10, "Channel intro/title"),
            ("preview", 15, "What's coming up"),
            ("main_1", 180, "Main content block 1"),
            ("transition_1", 5, "Transition/breathing room"),
            ("main_2", 180, "Main content block 2"),
            ("transition_2", 5, "Transition"),
            ("main_3", 180, "Main content block 3"),
            ("recap", 20, "Key points recap"),
            ("outro", 20, "Call to action/end screen")
        ],
        "youtube_short": [
            ("hook", 3, "Instant grab"),
            ("main", 50, "Core content"),
            ("punchline", 7, "Payoff/conclusion")
        ],
        "tutorial": [
            ("intro", 10, "What we'll learn"),
            ("prerequisites", 20, "What you need"),
            ("step_1", 60, "First step"),
            ("step_2", 60, "Second step"),
            ("step_3", 60, "Third step"),
            ("result", 30, "Final result"),
            ("outro", 10, "Summary and next steps")
        ],
        "vlog": [
            ("teaser", 5, "Quick preview"),
            ("title", 5, "Title card"),
            ("morning", 120, "Morning segment"),
            ("transition", 5, "Location change"),
            ("afternoon", 120, "Afternoon segment"),
            ("evening", 120, "Evening segment"),
            ("reflection", 30, "Thoughts/summary"),
            ("outro", 15, "Sign off")
        ]
    }

    def __init__(self):
        self.media_analyses = []
        self.story_beats = []
        self.edit_points = []
        self.music_beats = []

    def generate_rough_cut(self,
                          media_analyses: List[MediaAnalysis],
                          style: str = "youtube_episode",
                          target_duration: Optional[float] = None,
                          music_track: Optional[Path] = None) -> RoughCut:
        """Generate intelligent rough cut based on style"""

        print(f"🎬 Generating {style} rough cut...")

        self.media_analyses = media_analyses

        # 1. Analyze content structure
        content_structure = self.analyze_content_structure()

        # 2. Create story beats based on template
        self.story_beats = self.create_narrative_structure(style, content_structure)

        # 3. Assign clips to story beats
        self.assign_clips_to_beats()

        # 4. Generate edit points with timing
        self.edit_points = self.generate_edit_points()

        # 5. If music provided, sync to beat
        if music_track:
            self.sync_to_music(music_track)

        # 6. Optimize for target duration
        if target_duration:
            self.optimize_duration(target_duration)

        # 7. Add transitions and effects
        self.add_smart_transitions()

        # Calculate total duration
        total_duration = sum(ep.out_point - ep.in_point for ep in self.edit_points)

        return RoughCut(
            name=f"{style}_rough_cut",
            style=style,
            story_beats=self.story_beats,
            edit_points=self.edit_points,
            total_duration=total_duration,
            music_track=music_track,
            target_duration=target_duration
        )

    def analyze_content_structure(self) -> Dict:
        """Analyze available content"""

        structure = {
            "total_clips": len(self.media_analyses),
            "total_duration": sum(m.duration for m in self.media_analyses),
            "content_types": {},
            "quality_distribution": {},
            "scene_count": 0,
            "has_talking_head": False,
            "has_broll": False,
            "has_action": False
        }

        # Analyze content types
        for media in self.media_analyses:
            content_type = media.content_type
            if content_type not in structure["content_types"]:
                structure["content_types"][content_type] = 0
            structure["content_types"][content_type] += 1

            # Check specific types
            if content_type == "talking_head":
                structure["has_talking_head"] = True
            elif content_type == "broll":
                structure["has_broll"] = True
            elif content_type == "action":
                structure["has_action"] = True

        # Count scenes
        scenes = set(m.scene_number for m in self.media_analyses if m.scene_number)
        structure["scene_count"] = len(scenes)

        # Quality distribution
        for media in self.media_analyses:
            quality_tier = "high" if media.quality_score >= 80 else "medium" if media.quality_score >= 60 else "low"
            if quality_tier not in structure["quality_distribution"]:
                structure["quality_distribution"][quality_tier] = 0
            structure["quality_distribution"][quality_tier] += 1

        return structure

    def create_narrative_structure(self, style: str, content_structure: Dict) -> List[StoryBeat]:
        """Create story beats based on template and available content"""

        if style not in self.STORY_TEMPLATES:
            style = "youtube_episode"

        template = self.STORY_TEMPLATES[style]
        beats = []

        for beat_type, duration, notes in template:
            beat = StoryBeat(
                name=beat_type,
                type=self.classify_beat_type(beat_type),
                duration_target=duration,
                notes=notes
            )
            beats.append(beat)

        # Adjust beats based on available content
        self.adapt_beats_to_content(beats, content_structure)

        return beats

    def classify_beat_type(self, beat_name: str) -> str:
        """Classify beat type from name"""
        if "hook" in beat_name:
            return "hook"
        elif "intro" in beat_name or "title" in beat_name:
            return "intro"
        elif "main" in beat_name or "step" in beat_name:
            return "main"
        elif "transition" in beat_name:
            return "transition"
        elif "outro" in beat_name or "end" in beat_name:
            return "outro"
        return "main"

    def adapt_beats_to_content(self, beats: List[StoryBeat], content_structure: Dict):
        """Adapt story beats to available content"""

        total_available = content_structure["total_duration"]
        total_needed = sum(b.duration_target for b in beats)

        # Scale beats if not enough content
        if total_available < total_needed:
            scale_factor = total_available / total_needed * 0.9  # Leave 10% margin
            for beat in beats:
                beat.duration_target *= scale_factor

        # Adjust based on content types
        if not content_structure["has_talking_head"]:
            # Reduce talking segments
            for beat in beats:
                if beat.type == "main":
                    beat.duration_target *= 0.8

        if content_structure["has_broll"]:
            # Can use more B-roll in transitions
            for beat in beats:
                if beat.type == "transition":
                    beat.duration_target *= 1.5

    def assign_clips_to_beats(self):
        """
        Intelligently assign clips to story beats (clip-level assignment)
        
        Note: This method works at the clip level using quality_score as a fallback.
        Audio markers ("order", "naming", "best"/"select" commands) are processed
        at the segment level via RoughCutEngine. For marker-based beat assignment,
        use RoughCutEngine which handles segment-level marker processing.
        
        Quality score used here as fallback when markers are not available.
        Priority: 1) Audio markers (RoughCutEngine), 2) quality_score (this method)
        """
        # Sort by quality_score as fallback (markers handled by RoughCutEngine)
        sorted_clips = sorted(self.media_analyses, key=lambda x: x.quality_score, reverse=True)

        # Assign hook - highest energy/quality clip
        hook_beat = next((b for b in self.story_beats if b.type == "hook"), None)
        if hook_beat:
            hook_clips = self.find_hook_clips(sorted_clips)
            hook_beat.clips = hook_clips[:2]  # Max 2 clips for hook

        # Assign main content
        main_beats = [b for b in self.story_beats if b.type == "main"]
        main_clips = [c for c in sorted_clips if c.content_type in ["talking_head", "action"]]

        # Distribute main clips across main beats
        if main_beats and main_clips:
            clips_per_beat = len(main_clips) // len(main_beats)
            for i, beat in enumerate(main_beats):
                start_idx = i * clips_per_beat
                end_idx = start_idx + clips_per_beat if i < len(main_beats) - 1 else len(main_clips)
                beat.clips = main_clips[start_idx:end_idx]

        # Assign B-roll to transitions
        transition_beats = [b for b in self.story_beats if b.type == "transition"]
        broll_clips = [c for c in sorted_clips if c.content_type == "broll"]

        for i, beat in enumerate(transition_beats):
            if i < len(broll_clips):
                beat.clips = [broll_clips[i]]

        # Assign intro/outro
        self.assign_intro_outro_clips()

    def find_hook_clips(self, sorted_clips: List[MediaAnalysis]) -> List[MediaAnalysis]:
        """
        Find best clips for hook (quality_score as fallback)
        
        Note: Audio markers ("hook" commands) are processed at segment level via RoughCutEngine.
        Quality score used here as fallback when markers are not available.
        """
        hook_candidates = []

        for clip in sorted_clips:
            # Prefer short, high-quality, high-energy clips (quality_score as fallback)
            if clip.duration < 10 and clip.quality_score > 80:
                if clip.content_type in ["action", "establishing"]:
                    hook_candidates.append(clip)

        # If no ideal clips, use best overall
        if not hook_candidates:
            hook_candidates = sorted_clips[:3]

        return hook_candidates

    def assign_intro_outro_clips(self):
        """Assign clips for intro and outro"""

        intro_beat = next((b for b in self.story_beats if b.type == "intro"), None)
        outro_beat = next((b for b in self.story_beats if b.type == "outro"), None)

        # Find establishing shots for intro
        if intro_beat:
            establishing = [c for c in self.media_analyses if c.content_type == "establishing"]
            if establishing:
                intro_beat.clips = [establishing[0]]

        # Find good closing shot for outro
        if outro_beat:
            # Prefer talking head for call-to-action
            talking_heads = [c for c in self.media_analyses if c.content_type == "talking_head"]
            if talking_heads:
                outro_beat.clips = [talking_heads[-1]]  # Use last talking head

    def generate_edit_points(self) -> List[EditPoint]:
        """Generate precise edit points"""

        edit_points = []
        current_time = 0.0

        for beat in self.story_beats:
            if not beat.clips:
                continue

            beat_duration_per_clip = beat.duration_target / len(beat.clips) if beat.clips else beat.duration_target

            for clip in beat.clips:
                # Calculate in and out points
                if clip.duration <= beat_duration_per_clip:
                    # Use entire clip
                    in_point = 0
                    out_point = clip.duration
                else:
                    # Extract best portion
                    in_point, out_point = self.find_best_portion(clip, beat_duration_per_clip)

                edit_point = EditPoint(
                    timecode=current_time,
                    clip=clip,
                    in_point=in_point,
                    out_point=out_point,
                    transition="cut",
                    audio_fade=False
                )

                edit_points.append(edit_point)
                current_time += (out_point - in_point)

            beat.actual_duration = sum(
                ep.out_point - ep.in_point
                for ep in edit_points
                if ep.clip in beat.clips
            )

        return edit_points

    def find_best_portion(self, clip: MediaAnalysis, target_duration: float) -> Tuple[float, float]:
        """Find best portion of clip to use"""

        # If clip has best thumbnail time, center around that
        if clip.best_thumbnail_time:
            center = clip.best_thumbnail_time
            half_duration = target_duration / 2
            in_point = max(0, center - half_duration)
            out_point = min(clip.duration, in_point + target_duration)

            # Adjust if at boundaries
            if out_point == clip.duration:
                in_point = max(0, clip.duration - target_duration)
        else:
            # Use golden ratio for pleasant composition
            golden_ratio = 0.382
            ideal_start = clip.duration * golden_ratio

            in_point = max(0, ideal_start - target_duration / 2)
            out_point = min(clip.duration, in_point + target_duration)

        return in_point, out_point

    def sync_to_music(self, music_track: Path):
        """Sync edits to music beat"""

        print("🎵 Syncing to music beat...")

        # Detect beats in music
        self.music_beats = self.detect_music_beats(music_track)

        # Snap edit points to nearest beats
        for edit_point in self.edit_points:
            nearest_beat = self.find_nearest_beat(edit_point.timecode)
            if nearest_beat and abs(edit_point.timecode - nearest_beat) < 1.0:  # Within 1 second
                # Adjust timing to hit the beat
                adjustment = nearest_beat - edit_point.timecode
                edit_point.timecode = nearest_beat

                # Add impact transition on strong beats
                if self.is_strong_beat(nearest_beat):
                    edit_point.transition = "impact_cut"
                    edit_point.effects.append("zoom_punch")

    def detect_music_beats(self, music_track: Path) -> List[float]:
        """Detect beats in music track"""

        # Simplified beat detection using FFmpeg
        # In production, would use librosa or aubio
        cmd = [
            "ffmpeg", "-i", str(music_track),
            "-af", "silencedetect=n=-30dB:d=0.1",
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            # Parse beat points (simplified)
            beats = []
            # This is a placeholder - real implementation would use proper beat detection
            # For now, return beats every 2 seconds
            info = FFmpegProcessor.get_media_info(music_track)
            duration = info.get("duration_seconds", 0)
            beats = [i * 2.0 for i in range(int(duration / 2))]
            return beats
        except:
            return []

    def find_nearest_beat(self, timecode: float) -> Optional[float]:
        """Find nearest music beat to timecode"""
        if not self.music_beats:
            return None

        nearest = min(self.music_beats, key=lambda b: abs(b - timecode))
        return nearest

    def is_strong_beat(self, beat_time: float) -> bool:
        """Determine if beat is strong/downbeat"""
        # Simplified - every 4th beat is strong
        beat_index = self.music_beats.index(beat_time) if beat_time in self.music_beats else 0
        return beat_index % 4 == 0

    def optimize_duration(self, target_duration: float):
        """Optimize edit to hit target duration"""

        current_duration = sum(ep.out_point - ep.in_point for ep in self.edit_points)

        if current_duration == target_duration:
            return

        ratio = target_duration / current_duration

        if ratio > 1:
            # Need to extend - add more of each clip
            for ep in self.edit_points:
                available = ep.clip.duration - ep.out_point
                extension = min(available, (ep.out_point - ep.in_point) * (ratio - 1))
                ep.out_point += extension
        else:
            # Need to shorten - trim each clip proportionally
            for ep in self.edit_points:
                current_length = ep.out_point - ep.in_point
                new_length = current_length * ratio
                trim = current_length - new_length

                # Trim from end preferably
                ep.out_point -= trim

    def add_smart_transitions(self):
        """Add intelligent transitions between clips"""

        for i, edit_point in enumerate(self.edit_points[:-1]):
            next_point = self.edit_points[i + 1]

            # Determine transition type based on content
            if edit_point.clip.content_type != next_point.clip.content_type:
                # Content type change - use transition
                if edit_point.clip.content_type == "action" and next_point.clip.content_type == "talking_head":
                    edit_point.transition = "dissolve"
                    edit_point.audio_fade = True
                elif edit_point.clip.scene_number != next_point.clip.scene_number:
                    # Scene change
                    edit_point.transition = "fade_to_black"

            # Add L/J cuts for dialogue
            if edit_point.clip.has_speech and next_point.clip.has_speech:
                # Create J-cut (audio leads video)
                edit_point.audio_fade = False
                edit_point.effects.append("j_cut")

            # Speed ramps for action
            if edit_point.clip.content_type == "action":
                if i > 0 and self.edit_points[i - 1].clip.content_type != "action":
                    # Ramp into action
                    edit_point.speed_ramp = 1.5
                elif i < len(self.edit_points) - 2 and self.edit_points[i + 2].clip.content_type != "action":
                    # Ramp out of action
                    edit_point.speed_ramp = 0.8

    def export_edit_decision_list(self, rough_cut: RoughCut, output_path: Path):
        """Export EDL for Resolve"""

        edl_content = []
        edl_content.append("TITLE: " + rough_cut.name)
        edl_content.append("FCM: NON-DROP FRAME")
        edl_content.append("")

        for i, ep in enumerate(rough_cut.edit_points, 1):
            # EDL format
            # 001  AX  V  C  00:00:00:00 00:00:10:00 01:00:00:00 01:00:10:00

            source_in = self.frames_to_timecode(ep.in_point * 30)
            source_out = self.frames_to_timecode(ep.out_point * 30)
            record_in = self.frames_to_timecode(ep.timecode * 30)
            record_out = self.frames_to_timecode((ep.timecode + (ep.out_point - ep.in_point)) * 30)

            line = f"{i:03d}  AX  V  {ep.transition[0].upper()}  {source_in} {source_out} {record_in} {record_out}"
            edl_content.append(line)

            # Add clip name
            edl_content.append(f"* FROM CLIP NAME: {ep.clip.file_path.name}")

            # Add effects
            if ep.effects:
                edl_content.append(f"* EFFECT: {', '.join(ep.effects)}")

            edl_content.append("")

        output_path.write_text("\n".join(edl_content))
        print(f"📝 Exported EDL to: {output_path}")

    def frames_to_timecode(self, frames: float, fps: float = 30) -> str:
        """Convert frames to timecode"""
        total_seconds = frames / fps
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        frames_remainder = int((frames % fps))

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames_remainder:02d}"

    def generate_preview(self, rough_cut: RoughCut, output_path: Path, duration: float = 30):
        """Generate quick preview of rough cut"""

        print(f"🎬 Generating {duration}s preview...")

        # Take proportional samples from each story beat
        preview_clips = []
        for beat in rough_cut.story_beats:
            if beat.clips:
                # Take first clip from each beat
                preview_clips.append(beat.clips[0])

        if not preview_clips:
            return

        # Create simple concatenated preview
        segment_duration = duration / len(preview_clips)

        cmd = ["ffmpeg"]
        filter_complex = []

        for i, clip in enumerate(preview_clips):
            cmd.extend(["-i", str(clip.file_path)])

            # Trim and scale each input
            filter_complex.append(f"[{i}:v]trim=0:{segment_duration},setpts=PTS-STARTPTS,scale=1920:1080[v{i}]")

        # Concatenate
        concat_inputs = "".join([f"[v{i}]" for i in range(len(preview_clips))])
        filter_complex.append(f"{concat_inputs}concat=n={len(preview_clips)}:v=1:a=0[out]")

        cmd.extend([
            "-filter_complex", ";".join(filter_complex),
            "-map", "[out]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-y", str(output_path)
        ])

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Preview saved to: {output_path}")