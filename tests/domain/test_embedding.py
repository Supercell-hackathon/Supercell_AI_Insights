import pytest
from src.ai_insights.domain.embedding import Embedding


def test_embedding_creation():
    """Test the creation of an Embedding object."""
    embedding_id = 1
    text_id = 123  # Changed to int
    model_id = 101
    vector = [0.1, 0.2, 0.3]
    embedding = Embedding(
        id=embedding_id, text_id=text_id, model_id=model_id, vector=vector
    )

    assert embedding.id == embedding_id
    assert embedding.text_id == text_id
    assert embedding.model_id == model_id
    assert embedding.vector == vector


def test_embedding_to_dict():
    """Test the to_dict method of the Embedding class."""
    embedding_id = 1
    text_id = 123  # Changed to int
    model_id = 101
    vector = [0.1, 0.2, 0.3]
    embedding = Embedding(
        id=embedding_id, text_id=text_id, model_id=model_id, vector=vector
    )
    embedding_dict = embedding.to_dict()

    expected_dict = {
        "id": embedding_id,
        "text_id": text_id,
        "model_id": model_id,
        "vector": vector,
    }
    assert embedding_dict == expected_dict


def test_embedding_from_dict():
    """Test the from_dict class method of the Embedding class."""
    embedding_data = {
        "id": 1,
        "text_id": 123,  # Changed to int
        "model_id": 101,
        "vector": [0.1, 0.2, 0.3],
    }
    embedding = Embedding.from_dict(embedding_data)

    assert embedding.id == embedding_data["id"]
    assert embedding.text_id == embedding_data["text_id"]
    assert embedding.model_id == embedding_data["model_id"]
    assert embedding.vector == embedding_data["vector"]


def test_embedding_from_dict_with_extra_keys():
    """Test from_dict with a dictionary containing extra keys (should be ignored)."""
    embedding_data = {
        "id": 2,
        "text_id": 456,  # Changed to int
        "model_id": 102,
        "vector": [0.4, 0.5, 0.6],
        "extra_key": "should_be_ignored",
    }
    # Expecting a TypeError because the Embedding constructor does not accept extra_key
    with pytest.raises(TypeError):
        Embedding.from_dict(embedding_data)
