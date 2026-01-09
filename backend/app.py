"""Psyche-Lab Backend - Autonomous AI Laboratory System"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os

# Import core intelligence modules
from core.brain_manager import BrainManager
from core.memory_system import MemorySystem
from core.learning_engine import LearningEngine
from core.main_brain import MainBrain
from core.model_interface import ModelInterface

app = Flask(__name__)
CORS(app)

# Connect to Supabase
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize Intelligence System
print("🧠 Initializing Psyche-Lab Intelligence System...")

# Initialize all subsystems
model_interface = ModelInterface()
memory_system = MemorySystem(supabase)
brain_manager = BrainManager(supabase)
learning_engine = LearningEngine(supabase, memory_system, brain_manager)

# Initialize Main Brain (central orchestrator)
main_brain = MainBrain(
    brain_manager=brain_manager,
    memory_system=memory_system,
    learning_engine=learning_engine,
    model_interface=model_interface
)

print(f"✓ Intelligence System Online")
print(f"  - Active Brains: {len(brain_manager.get_active_brains())}")
print(f"  - Memory Systems: Initialized")
print(f"  - Learning Engine: Active")
print(f"  - Models: {len(model_interface.available_models)} available")


@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'system': 'Psyche-Lab Autonomous Intelligence',
        'version': '2.0-multi-brain',
        'subsystems': {
            'brains': brain_manager.get_brain_status()['active_brains'],
            'memory': 'active',
            'learning': 'active',
            'models': list(model_interface.available_models.keys())
        }
    })


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        context = data.get('context', {})
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Process through Main Brain (full multi-brain pipeline)
        result = main_brain.process_user_input(user_message, context)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/history', methods=['GET'])
def history():
    try:
        # Get interaction history from memory
        result = supabase.table('memories').select('*').eq('memory_type', 'user_input').order('created_at', desc=False).limit(50).execute()
        return jsonify({'messages': result.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/system/status', methods=['GET'])
def system_status():
    """Get comprehensive system status"""
    try:
        status = main_brain.get_system_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/system/brains', methods=['GET'])
def get_brains():
    """Get status of all brains"""
    try:
        status = brain_manager.get_brain_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/system/memory', methods=['GET'])
def get_memory():
    """Get memory system status"""
    try:
        hierarchy = memory_system.get_memory_hierarchy()
        return jsonify(hierarchy)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/system/learning', methods=['GET'])
def get_learning():
    """Get learning system status"""
    try:
        learning_status = learning_engine.get_learning_status()
        return jsonify(learning_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/system/models', methods=['GET'])
def get_models():
    """Get model configuration status"""
    try:
        model_status = model_interface.get_model_status()
        return jsonify(model_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/system/models/register', methods=['POST'])
def register_model():
    """Register a new model (API or local)"""
    try:
        data = request.json
        model_type = data.get('type')  # 'api' or 'local'
        
        if model_type == 'api':
            provider = data.get('provider')
            api_key = data.get('api_key')
            success = model_interface.register_api_model(provider, api_key)
        elif model_type == 'local':
            model_info = data.get('model_info', {})
            success = model_interface.register_local_model(model_info)
        else:
            return jsonify({'error': 'Invalid model type'}), 400
        
        if success:
            return jsonify({'success': True, 'models': model_interface.get_model_status()})
        else:
            return jsonify({'success': False, 'error': 'Failed to register model'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/system/adapt', methods=['POST'])
def adapt_system():
    """Trigger system adaptation"""
    try:
        data = request.json
        adaptation_type = data.get('type')  # 'create_brain', 'consolidate_memory', 'evaluate_brains'
        
        result = main_brain.adapt_architecture(adaptation_type)
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
