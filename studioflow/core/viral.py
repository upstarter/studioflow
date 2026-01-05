"""
Viral content optimization module
Ported from sf-youtube for title generation, hooks, and retention optimization
"""

import random
import re
from typing import List, Dict, Any
from datetime import datetime


class ViralOptimizer:
    """Generate viral-optimized content for maximum engagement"""

    # Psychological triggers for viral titles
    TRIGGERS = {
        "curiosity": [
            "You Won't Believe",
            "This Changes Everything",
            "Nobody Talks About This",
            "The Secret",
            "What They Don't Tell You",
            "The Truth About",
            "Hidden",
            "Revealed",
            "Exposed",
            "Nobody Expected"
        ],
        "urgency": [
            "Before It's Too Late",
            "Last Chance",
            "Right Now",
            "Today Only",
            "Limited Time",
            "Breaking",
            "Just Happened",
            "Emergency",
            "Alert",
            "Warning"
        ],
        "social_proof": [
            "Everyone Is",
            "Million People",
            "Goes Viral",
            "Breaking the Internet",
            "Most Popular",
            "#1",
            "Top Rated",
            "Best",
            "Everyone's Talking About",
            "Trending"
        ],
        "emotion": [
            "Mind-Blowing",
            "Shocking",
            "Insane",
            "Crazy",
            "Unbelievable",
            "Amazing",
            "Incredible",
            "Life-Changing",
            "Game-Changer",
            "Revolutionary"
        ],
        "fear_missing_out": [
            "Before Everyone Else",
            "Only Few Know",
            "Secret Method",
            "Insider",
            "Exclusive",
            "First Look",
            "Early Access",
            "Behind the Scenes",
            "Never Seen Before",
            "Rare"
        ]
    }

    # Platform-specific constraints
    PLATFORM_LIMITS = {
        "youtube": {
            "title_max": 100,
            "title_optimal": 60,
            "description_max": 5000,
            "tags_max": 500
        },
        "instagram": {
            "title_max": 125,
            "description_max": 2200,
            "hashtags_max": 30
        },
        "tiktok": {
            "title_max": 100,
            "description_max": 2200,
            "hashtags_max": 100
        }
    }

    def generate_titles(self,
                        topic: str,
                        style: str = "educational",
                        platform: str = "youtube",
                        count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate viral-optimized titles

        Args:
            topic: Main topic/keyword
            style: Content style (educational/entertainment/tutorial/review)
            platform: Target platform
            count: Number of titles to generate

        Returns:
            List of title variants with CTR predictions
        """
        titles = []
        templates = self._get_templates(style)

        for _ in range(count):
            template = random.choice(templates)
            trigger = random.choice(list(self.TRIGGERS.keys()))
            trigger_word = random.choice(self.TRIGGERS[trigger])

            # Generate title variants
            title_variants = [
                f"{trigger_word}: {topic}",
                f"{topic} - {trigger_word}",
                f"How {topic} {trigger_word}",
                f"Why {topic} Is {trigger_word}",
                f"The {trigger_word} {topic} Method",
                f"{topic}: {trigger_word} Results",
                f"I Tried {topic} - {trigger_word}!",
                f"{trigger_word} {topic} Hack",
                f"{topic} {trigger_word} (TESTED)",
                f"Stop! {topic} {trigger_word}"
            ]

            title = random.choice(title_variants)

            # Ensure within platform limits
            max_len = self.PLATFORM_LIMITS[platform]["title_optimal"]
            if len(title) > max_len:
                title = title[:max_len-3] + "..."

            # Add power elements
            title = self._add_power_elements(title, style)

            # Calculate CTR prediction
            ctr_score = self._calculate_ctr_score(title, trigger)

            titles.append({
                "title": title,
                "trigger": trigger,
                "ctr_prediction": f"{ctr_score}%",
                "length": len(title),
                "platform_optimized": platform
            })

        # Sort by CTR prediction
        titles.sort(key=lambda x: float(x["ctr_prediction"].rstrip('%')), reverse=True)
        return titles

    def _get_templates(self, style: str) -> List[str]:
        """Get title templates based on content style"""
        templates = {
            "educational": [
                "Learn {topic} in {time}",
                "{topic} Explained",
                "Master {topic}",
                "{topic} 101",
                "Complete {topic} Guide"
            ],
            "entertainment": [
                "{reaction} to {topic}",
                "{topic} Gone Wrong",
                "Trying {topic}",
                "{topic} Challenge",
                "{topic} Prank"
            ],
            "tutorial": [
                "How to {topic}",
                "{topic} Tutorial",
                "{topic} Step by Step",
                "DIY {topic}",
                "{topic} for Beginners"
            ],
            "review": [
                "{topic} Review",
                "Is {topic} Worth It?",
                "{topic} Honest Opinion",
                "Testing {topic}",
                "{topic} vs {alternative}"
            ]
        }
        return templates.get(style, templates["educational"])

    def _add_power_elements(self, title: str, style: str) -> str:
        """Add power elements to increase CTR"""
        power_elements = {
            "numbers": ["2024", "2025", "10X", "100%", "#1", "5 Minutes"],
            "brackets": ["[TESTED]", "[NEW]", "[UPDATED]", "[WORKING]", "[PROOF]"],
            "emoji": ["🔥", "💰", "⚡", "🚀", "💯", "⭐"],
            "caps": ["INSTANTLY", "NOW", "TODAY", "FAST", "EASY"]
        }

        # Add year if educational or tutorial
        if style in ["educational", "tutorial"] and "2024" not in title and "2025" not in title:
            if random.random() > 0.5:
                title += " (2025)"

        # Add brackets occasionally
        if random.random() > 0.7:
            bracket = random.choice(power_elements["brackets"])
            title += f" {bracket}"

        return title

    def _calculate_ctr_score(self, title: str, trigger: str) -> float:
        """Calculate predicted CTR based on title elements"""
        base_ctr = 4.0  # Base CTR

        # Trigger bonuses
        trigger_scores = {
            "curiosity": 2.5,
            "urgency": 2.0,
            "social_proof": 1.8,
            "emotion": 2.2,
            "fear_missing_out": 2.3
        }
        base_ctr += trigger_scores.get(trigger, 1.0)

        # Length bonus (50-70 chars is optimal)
        title_len = len(title)
        if 50 <= title_len <= 70:
            base_ctr += 1.0
        elif title_len > 90:
            base_ctr -= 1.0

        # Power word bonuses
        power_words = ["secret", "hack", "instant", "free", "proven", "guaranteed"]
        for word in power_words:
            if word.lower() in title.lower():
                base_ctr += 0.5

        # Caps and numbers bonus
        if any(c.isupper() for c in title.split()):
            base_ctr += 0.3
        if any(c.isdigit() for c in title):
            base_ctr += 0.4

        # Add some randomness
        base_ctr += random.uniform(-0.5, 0.5)

        # Ensure reasonable range
        return min(max(base_ctr, 3.0), 12.0)

    def generate_hooks(self, topic: str, duration: int = 3) -> List[str]:
        """
        Generate attention hooks for video intros

        Args:
            topic: Video topic
            duration: Target hook duration in seconds

        Returns:
            List of hook scripts
        """
        hooks = []

        # Question hooks
        hooks.append(f"What if I told you {topic} could change everything?")
        hooks.append(f"Did you know that {topic} is actually...?")
        hooks.append(f"Why is nobody talking about {topic}?")

        # Statement hooks
        hooks.append(f"This {topic} trick will blow your mind.")
        hooks.append(f"I discovered something about {topic} that shocked me.")
        hooks.append(f"Everything you know about {topic} is wrong.")

        # Challenge hooks
        hooks.append(f"99% of people get {topic} wrong. Here's why.")
        hooks.append(f"I bet you can't do {topic} like this.")
        hooks.append(f"Try {topic} for 30 days and this happens...")

        # Story hooks
        hooks.append(f"Last week, {topic} completely changed my life.")
        hooks.append(f"I failed at {topic} 10 times. Then this happened.")
        hooks.append(f"Nobody believed {topic} would work. I proved them wrong.")

        return hooks

    def optimize_description(self,
                             title: str,
                             topic: str,
                             platform: str = "youtube") -> str:
        """
        Generate optimized video description

        Args:
            title: Video title
            topic: Video topic
            platform: Target platform

        Returns:
            Optimized description with timestamps and CTAs
        """
        description_parts = []

        # Opening hook (mirrors title)
        description_parts.append(f"🎬 {title}\n")

        # Brief explanation
        description_parts.append(f"In this video, I reveal everything about {topic}. ")
        description_parts.append("This is the complete guide you've been looking for.\n\n")

        # Timestamps placeholder
        description_parts.append("⏱️ TIMESTAMPS:\n")
        description_parts.append("00:00 - Introduction\n")
        description_parts.append("00:30 - The Problem\n")
        description_parts.append("02:00 - The Solution\n")
        description_parts.append("05:00 - Real Examples\n")
        description_parts.append("08:00 - Your Next Steps\n\n")

        # Value proposition
        description_parts.append("🔥 WHAT YOU'LL LEARN:\n")
        description_parts.append(f"✅ The truth about {topic}\n")
        description_parts.append(f"✅ Step-by-step {topic} guide\n")
        description_parts.append(f"✅ Common {topic} mistakes to avoid\n")
        description_parts.append(f"✅ Advanced {topic} strategies\n\n")

        # Call to action
        description_parts.append("👍 SUPPORT THE CHANNEL:\n")
        description_parts.append("► Subscribe for more content\n")
        description_parts.append("► Like if this helped you\n")
        description_parts.append("► Comment your questions below\n\n")

        # SEO keywords
        description_parts.append(f"🏷️ TOPICS: {topic}, ")
        description_parts.append(f"how to {topic}, {topic} tutorial, ")
        description_parts.append(f"{topic} guide, {topic} tips, ")
        description_parts.append(f"{topic} 2025\n\n")

        # Social links placeholder
        description_parts.append("📱 CONNECT:\n")
        description_parts.append("► Instagram: @yourchannel\n")
        description_parts.append("► Twitter: @yourchannel\n")

        full_description = "".join(description_parts)

        # Ensure within platform limits
        max_len = self.PLATFORM_LIMITS[platform]["description_max"]
        if len(full_description) > max_len:
            full_description = full_description[:max_len-3] + "..."

        return full_description

    def analyze_retention_curve(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze transcript for retention optimization

        Args:
            transcript: Video transcript text

        Returns:
            Retention analysis with suggestions
        """
        analysis = {
            "hook_strength": 0,
            "pattern_interrupts": [],
            "open_loops": [],
            "cta_placements": [],
            "improvements": []
        }

        # Check hook (first 50 words)
        first_words = transcript.split()[:50]
        hook_text = " ".join(first_words)

        if any(word in hook_text.lower() for word in ["what if", "did you know", "secret"]):
            analysis["hook_strength"] = 8
        else:
            analysis["hook_strength"] = 4
            analysis["improvements"].append("Add stronger curiosity hook in first 3 seconds")

        # Find pattern interrupts (topic changes)
        sentences = transcript.split(".")
        for i in range(0, len(sentences), 10):  # Check every ~30 seconds
            if i > 0:
                analysis["pattern_interrupts"].append(f"Segment {i//10}: Add visual change or story")

        # Suggest open loops
        analysis["open_loops"] = [
            "Tease the main reveal early",
            "Mention 'coming up' segments",
            "Create mystery around key points"
        ]

        # CTA placements
        analysis["cta_placements"] = [
            "0:30 - Soft subscribe reminder",
            "Middle - Like button reminder",
            "End - Strong subscribe CTA"
        ]

        return analysis