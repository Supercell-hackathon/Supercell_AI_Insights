import json
from dotenv import load_dotenv
import os
import subprocess
import sys

import pandas as pd
from dotenv import load_dotenv

from src.ai_insights.infrastructure.adapters.llm.api_service import ApiService
from src.ai_insights.domain.embedding import Embedding

from src.ai_insights.application.use_cases import list_replays_by_recom

from src.ai_insights.infrastructure.adapters.database.replays_df_repo import (
    ReplaysDfRepo,
)

from src.ai_insights.infrastructure.adapters.game_api_clients.brawl_stars_client import (
    BrawlStarsClient,
)

from src.ai_insights.infrastructure.adapters.llm.ssem_embedder import SSEMEmbedder
from src.ai_insights.application.dtos.insight_dtos import RecommendedCharacterDTO
from src.ai_insights.application.use_cases.semantic_search import semantic_search


load_dotenv()
from src.ai_insights.infrastructure.adapters.llm.clip_context_generator import (
    brawler_clip_analysis,
)

API_KEY = os.getenv("BRAWLSTARS_TOKEN")
EMBEDDER_MODEL = SSEMEmbedder()
SEMANTIC_SEARCH_TRESHOLD = 0.3


# Remember to set brawl api token
def run_analysis() -> None:
    """
    Run the meta and community analysis.
    This function prompts the user to run the analysis and executes the scrapers if the user agrees.
    It uses subprocess to run each scraper in the same Python interpreter.
    """
    respuesta = input("Do you want to run the meta and community analysis? (yes/no): ")
    if respuesta.strip().lower() in ("si", "yes", "y"):
        print("Executing meta and community analysis...")
        modulos = [
            "src.ai_insights.infrastructure.adapters.web_scraping.youtube_scrapper",
            "src.ai_insights.infrastructure.adapters.web_scraping.web_scraper",
            "src.ai_insights.infrastructure.adapters.web_scraping.wiki_brawl_scrapper",
        ]
        for mod in modulos:
            # Ejecuta cada scraper con el mismo intérprete de Python
            resultado = subprocess.run([sys.executable, "-m", mod])
            if resultado.returncode != 0:
                print(f"Error executing {mod} (exit code {resultado.returncode})")
        print("Meta analysis and community analysis completed.")
    else:
        print("Analysis skipped. You can run it later with the command: python cli.py")


def get_insights():
    respuesta = input("Do you want to get player insights? (yes/no): ")
    if respuesta.strip().lower() in ("si", "yes", "y"):
        user_id = input("User ID:  (numbers only, eg. 9JVU8RC): ")
        api = ApiService(game="brawl", user_id="%23" + user_id)
        insights = api.get_ai_insights()

        print(insights["player_description"], "\n\n\n\n")
        print(insights["performance_summary"], "\n\n\n\n")
        print(insights["recommendations"], "\n\n\n\n")
        return insights["recommendations"]


def embed_data() -> None:
    respuesta = input("Do you want to embed the database? (yes/no): ")
    if respuesta.strip().lower() in ("si", "yes", "y"):
        modulos = [
            "src.ai_insights.infrastructure.adapters.database.data_embedder",
        ]
        for mod in modulos:
            resultado = subprocess.run([sys.executable, "-m", mod])
            if resultado.returncode != 0:
                print(f"Error executing {mod} (exit code {resultado.returncode})")
        print("Database embedding completed.")


