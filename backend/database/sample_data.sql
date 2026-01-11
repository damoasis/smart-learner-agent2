-- =====================================================
-- 智能学习助手Agent系统 - 样例数据初始化
-- 描述: CFP税务规划领域的样例数据
-- =====================================================

-- =====================================================
-- 第一部分: 创建默认租户
-- =====================================================

-- 插入演示租户
INSERT INTO tenants (tenant_id, tenant_name, subscription_plan, status, max_learners, max_domains, allowed_teaching_modes, settings) VALUES
('00000000-0000-0000-0000-000000000001', 'Demo Organization', 'premium', 'active', 100, 20, 
 ARRAY['socratic', 'lecture', 'case_based', 'inquiry', 'demonstration'], 
 '{"branding": {"logo_url": "", "primary_color": "#4F46E5"}, "features": {"ai_tutoring": true, "progress_tracking": true}}'::jsonb);

-- 为演示租户配置教学模式
INSERT INTO teaching_mode_configs (tenant_id, mode_id, enabled, priority, custom_parameters)
SELECT 
    '00000000-0000-0000-0000-000000000001'::uuid,
    mode_id,
    TRUE,
    CASE mode_name
        WHEN 'socratic' THEN 5
        WHEN 'lecture' THEN 4
        WHEN 'case_based' THEN 3
        WHEN 'inquiry' THEN 2
        WHEN 'demonstration' THEN 1
    END,
    '{}'::jsonb
FROM teaching_modes
WHERE is_system_mode = TRUE;

-- =====================================================
-- 第二部分: 创建演示学习者
-- =====================================================

INSERT INTO learners (learner_id, tenant_id, name, email, native_language, learning_preferences) VALUES
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 
 'Demo Learner', 'demo@example.com', 'zh', 
 '{"learning_style": "visual", "preferred_session_duration": 30, "difficulty_preference": "adaptive"}'::jsonb);

-- 创建学习目标: CFP考试备考
INSERT INTO learning_goals (goal_id, tenant_id, learner_id, goal_type, goal_name, target_date, status, goal_metadata) VALUES
('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001',
 '10000000-0000-0000-0000-000000000001', 'exam', 'CFP Certification Exam', '2026-06-01', 'active',
 '{"exam_type": "cfp", "total_topics": 73, "study_hours_per_week": 10}'::jsonb);

-- =====================================================
-- 第三部分: 创建知识领域 - 税务规划
-- =====================================================

INSERT INTO knowledge_domains (domain_id, tenant_id, goal_id, domain_code, domain_name, weight_percentage, total_topics, recommended_teaching_mode) 
SELECT 
    '30000000-0000-0000-0000-000000000001'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    '20000000-0000-0000-0000-000000000001'::uuid,
    'D',
    '税务规划 (Tax Planning)',
    18.00,
    14,
    mode_id
FROM teaching_modes WHERE mode_name = 'case_based' LIMIT 1;

-- 为税务规划领域配置教学策略
INSERT INTO domain_teaching_strategies (tenant_id, domain_id, primary_mode_id, fallback_mode_ids, switching_rules)
SELECT 
    '00000000-0000-0000-0000-000000000001'::uuid,
    '30000000-0000-0000-0000-000000000001'::uuid,
    (SELECT mode_id FROM teaching_modes WHERE mode_name = 'case_based'),
    ARRAY[(SELECT mode_id FROM teaching_modes WHERE mode_name = 'lecture'), 
          (SELECT mode_id FROM teaching_modes WHERE mode_name = 'socratic')],
    '{"consecutive_failures_threshold": 3, "auto_switch_enabled": true, "low_engagement_threshold": 0.3}'::jsonb;

-- =====================================================
-- 第四部分: 创建税务规划主题
-- =====================================================

-- 主题1: 个人所得税基础
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('40000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000001', 'D.1', '个人所得税基础',
 '理解美国个人所得税制度的基本原理,包括应税收入、免税收入、扣除项目等', 'medium', 45);

-- 主题2: 退休账户税务规则
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('40000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000001', 'D.2', '退休账户税务规则',
 '掌握401(k)、IRA、Roth IRA等退休账户的税务处理规则,包括缴款限额、提款规则、税收优惠等', 'hard', 60);

