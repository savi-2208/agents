"""
Filler-Aware Voice Agent
Filters filler word interruptions using FillerInterruptionHandler
"""
import asyncio
import logging
import sys
import os
from typing import AsyncIterable, Optional

# Add plugin path
sys.path.insert(0, r"C:\Users\Dell\OneDrive\Desktop\savyyyyyyyyyyy\agents\livekit-plugins\livekit-plugins-filler-handler")

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    stt,
    ModelSettings,
)
from livekit.plugins import deepgram, openai, silero, elevenlabs

# Import our handler
from livekit.plugins.filler_handler import FillerInterruptionHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("filler-aware-agent")


class FillerAwareAgent(Agent):
    """Agent that intelligently filters filler word interruptions"""
    
    def __init__(self):
        super().__init__(
            instructions=(
                "You are a friendly and helpful voice assistant. "
                "Engage in natural conversation with the user. "
                "Keep your responses concise and conversational."
            )
        )
        self.filler_handler: Optional[FillerInterruptionHandler] = None
    
    async def on_enter(self):
        """Called when agent becomes active in the session"""
        logger.info("🎬 Agent entering session")
        
        # Initialize filler handler with session reference
        self.filler_handler = FillerInterruptionHandler(
            session=self.session,
            fillers=['uh', 'um', 'umm', 'hmm', 'hm', 'er', 'ah', 'haan']
        )
        
        # Greet the user
        await self.session.generate_reply(
            instructions="Greet the user warmly and ask how you can help them today."
        )
    
    async def stt_node(
        self,
        audio: AsyncIterable[rtc.AudioFrame],
        model_settings: ModelSettings
    ) -> AsyncIterable[stt.SpeechEvent]:
        """
        Override STT node to filter filler interruptions
        """
        # Get default STT processing
        default_stt_stream = Agent.default.stt_node(self, audio, model_settings)
        
        # Filter events through our filler handler
        async for event in default_stt_stream:
            if self.filler_handler:
                filtered_event = await self.filler_handler.filter_speech_event(event)
                if filtered_event is not None:
                    # Event passed filter, yield it
                    yield filtered_event
            else:
                # Handler not initialized yet, pass through
                yield event
    
    async def on_exit(self):
        """Called before agent gives control to another agent"""
        if self.filler_handler:
            stats = self.filler_handler.get_statistics()
            logger.info(f"📊 Filler handler statistics: {stats}")


async def entrypoint(ctx: JobContext):
    """Entry point for the voice assistant"""
    
    logger.info(f"🚀 Starting filler-aware agent for room: {ctx.room.name}")
    
    # Connect to room
    await ctx.connect()
    
    logger.info(f"✅ Connected to room: {ctx.room.name}")
    
    # Create agent
    agent = FillerAwareAgent()
    
    # Create session with optimal configuration
    session = AgentSession(
        # Turn detection - use VAD for simplicity
        vad=silero.VAD.load(),
        
        # STT, LLM, TTS - using placeholder for now
        # You'll need to configure these with your API keys
        stt=deepgram.STT(model="nova-2") if os.getenv('DEEPGRAM_API_KEY') else None,
        llm=openai.LLM(model="gpt-4o-mini") if os.getenv('OPENAI_API_KEY') else None,
        tts=elevenlabs.TTS() if os.getenv('ELEVEN_API_KEY') else None,
        
        # Interruption settings
        allow_interruptions=True,
        min_interruption_duration=0.5,
        min_interruption_words=0,  # We handle word filtering in our handler
        
        # False interruption handling (built-in LiveKit feature)
        false_interruption_timeout=2.0,
        resume_false_interruption=True,
    )
    
    # Start agent session
    await session.start(agent=agent, room=ctx.room)
    
    logger.info("✅ Agent session started and ready for interaction")


if __name__ == "__main__":
    # Run the agent
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
    