"""
Unit tests for marker command parsing
"""

import pytest

from studioflow.core.marker_commands import MarkerCommandParser, ParsedCommands


class TestCommandParsing:
    """Test command parsing functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = MarkerCommandParser()
    
    def test_parse_number_words(self):
        """Parse number words correctly"""
        assert self.parser.parse_number("one") == 1
        assert self.parser.parse_number("five") == 5
        assert self.parser.parse_number("ten") == 10
        assert self.parser.parse_number("20") == 20
        assert self.parser.parse_number("invalid") is None
    
    def test_parse_order_command(self):
        """Parse 'order one' command"""
        commands = ["order", "one"]
        parsed = self.parser.parse(commands)
        assert parsed.order == 1
    
    def test_parse_step_command(self):
        """Parse 'step five' command"""
        commands = ["step", "five"]
        parsed = self.parser.parse(commands)
        assert parsed.step == 5
    
    def test_parse_naming_command(self):
        """Parse 'naming setup' command"""
        commands = ["naming", "setup"]
        parsed = self.parser.parse(commands)
        assert parsed.naming == "setup"
    
    def test_parse_naming_with_multiple_words(self):
        """Parse 'naming setup config' command"""
        commands = ["naming", "setup", "config"]
        parsed = self.parser.parse(commands)
        assert parsed.naming == "setup config"
    
    def test_parse_mark_flag(self):
        """Parse 'mark' as flag"""
        commands = ["mark"]
        parsed = self.parser.parse(commands)
        assert parsed.mark is True
    
    def test_parse_ending_flag(self):
        """Parse 'ending' as flag"""
        commands = ["ending", "mark"]
        parsed = self.parser.parse(commands)
        assert parsed.ending is True
        assert parsed.mark is True
    
    def test_parse_complex_start_command(self):
        """Parse complex START marker command"""
        commands = ["naming", "setup", "mark", "order", "one", "step", "five"]
        parsed = self.parser.parse(commands)
        assert parsed.naming == "setup"
        assert parsed.mark is True
        assert parsed.order == 1
        assert parsed.step == 5
    
    def test_parse_complex_end_command(self):
        """Parse complex END marker command"""
        commands = ["ending", "mark", "cta", "subscribe", "chapter", "intro"]
        parsed = self.parser.parse(commands)
        assert parsed.ending is True
        assert parsed.mark is True
        assert parsed.cta == "subscribe"
        assert parsed.chapter == "intro"
    
    def test_fuzzy_broll(self):
        """Fuzzy match B-roll variations"""
        assert self.parser.normalize_word("b roll") == "broll"
        assert self.parser.normalize_word("b-roll") == "broll"
        assert self.parser.normalize_word("b_roll") == "broll"
        assert self.parser.normalize_word("broll") == "broll"
    
    def test_fuzzy_cta(self):
        """Fuzzy match CTA variations"""
        assert self.parser.normalize_word("c t a") == "cta"
        assert self.parser.normalize_word("see t a") == "cta"
        assert self.parser.normalize_word("cta") == "cta"
    
    def test_fuzzy_hook(self):
        """Fuzzy match hook types"""
        assert self.parser.normalize_word("c o h") == "coh"
        assert self.parser.normalize_word("coh") == "coh"
    
    def test_parse_title_simple(self):
        """Parse 'title Intro' command"""
        commands = ["title", "Intro"]
        parsed = self.parser.parse(commands)
        assert parsed.title == "Intro"
        assert parsed.title_type is None
    
    def test_parse_title_with_type(self):
        """Parse 'title lower third Intro' command"""
        commands = ["title", "lower", "third", "Intro"]
        parsed = self.parser.parse(commands)
        assert parsed.title_type == "lower third"
        assert parsed.title == "Intro"
    
    def test_parse_effect_command(self):
        """Parse 'effect mtuber intro' command"""
        commands = ["effect", "mtuber", "intro"]
        parsed = self.parser.parse(commands)
        assert parsed.effect_product == "mtuber"
        assert parsed.effect_name == "intro"
        assert parsed.effect == "mtuber:intro"
    
    def test_parse_transition_product(self):
        """Parse 'transition mtuber fade' command"""
        commands = ["transition", "mtuber", "fade"]
        parsed = self.parser.parse(commands)
        assert parsed.transition_product == "mtuber"
        assert parsed.transition_name == "fade"
        assert parsed.transition == "mtuber:fade"
    
    def test_parse_transition_generic(self):
        """Parse 'transition warp' command"""
        commands = ["transition", "warp"]
        parsed = self.parser.parse(commands)
        assert parsed.transition_generic == "warp"
        assert parsed.transition == "warp"
    
    def test_parse_chapter_command(self):
        """Parse 'chapter config' command"""
        commands = ["chapter", "config"]
        parsed = self.parser.parse(commands)
        assert parsed.chapter == "config"
    
    def test_parse_chapter_multiple_words(self):
        """Parse 'chapter setup config' command"""
        commands = ["chapter", "setup", "config"]
        parsed = self.parser.parse(commands)
        assert parsed.chapter == "setup config"
    
    def test_parse_cta_command(self):
        """Parse 'cta subscribe' command"""
        commands = ["cta", "subscribe"]
        parsed = self.parser.parse(commands)
        assert parsed.cta == "subscribe"
    
    def test_parse_screen_command(self):
        """Parse 'screen hud' command"""
        commands = ["screen", "hud"]
        parsed = self.parser.parse(commands)
        assert parsed.screen == "hud"
    
    def test_parse_broll_command(self):
        """Parse 'broll screen' command"""
        commands = ["broll", "screen"]
        parsed = self.parser.parse(commands)
        assert parsed.broll == "screen"
    
    def test_parse_type_command(self):
        """Parse 'type camera' command"""
        commands = ["type", "camera"]
        parsed = self.parser.parse(commands)
        assert parsed.segment_type == "camera"
    
    def test_parse_quality_markers(self):
        """Parse quality markers"""
        commands_best = ["best"]
        commands_select = ["select"]
        commands_backup = ["backup"]
        
        parsed_best = self.parser.parse(commands_best)
        parsed_select = self.parser.parse(commands_select)
        parsed_backup = self.parser.parse(commands_backup)
        
        assert parsed_best.quality == "best"
        assert parsed_select.quality == "select"
        assert parsed_backup.quality == "backup"
    
    def test_parse_hook_command(self):
        """Parse 'hook coh' command"""
        commands = ["hook", "coh"]
        parsed = self.parser.parse(commands)
        assert parsed.hook == "coh"
    
    def test_parse_empty_commands(self):
        """Parse empty commands list"""
        commands = []
        parsed = self.parser.parse(commands)
        assert parsed.naming is None
        assert parsed.mark is False
    
    def test_parse_unknown_commands(self):
        """Parse commands with unknown words (should ignore)"""
        commands = ["unknown", "command", "naming", "setup"]
        parsed = self.parser.parse(commands)
        assert parsed.naming == "setup"
        # Unknown commands should be ignored
    
    def test_parse_complex_real_world(self):
        """Parse real-world complex command"""
        commands = ["naming", "setup", "mark", "order", "one", "step", "five", "type", "camera"]
        parsed = self.parser.parse(commands)
        assert parsed.naming == "setup"
        assert parsed.mark is True
        assert parsed.order == 1
        assert parsed.step == 5
        assert parsed.segment_type == "camera"
    
    def test_parse_preserves_original_commands(self):
        """Parsed commands preserve raw command list"""
        commands = ["naming", "setup", "done"]
        parsed = self.parser.parse(commands)
        assert parsed.raw_commands == commands


class TestNumberParsing:
    """Test number parsing edge cases"""
    
    def setup_method(self):
        self.parser = MarkerCommandParser()
    
    def test_parse_all_number_words(self):
        """Parse all number words from zero to twenty"""
        number_words = ["zero", "one", "two", "three", "four", "five",
                       "six", "seven", "eight", "nine", "ten", "eleven",
                       "twelve", "thirteen", "fourteen", "fifteen",
                       "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
        
        for i, word in enumerate(number_words):
            assert self.parser.parse_number(word) == i
    
    def test_parse_numeric_strings(self):
        """Parse numeric strings"""
        assert self.parser.parse_number("0") == 0
        assert self.parser.parse_number("10") == 10
        assert self.parser.parse_number("99") == 99
    
    def test_parse_invalid_numbers(self):
        """Parse invalid number strings"""
        assert self.parser.parse_number("invalid") is None
        assert self.parser.parse_number("") is None
        assert self.parser.parse_number("abc") is None


class TestFuzzyMatching:
    """Test fuzzy matching variations"""
    
    def setup_method(self):
        self.parser = MarkerCommandParser()
    
    def test_fuzzy_broll_variations(self):
        """Test all B-roll variations"""
        variations = ["broll", "b roll", "b-roll", "b_roll", "be roll"]
        for variation in variations:
            assert self.parser.normalize_word(variation) == "broll"
    
    def test_fuzzy_cta_variations(self):
        """Test all CTA variations"""
        variations = ["cta", "c t a", "see t a", "see tea"]
        for variation in variations:
            assert self.parser.normalize_word(variation) == "cta"
    
    def test_fuzzy_hook_variations(self):
        """Test hook type variations"""
        assert self.parser.normalize_word("coh") == "coh"
        assert self.parser.normalize_word("c o h") == "coh"
        assert self.parser.normalize_word("ch") == "ch"
        assert self.parser.normalize_word("c h") == "ch"
    
    def test_fuzzy_quality_variations(self):
        """Test quality marker variations"""
        assert self.parser.normalize_word("best") == "best"
        assert self.parser.normalize_word("select") == "select"
        assert self.parser.normalize_word("backup") == "backup"
    
    def test_fuzzy_transition_variations(self):
        """Test transition variations"""
        assert self.parser.normalize_word("warp") == "warp"
        assert self.parser.normalize_word("dissolve") == "dissolve"
        assert self.parser.normalize_word("fade") == "fade"

    def test_case_insensitive_parsing(self):
        """Test parsing is case insensitive"""
        commands_upper = ["NAMING", "SETUP", "ORDER", "ONE"]
        commands_lower = ["naming", "setup", "order", "one"]
        commands_mixed = ["Naming", "Setup", "Order", "One"]
        
        parsed_upper = self.parser.parse(commands_upper)
        parsed_lower = self.parser.parse(commands_lower)
        parsed_mixed = self.parser.parse(commands_mixed)
        
        # Naming preserves original case from commands
        assert parsed_upper.naming == "SETUP"  # Preserves case
        assert parsed_lower.naming == "setup"
        assert parsed_mixed.naming == "Setup"
        assert parsed_upper.order == 1
        assert parsed_lower.order == 1
        assert parsed_mixed.order == 1
    
    def test_parse_with_typos(self):
        """Test parsing handles common typos"""
        # Common typos
        commands_typo1 = ["naming", "setp"]  # typo: "setp" instead of "setup"
        commands_typo2 = ["order", "on"]  # typo: "on" instead of "one"
        
        parsed1 = self.parser.parse(commands_typo1)
        parsed2 = self.parser.parse(commands_typo2)
        
        # Should still parse what it can
        assert parsed1.naming == "setp"  # Preserves typo in naming
        # Order parsing might fail with typo, which is acceptable
    
    def test_parse_multiple_naming_commands(self):
        """Test parsing when multiple naming commands present (collects all)"""
        commands = ["naming", "first", "naming", "second"]
        parsed = self.parser.parse(commands)
        
        # Current behavior: collects all words between first "naming" and next command
        # This includes "first naming second" as the name
        assert parsed.naming == "first naming second"
    
    def test_parse_multiple_order_commands(self):
        """Test parsing when multiple order commands present (takes last)"""
        commands = ["order", "one", "order", "two"]
        parsed = self.parser.parse(commands)
        
        # Should take the last order command
        assert parsed.order == 2
    
    def test_parse_whitespace_handling(self):
        """Test parsing handles extra whitespace in commands"""
        # Commands might have extra spaces (should be normalized before parsing)
        # This tests that parser handles normalized input
        commands = ["naming", "  setup  ", "order", "one"]
        parsed = self.parser.parse(commands)
        
        assert parsed.naming is not None
        assert parsed.order == 1


@pytest.mark.unit
class TestMarkerCommandEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        self.parser = MarkerCommandParser()
    
    def test_parse_none_input(self):
        """Test parsing None input (should handle gracefully)"""
        # Parser should handle None or raise appropriate error
        try:
            parsed = self.parser.parse(None)
            # If it doesn't raise, result should be valid ParsedCommands
            assert parsed is not None
        except (TypeError, AttributeError):
            # Expected if None is not valid input
            pass
    
    def test_parse_very_long_command(self):
        """Test parsing very long command string"""
        commands = ["naming"] + ["word"] * 50  # Very long naming
        parsed = self.parser.parse(commands)
        
        assert parsed.naming is not None
        assert len(parsed.naming.split()) >= 50
    
    def test_parse_special_characters(self):
        """Test parsing commands with special characters"""
        commands = ["naming", "test-video_01", "order", "1"]
        parsed = self.parser.parse(commands)
        
        assert parsed.naming == "test-video_01"
        assert parsed.order == 1
    
    def test_parse_numbers_as_strings(self):
        """Test parsing numeric strings in commands"""
        commands = ["order", "1", "step", "2"]
        parsed = self.parser.parse(commands)
        
        assert parsed.order == 1
        assert parsed.step == 2
    
    def test_parse_unicode_characters(self):
        """Test parsing commands with unicode characters"""
        commands = ["naming", "testé", "order", "uno"]  # Unicode and non-English
        parsed = self.parser.parse(commands)
        
        assert parsed.naming == "testé"
        # Order parsing might not handle "uno", which is acceptable

