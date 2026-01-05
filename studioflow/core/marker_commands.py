"""
Audio Marker Command Parsing
Parses and normalizes commands from audio markers (between "slate" and "done")
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ParsedCommands:
    """Parsed marker commands"""
    naming: Optional[str] = None  # "naming setup" -> "setup"
    mark: bool = False  # "mark" command flag
    take: Optional[int] = None  # "take one" -> 1 (multiple attempts at same scene)
    order: Optional[int] = None  # "order one" -> 1 (position in final sequence)
    step: Optional[int] = None  # "step five" -> 5
    segment_type: Optional[str] = None  # "type camera" -> "camera"
    quality: Optional[str] = None  # "best", "select", "backup"
    hook: Optional[str] = None  # "hook coh" -> "coh"
    title: Optional[str] = None  # "title Intro" -> "Intro"
    title_type: Optional[str] = None  # "title lower third Intro" -> "lower third"
    effect: Optional[str] = None  # "effect mtuber intro" -> "mtuber:intro"
    effect_product: Optional[str] = None
    effect_name: Optional[str] = None
    transition: Optional[str] = None  # "transition mtuber fade" -> "mtuber:fade"
    transition_product: Optional[str] = None
    transition_name: Optional[str] = None
    transition_generic: Optional[str] = None  # "warp", "dissolve", "fade"
    screen: Optional[str] = None  # "screen hud" -> "hud"
    cta: Optional[str] = None  # "cta subscribe" -> "subscribe"
    chapter: Optional[str] = None  # "chapter config" -> "config"
    broll: Optional[str] = None  # "broll screen" -> "screen"
    ending: bool = False  # "ending" command flag (backwards compatible)
    
    # Retroactive actions (for previous segment)
    retroactive_actions: List[str] = field(default_factory=list)  # Actions after "apply"
    
    # Score system (4-level: skip, fair, good, best)
    score: Optional[str] = None  # Score level from retroactive actions
    score_level: Optional[int] = None  # Numeric score (0-3)
    
    # Emotion and energy markers
    emotion: Optional[str] = None  # "emotion energetic" -> "energetic"
    energy: Optional[str] = None  # "energy high" -> "high"
    
    # Scene numbering (replaces "order" for sequence positioning)
    scene_number: Optional[float] = None  # "scene one" -> 1.0, "scene one point five" -> 1.5
    scene_name: Optional[str] = None  # "scene one intro" -> "intro"
    
    # Raw commands for reference
    raw_commands: List[str] = field(default_factory=list)


class MarkerCommandParser:
    """Parse and normalize marker commands"""
    
    # Number word mapping
    NUMBER_WORDS = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
        "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
        "eighteen": 18, "nineteen": 19, "twenty": 20
    }
    
    # Score levels (used after "apply")
    SCORE_LEVELS = ["skip", "fair", "good", "best"]
    SCORE_SCALE = {
        "skip": 0,      # Remove/skip
        "fair": 1,      # Usable but not great (backup)
        "good": 2,      # Good quality (solid content)
        "best": 3       # Top tier (only one)
    }
    
    # Fuzzy normalization mappings
    NORMALIZATION_MAP = {
        # B-roll variations
        "broll": ["broll", "b roll", "b-roll", "b_roll", "be roll"],
        "cta": ["cta", "c t a", "see t a", "see tea"],
        # Quality markers
        "best": ["best", "best take"],
        "select": ["select", "selected"],
        "backup": ["backup", "back up"],
        # Hook types
        "coh": ["coh", "c o h", "cold open hook"],
        "ch": ["ch", "c h", "cold hook"],
        "psh": ["psh", "p s h", "pattern shift hook"],
        "tph": ["tph", "t p h", "third person hook"],
        # Transitions
        "warp": ["warp", "speed warp"],
        "dissolve": ["dissolve", "cross dissolve"],
        "fade": ["fade", "fade out", "fade in"],
    }
    
    def normalize_word(self, word: str) -> str:
        """Normalize a word using fuzzy matching"""
        word_lower = word.lower().strip()
        
        # Check normalization map
        for normalized, variations in self.NORMALIZATION_MAP.items():
            if word_lower in variations:
                return normalized
        
        return word_lower
    
    def parse_number(self, word: str) -> Optional[int]:
        """Parse number from word (e.g., 'one' -> 1, '5' -> 5)"""
        word_lower = word.lower().strip()
        
        # Check word mapping
        if word_lower in self.NUMBER_WORDS:
            return self.NUMBER_WORDS[word_lower]
        
        # Try direct integer
        try:
            return int(word_lower)
        except ValueError:
            return None
    
    def parse_decimal_number(self, words: List[str], start_idx: int) -> tuple[Optional[float], int]:
        """
        Parse decimal number from words (e.g., 'one point five' -> 1.5)
        
        Returns:
            (parsed_number, next_index) - parsed number and index after last consumed word
        """
        if start_idx >= len(words):
            return None, start_idx
        
        # Parse integer part
        first_word = words[start_idx].lower().strip()
        integer_part = None
        
        if first_word in self.NUMBER_WORDS:
            integer_part = self.NUMBER_WORDS[first_word]
        else:
            try:
                integer_part = int(first_word)
            except ValueError:
                return None, start_idx
        
        # Check for decimal point
        if start_idx + 1 >= len(words):
            return float(integer_part), start_idx + 1
        
        if words[start_idx + 1].lower().strip() == "point":
            # Parse decimal part (can be multiple digits: "two five" = 25 → 0.25)
            # Support up to 3 decimal places (0.001 precision)
            if start_idx + 2 >= len(words):
                return float(integer_part), start_idx + 2
            
            # Collect all digits after "point" (up to 3 digits for 0.001 precision)
            decimal_digits = []
            j = start_idx + 2
            max_decimal_digits = 3  # Limit to 3 decimal places (0.001 precision)
            
            while j < len(words) and len(decimal_digits) < max_decimal_digits:
                digit_word = words[j].lower().strip()
                
                # Check if it's a number word or digit
                if digit_word in self.NUMBER_WORDS:
                    digit = self.NUMBER_WORDS[digit_word]
                    if 0 <= digit <= 9:  # Single digit only
                        decimal_digits.append(digit)
                        j += 1
                    else:
                        break  # Multi-digit number word (e.g., "ten"), stop
                else:
                    try:
                        digit = int(digit_word)
                        if 0 <= digit <= 9:  # Single digit only
                            decimal_digits.append(digit)
                            j += 1
                        else:
                            break  # Multi-digit number, stop
                    except ValueError:
                        break  # Not a number, stop
            
            if decimal_digits:
                # Convert digits to decimal value
                # Example: [2, 5] → 0.25, [1, 2, 5] → 0.125
                decimal_value = 0.0
                for i, digit in enumerate(decimal_digits):
                    decimal_value += digit / (10 ** (i + 1))
                result = float(integer_part) + decimal_value
                return result, j
            else:
                # No valid decimal digits found
                return float(integer_part), start_idx + 2
        
        # No decimal point, just integer
        return float(integer_part), start_idx + 1
    
    def parse(self, commands: List[str]) -> ParsedCommands:
        """
        Parse commands into structured data
        
        Args:
            commands: List of command words (between "slate" and "done")
        
        Returns:
            ParsedCommands object with parsed data
        """
        parsed = ParsedCommands(raw_commands=commands)
        
        # Normalize all commands
        normalized = [self.normalize_word(cmd) for cmd in commands]
        
        i = 0
        while i < len(normalized):
            cmd = normalized[i]
            
            # Check for "apply" - retroactive actions for previous segment
            if cmd == "apply":
                # Collect all commands after "apply" until "done"
                i += 1  # Skip "apply"
                while i < len(normalized):
                    next_cmd = normalized[i]
                    # Check if next word is "done" (or variant)
                    if next_cmd in ["done", "don", "dun", "dunn", "doan", "doone"]:
                        break
                    parsed.retroactive_actions.append(next_cmd)
                    i += 1
                # Process retroactive actions to extract score
                for action in parsed.retroactive_actions:
                    if action in self.SCORE_LEVELS:
                        parsed.score = action
                        parsed.score_level = self.SCORE_SCALE[action]
                        break
                continue
            
            # Check for "ending" - DEPRECATED: Use "apply" instead
            # "ending" is kept for backwards compatibility but should be replaced with "apply"
            if cmd == "ending":
                import warnings
                warnings.warn(
                    "The 'ending' marker is deprecated. Use 'apply' for retroactive actions instead. "
                    "Example: 'slate apply conclusion done' instead of 'slate ending conclusion done'",
                    DeprecationWarning,
                    stacklevel=2
                )
                
                # Check if there are commands after "ending" (before "done")
                has_commands = False
                j = i + 1
                while j < len(normalized):
                    next_cmd = normalized[j]
                    if next_cmd in ["done", "don", "dun", "dunn", "doan", "doone"]:
                        break
                    has_commands = True
                    parsed.retroactive_actions.append(next_cmd)  # Treat as retroactive
                    j += 1
                
                if has_commands:
                    # "ending" with commands → treat as "apply" (retroactive)
                    parsed.ending = False  # Not a sequence end
                    # Process retroactive actions to extract score
                    for action in parsed.retroactive_actions:
                        if action in self.SCORE_LEVELS:
                            parsed.score = action
                            parsed.score_level = self.SCORE_SCALE[action]
                            break
                    i = j  # Move past all commands
                else:
                    # "ending" alone → DEPRECATED: No longer creates sequence end
                    # Segments naturally end at next marker or end of video
                    # This is kept for backwards compatibility but does nothing
                    parsed.ending = False  # Changed: no longer marks sequence end
                    i += 1
                continue
            
            # Check for "emotion"
            if cmd == "emotion" and i + 1 < len(normalized):
                parsed.emotion = normalized[i + 1]
                i += 2
                continue
            
            # Check for "energy"
            if cmd == "energy" and i + 1 < len(normalized):
                parsed.energy = normalized[i + 1]
                i += 2
                continue
            
            # Check for "naming" - TEMPORARILY DISABLED
            # TODO: Re-enable when we have a clear single-word naming convention
            # For now, naming is disabled to avoid ambiguity with multi-word names
            # If enabled, should be: "naming <single-word> done"
            # Example: "slate naming introduction done" → naming: "introduction"
            if cmd == "naming" and i + 1 < len(normalized):
                # For now, skip "naming" keyword entirely
                # In future: take exactly ONE word after "naming"
                # parsed.naming = commands[i + 1] if i + 1 < len(commands) else None
                # i += 2
                i += 1  # Skip "naming" for now
                continue
            
            # Check for "mark"
            if cmd == "mark":
                parsed.mark = True
                i += 1
                continue
            
            # Check for "scene" (with optional number and name)
            # Examples: "scene one", "scene one point five", "scene one intro"
            if cmd == "scene" and i + 1 < len(normalized):
                # Try to parse scene number (integer or decimal)
                scene_num, next_idx = self.parse_decimal_number(commands, i + 1)
                if scene_num is not None:
                    parsed.scene_number = scene_num
                    # Check if there's a name after the number
                    if next_idx < len(commands):
                        # Collect name (everything until next keyword or "done")
                        name_words = []
                        j = next_idx
                        while j < len(normalized):
                            next_cmd = normalized[j]
                            if next_cmd in ["mark", "take", "order", "step", "type", "hook", "title",
                                           "effect", "transition", "screen", "cta", "chapter", "broll",
                                           "emotion", "energy", "apply", "ending", "done", "don", "dun", "dunn", "doan", "doone"]:
                                break
                            name_words.append(commands[j])  # Use original case
                            j += 1
                        if name_words:
                            parsed.scene_name = " ".join(name_words)
                        i = j
                    else:
                        i = next_idx
                else:
                    # No number, just scene name
                    name_words = []
                    j = i + 1
                    while j < len(normalized):
                        next_cmd = normalized[j]
                        if next_cmd in ["mark", "take", "order", "step", "type", "hook", "title",
                                       "effect", "transition", "screen", "cta", "chapter", "broll",
                                       "emotion", "energy", "apply", "ending", "done", "don", "dun", "dunn", "doan", "doone"]:
                            break
                        name_words.append(commands[j])  # Use original case
                        j += 1
                    if name_words:
                        parsed.scene_name = " ".join(name_words)
                    i = j
                continue
            
            # Check for "take" (multiple attempts at same scene)
            if cmd == "take" and i + 1 < len(normalized):
                num = self.parse_number(normalized[i + 1])
                if num is not None:
                    parsed.take = num
                i += 2
                continue
            
            # Check for "order" (DEPRECATED - use scene number instead)
            # Kept for backwards compatibility, maps to scene_number
            if cmd == "order" and i + 1 < len(normalized):
                num = self.parse_number(normalized[i + 1])
                if num is not None:
                    parsed.order = num  # Keep for backwards compatibility
                    # Also set scene_number if not already set
                    if parsed.scene_number is None:
                        parsed.scene_number = float(num)
                i += 2
                continue
            
            # Check for "step"
            if cmd == "step" and i + 1 < len(normalized):
                num = self.parse_number(normalized[i + 1])
                if num is not None:
                    parsed.step = num
                i += 2
                continue
            
            # Check for "type"
            if cmd == "type" and i + 1 < len(normalized):
                parsed.segment_type = normalized[i + 1]
                i += 2
                continue
            
            # Check for quality markers
            if cmd in ["best", "select", "backup"]:
                parsed.quality = cmd
                i += 1
                continue
            
            # Check for "hook"
            if cmd == "hook" and i + 1 < len(normalized):
                parsed.hook = normalized[i + 1]
                i += 2
                continue
            
            # Check for "title"
            if cmd == "title":
                # Title can be "title Text" or "title lower third Text"
                if i + 2 < len(normalized) and normalized[i + 1] in ["lower", "full", "upper"]:
                    parsed.title_type = normalized[i + 1]
                    if i + 2 < len(normalized) and normalized[i + 2] == "third":
                        parsed.title_type = f"{normalized[i + 1]} third"
                        title_start = i + 3
                    else:
                        title_start = i + 2
                else:
                    title_start = i + 1
                
                # Collect title text
                title_words = []
                j = title_start
                while j < len(normalized):
                    next_cmd = normalized[j]
                    if next_cmd in ["mark", "order", "step", "type", "hook", "effect",
                                   "transition", "screen", "cta", "chapter", "broll"]:
                        break
                    title_words.append(commands[j])  # Use original case
                    j += 1
                parsed.title = " ".join(title_words) if title_words else None
                i = j
                continue
            
            # Check for "effect"
            if cmd == "effect" and i + 2 < len(normalized):
                parsed.effect_product = normalized[i + 1]
                parsed.effect_name = normalized[i + 2]
                parsed.effect = f"{normalized[i + 1]}:{normalized[i + 2]}"
                i += 3
                continue
            
            # Check for "transition"
            if cmd == "transition":
                if i + 2 < len(normalized):
                    # Product transition: "transition mtuber fade"
                    parsed.transition_product = normalized[i + 1]
                    parsed.transition_name = normalized[i + 2]
                    parsed.transition = f"{normalized[i + 1]}:{normalized[i + 2]}"
                    i += 3
                elif i + 1 < len(normalized):
                    # Generic transition: "transition warp"
                    parsed.transition_generic = normalized[i + 1]
                    parsed.transition = normalized[i + 1]
                    i += 2
                else:
                    i += 1
                continue
            
            # Check for "screen"
            if cmd == "screen" and i + 1 < len(normalized):
                parsed.screen = normalized[i + 1]
                i += 2
                continue
            
            # Check for "cta"
            if cmd == "cta" and i + 1 < len(normalized):
                parsed.cta = normalized[i + 1]
                i += 2
                continue
            
            # Check for "chapter"
            if cmd == "chapter" and i + 1 < len(normalized):
                # Collect chapter name
                chapter_words = []
                j = i + 1
                while j < len(normalized):
                    next_cmd = normalized[j]
                    if next_cmd in ["mark", "order", "step", "type", "hook", "title",
                                   "effect", "transition", "screen", "cta", "broll"]:
                        break
                    chapter_words.append(commands[j])  # Use original case
                    j += 1
                parsed.chapter = " ".join(chapter_words) if chapter_words else None
                i = j
                continue
            
            # Check for "broll"
            if cmd == "broll" and i + 1 < len(normalized):
                parsed.broll = normalized[i + 1]
                i += 2
                continue
            
            # Unknown command, skip
            i += 1
        
        return parsed


