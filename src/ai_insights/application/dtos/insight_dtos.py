from dataclasses import dataclass
from typing import Optional


@dataclass
class RecommendedCharacterDTO:
    character_id: str
    character_name: str
    reasoning: str
    confidence_score: Optional[float] = None
