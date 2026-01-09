-- Psyche-Lab Database Schema for Supabase
-- Complete autonomous AI laboratory system

-- ============================================
-- TABLE: brains
-- Stores all specialized AI brain instances
-- ============================================
CREATE TABLE IF NOT EXISTS brains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT NOT NULL,
    creation_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    config JSONB DEFAULT '{}',
    strength FLOAT DEFAULT 0.5,
    active BOOLEAN DEFAULT TRUE,
    analysis_count INT DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    termination_reason TEXT,
    termination_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for active brains
CREATE INDEX IF NOT EXISTS idx_brains_active ON brains(active);
CREATE INDEX IF NOT EXISTS idx_brains_role ON brains(role);

-- ============================================
-- TABLE: memories
-- Hierarchical memory storage system
-- ============================================
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content JSONB NOT NULL,
    memory_type TEXT NOT NULL, -- 'raw', 'pattern', 'belief', 'theory', 'user_input', 'interaction'
    abstraction_level INT DEFAULT 0, -- 0=raw, 1=pattern, 2=belief, 3=theory
    importance FLOAT DEFAULT 0.5,
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    related_memories UUID[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient memory retrieval
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_abstraction ON memories(abstraction_level);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);

-- ============================================
-- TABLE: theories
-- User theories and hypotheses tracking
-- ============================================
CREATE TABLE IF NOT EXISTS theories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hypothesis TEXT NOT NULL,
    category TEXT NOT NULL, -- 'behavior', 'preference', 'tendency', 'trait', 'engagement'
    strength FLOAT DEFAULT 0.5,
    evidence_for INT DEFAULT 0,
    evidence_against INT DEFAULT 0,
    tests_performed INT DEFAULT 0,
    last_tested TIMESTAMPTZ,
    competing_theories UUID[],
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for theory queries
CREATE INDEX IF NOT EXISTS idx_theories_active ON theories(active);
CREATE INDEX IF NOT EXISTS idx_theories_category ON theories(category);
CREATE INDEX IF NOT EXISTS idx_theories_strength ON theories(strength DESC);

-- ============================================
-- TABLE: messages (legacy/compatibility)
-- Original message storage for history
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at DESC);

-- ============================================
-- TABLE: system_logs (optional but recommended)
-- Track system evolution and adaptations
-- ============================================
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL, -- 'brain_created', 'brain_terminated', 'brain_merged', 'theory_generated', 'adaptation'
    event_data JSONB NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_system_logs_type ON system_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp DESC);

-- ============================================
-- FUNCTIONS: Automatic timestamp updates
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Attach update triggers
CREATE TRIGGER update_brains_updated_at BEFORE UPDATE ON brains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_theories_updated_at BEFORE UPDATE ON theories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Row Level Security (RLS) - Optional
-- Enable if you want user-specific data isolation
-- ============================================
-- ALTER TABLE brains ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE theories ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Example policy (modify based on your auth setup):
-- CREATE POLICY "Allow all operations for authenticated users" ON brains
--     FOR ALL USING (auth.role() = 'authenticated');

-- ============================================
-- NOTES FOR SETUP:
-- ============================================
-- 1. Run this script in your Supabase SQL Editor
-- 2. The script is idempotent (safe to run multiple times)
-- 3. All tables use UUID primary keys for scalability
-- 4. JSONB columns allow flexible schema evolution
-- 5. Indexes optimized for common query patterns
-- 6. Timestamps automatically managed
--
-- After running this:
-- 1. Get your Supabase URL from Project Settings > API
-- 2. Get your Supabase anon/public key from Project Settings > API
-- 3. Add these to your Render environment variables:
--    - SUPABASE_URL=your_project_url
--    - SUPABASE_KEY=your_anon_key
-- ============================================
