"""Brain Manager - Manages the lifecycle and coordination of specialized AI brains"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import json


class Brain:
    """Represents a single specialized intelligence unit"""
    
    def __init__(self, brain_id: str, role: str, creation_time: datetime, config: dict = None):
        self.id = brain_id
        self.role = role  # e.g., 'emotion_analyzer', 'pattern_detector', 'meta_reasoner'
        self.creation_time = creation_time
        self.config = config or {}
        self.strength = 0.5  # Initial confidence/effectiveness score
        self.active = True
        self.analysis_count = 0
        self.success_rate = 0.0
        self.last_analysis = None
        
    def analyze(self, input_data: dict) -> dict:
        """Perform brain-specific analysis on input data"""
        self.analysis_count += 1
        self.last_analysis = datetime.utcnow()
        
        # This is the interface - actual implementation would call specific models
        analysis = {
            'brain_id': self.id,
            'role': self.role,
            'confidence': self.strength,
            'findings': {},
            'timestamp': self.last_analysis.isoformat()
        }
        
        return analysis
    
    def update_strength(self, feedback: float):
        """Update brain effectiveness based on feedback"""
        # Simple exponential moving average
        self.strength = 0.8 * self.strength + 0.2 * feedback
        
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'role': self.role,
            'creation_time': self.creation_time.isoformat(),
            'strength': self.strength,
            'active': self.active,
            'analysis_count': self.analysis_count,
            'success_rate': self.success_rate
        }


class BrainManager:
    """Manages the multi-brain cognitive architecture"""
    
    def __init__(self, db_client):
        self.db = db_client
        self.brains: Dict[str, Brain] = {}
        self.brain_roles = {
            'emotion_analyzer': 'Analyzes emotional patterns and states',
            'pattern_detector': 'Identifies behavioral patterns and anomalies',
            'topic_tracker': 'Tracks topic switches and conversation flow',
            'prediction_engine': 'Predicts user reactions and needs',
            'meta_analyzer': 'Analyzes outputs from other brains',
        }
        self._initialize_brains()
        
    def _initialize_brains(self):
        """Initialize the core set of specialized brains"""
        # Load existing brains from database or create new ones
        try:
            result = self.db.table('brains').select('*').eq('active', True).execute()
            if result.data:
                for brain_data in result.data:
                    brain = Brain(
                        brain_id=brain_data['id'],
                        role=brain_data['role'],
                        creation_time=datetime.fromisoformat(brain_data['creation_time']),
                        config=brain_data.get('config', {})
                    )
                    brain.strength = brain_data.get('strength', 0.5)
                    brain.analysis_count = brain_data.get('analysis_count', 0)
                    self.brains[brain.id] = brain
            else:
                # Create initial brains
                for role, description in self.brain_roles.items():
                    self.create_brain(role, {'description': description})
        except Exception as e:
            print(f"Error initializing brains: {e}")
            # Create default brains even if DB fails
            for role, description in self.brain_roles.items():
                brain_id = str(uuid.uuid4())
                self.brains[brain_id] = Brain(
                    brain_id=brain_id,
                    role=role,
                    creation_time=datetime.utcnow(),
                    config={'description': description}
                )
    
    def create_brain(self, role: str, config: dict = None) -> Brain:
        """Birth a new specialized brain"""
        brain_id = str(uuid.uuid4())
        brain = Brain(
            brain_id=brain_id,
            role=role,
            creation_time=datetime.utcnow(),
            config=config
        )
        
        self.brains[brain_id] = brain
        
        # Persist to database
        try:
            self.db.table('brains').insert({
                'id': brain_id,
                'role': role,
                'creation_time': brain.creation_time.isoformat(),
                'config': config or {},
                'strength': brain.strength,
                'active': True,
                'analysis_count': 0
            }).execute()
        except Exception as e:
            print(f"Error saving brain to database: {e}")
        
        return brain
    
    def terminate_brain(self, brain_id: str, reason: str = 'redundant'):
        """Terminate an ineffective or redundant brain"""
        if brain_id in self.brains:
            self.brains[brain_id].active = False
            try:
                self.db.table('brains').update({
                    'active': False,
                    'termination_reason': reason,
                    'termination_time': datetime.utcnow().isoformat()
                }).eq('id', brain_id).execute()
            except Exception as e:
                print(f"Error terminating brain: {e}")
            del self.brains[brain_id]
    
    def merge_brains(self, brain_ids: List[str], new_role: str) -> Brain:
        """Merge multiple brains into a single more powerful brain"""
        if len(brain_ids) < 2:
            raise ValueError("Need at least 2 brains to merge")
        
        # Calculate merged strength
        merged_strength = sum(self.brains[bid].strength for bid in brain_ids if bid in self.brains) / len(brain_ids)
        
        # Create new merged brain
        merged_brain = self.create_brain(
            role=new_role,
            config={
                'merged_from': brain_ids,
                'merge_time': datetime.utcnow().isoformat()
            }
        )
        merged_brain.strength = min(1.0, merged_strength * 1.2)  # Bonus for merging
        
        # Terminate old brains
        for bid in brain_ids:
            if bid in self.brains:
                self.terminate_brain(bid, reason='merged')
        
        return merged_brain
    
    def get_active_brains(self) -> List[Brain]:
        """Get all currently active brains"""
        return [brain for brain in self.brains.values() if brain.active]
    
    def analyze_with_all_brains(self, input_data: dict) -> List[dict]:
        """Run analysis through all active brains"""
        analyses = []
        for brain in self.get_active_brains():
            try:
                analysis = brain.analyze(input_data)
                analyses.append(analysis)
            except Exception as e:
                print(f"Brain {brain.id} ({brain.role}) analysis failed: {e}")
        return analyses
    
    def evaluate_brain_performance(self):
        """Autonomously evaluate which brains are effective and which should be terminated"""
        for brain in list(self.brains.values()):
            if brain.analysis_count > 10 and brain.strength < 0.2:
                # Low performing brain after significant use
                self.terminate_brain(brain.id, reason='low_performance')
            elif brain.analysis_count > 100 and brain.strength > 0.9:
                # High performing brain - could spawn a variation
                pass
    
    def get_brain_status(self) -> dict:
        """Get status of all brains for observation"""
        return {
            'total_brains': len(self.brains),
            'active_brains': len(self.get_active_brains()),
            'brains': [brain.to_dict() for brain in self.brains.values()]
        }
