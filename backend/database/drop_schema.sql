-- =====================================================
-- 智能学习助手Agent系统 - 数据库清理脚本
-- 用途: 删除所有表、函数、扩展,用于重新初始化数据库
-- 警告: 此操作将删除所有数据,请谨慎使用!
-- =====================================================

-- 删除所有触发器
DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants CASCADE;
DROP TRIGGER IF EXISTS update_tenant_configurations_updated_at ON tenant_configurations CASCADE;
DROP TRIGGER IF EXISTS update_teaching_mode_configs_updated_at ON teaching_mode_configs CASCADE;
DROP TRIGGER IF EXISTS update_learners_updated_at ON learners CASCADE;
DROP TRIGGER IF EXISTS update_learning_goals_updated_at ON learning_goals CASCADE;
DROP TRIGGER IF EXISTS update_domain_teaching_strategies_updated_at ON domain_teaching_strategies CASCADE;
DROP TRIGGER IF EXISTS update_concepts_updated_at ON concepts CASCADE;
DROP TRIGGER IF EXISTS update_topic_mastery_updated_at ON topic_mastery CASCADE;
DROP TRIGGER IF EXISTS update_knowledge_gaps_updated_at ON knowledge_gaps CASCADE;
DROP TRIGGER IF EXISTS update_verified_content_updated_at ON verified_content CASCADE;

-- 删除函数
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- 删除所有表(按依赖关系逆序删除)
DROP TABLE IF EXISTS mnemonic_devices CASCADE;
DROP TABLE IF EXISTS content_source_mapping CASCADE;
DROP TABLE IF EXISTS verified_content CASCADE;
DROP TABLE IF EXISTS authority_sources CASCADE;
DROP TABLE IF EXISTS knowledge_gaps CASCADE;
DROP TABLE IF EXISTS topic_mastery CASCADE;
DROP TABLE IF EXISTS comprehension_checks CASCADE;
DROP TABLE IF EXISTS explanations CASCADE;
DROP TABLE IF EXISTS questions_asked CASCADE;
DROP TABLE IF EXISTS learning_sessions CASCADE;
DROP TABLE IF EXISTS topic_dependencies CASCADE;
DROP TABLE IF EXISTS concepts CASCADE;
DROP TABLE IF EXISTS topics CASCADE;
DROP TABLE IF EXISTS domain_teaching_strategies CASCADE;
DROP TABLE IF EXISTS knowledge_domains CASCADE;
DROP TABLE IF EXISTS learning_goals CASCADE;
DROP TABLE IF EXISTS learners CASCADE;
DROP TABLE IF EXISTS teaching_mode_configs CASCADE;
DROP TABLE IF EXISTS teaching_modes CASCADE;
DROP TABLE IF EXISTS tenant_users CASCADE;
DROP TABLE IF EXISTS tenant_configurations CASCADE;
DROP TABLE IF EXISTS tenants CASCADE;

-- 注意: 不删除扩展,因为可能被其他数据库对象使用
-- 如果需要完全清理,请手动执行:
-- DROP EXTENSION IF EXISTS vector CASCADE;
-- DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE;

-- =====================================================
-- 清理完成
-- =====================================================
