-- =====================================================
-- 智能学习助手Agent系统 - PostgreSQL数据库Schema
-- 版本: 1.0
-- 创建日期: 2026-01-07
-- 描述: 支持多租户、多教学模式的通用学习助手系统
-- =====================================================

-- 启用pgvector扩展(用于向量语义搜索)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 第一部分: 租户管理表
-- =====================================================

-- 租户主表
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_name VARCHAR(255) NOT NULL,
    subscription_plan VARCHAR(50) CHECK (subscription_plan IN ('free', 'basic', 'premium', 'enterprise')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'inactive')),
    max_learners INTEGER DEFAULT 10,
    max_domains INTEGER DEFAULT 5,
    allowed_teaching_modes VARCHAR(100)[] DEFAULT ARRAY['socratic'],
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 租户配置表
CREATE TABLE tenant_configurations (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value JSONB NOT NULL,
    config_type VARCHAR(50) CHECK (config_type IN ('teaching_mode', 'branding', 'feature', 'limit')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, config_key)
);

-- 租户用户关联表
CREATE TABLE tenant_users (
    mapping_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(50) CHECK (role IN ('admin', 'instructor', 'learner')) DEFAULT 'learner',
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, user_id)
);

-- =====================================================
-- 第二部分: 教学模式管理表
-- =====================================================

-- 教学模式定义表
CREATE TABLE teaching_modes (
    mode_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mode_name VARCHAR(100) NOT NULL UNIQUE,
    mode_type VARCHAR(50) CHECK (mode_type IN ('interactive', 'passive', 'hybrid')),
    description TEXT,
    applicable_scenarios TEXT[],
    default_parameters JSONB DEFAULT '{}',
    is_system_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 租户教学模式配置表
CREATE TABLE teaching_mode_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    mode_id UUID REFERENCES teaching_modes(mode_id) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    custom_parameters JSONB DEFAULT '{}',
    domain_mapping JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, mode_id)
);

-- =====================================================
-- 第三部分: 用户与学习目标表
-- =====================================================

-- 学习者表
CREATE TABLE learners (
    learner_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    native_language VARCHAR(50) DEFAULT 'en',
    learning_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, email)
);

