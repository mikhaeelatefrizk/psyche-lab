"""Learning Engine and Theory Manager - Autonomous learning and hypothesis testing"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import random


class Theory:
    """Represents a hypothesis about the user"""
    
    def __init__(self, theory_id: str, hypothesis: str, category: str):
        self.id = theory_id
        self.hypothesis = hypothesis
        self.category = category  # 'behavior', 'preference', 'tendency', 'trait'
        self.created_at = datetime.utcnow()
        self.strength = 0.5  # Confidence in this theory
        self.evidence_for = 0
        self.evidence_against = 0
        self.tests_performed = 0
        self.last_tested = None
        self.competing_theories: List[str] = []  # IDs of theories that compete with this one
        
    def test(self, outcome: bool, weight: float = 1.0):
        """Test the theory with an outcome"""
        self.tests_performed += 1
        self.last_tested = datetime.utcnow()
        
        if outcome:
            self.evidence_for += weight
        else:
            self.evidence_against += weight
        
        # Update strength using Bayesian-like update
        total_evidence = self.evidence_for + self.evidence_against
        if total_evidence > 0:
            self.strength = self.evidence_for / total_evidence
    
    def merge_with(self, other_theory: 'Theory') -> 'Theory':
        """Merge this theory with another compatible theory"""
        merged_id = str(uuid.uuid4())
        merged_hypothesis = f"{self.hypothesis} AND {other_theory.hypothesis}"
        
        merged = Theory(merged_id, merged_hypothesis, self.category)
        merged.strength = (self.strength + other_theory.strength) / 2
        merged.evidence_for = self.evidence_for + other_theory.evidence_for
        merged.evidence_against = self.evidence_against + other_theory.evidence_against
        merged.tests_performed = self.tests_performed + other_theory.tests_performed
        
        return merged
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'hypothesis': self.hypothesis,
            'category': self.category,
            'strength': self.strength,
            'evidence_for': self.evidence_for,
            'evidence_against': self.evidence_against,
            'tests_performed': self.tests_performed,
            'created_at': self.created_at.isoformat(),
            'last_tested': self.last_tested.isoformat() if self.last_tested else None
        }


class LearningEngine:
    """Autonomous learning system with theory generation and evolution"""
    
    def __init__(self, db_client, memory_system, brain_manager):
        self.db = db_client
        self.memory = memory_system
        self.brain_manager = brain_manager
        self.theories: Dict[str, Theory] = {}
        self.prediction_history: List[dict] = []
        self._load_theories()
    
    def _load_theories(self):
        """Load existing theories from database"""
        try:
            result = self.db.table('theories').select('*').eq('active', True).execute()
            for theory_data in result.data:
                theory = Theory(
                    theory_id=theory_data['id'],
                    hypothesis=theory_data['hypothesis'],
                    category=theory_data['category']
                )
                theory.strength = theory_data.get('strength', 0.5)
                theory.evidence_for = theory_data.get('evidence_for', 0)
                theory.evidence_against = theory_data.get('evidence_against', 0)
                theory.tests_performed = theory_data.get('tests_performed', 0)
                self.theories[theory.id] = theory
        except Exception as e:
            print(f"Error loading theories: {e}")
    
    def generate_theory_from_pattern(self, pattern: dict) -> Theory:
        """Automatically generate a theory from an observed pattern"""
        theory_id = str(uuid.uuid4())
        
        # Create hypothesis based on pattern
        hypothesis = f"User tends to {pattern.get('pattern_type', 'behave')} in {pattern.get('context', 'certain situations')}"
        category = pattern.get('category', 'behavior')
        
        theory = Theory(theory_id, hypothesis, category)
        self.theories[theory_id] = theory
        
        # Persist to database
        try:
            self.db.table('theories').insert({
                'id': theory_id,
                'hypothesis': hypothesis,
                'category': category,
                'strength': theory.strength,
                'evidence_for': 0,
                'evidence_against': 0,
                'tests_performed': 0,
                'created_at': theory.created_at.isoformat(),
                'active': True
            }).execute()
        except Exception as e:
            print(f"Error saving theory: {e}")
        
        return theory
    
    def test_theories_against_interaction(self, interaction: dict) -> List[dict]:
        """Test all theories against a new user interaction"""
        results = []
        
        for theory in self.theories.values():
            # Simple heuristic testing - in production would use more sophisticated analysis
            predicted_outcome = theory.strength > 0.5
            actual_outcome = self._evaluate_theory_fit(theory, interaction)
            
            # Test the theory
            theory.test(actual_outcome == predicted_outcome)
            
            results.append({
                'theory_id': theory.id,
                'hypothesis': theory.hypothesis,
                'predicted': predicted_outcome,
                'actual': actual_outcome,
                'match': actual_outcome == predicted_outcome,
                'new_strength': theory.strength
            })
        
        # Evolution step: remove weak theories, merge strong ones
        self._evolve_theories()
        
        return results
    
    def _evaluate_theory_fit(self, theory: Theory, interaction: dict) -> bool:
        """Evaluate if interaction supports the theory (simplified)"""
        # This is a placeholder - would use actual semantic analysis
        return random.random() > 0.5  # Random for now
    
    def _evolve_theories(self):
        """Evolve the theory space: remove weak, merge compatible, generate new"""
        # Remove theories with very low strength after sufficient testing
        to_remove = []
        for theory_id, theory in self.theories.items():
            if theory.tests_performed > 20 and theory.strength < 0.2:
                to_remove.append(theory_id)
                try:
                    self.db.table('theories').update({'active': False}).eq('id', theory_id).execute()
                except Exception as e:
                    print(f"Error deactivating theory: {e}")
        
        for theory_id in to_remove:
            del self.theories[theory_id]
        
        # Identify theories that could be merged
        strong_theories = [t for t in self.theories.values() if t.strength > 0.7 and t.tests_performed > 10]
        if len(strong_theories) >= 2:
            # Merge two strong theories
            theory1 = strong_theories[0]
            theory2 = strong_theories[1]
            merged = theory1.merge_with(theory2)
            self.theories[merged.id] = merged
            
            try:
                self.db.table('theories').insert({
                    'id': merged.id,
                    'hypothesis': merged.hypothesis,
                    'category': merged.category,
                    'strength': merged.strength,
                    'evidence_for': merged.evidence_for,
                    'evidence_against': merged.evidence_against,
                    'tests_performed': merged.tests_performed,
                    'created_at': merged.created_at.isoformat(),
                    'active': True
                }).execute()
            except Exception as e:
                print(f"Error saving merged theory: {e}")
    
    def predict_user_response(self, context: dict) -> dict:
        """Predict user response based on theories and patterns"""
        # Get relevant theories
        relevant_theories = [t for t in self.theories.values() if t.strength > 0.6]
        
        # Combine theories for prediction
        prediction = {
            'likely_response_type': 'neutral',
            'confidence': 0.5,
            'reasoning': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for theory in relevant_theories[:5]:  # Top 5 theories
            prediction['reasoning'].append({
                'theory': theory.hypothesis,
                'strength': theory.strength
            })
        
        if relevant_theories:
            prediction['confidence'] = sum(t.strength for t in relevant_theories) / len(relevant_theories)
        
        # Store prediction for later evaluation
        self.prediction_history.append({
            'prediction': prediction,
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return prediction
    
    def learn_from_implicit_signals(self, signals: dict):
        """Learn from implicit user signals (engagement, pauses, topic changes)"""
        # Extract learning signals
        engagement_level = signals.get('engagement', 0.5)
        response_time = signals.get('response_time_seconds', 5.0)
        topic_switch = signals.get('topic_switched', False)
        
        # Update theories based on signals
        for theory in self.theories.values():
            if theory.category == 'engagement':
                # Test engagement-related theories
                outcome = engagement_level > 0.6
                theory.test(outcome, weight=0.5)
        
        # Generate new theories from patterns in signals
        if topic_switch and response_time < 2:
            # Fast topic switch might indicate disinterest
            new_theory = self.generate_theory_from_pattern({
                'pattern_type': 'disengage_quickly',
                'context': 'certain topics',
                'category': 'engagement'
            })
    
    def get_learning_status(self) -> dict:
        """Get current state of learning system"""
        return {
            'total_theories': len(self.theories),
            'strong_theories': len([t for t in self.theories.values() if t.strength > 0.7]),
            'weak_theories': len([t for t in self.theories.values() if t.strength < 0.3]),
            'total_predictions': len(self.prediction_history),
            'theories_by_category': self._count_theories_by_category(),
            'recent_theories': [t.to_dict() for t in sorted(self.theories.values(), key=lambda x: x.created_at, reverse=True)[:5]]
        }
    
    def _count_theories_by_category(self) -> dict:
        counts = {}
        for theory in self.theories.values():
            counts[theory.category] = counts.get(theory.category, 0) + 1
        return counts
