"""
Intelligent Rough Cut Engine
Analyzes transcripts and creates structured rough cuts for doc, interview, episode styles
Smart documentary features: NLP analysis, quote extraction, thematic grouping, B-roll matching
"""

import re
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

# Set up logger for warnings
logger = logging.getLogger(__name__)


class CutStyle(Enum):
    DOC = "doc"
    INTERVIEW = "interview"
    EPISODE = "episode"
    TUTORIAL = "tutorial"
    REVIEW = "review"           # NEW: Product reviews
    UNBOXING = "unboxing"       # NEW: Unboxing videos
    COMPARISON = "comparison"   # NEW: Side-by-side comparisons
    SETUP = "setup"             # NEW: Setup/installation guides
    EXPLAINER = "explainer"     # NEW: Concept explainers


@dataclass
class Segment:
    """A segment of a clip to include in rough cut"""
    source_file: Path
    start_time: float  # seconds
    end_time: float
    text: str
    speaker: Optional[str] = None
    topic: Optional[str] = None
    score: float = 0.0  # Quality/importance score
    segment_type: str = "content"  # content, intro, outro, broll_point


@dataclass
class SRTEntry:
    """Parsed SRT subtitle entry"""
    index: int
    start_time: float
    end_time: float
    text: str


@dataclass
class ClipAnalysis:
    """Analysis of a single clip"""
    file_path: Path
    duration: float
    transcript_path: Optional[Path]
    entries: List[SRTEntry] = field(default_factory=list)
    has_speech: bool = False
    speakers: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    best_moments: List[Segment] = field(default_factory=list)
    silence_regions: List[Tuple[float, float]] = field(default_factory=list)
    filler_regions: List[Tuple[float, float]] = field(default_factory=list)
    
    # Visual/quality analysis (optional - populated if analysis available)
    shot_type: Optional[str] = None  # wide, medium, close, extreme_close, broll
    content_type: Optional[str] = None  # talking_head, screen_recording, broll, graphics, action, static, establishing
    faces_detected: int = 0
    quality_score: Optional[float] = None  # 0-100
    is_shaky: bool = False
    exposure_rating: Optional[str] = None  # under, normal, over
    audio_level: Optional[str] = None  # silent, quiet, normal, loud
    
    # Filename convention metadata (parsed from filename)
    is_screen_recording: bool = False  # Detected from SCREEN_ prefix
    step_number: Optional[int] = None  # Extracted from STEP##_ pattern
    topic_tag: Optional[str] = None  # Extracted topic (SETUP_, CONFIG_, etc.)
    is_hook: bool = False  # Detected from HOOK_ prefix
    hook_flow_type: Optional[str] = None  # YouTube hook flow type (CH, AH, PSH, TPH, etc.)
    is_cta: bool = False  # Detected from CTA_ prefix
    is_mistake: bool = False  # Detected from MISTAKE_ or DELETE_ prefix
    take_number: Optional[int] = None  # Extracted from (N) or _TAKEN pattern
    
    # Audio marker metadata
    markers: List = field(default_factory=list)  # AudioMarker objects detected in transcript
    transcript_json_path: Optional[Path] = None  # Path to JSON transcript (for marker detection)


@dataclass
class Quote:
    """Extracted quote with importance scoring"""
    text: str
    start_time: float
    end_time: float
    importance_score: float  # 0-100
    topic: str
    emotion: str  # positive, negative, neutral
    speaker: Optional[str] = None
    clip: Optional['ClipAnalysis'] = None


@dataclass
class NaturalEditPoint:
    """Natural edit point (pause, sentence end, breath)"""
    timecode: float
    confidence: float  # 0-1
    edit_type: str  # pause, sentence_end, breath, combined
    near_sentence_end: bool = False
    has_breath: bool = False


@dataclass
class InterviewSegment:
    """Enhanced interview segment with transcript analysis"""
    clip: ClipAnalysis
    transcript: str
    quotes: List[Quote] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    emotion_score: float = 0.0  # -1 to 1
    natural_pauses: List[NaturalEditPoint] = field(default_factory=list)
    duration: float = 0.0
    keywords: List[str] = field(default_factory=list)


@dataclass
class Theme:
    """Thematic section for documentary"""
    name: str
    key_quotes: List[Quote] = field(default_factory=list)
    supporting_broll: List[ClipAnalysis] = field(default_factory=list)
    duration_target: float = 0.0
    order: int = 0
    description: str = ""


@dataclass
class RemovedSegment:
    """Segment that was removed from rough cut"""
    segment: Segment
    reason: str  # Why it was removed (low_score, duration_limit, etc.)
    score: float  # Original score
    transcript: Optional[str] = None
    visual_description: Optional[str] = None
    thumbnail_time: Optional[float] = None  # Timecode for thumbnail extraction


@dataclass
class ScoringConfig:
    """Centralized scoring thresholds for rough cut generation"""
    segment_threshold: float = 0.15  # Minimum score for segment inclusion
    quote_min_importance: float = 50.0  # Minimum importance for quote extraction
    duplicate_overlap_pct: float = 0.3  # Overlap percentage threshold for duplicates
    merge_gap_threshold_doc: float = 2.0  # Gap threshold for merging (documentary)
    merge_gap_threshold_episode: float = 1.0  # Gap threshold for merging (episode)
    merge_gap_threshold_tutorial: float = 0.5  # Gap threshold for merging (tutorial - aggressive)


@dataclass
class HookCandidate:
    """Candidate hook segment for YouTube retention optimization"""
    segment: Segment
    retention_score: float  # Predicted retention % (0-100)
    energy_score: float  # Audio energy level (0-1)
    clarity_score: float  # Clarity/no filler words (0-1)
    duration: float  # Duration in seconds
    hook_type: str  # value_prop, question, reveal, promise, etc.
    hook_flow_type: Optional[str] = None  # YouTube hook flow type (CH, AH, PSH, TPH, etc.)
    hook_phrase_present: bool = False  # Contains hook phrase pattern
    flow_performance_multiplier: float = 1.0  # Performance boost based on named flow type


@dataclass
class RoughCutPlan:
    """Complete rough cut plan"""
    style: CutStyle
    clips: List[ClipAnalysis]
    segments: List[Segment]
    total_duration: float
    structure: Dict[str, List[Segment]]  # Section name -> segments
    themes: List[Theme] = field(default_factory=list)  # Thematic organization
    narrative_arc: Dict[str, List[Segment]] = field(default_factory=dict)  # Hook, setup, act1, etc.
    removed_segments: List[RemovedSegment] = field(default_factory=list)  # Footage that was cut