-- 学习目标表
CREATE TABLE learning_goals (
    goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    learner_id UUID REFERENCES learners(learner_id) ON DELETE CASCADE NOT NULL,
    goal_type VARCHAR(50) DEFAULT 'exam',
    goal_name VARCHAR(255) NOT NULL,
    target_date DATE,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
    preferred_teaching_mode UUID REFERENCES teaching_modes(mode_id),
    goal_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 第四部分: 知识结构表
-- =====================================================

-- 知识领域表
CREATE TABLE knowledge_domains (
    domain_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    goal_id UUID REFERENCES learning_goals(goal_id) ON DELETE CASCADE NOT NULL,
    domain_code VARCHAR(20),
    domain_name VARCHAR(255) NOT NULL,
    weight_percentage DECIMAL(5,2),
    total_topics INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed')),
    recommended_teaching_mode UUID REFERENCES teaching_modes(mode_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 领域教学策略表
CREATE TABLE domain_teaching_strategies (
    strategy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    domain_id UUID REFERENCES knowledge_domains(domain_id) ON DELETE CASCADE NOT NULL,
    primary_mode_id UUID REFERENCES teaching_modes(mode_id) NOT NULL,
    fallback_mode_ids UUID[],
    switching_rules JSONB DEFAULT '{}',
    effectiveness_score DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, domain_id)
);

-- 主题表
CREATE TABLE topics (
    topic_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    domain_id UUID REFERENCES knowledge_domains(domain_id) ON DELETE CASCADE NOT NULL,
    topic_code VARCHAR(20),
    topic_name VARCHAR(255) NOT NULL,
    description TEXT,
    reference_materials JSONB DEFAULT '{}',
    estimated_learning_time_minutes INTEGER,
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
    recommended_teaching_mode UUID REFERENCES teaching_modes(mode_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 概念表
CREATE TABLE concepts (
    concept_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topics(topic_id) ON DELETE CASCADE NOT NULL,
    concept_name VARCHAR(255) NOT NULL,
    explanation TEXT,
    formulas TEXT[],
    rules TEXT[],
    common_pitfalls TEXT[],
    exam_tips TEXT[],
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 主题依赖关系表
CREATE TABLE topic_dependencies (
    dependency_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prerequisite_topic_id UUID REFERENCES topics(topic_id) ON DELETE CASCADE NOT NULL,
    dependent_topic_id UUID REFERENCES topics(topic_id) ON DELETE CASCADE NOT NULL,
    dependency_type VARCHAR(50) CHECK (dependency_type IN ('required', 'recommended', 'related')),
    strength DECIMAL(3,2) DEFAULT 0.50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (prerequisite_topic_id != dependent_topic_id)
);

-- =====================================================
-- 第五部分: 学习追踪表
-- =====================================================

-- 学习会话表
CREATE TABLE learning_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    learner_id UUID REFERENCES learners(learner_id) ON DELETE CASCADE NOT NULL,
    goal_id UUID REFERENCES learning_goals(goal_id) ON DELETE CASCADE NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    session_format VARCHAR(50) CHECK (session_format IN ('teaching', 'practice', 'review')),
    teaching_mode_used UUID REFERENCES teaching_modes(mode_id),
    teaching_mode_switches JSONB[] DEFAULT ARRAY[]::JSONB[],
    session_notes TEXT,
    topics_covered UUID[],
    performance_summary JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 提问记录表
CREATE TABLE questions_asked (
    question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES learning_sessions(session_id) ON DELETE CASCADE NOT NULL,
    topic_id UUID REFERENCES topics(topic_id),
    question_text TEXT NOT NULL,
    initial_understanding TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 解释记录表
CREATE TABLE explanations (
    explanation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions_asked(question_id) ON DELETE CASCADE NOT NULL,
    agent_explanation TEXT NOT NULL,
    teaching_method_used VARCHAR(100),
    teaching_agent_type VARCHAR(50),
    sources_cited JSONB DEFAULT '{}',
    explanation_length_words INTEGER,
    clarity_rating DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 理解检查表
CREATE TABLE comprehension_checks (
    check_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    explanation_id UUID REFERENCES explanations(explanation_id) ON DELETE CASCADE NOT NULL,
    question_asked TEXT NOT NULL,
    learner_response TEXT,
    is_correct BOOLEAN,
    assessment_result VARCHAR(50) CHECK (assessment_result IN ('fully_understood', 'partially_understood', 'not_understood')),
    follow_up_needed BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 主题掌握表
CREATE TABLE topic_mastery (
    mastery_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    learner_id UUID REFERENCES learners(learner_id) ON DELETE CASCADE NOT NULL,
    topic_id UUID REFERENCES topics(topic_id) ON DELETE CASCADE NOT NULL,
    mastery_date DATE DEFAULT CURRENT_DATE,
    confidence_level VARCHAR(50) CHECK (confidence_level IN ('high', 'medium_high', 'medium', 'low')),
    key_points_understood TEXT[],
    supporting_session_ids UUID[],
    last_reviewed TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    teaching_modes_used UUID[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, learner_id, topic_id)
);

-- 知识缺口表
CREATE TABLE knowledge_gaps (
    gap_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE NOT NULL,
    learner_id UUID REFERENCES learners(learner_id) ON DELETE CASCADE NOT NULL,
    topic_id UUID REFERENCES topics(topic_id) ON DELETE CASCADE NOT NULL,
    severity_level VARCHAR(50) CHECK (severity_level IN ('high', 'medium', 'low')),
    gap_description TEXT,
    identified_date DATE DEFAULT CURRENT_DATE,
    resolution_date DATE,
    resolution_notes TEXT,
    related_session_ids UUID[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 第六部分: 内容验证与记忆辅助表
-- =====================================================

-- 权威来源表
CREATE TABLE authority_sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(255) NOT NULL,
    source_url TEXT,
    domain_relevance VARCHAR(100),
    trust_score DECIMAL(3,2) DEFAULT 0.80,
    last_verified DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 已验证内容表
CREATE TABLE verified_content (
    content_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept_id UUID REFERENCES concepts(concept_id) ON DELETE CASCADE,
    content_type VARCHAR(50) CHECK (content_type IN ('rule', 'formula', 'fact', 'procedure')),
    content_text TEXT NOT NULL,
    verification_date DATE DEFAULT CURRENT_DATE,
    confidence_score DECIMAL(3,2) DEFAULT 0.90,
    needs_reverification_after DATE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 内容来源映射表
CREATE TABLE content_source_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES verified_content(content_id) ON DELETE CASCADE NOT NULL,
    source_id UUID REFERENCES authority_sources(source_id) ON DELETE CASCADE NOT NULL,
    citation_text TEXT,
    accessed_date DATE DEFAULT CURRENT_DATE
);

-- 记忆辅助表
CREATE TABLE mnemonic_devices (
    mnemonic_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topics(topic_id) ON DELETE CASCADE NOT NULL,
    mnemonic_type VARCHAR(50) CHECK (mnemonic_type IN ('acronym', 'visual', 'rhyme', 'story', 'comparison_table')),
    content JSONB NOT NULL,
    effectiveness_rating DECIMAL(3,2) DEFAULT 0.00,
    created_for_learner_id UUID REFERENCES learners(learner_id),
    is_language_independent BOOLEAN DEFAULT FALSE,
    applicable_languages VARCHAR(100)[],
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 第七部分: 索引创建
-- =====================================================

-- 租户相关索引
CREATE INDEX idx_tenant_status ON tenants(status);
CREATE INDEX idx_tenant_name ON tenants USING gin(to_tsvector('english', tenant_name));
CREATE INDEX idx_tenant_config ON tenant_configurations(tenant_id, config_key);
CREATE INDEX idx_tenant_user ON tenant_users(tenant_id, user_id);

-- 教学模式索引
CREATE INDEX idx_mode_name ON teaching_modes(mode_name);
CREATE INDEX idx_mode_type ON teaching_modes(mode_type);
CREATE INDEX idx_tenant_mode_config ON teaching_mode_configs(tenant_id, mode_id);
CREATE INDEX idx_domain_strategy ON domain_teaching_strategies(tenant_id, domain_id);

-- 学习者和目标索引
CREATE INDEX idx_tenant_learner ON learners(tenant_id, learner_id);
CREATE INDEX idx_tenant_email ON learners(tenant_id, email);
CREATE INDEX idx_tenant_learner_goal ON learning_goals(tenant_id, learner_id, status);
CREATE INDEX idx_tenant_goal ON learning_goals(tenant_id, goal_id);

-- 知识结构索引
CREATE INDEX idx_tenant_goal_domain ON knowledge_domains(tenant_id, goal_id);
CREATE INDEX idx_tenant_domain ON knowledge_domains(tenant_id, domain_id);
CREATE INDEX idx_tenant_domain_topic ON topics(tenant_id, domain_id);
CREATE INDEX idx_tenant_topic_code ON topics(tenant_id, topic_code);
CREATE INDEX idx_topic_concept ON concepts(topic_id);
CREATE INDEX idx_concept_embedding ON concepts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_prerequisite ON topic_dependencies(prerequisite_topic_id);
CREATE INDEX idx_dependent ON topic_dependencies(dependent_topic_id);

-- 学习追踪索引
CREATE INDEX idx_tenant_learner_session ON learning_sessions(tenant_id, learner_id, start_time DESC);
CREATE INDEX idx_tenant_goal_session ON learning_sessions(tenant_id, goal_id, start_time DESC);
CREATE INDEX idx_teaching_mode_session ON learning_sessions(teaching_mode_used);
CREATE INDEX idx_session_question ON questions_asked(session_id);
CREATE INDEX idx_question_explanation ON explanations(question_id);
CREATE INDEX idx_explanation_check ON comprehension_checks(explanation_id);
CREATE INDEX idx_tenant_learner_mastery ON topic_mastery(tenant_id, learner_id, topic_id);
CREATE INDEX idx_confidence_level ON topic_mastery(learner_id, confidence_level);
CREATE INDEX idx_tenant_learner_gap ON knowledge_gaps(tenant_id, learner_id, severity_level, resolution_date);

-- 内容验证索引
CREATE INDEX idx_domain_source ON authority_sources(domain_relevance, trust_score DESC);
CREATE INDEX idx_concept_content ON verified_content(concept_id);
CREATE INDEX idx_reverification ON verified_content(needs_reverification_after) WHERE needs_reverification_after IS NOT NULL;
CREATE INDEX idx_content_sources ON content_source_mapping(content_id);
CREATE INDEX idx_source_contents ON content_source_mapping(source_id);
CREATE INDEX idx_topic_mnemonic ON mnemonic_devices(topic_id, effectiveness_rating DESC);
CREATE INDEX idx_learner_mnemonic ON mnemonic_devices(created_for_learner_id);

-- =====================================================
-- 第八部分: Row-Level Security (RLS) 配置
-- =====================================================

-- 启用RLS
ALTER TABLE learners ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_sessions ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略 - learners表
CREATE POLICY learner_isolation ON learners
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY learner_isolation_insert ON learners
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- 创建RLS策略 - learning_goals表
CREATE POLICY goal_isolation ON learning_goals
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY goal_isolation_insert ON learning_goals
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- 创建RLS策略 - knowledge_domains表
CREATE POLICY domain_isolation ON knowledge_domains
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY domain_isolation_insert ON knowledge_domains
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- 创建RLS策略 - topics表
CREATE POLICY topic_isolation ON topics
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY topic_isolation_insert ON topics
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- 创建RLS策略 - learning_sessions表
CREATE POLICY session_isolation ON learning_sessions
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY session_isolation_insert ON learning_sessions
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- =====================================================
-- 第九部分: 触发器和函数
-- =====================================================

-- 自动更新updated_at字段的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要自动更新时间戳的表添加触发器
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_configurations_updated_at BEFORE UPDATE ON tenant_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teaching_mode_configs_updated_at BEFORE UPDATE ON teaching_mode_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learners_updated_at BEFORE UPDATE ON learners
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_goals_updated_at BEFORE UPDATE ON learning_goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_domain_teaching_strategies_updated_at BEFORE UPDATE ON domain_teaching_strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concepts_updated_at BEFORE UPDATE ON concepts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_topic_mastery_updated_at BEFORE UPDATE ON topic_mastery
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_gaps_updated_at BEFORE UPDATE ON knowledge_gaps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_verified_content_updated_at BEFORE UPDATE ON verified_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 第十部分: 初始化系统教学模式数据
-- =====================================================

-- 插入5种系统内置教学模式
INSERT INTO teaching_modes (mode_name, mode_type, description, applicable_scenarios, is_system_mode) VALUES
('socratic', 'interactive', '苏格拉底式教学:通过提问引导学习者自己发现答案,强调批判性思维和深度理解', 
 ARRAY['概念理解', '批判性思维', '深度探索', '哲学讨论', '法律推理'], TRUE),

('lecture', 'passive', '讲授式教学:系统化讲解知识,结构化呈现内容,适合新知识导入和理论基础建立', 
 ARRAY['新知识导入', '理论基础', '系统性学习', '数学公式', '历史事件'], TRUE),

('case_based', 'hybrid', '案例教学:通过真实案例情境引导学习,强调实践应用和问题解决能力', 
 ARRAY['实践应用', '问题解决', '商业分析', '医学诊断', '法律案例'], TRUE),

('inquiry', 'interactive', '探究式教学:学习者主导探索,通过实验和发现学习,培养自主学习和创新能力', 
 ARRAY['科学实验', '项目学习', '创新思维', '研究方法', '自主学习'], TRUE),

('demonstration', 'passive', '演示教学:步骤化演示操作过程,适合技能学习和工具使用培训', 
 ARRAY['技能学习', '工具使用', '编程操作', '软件教学', '实验步骤'], TRUE);