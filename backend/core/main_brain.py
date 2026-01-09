"""Main Brain - Meta-reasoning controller that integrates all subsystems"""
from datetime import datetime
from typing import Dict, List, Optional
import json


class MainBrain:
    """Central intelligence orchestrator - integrates all brains and makes final decisions"""
    
    def __init__(self, brain_manager, memory_system, learning_engine, model_interface):
        self.brain_manager = brain_manager
        self.memory = memory_system
        self.learning = learning_engine
        self.model_interface = model_interface
        self.internal_state = {
            'focus': 'neutral',
            'confidence': 0.5,
            'uncertainty_threshold': 0.7
        }
        self.reasoning_log = []
    
    def process_user_input(self, user_message: str, context: dict = None) -> dict:
        """Main entry point: process user input and generate response"""
        start_time = datetime.utcnow()
        
        # Store raw interaction in memory
        interaction_data = {
            'message': user_message,
            'timestamp': start_time.isoformat(),
            'context': context or {}
        }
        self.memory.store_raw_memory(interaction_data, 'user_input')
        
        # Phase 1: Multi-brain analysis
        brain_analyses = self.brain_manager.analyze_with_all_brains({
            'input': user_message,
            'context': context
        })
        
        # Phase 2: Meta-reasoning - integrate brain outputs
        meta_analysis = self._perform_meta_reasoning(brain_analyses)
        
        # Phase 3: Retrieve relevant memories
        relevant_memories = self.memory.retrieve_memories({'input': user_message}, limit=5)
        
        # Phase 4: Test theories
        theory_tests = self.learning.test_theories_against_interaction(interaction_data)
        
        # Phase 5: Make prediction about user
        prediction = self.learning.predict_user_response(context or {})
        
        # Phase 6: Generate response using model
        response_data = self._generate_response(
            user_message=user_message,
            meta_analysis=meta_analysis,
            memories=relevant_memories,
            theories=theory_tests,
            prediction=prediction
        )
        
        # Phase 7: Learn from implicit signals (response time, etc.)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        self._extract_implicit_signals({
            'processing_time': processing_time,
            'confidence': meta_analysis.get('confidence', 0.5)
        })
        
        # Log reasoning process
        self._log_reasoning(
            user_input=user_message,
            brain_analyses=brain_analyses,
            meta_analysis=meta_analysis,
            final_response=response_data
        )
        
        return {
            'response': response_data['text'],
            'internal_reasoning': self._format_reasoning_for_display(meta_analysis),
            'brain_states': self.brain_manager.get_brain_status(),
            'memory_state': self.memory.get_memory_hierarchy(),
            'learning_state': self.learning.get_learning_status(),
            'confidence': meta_analysis.get('confidence', 0.5),
            'processing_time_seconds': processing_time
        }
    
    def _perform_meta_reasoning(self, brain_analyses: List[dict]) -> dict:
        """Meta-analyze outputs from all specialized brains"""
        meta = {
            'consensus': {},
            'conflicts': [],
            'confidence': 0.0,
            'dominant_signal': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if not brain_analyses:
            meta['confidence'] = 0.3
            return meta
        
        # Aggregate confidence scores
        total_confidence = sum(b.get('confidence', 0) for b in brain_analyses)
        meta['confidence'] = total_confidence / len(brain_analyses) if brain_analyses else 0
        
        # Identify conflicts between brains
        brain_outputs = {b['brain_id']: b for b in brain_analyses}
        
        # Find dominant signal (highest confidence brain)
        if brain_analyses:
            dominant = max(brain_analyses, key=lambda b: b.get('confidence', 0))
            meta['dominant_signal'] = {
                'brain': dominant.get('role'),
                'confidence': dominant.get('confidence')
            }
        
        # Check for conflicts (brains with opposing high-confidence signals)
        high_conf_brains = [b for b in brain_analyses if b.get('confidence', 0) > 0.7]
        if len(high_conf_brains) > 1:
            meta['conflicts'].append({
                'type': 'multiple_high_confidence',
                'brains': [b['role'] for b in high_conf_brains]
            })
        
        return meta
    
    def _generate_response(self, user_message: str, meta_analysis: dict, 
                          memories: List, theories: List, prediction: dict) -> dict:
        """Generate final response using model interface"""
        
        # Build context for model
        context_for_model = {
            'user_message': user_message,
            'system_confidence': meta_analysis.get('confidence', 0.5),
            'relevant_memories': [m.to_dict() for m in memories[:3]],
            'active_theories': [t for t in theories if t.get('new_strength', 0) > 0.6][:3],
            'prediction': prediction
        }
        
        # For now, use a simple response (would call actual model)
        # In production, this would call the model_interface
        response_text = self.model_interface.generate_response(context_for_model)
        
        return {
            'text': response_text,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _extract_implicit_signals(self, signals: dict):
        """Extract and learn from implicit signals"""
        self.learning.learn_from_implicit_signals(signals)
    
    def _log_reasoning(self, user_input: str, brain_analyses: List, 
                      meta_analysis: dict, final_response: dict):
        """Log the reasoning process for transparency"""
        reasoning_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_input': user_input,
            'brain_count': len(brain_analyses),
            'meta_confidence': meta_analysis.get('confidence'),
            'response': final_response.get('text', '')[:100]  # First 100 chars
        }
        self.reasoning_log.append(reasoning_entry)
        
        # Keep only recent reasoning logs
        if len(self.reasoning_log) > 100:
            self.reasoning_log = self.reasoning_log[-100:]
    
    def _format_reasoning_for_display(self, meta_analysis: dict) -> dict:
        """Format internal reasoning for user observation"""
        return {
            'meta_confidence': round(meta_analysis.get('confidence', 0), 2),
            'dominant_brain': meta_analysis.get('dominant_signal', {}).get('brain'),
            'conflicts_detected': len(meta_analysis.get('conflicts', [])),
            'reasoning_depth': 'multi-brain-meta-analysis'
        }
    
    def request_resource(self, resource_type: str, details: dict) -> dict:
        """System requests resources from user (models, data, etc.)"""
        request = {
            'request_type': resource_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'reason': self._explain_resource_need(resource_type, details)
        }
        return request
    
    def _explain_resource_need(self, resource_type: str, details: dict) -> str:
        """Explain why the system needs a resource"""
        explanations = {
            'model': f"The system requires a {details.get('model_type')} model to improve {details.get('capability')}.",
            'data': f"Additional data about {details.get('topic')} would enhance understanding.",
            'compute': f"More computational resources needed for {details.get('task')}."
        }
        return explanations.get(resource_type, "Resource needed for system improvement.")
    
    def adapt_architecture(self, adaptation_type: str):
        """Autonomously adapt internal architecture"""
        if adaptation_type == 'create_brain':
            # Determine if new brain needed
            brain_perf = self.brain_manager.get_brain_status()
            # Logic to decide on new brain creation
            pass
        elif adaptation_type == 'consolidate_memory':
            removed_count = self.memory.consolidate_memories()
            return {'memories_removed': removed_count}
        elif adaptation_type == 'evaluate_brains':
            self.brain_manager.evaluate_brain_performance()
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status for observation"""
        return {
            'main_brain': {
                'state': self.internal_state,
                'reasoning_log_size': len(self.reasoning_log)
            },
            'brains': self.brain_manager.get_brain_status(),
            'memory': self.memory.get_memory_hierarchy(),
            'learning': self.learning.get_learning_status(),
            'timestamp': datetime.utcnow().isoformat()
        }
