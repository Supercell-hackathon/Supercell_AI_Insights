from dataclasses import dataclass
from typing import Optional

from src.ai_insights.domain.embedding import Embedding


@dataclass
class RecommendedCharacterDTO:
    character_id: str
    character_name: str
    reasoning: str
    embedding: Embedding
    confidence_score: Optional[float] = None
