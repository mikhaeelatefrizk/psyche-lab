"""Memory System - Hierarchical memory with abstraction layers"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json


class MemoryEntry:
    """Represents a single memory entry"""
    
    def __init__(self, entry_id: str, content: dict, memory_type: str, abstraction_level: int = 0):
        self.id = entry_id
        self.content = content
        self.memory_type = memory_type  # 'raw', 'pattern', 'belief', 'theory'
        self.abstraction_level = abstraction_level  # 0=raw, 1=summarized, 2=patterns, 3=beliefs
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.access_count = 0
        self.importance = 0.5
        self.related_memories: List[str] = []
        
    def access(self):
        """Mark memory as accessed"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type,
            'abstraction_level': self.abstraction_level,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'importance': self.importance,
            'related_memories': self.related_memories
        }


class MemorySystem:
    """Hierarchical memory system with automatic abstraction"""
    
    def __init__(self, db_client):
        self.db = db_client
        self.short_term_memory: Dict[str, MemoryEntry] = {}  # Recent, raw memories
        self.working_memory: Dict[str, MemoryEntry] = {}  # Currently active patterns
        self.abstraction_thresholds = {
            'raw_to_pattern': 5,  # 5 related raw memories → pattern
            'pattern_to_belief': 10,  # 10 consistent patterns → belief
            'belief_to_theory': 20  # 20 reinforced beliefs → theory
        }
        self._load_recent_memories()
    
    def _load_recent_memories(self, days: int = 7):
        """Load recent memories from database into working memory"""
        try:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            result = self.db.table('memories').select('*').gte('created_at', cutoff).order('created_at', desc=True).limit(100).execute()
            
            for mem_data in result.data:
                entry = MemoryEntry(
                    entry_id=mem_data['id'],
                    content=mem_data['content'],
                    memory_type=mem_data['memory_type'],
                    abstraction_level=mem_data.get('abstraction_level', 0)
                )
                entry.importance = mem_data.get('importance', 0.5)
                entry.access_count = mem_data.get('access_count', 0)
                
                if entry.abstraction_level == 0:
                    self.short_term_memory[entry.id] = entry
                else:
                    self.working_memory[entry.id] = entry
        except Exception as e:
            print(f"Error loading memories: {e}")
    
    def store_raw_memory(self, content: dict, memory_type: str = 'interaction') -> MemoryEntry:
        """Store a new raw memory"""
        import uuid
        entry_id = str(uuid.uuid4())
        
        entry = MemoryEntry(
            entry_id=entry_id,
            content=content,
            memory_type=memory_type,
            abstraction_level=0
        )
        
        self.short_term_memory[entry_id] = entry
        
        # Persist to database
        try:
            self.db.table('memories').insert({
                'id': entry_id,
                'content': content,
                'memory_type': memory_type,
                'abstraction_level': 0,
                'created_at': entry.created_at.isoformat(),
                'importance': entry.importance,
                'access_count': 0
            }).execute()
        except Exception as e:
            print(f"Error storing memory: {e}")
        
        # Trigger abstraction check
        self._check_abstraction_opportunities()
        
        return entry
    
    def retrieve_memories(self, query: dict, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve relevant memories based on query"""
        # Simple retrieval - in production would use vector similarity
        relevant = []
        
        # Search in working memory first (higher abstraction)
        for memory in self.working_memory.values():
            memory.access()
            relevant.append(memory)
            if len(relevant) >= limit:
                break
        
        # Then short-term if needed
        if len(relevant) < limit:
            for memory in list(self.short_term_memory.values())[:limit-len(relevant)]:
                memory.access()
                relevant.append(memory)
        
        return relevant
    
    def _check_abstraction_opportunities(self):
        """Check if raw memories can be abstracted into patterns/beliefs/theories"""
        # Count similar memories
        if len(self.short_term_memory) >= self.abstraction_thresholds['raw_to_pattern']:
            self._abstract_to_pattern()
        
        if len([m for m in self.working_memory.values() if m.abstraction_level == 1]) >= 5:
            self._abstract_to_belief()
    
    def _abstract_to_pattern(self):
        """Abstract multiple raw memories into a pattern"""
        import uuid
        
        # Take oldest raw memories and create a pattern
        raw_memories = sorted(
            self.short_term_memory.values(),
            key=lambda m: m.created_at
        )[:self.abstraction_thresholds['raw_to_pattern']]
        
        # Create pattern memory
        pattern_content = {
            'pattern_type': 'behavioral',
            'summary': 'Detected pattern from user interactions',
            'source_memories': [m.id for m in raw_memories],
            'occurrences': len(raw_memories)
        }
        
        pattern_id = str(uuid.uuid4())
        pattern = MemoryEntry(
            entry_id=pattern_id,
            content=pattern_content,
            memory_type='pattern',
            abstraction_level=1
        )
        pattern.importance = 0.7  # Patterns are more important
        
        self.working_memory[pattern_id] = pattern
        
        # Store pattern in database
        try:
            self.db.table('memories').insert({
                'id': pattern_id,
                'content': pattern_content,
                'memory_type': 'pattern',
                'abstraction_level': 1,
                'created_at': pattern.created_at.isoformat(),
                'importance': pattern.importance,
                'access_count': 0
            }).execute()
        except Exception as e:
            print(f"Error storing pattern: {e}")
        
        # Mark raw memories as abstracted (keep them but lower importance)
        for raw_mem in raw_memories:
            raw_mem.importance *= 0.5
            if raw_mem.id in self.short_term_memory:
                del self.short_term_memory[raw_mem.id]
    
    def _abstract_to_belief(self):
        """Abstract patterns into beliefs about the user"""
        import uuid
        
        patterns = [m for m in self.working_memory.values() if m.abstraction_level == 1]
        
        if len(patterns) >= 5:
            belief_content = {
                'belief_type': 'user_tendency',
                'description': 'Extracted belief from consistent patterns',
                'confidence': 0.6,
                'source_patterns': [p.id for p in patterns[:5]]
            }
            
            belief_id = str(uuid.uuid4())
            belief = MemoryEntry(
                entry_id=belief_id,
                content=belief_content,
                memory_type='belief',
                abstraction_level=2
            )
            belief.importance = 0.85
            
            self.working_memory[belief_id] = belief
            
            try:
                self.db.table('memories').insert({
                    'id': belief_id,
                    'content': belief_content,
                    'memory_type': 'belief',
                    'abstraction_level': 2,
                    'created_at': belief.created_at.isoformat(),
                    'importance': belief.importance,
                    'access_count': 0
                }).execute()
            except Exception as e:
                print(f"Error storing belief: {e}")
    
    def get_memory_hierarchy(self) -> dict:
        """Get overview of memory system state"""
        return {
            'short_term_count': len(self.short_term_memory),
            'working_memory_count': len(self.working_memory),
            'abstraction_levels': {
                'raw': len([m for m in self.short_term_memory.values() if m.abstraction_level == 0]),
                'patterns': len([m for m in self.working_memory.values() if m.abstraction_level == 1]),
                'beliefs': len([m for m in self.working_memory.values() if m.abstraction_level == 2]),
                'theories': len([m for m in self.working_memory.values() if m.abstraction_level == 3])
            }
        }
    
    def consolidate_memories(self):
        """Periodic consolidation: move important memories to long-term, forget unimportant ones"""
        # Remove low-importance, rarely accessed memories from short-term
        to_remove = []
        for mem_id, memory in self.short_term_memory.items():
            days_old = (datetime.utcnow() - memory.created_at).days
            if days_old > 7 and memory.importance < 0.3 and memory.access_count < 2:
                to_remove.append(mem_id)
        
        for mem_id in to_remove:
            del self.short_term_memory[mem_id]
        
        return len(to_remove)
