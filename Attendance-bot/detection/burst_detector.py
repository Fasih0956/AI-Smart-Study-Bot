"""
Burst Detector - counts "present" word occurrences across all chat,
not just message count. Handles multiple "present" in one message.
"""
import time
from typing import List, Tuple

BURST_THRESHOLD  = 5      # occurrences of "present"
BURST_WINDOW_SECS = 3.0  # window in seconds
PRESENT_KEYWORDS = {"present", "here", "p"}


class BurstDetector:
    def __init__(self):
        self.last_seen_text = ""
        self.occurrence_times: list = []
        self.last_burst_time = 0
        self.cooldown_secs = 30

    def check_with_count(self, chat_messages: List[str]) -> Tuple[int, bool]:
        now = time.time()

        if now - self.last_burst_time < self.cooldown_secs:
            return 0, False

        # Join all chat into one string
        full_text = " ".join(chat_messages).lower()

        # Only process new content since last check
        if full_text == self.last_seen_text:
            # Nothing new — clean old timestamps and return
            cutoff = now - BURST_WINDOW_SECS
            self.occurrence_times = [t for t in self.occurrence_times if t > cutoff]
            count = len(self.occurrence_times)
            return count, False

        # Find new content
        new_text = full_text[len(self.last_seen_text):]
        self.last_seen_text = full_text

        # Count how many times any present keyword appears in new content
        words = new_text.split()
        new_occurrences = sum(1 for w in words if w.strip("!.,?") in PRESENT_KEYWORDS)

        # Add timestamps for each new occurrence
        for _ in range(new_occurrences):
            self.occurrence_times.append(now)

        # Remove old occurrences outside window
        cutoff = now - BURST_WINDOW_SECS
        self.occurrence_times = [t for t in self.occurrence_times if t > cutoff]
        count = len(self.occurrence_times)

        triggered = count >= BURST_THRESHOLD
        if triggered:
            self.last_burst_time = now
            self.occurrence_times = []
            self.last_seen_text = ""  # reset so new messages detected after cooldown

        return count, triggered

    def check(self, chat_messages: List[str]) -> bool:
        _, triggered = self.check_with_count(chat_messages)
        return triggered