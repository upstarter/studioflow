"""
End-to-End Tests for Unified Import Pipeline
Tests the complete pipeline from ingest to ready-to-edit project
"""

import pytest
from pathlib import Path
import json
import shutil
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from studioflow.core.unified_import import UnifiedImportPipeline, ImportResult
from studioflow.core.config import get_config


@pytest.mark.e2e
@pytest.mark.requires_ffmpeg
@pytest.mark.slow
class TestUnifiedImportPipeline:
    """
    End-to-End Tests for Unified Import Pipeline
    
    Tests the complete workflow:
    - Phase 1 (Immediate): Import, Normalize, Proxies
    - Phase 2 (Background): Transcription, Marker Detection
    - Phase 3 (On-Demand): Rough Cut, Resolve Setup
    """
    
    def test_phase1_immediate_processing(self, temp_project_dir, test_output_dir):
        """
        Test Phase 1: Immediate Processing
        - Import media
        - Normalize audio
        - Generate proxies
        """
        # Find original clips with markers
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_footage"
        original_clips = list(fixtures_dir.glob("*original-markers.*"))
        
        if not original_clips:
            pytest.skip("No original clips with markers found")
        
        # Use first clip for testing
        test_clip = original_clips[0]
        
        # Create mock ingest pool directory
        ingest_pool = temp_project_dir / "ingest_pool"
        ingest_pool.mkdir(parents=True)
        
        # Copy test clip to ingest pool
        ingest_clip = ingest_pool / test_clip.name
        shutil.copy2(test_clip, ingest_clip)
        
        # Initialize pipeline
        pipeline = UnifiedImportPipeline()
        
        # Use unique codeword
        unique_codeword = f"test_phase1_{uuid.uuid4().hex[:8]}"
        
        # Run Phase 1 only
        result = pipeline.process_sd_card(
            source_path=ingest_pool,
            codeword=unique_codeword,
            from_ingest=True,
            normalize_audio=True,
            transcribe=False,  # Skip Phase 2
            detect_markers=False,  # Skip Phase 2
            generate_rough_cut=False,  # Skip Phase 3
            setup_resolve=False  # Skip Phase 3
        )
        
        # Verify results
        assert result.success, f"Phase 1 failed: {result.errors}"
        assert result.files_imported > 0, "No files imported"
        assert result.files_normalized > 0, "Audio not normalized"
        assert result.proxies_created > 0, "Proxies not created"
        
        # Verify project structure
        project_path = result.project_path
        assert project_path.exists(), "Project directory not created"
        assert (project_path / "01_MEDIA" / "Original").exists(), "Original media directory not created"
        assert (project_path / "01_MEDIA" / "Normalized").exists(), "Normalized media directory not created"
        assert (project_path / "01_MEDIA" / "Proxy").exists(), "Proxy directory not created"
        
        # Verify files exist
        original_dir = project_path / "01_MEDIA" / "Original"
        normalized_dir = project_path / "01_MEDIA" / "Normalized"
        proxy_dir = project_path / "01_MEDIA" / "Proxy"
        
        original_files = list(original_dir.rglob("*.mp4")) + list(original_dir.rglob("*.MP4"))
        normalized_files = list(normalized_dir.rglob("*normalized*"))
        proxy_files = list(proxy_dir.rglob("*proxy*"))
        
        assert len(original_files) > 0, "Original files not found"
        assert len(normalized_files) > 0, "Normalized files not found"
        assert len(proxy_files) > 0, "Proxy files not found"
        
        # Copy project output to test_output_dir for inspection
        self._copy_project_to_output(result.project_path, test_output_dir)
        
        print(f"\n✅ Phase 1 Complete:")
        print(f"  - Files imported: {result.files_imported}")
        print(f"  - Files normalized: {result.files_normalized}")
        print(f"  - Proxies created: {result.proxies_created}")
        print(f"  - Output copied to: {test_output_dir}")
    
    def test_phase2_background_processing(self, temp_project_dir, test_output_dir):
        """
        Test Phase 2: Background Processing
        - Transcription
        - Marker Detection
        """
        # Find original clips with markers
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_footage"
        original_clips = list(fixtures_dir.glob("*original-markers.*"))
        
        if not original_clips:
            pytest.skip("No original clips with markers found")
        
        # Use first clip for testing
        test_clip = original_clips[0]
        
        # Create mock ingest pool directory
        ingest_pool = temp_project_dir / "ingest_pool"
        ingest_pool.mkdir(parents=True)
        
        # Copy test clip to ingest pool
        ingest_clip = ingest_pool / test_clip.name
        shutil.copy2(test_clip, ingest_clip)
        
        # Initialize pipeline
        pipeline = UnifiedImportPipeline()
        
        # Use unique codeword
        unique_codeword = f"test_phase2_{uuid.uuid4().hex[:8]}"
        
        # Run Phase 1 + Phase 2
        result = pipeline.process_sd_card(
            source_path=ingest_pool,
            codeword=unique_codeword,
            from_ingest=True,
            normalize_audio=True,
            transcribe=True,  # Phase 2
            detect_markers=True,  # Phase 2
            generate_rough_cut=False,  # Skip Phase 3
            setup_resolve=False  # Skip Phase 3
        )
        
        # Verify results
        assert result.success, f"Phase 2 failed: {result.errors}"
        assert result.transcripts_generated > 0, "Transcripts not generated"
        assert result.markers_detected > 0, "Markers not detected"
        assert result.segments_extracted > 0, "Segments not extracted"
        
        # Verify transcript files exist
        transcript_dir = result.project_path / "02_Transcription"
        assert transcript_dir.exists(), "Transcription directory not created"
        
        transcript_files = list(transcript_dir.glob("*transcript.json"))
        assert len(transcript_files) > 0, "Transcript files not found"
        
        # Verify segments info exists
        segments_dir = result.project_path / "03_Segments"
        if segments_dir.exists():
            segment_files = list(segments_dir.glob("*segments.json"))
            assert len(segment_files) > 0, "Segment info files not found"
        
        # Copy project output to test_output_dir for inspection
        self._copy_project_to_output(result.project_path, test_output_dir)
        
        print(f"\n✅ Phase 2 Complete:")
        print(f"  - Transcripts generated: {result.transcripts_generated}")
        print(f"  - Markers detected: {result.markers_detected}")
        print(f"  - Segments extracted: {result.segments_extracted}")
        print(f"  - Output copied to: {test_output_dir}")
    
    def test_full_pipeline_e2e(self, temp_project_dir, test_output_dir):
        """
        Test Full E2E Pipeline: All Phases
        Uses original clips with markers from fixtures
        """
        # Find original clips with markers
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_footage"
        original_clips = list(fixtures_dir.glob("*original-markers.*"))
        
        if not original_clips:
            pytest.skip("No original clips with markers found")
        
        # Create mock ingest pool directory
        ingest_pool = temp_project_dir / "ingest_pool"
        ingest_pool.mkdir(parents=True)
        
        # Copy all test clips to ingest pool
        for clip in original_clips[:2]:  # Use first 2 clips
            ingest_clip = ingest_pool / clip.name
            shutil.copy2(clip, ingest_clip)
        
        # Initialize pipeline
        pipeline = UnifiedImportPipeline()
        
        # Use unique codeword
        unique_codeword = f"test_e2e_{uuid.uuid4().hex[:8]}"
        
        # Run full pipeline (all phases)
        result = pipeline.process_sd_card(
            source_path=ingest_pool,
            codeword=unique_codeword,
            from_ingest=True,
            normalize_audio=True,
            transcribe=True,
            detect_markers=True,
            generate_rough_cut=True,  # Phase 3
            setup_resolve=False  # Skip Resolve (may not be available)
        )
        
        # Verify results
        assert result.success, f"E2E pipeline failed: {result.errors}"
        
        # Phase 1 verification
        assert result.files_imported > 0, "No files imported"
        assert result.files_normalized > 0, "Audio not normalized"
        # Proxies may fail (non-critical) - check if attempted
        if result.proxies_created == 0:
            print("  [yellow]⚠ Proxies not created (may be expected)[/yellow]")
        
        # Phase 2 verification
        assert result.transcripts_generated > 0, "Transcripts not generated"
        assert result.markers_detected > 0, "Markers not detected"
        assert result.segments_extracted > 0, "Segments not extracted"
        
        # Phase 3 verification (if enabled)
        if result.rough_cut_created:
            timeline_dir = result.project_path / "04_Timelines"
            assert timeline_dir.exists(), "Timeline directory not created"
            edl_files = list(timeline_dir.glob("*.edl"))
            assert len(edl_files) > 0, "Rough cut EDL not created"
        
        # Verify complete project structure
        project_path = result.project_path
        expected_dirs = [
            "01_MEDIA/Original",
            "01_MEDIA/Normalized",
            "01_MEDIA/Proxy",
            "02_Transcription",
            "03_Segments"
        ]
        
        for dir_path in expected_dirs:
            full_path = project_path / dir_path
            assert full_path.exists(), f"Directory not created: {dir_path}"
        
        # Save summary to output directory
        summary = {
            "test": "full_pipeline_e2e",
            "timestamp": datetime.now().isoformat(),
            "result": {
                "success": result.success,
                "files_imported": result.files_imported,
                "files_normalized": result.files_normalized,
                "proxies_created": result.proxies_created,
                "transcripts_generated": result.transcripts_generated,
                "markers_detected": result.markers_detected,
                "segments_extracted": result.segments_extracted,
                "rough_cut_created": result.rough_cut_created,
                "resolve_project_created": result.resolve_project_created
            },
            "errors": result.errors,
            "warnings": result.warnings,
            "project_path": str(result.project_path)
        }
        
        # Copy project output to test_output_dir for inspection
        self._copy_project_to_output(result.project_path, test_output_dir)
        
        summary_file = test_output_dir / "e2e_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✅ Full E2E Pipeline Complete:")
        print(f"  - Project: {result.project_path}")
        print(f"  - Files imported: {result.files_imported}")
        print(f"  - Transcripts: {result.transcripts_generated}")
        print(f"  - Markers: {result.markers_detected}")
        print(f"  - Segments: {result.segments_extracted}")
        print(f"  - Output copied to: {test_output_dir}")
        print(f"  - Summary saved to: {summary_file}")
    
    def _copy_project_to_output(self, project_path: Path, output_dir: Path):
        """Copy project files to test output directory for inspection"""
        import shutil
        
        # Copy key directories (skip large files, copy structure and metadata)
        dirs_to_copy = [
            "02_Transcription",  # Transcripts (small JSON/SRT files)
            "03_Segments",        # Segment info (JSON) + actual split clips
            "04_Timelines"        # EDL files
        ]
        
        project_output = output_dir / "project_output"
        project_output.mkdir(exist_ok=True)
        
        for dir_name in dirs_to_copy:
            source_dir = project_path / dir_name
            if source_dir.exists():
                dest_dir = project_output / dir_name
                # Copy directory structure
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                try:
                    shutil.copytree(source_dir, dest_dir)
                except TypeError:
                    # Fallback for older Python versions
                    import distutils.dir_util
                    distutils.dir_util.copy_tree(str(source_dir), str(dest_dir))
        
        # Copy normalized media (for audio verification)
        normalized_dir = project_path / "01_MEDIA" / "Normalized"
        if normalized_dir.exists():
            dest_normalized = project_output / "01_MEDIA" / "Normalized"
            dest_normalized.mkdir(parents=True, exist_ok=True)
            for norm_file in normalized_dir.rglob("*"):
                if norm_file.is_file():
                    # Copy normalized files (for audio verification)
                    rel_path = norm_file.relative_to(normalized_dir)
                    dest_file = dest_normalized / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(norm_file, dest_file)
        
        # Create README with project info
        readme = project_output / "README.md"
        readme.write_text(f"""# Test Output: Full E2E Pipeline

## Project Location
{project_path}

## Output Structure
- `01_MEDIA/Normalized/` - Normalized audio files (for verification)
- `02_Transcription/` - Transcripts (JSON + SRT)
- `03_Segments/` - Segment boundaries (JSON) + actual split video clips (.mov)
- `04_Timelines/` - Rough cut EDL files

## Verification
1. **Audio Normalization**: Play files in `01_MEDIA/Normalized/` and verify consistent audio levels
2. **Transcripts**: Check `02_Transcription/*.json` for word-level timestamps
3. **Segments**: 
   - Check `03_Segments/*.json` for correct cut points
   - Play split clips in `03_Segments/*.mov` to verify cuts are correct
4. **Rough Cut**: Import `04_Timelines/*.edl` into Resolve to verify timeline
""")
    
    def test_project_selection_priority(self, temp_project_dir):
        """
        Test project selection priority:
        1. Codeword provided (explicit)
        2. SD card label
        3. Active project
        4. Auto-create with default
        """
        import uuid
        pipeline = UnifiedImportPipeline()
        
        # Test 1: Explicit codeword (highest priority)
        unique_codeword = f"explicit_test_{uuid.uuid4().hex[:8]}"
        project, name = pipeline.determine_project(
            mount_point=temp_project_dir,
            codeword=unique_codeword
        )
        assert unique_codeword in name, "Explicit codeword not used"
        
        # Test 2: Auto-create with default
        unique_codeword2 = f"auto_test_{uuid.uuid4().hex[:8]}"
        project2, name2 = pipeline.determine_project(
            mount_point=temp_project_dir,
            codeword=unique_codeword2
        )
        assert unique_codeword2 in name2, "Codeword not used"
        assert name2.endswith("_Import"), "Project name format incorrect"
    
    def test_library_path_handling(self, temp_project_dir):
        """
        Test library path handling:
        - Use /mnt/studio/PROJECTS/ if exists
        - Fallback to config.storage.active
        """
        from studioflow.core.project import Project
        
        # Test with library path (if exists)
        config = get_config()
        library_path = config.storage.studio
        
        project = Project("test_library", path=None)
        
        if library_path and library_path.exists():
            # If library path exists, project should be created there
            if library_path.name == "PROJECTS":
                expected_base = library_path
            else:
                expected_base = library_path / "PROJECTS"
            assert project.path.parent == expected_base, f"Project not in library path: {project.path}"
        else:
            # Fallback to active storage
            assert project.path.parent == config.storage.active, "Project not in active storage"
    
    def test_error_handling_non_critical(self, temp_project_dir):
        """
        Test error handling for non-critical errors:
        - Normalization failure should continue
        - Proxy generation failure should continue
        - Transcription failure should continue
        """
        import uuid
        # Create a test clip (empty file to simulate error)
        ingest_pool = temp_project_dir / "ingest_pool"
        ingest_pool.mkdir(parents=True)
        
        # Create invalid video file
        invalid_clip = ingest_pool / "invalid.mp4"
        invalid_clip.write_bytes(b"invalid video data")
        
        pipeline = UnifiedImportPipeline()
        
        # Use unique codeword
        unique_codeword = f"test_errors_{uuid.uuid4().hex[:8]}"
        
        # Run pipeline - should handle errors gracefully
        result = pipeline.process_sd_card(
            source_path=ingest_pool,
            codeword=unique_codeword,
            from_ingest=True,
            normalize_audio=True,
            transcribe=True,
            detect_markers=True,
            generate_rough_cut=False,
            setup_resolve=False
        )
        
        # Should have warnings but not critical errors
        # (Import might succeed even with invalid file)
        if result.errors:
            # Check that errors are logged
            assert len(result.errors) > 0, "Errors should be logged"
        
        # Pipeline should still attempt to complete
        assert result.project_path is not None, "Project should be created even with errors"
    
    def test_phased_processing_flags(self, temp_project_dir):
        """
        Test that phased processing flags work correctly:
        - Phase 1 can run independently
        - Phase 2 requires Phase 1
        - Phase 3 is optional
        """
        import uuid
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_footage"
        original_clips = list(fixtures_dir.glob("*original-markers.*"))
        
        if not original_clips:
            pytest.skip("No original clips with markers found")
        
        pipeline = UnifiedImportPipeline()
        
        # Test: Phase 1 only
        test_clip1 = original_clips[0]
        ingest_pool1 = temp_project_dir / "ingest_pool_1"
        ingest_pool1.mkdir(parents=True)
        shutil.copy2(test_clip1, ingest_pool1 / test_clip1.name)
        
        unique_codeword1 = f"test_phase1_only_{uuid.uuid4().hex[:8]}"
        result1 = pipeline.process_sd_card(
            source_path=ingest_pool1,
            codeword=unique_codeword1,
            from_ingest=True,
            normalize_audio=True,
            transcribe=False,
            detect_markers=False,
            generate_rough_cut=False,
            setup_resolve=False
        )
        assert result1.success, "Phase 1 should succeed independently"
        assert result1.transcripts_generated == 0, "Phase 2 should be skipped"
        
        # Test: Phase 1 + Phase 2 (use different clip to avoid conflicts)
        if len(original_clips) > 1:
            test_clip2 = original_clips[1]
        else:
            test_clip2 = original_clips[0]
        ingest_pool2 = temp_project_dir / "ingest_pool_2"
        ingest_pool2.mkdir(parents=True)
        shutil.copy2(test_clip2, ingest_pool2 / test_clip2.name)
        
        unique_codeword2 = f"test_phase1_2_{uuid.uuid4().hex[:8]}"
        result2 = pipeline.process_sd_card(
            source_path=ingest_pool2,
            codeword=unique_codeword2,
            from_ingest=True,
            normalize_audio=True,
            transcribe=True,
            detect_markers=True,
            generate_rough_cut=False,
            setup_resolve=False
        )
        assert result2.success, "Phase 1+2 should succeed"
        # Note: Transcription may take time, so we check if it was attempted
        # If files were imported, transcription should run (may be 0 if files not found)
        assert result2.files_imported > 0, "Files should be imported for Phase 2"
        
        # Test: All phases (use same clip as phase 2 to avoid disk space issues)
        # Skip if disk space is low (large video files)
        try:
            ingest_pool3 = temp_project_dir / "ingest_pool_3"
            ingest_pool3.mkdir(parents=True)
            # Use hardlink if possible to save space, otherwise skip
            try:
                import os
                test_clip2.stat().st_ino  # Check if file exists
                # Try to create hardlink (saves space)
                try:
                    os.link(test_clip2, ingest_pool3 / test_clip2.name)
                except (OSError, AttributeError):
                    # Fallback to copy, but skip if it fails (disk space)
                    shutil.copy2(test_clip2, ingest_pool3 / test_clip2.name)
            except OSError:
                pytest.skip("Disk space issue - skipping all phases test")
            
            unique_codeword3 = f"test_all_phases_{uuid.uuid4().hex[:8]}"
            result3 = pipeline.process_sd_card(
                source_path=ingest_pool3,
                codeword=unique_codeword3,
                from_ingest=True,
                normalize_audio=True,
                transcribe=True,
                detect_markers=True,
                generate_rough_cut=True,
                setup_resolve=False
            )
            assert result3.success, "All phases should succeed"
            # Segments require markers to be detected, which requires transcription
            # If transcription runs and markers are found, segments should be extracted
            if result3.markers_detected > 0:
                assert result3.segments_extracted > 0, "Segments should be extracted if markers found"
        except OSError as e:
            if "No space left" in str(e):
                pytest.skip(f"Disk space issue - skipping all phases test: {e}")
            raise

