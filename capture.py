import sys
import re

class ProgressCapture:
    def __init__(self, progress, value):
        self.set_progress = progress
        self.current_value = value

    def write(self, text):                    
        if not text.strip():
            return
        else:
            match = re.search(r"(\d+)/(\d+)\s+utterances processed", text)
            if match:
                value = int(match.group(1))
                total = int(match.group(2))
                increment = round(((value / total) * 55), 1)
                self.set_progress((self.current_value + increment, repr(text).strip("'")))

    def flush(self):
        pass