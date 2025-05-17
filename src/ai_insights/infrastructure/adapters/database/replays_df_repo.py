"""
This module implements the Repository interface using a pandas DataFrame as the storage system.
The DataFrameRepo class provides methods to list and filter job posts stored in a DataFrame.
"""

import pandas as pd
from src.ai_insights.application.ports.repository import Repository
from typing import Optional, Dict, Any


class ReplaysDfRepo(Repository):
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def get(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieves data from the DataFrame, optionally filtered by specified criteria.

        Args:
            filters: Optional dictionary which keys are the column names of the DataFrame:

        Returns:
            A dictionary
        """
        data = self.data.copy()
        if "ids" in filters:
            data = data[data["id"].isin(filters["ids"])]
        if "character_id" in filters:
            data = data[data["character_id"] == filters["character_id"]]

        filtered_data = [
            {
                "id": row["id"],
                "title": row["title"],
                "character_id": row["character_id"],
                "replay_description": row["replay_description"],
                "embedding": row["embedding"],
                "video_path": row["video_path"],
            }
            for _, row in data.iterrows()
        ]

        return filtered_data
