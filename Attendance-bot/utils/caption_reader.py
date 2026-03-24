"""Caption reader and text buffer."""

from collections import deque


class CaptionReader:
    def __init__(self, maxlen: int = 100):
        self.buffer: deque = deque(maxlen=maxlen)

    def add(self, text: str):
        if text and text.strip():
            self.buffer.append(text.strip())

    def get_recent(self, n: int = 10) -> str:
        items = list(self.buffer)[-n:]
        return " ".join(items)

    def get_all(self) -> str:
        return " ".join(self.buffer)

    def clear(self):
        self.buffer.clear()
