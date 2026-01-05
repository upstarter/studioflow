#!/usr/bin/env python3
"""
Test Unified Import Pipeline on CAMA and CAMB original footage
Runs the pipeline directly on test fixtures without copying files
"""

import sys
from pathlib import Path
from datetime import datetime
import uuid
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from studioflow.core.unified_import import UnifiedImportPipeline

def test_single_fixture(fixture_path: Path, codeword_prefix: str = "test_fixture"):
    """Test unified pipeline on a single fixture file"""
    import os
    import uuid
    
    fixtures_dir = fixture_path.parent
    
    print(f"\n{'='*70}")
    print("Testing Unified Import Pipeline on Fixture")
    print(f"{'='*70}\n")
    print(f"Fixture: {fixture_path.name} ({fixture_path.stat().st_size / 1e9:.2f} GB)\n")
    
    # Create test output directory structure
    test_output_base = Path(__file__).parent / "tests" / "output" / "unified_pipeline"
    test_output_base.mkdir(parents=True, exist_ok=True)
    test_projects_dir = test_output_base / "projects"
    test_projects_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir = test_output_base / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    
    # Create temporary ingest pool with symlink
    ingest_pool = test_output_base / "ingest_pool"
    if ingest_pool.exists():
        import shutil
        shutil.rmtree(ingest_pool)
    ingest_pool.mkdir(parents=True)
    
    # Create symlink to fixture
    fixture_link = ingest_pool / fixture_path.name
    try:
        os.symlink(fixture_path, fixture_link)
    except OSError as e:
        print(f"⚠ Warning: Could not create symlink: {e}")
        ingest_pool = fixtures_dir
    
    # Override config
    from studioflow.core.config import get_config
    config = get_config()
    original_active = config.storage.active
    original_studio = config.storage.studio
    
    config.storage.active = test_projects_dir
    config.storage.studio = None
    
    # Initialize pipeline
    pipeline = UnifiedImportPipeline()
    pipeline.project_manager.projects_dir = test_projects_dir
    
    # Use unique codeword
    unique_codeword = f"{codeword_prefix}_{uuid.uuid4().hex[:8]}"
    
    print(f"Running pipeline with codeword: {unique_codeword}\n")
    print("Pipeline phases:")
    print("  ✓ Phase 1: Import, Normalize, Proxies")
    print("  ✓ Phase 2: Transcription, Marker Detection")
    print("  ✓ Phase 3: Rough Cut Generation\n")
    
    # Run full pipeline
    print("Starting pipeline...\n")
    result = pipeline.process_sd_card(
        source_path=ingest_pool,
        codeword=unique_codeword,
        from_ingest=True,
        normalize_audio=True,
        transcribe=True,
        detect_markers=True,
        generate_rough_cut=True,
        setup_resolve=False
    )
    
    # Print results
    print(f"\n{'='*70}")
    print("Pipeline Results")
    print(f"{'='*70}\n")
    
    if result.success:
        print("✅ Pipeline completed successfully!\n")
    else:
        print("❌ Pipeline failed!\n")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
        print()
    
    print("Statistics:")
    print(f"  Files imported:       {result.files_imported}")
    print(f"  Files normalized:     {result.files_normalized}")
    print(f"  Proxies created:      {result.proxies_created}")
    print(f"  Transcripts generated: {result.transcripts_generated}")
    print(f"  Markers detected:     {result.markers_detected}")
    print(f"  Segments extracted:   {result.segments_extracted}")
    print(f"  Rough cut created:    {result.rough_cut_created}")
    print(f"  Resolve project:      {result.resolve_project_created}\n")
    
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
        print()
    
    if result.success and result.project_path:
        project_path = result.project_path
        print(f"Project path: {project_path}\n")
        
        # Check outputs
        print("Generated outputs:")
        
        # Check segments
        segments_dir = project_path / "03_Segments"
        if segments_dir.exists():
            segment_files = list(segments_dir.rglob("*.mov")) + list(segments_dir.rglob("*.MP4"))
            print(f"  Segments: {len(segment_files)} files in {segments_dir}")
            if segment_files:
                print("    Sample files:")
                for seg_file in segment_files[:10]:
                    size_mb = seg_file.stat().st_size / 1e6
                    print(f"      - {seg_file.name} ({size_mb:.1f} MB)")
                if len(segment_files) > 10:
                    print(f"      ... and {len(segment_files) - 10} more")
        else:
            print(f"  ⚠ Segments directory not found: {segments_dir}")
        
        # Check transcripts
        transcript_dir = project_path / "02_Transcription"
        if transcript_dir.exists():
            transcript_files = list(transcript_dir.glob("*.json"))
            print(f"  Transcripts: {len(transcript_files)} files in {transcript_dir}")
        else:
            print(f"  ⚠ Transcript directory not found: {transcript_dir}")
        
        # Check timelines
        timeline_dir = project_path / "04_Timelines"
        if timeline_dir.exists():
            edl_files = list(timeline_dir.glob("*.edl"))
            print(f"  Timelines: {len(edl_files)} EDL files in {timeline_dir}")
        else:
            print(f"  ⚠ Timeline directory not found: {timeline_dir}")
        
        print()
        
        # Save summary
        summary_file = summaries_dir / f"pipeline_summary_{unique_codeword}.json"
        summary = {
            "test": codeword_prefix,
            "timestamp": datetime.now().isoformat(),
            "codeword": unique_codeword,
            "fixture": fixture_path.name,
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
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"Summary saved to: {summary_file}\n")
    
    print(f"{'='*70}\n")
    
    # Restore original config
    try:
        config.storage.active = original_active
        config.storage.studio = original_studio
    except NameError:
        pass
    
    return result.success