def show_replays_matching_recommendations(recommendations):
    # parse recommendations
    if recommendations.startswith("```json"):
        recommendations = recommendations[7:]  # Remove ```json\n
    if recommendations.endswith("```"):
        recommendations = recommendations[:-3]  # Remove ```
    recommendations_dict = json.loads(recommendations)
    recommendations = recommendations_dict["recommendations"]

    # load brawlers and ids data
    with open("data/processed/brawlers_to_ids.json", "r") as f:
        brawler_to_id = json.load(f)

    # add brawler_id to each recommendation
    for ix, recommendation in enumerate(recommendations):
        brawler_name = recommendation["brawler_name"].upper()
        brawler_id = brawler_to_id.get(brawler_name)
        recommendations[ix]["brawler_id"] = brawler_id

    # embed recommendation tips
    recommendations_keys = list(recommendations[0].keys())
    tip_column = "concise_tip" if "concise_tip" in recommendations_keys else "tip"

    concise_tips_list = [
        recommendation[tip_column] for recommendation in recommendations
    ]
    tips_embeddings = EMBEDDER_MODEL.generate_embeddings(concise_tips_list)
    for ix in range(len(recommendations)):
        recommendations[ix]["concise_tip_embedding"] = tips_embeddings[ix]
    # create recommendation objects
    recommendations_objects = [
        RecommendedCharacterDTO(
            character_id=recommendation["brawler_id"],
            character_name=recommendation["brawler_name"],
            reasoning=recommendation[tip_column],
            embedding=Embedding(
                id=0,
                text_id=0,
                model_id=1,
                vector=recommendation["concise_tip_embedding"],
            ),
        )
        for recommendation in recommendations
    ]

    # load replays data
    videos_data_df = pd.read_csv("data/mock/mock_replays.csv")
    replay_descriptions = videos_data_df["replay_description"].tolist()
    # embed replay descriptions
    video_descriptions_embeddings = EMBEDDER_MODEL.generate_embeddings(
        replay_descriptions
    )
    # add embeddings to dataframe
    for ix, row in videos_data_df.iterrows():
        embedding = video_descriptions_embeddings[ix]
        embedding = Embedding(id=ix, text_id=ix, model_id=1, vector=embedding)
        videos_data_df.at[ix, "embedding"] = embedding

    # get replays from players with the same brawler in the rank of brawlers (TOP)
    replays_df_repo = ReplaysDfRepo(videos_data_df)
    brawl_stars_client = BrawlStarsClient(API_KEY)

    country_code = "global"

    print("\nRecovering replays for recommendations...\n")
    recovered_replays = []
    for recommendation in recommendations:
        brawler_id = recommendation["brawler_id"]
        endpoint = f"/v1/rankings/{country_code}/brawlers/{brawler_id}"

        request = {
            "endpoint": endpoint,
            "filters": ["items", "tag"],
        }

        replays_list = list_replays_by_recom.list_replays_by_recom(
            request=request,
            game_api_client=brawl_stars_client,
            replays_repo=replays_df_repo,
        )

        recovered_replays.extend(replays_list)
    # reshape for semantic search
    for ix in range(len(recovered_replays)):
        recovered_replays[ix].embedding.vector = recovered_replays[
            ix
        ].embedding.vector.reshape(1, -1)

    relevant_replays_objects = []
    for recommendation in recommendations_objects:
        recommendation.embedding.vector = recommendation.embedding.vector.reshape(1, -1)
        relevant_replays = semantic_search(
            recommendation, recovered_replays, SEMANTIC_SEARCH_TRESHOLD
        )
        relevant_replays_objects.extend(relevant_replays)

    print("Relevant replays found: ", len(relevant_replays_objects))
    # print relevant replays
    for replay in relevant_replays_objects:
        print(f"Title: {replay.title}")
        print(f"Description: {replay.replay_description}\n")


def analyze_clip() -> bool:
    """
    Prompts the user to run video clip analysis for a specific Brawler.
    Returns True if analysis was attempted, False otherwise.
    """
    did_run_analysis = False
    respuesta = input(
        "Do you want to run a video clip analysis for a specific Brawler? (yes/no): "
    )
    if respuesta.strip().lower() in ("si", "yes", "s", "y"):
        brawler_name_input = input(
            "Enter the Brawler's name for the video clip analysis (e.g., hank, piper): "
        )
        if brawler_name_input.strip():
            print(
                f"CLI: Triggering video clip analysis for Brawler: {brawler_name_input.strip()}"
            )
            try:
                brawler_clip_analysis(brawler_name=brawler_name_input.strip())
                did_run_analysis = True
            except NameError:
                print(
                    "CLI Error: 'brawler_clip_analysis' function is not available (import failed)."
                )
            except Exception as e:
                print(
                    f"CLI Error: An unexpected error occurred during video clip analysis for '{brawler_name_input.strip()}': {e}"
                )
        else:
            print("No Brawler name provided. Video clip analysis skipped.")
    else:
        print("Video clip analysis skipped by user.")
    return did_run_analysis


def analyze_clip() -> bool:
    """
    Prompts the user to run video clip analysis for a specific Brawler.
    Returns True if analysis was attempted, False otherwise.
    """
    did_run_analysis = False
    respuesta = input(
        "Do you want to run a video clip analysis for a specific Brawler? (yes/no): "
    )
    if respuesta.strip().lower() in ("si", "yes", "s", "y"):
        brawler_name_input = input(
            "Enter the Brawler's name for the video clip analysis (e.g., hank, piper): "
        )
        if brawler_name_input.strip():
            print(
                f"CLI: Triggering video clip analysis for Brawler: {brawler_name_input.strip()}"
            )
            try:
                brawler_clip_analysis(brawler_name=brawler_name_input.strip())
                did_run_analysis = True
            except NameError:
                print(
                    "CLI Error: 'brawler_clip_analysis' function is not available (import failed)."
                )
            except Exception as e:
                print(
                    f"CLI Error: An unexpected error occurred during video clip analysis for '{brawler_name_input.strip()}': {e}"
                )
        else:
            print("No Brawler name provided. Video clip analysis skipped.")
    else:
        print("Video clip analysis skipped by user.")
    return did_run_analysis


if __name__ == "__main__":
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    recommendations = get_insights()

    # embed_data()
    # analyze_clip()
    # run_analysis()

    show_replays_matching_recommendations(recommendations)