class TranscriptAnalyzer:
    """Deep transcript analysis with NLP for smart documentary editing"""
    
    def __init__(self):
        self._spacy_available = self._check_spacy()
        self._textblob_available = self._check_textblob()
        self._vader_available = self._check_vader()
        self._seen_quotes: Set[str] = set()
        
        # Cache NLP model instances for performance
        self._vader_analyzer = None
        self._sentiment_cache: Dict[str, float] = {}  # Cache sentiment scores
        self._topic_cache: Dict[str, str] = {}  # Cache topic detection
        self._keyword_cache: Dict[str, List[str]] = {}  # Cache keyword extraction
        
    def _check_spacy(self) -> bool:
        """Check if spaCy is available"""
        try:
            import spacy
            # Try to load English model (will fail if not downloaded)
            try:
                self._nlp = spacy.load("en_core_web_sm")
                return True
            except OSError:
                # Model not downloaded, but spaCy is available
                return False
        except ImportError:
            return False
    
    def _check_textblob(self) -> bool:
        """Check if TextBlob is available"""
        try:
            from textblob import TextBlob
            return True
        except ImportError:
            return False
    
    def _check_vader(self) -> bool:
        """Check if VADER sentiment is available and initialize analyzer"""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._vader_analyzer = SentimentIntensityAnalyzer()  # Initialize once
            return True
        except ImportError:
            return False
    
    def extract_quotes(self, clip: ClipAnalysis, min_importance: Optional[float] = None) -> List[Quote]:
        """Extract important quotes from clip transcript
        
        Args:
            clip: Clip to analyze
            min_importance: Minimum importance score (uses scoring_config if None)
        """
        if min_importance is None:
            # Get from engine's scoring config if available
            min_importance = 50.0  # Default fallback
        """Extract key quotes from clip transcript with importance scoring"""
        quotes = []
        
        if not clip.entries:
            return quotes
        
        # Build full transcript
        full_text = ' '.join(e.text for e in clip.entries)
        
        # Split into sentences (simple approach)
        sentences = re.split(r'[.!?]+', full_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for entry in clip.entries:
            # Score this entry as a potential quote
            importance = self._calculate_quote_importance(entry.text, full_text)
            
            if importance >= min_importance:
                # Detect topic and emotion
                topic = self._detect_topic(entry.text)
                emotion = self._analyze_emotion(entry.text)
                
                quote = Quote(
                    text=entry.text,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    importance_score=importance,
                    topic=topic,
                    emotion=emotion,
                    clip=clip
                )
                quotes.append(quote)
                self._seen_quotes.add(entry.text.lower())
        
        return sorted(quotes, key=lambda x: x.importance_score, reverse=True)
    
    def _calculate_quote_importance(self, quote: str, full_text: str) -> float:
        """Calculate importance score for a quote (0-100) - optimized"""
        score = 0.0
        quote_lower = quote.lower()
        
        # Uniqueness (not repeated elsewhere) - 30 pts
        if quote_lower not in self._seen_quotes:
            score += 30.0
        
        # Information density (factual content) - 20 pts
        # Pre-compile regex patterns for better performance
        has_numbers = bool(re.search(r'\d+', quote))
        has_names = bool(re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', quote))  # Proper names
        has_dates = bool(re.search(r'\b(19|20)\d{2}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', quote, re.I))
        
        if has_numbers or has_names or has_dates:
            score += 20.0
        
        # Emotional impact (sentiment analysis) - 20 pts (cached)
        sentiment = self._analyze_sentiment(quote)
        score += abs(sentiment) * 20.0
        
        # Length (optimal 10-30 words) - 15 pts
        word_count = len(quote.split())
        if 10 <= word_count <= 30:
            score += 15.0
        elif word_count > 30:
            score += 10.0
        elif word_count >= 5:
            score += 5.0  # Short but valid
        
        # Question/engagement - 10 pts
        if '?' in quote:
            score += 10.0
        
        # Filler word penalty - only if excessive
        filler_count = 0
        filler_patterns = [
            r'\bum+\b', r'\buh+\b', r'\bah+\b', r'\blike\b', r'\byou know\b',
            r'\bso+\b', r'\bbasically\b', r'\bactually\b', r'\bi mean\b'
        ]
        for pattern in filler_patterns:
            if re.search(pattern, quote_lower):
                filler_count += 1
        
        # Only penalize if mostly filler (more than 2 instances)
        if filler_count > 2:
            score -= min(15.0, filler_count * 5.0)  # Max 15 point penalty
        
        return min(100.0, max(0.0, score))
    
    def _detect_topic(self, text: str) -> str:
        """Detect topic using NLP or keyword matching with caching"""
        # Check cache first
        text_key = text.lower().strip()[:100]  # Cache key (first 100 chars)
        if text_key in self._topic_cache:
            return self._topic_cache[text_key]
        
        topic = "general"
        
        if self._spacy_available and hasattr(self, '_nlp'):
            try:
                doc = self._nlp(text)
                # Extract named entities and key phrases
                entities = [ent.label_ for ent in doc.ents]
                if entities:
                    # Return most common entity type
                    from collections import Counter
                    topic = Counter(entities).most_common(1)[0][0]
            except:
                pass
        
        # Fallback to keyword matching if spaCy didn't find topic
        if topic == "general":
            text_lower = text.lower()
            topic_keywords = {
                'introduction': ['introduce', 'background', 'context', 'start'],
                'problem': ['problem', 'issue', 'challenge', 'difficulty', 'struggle'],
                'personal_stories': ['remember', 'story', 'happened', 'when i', 'my'],
                'expert_opinions': ['research', 'study', 'data', 'evidence', 'prove'],
                'solutions': ['solution', 'solve', 'fix', 'improve', 'help', 'way'],
                'conclusion': ['conclusion', 'finally', 'summary', 'wrap up', 'end']
            }
            
            for topic_name, keywords in topic_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    topic = topic_name
                    break
        
        # Cache result
        self._topic_cache[text_key] = topic
        return topic
    
    def _analyze_emotion(self, text: str) -> str:
        """Analyze emotion (positive, negative, neutral)"""
        sentiment = self._analyze_sentiment(text)
        
        if sentiment > 0.1:
            return "positive"
        elif sentiment < -0.1:
            return "negative"
        else:
            return "neutral"
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment score (-1 to 1) with caching"""
        # Check cache first
        text_key = text.lower().strip()
        if text_key in self._sentiment_cache:
            return self._sentiment_cache[text_key]
        
        sentiment = 0.0
        
        # Try VADER first (better for social media/casual text)
        if self._vader_available and self._vader_analyzer:
            try:
                scores = self._vader_analyzer.polarity_scores(text)
                sentiment = scores['compound']  # -1 to 1
            except:
                pass
        
        # Fallback to TextBlob if VADER didn't work
        if sentiment == 0.0 and self._textblob_available:
            try:
                from textblob import TextBlob
                blob = TextBlob(text)
                sentiment = blob.sentiment.polarity  # -1 to 1
            except:
                pass
        
        # Simple heuristic fallback if both failed
        if sentiment == 0.0:
            positive_words = ['love', 'happy', 'great', 'wonderful', 'amazing', 'best', 'good', 'excellent']
            negative_words = ['hate', 'sad', 'terrible', 'awful', 'worst', 'bad', 'horrible', 'difficult']
            
            text_lower = text_key
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = 0.3
            elif negative_count > positive_count:
                sentiment = -0.3
            else:
                sentiment = 0.0
        
        # Cache result
        self._sentiment_cache[text_key] = sentiment
        return sentiment
    
    def extract_topics(self, clips: List[ClipAnalysis]) -> Dict[str, List[Quote]]:
        """Extract and group quotes by topics"""
        all_quotes = []
        
        # Extract quotes from all clips
        for clip in clips:
            if clip.entries:
                quotes = self.extract_quotes(clip, min_importance=60.0)
                all_quotes.extend(quotes)
        
        # Group by topic
        topics: Dict[str, List[Quote]] = {}
        for quote in all_quotes:
            if quote.topic not in topics:
                topics[quote.topic] = []
            topics[quote.topic].append(quote)
        
        # Sort quotes within each topic by importance
        for topic in topics:
            topics[topic].sort(key=lambda x: x.importance_score, reverse=True)
        
        return topics
    
    def find_natural_edit_points(self, clip: ClipAnalysis) -> List[NaturalEditPoint]:
        """Find natural edit points (pauses, sentence ends, breaths)"""
        points = []
        
        if not clip.entries:
            return points
        
        # Find silence gaps (pauses)
        pauses = []
        for i in range(len(clip.entries) - 1):
            gap_start = clip.entries[i].end_time
            gap_end = clip.entries[i + 1].start_time
            gap_duration = gap_end - gap_start
            
            if gap_duration > 0.3:  # More than 0.3 seconds
                pauses.append({
                    'time': gap_start + (gap_duration / 2),
                    'duration': gap_duration,
                    'confidence': min(1.0, gap_duration / 2.0)  # Longer pause = higher confidence
                })
        
        # Find sentence boundaries from transcript
        sentence_ends = []
        for entry in clip.entries:
            text = entry.text.strip()
            # Check if ends with sentence punctuation
            if text and text[-1] in '.!?':
                sentence_ends.append(entry.end_time)
        
        # Combine: good edit point = pause near sentence end
        # Optimize: pre-sort sentence_ends for faster lookup
        sentence_ends_sorted = sorted(sentence_ends)
        
        for pause in pauses:
            # Binary search for nearest sentence end (faster than linear search)
            near_sentence = False
            pause_time = pause['time']
            
            # Check if pause is near any sentence end (within 1.0s)
            for se in sentence_ends_sorted:
                if abs(pause_time - se) < 1.0:
                    near_sentence = True
                    break
                elif se > pause_time + 1.0:  # Early exit optimization
                    break
            
            # Higher confidence if pause is longer and near sentence end
            confidence = pause['confidence']
            if near_sentence:
                confidence = min(1.0, confidence * 1.5)
            
            points.append(NaturalEditPoint(
                timecode=pause['time'],
                confidence=confidence,
                edit_type="combined" if near_sentence else "pause",
                near_sentence_end=near_sentence,
                has_breath=False  # Would need audio analysis for this
            ))
        
        return sorted(points, key=lambda x: -x.confidence)
    
    def analyze_interview_segment(self, clip: ClipAnalysis) -> InterviewSegment:
        """Create enhanced interview segment with full analysis"""
        # Build transcript
        transcript = ' '.join(e.text for e in clip.entries) if clip.entries else ""
        
        # Extract quotes with lower threshold for better coverage
        quotes = self.extract_quotes(clip, min_importance=50.0)  # Lowered from 70.0
        
        # Extract topics
        topics = self._extract_topics_nlp(transcript) if transcript else []
        
        # Calculate emotion score
        emotion_score = self._analyze_sentiment(transcript) if transcript else 0.0
        
        # Find natural pauses
        natural_pauses = self.find_natural_edit_points(clip)
        
        # Extract keywords
        keywords = self._extract_keywords(transcript) if transcript else []
        
        return InterviewSegment(
            clip=clip,
            transcript=transcript,
            quotes=quotes,
            topics=topics,
            emotion_score=emotion_score,
            natural_pauses=natural_pauses,
            duration=clip.duration,
            keywords=keywords
        )
    
    def _extract_topics_nlp(self, text: str) -> List[str]:
        """Extract topics using NLP"""
        topics = []
        
        if self._spacy_available and hasattr(self, '_nlp'):
            try:
                doc = self._nlp(text)
                # Extract noun phrases and named entities as topics
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) <= 3:  # Short phrases only
                        topics.append(chunk.text.lower())
                
                # Also get named entities
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT']:
                        topics.append(ent.text.lower())
            except:
                pass
        
        # Fallback to keyword-based topic detection
        if not topics:
            topic_keywords = {
                'introduction': ['introduce', 'background', 'context'],
                'problem': ['problem', 'issue', 'challenge'],
                'personal_stories': ['remember', 'story', 'happened'],
                'solutions': ['solution', 'solve', 'fix', 'help']
            }
            
            text_lower = text.lower()
            for topic, keywords in topic_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    topics.append(topic)
        
        return list(set(topics))  # Remove duplicates
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text with caching"""
        # Check cache first
        text_key = text.lower().strip()[:200]  # Cache key (first 200 chars)
        if text_key in self._keyword_cache:
            return self._keyword_cache[text_key]
        
        keywords = []
        
        if self._spacy_available and hasattr(self, '_nlp'):
            try:
                doc = self._nlp(text)
                # Get nouns and proper nouns
                for token in doc:
                    if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                        if len(token.text) > 3:  # Skip very short words
                            keywords.append(token.text.lower())
            except:
                pass
        
        # Fallback: simple word frequency
        if not keywords:
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            from collections import Counter
            common_words = Counter(words).most_common(10)
            keywords = [word for word, count in common_words]
        
        keywords = keywords[:20]  # Limit to top 20
        
        # Cache result
        self._keyword_cache[text_key] = keywords
        return keywords
    
    def detect_feature_mentions(self, clip: ClipAnalysis) -> List[Segment]:
        """Detect product feature mentions in transcript"""
        segments = []
        if not clip.entries:
            return segments
        
        feature_keywords = [
            r'\bfeature\b', r'\bhas\b', r'\bincludes\b', r'\bcomes with\b',
            r'\bspec\b', r'\bspecification\b', r'\bcapability\b', r'\bcan\b',
            r'\bsupports\b', r'\boffers\b', r'\bprovides\b', r'\bequipped with\b'
        ]
        
        for entry in clip.entries:
            text_lower = entry.text.lower()
            for pattern in feature_keywords:
                if re.search(pattern, text_lower):
                    segments.append(Segment(
                        source_file=clip.file_path,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=entry.text,
                        segment_type="feature",
                        score=0.7  # High score for feature mentions
                    ))
                    break
        
        return segments
    
    def detect_pros_cons(self, clip: ClipAnalysis) -> Tuple[List[Segment], List[Segment]]:
        """Detect pros and cons statements"""
        pros = []
        cons = []
        
        if not clip.entries:
            return pros, cons
        
        pros_keywords = [
            r'\bgreat\b', r'\bexcellent\b', r'\blove\b', r'\bbest\b', r'\bamazing\b',
            r'\bfantastic\b', r'\bperfect\b', r'\boutstanding\b', r'\bimpressive\b',
            r'\bpro\b', r'\badvantage\b', r'\bplus\b', r'\bgood\b', r'\bstrong\b'
        ]
        
        cons_keywords = [
            r'\bbut\b', r'\bhowever\b', r'\bissue\b', r'\bproblem\b', r'\bdisappointing\b',
            r'\bweak\b', r'\bpoor\b', r'\bbad\b', r'\bcon\b', r'\bdisadvantage\b',
            r'\bminus\b', r'\bconcern\b', r'\bworried\b', r'\bunfortunately\b'
        ]
        
        for entry in clip.entries:
            text_lower = entry.text.lower()
            
            # Check for pros
            for pattern in pros_keywords:
                if re.search(pattern, text_lower):
                    pros.append(Segment(
                        source_file=clip.file_path,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=entry.text,
                        segment_type="pro",
                        score=0.6
                    ))
                    break
            
            # Check for cons
            for pattern in cons_keywords:
                if re.search(pattern, text_lower):
                    cons.append(Segment(
                        source_file=clip.file_path,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=entry.text,
                        segment_type="con",
                        score=0.6
                    ))
                    break
        
        return pros, cons
    
    def detect_reveals(self, clip: ClipAnalysis) -> List[Segment]:
        """Detect unboxing reveal moments"""
        segments = []
        if not clip.entries:
            return segments
        
        reveal_keywords = [
            r'\bwow\b', r'\blook at this\b', r'\bhere it is\b', r'\bhere we go\b',
            r'\bcheck this out\b', r'\bamazing\b', r'\bincredible\b', r'\bunbox\b',
            r'\bopening\b', r'\bfirst look\b', r'\binitial thoughts\b', r'\bopening it\b'
        ]
        
        for entry in clip.entries:
            text_lower = entry.text.lower()
            for pattern in reveal_keywords:
                if re.search(pattern, text_lower):
                    # Boost score for emotional reactions
                    score = 0.8 if any(word in text_lower for word in ['wow', 'amazing', 'incredible']) else 0.6
                    segments.append(Segment(
                        source_file=clip.file_path,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=entry.text,
                        segment_type="reveal",
                        score=score
                    ))
                    break
        
        return segments
    
    def detect_comparisons(self, clip: ClipAnalysis) -> List[Segment]:
        """Detect comparison statements"""
        segments = []
        if not clip.entries:
            return segments
        
        comparison_keywords = [
            r'\bvs\b', r'\bversus\b', r'\bcompared to\b', r'\bcompared with\b',
            r'\bbetter than\b', r'\bworse than\b', r'\bfaster than\b', r'\bslower than\b',
            r'\bmore\b.*\bthan\b', r'\bless\b.*\bthan\b', r'\bdifference\b', r'\bversus\b'
        ]
        
        for entry in clip.entries:
            text_lower = entry.text.lower()
            for pattern in comparison_keywords:
                if re.search(pattern, text_lower):
                    segments.append(Segment(
                        source_file=clip.file_path,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=entry.text,
                        segment_type="comparison",
                        score=0.7
                    ))
                    break
        
        return segments
    
    def detect_concepts(self, clip: ClipAnalysis) -> List[Segment]:
        """Detect concept introduction segments"""
        segments = []
        if not clip.entries:
            return segments
        
        concept_keywords = [
            r'\blet me explain\b', r'\bhere\'s how\b', r'\bthe concept is\b', r'\bbasically\b',
            r'\bin simple terms\b', r'\bwhat this means\b', r'\bto understand\b', r'\bthink of it\b',
            r'\bimagine\b', r'\bessentially\b', r'\bthe idea is\b', r'\bconcept\b'
        ]
        
        for entry in clip.entries:
            text_lower = entry.text.lower()
            for pattern in concept_keywords:
                if re.search(pattern, text_lower):
                    segments.append(Segment(
                        source_file=clip.file_path,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=entry.text,
                        segment_type="concept",
                        score=0.7
                    ))
                    break
        
        return segments


class RoughCutEngine:
    """Creates intelligent rough cuts from footage + transcripts"""

    # Filler words to detect and optionally trim
    FILLER_WORDS = [
        r'\bum+\b', r'\buh+\b', r'\bah+\b', r'\blike\b', r'\byou know\b',
        r'\bso+\b', r'\bbasically\b', r'\bactually\b', r'\bi mean\b'
    ]

    # Topic detection keywords
    TOPIC_KEYWORDS = {
        'family': ['mom', 'dad', 'father', 'mother', 'brother', 'sister', 'grandma', 'grandmother', 'grandpa', 'grandfather', 'family', 'parents'],
        'memories': ['remember', 'memory', 'memories', 'used to', 'back then', 'when i was', 'years ago'],
        'emotions': ['love', 'happy', 'sad', 'miss', 'wish', 'hope', 'dream', 'feel', 'feeling'],
        'stories': ['tell you', 'story', 'happened', 'one time', 'once upon'],
        'advice': ['should', 'important', 'learn', 'advice', 'lesson', 'wisdom'],
        'future': ['will', 'going to', 'want to', 'plan', 'future', 'someday'],
        'past': ['was', 'were', 'did', 'had', 'ago', 'before', 'childhood'],
    }

    # Style-specific structure templates
    STYLE_STRUCTURES = {
        CutStyle.DOC: {
            'sections': ['opening', 'context', 'main_story', 'reflection', 'closing'],
            'pacing': 'slow',  # Let moments breathe
            'min_segment': 3.0,  # Lower minimum to keep shorter moments
            'max_segment': 90.0,  # Allow longer uninterrupted segments
            'target_ratio': 0.8,  # Keep 80% of raw footage - documentary style
            'pre_handle': 1.0,   # 1 second before speech (see speaker)
            'post_handle': 0.5,  # 0.5 seconds after (breathing room)
        },
        CutStyle.INTERVIEW: {
            'sections': ['intro', 'q1', 'q2', 'q3', 'highlight', 'closing'],
            'pacing': 'medium',
            'min_segment': 3.0,
            'max_segment': 45.0,
            'target_ratio': 0.5,
            'pre_handle': 0.75,  # See speaker before answer
            'post_handle': 0.4,  # Brief pause after
        },
        CutStyle.EPISODE: {
            'sections': ['hook', 'intro', 'main_content', 'climax', 'outro', 'cta'],
            'pacing': 'fast',  # Quick cuts, high energy
            'min_segment': 2.0,
            'max_segment': 30.0,
            'target_ratio': 0.4,
            'pre_handle': 0.3,   # Tight cuts for energy
            'post_handle': 0.2,  # Quick transitions
        },
        CutStyle.TUTORIAL: {
            'sections': ['hook', 'intro', 'step_1', 'step_2', 'step_3', 'summary', 'cta'],
            'pacing': 'very_fast',  # Aggressive jump cuts
            'min_segment': 1.0,  # Allow very short segments
            'max_segment': 20.0,  # Shorter max for tutorials
            'target_ratio': 0.3,  # Keep only 30% (aggressive)
            'pre_handle': 0.1,   # Minimal handles
            'post_handle': 0.1,
            'jump_cut_threshold': 0.5,  # Remove gaps <0.5s
            'mistake_detection': True,
            'step_detection': True,
            'screen_recording_aware': True,
            'hook_optimization': True,
            'ad_break_interval': 120,  # Ad every 2 minutes
            'cta_timing': 0.75,  # CTA at 75% through video
        },
        CutStyle.REVIEW: {
            'sections': ['hook', 'intro', 'overview', 'features', 'pros', 'cons', 'verdict', 'cta'],
            'pacing': 'medium_fast',  # Balanced - informative but engaging
            'min_segment': 2.5,
            'max_segment': 45.0,  # Allow longer feature explanations
            'target_ratio': 0.5,  # Keep 50% - comprehensive but edited
            'pre_handle': 0.4,
            'post_handle': 0.3,
            'feature_detection': True,  # Detect feature mentions
            'pros_cons_detection': True,  # Identify pros/cons statements
            'verdict_optimization': True,  # Prioritize conclusion segments
            'broll_matching': True,  # Match B-roll to feature descriptions
        },
        CutStyle.UNBOXING: {
            'sections': ['hook', 'intro', 'unboxing', 'first_look', 'initial_thoughts', 'cta'],
            'pacing': 'fast',  # High energy, quick reveals
            'min_segment': 1.5,
            'max_segment': 25.0,
            'target_ratio': 0.4,  # Keep 40% - fast-paced
            'pre_handle': 0.2,  # Tight cuts
            'post_handle': 0.2,
            'reveal_detection': True,  # Detect "wow" moments, reveals
            'reaction_prioritization': True,  # Prioritize emotional reactions
            'unboxing_sequence': True,  # Maintain unboxing order
        },
        CutStyle.COMPARISON: {
            'sections': ['hook', 'intro', 'product_a', 'product_b', 'side_by_side', 'winner', 'cta'],
            'pacing': 'medium',  # Need time to process comparisons
            'min_segment': 3.0,
            'max_segment': 60.0,  # Allow longer comparison segments
            'target_ratio': 0.6,  # Keep 60% - comprehensive comparison
            'pre_handle': 0.5,
            'post_handle': 0.4,
            'comparison_detection': True,  # Detect "vs", "compared to", "better than"
            'product_switching': True,  # Alternate between products A and B
            'spec_extraction': True,  # Extract specification mentions
        },
        CutStyle.SETUP: {
            'sections': ['hook', 'intro', 'prerequisites', 'step_1', 'step_2', 'step_3', 'verification', 'troubleshooting', 'cta'],
            'pacing': 'medium',  # Clear, methodical
            'min_segment': 2.0,
            'max_segment': 30.0,
            'target_ratio': 0.5,  # Keep 50% - comprehensive but edited
            'pre_handle': 0.3,
            'post_handle': 0.3,
            'step_detection': True,  # Detect step indicators
            'error_detection': True,  # Detect mistakes/corrections
            'screen_recording_aware': True,  # Prioritize screen recordings
            'command_extraction': True,  # Extract commands/code snippets
        },
        CutStyle.EXPLAINER: {
            'sections': ['hook', 'intro', 'concept_intro', 'explanation', 'examples', 'summary', 'cta'],
            'pacing': 'slow_medium',  # Educational, needs time to absorb
            'min_segment': 4.0,  # Longer segments for concepts
            'max_segment': 90.0,  # Allow extended explanations
            'target_ratio': 0.7,  # Keep 70% - comprehensive explanations
            'pre_handle': 0.6,  # More breathing room
            'post_handle': 0.5,
            'concept_detection': True,  # Detect concept introductions
            'example_detection': True,  # Identify example segments
            'visual_aid_matching': True,  # Match graphics/B-roll to explanations
        },
    }

    def __init__(self, scoring_config: Optional[ScoringConfig] = None):
        self.clips: List[ClipAnalysis] = []
        self.transcript_analyzer = TranscriptAnalyzer()
        self.interview_segments: List[InterviewSegment] = []
        self.themes: List[Theme] = []
        self.scoring_config = scoring_config or ScoringConfig()

    def _get_base_filename(self, file_path: Path) -> str:
        """Get base filename without normalized/duplicate suffixes
        
        Handles:
        - _normalized suffix
        - (1), (2) duplicate markers
        - _1_normalized, _2_normalized patterns
        """
        name = file_path.stem
        import re
        # Remove normalized suffix (handles _normalized, _1_normalized, etc.)
        name = re.sub(r'_?\d*_normalized$', '', name)
        # Remove duplicate markers like (1), (2), etc.
        name = re.sub(r'\s*\(\d+\)\s*$', '', name)
        return name.lower()
    
    def analyze_clips(self, footage_dir: Path, auto_transcribe: bool = True) -> List[ClipAnalysis]:
        """Analyze all clips and their transcripts
        
        Args:
            footage_dir: Directory containing video files
            auto_transcribe: Automatically transcribe clips without transcripts
        """
        # Ensure footage_dir is a Path object
        footage_dir = Path(footage_dir)
        
        self.clips = []

        # Find all video files (recursively search subdirectories)
        video_files = []
        for ext in ['*.mov', '*.mp4', '*.MOV', '*.MP4', '*.mxf', '*.MXF']:
            video_files.extend(footage_dir.rglob(ext))  # Use rglob for recursive search
        
        # Filter out ONLY normalized versions if original exists
        # Keep ALL numbered versions (1), (2), etc. - they're different takes!
        # Only remove normalized versions when we have the original
        filtered_files = []
        
        # Collect all non-normalized files (including numbered versions)
        originals = [vf for vf in video_files if "_normalized" not in vf.stem]
        
        # Always include all originals (including numbered versions like (1), (2))
        filtered_files.extend(originals)
        
        # For normalized files, only include if original doesn't exist
        # Filter: prefer normalized files, exclude non-normalized if normalized exists
        normalized_map = {}  # base_name -> normalized_file
        non_normalized_map = {}  # base_name -> non_normalized_file
        
        for vf in video_files:
            # Get base name (normalize the name by removing _normalized and (N) suffixes)
            base_name = vf.stem.replace("_normalized", "")
            base_name = re.sub(r'\s*\(\d+\)\s*$', '', base_name)
            
            if "_normalized" in vf.stem:
                if base_name not in normalized_map:
                    normalized_map[base_name] = vf
            else:
                if base_name not in non_normalized_map:
                    non_normalized_map[base_name] = vf
        
        # Prefer normalized files, fall back to non-normalized if no normalized exists
        filtered_files = []
        for base_name in set(list(normalized_map.keys()) + list(non_normalized_map.keys())):
            if base_name in normalized_map:
                filtered_files.append(normalized_map[base_name])
            elif base_name in non_normalized_map:
                filtered_files.append(non_normalized_map[base_name])
        
        video_files = filtered_files

        for video_file in sorted(video_files):
            # Ensure audio is normalized to -14 LUFS (YouTube standard) before analysis
            # Each clip is normalized independently to ensure consistent levels
            normalized_file = self._ensure_normalized_audio(video_file, target_lufs=-14.0)
            file_to_analyze = normalized_file if normalized_file else video_file
            
            analysis = self._analyze_single_clip(file_to_analyze)
            
            # Auto-transcribe if no transcript found and auto_transcribe is enabled
            if auto_transcribe and not analysis.transcript_path and not analysis.entries:
                # Generate transcript with JSON for marker detection
                transcript_path = self._generate_transcript(video_file, include_json=True)
                if transcript_path:
                    analysis.transcript_path = transcript_path
                    analysis.entries = self._parse_srt(transcript_path)
                    analysis.has_speech = len(analysis.entries) > 0
                    
                    # Find JSON transcript path for marker detection
                    # JSON file is named: {base}_transcript.json
                    json_path = transcript_path.parent / f"{transcript_path.stem}_transcript.json"
                    if not json_path.exists():
                        # Try alternative: remove .srt extension and add _transcript.json
                        base_name = transcript_path.stem.replace('.srt', '')
                        json_path = transcript_path.parent / f"{base_name}_transcript.json"
                    if json_path.exists():
                        analysis.transcript_json_path = json_path
                    
                    # Re-analyze with transcript
                    if analysis.entries:
                        full_text = ' '.join(e.text for e in analysis.entries)
                        analysis.topics = self._detect_topics(full_text)
                        analysis.silence_regions = self._find_silence_regions(analysis.entries, analysis.duration)
                        analysis.filler_regions = self._find_filler_regions(analysis.entries)
                        analysis.best_moments = self._find_best_moments(analysis)
            
            self.clips.append(analysis)

        return self.clips
    
    def _generate_transcript(self, video_path: Path, include_json: bool = False) -> Optional[Path]:
        """Generate transcript using Whisper if available
        
        Args:
            video_path: Video file to transcribe
            include_json: If True, also generate JSON with word-level timestamps (for audio markers)
        """
        try:
            from studioflow.core.transcription import TranscriptionService
            service = TranscriptionService()
            
            formats = ["srt", "json"] if include_json else ["srt"]
            result = service.transcribe(video_path, model="base", output_formats=formats)
            
            if result.get("success") and "srt" in result.get("output_files", {}):
                return result["output_files"]["srt"]
        except Exception as e:
            print(f"Warning: Could not auto-transcribe {video_path.name}: {e}")
        
        return None
    
    def _ensure_normalized_audio(self, video_file: Path, target_lufs: float = -14.0) -> Optional[Path]:
        """Ensure audio is normalized to target LUFS (YouTube standard: -14 LUFS)
        
        Returns normalized file path if normalization was needed/applied, None if already normalized.
        """
        from .ffmpeg import FFmpegProcessor
        
        # Check if already normalized (has _normalized in name or check LUFS)
        if "_normalized" in video_file.stem:
            # Already normalized, use as-is
            return None
        
        # Check current LUFS level
        current_lufs = self._get_audio_lufs(video_file)
        if current_lufs is None:
            # Can't measure, assume needs normalization
            pass
        elif abs(current_lufs - target_lufs) < 0.5:
            # Already at target level (within 0.5 LUFS tolerance)
            return None
        
        # Normalize audio
        normalized_path = video_file.parent / f"{video_file.stem}_normalized{video_file.suffix}"
        
        # Skip if normalized version already exists
        if normalized_path.exists():
            return normalized_path
        
        # Normalize to target LUFS
        result = FFmpegProcessor.normalize_audio(video_file, normalized_path, target_lufs=target_lufs)
        
        if result.success:
            return normalized_path
        else:
            # Normalization failed, use original
            return None
    
    def _get_audio_lufs(self, video_file: Path) -> Optional[float]:
        """Get current audio LUFS level"""
        import subprocess
        import re
        import json
        
        try:
            cmd = [
                "ffmpeg", "-i", str(video_file),
                "-af", "loudnorm=I=-14:print_format=json",
                "-f", "null", "-"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Extract loudnorm stats from stderr
            json_match = re.search(r'\{[^}]+\}', result.stderr[::-1])
            if json_match:
                stats = json.loads(json_match.group()[::-1])
                return float(stats.get('input_i', -70))
        except:
            pass
        
        return None

    def _analyze_single_clip(self, video_path: Path) -> ClipAnalysis:
        """Analyze a single clip"""
        import subprocess

        # Get duration
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'json', str(video_path)
            ], capture_output=True, text=True)
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
        except:
            duration = 0.0

        # Find transcript
        srt_path = video_path.with_suffix('.srt')
        if not srt_path.exists():
            srt_path = video_path.parent / f"{video_path.stem}.srt"

        # Infer visual/quality attributes (optional - can be enhanced with ML later)
        shot_type = self._infer_shot_type(video_path, duration)
        content_type = self._infer_content_type(video_path)
        quality_score = self._estimate_quality_score(video_path, duration)
        is_shaky = self._detect_shake(video_path)
        exposure_rating = self._analyze_exposure(video_path)
        audio_level = self._analyze_audio_level(video_path)
        
        # Parse filename convention metadata
        filename_metadata = self._parse_filename_convention(video_path)
        
        analysis = ClipAnalysis(
            file_path=video_path,
            duration=duration,
            transcript_path=srt_path if srt_path.exists() else None,
            shot_type=shot_type,
            content_type=content_type,
            quality_score=quality_score,
            is_shaky=is_shaky,
            exposure_rating=exposure_rating,
            audio_level=audio_level,
            is_screen_recording=filename_metadata['is_screen_recording'],
            step_number=filename_metadata['step_number'],
            topic_tag=filename_metadata['topic_tag'],
            is_hook=filename_metadata['is_hook'],
            hook_flow_type=filename_metadata['hook_flow_type'],
            is_cta=filename_metadata['is_cta'],
            is_mistake=filename_metadata['is_mistake'],
            take_number=filename_metadata['take_number']
        )

        # Parse transcript if available
        if analysis.transcript_path and analysis.transcript_path.exists():
            analysis.entries = self._parse_srt(analysis.transcript_path)
            analysis.has_speech = len(analysis.entries) > 0

            # Analyze content
            if analysis.entries:
                full_text = ' '.join(e.text for e in analysis.entries)
                analysis.topics = self._detect_topics(full_text)
                analysis.silence_regions = self._find_silence_regions(analysis.entries, duration)
                analysis.filler_regions = self._find_filler_regions(analysis.entries)
                analysis.best_moments = self._find_best_moments(analysis)

        return analysis
    
    def _infer_shot_type(self, video_path: Path, duration: float) -> Optional[str]:
        """Infer shot type from filename and duration"""
        name_lower = video_path.stem.lower()
        name_upper = video_path.stem.upper()
        
        # Check filename patterns (priority order)
        if 'wide' in name_lower or 'establishing' in name_lower:
            return "wide"
        elif 'close' in name_lower or 'cu' in name_lower:
            return "close"
        elif 'medium' in name_lower or 'mc' in name_lower:
            return "medium"
        elif 'broll' in name_lower or 'b-roll' in name_lower or name_upper.startswith('BROLL_') or name_upper.startswith('B_'):
            return "broll"
        elif duration < 10:
            return "broll"  # Short clips are often B-roll
        else:
            return "medium"  # Default
    
    def _infer_content_type(self, video_path: Path) -> Optional[str]:
        """Infer content type from filename using convention"""
        name_lower = video_path.stem.lower()
        name_upper = video_path.stem.upper()
        
        # Check for screen recording (highest priority)
        if (name_upper.startswith('SCREEN_') or name_upper.startswith('SCR_') or 
            'screen' in name_lower or 'recording' in name_lower or 'capture' in name_lower):
            return "screen_recording"
        
        # Check for B-roll
        if (name_upper.startswith('BROLL_') or name_upper.startswith('B_') or
            'broll' in name_lower or 'b-roll' in name_lower):
            return "broll"
        
        # Check for graphics
        if name_upper.startswith('GFX_') or name_upper.startswith('GRAPHICS_'):
            return "graphics"
        
        # Check for talking head (camera footage)
        if (name_upper.startswith('CAM_') or name_upper.startswith('CAMERA_') or
            'talking' in name_lower or 'interview' in name_lower or 'talking_head' in name_lower):
            return "talking_head"
        
        # Check other content types
        if 'action' in name_lower or 'movement' in name_lower:
            return "action"
        elif 'static' in name_lower or 'still' in name_lower:
            return "static"
        elif 'establishing' in name_lower:
            return "establishing"
        
        # Default: assume talking head if no prefix (camera footage)
        return "talking_head"
    
    def _estimate_quality_score(self, video_path: Path, duration: float) -> Optional[float]:
        """
        Estimate quality score (fallback metric)
        
        Note: This is a fallback metric when audio markers are not available.
        Audio markers take precedence for clip ordering and selection.
        Priority: 1) Audio markers, 2) quality_score (this method), 3) File-based sorting
        """
        """Estimate quality score (0-100) based on filename convention and heuristics"""
        score = 50.0  # Base score
        name_lower = video_path.stem.lower()
        name_upper = video_path.stem.upper()
        
        # Filename quality indicators (convention-based)
        if (name_upper.startswith('BEST_') or name_upper.startswith('SELECT_') or 
            name_upper.startswith('HERO_') or name_upper.startswith('FINAL_') or
            'best' in name_lower or 'select' in name_lower or 'hero' in name_lower):
            score += 25  # High quality markers
        elif name_upper.startswith('TEST_') or name_upper.startswith('BACKUP_') or 'test' in name_lower:
            score -= 25  # Lower priority
        
        # Hook/opening markers (high value for tutorials)
        if name_upper.startswith('HOOK_') or name_upper.startswith('OPENING_'):
            score += 15
        
        # Duration bonus (longer = more content, but not always better)
        if duration > 60:
            score += 5
        elif duration > 30:
            score += 3
        
        # Step markers (organized content = higher quality)
        if 'STEP' in name_upper or name_upper.startswith('S') and any(c.isdigit() for c in name_upper[:5]):
            score += 5
        
        return min(100.0, max(0.0, score))
    
    def _detect_shake(self, video_path: Path) -> bool:
        """Detect if footage is shaky (simplified heuristic)"""
        name_lower = video_path.stem.lower()
        # Would use motion vector analysis in production
        return "handheld" in name_lower or "shaky" in name_lower
    
    def _analyze_exposure(self, video_path: Path) -> Optional[str]:
        """Analyze exposure levels (simplified - would use histogram in production)"""
        # For now, return None (unknown) - can be enhanced with FFmpeg histogram analysis
        return None
    
    def _analyze_audio_level(self, video_path: Path) -> Optional[str]:
        """Analyze audio levels (simplified)"""
        # Would use FFmpeg volumedetect in production
        # For now, return None (unknown) - can be enhanced
        return None
    
    def _parse_filename_convention(self, video_path: Path) -> Dict[str, any]:
        """Parse filename convention to extract metadata
        
        Returns:
            Dict with parsed metadata: is_screen_recording, step_number, topic_tag, etc.
        """
        filename = video_path.stem
        name_upper = filename.upper()
        name_lower = filename.lower()
        
        metadata = {
            'is_screen_recording': False,
            'step_number': None,
            'topic_tag': None,
            'is_hook': False,
            'hook_flow_type': None,
            'is_cta': False,
            'is_mistake': False,
            'take_number': None
        }
        
        # Screen recording detection
        if (name_upper.startswith('SCREEN_') or name_upper.startswith('SCR_') or
            'screen' in name_lower or 'recording' in name_lower or 'capture' in name_lower):
            metadata['is_screen_recording'] = True
        
        # Step number detection (STEP##_ or S##_)
        step_match = re.search(r'STEP(\d+)', name_upper)
        if not step_match:
            step_match = re.search(r'^S(\d+)_', name_upper)
        if step_match:
            metadata['step_number'] = int(step_match.group(1))
        
        # Topic tag detection (SETUP_, CONFIG_, DEMO_, etc.)
        topic_patterns = [
            r'^(SETUP|CONFIG|DEMO|INTRO|OUTRO|EXPLAIN|TROUBLESHOOT|ADVANCED)_',
            r'_(SETUP|CONFIG|DEMO|INTRO|OUTRO|EXPLAIN|TROUBLESHOOT|ADVANCED)_'
        ]
        for pattern in topic_patterns:
            topic_match = re.search(pattern, name_upper)
            if topic_match:
                metadata['topic_tag'] = topic_match.group(1).lower()
                break
        
        # Hook detection and flow type
        if name_upper.startswith('HOOK_') or name_upper.startswith('OPENING_') or 'hook' in name_lower:
            metadata['is_hook'] = True
        
        # YouTube Hook Flow Types (recognized patterns)
        # These are proven hook patterns that perform well on YouTube
        hook_flow_patterns = {
            'CH': r'\bHOOK_CH\b|\bCH_HOOK\b|_CH_|^CH_',  # Curiosity Hook
            'AH': r'\bHOOK_AH\b|\bAH_HOOK\b|_AH_|^AH_',  # Action Hook
            'PSH': r'\bHOOK_PSH\b|\bPSH_HOOK\b|_PSH_|^PSH_',  # Problem-Solution Hook
            'TPH': r'\bHOOK_TPH\b|\bTPH_HOOK\b|_TPH_|^TPH_',  # Time-Promise Hook
            'COH': r'\bHOOK_COH\b|\bCOH_HOOK\b|_COH_|^COH_',  # Contrarian Hook
            'VH': r'\bHOOK_VH\b|\bVH_HOOK\b|_VH_|^VH_',  # Visual Hook
            'SH': r'\bHOOK_SH\b|\bSH_HOOK\b|_SH_|^SH_',  # Statistic Hook
            'QH': r'\bHOOK_QH\b|\bQH_HOOK\b|_QH_|^QH_',  # Question Hook
            'VALUE_PROP': r'\bHOOK_VP\b|\bVP_HOOK\b|_VP_|^VP_|VALUE_PROP',  # Value Proposition
            'REVEAL': r'\bHOOK_REVEAL\b|_REVEAL_|^REVEAL_',  # Reveal Hook
            'PROMISE': r'\bHOOK_PROMISE\b|_PROMISE_|^PROMISE_',  # Promise Hook
        }
        
        for flow_type, pattern in hook_flow_patterns.items():
            if re.search(pattern, name_upper):
                metadata['hook_flow_type'] = flow_type
                metadata['is_hook'] = True  # Ensure is_hook is set
                break
        
        # CTA detection
        if name_upper.startswith('CTA_') or name_upper.startswith('OUTRO_') or 'cta' in name_lower:
            metadata['is_cta'] = True
        
        # Mistake/delete detection
        if (name_upper.startswith('MISTAKE_') or name_upper.startswith('DELETE_') or 
            name_upper.startswith('RETAKE_') or 'mistake' in name_lower or 'delete' in name_lower):
            metadata['is_mistake'] = True
        
        # Take number detection: (N), _TAKEN, _TAKE_N
        take_match = re.search(r'\((\d+)\)', filename)
        if not take_match:
            take_match = re.search(r'_TAKE(\d+)', name_upper)
        if not take_match:
            take_match = re.search(r'_TAKEN', name_upper)
            if take_match:
                # Try to find number before _TAKEN
                before_take = filename[:take_match.start()].split('_')[-1]
                if before_take.isdigit():
                    metadata['take_number'] = int(before_take)
        if take_match and not metadata['take_number']:
            metadata['take_number'] = int(take_match.group(1))
        
        return metadata

    def _parse_srt(self, srt_path: Path) -> List[SRTEntry]:
        """Parse SRT file into entries"""
        entries = []
        content = srt_path.read_text(encoding='utf-8', errors='ignore')

        # Split into blocks
        blocks = re.split(r'\n\n+', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0])
                    # Parse timestamp: 00:00:01,000 --> 00:00:04,000
                    time_match = re.match(
                        r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
                        lines[1]
                    )
                    if time_match:
                        g = time_match.groups()
                        start = int(g[0])*3600 + int(g[1])*60 + int(g[2]) + int(g[3])/1000
                        end = int(g[4])*3600 + int(g[5])*60 + int(g[6]) + int(g[7])/1000
                        text = ' '.join(lines[2:])

                        entries.append(SRTEntry(
                            index=index,
                            start_time=start,
                            end_time=end,
                            text=text
                        ))
                except (ValueError, IndexError):
                    continue

        return entries

    def _detect_topics(self, text: str) -> List[str]:
        """Detect topics in text"""
        text_lower = text.lower()
        detected = []

        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if topic not in detected:
                        detected.append(topic)
                    break

        return detected

    def _find_silence_regions(self, entries: List[SRTEntry], total_duration: float) -> List[Tuple[float, float]]:
        """Find gaps between speech (silence regions)"""
        silence = []

        # Check start
        if entries and entries[0].start_time > 1.0:
            silence.append((0, entries[0].start_time))

        # Check gaps between entries
        for i in range(len(entries) - 1):
            gap_start = entries[i].end_time
            gap_end = entries[i + 1].start_time
            if gap_end - gap_start > 1.0:  # More than 1 second gap
                silence.append((gap_start, gap_end))

        # Check end
        if entries and entries[-1].end_time < total_duration - 1.0:
            silence.append((entries[-1].end_time, total_duration))

        return silence

    def _find_filler_regions(self, entries: List[SRTEntry]) -> List[Tuple[float, float]]:
        """Find regions with filler words"""
        filler_regions = []

        for entry in entries:
            for pattern in self.FILLER_WORDS:
                if re.search(pattern, entry.text.lower()):
                    filler_regions.append((entry.start_time, entry.end_time))
                    break

        return filler_regions

    def _find_best_moments(self, clip: ClipAnalysis) -> List[Segment]:
        """Find the best moments in a clip based on content
        
        CRITICAL: Only cuts at complete sentence boundaries to avoid cutting off speech.
        Merges continuous segments to avoid unnecessary cuts.
        Only creates separate segments at natural pauses (>3s gap) AND sentence boundaries.
        """
        moments = []

        if not clip.entries:
            return moments

        # Find natural edit points (pauses) first - cache per clip
        if not hasattr(clip, '_cached_natural_pauses'):
            if hasattr(self, 'transcript_analyzer'):
                clip._cached_natural_pauses = self.transcript_analyzer.find_natural_edit_points(clip)
            else:
                clip._cached_natural_pauses = []
        
        pause_times = {p.timecode for p in clip._cached_natural_pauses if p.confidence > 0.5}
        
        # Build continuous segments, ONLY breaking at:
        # 1. Natural pauses (>3 seconds) AND
        # 2. Complete sentence boundaries (ends with . ! ?)
        current_segment_start = None
        current_segment_end = None
        current_text_parts = []
        current_max_score = 0.0
        
        for i, entry in enumerate(clip.entries):
            score = self._score_segment(entry.text)
            
            # Check if this entry should be included (low threshold)
            if score > 0.1:
                entry_text = entry.text.strip()
                
                # Check if previous entry ended a complete sentence
                prev_ends_sentence = False
                if i > 0:
                    prev_text = clip.entries[i-1].text.strip()
                    prev_ends_sentence = prev_text and prev_text[-1] in '.!?'
                
                # Check if current entry starts with a complete sentence (not mid-sentence)
                # Look for sentence start indicators
                entry_starts_sentence = False
                if entry_text:
                    # Starts with capital letter (likely new sentence)
                    # OR starts after a long pause (gap > 3s)
                    # OR previous entry ended with sentence punctuation
                    gap = entry.start_time - clip.entries[i-1].end_time if i > 0 else 0
                    entry_starts_sentence = (
                        entry_text[0].isupper() or 
                        gap > 3.0 or
                        (i > 0 and prev_ends_sentence)
                    )
                
                # Check if there's a natural pause before this entry
                has_pause_before = False
                gap = 0.0
                if i > 0:
                    prev_entry = clip.entries[i-1]
                    gap = entry.start_time - prev_entry.end_time
                    # Require longer pause (3+ seconds) for natural break
                    if gap > 3.0:
                        has_pause_before = True
                    else:
                        # Check if there's a pause marker near this gap (within 1s)
                        for pause_time in pause_times:
                            if abs(pause_time - prev_entry.end_time) < 1.0:
                                has_pause_before = True
                                break
                
                # CRITICAL: Only break segment if:
                # 1. Previous entry ended a complete sentence AND
                # 2. There's a natural pause (>3s) OR entry clearly starts new sentence
                should_break = (
                    prev_ends_sentence and 
                    (has_pause_before or entry_starts_sentence)
                ) or gap > 4.0  # Very long pause always breaks
                
                # Start new segment if:
                # 1. No current segment, OR
                # 2. Natural break point (sentence end + pause)
                if current_segment_start is None:
                    # Start new segment - use entry start time
                    # But only if entry starts a sentence (not mid-sentence)
                    if entry_starts_sentence or i == 0:
                        current_segment_start = entry.start_time
                        current_segment_end = entry.end_time
                        current_text_parts = [entry.text]
                        current_max_score = score
                    else:
                        # Skip this entry if it's mid-sentence (wait for sentence start)
                        continue
                elif should_break:
                    # Save current segment and start new one
                    # Ensure previous segment ends at complete sentence
                    if current_segment_start is not None:
                        # Check if current segment ends properly
                        final_text = ' '.join(current_text_parts)
                        if final_text.strip() and final_text.strip()[-1] not in '.!?':
                            # Extend to end of current entry to try to complete sentence
                            current_segment_end = entry.end_time
                            current_text_parts.append(entry.text)
                        
                        moments.append(Segment(
                            source_file=clip.file_path,
                            start_time=current_segment_start,
                            end_time=current_segment_end,
                            text=' '.join(current_text_parts),
                            score=current_max_score
                        ))
                    # Start new segment (only if entry starts sentence)
                    if entry_starts_sentence:
                        current_segment_start = entry.start_time
                        current_segment_end = entry.end_time
                        current_text_parts = [entry.text]
                        current_max_score = score
                    else:
                        # Don't start new segment if mid-sentence - continue current
                        current_segment_end = entry.end_time
                        current_text_parts.append(entry.text)
                        current_max_score = max(current_max_score, score)
                else:
                    # Continue current segment (merge with previous)
                    # Always extend to end of current entry
                    current_segment_end = entry.end_time
                    current_text_parts.append(entry.text)
                    current_max_score = max(current_max_score, score)
        
        # Don't forget the last segment - ensure it ends at sentence boundary
        if current_segment_start is not None:
            final_text = ' '.join(current_text_parts)
            # If doesn't end with sentence punctuation, try to extend to next entry
            # But if it's the last entry, just use it as-is
            moments.append(Segment(
                source_file=clip.file_path,
                start_time=current_segment_start,
                end_time=current_segment_end,
                text=final_text,
                score=current_max_score
            ))

        # Final merge pass for any remaining adjacent segments (with larger gap threshold)
        moments = self._merge_adjacent_segments(moments, gap_threshold=3.0)  # Increased from 2.0

        return sorted(moments, key=lambda x: x.score, reverse=True)

    def _score_segment(self, text: str) -> float:
        """Score a segment for quality/interest"""
        # Base score: all speech has value
        score = 0.2
        text_lower = text.lower()

        # Length bonus (not too short, not too long)
        word_count = len(text.split())
        if 5 <= word_count <= 30:
            score += 0.2
        elif word_count > 30:
            score += 0.15
        elif word_count >= 3:
            score += 0.1  # Short but still valid

        # Topic keywords bonus
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    score += 0.15
                    break

        # Emotional words bonus
        emotional_words = ['love', 'remember', 'miss', 'wish', 'dream', 'hope', 'happy', 'proud']
        for word in emotional_words:
            if word in text_lower:
                score += 0.1

        # Question bonus (indicates engagement)
        if '?' in text:
            score += 0.1

        # Filler word penalty (reduced - fillers are natural speech)
        filler_count = 0
        for pattern in self.FILLER_WORDS:
            if re.search(pattern, text_lower):
                filler_count += 1
        # Only penalize if mostly filler
        if filler_count > 2:
            score -= 0.15

        return min(1.0, max(0.0, score))

    def _merge_adjacent_segments(self, segments: List[Segment], gap_threshold: float = 2.0) -> List[Segment]:
        """Merge segments that are close together or overlapping
        
        More aggressive merging to avoid unnecessary cuts in continuous clips.
        Only keeps separate segments if there's a significant gap (natural pause).
        """
        if not segments:
            return []

        # Sort by start time
        sorted_segs = sorted(segments, key=lambda x: (str(x.source_file), x.start_time))
        merged = [sorted_segs[0]]

        for seg in sorted_segs[1:]:
            last = merged[-1]
            
            # Same file
            if seg.source_file == last.source_file:
                gap = seg.start_time - last.end_time
                
                # If overlapping or very close (within gap_threshold), merge
                if gap <= gap_threshold:
                    # Merge: extend to cover both segments
                    merged[-1] = Segment(
                        source_file=last.source_file,
                        start_time=min(last.start_time, seg.start_time),
                        end_time=max(last.end_time, seg.end_time),
                        text=last.text + ' ' + seg.text if seg.text else last.text,
                        score=max(last.score, seg.score)  # Keep highest score
                    )
                else:
                    # Significant gap - keep separate (natural pause)
                    merged.append(seg)
            else:
                # Different file - keep separate
                merged.append(seg)

        return merged
    
    def _deduplicate_segments(self, segments: List[Segment]) -> List[Segment]:
        """Remove duplicate or heavily overlapping segments - AGGRESSIVE
        
        Now removes:
        - Exact duplicates (same file, same time range)
        - Segments with >30% overlap (was 50%)
        - Segments that are subsets of existing segments
        - Segments from same file that are very close (<5s apart) with similar content
        """
        if not segments:
            return []
        
        # Sort by score (descending) and start time
        sorted_segs = sorted(segments, key=lambda x: (-x.score, str(x.source_file), x.start_time))
        unique = []
        seen_ranges = set()
        
        for seg in sorted_segs:
            # Create a key for this time range
            range_key = (seg.source_file, seg.start_time, seg.end_time)
            
            # Check for exact duplicates
            if range_key in seen_ranges:
                continue
            
            # Get base filename for normalized duplicate detection
            seg_base = self._get_base_filename(seg.source_file)
            
            # Check for significant overlap with existing segments from same file OR same base file
            overlaps = False
            is_subset = False
            seg_duration = seg.end_time - seg.start_time
            
            # Check against all existing segments
            for existing in unique:
                existing_base = self._get_base_filename(existing.source_file)
                
                # Check if same file OR same base file (normalized/duplicate version)
                same_source = (
                    seg.source_file == existing.source_file or
                    seg_base == existing_base
                )
                
                if same_source:
                    # Calculate overlap
                    overlap_start = max(seg.start_time, existing.start_time)
                    overlap_end = min(seg.end_time, existing.end_time)
                    overlap_duration = max(0, overlap_end - overlap_start)
                    
                    if overlap_duration > 0:
                        # Check if more than 30% overlap (more aggressive than before)
                        overlap_pct_seg = (overlap_duration / seg_duration) if seg_duration > 0 else 0
                        existing_duration = existing.end_time - existing.start_time
                        overlap_pct_existing = (overlap_duration / existing_duration) if existing_duration > 0 else 0
                        
                        # Use config threshold for overlap detection
                        if overlap_pct_seg > self.scoring_config.duplicate_overlap_pct or overlap_pct_existing > self.scoring_config.duplicate_overlap_pct:
                            overlaps = True
                            break
                    
                    # If same base file and similar time range, prefer non-normalized version
                    if seg_base == existing_base and seg.source_file != existing.source_file:
                        # Check if time ranges are very similar (within 2 seconds)
                        time_diff = abs(seg.start_time - existing.start_time) + abs(seg.end_time - existing.end_time)
                        if time_diff < 2.0:
                            # Prefer non-normalized version
                            if "_normalized" in str(seg.source_file) and "_normalized" not in str(existing.source_file):
                                overlaps = True  # Skip normalized version
                                break
                            elif "_normalized" not in str(seg.source_file) and "_normalized" in str(existing.source_file):
                                # Mark for replacement (don't modify list during iteration)
                                # Will handle after loop
                                overlaps = True  # Skip this segment, keep existing
                                break
                        
                        # Check if this segment is a subset of existing (completely contained)
                        if (seg.start_time >= existing.start_time and seg.end_time <= existing.end_time):
                            is_subset = True
                            break
                        
                        # Check if existing is a subset of this segment
                        if (existing.start_time >= seg.start_time and existing.end_time <= seg.end_time):
                            # Mark for replacement (don't modify list during iteration)
                            overlaps = True  # Skip this segment, existing is subset
                            break
                    
                    # Also check if segments are very close together (<5s gap) - likely duplicates
                    gap_before = seg.start_time - existing.end_time
                    gap_after = existing.start_time - seg.end_time
                    if gap_before >= 0 and gap_before < 5.0:
                        # Segments are close - check if content is similar
                        if seg.text and existing.text:
                            # Simple similarity check: if texts share significant words
                            seg_words = set(seg.text.lower().split())
                            existing_words = set(existing.text.lower().split())
                            if len(seg_words) > 0 and len(existing_words) > 0:
                                similarity = len(seg_words & existing_words) / max(len(seg_words), len(existing_words))
                                if similarity > 0.5:  # More than 50% word overlap
                                    overlaps = True
                                    break
                
                # Early exit: if we've passed this file's segments, no need to check further
                if existing.source_file > seg.source_file:
                    break
            
            if not overlaps and not is_subset:
                unique.append(seg)
                seen_ranges.add(range_key)
        
        # Post-process: Remove any segments that are subsets of others
        # (This handles cases where we couldn't remove during iteration safely)
        final_unique = []
        for seg in unique:
            is_subset_of_any = False
            for other in unique:
                if seg != other and seg.source_file == other.source_file:
                    if (seg.start_time >= other.start_time and seg.end_time <= other.end_time):
                        is_subset_of_any = True
                        break
            if not is_subset_of_any:
                final_unique.append(seg)
        
        return final_unique

    def create_rough_cut(self, style: CutStyle, target_duration: Optional[float] = None, 
                        use_smart_features: bool = True, use_audio_markers: bool = False) -> RoughCutPlan:
        """Create a rough cut plan based on style
        
        Args:
            style: Cut style (DOC, INTERVIEW, EPISODE, TUTORIAL, REVIEW, UNBOXING, COMPARISON, SETUP, EXPLAINER)
            target_duration: Target duration in seconds
            use_smart_features: Use NLP-based smart features (for documentaries)
            use_audio_markers: Use audio markers for segment extraction (if markers detected)
        """
        if not self.clips:
            raise ValueError("No clips analyzed. Call analyze_clips() first.")

        # Check if audio markers should be used
        if use_audio_markers:
            # Detect markers in clips
            from .rough_cut_markers import detect_markers_in_clips, extract_segments_from_markers
            clips_with_markers = detect_markers_in_clips(self.clips)
            
            # Check if any clips have markers
            has_markers = any(clip.markers for clip in clips_with_markers)
            
            if has_markers:
                # Use marker-based rough cut
                return self._create_marker_based_cut(style, target_duration, clips_with_markers)

        style_config = self.STYLE_STRUCTURES[style]

        # Route to style-specific methods
        if style == CutStyle.DOC and use_smart_features:
            return self._create_smart_documentary_cut(target_duration)
        elif style == CutStyle.REVIEW:
            return self._create_review_cut(self.clips, target_duration)
        elif style == CutStyle.UNBOXING:
            return self._create_unboxing_cut(self.clips, target_duration)
        elif style == CutStyle.COMPARISON:
            return self._create_comparison_cut(self.clips, target_duration)
        elif style == CutStyle.SETUP:
            return self._create_setup_cut(self.clips, target_duration)
        elif style == CutStyle.EXPLAINER:
            return self._create_explainer_cut(self.clips, target_duration)
        
        # Original quality-based approach for other styles (INTERVIEW, EPISODE, TUTORIAL)
        return self._create_quality_based_cut(style, target_duration, style_config)
    
    def _create_marker_based_cut(self, style: CutStyle, target_duration: Optional[float],
                                 clips_with_markers: List[ClipAnalysis]) -> RoughCutPlan:
        """Create rough cut from audio markers"""
        from .rough_cut_markers import extract_segments_from_markers
        
        # Extract segments from markers
        segments = extract_segments_from_markers(clips_with_markers)
        
        # Sort segments by order command if present, otherwise by timestamp
        def get_segment_order(seg: Segment) -> Tuple[int, float]:
            # Try to find order from markers
            for clip in clips_with_markers:
                if clip.file_path == seg.source_file:
                    for marker in clip.markers:
                        if (marker.marker_type == "start" and 
                            marker.cut_point <= seg.start_time <= marker.cut_point + 1.0):
                            order = marker.parsed_commands.order
                            if order is not None:
                                return (order, seg.start_time)
            return (999, seg.start_time)  # No order found, sort by time
        
        segments.sort(key=get_segment_order)
        
        # Organize into structure
        structure = {}
        for seg in segments:
            section = seg.segment_type if seg.segment_type else "content"
            if section not in structure:
                structure[section] = []
            structure[section].append(seg)
        
        # Calculate total duration
        total_duration = sum(seg.end_time - seg.start_time for seg in segments)
        
        return RoughCutPlan(
            style=style,
            clips=clips_with_markers,
            segments=segments,
            total_duration=total_duration,
            structure=structure,
            themes=[],
            narrative_arc={},
            removed_segments=[]
        )
    
    def _create_quality_based_cut(self, style: CutStyle, target_duration: Optional[float],
                                  style_config: Dict) -> RoughCutPlan:
        """Original quality-based rough cut with removed segments tracking"""
        # Collect all good segments
        all_segments = []
        for clip in self.clips:
            all_segments.extend(clip.best_moments)
        
        # Remove duplicates and overlapping segments (merge happens at final output)
        all_segments = self._deduplicate_segments(all_segments)

        # Sort by score
        all_segments.sort(key=lambda x: x.score, reverse=True)

        # Calculate target duration
        total_raw = sum(c.duration for c in self.clips)
        if target_duration is None:
            target_duration = total_raw * style_config['target_ratio']

        # CRITICAL: Extend segments to complete sentence boundaries before selection
        # This ensures we never cut mid-sentence or cut off speech
        extended_segments = []
        for seg in all_segments:
            # Find the clip this segment belongs to
            clip = next((c for c in self.clips if c.file_path == seg.source_file), None)
            if clip and clip.entries and seg.text:
                # Find entries that overlap with this segment
                overlapping_entries = [
                    e for e in clip.entries
                    if not (e.end_time <= seg.start_time or e.start_time >= seg.end_time)
                ]
                
                if overlapping_entries:
                    # Find the first entry that overlaps
                    first_entry = overlapping_entries[0]
                    first_entry_idx = clip.entries.index(first_entry)
                    actual_start = first_entry.start_time
                    
                    # Check if segment text starts mid-sentence
                    seg_text = seg.text.strip()
                    starts_mid_sentence = seg_text and not seg_text[0].isupper() and seg_text[0] not in '"' and not seg_text[0].isdigit()
                    
                    # Also check if first entry itself starts mid-sentence
                    first_entry_text = first_entry.text.strip()
                    first_starts_mid = first_entry_text and not first_entry_text[0].isupper() and first_entry_text[0] not in '"'
                    
                    if (starts_mid_sentence or first_starts_mid) and first_entry_idx > 0:
                        # Look backwards to find where sentence actually starts
                        found_sentence_start = False
                        for j in range(first_entry_idx - 1, -1, -1):
                            prev_entry = clip.entries[j]
                            prev_text = prev_entry.text.strip()
                            
                            # If previous entry ends with sentence punctuation, we found the start
                            if prev_text and prev_text[-1] in '.!?':
                                # Next entry (first_entry) starts new sentence
                                actual_start = first_entry.start_time
                                found_sentence_start = True
                                break
                            
                            # Otherwise, extend backwards
                            actual_start = prev_entry.start_time
                            
                            # Stop if we've gone back too far (more than 10 seconds)
                            if first_entry.start_time - actual_start > 10.0:
                                actual_start = first_entry.start_time
                                break
                            
                            if j == 0:
                                # Reached beginning - can't extend further
                                # If we're at clip start and still mid-sentence, add small padding
                                if actual_start == 0.0 or actual_start < 0.5:
                                    actual_start = max(0.0, first_entry.start_time - 0.5)  # 0.5s padding
                                break
                        
                        # If we couldn't find sentence start and we're at clip beginning,
                        # add padding to avoid cutting off speech
                        if not found_sentence_start and actual_start <= first_entry.start_time:
                            if first_entry_idx == 0 or actual_start < 1.0:
                                actual_start = max(0.0, first_entry.start_time - 1.0)  # 1s padding at start
                    
                    # Find the last entry that overlaps
                    last_entry = overlapping_entries[-1]
                    last_entry_idx = clip.entries.index(last_entry)
                    actual_end = last_entry.end_time
                    
                    # Check if segment text ends mid-sentence
                    ends_mid_sentence = seg_text and seg_text[-1] not in '.!?'
                    
                    if ends_mid_sentence and last_entry_idx < len(clip.entries) - 1:
                        # Look forwards to find where sentence actually ends
                        for j in range(last_entry_idx + 1, len(clip.entries)):
                            next_entry = clip.entries[j]
                            next_text = next_entry.text.strip()
                            
                            # Extend to include this entry
                            actual_end = next_entry.end_time
                            
                            # If this entry ends with sentence punctuation, we found the end
                            if next_text and next_text[-1] in '.!?':
                                break
                            
                            # Stop if we've extended too far (more than 5 seconds)
                            if actual_end - last_entry.end_time > 5.0:
                                actual_end = last_entry.end_time
                                break
                            
                            if j >= last_entry_idx + 5:  # Don't extend more than 5 entries
                                break
                    
                    # Create extended segment with complete sentences
                    extended_seg = Segment(
                        source_file=seg.source_file,
                        start_time=actual_start,
                        end_time=actual_end,
                        text=seg.text,  # Keep original text for reference
                        topic=seg.topic,
                        score=seg.score,
                        segment_type=seg.segment_type
                    )
                    extended_segments.append(extended_seg)
                else:
                    # No overlapping entries - use segment as-is
                    extended_segments.append(seg)
            else:
                # No clip or entries - use segment as-is
                extended_segments.append(seg)
        
        # Use extended segments for selection
        all_segments = extended_segments
        
        # Select segments to fit target duration (optimized to keep good footage)
        selected = []
        removed = []
        current_duration = 0
        
        # Use scoring config threshold (Phase 3: Unify scoring thresholds)
        min_score_threshold = self.scoring_config.segment_threshold

        for seg in all_segments:
            seg_duration = seg.end_time - seg.start_time
            
            # Track why segments are removed
            reason = None
            
            if seg_duration < style_config['min_segment']:
                reason = f"too_short ({seg_duration:.1f}s < {style_config['min_segment']}s)"
            elif seg.score < min_score_threshold:
                reason = f"low_score ({seg.score:.2f} < {min_score_threshold})"
            elif seg_duration > style_config['max_segment']:
                # Truncate long segments but keep the truncated version
                truncated_seg = Segment(
                    source_file=seg.source_file,
                    start_time=seg.start_time,
                    end_time=seg.start_time + style_config['max_segment'],
                    text=seg.text[:200] + '...',
                    score=seg.score
                )
                seg = truncated_seg
                seg_duration = style_config['max_segment']
                # Track the removed portion
                removed_portion = Segment(
                    source_file=seg.source_file,
                    start_time=seg.start_time + style_config['max_segment'],
                    end_time=seg.end_time,
                    text=seg.text[200:] if len(seg.text) > 200 else "",
                    score=seg.score * 0.8  # Slightly lower score for remainder
                )
                removed.append(RemovedSegment(
                    segment=removed_portion,
                    reason=f"truncated_remainder (kept first {style_config['max_segment']}s)",
                    score=removed_portion.score
                ))

            if reason:
                # Segment was removed
                removed.append(RemovedSegment(
                    segment=seg,
                    reason=reason,
                    score=seg.score
                ))
                continue

            # Check for duplicates before adding
            is_duplicate = False
            for existing in selected:
                if seg.source_file == existing.source_file:
                    # Check if this segment overlaps significantly with existing
                    overlap_start = max(seg.start_time, existing.start_time)
                    overlap_end = min(seg.end_time, existing.end_time)
                    overlap_duration = max(0, overlap_end - overlap_start)
                    
                    if overlap_duration > 0:
                        # Calculate overlap percentage
                        seg_duration_check = seg.end_time - seg.start_time
                        existing_duration = existing.end_time - existing.start_time
                        overlap_pct = overlap_duration / min(seg_duration_check, existing_duration)
                        
                        if overlap_pct > self.scoring_config.duplicate_overlap_pct:  # Use config threshold
                            is_duplicate = True
                            removed.append(RemovedSegment(
                                segment=seg,
                                reason=f"duplicate_overlap ({overlap_pct*100:.0f}% with existing segment)",
                                score=seg.score
                            ))
                            break
            
            if is_duplicate:
                continue
            
            # Phase 6: Include handles in duration calculation
            pre_handle = style_config.get('pre_handle', 0.0)
            post_handle = style_config.get('post_handle', 0.0)
            seg_duration_with_handles = seg_duration + pre_handle + post_handle
            
            if current_duration + seg_duration_with_handles <= target_duration:
                selected.append(seg)
                current_duration += seg_duration_with_handles
            else:
                # Exceeds target duration - but check if it's high quality
                # More aggressive: keep high-quality segments even if slightly over
                # Phase 6: Include handles in duration calculation
                if seg.score > 0.7:  # Very high quality - keep it anyway
                    selected.append(seg)
                    current_duration += seg_duration_with_handles
                elif seg.score > 0.6 and (current_duration + seg_duration_with_handles) <= target_duration * 1.1:
                    # Good quality, allow 10% overflow
                    selected.append(seg)
                    current_duration += seg_duration_with_handles
                else:
                    removed.append(RemovedSegment(
                        segment=seg,
                        reason=f"duration_limit (would exceed {target_duration:.1f}s)",
                        score=seg.score
                    ))
        
        # Organize into structure (merge happens at final output)
        structure = self._organize_by_structure(selected, style)

        # Flatten structure back to ordered segments
        ordered_segments = []
        for section in style_config['sections']:
            if section in structure:
                ordered_segments.extend(structure[section])

        return RoughCutPlan(
            style=style,
            clips=self.clips,
            segments=ordered_segments,
            total_duration=sum(s.end_time - s.start_time for s in ordered_segments),
            structure=structure,
            removed_segments=removed
        )
    
    def _organize_by_structure(self, segments: List[Segment], style: CutStyle) -> Dict[str, List[Segment]]:
        """Organize segments into style-specific structure"""
        sections = self.STYLE_STRUCTURES[style]['sections']
        structure = {s: [] for s in sections}

        if not segments:
            return structure

        if style == CutStyle.DOC:
            # Documentary: opening context, main story, reflection, closing
            # Sort by time for narrative flow
            segments.sort(key=lambda x: (str(x.source_file), x.start_time))

            n = len(segments)
            if n >= 5:
                structure['opening'] = segments[:1]
                structure['context'] = segments[1:n//4]
                structure['main_story'] = segments[n//4:3*n//4]
                structure['reflection'] = segments[3*n//4:-1]
                structure['closing'] = segments[-1:]
            else:
                structure['main_story'] = segments

        elif style == CutStyle.INTERVIEW:
            # Interview: group by topic/question
            segments.sort(key=lambda x: x.score, reverse=True)

            n = len(segments)
            if n >= 6:
                structure['intro'] = segments[:1]
                structure['q1'] = segments[1:n//3]
                structure['q2'] = segments[n//3:2*n//3]
                structure['q3'] = segments[2*n//3:-2]
                structure['highlight'] = [segments[0]]  # Best moment
                structure['closing'] = segments[-1:]
            else:
                structure['highlight'] = segments

        elif style == CutStyle.EPISODE:
            # Episode: hook, content, climax, outro
            # Best moment first as hook
            segments.sort(key=lambda x: x.score, reverse=True)

            n = len(segments)
            if n >= 6:
                structure['hook'] = segments[:1]
                structure['intro'] = segments[1:2]
                structure['main_content'] = segments[2:-3]
                structure['climax'] = segments[-3:-1]
                structure['outro'] = segments[-1:]
                structure['cta'] = []  # Placeholder for call-to-action
            else:
                structure['main_content'] = segments

        return structure
    
    def _create_smart_documentary_cut(self, target_duration: Optional[float]) -> RoughCutPlan:
        """Create smart documentary rough cut using transcript analysis"""
        # 1. Analyze interview segments
        interview_clips = [c for c in self.clips if c.has_speech]
        # B-roll clips are those without speech (or with minimal speech)
        broll_clips = [c for c in self.clips if not c.has_speech]
        
        self.interview_segments = []
        for clip in interview_clips:
            segment = self.transcript_analyzer.analyze_interview_segment(clip)
            self.interview_segments.append(segment)
        
        # 2. Organize by themes
        self.themes = self._organize_by_themes()
        
        # 3. Build narrative arc
        narrative_arc = self._build_narrative_arc(target_duration)
        
        # 4. Match B-roll to interview segments
        segments_with_broll = self._add_broll_to_segments(narrative_arc, broll_clips)
        
        # 5. Convert to segments
        ordered_segments = self._convert_to_segments(segments_with_broll)
        
        # 6. Remove duplicates and overlapping segments (merge happens at final output)
        ordered_segments = self._deduplicate_segments(ordered_segments)
        
        # Single merge pass at final output (Phase 2: Consolidate merging)
        ordered_segments = self._merge_adjacent_segments(
            ordered_segments, 
            gap_threshold=self.scoring_config.merge_gap_threshold_doc
        )
        
        # Calculate total duration
        total_duration = sum(s.end_time - s.start_time for s in ordered_segments)
        
        # 8. Track removed segments
        removed = self._identify_removed_segments_for_doc(ordered_segments)
        
        return RoughCutPlan(
            style=CutStyle.DOC,
            clips=self.clips,
            segments=ordered_segments,
            total_duration=total_duration,
            structure=narrative_arc,  # Use narrative arc as structure
            themes=self.themes,
            narrative_arc=narrative_arc,
            removed_segments=removed
        )
    
    def _identify_removed_segments_for_doc(self, selected_segments: List[Segment]) -> List[RemovedSegment]:
        """Identify segments that were removed from documentary cut"""
        removed = []
        
        # Get all possible segments from clips
        all_possible_segments = []
        for clip in self.clips:
            if clip.has_speech:
                # Get all transcript entries as potential segments
                for entry in clip.entries:
                    seg = Segment(
                        source_file=clip.file_path,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=entry.text,
                        score=self._score_segment(entry.text) if hasattr(self, '_score_segment') else 0.5
                    )
                    all_possible_segments.append(seg)
        
        # Find segments that weren't selected
        selected_set = {(s.source_file, s.start_time, s.end_time) for s in selected_segments}
        
        for seg in all_possible_segments:
            seg_key = (seg.source_file, seg.start_time, seg.end_time)
            if seg_key not in selected_set:
                # Check if this segment overlaps with any selected segment
                overlaps = any(
                    s.source_file == seg.source_file and
                    not (seg.end_time <= s.start_time or seg.start_time >= s.end_time)
                    for s in selected_segments
                )
                
                if not overlaps:
                    removed.append(RemovedSegment(
                        segment=seg,
                        reason="not_selected_for_narrative",
                        score=seg.score
                    ))
        
        return removed
    
    def _organize_by_themes(self) -> List[Theme]:
        """Organize interview segments by topics/themes"""
        # Extract all quotes grouped by topic
        topics_dict = self.transcript_analyzer.extract_topics(self.clips)
        
        themes = []
        theme_order = {
            'introduction': 1,
            'problem': 2,
            'personal_stories': 3,
            'expert_opinions': 4,
            'solutions': 5,
            'conclusion': 6
        }
        
        for topic_name, quotes in topics_dict.items():
            # Quality filter: require at least 2 quotes, or 1 very high-quality quote
            if len(quotes) < 2:
                # Check if single quote is exceptional (importance > 90)
                if len(quotes) == 1 and quotes[0].importance_score > 90.0:
                    pass  # Keep exceptional single quotes
                else:
                    continue
            
            # Calculate target duration based on number of quotes
            avg_quote_duration = sum(q.end_time - q.start_time for q in quotes) / len(quotes)
            target_duration = len(quotes) * avg_quote_duration * 1.2  # Add 20% padding
            
            # Select top quotes (already sorted by importance_score)
            # Increase from 10 to 15 for better coverage
            key_quotes = quotes[:15] if len(quotes) >= 15 else quotes
            
            theme = Theme(
                name=topic_name,
                key_quotes=key_quotes,
                duration_target=target_duration,
                order=theme_order.get(topic_name, 99),
                description=f"{len(quotes)} quotes about {topic_name}"
            )
            themes.append(theme)
        
        # Sort by narrative order
        themes.sort(key=lambda t: t.order)
        return themes
    
    def _build_narrative_arc(self, target_duration: Optional[float]) -> Dict[str, List[Segment]]:
        """Build documentary narrative arc: hook → setup → act1 → act2 → act3 → conclusion"""
        arc = {
            'hook': [],
            'setup': [],
            'act_1': [],
            'act_2': [],
            'act_3': [],
            'conclusion': []
        }
        
        if not self.interview_segments:
            return arc
        
        # Calculate target duration per act
        if target_duration is None:
            target_duration = sum(s.duration for s in self.interview_segments) * 0.6
        
        act_durations = {
            'hook': target_duration * 0.05,      # 5%
            'setup': target_duration * 0.10,     # 10%
            'act_1': target_duration * 0.25,      # 25%
            'act_2': target_duration * 0.40,      # 40%
            'act_3': target_duration * 0.15,      # 15%
            'conclusion': target_duration * 0.05  # 5%
        }
        
        # Hook: Best emotional moment or most compelling question
        # Pre-compute all quotes with their segment references for efficiency
        all_quotes_with_segments = []
        for seg in self.interview_segments:
            for quote in seg.quotes:
                all_quotes_with_segments.append((quote, seg))
        
        if all_quotes_with_segments:
            # Find quote with highest emotional impact (optimized)
            best_quote, best_seg = max(
                all_quotes_with_segments,
                key=lambda x: abs(x[1].emotion_score) * 0.5 + (x[0].importance_score / 100.0) * 0.5
            )
            
            hook_seg = self._quote_to_segment(best_quote, max_duration=30.0)
            if hook_seg:
                arc['hook'].append(hook_seg)
        
        # Setup: Establishing context (first interview segments, establishing shots)
        # Use pre-computed quotes with segments
        setup_quotes = [(q, s) for q, s in all_quotes_with_segments if q.topic == 'introduction']
        # Sort by importance and take top 3
        setup_quotes.sort(key=lambda x: x[0].importance_score, reverse=True)
        for quote, _ in setup_quotes[:3]:
            seg = self._quote_to_segment(quote, max_duration=20.0)
            if seg:
                arc['setup'].append(seg)
        
        # Act 1: Problem/conflict (thematic sections)
        problem_themes = [t for t in self.themes if 'problem' in t.name.lower() or t.order == 2]
        arc['act_1'] = self._themes_to_segments(problem_themes, act_durations['act_1'])
        
        # Act 2: Deep dive (personal stories, expert opinions)
        deep_themes = [t for t in self.themes if t.order in [3, 4]]
        arc['act_2'] = self._themes_to_segments(deep_themes, act_durations['act_2'])
        
        # Act 3: Resolution/solutions
        solution_themes = [t for t in self.themes if 'solution' in t.name.lower() or t.order == 5]
        arc['act_3'] = self._themes_to_segments(solution_themes, act_durations['act_3'])
        
        # Conclusion: Wrap up
        conclusion_quotes = [(q, s) for q, s in all_quotes_with_segments if q.topic == 'conclusion']
        conclusion_quotes.sort(key=lambda x: x[0].importance_score, reverse=True)
        for quote, _ in conclusion_quotes[:2]:
            seg = self._quote_to_segment(quote, max_duration=15.0)
            if seg:
                arc['conclusion'].append(seg)
        
        return arc
    
    def _quote_to_segment(self, quote: Quote, max_duration: Optional[float] = None) -> Optional[Segment]:
        """Convert a quote to a segment with natural edit points - optimized"""
        if not quote.clip:
            return None
        
        # Find natural pause before quote (cached per clip)
        if not hasattr(quote.clip, '_cached_edit_points'):
            quote.clip._cached_edit_points = self.transcript_analyzer.find_natural_edit_points(quote.clip)
        
        pauses = quote.clip._cached_edit_points
        in_point = quote.start_time
        out_point = quote.end_time
        
        # Adjust to natural pause if available (optimized search)
        # Sort pauses by timecode for binary search
        pauses_sorted = sorted(pauses, key=lambda p: p.timecode)
        
        for pause in pauses_sorted:
            if abs(pause.timecode - quote.start_time) < 2.0:
                in_point = pause.timecode
                break
            elif pause.timecode > quote.start_time + 2.0:
                break  # Early exit
        
        # Find natural pause after quote
        for pause in pauses_sorted:
            if pause.timecode > quote.end_time:
                if pause.timecode - quote.end_time < 2.0:
                    out_point = pause.timecode
                break
            elif pause.timecode > quote.end_time + 2.0:
                break  # Early exit
        
        # Limit duration if needed
        if max_duration and (out_point - in_point) > max_duration:
            out_point = in_point + max_duration
        
        return Segment(
            source_file=quote.clip.file_path,
            start_time=in_point,
            end_time=out_point,
            text=quote.text,
            topic=quote.topic,
            score=quote.importance_score / 100.0,
            segment_type="interview"
        )
    
    def _themes_to_segments(self, themes: List[Theme], target_duration: float) -> List[Segment]:
        """Convert themes to segments, selecting best quotes - optimized for quality"""
        segments = []
        current_duration = 0.0
        
        # Sort themes by order (narrative importance)
        themes_sorted = sorted(themes, key=lambda t: t.order)
        
        for theme in themes_sorted:
            # Quotes are already sorted by importance_score in theme
            for quote in theme.key_quotes:
                if current_duration >= target_duration:
                    break
                
                seg = self._quote_to_segment(quote)
                if seg:
                    seg_duration = seg.end_time - seg.start_time
                    
                    # Allow slight overflow for high-quality quotes
                    if current_duration + seg_duration <= target_duration * 1.1:  # 10% tolerance
                        segments.append(seg)
                        current_duration += seg_duration
                    elif quote.importance_score > 85.0:  # Very high quality - include anyway
                        segments.append(seg)
                        current_duration += seg_duration
        
        return segments
    
    def _add_broll_to_segments(self, narrative_arc: Dict[str, List[Segment]], 
                               broll_clips: List[ClipAnalysis]) -> Dict[str, List[Segment]]:
        """Match and insert B-roll clips into interview segments"""
        enhanced_arc = {}
        
        for section_name, segments in narrative_arc.items():
            enhanced_segments = []
            
            for seg in segments:
                # Add interview segment
                enhanced_segments.append(seg)
                
                # Find matching B-roll
                if seg.text:  # Has transcript
                    # Extract keywords from segment text
                    keywords = self.transcript_analyzer._extract_keywords(seg.text)
                    topic = seg.topic or "general"
                    
                    # Match B-roll
                    matches = self._match_broll_to_interview(seg, keywords, topic, broll_clips)
                    
                    # Insert B-roll after segment (or at natural points)
                    for broll, score in matches[:2]:  # Top 2 matches
                        broll_seg = Segment(
                            source_file=broll.file_path,
                            start_time=0.0,
                            end_time=min(10.0, broll.duration),  # Max 10 seconds of B-roll
                            text="",
                            topic=topic,
                            score=score,
                            segment_type="broll"
                        )
                        enhanced_segments.append(broll_seg)
            
            enhanced_arc[section_name] = enhanced_segments
        
        return enhanced_arc
    
    def _match_broll_to_interview(self, interview_seg: Segment, keywords: List[str], 
                                  topic: str, broll_clips: List[ClipAnalysis]) -> List[Tuple[ClipAnalysis, float]]:
        """Match B-roll clips to interview segment based on content/emotion - optimized"""
        matches = []
        
        # Pre-process keywords for faster matching
        keywords_lower = [k.lower() for k in keywords]
        topic_lower = topic.lower() if topic else ""
        
        for broll in broll_clips:
            # Content match score (simplified - would use visual analysis in production)
            content_score = 0.5  # Default neutral
            
            # Check if B-roll filename or metadata suggests match
            broll_name_lower = broll.file_path.stem.lower()
            
            # Optimized keyword matching
            keyword_matches = sum(1 for kw in keywords_lower if kw in broll_name_lower)
            content_score += min(0.6, keyword_matches * 0.2)  # Cap at 0.6
            
            # Topic match
            if topic_lower and topic_lower in broll_name_lower:
                content_score += 0.3  # Strong topic match
            
            # Visual quality (would use MediaAnalysis in production)
            quality_score = 0.8  # Assume good quality
            
            # Combined score (weighted)
            total_score = (content_score * 0.6 + quality_score * 0.4)
            
            if total_score > 0.5:  # Threshold
                matches.append((broll, total_score))
        
        # Sort by score (descending)
        matches.sort(key=lambda x: -x[1])
        return matches
    
    def _convert_to_segments(self, narrative_arc: Dict[str, List[Segment]]) -> List[Segment]:
        """Convert narrative arc structure to flat list of segments"""
        ordered_segments = []
        
        # Order: hook → setup → act1 → act2 → act3 → conclusion
        arc_order = ['hook', 'setup', 'act_1', 'act_2', 'act_3', 'conclusion']
        
        for section in arc_order:
            if section in narrative_arc:
                ordered_segments.extend(narrative_arc[section])
        
        return ordered_segments

    def _organize_by_structure(self, segments: List[Segment], style: CutStyle) -> Dict[str, List[Segment]]:
        """Organize segments into style-specific structure"""
        sections = self.STYLE_STRUCTURES[style]['sections']
        structure = {s: [] for s in sections}

        if not segments:
            return structure

        if style == CutStyle.DOC:
            # Documentary: opening context, main story, reflection, closing
            # Sort by time for narrative flow
            segments.sort(key=lambda x: (str(x.source_file), x.start_time))

            n = len(segments)
            if n >= 5:
                structure['opening'] = segments[:1]
                structure['context'] = segments[1:n//4]
                structure['main_story'] = segments[n//4:3*n//4]
                structure['reflection'] = segments[3*n//4:-1]
                structure['closing'] = segments[-1:]
            else:
                structure['main_story'] = segments

        elif style == CutStyle.INTERVIEW:
            # Interview: group by topic/question
            segments.sort(key=lambda x: x.score, reverse=True)

            n = len(segments)
            if n >= 6:
                structure['intro'] = segments[:1]
                structure['q1'] = segments[1:n//3]
                structure['q2'] = segments[n//3:2*n//3]
                structure['q3'] = segments[2*n//3:-2]
                structure['highlight'] = [segments[0]]  # Best moment
                structure['closing'] = segments[-1:]
            else:
                structure['highlight'] = segments

        elif style == CutStyle.EPISODE:
            # Episode: hook, content, climax, outro
            # Best moment first as hook
            segments.sort(key=lambda x: x.score, reverse=True)

            n = len(segments)
            if n >= 6:
                structure['hook'] = segments[:1]
                structure['intro'] = segments[1:2]
                structure['main_content'] = segments[2:-3]
                structure['climax'] = segments[-3:-1]
                structure['outro'] = segments[-1:]
                structure['cta'] = []  # Placeholder for call-to-action
            else:
                structure['main_content'] = segments
        
        elif style == CutStyle.REVIEW:
            # Review: hook, intro, overview, features, pros, cons, verdict, cta
            segments.sort(key=lambda x: (x.segment_type == "feature", x.segment_type == "pro", x.segment_type == "con", x.score), reverse=True)
            
            n = len(segments)
            if n >= 8:
                structure['hook'] = segments[:1]
                structure['intro'] = segments[1:2]
                # Features
                features = [s for s in segments if s.segment_type == "feature"]
                structure['features'] = features[:n//4] if features else segments[2:n//2]
                # Pros
                pros = [s for s in segments if s.segment_type == "pro"]
                structure['pros'] = pros[:n//6] if pros else segments[n//2:2*n//3]
                # Cons
                cons = [s for s in segments if s.segment_type == "con"]
                structure['cons'] = cons[:n//6] if cons else segments[2*n//3:-2]
                # Verdict
                structure['verdict'] = segments[-2:-1]
                structure['cta'] = segments[-1:]
            else:
                structure['main_content'] = segments
        
        elif style == CutStyle.UNBOXING:
            # Unboxing: hook, intro, unboxing, first_look, initial_thoughts, cta
            segments.sort(key=lambda x: (x.segment_type == "reveal", x.score), reverse=True)
            
            n = len(segments)
            if n >= 6:
                structure['hook'] = segments[:1]
                structure['intro'] = segments[1:2]
                # Reveals go to unboxing section
                reveals = [s for s in segments if s.segment_type == "reveal"]
                structure['unboxing'] = reveals[:n//3] if reveals else segments[2:n//2]
                structure['first_look'] = segments[n//2:2*n//3]
                structure['initial_thoughts'] = segments[2*n//3:-1]
                structure['cta'] = segments[-1:]
            else:
                structure['main_content'] = segments
        
        elif style == CutStyle.COMPARISON:
            # Comparison: hook, intro, product_a, product_b, side_by_side, winner, cta
            segments.sort(key=lambda x: (x.segment_type == "comparison", x.score), reverse=True)
            
            n = len(segments)
            if n >= 7:
                structure['hook'] = segments[:1]
                structure['intro'] = segments[1:2]
                # Alternate between products (simple split)
                structure['product_a'] = segments[2:n//2]
                structure['product_b'] = segments[n//2:2*n//3]
                # Comparisons go to side_by_side
                comparisons = [s for s in segments if s.segment_type == "comparison"]
                structure['side_by_side'] = comparisons[:n//6] if comparisons else segments[2*n//3:-2]
                structure['winner'] = segments[-2:-1]
                structure['cta'] = segments[-1:]
            else:
                structure['main_content'] = segments
        
        elif style == CutStyle.SETUP:
            # Setup: hook, intro, prerequisites, step_1, step_2, step_3, verification, troubleshooting, cta
            # Sort by step number if available, otherwise by score
            segments.sort(key=lambda x: (getattr(x, 'step_number', 999), x.score), reverse=False)
            
            n = len(segments)
            if n >= 9:
                structure['hook'] = segments[:1]
                structure['intro'] = segments[1:2]
                structure['prerequisites'] = segments[2:3]
                structure['step_1'] = segments[3:n//3]
                structure['step_2'] = segments[n//3:2*n//3]
                structure['step_3'] = segments[2*n//3:-3]
                structure['verification'] = segments[-3:-2]
                structure['troubleshooting'] = segments[-2:-1]
                structure['cta'] = segments[-1:]
            else:
                structure['main_content'] = segments
        
        elif style == CutStyle.EXPLAINER:
            # Explainer: hook, intro, concept_intro, explanation, examples, summary, cta
            segments.sort(key=lambda x: (x.segment_type == "concept", x.score), reverse=True)
            
            n = len(segments)
            if n >= 7:
                structure['hook'] = segments[:1]
                structure['intro'] = segments[1:2]
                # Concepts go to concept_intro
                concepts = [s for s in segments if s.segment_type == "concept"]
                structure['concept_intro'] = concepts[:n//6] if concepts else segments[2:n//3]
                structure['explanation'] = segments[n//3:2*n//3]
                structure['examples'] = segments[2*n//3:-2]
                structure['summary'] = segments[-2:-1]
                structure['cta'] = segments[-1:]
            else:
                structure['main_content'] = segments

        return structure
    
    def _create_review_cut(self, clips: List[ClipAnalysis], target_duration: Optional[float] = None) -> RoughCutPlan:
        """Create product review rough cut with feature/pros/cons detection"""
        style_config = self.STYLE_STRUCTURES[CutStyle.REVIEW]
        
        # Collect all segments
        all_segments = []
        for clip in clips:
            all_segments.extend(clip.best_moments)
            
            # Detect feature mentions
            if style_config.get('feature_detection', False):
                features = self.transcript_analyzer.detect_feature_mentions(clip)
                all_segments.extend(features)
            
            # Detect pros/cons
            if style_config.get('pros_cons_detection', False):
                pros, cons = self.transcript_analyzer.detect_pros_cons(clip)
                all_segments.extend(pros)
                all_segments.extend(cons)
        
        # Remove duplicates
        all_segments = self._deduplicate_segments(all_segments)
        all_segments.sort(key=lambda x: x.score, reverse=True)
        
        # Calculate target duration
        total_raw = sum(c.duration for c in clips)
        if target_duration is None:
            target_duration = total_raw * style_config['target_ratio']
        
        # Select segments
        selected = []
        removed = []
        current_duration = 0.0
        pre_handle = style_config.get('pre_handle', 0.4)
        post_handle = style_config.get('post_handle', 0.3)
        
        for seg in all_segments:
            seg_duration = seg.end_time - seg.start_time
            seg_duration_with_handles = seg_duration + pre_handle + post_handle
            
            if current_duration + seg_duration_with_handles <= target_duration:
                selected.append(seg)
                current_duration += seg_duration_with_handles
            else:
                removed.append(RemovedSegment(
                    segment=seg,
                    reason="duration_limit",
                    score=seg.score
                ))
        
        # Merge adjacent segments
        selected = self._merge_adjacent_segments(selected, gap_threshold=1.0)
        
        # Organize by structure
        structure = self._organize_by_structure(selected, CutStyle.REVIEW)
        
        # Flatten to ordered segments
        ordered_segments = []
        for section in style_config['sections']:
            if section in structure:
                ordered_segments.extend(structure[section])
        
        return RoughCutPlan(
            style=CutStyle.REVIEW,
            clips=clips,
            segments=ordered_segments,
            total_duration=sum(s.end_time - s.start_time for s in ordered_segments),
            structure=structure,
            removed_segments=removed
        )
    
    def _create_unboxing_cut(self, clips: List[ClipAnalysis], target_duration: Optional[float] = None) -> RoughCutPlan:
        """Create unboxing rough cut with reveal detection"""
        style_config = self.STYLE_STRUCTURES[CutStyle.UNBOXING]
        
        # Collect all segments
        all_segments = []
        for clip in clips:
            all_segments.extend(clip.best_moments)
            
            # Detect reveals
            if style_config.get('reveal_detection', False):
                reveals = self.transcript_analyzer.detect_reveals(clip)
                all_segments.extend(reveals)
        
        # Remove duplicates
        all_segments = self._deduplicate_segments(all_segments)
        
        # Prioritize reveals and reactions
        if style_config.get('reaction_prioritization', False):
            all_segments.sort(key=lambda x: (x.segment_type == "reveal", x.score), reverse=True)
        else:
            all_segments.sort(key=lambda x: x.score, reverse=True)
        
        # Calculate target duration
        total_raw = sum(c.duration for c in clips)
        if target_duration is None:
            target_duration = total_raw * style_config['target_ratio']
        
        # Select segments
        selected = []
        removed = []
        current_duration = 0.0
        pre_handle = style_config.get('pre_handle', 0.2)
        post_handle = style_config.get('post_handle', 0.2)
        
        for seg in all_segments:
            seg_duration = seg.end_time - seg.start_time
            seg_duration_with_handles = seg_duration + pre_handle + post_handle
            
            if current_duration + seg_duration_with_handles <= target_duration:
                selected.append(seg)
                current_duration += seg_duration_with_handles
            else:
                removed.append(RemovedSegment(
                    segment=seg,
                    reason="duration_limit",
                    score=seg.score
                ))
        
        # Merge adjacent segments
        selected = self._merge_adjacent_segments(selected, gap_threshold=0.5)
        
        # Organize by structure
        structure = self._organize_by_structure(selected, CutStyle.UNBOXING)
        
        # Flatten to ordered segments
        ordered_segments = []
        for section in style_config['sections']:
            if section in structure:
                ordered_segments.extend(structure[section])
        
        return RoughCutPlan(
            style=CutStyle.UNBOXING,
            clips=clips,
            segments=ordered_segments,
            total_duration=sum(s.end_time - s.start_time for s in ordered_segments),
            structure=structure,
            removed_segments=removed
        )
    
    def _create_comparison_cut(self, clips: List[ClipAnalysis], target_duration: Optional[float] = None) -> RoughCutPlan:
        """Create comparison rough cut with product switching"""
        style_config = self.STYLE_STRUCTURES[CutStyle.COMPARISON]
        
        # Collect all segments
        all_segments = []
        for clip in clips:
            all_segments.extend(clip.best_moments)
            
            # Detect comparisons
            if style_config.get('comparison_detection', False):
                comparisons = self.transcript_analyzer.detect_comparisons(clip)
                all_segments.extend(comparisons)
        
        # Remove duplicates
        all_segments = self._deduplicate_segments(all_segments)
        all_segments.sort(key=lambda x: x.score, reverse=True)
        
        # Calculate target duration
        total_raw = sum(c.duration for c in clips)
        if target_duration is None:
            target_duration = total_raw * style_config['target_ratio']
        
        # Select segments
        selected = []
        removed = []
        current_duration = 0.0
        pre_handle = style_config.get('pre_handle', 0.5)
        post_handle = style_config.get('post_handle', 0.4)
        
        for seg in all_segments:
            seg_duration = seg.end_time - seg.start_time
            seg_duration_with_handles = seg_duration + pre_handle + post_handle
            
            if current_duration + seg_duration_with_handles <= target_duration:
                selected.append(seg)
                current_duration += seg_duration_with_handles
            else:
                removed.append(RemovedSegment(
                    segment=seg,
                    reason="duration_limit",
                    score=seg.score
                ))
        
        # Merge adjacent segments
        selected = self._merge_adjacent_segments(selected, gap_threshold=2.0)
        
        # Organize by structure (alternate between products if detected)
        structure = self._organize_by_structure(selected, CutStyle.COMPARISON)
        
        # Flatten to ordered segments
        ordered_segments = []
        for section in style_config['sections']:
            if section in structure:
                ordered_segments.extend(structure[section])
        
        return RoughCutPlan(
            style=CutStyle.COMPARISON,
            clips=clips,
            segments=ordered_segments,
            total_duration=sum(s.end_time - s.start_time for s in ordered_segments),
            structure=structure,
            removed_segments=removed
        )
    
    def _create_setup_cut(self, clips: List[ClipAnalysis], target_duration: Optional[float] = None) -> RoughCutPlan:
        """Create setup guide rough cut with step detection"""
        style_config = self.STYLE_STRUCTURES[CutStyle.SETUP]
        
        # Similar to tutorial but more methodical
        # Prioritize screen recordings if available
        screen_clips = [c for c in clips if c.is_screen_recording]
        other_clips = [c for c in clips if not c.is_screen_recording]
        
        # Collect segments, prioritizing screen recordings
        all_segments = []
        for clip in screen_clips + other_clips:
            all_segments.extend(clip.best_moments)
            # Boost score for screen recordings
            if clip.is_screen_recording:
                for seg in all_segments[-len(clip.best_moments):]:
                    seg.score *= 1.2
        
        # Remove duplicates
        all_segments = self._deduplicate_segments(all_segments)
        all_segments.sort(key=lambda x: x.score, reverse=True)
        
        # Calculate target duration
        total_raw = sum(c.duration for c in clips)
        if target_duration is None:
            target_duration = total_raw * style_config['target_ratio']
        
        # Select segments
        selected = []
        removed = []
        current_duration = 0.0
        pre_handle = style_config.get('pre_handle', 0.3)
        post_handle = style_config.get('post_handle', 0.3)
        
        for seg in all_segments:
            seg_duration = seg.end_time - seg.start_time
            seg_duration_with_handles = seg_duration + pre_handle + post_handle
            
            if current_duration + seg_duration_with_handles <= target_duration:
                selected.append(seg)
                current_duration += seg_duration_with_handles
            else:
                removed.append(RemovedSegment(
                    segment=seg,
                    reason="duration_limit",
                    score=seg.score
                ))
        
        # Merge adjacent segments
        selected = self._merge_adjacent_segments(selected, gap_threshold=1.0)
        
        # Organize by structure
        structure = self._organize_by_structure(selected, CutStyle.SETUP)
        
        # Flatten to ordered segments
        ordered_segments = []
        for section in style_config['sections']:
            if section in structure:
                ordered_segments.extend(structure[section])
        
        return RoughCutPlan(
            style=CutStyle.SETUP,
            clips=clips,
            segments=ordered_segments,
            total_duration=sum(s.end_time - s.start_time for s in ordered_segments),
            structure=structure,
            removed_segments=removed
        )
    
    def _create_explainer_cut(self, clips: List[ClipAnalysis], target_duration: Optional[float] = None) -> RoughCutPlan:
        """Create explainer video rough cut with concept detection"""
        style_config = self.STYLE_STRUCTURES[CutStyle.EXPLAINER]
        
        # Collect all segments
        all_segments = []
        for clip in clips:
            all_segments.extend(clip.best_moments)
            
            # Detect concepts
            if style_config.get('concept_detection', False):
                concepts = self.transcript_analyzer.detect_concepts(clip)
                all_segments.extend(concepts)
        
        # Remove duplicates
        all_segments = self._deduplicate_segments(all_segments)
        all_segments.sort(key=lambda x: x.score, reverse=True)
        
        # Calculate target duration
        total_raw = sum(c.duration for c in clips)
        if target_duration is None:
            target_duration = total_raw * style_config['target_ratio']
        
        # Select segments (more lenient for explainers - keep more content)
        selected = []
        removed = []
        current_duration = 0.0
        pre_handle = style_config.get('pre_handle', 0.6)
        post_handle = style_config.get('post_handle', 0.5)
        
        for seg in all_segments:
            seg_duration = seg.end_time - seg.start_time
            seg_duration_with_handles = seg_duration + pre_handle + post_handle
            
            # Allow 10% overflow for high-quality explainer segments
            if current_duration + seg_duration_with_handles <= target_duration * 1.1:
                selected.append(seg)
                current_duration += seg_duration_with_handles
            else:
                removed.append(RemovedSegment(
                    segment=seg,
                    reason="duration_limit",
                    score=seg.score
                ))
        
        # Merge adjacent segments (more aggressive for explainers)
        selected = self._merge_adjacent_segments(selected, gap_threshold=2.0)
        
        # Organize by structure
        structure = self._organize_by_structure(selected, CutStyle.EXPLAINER)
        
        # Flatten to ordered segments
        ordered_segments = []
        for section in style_config['sections']:
            if section in structure:
                ordered_segments.extend(structure[section])
        
        return RoughCutPlan(
            style=CutStyle.EXPLAINER,
            clips=clips,
            segments=ordered_segments,
            total_duration=sum(s.end_time - s.start_time for s in ordered_segments),
            structure=structure,
            removed_segments=removed
        )

    def export_edl(self, plan: RoughCutPlan, output_path: Path) -> Path:
        """Export rough cut as EDL file with handles for breathing room"""
        lines = [
            "TITLE: StudioFlow Rough Cut",
            f"FCM: NON-DROP FRAME",
            ""
        ]

        # Get handles from style config
        style_config = self.STYLE_STRUCTURES.get(plan.style, {})
        pre_handle = style_config.get('pre_handle', 0.5)   # Default 0.5s before
        post_handle = style_config.get('post_handle', 0.3)  # Default 0.3s after

        # Build clip duration cache for bounds checking
        clip_durations = {c.file_path: c.duration for c in plan.clips}

        timeline_position = 0.0
        for i, seg in enumerate(plan.segments, 1):
            # Apply handles (with bounds checking)
            clip_duration = clip_durations.get(seg.source_file, float('inf'))

            # Extend start earlier (pre-handle) but not before 0
            start_with_handle = max(0.0, seg.start_time - pre_handle)
            # Extend end later (post-handle) but not past clip duration
            end_with_handle = min(clip_duration, seg.end_time + post_handle)

            segment_duration = end_with_handle - start_with_handle

            # EDL format with handles applied
            src_in = self._format_timecode(start_with_handle)
            src_out = self._format_timecode(end_with_handle)
            rec_in = self._format_timecode(timeline_position)
            rec_out = self._format_timecode(timeline_position + segment_duration)

            lines.append(f"{i:03d}  {seg.source_file.stem[:8]}  V  C  {src_in} {src_out} {rec_in} {rec_out}")
            lines.append(f"* FROM CLIP NAME: {seg.source_file.name}")
            if seg.text:
                lines.append(f"* COMMENT: {seg.text[:50]}...")
            # Add marker metadata
            if seg.topic:
                lines.append(f"* TOPIC: {seg.topic}")
            if seg.segment_type and seg.segment_type != "content":
                lines.append(f"* TYPE: {seg.segment_type}")
            lines.append("")

            timeline_position += segment_duration

        output_path.write_text('\n'.join(lines))
        return output_path

    def export_fcpxml(self, plan: RoughCutPlan, output_path: Path) -> Path:
        """Export rough cut as FCPXML for Resolve/FCP"""
        import xml.etree.ElementTree as ET

        fcpxml = ET.Element('fcpxml', version='1.9')
        resources = ET.SubElement(fcpxml, 'resources')

        # Add format
        format_elem = ET.SubElement(resources, 'format', {
            'id': 'r1',
            'name': 'FFVideoFormat1080p30',
            'frameDuration': '1001/30000s',
            'width': '1920',
            'height': '1080'
        })

        # Add assets
        for i, clip in enumerate(plan.clips):
            ET.SubElement(resources, 'asset', {
                'id': f'asset{i}',
                'name': clip.file_path.stem,
                'src': f'file://{clip.file_path}',
                'format': 'r1'
            })

        # Create event and project
        library = ET.SubElement(fcpxml, 'library')
        event = ET.SubElement(library, 'event', name='StudioFlow Rough Cut')
        project = ET.SubElement(event, 'project', name=f'Rough Cut - {plan.style.value}')
        sequence = ET.SubElement(project, 'sequence', format='r1')
        spine = ET.SubElement(sequence, 'spine')

        # Add clips to timeline
        for seg in plan.segments:
            # Find asset id
            asset_id = None
            for i, clip in enumerate(plan.clips):
                if clip.file_path == seg.source_file:
                    asset_id = f'asset{i}'
                    break

            if asset_id:
                duration = seg.end_time - seg.start_time
                clip_elem = ET.SubElement(spine, 'asset-clip', {
                    'ref': asset_id,
                    'offset': f'{int(seg.start_time * 30000)}/30000s',
                    'duration': f'{int(duration * 30000)}/30000s',
                    'start': f'{int(seg.start_time * 30000)}/30000s'
                })
                # Add marker metadata as notes
                metadata = []
                if seg.topic:
                    metadata.append(f"Topic: {seg.topic}")
                if seg.segment_type and seg.segment_type != "content":
                    metadata.append(f"Type: {seg.segment_type}")
                if seg.text:
                    metadata.append(f"Text: {seg.text[:100]}")
                if metadata:
                    note_elem = ET.SubElement(clip_elem, 'note')
                    note_elem.text = " | ".join(metadata)

        tree = ET.ElementTree(fcpxml)
        tree.write(str(output_path), encoding='UTF-8', xml_declaration=True)
        return output_path

    def _format_timecode(self, seconds: float, fps: float = 30.0) -> str:
        """Format seconds as timecode HH:MM:SS:FF"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds % 1) * fps)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"

    def get_summary(self, plan: RoughCutPlan) -> str:
        """Get human-readable summary of rough cut plan"""
        lines = [
            f"Rough Cut Plan - {plan.style.value.upper()}",
            "=" * 40,
            f"Total Duration: {plan.total_duration:.1f}s ({plan.total_duration/60:.1f} min)",
            f"Segments: {len(plan.segments)}",
            f"Source Clips: {len(plan.clips)}",
            "",
            "Structure:",
        ]

        for section, segs in plan.structure.items():
            if segs:
                section_dur = sum(s.end_time - s.start_time for s in segs)
                lines.append(f"  {section}: {len(segs)} segments ({section_dur:.1f}s)")

        lines.extend(["", "Top Moments:"])
        for seg in sorted(plan.segments, key=lambda x: x.score, reverse=True)[:5]:
            preview = seg.text[:60] + '...' if len(seg.text) > 60 else seg.text
            lines.append(f"  [{seg.score:.2f}] {preview}")

        return '\n'.join(lines)
    
    def export_removed_footage_edl(self, plan: RoughCutPlan, output_path: Path) -> Path:
        """Export removed segments as a 'source tape' EDL for review"""
        if not plan.removed_segments:
            # Create empty EDL
            output_path.write_text("TITLE: StudioFlow Removed Footage\nFCM: NON-DROP FRAME\n\n")
            return output_path
        
        lines = [
            "TITLE: StudioFlow Removed Footage (Source Tape)",
            "FCM: NON-DROP FRAME",
            f"* Total removed segments: {len(plan.removed_segments)}",
            ""
        ]
        
        timeline_position = 0.0
        for i, removed in enumerate(plan.removed_segments, 1):
            seg = removed.segment
            seg_duration = seg.end_time - seg.start_time
            
            src_in = self._format_timecode(seg.start_time)
            src_out = self._format_timecode(seg.end_time)
            rec_in = self._format_timecode(timeline_position)
            rec_out = self._format_timecode(timeline_position + seg_duration)
            
            lines.append(f"{i:03d}  {seg.source_file.stem[:8]}  V  C  {src_in} {src_out} {rec_in} {rec_out}")
            lines.append(f"* FROM CLIP NAME: {seg.source_file.name}")
            lines.append(f"* REMOVED REASON: {removed.reason}")
            lines.append(f"* ORIGINAL SCORE: {removed.score:.2f}")
            if seg.text:
                lines.append(f"* TRANSCRIPT: {seg.text[:100]}...")
            lines.append("")
            
            timeline_position += seg_duration
        
        output_path.write_text('\n'.join(lines))
        return output_path
    
    def generate_removed_transcripts(self, plan: RoughCutPlan, output_path: Path) -> Path:
        """Generate transcript of all removed content"""
        if not plan.removed_segments:
            output_path.write_text("# Removed Footage Transcript\n\nNo footage was removed.\n")
            return output_path
        
        lines = [
            "# Removed Footage Transcript",
            f"# Total segments removed: {len(plan.removed_segments)}",
            f"# Total duration: {sum(s.segment.end_time - s.segment.start_time for s in plan.removed_segments):.1f}s",
            ""
        ]
        
        # Group by source file
        by_file = {}
        for removed in plan.removed_segments:
            file_key = str(removed.segment.source_file)
            if file_key not in by_file:
                by_file[file_key] = []
            by_file[file_key].append(removed)
        
        for file_path, removed_list in sorted(by_file.items()):
            lines.append(f"## {Path(file_path).name}")
            lines.append("")
            
            for removed in sorted(removed_list, key=lambda r: r.segment.start_time):
                seg = removed.segment
                timecode = self._format_timecode(seg.start_time)
                duration = seg.end_time - seg.start_time
                
                lines.append(f"### {timecode} ({duration:.1f}s)")
                lines.append(f"**Reason:** {removed.reason}")
                lines.append(f"**Score:** {removed.score:.2f}")
                lines.append("")
                
                if seg.text:
                    lines.append(f"**Transcript:**")
                    lines.append(f"{seg.text}")
                    lines.append("")
                else:
                    lines.append("*No transcript available*")
                    lines.append("")
        
        output_path.write_text('\n'.join(lines))
        return output_path
    
    def generate_removed_visual_descriptions(self, plan: RoughCutPlan, output_path: Path,
                                            extract_thumbnails: bool = True) -> Path:
        """Generate visual descriptions of removed footage with optional thumbnails"""
        if not plan.removed_segments:
            output_path.write_text("# Removed Footage Visual Descriptions\n\nNo footage was removed.\n")
            return output_path
        
        lines = [
            "# Removed Footage Visual Descriptions",
            f"# Total segments removed: {len(plan.removed_segments)}",
            ""
        ]
        
        # Group by source file
        by_file = {}
        for removed in plan.removed_segments:
            file_key = str(removed.segment.source_file)
            if file_key not in by_file:
                by_file[file_key] = []
            by_file[file_key].append(removed)
        
        for file_path, removed_list in sorted(by_file.items()):
            clip_path = Path(file_path)
            lines.append(f"## {clip_path.name}")
            lines.append("")
            
            # Get clip analysis for metadata
            clip_analysis = next((c for c in plan.clips if c.file_path == clip_path), None)
            
            for removed in sorted(removed_list, key=lambda r: r.segment.start_time):
                seg = removed.segment
                timecode = self._format_timecode(seg.start_time)
                duration = seg.end_time - seg.start_time
                midpoint = seg.start_time + (duration / 2)
                
                lines.append(f"### {timecode} ({duration:.1f}s)")
                lines.append(f"**Reason:** {removed.reason}")
                lines.append(f"**Score:** {removed.score:.2f}")
                lines.append("")
                
                # Visual description
                if clip_analysis:
                    description_parts = []
                    
                    if clip_analysis.shot_type:
                        description_parts.append(f"Shot type: {clip_analysis.shot_type}")
                    if clip_analysis.content_type:
                        description_parts.append(f"Content: {clip_analysis.content_type}")
                    if clip_analysis.faces_detected > 0:
                        description_parts.append(f"Faces: {clip_analysis.faces_detected}")
                    if clip_analysis.is_shaky:
                        description_parts.append("Shaky")
                    if clip_analysis.quality_score:
                        description_parts.append(f"Quality: {clip_analysis.quality_score:.0f}/100")
                    
                    if description_parts:
                        lines.append("**Visual Description:**")
                        lines.append(" - ".join(description_parts))
                    else:
                        lines.append("**Visual Description:** *No analysis available*")
                else:
                    lines.append("**Visual Description:** *Clip not analyzed*")
                
                lines.append("")
                
                # Thumbnail extraction
                if extract_thumbnails:
                    thumbnail_path = self._extract_thumbnail_for_segment(seg, midpoint, output_path.parent)
                    if thumbnail_path:
                        lines.append(f"**Thumbnail:** `{thumbnail_path.name}`")
                        lines.append("")
            
            lines.append("---")
            lines.append("")
        
        output_path.write_text('\n'.join(lines))
        return output_path
    
    def _extract_thumbnail_for_segment(self, segment: Segment, timecode: float, 
                                       output_dir: Path) -> Optional[Path]:
        """Extract thumbnail frame from segment"""
        try:
            from studioflow.core.ffmpeg import FFmpegProcessor
            
            thumbnail_name = f"{segment.source_file.stem}_{timecode:.1f}s.jpg"
            thumbnail_path = output_dir / thumbnail_name
            
            result = FFmpegProcessor.generate_thumbnail(
                segment.source_file,
                thumbnail_path,
                timestamp=timecode
            )
            
            if result.success:
                return thumbnail_path
        except Exception:
            pass
        
        return None
    
    def create_source_tape_video(self, plan: RoughCutPlan, output_path: Path) -> Optional[Path]:
        """Create concatenated video of all removed footage (source tape)"""
        if not plan.removed_segments:
            return None
        
        try:
            import subprocess
            from studioflow.core.ffmpeg import FFmpegProcessor
            
            # Create concat file for ffmpeg
            concat_file = output_path.parent / "removed_concat.txt"
            concat_lines = []
            
            for removed in plan.removed_segments:
                seg = removed.segment
                # Escape special characters in path
                file_path = str(seg.source_file).replace("'", "'\\''")
                concat_lines.append(f"file '{file_path}'")
                concat_lines.append(f"inpoint {seg.start_time}")
                concat_lines.append(f"outpoint {seg.end_time}")
            
            concat_file.write_text('\n'.join(concat_lines))
            
            # Use ffmpeg to concatenate
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",  # Stream copy for speed
                "-y",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Clean up concat file
                concat_file.unlink()
                return output_path
            else:
                print(f"Warning: Failed to create source tape: {result.stderr}")
                if concat_file.exists():
                    concat_file.unlink()
        except Exception as e:
            print(f"Warning: Could not create source tape video: {e}")
        
        return None
    
    def generate_hook_test_timelines(self, clips: List[ClipAnalysis], output_dir: Path, 
                                     max_hooks: int = 5) -> List[Path]:
        """Generate multiple hook test timelines for A/B testing on YouTube
        
        Creates multiple hook candidates and exports each as a separate timeline
        to 04_TIMELINES/02_HOOK_TESTS/ directory for Resolve import.
        
        Args:
            clips: List of analyzed clips
            output_dir: Base output directory (should be project root)
            max_hooks: Maximum number of hook candidates to generate (default: 5)
        
        Returns:
            List of exported timeline file paths (EDL and FCPXML)
        """
        # Ensure output directory exists
        hook_tests_dir = output_dir / "04_TIMELINES" / "02_HOOK_TESTS"
        hook_tests_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate multiple hook candidates
        hook_candidates = self._generate_hook_candidates(clips, max_hooks=max_hooks)
        
        if not hook_candidates:
            logger.warning("No hook candidates found for testing")
            return []
        
        exported_files = []
        
        # Export each hook candidate as a separate timeline
        for i, candidate in enumerate(hook_candidates, 1):
            # Use hook flow type if available, otherwise use hook_type
            flow_tag = candidate.hook_flow_type if candidate.hook_flow_type else candidate.hook_type.upper()
            hook_name = f"HOOK_TEST_{i:02d}_{flow_tag}"
            
            # Find the clip that contains this segment
            source_clip = next((c for c in clips if c.file_path == candidate.segment.source_file), None)
            if not source_clip:
                logger.warning(f"Could not find source clip for {candidate.segment.source_file}")
                continue
            
            # Create a minimal rough cut plan for this hook
            hook_plan = RoughCutPlan(
                style=CutStyle.TUTORIAL,
                clips=[source_clip],
                segments=[candidate.segment],
                total_duration=candidate.duration,
                structure={'hook': [candidate.segment]},
                removed_segments=[]
            )
            
            # Export as EDL
            edl_path = hook_tests_dir / f"{hook_name}.edl"
            try:
                self.export_edl(hook_plan, edl_path)
                exported_files.append(edl_path)
            except Exception as e:
                logger.warning(f"Failed to export EDL for {hook_name}: {e}")
            
            # Export as FCPXML (better for Resolve)
            fcpxml_path = hook_tests_dir / f"{hook_name}.fcpxml"
            try:
                self.export_fcpxml(hook_plan, fcpxml_path)
                exported_files.append(fcpxml_path)
            except Exception as e:
                logger.warning(f"Failed to export FCPXML for {hook_name}: {e}")
            
            # Create metadata file for this hook test
            metadata_path = hook_tests_dir / f"{hook_name}_METADATA.txt"
            metadata_content = f"""Hook Test #{i}: {candidate.hook_type.upper()}
========================================

Retention Score: {candidate.retention_score:.1f}%
Energy Score: {candidate.energy_score:.2f}
Clarity Score: {candidate.clarity_score:.2f}
Duration: {candidate.duration:.1f}s
Hook Phrase Present: {candidate.hook_phrase_present}

Source Clip: {candidate.segment.source_file.name}
Start Time: {candidate.segment.start_time:.2f}s
End Time: {candidate.segment.end_time:.2f}s

Transcript:
{candidate.segment.text}

---
Generated by StudioFlow Hook Test Generator
Ready for unlisted YouTube upload for retention testing
"""
            metadata_path.write_text(metadata_content)
            exported_files.append(metadata_path)
        
        # Create summary file
        summary_path = hook_tests_dir / "HOOK_TESTS_SUMMARY.txt"
        summary_content = f"""Hook Tests Generated: {len(hook_candidates)}
========================================

Generated {len(hook_candidates)} hook test timelines for A/B testing.

Files:
"""
        for i, candidate in enumerate(hook_candidates, 1):
            flow_tag = candidate.hook_flow_type if candidate.hook_flow_type else candidate.hook_type.upper()
            flow_info = f" ({candidate.hook_flow_type} - {candidate.flow_performance_multiplier}x multiplier)" if candidate.hook_flow_type else ""
            summary_content += f"\n{i}. HOOK_TEST_{i:02d}_{flow_tag}{flow_info}\n"
            summary_content += f"   Retention Score: {candidate.retention_score:.1f}%\n"
            summary_content += f"   Duration: {candidate.duration:.1f}s\n"
            summary_content += f"   Files: HOOK_TEST_{i:02d}_*.edl, HOOK_TEST_{i:02d}_*.fcpxml\n"
        
        summary_content += f"""

Import to Resolve:
1. Open DaVinci Resolve
2. File → Import → Timeline → Import AAF, EDL, XML, FCPXML...
3. Select the .fcpxml files from this directory
4. Each hook test will be imported as a separate timeline

Export for YouTube:
1. Render each timeline as 1080p, 16-20Mbps
2. Upload as unlisted videos
3. Compare retention analytics after 24-48 hours
4. Select best performing hook for final video

Best Hook Recommendation:
"""
        if hook_candidates:
            best = max(hook_candidates, key=lambda x: x.retention_score)
            best_idx = hook_candidates.index(best) + 1
            best_flow_tag = best.hook_flow_type if best.hook_flow_type else best.hook_type.upper()
            summary_content += f"HOOK_TEST_{best_idx:02d}_{best_flow_tag}\n"
            summary_content += f"Retention Score: {best.retention_score:.1f}%\n"
            if best.hook_flow_type:
                summary_content += f"Hook Flow Type: {best.hook_flow_type} ({best.flow_performance_multiplier}x multiplier)\n"
        
        summary_path.write_text(summary_content)
        exported_files.append(summary_path)
        
        logger.info(f"Generated {len(hook_candidates)} hook test timelines in {hook_tests_dir}")
        return exported_files
    
    def _calculate_audio_energy(self, clip: ClipAnalysis, start_time: float, end_time: float) -> float:
        """Calculate audio energy level (0-1) for hook optimization"""
        # Simplified: check if clip has good audio level
        if clip.audio_level == "normal" or clip.audio_level == "loud":
            return 0.8
        elif clip.audio_level == "quiet":
            return 0.5
        else:
            return 0.3
    
    def _calculate_clarity_score(self, text: str) -> float:
        """Calculate clarity score (0-1) - no filler words, clear speech"""
        text_lower = text.lower()
        
        # Count filler words
        filler_patterns = [
            r'\bum+\b', r'\buh+\b', r'\bah+\b', r'\blike\b', r'\byou know\b',
            r'\bso+\b', r'\bbasically\b', r'\bactually\b', r'\bi mean\b'
        ]
        
        filler_count = sum(1 for pattern in filler_patterns if re.search(pattern, text_lower))
        word_count = len(text.split())
        
        if word_count == 0:
            return 0.0
        
        filler_ratio = filler_count / word_count
        
        # Score: 1.0 = no fillers, 0.0 = all fillers
        return max(0.0, 1.0 - (filler_ratio * 2.0))  # Penalize fillers
    
    # YouTube Hook Flow Performance Multipliers (based on 2025 best practices)
    # These multipliers boost retention scores for proven hook patterns
    HOOK_FLOW_MULTIPLIERS = {
        'CH': 1.3,      # Curiosity Hook - High engagement
        'AH': 1.25,     # Action Hook - Immediate engagement
        'PSH': 1.2,     # Problem-Solution Hook - Clear value
        'TPH': 1.15,    # Time-Promise Hook - Specific value
        'COH': 1.35,    # Contrarian Hook - Pattern interrupt (highest)
        'VH': 1.1,      # Visual Hook - Depends on visuals
        'SH': 1.2,      # Statistic Hook - Credibility
        'QH': 1.15,     # Question Hook - Engagement
        'VALUE_PROP': 1.1,  # Value Proposition - Standard
        'REVEAL': 1.25,     # Reveal Hook - Curiosity
        'PROMISE': 1.15,    # Promise Hook - Value
    }
    
    def _generate_hook_candidates(self, clips: List[ClipAnalysis], max_hooks: int = 5) -> List[HookCandidate]:
        """Generate multiple hook candidates for A/B testing
        
        Prioritizes clips with named hook flow types (CH, AH, PSH, etc.)
        and applies performance multipliers based on proven YouTube patterns.
        
        Returns:
            List of HookCandidate objects, sorted by retention score (best first)
        """
        candidates = []
        
        # Priority 1: Clips with named hook flow types (highest priority)
        named_hook_clips = [c for c in clips if c.is_hook and c.hook_flow_type]
        # Priority 2: Clips explicitly marked as hooks
        hook_clips = [c for c in clips if c.is_hook and not c.hook_flow_type]
        # Priority 3: First 3 clips if no explicit hooks
        search_clips = named_hook_clips if named_hook_clips else (hook_clips if hook_clips else clips[:3])
        
        for clip in search_clips:
            if not clip.entries:
                continue
            
            # Analyze first 60 seconds for hook candidates
            first_60_seconds = [e for e in clip.entries if e.end_time <= 60.0]
            
            for i, entry in enumerate(first_60_seconds):
                # Check if this entry contains hook phrases
                hook_phrases = [
                    (r"in this video.*?show you", "value_prop"),
                    (r"i'm going to.*?teach you", "value_prop"),
                    (r"by the end.*?you'll know", "promise"),
                    (r"you won't believe.*?", "reveal"),
                    (r"today.*?reveal.*?secret", "reveal"),
                    (r"in this.*?tutorial", "value_prop"),
                    (r"i'll show you.*?how", "value_prop"),
                    (r"learn.*?in.*?minutes", "promise"),
                    (r"watch.*?to.*?learn", "value_prop"),
                    (r"here's.*?how", "value_prop")
                ]
                
                hook_type = "generic"
                has_hook_phrase = False
                
                for pattern, htype in hook_phrases:
                    if re.search(pattern, entry.text.lower()):
                        hook_type = htype
                        has_hook_phrase = True
                        break
                
                # Build candidate segment (5-15 seconds ideal)
                start_time = entry.start_time
                end_time = min(entry.end_time, start_time + 15.0)  # Max 15s
                
                # Extend to include complete sentences if needed
                if end_time - start_time < 5.0:
                    # Try to extend to 5-15 seconds
                    for j in range(i, min(i + 5, len(clip.entries))):
                        if clip.entries[j].end_time - start_time <= 15.0:
                            end_time = clip.entries[j].end_time
                        else:
                            break
                
                duration = end_time - start_time
                
                # Score this hook candidate
                if 5.0 <= duration <= 15.0:  # Ideal duration
                    # Calculate scores
                    energy_score = self._calculate_audio_energy(clip, start_time, end_time)
                    clarity_score = self._calculate_clarity_score(entry.text)
                    
                    # Retention prediction (simplified)
                    retention_score = (
                        (1.0 if has_hook_phrase else 0.5) * 40.0 +  # Hook phrase: 40%
                        energy_score * 30.0 +  # Energy: 30%
                        clarity_score * 20.0 +  # Clarity: 20%
                        (1.0 if 5.0 <= duration <= 15.0 else 0.5) * 10.0  # Duration: 10%
                    )
                    
                    if retention_score > 50.0:  # Lower threshold to get more candidates
                        candidate = HookCandidate(
                            segment=Segment(
                                source_file=clip.file_path,
                                start_time=start_time,
                                end_time=end_time,
                                text=entry.text,
                                score=retention_score / 100.0,
                                segment_type="hook"
                            ),
                            retention_score=retention_score,
                            energy_score=energy_score,
                            clarity_score=clarity_score,
                            duration=duration,
                            hook_type=hook_type,
                            hook_phrase_present=has_hook_phrase
                        )
                        candidates.append(candidate)
        
        # Sort by retention score (best first) and return top N
        candidates.sort(key=lambda x: x.retention_score, reverse=True)
        return candidates[:max_hooks]