def test_cama_camb_pipeline():
    """Test unified pipeline on CAMA and CAMB original footage"""
    
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures" / "test_footage"
    
    # Try production fixture first, fallback to original fixtures
    production_fixture = fixtures_dir / "PRODUCTION-FIXTURE-comprehensive-episode.MP4"
    test_fixture = fixtures_dir / "TEST-FIXTURE-comprehensive-markers.MP4"
    
    # Find original clips (fallback)
    cama_clip = fixtures_dir / "CAMA-C0176-original-markers.MP4"
    camb_clip = fixtures_dir / "CAMB-C0030-original-markers.MP4"
    
    # Prefer production fixture if available
    if production_fixture.exists():
        print(f"\n{'='*70}")
        print("Using Production-Grade Fixture")
        print(f"{'='*70}\n")
        print(f"Production Fixture: {production_fixture.name} ({production_fixture.stat().st_size / 1e9:.2f} GB)")
        return test_single_fixture(production_fixture, "production_episode")
    
    # Try test fixture if available
    if test_fixture.exists():
        print(f"\n{'='*70}")
        print("Using Test Fixture")
        print(f"{'='*70}\n")
        print(f"Test Fixture: {test_fixture.name} ({test_fixture.stat().st_size / 1e9:.2f} GB)")
        return test_single_fixture(test_fixture, "test_comprehensive")
    
    # Fallback to original fixtures
    print(f"\n{'='*70}")
    print("Using Original CAMA/CAMB Fixtures")
    print(f"{'='*70}\n")
    
    if not cama_clip.exists():
        print(f"❌ CAMA clip not found: {cama_clip}")
        return False
    
    if not camb_clip.exists():
        print(f"❌ CAMB clip not found: {camb_clip}")
        return False
    
    print(f"\n{'='*70}")
    print("Testing Unified Import Pipeline on Original Footage")
    print(f"{'='*70}\n")
    print(f"CAMA (FX30): {cama_clip.name} ({cama_clip.stat().st_size / 1e9:.2f} GB)")
    print(f"CAMB (ZV-E10): {camb_clip.name} ({camb_clip.stat().st_size / 1e9:.2f} GB)\n")
    
    # Use fixtures directory as source (direct, no copying needed)
    # The pipeline expects an "ingest pool" structure, so we'll create a temp structure
    # But use symlinks to avoid copying large files
    
    import os
    
    # Create test output directory structure
    test_output_base = Path(__file__).parent / "tests" / "output" / "unified_pipeline"
    test_output_base.mkdir(parents=True, exist_ok=True)
    test_projects_dir = test_output_base / "projects"
    test_projects_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir = test_output_base / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    
    # Create temporary ingest pool with symlinks
    ingest_pool = test_output_base / "ingest_pool"
    if ingest_pool.exists():
        import shutil
        shutil.rmtree(ingest_pool)
    ingest_pool.mkdir(parents=True)
    
    # Create symlinks to original files
    cama_link = ingest_pool / cama_clip.name
    camb_link = ingest_pool / camb_clip.name
    
    try:
        os.symlink(cama_clip, cama_link)
        os.symlink(camb_clip, camb_link)
    except OSError as e:
        print(f"⚠ Warning: Could not create symlinks: {e}")
        print("Falling back to direct path usage...")
        # Just use the fixtures directory directly
        ingest_pool = fixtures_dir
    
    # Override config to use test output directory instead of production storage
    from studioflow.core.config import get_config
    
    # Temporarily override config storage paths to use test directory
    config = get_config()
    original_active = config.storage.active
    original_library = config.storage.studio
    
    # Override to use test directory (set library to None so it uses active instead)
    config.storage.active = test_projects_dir
    config.storage.studio = None  # Disable studio path for tests
    
    # Initialize pipeline (will use the overridden config)
    pipeline = UnifiedImportPipeline()
    pipeline.project_manager.projects_dir = test_projects_dir
    
    # Use unique codeword
    unique_codeword = f"test_cama_camb_{uuid.uuid4().hex[:8]}"
    
    print(f"Running pipeline with codeword: {unique_codeword}\n")
    print("Pipeline phases:")
    print("  ✓ Phase 1: Import, Normalize, Proxies")
    print("  ✓ Phase 2: Transcription, Marker Detection")
    print("  ✓ Phase 3: Rough Cut Generation\n")
    
    # Run full pipeline
    print("Starting pipeline...\n")
    result = pipeline.process_sd_card(
        source_path=ingest_pool,
        codeword=unique_codeword,
        from_ingest=True,
        normalize_audio=True,
        transcribe=True,
        detect_markers=True,
        generate_rough_cut=True,
        setup_resolve=False  # Skip Resolve
    )
    
    # Print results
    print(f"\n{'='*70}")
    print("Pipeline Results")
    print(f"{'='*70}\n")
    
    if result.success:
        print("✅ Pipeline completed successfully!\n")
    else:
        print("❌ Pipeline failed!\n")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
        print()
    
    print("Statistics:")
    print(f"  Files imported:       {result.files_imported}")
    print(f"  Files normalized:     {result.files_normalized}")
    print(f"  Proxies created:      {result.proxies_created}")
    print(f"  Transcripts generated: {result.transcripts_generated}")
    print(f"  Markers detected:     {result.markers_detected}")
    print(f"  Segments extracted:   {result.segments_extracted}")
    print(f"  Rough cut created:    {result.rough_cut_created}")
    print(f"  Resolve project:      {result.resolve_project_created}\n")
    
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
        print()
    
    if result.success and result.project_path:
        project_path = result.project_path
        print(f"Project path: {project_path}\n")
        
        # Check outputs
        print("Generated outputs:")
        
        # Check segments
        segments_dir = project_path / "03_Segments"
        if segments_dir.exists():
            segment_files = list(segments_dir.rglob("*.mov")) + list(segments_dir.rglob("*.MP4"))
            print(f"  Segments: {len(segment_files)} files in {segments_dir}")
            if segment_files:
                print("    Sample files:")
                for seg_file in segment_files[:5]:
                    size_mb = seg_file.stat().st_size / 1e6
                    print(f"      - {seg_file.name} ({size_mb:.1f} MB)")
                if len(segment_files) > 5:
                    print(f"      ... and {len(segment_files) - 5} more")
        else:
            print(f"  ⚠ Segments directory not found: {segments_dir}")
        
        # Check transcripts
        transcript_dir = project_path / "02_Transcription"
        if transcript_dir.exists():
            transcript_files = list(transcript_dir.glob("*.json"))
            print(f"  Transcripts: {len(transcript_files)} files in {transcript_dir}")
        else:
            print(f"  ⚠ Transcript directory not found: {transcript_dir}")
        
        # Check timelines
        timeline_dir = project_path / "04_Timelines"
        if timeline_dir.exists():
            edl_files = list(timeline_dir.glob("*.edl"))
            print(f"  Timelines: {len(edl_files)} EDL files in {timeline_dir}")
        else:
            print(f"  ⚠ Timeline directory not found: {timeline_dir}")
        
        print()
        
        # Save summary
        summary_file = summaries_dir / f"pipeline_summary_{unique_codeword}.json"
        summary = {
            "test": "cama_camb_pipeline",
            "timestamp": datetime.now().isoformat(),
            "codeword": unique_codeword,
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
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"Summary saved to: {summary_file}\n")
    
    print(f"{'='*70}\n")
    
    # Restore original config (only if we successfully got config earlier)
    try:
        config.storage.active = original_active
        config.storage.studio = original_library
    except NameError:
        pass  # Config override wasn't set up
    
    return result.success

if __name__ == "__main__":
    success = test_cama_camb_pipeline()
    sys.exit(0 if success else 1)

