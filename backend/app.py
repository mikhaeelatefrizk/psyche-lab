from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os

app = Flask(__name__)
CORS(app)

# Connect to Supabase
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

@app.route('/')
def home():
    return 'Psyche-Lab Backend Running - Database Connected'

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        # Save user message to database (timestamp auto-generated)
        supabase.table('messages').insert({
            'role': 'user',
            'content': user_message
        }).execute()
        
        # Generate AI response (still echo for now)
        ai_response = f'Echo: {user_message}'
        
        # Save AI response to database
        supabase.table('messages').insert({
            'role': 'assistant',
            'content': ai_response
        }).execute()
        
        return jsonify({'response': ai_response})
    except Exception as e:
        print(f"Error: {str(e)}")  # Log error for debugging
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def history():
    try:
        result = supabase.table('messages').select('*').order('created_at', desc=False).execute()
        return jsonify({'messages': result.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
