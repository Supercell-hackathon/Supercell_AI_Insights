import pytest
import pandas as pd
from src.ai_insights.infrastructure.adapters.database.replays_df_repo import (
    ReplaysDfRepo,
)
from src.ai_insights.domain.embedding import (
    Embedding,
)  # Assuming Embedding is importable for test data


@pytest.fixture
def sample_replays_data():
    data = {
        "id": [1, 2, 3, 4, 5],
        "title": ["Replay 1", "Replay 2", "Replay 3", "Replay 4", "Replay 5"],
        "character_id": [101, 102, 101, 103, 102],
        "replay_description": ["Desc 1", "Desc 2", "Desc 3", "Desc 4", "Desc 5"],
        "embedding": [
            Embedding(id=1, text_id=1, model_id=1, vector=[0.1, 0.2]),
            Embedding(id=2, text_id=2, model_id=1, vector=[0.3, 0.4]),
            Embedding(id=3, text_id=3, model_id=1, vector=[0.5, 0.6]),
            Embedding(id=4, text_id=4, model_id=1, vector=[0.7, 0.8]),
            Embedding(id=5, text_id=5, model_id=1, vector=[0.9, 1.0]),
        ],
        "video_path": ["path/1", "path/2", "path/3", "path/4", "path/5"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def replays_repo(sample_replays_data):
    return ReplaysDfRepo(data=sample_replays_data)


def test_replays_df_repo_initialization(replays_repo, sample_replays_data):
    pd.testing.assert_frame_equal(replays_repo.data, sample_replays_data)


def test_get_all_replays(replays_repo, sample_replays_data):
    result = replays_repo.get(filters={})
    expected = [
        {
            "id": row["id"],
            "title": row["title"],
            "character_id": row["character_id"],
            "replay_description": row["replay_description"],
            "embedding": row["embedding"],
            "video_path": row["video_path"],
        }
        for _, row in sample_replays_data.iterrows()
    ]
    assert result == expected


def test_get_replays_by_ids(replays_repo, sample_replays_data):
    filter_ids = [1, 3]
    result = replays_repo.get(filters={"ids": filter_ids})
    expected_df = sample_replays_data[sample_replays_data["id"].isin(filter_ids)]
    expected = [
        {
            "id": row["id"],
            "title": row["title"],
            "character_id": row["character_id"],
            "replay_description": row["replay_description"],
            "embedding": row["embedding"],
            "video_path": row["video_path"],
        }
        for _, row in expected_df.iterrows()
    ]
    assert result == expected
    assert len(result) == 2
    assert all(item["id"] in filter_ids for item in result)


def test_get_replays_by_character_id(replays_repo, sample_replays_data):
    filter_character_id = 101
    result = replays_repo.get(filters={"character_id": filter_character_id})
    expected_df = sample_replays_data[
        sample_replays_data["character_id"] == filter_character_id
    ]
    expected = [
        {
            "id": row["id"],
            "title": row["title"],
            "character_id": row["character_id"],
            "replay_description": row["replay_description"],
            "embedding": row["embedding"],
            "video_path": row["video_path"],
        }
        for _, row in expected_df.iterrows()
    ]
    assert result == expected
    assert len(result) == 2
    assert all(item["character_id"] == filter_character_id for item in result)


def test_get_replays_by_ids_and_character_id(replays_repo, sample_replays_data):
    filter_ids = [1, 2, 3]
    filter_character_id = 101
    result = replays_repo.get(
        filters={"ids": filter_ids, "character_id": filter_character_id}
    )
    expected_df = sample_replays_data[
        sample_replays_data["id"].isin(filter_ids)
        & (sample_replays_data["character_id"] == filter_character_id)
    ]
    expected = [
        {
            "id": row["id"],
            "title": row["title"],
            "character_id": row["character_id"],
            "replay_description": row["replay_description"],
            "embedding": row["embedding"],
            "video_path": row["video_path"],
        }
        for _, row in expected_df.iterrows()
    ]
    assert result == expected
    assert len(result) == 2
    assert any(item["id"] == 1 and item["character_id"] == 101 for item in result)
    assert any(item["id"] == 3 and item["character_id"] == 101 for item in result)


def test_get_replays_no_match(replays_repo):
    result = replays_repo.get(filters={"ids": [99], "character_id": 999})
    assert result == []


def test_get_replays_empty_filters(replays_repo, sample_replays_data):
    result = replays_repo.get(filters={})
    expected_df = sample_replays_data
    expected = [
        {
            "id": row["id"],
            "title": row["title"],
            "character_id": row["character_id"],
            "replay_description": row["replay_description"],
            "embedding": row["embedding"],
            "video_path": row["video_path"],
        }
        for _, row in expected_df.iterrows()
    ]
    assert result == expected
    assert len(result) == len(sample_replays_data)


def test_get_replays_filter_ids_not_found(replays_repo):
    result = replays_repo.get(filters={"ids": [100, 200]})
    assert result == []


def test_get_replays_filter_character_id_not_found(replays_repo):
    result = replays_repo.get(filters={"character_id": 999})
    assert result == []
