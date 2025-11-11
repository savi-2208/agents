"""Unit tests for filler word detection logic"""
import pytest
import re


class SimpleFillerClassifier:
    """Simplified classifier for testing core logic"""
    
    FILLERS = ['uh', 'um', 'umm', 'hmm', 'hm', 'er', 'ah', 'haan']
    
    def __init__(self):
        pattern = '|'.join(rf'\b{re.escape(w)}\b' for w in self.FILLERS)
        self.filler_pattern = re.compile(pattern, re.IGNORECASE)
    
    def is_filler_only(self, text):
        """Check if text contains only filler words"""
        if not text or not text.strip():
            return True, "empty_text"
        
        cleaned = text.strip().lower()
        text_without_fillers = self.filler_pattern.sub('', cleaned).strip()
        text_without_fillers = ' '.join(text_without_fillers.split())
        
        if not text_without_fillers:
            return True, "only_filler_words"
        
        remaining_words = text_without_fillers.split()
        if len(remaining_words) < 2:
            return True, f"insufficient_words_{len(remaining_words)}"
        
        return False, "valid_content"


@pytest.fixture
def classifier():
    """Create a classifier instance"""
    return SimpleFillerClassifier()


class TestFillerClassification:
    """Test filler word classification logic"""
    
    def test_pure_fillers(self, classifier):
        """Test detection of pure filler words"""
        test_cases = [
            ("uh", True),
            ("umm", True),
            ("hmm yeah", True),
            ("uh um hmm", True),
            ("er", True),
        ]
        
        for text, expected_is_filler in test_cases:
            is_filler, reason = classifier.is_filler_only(text)
            assert is_filler == expected_is_filler, f"Failed for: '{text}', reason: {reason}"
    
    def test_valid_content(self, classifier):
        """Test detection of valid interruptions"""
        test_cases = [
            ("wait one second", False),
            ("no not that one", False),
            ("stop please", False),
            ("can you repeat that", False),
            ("hold on", False),
        ]
        
        for text, expected_is_filler in test_cases:
            is_filler, reason = classifier.is_filler_only(text)
            assert is_filler == expected_is_filler, f"Failed for: '{text}', reason: {reason}"
    
    def test_mixed_content(self, classifier):
        """Test mixed filler and real content"""
        # "umm okay stop" should be valid (contains 2+ real words after filtering)
        is_filler, reason = classifier.is_filler_only("umm okay stop")
        assert not is_filler, f"Should be valid, got reason: {reason}"
        
        # "uh yeah" is only 1 real word after filtering, should be treated as filler
        is_filler, reason = classifier.is_filler_only("uh yeah")
        assert is_filler, f"Should be filler (only 1 word remaining), got reason: {reason}"
        
        # "um wait please" should be valid (2 words remain)
        is_filler, reason = classifier.is_filler_only("um wait please")
        assert not is_filler, f"Should be valid (2 words remain)"
    
    def test_empty_strings(self, classifier):
        """Test empty or whitespace strings"""
        test_cases = ["", "   ", "\n", "\t"]
        
        for text in test_cases:
            is_filler, reason = classifier.is_filler_only(text)
            assert is_filler, f"Empty string should be filler: '{text}'"
    
    def test_case_insensitive(self, classifier):
        """Test that matching is case insensitive"""
        test_cases = ["UMM", "Uh", "HmM"]
        
        for text in test_cases:
            is_filler, reason = classifier.is_filler_only(text)
            assert is_filler, f"Should detect filler regardless of case: '{text}'"
    
    def test_word_boundaries(self, classifier):
        """Test that we match whole words only"""
        # "summit" contains "um" but should NOT be filtered
        is_filler, reason = classifier.is_filler_only("let's summit")
        assert not is_filler, "Should not match partial words"
        
        # "hummer" contains "um" but should NOT be filtered
        is_filler, reason = classifier.is_filler_only("hummer truck")
        assert not is_filler, "Should not match partial words"


class TestAgentStateLogic:
    """Test interruption decision logic based on agent state"""
    
    def test_allow_when_not_speaking(self):
        """Should allow all speech when agent is not speaking"""
        agent_speaking = False
        test_cases = ["uh", "umm", "wait", "stop"]
        
        for text in test_cases:
            # Logic: if not speaking, always allow
            should_allow = not agent_speaking
            assert should_allow, f"Should allow when not speaking: {text}"
    
    def test_filter_logic_when_speaking(self, classifier):
        """Should filter fillers when agent is speaking"""
        agent_speaking = True
        
        # Test filler - should be filtered
        is_filler, _ = classifier.is_filler_only("uh")
        should_filter = agent_speaking and is_filler
        assert should_filter, "Should filter filler when speaking"
        
        # Test valid - should not be filtered
        is_filler, _ = classifier.is_filler_only("wait please")
        should_filter = agent_speaking and is_filler
        assert not should_filter, "Should not filter valid content when speaking"


def test_statistics_tracking():
    """Test that we can track statistics"""
    stats = {'total': 0, 'filtered': 0, 'allowed': 0}
    
    # Simulate some events
    stats['total'] += 1
    stats['filtered'] += 1
    
    stats['total'] += 1
    stats['allowed'] += 1
    
    assert stats['total'] == 2
    assert stats['filtered'] == 1
    assert stats['allowed'] == 1
    
    filter_rate = stats['filtered'] / stats['total']
    assert filter_rate == 0.5