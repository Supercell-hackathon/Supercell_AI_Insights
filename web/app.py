from flask import Flask, render_template, request
import sys
import os

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.ai_insights.infrastructure.adapters.llm.api_service import ApiService

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    ai_insights = None
    user_id = None
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id:
            api_service = ApiService(game = 'brawl', user_id=user_id, model = "gemini-1.5-flash")
            ai_insights = api_service.get_ai_insights()
    
    data = {
        'title': 'Supercell AI Insights',
        'user_id': user_id,
        'ai_insights': ai_insights
    }
    
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True) 