import sys
import re

class ProgressCapture:
    def __init__(self, progress, value):
        """
        :param progress: Function updates site while data is processing
        :param value: The loading value
        """
        self.set_progress = progress
        self.current_value = value

    def write(self, text):
        """
        Capture stdout data and pass it to the loading bar
        
        :param text: The data
        """                    
        if not text.strip():
            return
        else:
            match = re.search(r"(\d+)/(\d+)\s+utterances processed", text)
            if match:
                value = int(match.group(1))
                total = int(match.group(2))
                increment = round(((value / total) * 55), 1)
                self.set_progress((self.current_value + increment, "This may take a few moments..", repr(text).strip("'")))

    def flush(self):
        pass