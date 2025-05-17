import pytest
import os

from dotenv import load_dotenv
from src.ai_insights.infrastructure.adapters.game_api_clients.brawl_stars_client import (
    BrawlStarsClient,
)


@pytest.fixture
def client():
    # Load environment variables from .env file
    load_dotenv()
    # Set the API key for Brawl Stars
    API_KEY = os.getenv("BRAWL_STARS_API_KEY")
    """This fixture creates and returns a BrawlStarsClient instance."""
    instance = BrawlStarsClient(API_KEY)
    return instance  # 'yield' is often used to allow for teardown code after it


def test_brawl_stars_client_get(client):
    brawler_id = 16000000
    endpoint = f"/v1/brawlers/{brawler_id}"
    response = client.get(endpoint)
    expected_response = {
        "id": 16000000,
        "name": "SHELLY",
        "starPowers": [
            {"id": 23000076, "name": "SHELL SHOCK"},
            {"id": 23000135, "name": "BAND-AID"},
        ],
        "gadgets": [
            {"id": 23000255, "name": "FAST FORWARD"},
            {"id": 23000288, "name": "CLAY PIGEONS"},
        ],
    }
    assert (
        response == expected_response
    ), f"Expected {expected_response}, but got {response}"
