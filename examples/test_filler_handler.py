"""Manual test script for FillerInterruptionHandler"""
import asyncio
import logging
import sys
from unittest.mock import Mock

# Add plugin path
sys.path.insert(0, r"C:\Users\Dell\OneDrive\Desktop\savyyyyyyyyyyy\agents\livekit-plugins\livekit-plugins-filler-handler")

from livekit.plugins.filler_handler import FillerInterruptionHandler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_scenarios():
    """Test various interruption scenarios"""
    
    # Create mock session
    session = Mock()
    session.on = Mock(return_value=lambda f: f)
    
    # Create handler
    handler = FillerInterruptionHandler(session)
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Filler while agent speaks',
            'agent_speaking': True,
            'text': 'umm',
            'expected': False,
        },
        {
            'name': 'Valid interrupt while agent speaks',
            'agent_speaking': True,
            'text': 'wait one second',
            'expected': True,
        },
        {
            'name': 'Filler while agent quiet',
            'agent_speaking': False,
            'text': 'hmm',
            'expected': True,
        },
        {
            'name': 'Mixed filler and command',
            'agent_speaking': True,
            'text': 'umm okay stop',
            'expected': True,
        },
        {
            'name': 'Multiple fillers',
            'agent_speaking': True,
            'text': 'uh um er',
            'expected': False,
        },
        {
            'name': 'Short valid command',
            'agent_speaking': True,
            'text': 'wait please',
            'expected': True,
        },
        {
            'name': 'Hindi filler',
            'agent_speaking': True,
            'text': 'haan',
            'expected': False,
        },
        {
            'name': 'Valid when not speaking',
            'agent_speaking': False,
            'text': 'hello there',
            'expected': True,
        },
    ]
    
    print("\n" + "="*80)
    print("FILLER INTERRUPTION HANDLER - MANUAL TEST")
    print("="*80 + "\n")
    
    passed = 0
    failed = 0
    
    for i, scenario in enumerate(scenarios, 1):
        # Set agent state
        handler.agent_speaking = scenario['agent_speaking']
        
        # Test decision
        allow, reason = await handler.should_allow_interruption(scenario['text'])
        
        # Check result
        success = allow == scenario['expected']
        status = "✅ PASS" if success else "❌ FAIL"
        
        if success:
            passed += 1
        else:
            failed += 1
        
        print(f"{i}. {status} | {scenario['name']}")
        print(f"   Text: '{scenario['text']}'")
        print(f"   Agent Speaking: {scenario['agent_speaking']}")
        print(f"   Expected: {scenario['expected']}, Got: {allow}")
        print(f"   Reason: {reason}")
        print()
    
    # Print statistics
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"✅ Passed: {passed}/{len(scenarios)}")
    print(f"❌ Failed: {failed}/{len(scenarios)}")
    
    stats = handler.get_statistics()
    print(f"\nHandler Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_scenarios())
    sys.exit(0 if success else 1)