-- 主题3: 资本利得与亏损
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('40000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000001', 'D.3', '资本利得与亏损',
 '理解资本资产的定义、长期与短期资本利得的税率、资本亏损的抵扣规则', 'medium', 50);

-- 主题4: 税收抵免与扣除
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('40000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000001', 'D.4', '税收抵免与扣除',
 '区分税收抵免(Tax Credits)和税收扣除(Deductions),掌握常见的教育抵免、儿童抵免等', 'easy', 40);

-- 主题5: 遗产与赠与税
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('40000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000001', 'D.5', '遗产与赠与税',
 '理解遗产税和赠与税的征收规则、豁免额度、税率结构', 'hard', 55);

-- =====================================================
-- 第五部分: 创建概念和知识点
-- =====================================================

-- 主题D.2的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules, common_pitfalls) VALUES
('50000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000002',
 '401(k)缴款限额', 
 '2024年401(k)计划的选择性延期缴款(elective deferral)限额为$23,000。年满50岁的参与者可额外缴纳$7,500的追赶缴款(catch-up contribution)。',
 ARRAY['2024年限额 = $23,000', '追赶缴款(50+) = $7,500', '总限额(50+) = $30,500'],
 ARRAY['限额每年由IRS调整', '雇主匹配不计入此限额', 'Roth 401(k)和传统401(k)共享此限额'],
 ARRAY['混淆员工缴款限额和总缴款限额', '忘记追赶缴款只适用于50岁及以上', '误以为雇主匹配占用员工限额']),

('50000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000002',
 'IRA缴款限额', 
 '2024年IRA(传统和Roth)的年度缴款限额为$7,000。年满50岁者可额外缴纳$1,000追赶缴款。',
 ARRAY['2024年限额 = $7,000', '追赶缴款(50+) = $1,000', '总限额(50+) = $8,000'],
 ARRAY['传统IRA和Roth IRA共享此限额', '必须有earned income才能缴款', '配偶IRA允许非工作配偶缴款'],
 ARRAY['混淆IRA和401(k)的限额', '忘记Roth和传统IRA限额是合并计算', '忽略收入限制条件']),

('50000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000002',
 'Required Minimum Distribution (RMD)', 
 '从传统IRA和401(k)账户必须在72岁(或73岁,根据出生年份)开始提取最低要求分配。RMD金额基于账户余额和IRS寿命表计算。',
 ARRAY['RMD = 账户余额 / 分配期(Distribution Period)', '分配期从IRS Uniform Lifetime Table查询'],
 ARRAY['Roth IRA在所有者生前无RMD要求', '未按时提取RMD将面临50%罚款', '每年12月31日前必须完成提取'],
 ARRAY['忘记Roth IRA无RMD', '延迟首次RMD可能导致双重征税', '误用错误的寿命表']);

-- 主题D.4的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules) VALUES
('50000000-0000-0000-0000-000000000004', '40000000-0000-0000-0000-000000000004',
 'American Opportunity Tax Credit (AOTC)', 
 '美国机会税收抵免为符合条件的教育支出提供最高$2,500的抵免。适用于前四年的高等教育。',
 ARRAY['最高抵免 = $2,500', '100%抵免前$2,000支出 + 25%抵免后$2,000支出'],
 ARRAY['仅适用于前4年大学教育', '学生必须至少半日制入学', 'MAGI超过限额会减少抵免额', '40%可退还']);

-- =====================================================
-- 第六部分: 创建主题依赖关系
-- =====================================================

-- D.1是D.2的前置知识
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('40000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000002', 'recommended', 0.70);

-- D.1是D.3的前置知识
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('40000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000003', 'recommended', 0.60);

-- D.1是D.4的相关知识
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('40000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000004', 'related', 0.50);

-- =====================================================
-- 第七部分: 创建权威来源
-- =====================================================

