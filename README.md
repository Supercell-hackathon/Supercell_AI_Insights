# Supercell AI Insights ⚔️🧠

**A Supercell Hackathon project ("NITA BEAR LOVERS" team) focused on leveraging AI to enhance player experiences across Supercell's universe of games through intelligent insights and personalized recommendations.** 

## Vision

Supercell AI Insights aims to empower players by providing them with a deeper understanding of game dynamics and personalized guidance. By harvesting and analyzing game data, community sentiment, and individual gameplay patterns, we strive to offer tailored suggestions that help players discover new strategies, master new characters/units, and ultimately, derive more enjoyment from their favorite Supercell games.

While our initial proof-of-concept and development focused on **Brawl Stars**, the core AI framework and methodologies are designed with the vision to be adaptable to other beloved Supercell titles. Our main goal is to **improve the player experience by recommending new characters/units, effective techniques, and optimal builds.**

## Core Components & Features

The project is built around several key components to achieve its goals:

1.  **Cross-Platform Meta & Community Scraper:**
    * Automatically harvests data from key sources like official game Wikis (e.g., Brawl Stars Wiki), community hubs (e.g., BrawlHub), and YouTube.
    * Gathers information on characters/units (stats, abilities, etc.), game meta, and community sentiment. 
    * This data feeds into a unified document store for further processing and retrieval. 

2.  **AI-Driven Profiling & Recommendations:**
    * The system aims to use player profiles (potentially via Supercell API) and meta trends to suggest tailored character/unit builds, gadgets, and tactics. 
    * Generates recommendations and insights on game style.

3.  **Dual Embedding Pipeline & RAG:**
    * We employ a dual embedding strategy, indexing both raw scraped data and AI-generated insights (like tips or replay analyses). 
    * This enables powerful Retrieval Augmented Generation (RAG), where the LLM's knowledge is augmented with specific, current game data to provide relevant and accurate outputs.
    * Supports semantic search capabilities over the indexed data. 
4.  **Generative AI Gameplay Clip Analysis (Powered by Google Gemini):**
    * **Gameplay Input:** The system analyzes short video clips of gameplay.
    * **Contextual Understanding:** Each analysis is enriched by specific context provided about the game state or characters/units in focus (via `.txt` files).
    * **AI-Generated Summaries:** Utilizes a "Video to text AI model" (like Google Gemini) to generate concise, Brawler-focused textual descriptions of key actions and abilities used. Player names are intentionally omitted.
    * **Structured Output:** The analysis for each clip is saved as a JSON file (e.g., `data/raw/{character_name}_clip_context.json`).

## AI Techniques & Technologies

* **Generative AI (Google Gemini):** For video understanding, contextual reasoning, and textual description generation (Video to text AI model.
* **Large Language Models (LLM):** Central to generating insights, recommendations, and analyzing game style. 
* **Retrieval Augmented Generation (RAG):** To provide LLMs with relevant, up-to-date game data from our document and vector databases.
* **Embeddings:** Used to represent textual data (Brawler info, community tips, replay descriptions) semantically, stored in Vector DBs for efficient retrieval. 
* **Web Scraping:** Python-based tools for automated data collection.
* **Data Storage:** Utilizing Document DBs for scraped game data and community sentiment, and Vector DBs for embeddings. 
* **Python:** The core programming language for all project components.

# Demo
Basic website showing all AI generated data! 🤖

https://github.com/user-attachments/assets/e88bff51-1d57-4a94-97d3-020afbc3d676



## Project Structure Overview

The project's codebase is organized to reflect its architecture:

* `cli.py`: The main command-line interface for interacting with the system.
* `data/`: Contains raw input data (video clips in `data/raw/clips/`, textual contexts in `data/raw/context/`) and processed outputs (like the JSON analyses from video clips).
* `src/ai_insights/`: Houses the core application logic:
    * `infrastructure/adapters/llm/`: Includes `clip_context_generator.py` for Gemini API interaction and the `api_service.py` for other LLM-driven insights.
    * `infrastructure/adapters/web_scraping/`: Modules for data collection (YouTube, Wikis, etc.). 
    * (Other directories like `application`, `domain` define business logic and data structures).

## Target Users

* **Average Player:** To receive daily, bite-sized insights tailored to their playstyle, helping them discover new builds, tricks, and trends without extensive research. 
* **Developers (Supercell):** To get a real-time pulse of community sentiment and meta shifts, with massive data distilled into actionable feedback. 

## Getting Started & Usage (Current PoC - Brawl Stars Focused)

The current implementation provides a proof-of-concept primarily demonstrated with Brawl Stars.

1.  **Environment Setup:**
    * Create a `.env` file in the project root and add your `GOOGLE_API_KEY` (for Gemini) and any other necessary API keys (e.g., `BRAWL_API_TOKEN` if `ApiService` uses it directly).
        ```env
        GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
        # BRAWL_STARS_API_URL="[https://api.brawlstars.com](https://api.brawlstars.com)" # If needed by ApiService
        # BRAWL_API_TOKEN="YOUR_BRAWL_STARS_API_TOKEN"  # If needed by ApiService
        ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set `PYTHONPATH`:**
    Ensure Python can find your `src` modules. From the project root:
    * Linux/macOS: `export PYTHONPATH="$PWD:$PYTHONPATH"`
    * Windows (PowerShell): `$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"`

4.  **Running the Video Clip Analysis:**
    * Place video clips (e.g., `hank_clip.mp4`) in `data/raw/clips/`.
    * Create/edit context files (e.g., `hank_context.txt`) in `data/raw/context/`.
    * Execute from the project root (replace `hank` with the target Brawler/character name):
        ```bash
        python cli.py --analyze_clip hank
        ```
    * The output JSON will be in `data/raw/hank_clip_context.json`.

5.  **Running Default CLI Flow (Player Insights & Scraper Prompt):**
    ```bash
    python cli.py
    ```

## Future Roadmap

Our vision for Supercell AI Insights extends further:

* **Fine-tuning of Video-to-Text LLM:** Enhance the accuracy and specificity of gameplay analysis through model fine-tuning. 
* **Expanded Data Sources:** Continuously gather information from a wider array of multiple sources. 
* **Advanced Community Sentiment Analysis:** Develop more sophisticated methods to get and interpret community feedback. 
* **Generalization:** Adapt and extend the system to be effectively used across multiple Supercell games. 
* Integrate with Supercell API for richer embedded player data. 
* Develop the "Semantic Search Matcher" for relevant replays. 
