import pytest
from unittest import mock


from src.ai_insights.domain.embedding import Embedding
from src.ai_insights.application.dtos.replay import ReplayDTO
from src.ai_insights.application.use_cases.list_replays_by_recom import (
    list_replays_by_recom,
)


@pytest.fixture
def entity_replays():
    return [
        ReplayDTO(
            id=1,
            title="Replay 1",
            character_id=123,
            replay_description="Description 1",
            embedding=Embedding(
                id=1, text_id=123, model_id=101, vector=[0.1, 0.2, 0.3]
            ),
            video_path="path/to/replay1",
        ),
        ReplayDTO(
            id=2,
            title="Replay 2",
            character_id=456,
            replay_description="Description 2",
            embedding=Embedding(
                id=2, text_id=456, model_id=102, vector=[0.4, 0.5, 0.6]
            ),
            video_path="path/to/replay2",
        ),
    ]


def test_list_replays_by_recom_use_case(entity_replays):
    game_api_client = mock.Mock()
    game_api_client.get.return_value = {"some": "data"}
    replays_repo = mock.Mock()
    replays_repo.get.return_value = [
        {
            "id": replay.id,
            "title": replay.title,
            "character_id": replay.character_id,
            "replay_description": replay.replay_description,
            "embedding": replay.embedding,
            "video_path": replay.video_path,
        }
        for replay in entity_replays
    ]
    relevant_replays_expected = entity_replays
    relevant_replays_actual = list_replays_by_recom(
        request="some_request",
        game_api_client=game_api_client,
        replays_repo=replays_repo,
    )
    assert len(relevant_replays_actual) == len(relevant_replays_expected)
    for expected, actual in zip(relevant_replays_expected, relevant_replays_actual):
        assert expected.id == actual.id
        assert expected.title == actual.title
        assert expected.character_id == actual.character_id
        assert expected.replay_description == actual.replay_description
        assert expected.embedding == actual.embedding
        assert expected.video_path == actual.video_path
