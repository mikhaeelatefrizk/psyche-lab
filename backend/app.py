from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'Psyche-Lab Backend Running'

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    # Simple echo for now - will connect to OpenRouter later
    ai_response = f'Echo: {user_message}'
    
    return jsonify({'response': ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
