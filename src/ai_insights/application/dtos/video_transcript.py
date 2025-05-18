from dataclasses import dataclass

@dataclass
class VideoTranscriptDto:
    id: str
    title: str
    creator: str
    transcript: str