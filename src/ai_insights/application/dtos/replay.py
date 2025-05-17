from dataclasses import dataclass
from src.ai_insights.domain.embedding import Embedding


@dataclass
class ReplayDTO:
    id: int
    title: str
    character_id: int
    replay_description: str
    embedding: Embedding
    video_path: str

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "character_id": self.character_id,
            "replay_description": self.replay_description,
            "embedding": self.embedding,
            "video_path": self.video_path,
        }
