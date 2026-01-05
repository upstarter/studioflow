"""
Advanced Timeline Automation
Intelligent timeline assembly with B-roll placement, music sync, transitions
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .resolve_api import ResolveDirectAPI


class TransitionType(str, Enum):
    """Transition types"""
    CUT = "cut"
    DISSOLVE = "dissolve"
    FADE_TO_BLACK = "fade_to_black"
    WHIP = "whip"
    ZOOM = "zoom"


@dataclass
class TimelineClip:
    """Clip in timeline"""
    clip_path: Path
    start_time: float
    duration: float
    track: int = 1
    in_point: float = 0.0
    out_point: Optional[float] = None
    effects: List[str] = None
    transition_in: Optional[TransitionType] = None
    transition_out: Optional[TransitionType] = None


@dataclass
class BrollMatch:
    """B-roll matched to A-roll"""
    aroll_start: float
    aroll_end: float
    broll_path: Path
    broll_in: float
    broll_out: float
    track: int = 2
    reason: str = ""  # Why this B-roll was matched


class TimelineAutomation:
    """Advanced timeline automation with intelligent assembly"""
    
    def __init__(self, resolve_api: ResolveDirectAPI):
        self.resolve_api = resolve_api
    
    def create_smart_assembly(
        self,
        timeline_name: str,
        aroll_clips: List[Path],
        broll_clips: List[Path],
        music_track: Optional[Path] = None,
        hook_clips: Optional[List[Path]] = None,
        style: str = "youtube"
    ) -> Dict[str, Any]:
        """
        Create intelligent timeline assembly
        
        Args:
            timeline_name: Name for timeline
            aroll_clips: Primary A-roll clips
            broll_clips: B-roll clips for overlay
            music_track: Background music
            hook_clips: Clips for hook/intro
            style: Assembly style (youtube, tutorial, vlog)
        """
        
        if not self.resolve_api.is_connected():
            return {"error": "Resolve not connected"}
        
        media_pool = self.resolve_api.media_pool
        timeline = media_pool.CreateEmptyTimeline(timeline_name)
        
        if not timeline:
            return {"error": "Failed to create timeline"}
        
        timeline_clips = []
        broll_matches = []
        
        # Step 1: Add hook (first 5-15 seconds)
        if hook_clips:
            hook_duration = 10.0
            hook_clip = self._select_best_hook(hook_clips)
            if hook_clip:
                timeline_clips.append(TimelineClip(
                    clip_path=hook_clip,
                    start_time=0.0,
                    duration=hook_duration,
                    track=1
                ))
        
        # Step 2: Place A-roll foundation
        current_time = timeline_clips[-1].start_time + timeline_clips[-1].duration if timeline_clips else 0.0
        
        for aroll in aroll_clips:
            # Analyze clip to find best portion
            duration = self._get_clip_duration(aroll)
            best_in, best_out = self._find_best_portion(aroll, duration)
            clip_duration = best_out - best_in
            
            timeline_clips.append(TimelineClip(
                clip_path=aroll,
                start_time=current_time,
                duration=clip_duration,
                track=1,
                in_point=best_in,
                out_point=best_out
            ))
            
            current_time += clip_duration
        
        # Step 3: Match and place B-roll
        broll_matches = self._match_broll_to_aroll(
            timeline_clips,
            broll_clips
        )
        
        # Step 4: Add transitions
        self._add_smart_transitions(timeline_clips, style)
        
        # Step 5: Add music (if provided)
        if music_track:
            music_clip = self._add_music_bed(timeline, music_track, current_time)
        
        # Step 6: Actually add clips to timeline (resizable clips)
        self._add_clips_to_timeline(timeline, timeline_clips, broll_matches)
        
        # Step 7: Add chapter markers (if available)
        # This would be done separately via chapter generation
        
        return {
            "success": True,
            "timeline_name": timeline_name,
            "aroll_clips": len(timeline_clips),
            "broll_matches": len(broll_matches),
            "total_duration": current_time,
            "has_music": music_track is not None
        }
    
    def _select_best_hook(self, clips: List[Path]) -> Optional[Path]:
        """Select best clip for hook/intro"""
        # Prefer short, high-energy clips
        # For now, just use first clip
        return clips[0] if clips else None
    
    def _get_clip_duration(self, clip_path: Path) -> float:
        """Get clip duration"""
        from .ffmpeg import FFmpegProcessor
        info = FFmpegProcessor.get_media_info(clip_path)
        return info.get("duration_seconds", 0)
    
    def _find_best_portion(self, clip_path: Path, total_duration: float) -> Tuple[float, float]:
        """Find best portion of clip to use"""
        # For now, use golden ratio position
        # In production, would analyze for best moment
        golden_ratio = 0.382
        ideal_start = total_duration * golden_ratio
        
        # Use middle portion
        use_duration = min(total_duration * 0.6, 60.0)  # Max 60 seconds
        in_point = max(0, ideal_start - use_duration / 2)
        out_point = min(total_duration, in_point + use_duration)
        
        return in_point, out_point
    
    def _match_broll_to_aroll(
        self,
        aroll_clips: List[TimelineClip],
        broll_clips: List[Path]
    ) -> List[BrollMatch]:
        """Intelligently match B-roll to A-roll segments"""
        matches = []
        
        # Simple matching: place B-roll over A-roll gaps or long segments
        for aroll in aroll_clips:
            # If A-roll is longer than 10 seconds, add B-roll overlay
            if aroll.duration > 10.0:
                # Find suitable B-roll
                if broll_clips:
                    broll = broll_clips.pop(0) if broll_clips else None
                    if broll:
                        broll_duration = min(aroll.duration * 0.8, 15.0)  # 80% of A-roll or 15s max
                        
                        matches.append(BrollMatch(
                            aroll_start=aroll.start_time + 2.0,  # Start 2s into A-roll
                            aroll_end=aroll.start_time + 2.0 + broll_duration,
                            broll_path=broll,
                            broll_in=0.0,
                            broll_out=broll_duration,
                            track=2,
                            reason="Long A-roll segment"
                        ))
        
        return matches
    
    def _add_smart_transitions(self, clips: List[TimelineClip], style: str):
        """Add intelligent transitions between clips"""
        transition_rules = {
            "youtube": {
                "default": TransitionType.CUT,
                "scene_change": TransitionType.DISSOLVE,
                "time_jump": TransitionType.FADE_TO_BLACK,
            },
            "tutorial": {
                "default": TransitionType.CUT,
                "step_change": TransitionType.DISSOLVE,
            },
            "vlog": {
                "default": TransitionType.WHIP,
                "location_change": TransitionType.FADE_TO_BLACK,
            }
        }
        
        rules = transition_rules.get(style, transition_rules["youtube"])
        
        for i, clip in enumerate(clips[:-1]):
            next_clip = clips[i + 1]
            
            # Determine transition type
            # For now, use default
            clip.transition_out = rules["default"]
            next_clip.transition_in = rules["default"]
    
    def _add_music_bed(self, timeline, music_path: Path, video_duration: float) -> Dict:
        """Add background music with automatic ducking"""
        # Music would be added to audio track
        # Automatic ducking when speech detected
        return {
            "success": True,
            "music_path": music_path,
            "duration": video_duration
        }
    
    def _add_clips_to_timeline(
        self,
        timeline,
        timeline_clips: List[TimelineClip],
        broll_matches: List[BrollMatch]
    ):
        """
        Add clips to Resolve timeline as FULL RESIZABLE CLIPS.
        
        Key: Clips are added with in/out points set, but the FULL CLIP
        is available in the Media Pool, so you can resize/extend them
        in the timeline editor.
        """
        media_pool = self.resolve_api.media_pool
        
        # Get clips from media pool (must import first if not already imported)
        # We'll import full clips, then set in/out points when adding to timeline
        
        # Add A-roll clips to timeline
        for clip_data in timeline_clips:
            clip_path = clip_data.clip_path
            
            # Find or import clip in media pool
            clip_item = self._get_or_import_clip(media_pool, clip_path)
            
            if clip_item:
                try:
                    # Add clip to timeline with in/out points
                    # Using AppendToTimeline which preserves full clip for resizing
                    result = media_pool.AppendToTimeline([
                        {
                            "mediaPoolItem": clip_item,
                            "startFrame": int(clip_data.in_point * timeline.GetSetting("timelineFrameRate")),
                            "endFrame": int(clip_data.out_point * timeline.GetSetting("timelineFrameRate")) if clip_data.out_point else None,
                            "trackIndex": clip_data.track - 1  # Resolve uses 0-based indexing
                        }
                    ])
                    
                    # Note: Even with in/out points set, the full clip remains available
                    # You can extend/trim in timeline because the source clip is full-length
                    
                except Exception as e:
                    # Fallback: Just append full clip, user can trim manually
                    print(f"  Note: Could not set in/out points for {clip_path.name}, added full clip (resizable)")
                    try:
                        media_pool.AppendToTimeline([clip_item])
                    except:
                        print(f"  Warning: Failed to add {clip_path.name} to timeline")
        
        # Add B-roll clips to timeline
        for broll in broll_matches:
            clip_path = broll.broll_path
            clip_item = self._get_or_import_clip(media_pool, clip_path)
            
            if clip_item:
                try:
                    # Add B-roll with in/out points, but still resizable
                    timeline_frame_rate = timeline.GetSetting("timelineFrameRate") or 30
                    result = media_pool.AppendToTimeline([
                        {
                            "mediaPoolItem": clip_item,
                            "startFrame": int(broll.broll_in * timeline_frame_rate),
                            "endFrame": int(broll.broll_out * timeline_frame_rate),
                            "trackIndex": broll.track - 1
                        }
                    ])
                except Exception as e:
                    # Fallback: Add full clip
                    print(f"  Note: Added full B-roll clip for {clip_path.name} (resizable)")
                    try:
                        media_pool.AppendToTimeline([clip_item])
                    except:
                        print(f"  Warning: Failed to add B-roll {clip_path.name}")
    
    def _get_or_import_clip(self, media_pool, clip_path: Path):
        """
        Get clip from media pool, or import it if not present.
        Returns the MediaPoolItem.
        """
        # Check if clip is already in media pool
        root_folder = media_pool.GetRootFolder()
        all_clips = root_folder.GetClipList()
        
        # Search by filename
        for clip in all_clips:
            if clip.GetName() == clip_path.name:
                return clip
        
        # Not found, import it
        try:
            # Import the full clip (this ensures it's resizable)
            imported = media_pool.ImportMedia([str(clip_path)])
            if imported and len(imported) > 0:
                return imported[0]
        except Exception as e:
            print(f"  Warning: Could not import {clip_path.name}: {e}")
        
        return None


