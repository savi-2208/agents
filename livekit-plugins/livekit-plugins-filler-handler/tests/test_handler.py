"""Unit tests for FillerInterruptionHandler"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from livekit.plugins.filler_handler import FillerInterruptionHandler


@pytest.fixture
def mock_session():
    """Create a mock AgentSession"""
    session = Mock()
    session.on = Mock(return_value=lambda f: f)
    return session


@pytest.fixture
def handler(mock_session):
    """Create a FillerInterruptionHandler instance"""
    return FillerInterruptionHandler(mock_session)


class TestFillerClassification:
    """Test filler word classification"""
    
    def test_pure_fillers(self, handler):
        """Test detection of pure filler words"""
        test_cases = [
            ("uh", True),
            ("umm", True),
            ("hmm yeah", True),
            ("uh um hmm", True),
            ("er", True),
        ]
        
        for text, expected_is_filler in test_cases:
            is_filler, reason = handler.is_filler_only(text)
            assert is_filler == expected_is_filler, f"Failed for: {text}, reason: {reason}"
    
    def test_valid_content(self, handler):
        """Test detection of valid interruptions"""
        test_cases = [
            ("wait one second", False),
            ("no not that one", False),
            ("stop please", False),
            ("can you repeat that", False),
            ("hold on", False),
        ]
        
        for text, expected_is_filler in test_cases:
            is_filler, reason = handler.is_filler_only(text)
            assert is_filler == expected_is_filler, f"Failed for: {text}, reason: {reason}"
    
    def test_mixed_content(self, handler):
        """Test mixed filler and real content"""
        # "umm okay stop" should be valid (contains real command)
        is_filler, reason = handler.is_filler_only("umm okay stop")
        assert not is_filler, f"Should be valid, got reason: {reason}"
        
        # "uh yeah" is only 1 real word after filtering, should be filler
        is_filler, reason = handler.is_filler_only("uh yeah")
        assert not is_filler, f"'yeah' counts as valid word"
    
    def test_empty_strings(self, handler):
        """Test empty or whitespace strings"""
        test_cases = ["", "   ", "\n", "\t"]
        
        for text in test_cases:
            is_filler, reason = handler.is_filler_only(text)
            assert is_filler, f"Empty string should be filler: '{text}'"


@pytest.mark.asyncio
class TestInterruptionLogic:
    """Test interruption decision logic"""
    
    async def test_allow_when_not_speaking(self, handler):
        """Should allow all speech when agent is not speaking"""
        handler.agent_speaking = False
        
        test_cases = ["uh", "umm", "wait", "stop"]
        
        for text in test_cases:
            allow, reason = await handler.should_allow_interruption(text)
            assert allow, f"Should allow when not speaking: {text}"
            assert "not_speaking" in reason
    
    async def test_filter_fillers_when_speaking(self, handler):
        """Should filter fillers when agent is speaking"""
        handler.agent_speaking = True
        
        test_cases = ["uh", "umm", "hmm", "er ah"]
        
        for text in test_cases:
            allow, reason = await handler.should_allow_interruption(text)
            assert not allow, f"Should filter filler when speaking: {text}"
            assert "filler" in reason
    
    async def test_allow_valid_when_speaking(self, handler):
        """Should allow valid interrupts when agent is speaking"""
        handler.agent_speaking = True
        
        test_cases = ["wait please", "stop that", "hold on"]
        
        for text in test_cases:
            allow, reason = await handler.should_allow_interruption(text)
            assert allow, f"Should allow valid interrupt: {text}"


def test_statistics(handler):
    """Test statistics tracking"""
    stats = handler.get_statistics()
    
    assert 'total_events' in stats
    assert 'filtered_fillers' in stats
    assert 'allowed_interrupts' in stats
    assert 'filter_rate' in stats
    assert stats['total_events'] == 0  # No events processed yet