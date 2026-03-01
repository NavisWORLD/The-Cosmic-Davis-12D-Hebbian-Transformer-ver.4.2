"""
<<<<<<< HEAD:cosmos/tools/productivity/whisperer.py
cosmos Meeting Whisperer
=======
Farnsworth Meeting Whisperer
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/productivity/whisperer.py
----------------------------

"Did he say 'To shreds'? Oh my."

Simulates a real-time transcript analyzer.
"""

from loguru import logger

class MeetingWhisperer:
    def analyze_segment(self, text: str):
        """Analyze live text for actionable items."""
        text = text.lower()
        if "action item" in text or "todo" in text:
            logger.info(f"📝 ACTION ITEM DETECTED: {text}")
<<<<<<< HEAD:cosmos/tools/productivity/whisperer.py
        if "cosmos" in text:
=======
        if "farnsworth" in text:
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/productivity/whisperer.py
            logger.info("👀 They are talking about me!")

whisperer = MeetingWhisperer()
