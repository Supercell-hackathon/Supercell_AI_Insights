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
    if respuesta.strip().lower() in ('si', 'si', 's', 'yes'):
        print('Executing meta and community analysis...')
        módulos = [
            'src.ai_insights.infrastructure.adapters.web_scraping.youtube_scrapper',
            'src.ai_insights.infrastructure.adapters.web_scraping.web_scraper',
            'src.ai_insights.infrastructure.adapters.web_scraping.wiki_brawl_scrapper'
        ]
        for mod in módulos:
            # Ejecuta cada scraper con el mismo intérprete de Python
            resultado = subprocess.run([sys.executable, '-m', mod])
            if resultado.returncode != 0:
                print(f'Error executing {mod} (exit code {resultado.returncode})')
        print('Meta analysis and community analysis completed.')
    else:
        print('Analysis skipped. You can run it later with the command: python cli.py')

if __name__ == "__main__":
    api = ApiService(game='brawl', user_id='%239JVU8RC')
    insights = api.get_ai_insights()

    print(insights['player_description'], '\n\n\n\n')
    print(insights['performance_summary'], '\n\n\n\n')
    print(insights['recommendations'], '\n\n\n\n')

   
    run_analysis()
   