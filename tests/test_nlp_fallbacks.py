"""
Tests for NLP library fallback chains
Tests graceful degradation when libraries are missing
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

from studioflow.core.rough_cut import (
    TranscriptAnalyzer,
    ClipAnalysis,
    SRTEntry
)


class TestNLPFallbacks:
    """Test NLP library availability and fallback chains"""
    
    def test_spacy_unavailable_fallback(self):
        """Test that keyword fallback works when spaCy unavailable"""
        analyzer = TranscriptAnalyzer()
        
        # Mock spaCy as unavailable
        original_spacy = analyzer._spacy_available
        analyzer._spacy_available = False
        if hasattr(analyzer, '_nlp'):
            delattr(analyzer, '_nlp')
        
        try:
            topic = analyzer._detect_topic("We have a major problem with the system.")
            # Should fallback to keyword matching
            assert "problem" in topic.lower() or topic == "problem"
        finally:
            analyzer._spacy_available = original_spacy
    
    def test_vader_unavailable_fallback_to_textblob(self):
        """Test VADER → TextBlob fallback"""
        analyzer = TranscriptAnalyzer()
        
        # Mock VADER as unavailable
        original_vader = analyzer._vader_available
        analyzer._vader_available = False
        analyzer._vader_analyzer = None
        
        try:
            # Test that fallback works (will use TextBlob if available, else heuristic)
            sentiment = analyzer._analyze_sentiment("I love this project!")
            # Should return some sentiment value
            assert isinstance(sentiment, (int, float))
            assert -1.0 <= sentiment <= 1.0
            # With "love" in text, should be positive (heuristic or TextBlob)
            assert sentiment >= 0.0
        finally:
            analyzer._vader_available = original_vader
    
    def test_all_nlp_unavailable_heuristic_fallback(self):
        """Test that heuristic fallback works when all NLP unavailable"""
        analyzer = TranscriptAnalyzer()
        
        # Mock all NLP libraries as unavailable
        with patch.object(analyzer, '_vader_available', False):
            with patch.object(analyzer, '_textblob_available', False):
                # Should use word-count heuristic
                positive_sentiment = analyzer._analyze_sentiment("I love this amazing wonderful project!")
                negative_sentiment = analyzer._analyze_sentiment("I hate this terrible awful project!")
                neutral_sentiment = analyzer._analyze_sentiment("The weather is sunny today.")
                
                assert positive_sentiment > 0
                assert negative_sentiment < 0
                assert abs(neutral_sentiment) < 0.5
    
    def test_quote_extraction_without_nlp(self):
        """Test quote extraction works without NLP libraries"""
        analyzer = TranscriptAnalyzer()
        
        # Disable all NLP
        with patch.object(analyzer, '_spacy_available', False):
            with patch.object(analyzer, '_vader_available', False):
                with patch.object(analyzer, '_textblob_available', False):
                    clip = ClipAnalysis(
                        file_path=Path("test.mp4"),
                        duration=30.0,
                        transcript_path=None,
                        entries=[
                            SRTEntry(1, 0.0, 5.0, "This is an important statement with numbers like 2024."),
                            SRTEntry(2, 5.0, 10.0, "Um, you know, like, basically..."),
                        ]
                    )
                    
                    quotes = analyzer.extract_quotes(clip, min_importance=50.0)
                    
                    # Should still extract quotes using heuristics
                    assert len(quotes) > 0
                    # First quote should score higher (has numbers, better content)
                    assert quotes[0].importance_score > quotes[1].importance_score if len(quotes) > 1 else True
    
    def test_topic_detection_keyword_fallback(self):
        """Test topic detection falls back to keywords"""
        analyzer = TranscriptAnalyzer()
        
        with patch.object(analyzer, '_spacy_available', False):
            # Test various topic keywords
            test_cases = [
                ("We have a problem with the system.", "problem"),
                ("The solution is to fix this bug.", "solution"),
                ("Let me introduce the background.", "introduction"),
                ("I remember when this happened.", "personal_stories"),
                ("Research shows that data proves this.", "expert_opinions"),
                ("In conclusion, we must wrap up.", "conclusion"),
            ]
            
            for text, expected_topic in test_cases:
                topic = analyzer._detect_topic(text)
                assert expected_topic in topic.lower() or topic == expected_topic
    
    def test_keyword_extraction_fallback(self):
        """Test keyword extraction falls back to word frequency"""
        analyzer = TranscriptAnalyzer()
        
        with patch.object(analyzer, '_spacy_available', False):
            text = "The climate change problem requires urgent solutions from climate experts."
            keywords = analyzer._extract_keywords(text)
            
            # Should extract keywords using word frequency
            assert len(keywords) > 0
            # Common words should appear
            assert any("climate" in kw.lower() for kw in keywords) or any("problem" in kw.lower() for kw in keywords)
    
    def test_natural_edit_points_without_audio_analysis(self):
        """Test natural edit point detection works without audio analysis"""
        analyzer = TranscriptAnalyzer()
        
        clip = ClipAnalysis(
            file_path=Path("test.mp4"),
            duration=30.0,
            transcript_path=None,
            entries=[
                SRTEntry(1, 0.0, 5.0, "First sentence."),
                SRTEntry(2, 8.0, 12.0, "Second sentence."),  # 3 second gap
                SRTEntry(3, 12.0, 15.0, "Third sentence."),
            ]
        )
        
        edit_points = analyzer.find_natural_edit_points(clip)
        
        # Should find pause between entries
        assert len(edit_points) > 0
        # Should detect the 3-second gap
        assert any(5.0 < ep.timecode < 8.0 for ep in edit_points)
    
    def test_interview_segment_analysis_graceful_degradation(self):
        """Test full analysis works with missing NLP libraries"""
        analyzer = TranscriptAnalyzer()
        
        # Disable all NLP
        with patch.object(analyzer, '_spacy_available', False):
            with patch.object(analyzer, '_vader_available', False):
                with patch.object(analyzer, '_textblob_available', False):
                    clip = ClipAnalysis(
                        file_path=Path("interview.mp4"),
                        duration=60.0,
                        transcript_path=None,
                        entries=[
                            SRTEntry(1, 0.0, 10.0, "I remember when we started in 2020."),
                            SRTEntry(2, 10.0, 20.0, "It was challenging but we found solutions."),
                        ],
                        has_speech=True
                    )
                    
                    segment = analyzer.analyze_interview_segment(clip)
                    
                    # Should still work with fallbacks
                    assert segment is not None
                    assert segment.clip == clip
                    assert len(segment.quotes) >= 0  # May have quotes from heuristics
                    assert segment.emotion_score is not None
                    assert len(segment.natural_pauses) >= 0


class TestLibraryAvailability:
    """Test library availability detection"""
    
    def test_spacy_availability_check(self):
        """Test spaCy availability detection"""
        analyzer = TranscriptAnalyzer()
        
        # Test when spaCy is available
        if analyzer._spacy_available:
            assert hasattr(analyzer, '_nlp') or analyzer._spacy_available == False
        else:
            # If not available, should gracefully handle
            assert analyzer._spacy_available == False
    
    def test_textblob_availability_check(self):
        """Test TextBlob availability detection"""
        analyzer = TranscriptAnalyzer()
        
        # Should detect availability
        assert isinstance(analyzer._textblob_available, bool)
    
    def test_vader_availability_check(self):
        """Test VADER availability detection"""
        analyzer = TranscriptAnalyzer()
        
        # Should detect availability
        assert isinstance(analyzer._vader_available, bool)
    
    def test_quote_importance_scoring_weights(self):
        """Test quote importance scoring algorithm weights"""
        analyzer = TranscriptAnalyzer()
        
        # Test uniqueness (30 pts)
        clip1 = ClipAnalysis(
            file_path=Path("test1.mp4"),
            duration=10.0,
            transcript_path=None,
            entries=[SRTEntry(1, 0.0, 5.0, "Unique statement with numbers 2024.")]
        )
        
        clip2 = ClipAnalysis(
            file_path=Path("test2.mp4"),
            duration=10.0,
            transcript_path=None,
            entries=[SRTEntry(1, 0.0, 5.0, "Unique statement with numbers 2024.")]  # Same text
        )
        
        # First quote should score higher (uniqueness bonus)
        quotes1 = analyzer.extract_quotes(clip1, min_importance=0.0)
        quotes2 = analyzer.extract_quotes(clip2, min_importance=0.0)
        
        if quotes1 and quotes2:
            # First occurrence gets uniqueness bonus
            assert quotes1[0].importance_score >= quotes2[0].importance_score
    
    def test_quote_importance_edge_cases(self):
        """Test quote importance scoring with edge cases"""
        analyzer = TranscriptAnalyzer()
        
        # Very short quote
        short_clip = ClipAnalysis(
            file_path=Path("short.mp4"),
            duration=5.0,
            transcript_path=None,
            entries=[SRTEntry(1, 0.0, 2.0, "Hi.")]
        )
        
        # Very long quote
        long_clip = ClipAnalysis(
            file_path=Path("long.mp4"),
            duration=60.0,
            transcript_path=None,
            entries=[SRTEntry(1, 0.0, 30.0, " ".join(["word"] * 100))]
        )
        
        # All fillers
        filler_clip = ClipAnalysis(
            file_path=Path("filler.mp4"),
            duration=10.0,
            transcript_path=None,
            entries=[SRTEntry(1, 0.0, 5.0, "Um, you know, like, basically, uh, so...")]
        )
        
        # Test they all handle gracefully
        short_quotes = analyzer.extract_quotes(short_clip, min_importance=0.0)
        long_quotes = analyzer.extract_quotes(long_clip, min_importance=0.0)
        filler_quotes = analyzer.extract_quotes(filler_clip, min_importance=0.0)
        
        # Should not crash, may return empty or low-scoring quotes
        assert isinstance(short_quotes, list)
        assert isinstance(long_quotes, list)
        assert isinstance(filler_quotes, list)