INSERT INTO authority_sources (source_name, source_url, domain_relevance, trust_score) VALUES
('IRS Official Website', 'https://www.irs.gov', 'tax', 1.00),
('IRS Publication 590-A', 'https://www.irs.gov/pub/irs-pdf/p590a.pdf', 'retirement_accounts', 1.00),
('IRS Publication 590-B', 'https://www.irs.gov/pub/irs-pdf/p590b.pdf', 'retirement_distributions', 1.00),
('IRS Publication 970', 'https://www.irs.gov/pub/irs-pdf/p970.pdf', 'education_tax_benefits', 1.00),
('CFP Board Official Site', 'https://www.cfp.net', 'cfp_exam', 0.95),
('Social Security Administration', 'https://www.ssa.gov', 'social_security', 1.00);

-- =====================================================
-- 第八部分: 创建验证内容示例
-- =====================================================

INSERT INTO verified_content (content_id, concept_id, content_type, content_text, verification_date, confidence_score, needs_reverification_after, metadata) VALUES
('60000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'fact',
 '2024年401(k)选择性延期缴款限额为$23,000,50岁及以上追赶缴款为$7,500', 
 '2024-01-15', 1.00, '2025-01-01',
 '{"tax_year": 2024, "source_publication": "IRS Notice 2023-75"}'::jsonb),

('60000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', 'fact',
 '2024年IRA年度缴款限额为$7,000,50岁及以上追赶缴款为$1,000', 
 '2024-01-15', 1.00, '2025-01-01',
 '{"tax_year": 2024, "source_publication": "IRS Publication 590-A"}'::jsonb);

-- 关联验证内容与权威来源
INSERT INTO content_source_mapping (content_id, source_id, citation_text) 
SELECT 
    '60000000-0000-0000-0000-000000000001'::uuid,
    source_id,
    'IRS Notice 2023-75: 2024 Limitations Adjusted as Provided in Section 415(d)'
FROM authority_sources WHERE source_name = 'IRS Official Website';

-- =====================================================
-- 第九部分: 创建记忆辅助示例
-- =====================================================

-- 记忆辅助: 退休账户缴款限额
INSERT INTO mnemonic_devices (topic_id, mnemonic_type, content, effectiveness_rating, is_language_independent) VALUES
('40000000-0000-0000-0000-000000000002', 'acronym',
 '{"title": "2024退休账户限额记忆法", "acronym": "23-7 vs 7-1", 
   "explanation": "401(k): $23,000 + $7,000追赶 | IRA: $7,000 + $1,000追赶", 
   "visual": "大账户(401k)限额更大,小账户(IRA)限额更小"}'::jsonb,
 0.85, TRUE);

-- 记忆辅助: AOTC vs LLC对比
INSERT INTO mnemonic_devices (topic_id, mnemonic_type, content, effectiveness_rating, is_language_independent) VALUES
('40000000-0000-0000-0000-000000000004', 'comparison_table',
 '{"title": "AOTC vs LLC教育税收抵免对比", 
   "table": {
     "headers": ["项目", "AOTC", "LLC"],
     "rows": [
       ["最高抵免额", "$2,500", "$2,000"],
       ["适用年限", "前4年", "无限制"],
       ["可退还", "40%", "0%"],
       ["学习要求", "至少半日制", "无要求"]
     ]
   }}'::jsonb,
 0.90, TRUE);

-- =====================================================
-- 样例数据初始化完成
-- =====================================================

-- 验证数据
SELECT 
    t.tenant_name,
    COUNT(DISTINCT l.learner_id) as total_learners,
    COUNT(DISTINCT lg.goal_id) as total_goals,
    COUNT(DISTINCT kd.domain_id) as total_domains,
    COUNT(DISTINCT tp.topic_id) as total_topics,
    COUNT(DISTINCT c.concept_id) as total_concepts
FROM tenants t
LEFT JOIN learners l ON t.tenant_id = l.tenant_id
LEFT JOIN learning_goals lg ON l.learner_id = lg.learner_id
LEFT JOIN knowledge_domains kd ON lg.goal_id = kd.goal_id
LEFT JOIN topics tp ON kd.domain_id = tp.domain_id
LEFT JOIN concepts c ON tp.topic_id = c.topic_id
WHERE t.tenant_id = '00000000-0000-0000-0000-000000000001'
GROUP BY t.tenant_name;
