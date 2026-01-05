# Test Documentation

Documentation for the StudioFlow test suite.

## Files

- **[TEST_SUITE_GUIDE.md](TEST_SUITE_GUIDE.md)** - Complete guide for test suite development
  - Test infrastructure and fixtures
  - Implementation strategy and phases
  - Development guidelines and patterns
  - Running tests

- **[TEST_FIXTURES_GUIDE.md](TEST_FIXTURES_GUIDE.md)** - Guide for creating test video clips
  - Camera settings (FX30, ZVE10)
  - Priority clips and scripts
  - Recording procedures
  - Filenaming conventions

## Quick Start

### For Test Development

1. Read **[TEST_SUITE_GUIDE.md](TEST_SUITE_GUIDE.md)**
2. Start with Phase 1: Foundation Layer (config, FFmpeg, media)
3. Follow the phase-by-phase implementation plan
4. Use fixtures and patterns from the guide

### For Creating Test Footage

1. Read **[TEST_FIXTURES_GUIDE.md](TEST_FIXTURES_GUIDE.md)**
2. Configure cameras (FX30: PP10, Log Shooting OFF, Linear PCM)
3. Record priority clips (Comprehensive Marker Test, Talking Head Baseline)
4. Follow filenaming conventions
5. Organize in `tests/fixtures/test_footage/`

## Summary

All test documentation has been consolidated from 14+ files into 2 comprehensive guides:
- **TEST_SUITE_GUIDE.md**: Test development (415 lines)
- **TEST_FIXTURES_GUIDE.md**: Test footage creation (397 lines)

These guides contain all essential information from the original documentation, simplified and organized for easy reference.

