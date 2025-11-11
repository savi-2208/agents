# handler.py - Minimal Filler Interruption Handler
import asyncio
import logging
import re
from typing import Optional
from livekit.agents import stt, AgentSession

logger = logging.getLogger("filler_handler")
logger.setLevel(logging.INFO)

class FillerInterruptionHandler:
    """Minimal filler word interruption handler for LiveKit Agents"""
    
    # Default filler words
    FILLERS = ['uh', 'um', 'umm', 'hmm', 'hm', 'er', 'ah', 'haan', 'acha']
    
    def __init__(self, session: AgentSession, fillers: list = None):
        """Initialize handler with session and optional custom filler list"""
        self.session = session
        self.fillers = fillers or self.FILLERS
        self.agent_speaking = False
        
        # Pre-compile regex pattern for performance
        pattern = '|'.join(rf'\b{re.escape(w)}\b' for w in self.fillers)
        self.filler_pattern = re.compile(pattern, re.IGNORECASE)
        
        # Statistics
        self.stats = {
            'total_events': 0,
            'filtered_fillers': 0,
            'allowed_interrupts': 0,
        }
        
        # Set up event listeners to track agent state
        self._setup_event_listeners()
        
        logger.info(f"✅ FillerInterruptionHandler initialized with {len(self.fillers)} filler words")
    
    def _setup_event_listeners(self):
        """Subscribe to agent events to track speaking state"""
        
        @self.session.on("speech_created")
        def on_speech_created(event):
            try:
                handle = getattr(event, "speech_handle", None)
                sid = getattr(handle, "id", None)
                logger.debug(f"Agent started speaking: {sid}")
            except Exception as e:
                logger.debug(f"speech_created log skipped: {e}")

        @self.session.on("speech_stopped")
        def on_speech_stopped(event):
            try:
                handle = getattr(event, "speech_handle", None)
                sid = getattr(handle, "id", None)
                logger.debug(f"Agent stopped speaking: {sid}")
            except Exception as e:
                logger.debug(f"speech_stopped log skipped: {e}")
        # @self.session.on("speech_created")
        # def on_speech_created(speech_handle):
        #     self.agent_speaking = True
        #     logger.debug(f"🎤 Agent started speaking: {speech_handle.id}")
        
        # @self.session.on("speech_finished")
        # def on_speech_finished(speech_handle):
        #     self.agent_speaking = False
        #     logger.debug(f"✋ Agent finished speaking: {speech_handle.id}")
    
    def is_filler_only(self, text: str) -> tuple[bool, str]:
        """
        Check if text contains only filler words
        
        Returns:
            (is_filler_only: bool, reason: str)
        """
        if not text or not text.strip():
            return True, "empty_text"
        
        # Clean text
        cleaned = text.strip().lower()
        
        # Remove all filler words
        text_without_fillers = self.filler_pattern.sub('', cleaned).strip()
        
        # Remove extra whitespace
        text_without_fillers = ' '.join(text_without_fillers.split())
        
        # If nothing left, it was filler-only
        if not text_without_fillers:
            return True, "only_filler_words"
        
        # Check if remaining content is substantial (at least 2 words)
        remaining_words = text_without_fillers.split()
        if len(remaining_words) < 2:
            return True, f"insufficient_words_{len(remaining_words)}"
        
        return False, "valid_content"
    
    async def should_allow_interruption(self, text: str, confidence: float = None) -> tuple[bool, str]:
        """
        Main decision logic: should this transcription trigger an interruption?
        
        Returns:
            (allow_interrupt: bool, reason: str)
        """
        self.stats['total_events'] += 1
        
        # Always allow when agent is NOT speaking
        if not self.agent_speaking:
            logger.info(f"✅ Allowed (agent quiet): '{text}'")
            self.stats['allowed_interrupts'] += 1
            return True, "agent_not_speaking"
        
        # Agent IS speaking - check if filler only
        is_filler, reason = self.is_filler_only(text)
        
        if is_filler:
            # Block this interruption
            logger.info(f"❌ Blocked filler: '{text}' [reason: {reason}]")
            self.stats['filtered_fillers'] += 1
            return False, f"filler_{reason}"
        else:
            # Valid interruption - allow it
            logger.info(f"✅ Allowed interrupt: '{text}'")
            self.stats['allowed_interrupts'] += 1
            return True, "valid_content"
    
    async def filter_speech_event(
        self, 
        event: stt.SpeechEvent
    ) -> Optional[stt.SpeechEvent]:
        """
        Filter a speech event, returning None if it should be ignored
        
        This is the main integration point with STT stream.
        """
        # Only filter FINAL_TRANSCRIPT events
        if event.type != stt.SpeechEventType.FINAL_TRANSCRIPT:
            return event
        
        # Extract text and confidence
        if not event.alternatives:
            return event
        
        alternative = event.alternatives[0]
        text = alternative.text
        confidence = getattr(alternative, 'confidence', None)
        
        # Check if we should allow this interruption
        should_allow, reason = await self.should_allow_interruption(text, confidence)
        
        if should_allow:
            return event  # Pass through
        else:
            return None  # Block this event
    
    def get_statistics(self) -> dict:
        """Get handler statistics"""
        total = self.stats['total_events']
        return {
            **self.stats,
            'filter_rate': (
                self.stats['filtered_fillers'] / total 
                if total > 0 else 0
            )
        }