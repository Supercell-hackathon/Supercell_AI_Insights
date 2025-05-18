#from src.ai_insights.infrastructure.adapters.llm.api_service import ApiService
import os
from dotenv import load_dotenv
import subprocess
import sys
from src.ai_insights.infrastructure.adapters.llm.api_service import ApiService
load_dotenv()

# Remember to set brawl api token
def run_analysis() -> None:
    """
    Run the meta and community analysis.
    This function prompts the user to run the analysis and executes the scrapers if the user agrees.
    It uses subprocess to run each scraper in the same Python interpreter.
    """
    respuesta = input('Do you want to run the meta and community analysis? (yes/no): ')
    if respuesta.strip().lower() in ('si', 'yes', 'y'):
        print('Executing meta and community analysis...')
        modulos = [
            'src.ai_insights.infrastructure.adapters.web_scraping.youtube_scrapper',
            'src.ai_insights.infrastructure.adapters.web_scraping.web_scraper',
            'src.ai_insights.infrastructure.adapters.web_scraping.wiki_brawl_scrapper'
        ]
        for mod in modulos:
            # Ejecuta cada scraper con el mismo intérprete de Python
            resultado = subprocess.run([sys.executable, '-m', mod])
            if resultado.returncode != 0:
                print(f'Error executing {mod} (exit code {resultado.returncode})')
        print('Meta analysis and community analysis completed.')
    else:
        print('Analysis skipped. You can run it later with the command: python cli.py')

def get_insights() -> None:
    respuesta = input('Do you want to get player insights? (yes/no): ')
    if respuesta.strip().lower() in ('si', 'yes', 'y'):
        user_id = input('User ID:  (numbers only, eg. 9JVU8RC): ')
        api = ApiService(game='brawl', user_id='%23'+user_id)
        insights = api.get_ai_insights()

        print(insights['player_description'], '\n\n\n\n')
        print(insights['performance_summary'], '\n\n\n\n')
        print(insights['recommendations'], '\n\n\n\n')

def embed_data() -> None:
    respuesta = input('Do you want to embed the database? (yes/no): ')
    if respuesta.strip().lower() in ('si', 'yes', 'y'):
        modulos = [
            'src.ai_insights.infrastructure.adapters.database.data_embedder',
        ]
        for mod in modulos:
            resultado = subprocess.run([sys.executable, '-m', mod])
            if resultado.returncode != 0:
                print(f'Error executing {mod} (exit code {resultado.returncode})')
        print('Database embedding completed.')

if __name__ == "__main__":

    embed_data()
   
    run_analysis()
    get_insights()
   