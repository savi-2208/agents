"""Simplified manual test script for FillerInterruptionHandler"""
import asyncio
import sys
import re

# Add plugin path
# sys.path.insert(0, r"C:\Users\Dell\OneDrive\Desktop\savyyyyyyyyyyy\agents\livekit-plugins\livekit-plugins-filler-handler")


class SimpleFillerHandler:
    """Simplified version of FillerInterruptionHandler for testing"""
    
    FILLERS = ['uh', 'um', 'umm', 'hmm', 'hm', 'er', 'ah', 'haan']
    
    def __init__(self):
        self.agent_speaking = False
        pattern = '|'.join(rf'\b{re.escape(w)}\b' for w in self.FILLERS)
        self.filler_pattern = re.compile(pattern, re.IGNORECASE)
        self.stats = {'total': 0, 'filtered': 0, 'allowed': 0}
    
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
    
    async def should_allow_interruption(self, text):
        """Main decision logic"""
        self.stats['total'] += 1
        
        if not self.agent_speaking:
            self.stats['allowed'] += 1
            return True, "agent_not_speaking"
        
        is_filler, reason = self.is_filler_only(text)
        
        if is_filler:
            self.stats['filtered'] += 1
            return False, f"filler_{reason}"
        else:
            self.stats['allowed'] += 1
            return True, "valid_content"


async def test_scenarios():
    """Test various interruption scenarios"""
    
    handler = SimpleFillerHandler()
    
    scenarios = [
        {'name': 'Filler while agent speaks', 'speaking': True, 'text': 'umm', 'expected': False},
        {'name': 'Valid interrupt while agent speaks', 'speaking': True, 'text': 'wait one second', 'expected': True},
        {'name': 'Filler while agent quiet', 'speaking': False, 'text': 'hmm', 'expected': True},
        {'name': 'Mixed filler and command', 'speaking': True, 'text': 'umm okay stop', 'expected': True},
        {'name': 'Multiple fillers', 'speaking': True, 'text': 'uh um er', 'expected': False},
        {'name': 'Short valid command', 'speaking': True, 'text': 'wait please', 'expected': True},
        {'name': 'Hindi filler', 'speaking': True, 'text': 'haan', 'expected': False},
        {'name': 'Valid when not speaking', 'speaking': False, 'text': 'hello there', 'expected': True},
    ]
    
    print("\n" + "="*80)
    print("FILLER INTERRUPTION HANDLER - MANUAL TEST")
    print("="*80 + "\n")
    
    passed = 0
    failed = 0
    
    for i, scenario in enumerate(scenarios, 1):
        handler.agent_speaking = scenario['speaking']
        allow, reason = await handler.should_allow_interruption(scenario['text'])
        
        success = allow == scenario['expected']
        status = "✅ PASS" if success else "❌ FAIL"
        
        if success:
            passed += 1
        else:
            failed += 1
        
        print(f"{i}. {status} | {scenario['name']}")
        print(f"   Text: '{scenario['text']}'")
        print(f"   Agent Speaking: {scenario['speaking']}")
        print(f"   Expected: {scenario['expected']}, Got: {allow}")
        print(f"   Reason: {reason}")
        print()
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"✅ Passed: {passed}/{len(scenarios)}")
    print(f"❌ Failed: {failed}/{len(scenarios)}")
    print(f"\nStatistics: {handler.stats}")
    print()
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_scenarios())
    print("\n✅ ALL TESTS PASSED!" if success else "\n❌ SOME TESTS FAILED")
    sys.exit(0 if success else 1)
    