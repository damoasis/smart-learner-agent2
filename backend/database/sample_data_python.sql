-- =====================================================
-- 智能学习助手Agent系统 - Python编程领域样例数据
-- 描述: Python编程基础知识领域的完整样例数据
-- 领域: Python编程基础
-- 主题数: 7个
-- 概念数: 约20个
-- =====================================================

-- =====================================================
-- 第一部分: 创建知识领域 - Python编程基础
-- =====================================================

-- 假设使用现有的演示租户和学习者
-- tenant_id: '00000000-0000-0000-0000-000000000001'
-- learner_id: '10000000-0000-0000-0000-000000000001'

-- 创建学习目标: Python编程入门
INSERT INTO learning_goals (goal_id, tenant_id, learner_id, goal_type, goal_name, target_date, status, goal_metadata) VALUES
('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001',
 '10000000-0000-0000-0000-000000000001', 'skill', 'Python Programming Fundamentals', '2026-03-01', 'active',
 '{"skill_type": "programming", "total_topics": 7, "study_hours_per_week": 8}'::jsonb);

-- 创建Python编程领域
INSERT INTO knowledge_domains (domain_id, tenant_id, goal_id, domain_code, domain_name, weight_percentage, total_topics, recommended_teaching_mode) 
SELECT 
    '30000000-0000-0000-0000-000000000002'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    '20000000-0000-0000-0000-000000000002'::uuid,
    'PY',
    'Python编程基础 (Python Programming Fundamentals)',
    100.00,
    7,
    mode_id
FROM teaching_modes WHERE mode_name = 'lecture' LIMIT 1;

-- 为Python领域配置教学策略
INSERT INTO domain_teaching_strategies (tenant_id, domain_id, primary_mode_id, fallback_mode_ids, switching_rules)
SELECT 
    '00000000-0000-0000-0000-000000000001'::uuid,
    '30000000-0000-0000-0000-000000000002'::uuid,
    (SELECT mode_id FROM teaching_modes WHERE mode_name = 'lecture'),
    ARRAY[(SELECT mode_id FROM teaching_modes WHERE mode_name = 'socratic')],
    '{"consecutive_failures_threshold": 2, "auto_switch_enabled": true, "low_engagement_threshold": 0.4}'::jsonb;

-- =====================================================
-- 第二部分: 创建Python主题
-- =====================================================

-- 主题1: Python基本语法与变量
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.1', 'Python基本语法与变量',
 '掌握Python的基本语法规则、变量命名、注释、缩进等核心概念', 'easy', 60);

-- 主题2: 数据类型与运算符
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.2', '数据类型与运算符',
 '理解Python的基本数据类型(int, float, str, bool)和各种运算符(算术、比较、逻辑)', 'easy', 75);

-- 主题3: 控制结构(条件与循环)
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.3', '控制结构(条件与循环)',
 '掌握if-elif-else条件语句、for循环、while循环及控制流语句(break, continue)', 'medium', 90);

-- 主题4: 函数与参数
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.4', '函数与参数',
 '学习函数定义、参数类型(位置、默认、关键字、*args、**kwargs)、返回值和作用域', 'medium', 100);

-- 主题5: 数据结构(列表、字典、集合)
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.5', '数据结构(列表、字典、集合)',
 '掌握Python核心数据结构: list, tuple, dict, set的特性、操作和使用场景', 'medium', 120);

-- 主题6: 文件处理与异常
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.6', '文件处理与异常',
 '学习文件读写操作(open, read, write)、异常处理机制(try-except-finally)', 'medium', 90);

-- 主题7: 面向对象基础
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.7', '面向对象基础',
 '理解类和对象的概念、类的定义、__init__方法、实例属性和方法', 'hard', 110);

-- =====================================================
-- 第三部分: 创建概念和知识点
-- =====================================================

-- 主题PY.1的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules, common_pitfalls) VALUES
('51000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000001',
 'Python缩进规则', 
 'Python使用缩进来表示代码块,而不是大括号。标准缩进是4个空格。同一代码块的所有语句必须保持相同的缩进级别。',
 ARRAY['标准缩进 = 4个空格', 'Tab可以使用但不推荐', '不要混用空格和Tab'],
 ARRAY['缩进用于定义代码块', '函数、类、循环、条件语句都需要缩进', '缩进错误会导致IndentationError'],
 ARRAY['混用Tab和空格导致难以发现的错误', '复制代码时缩进不一致', '忘记在冒号后缩进']),

('51000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000001',
 '变量命名规范', 
 'Python变量名使用小写字母和下划线(snake_case)。变量名必须以字母或下划线开头,不能包含空格,区分大小写。',
 ARRAY['有效命名: user_name, _count, data2', '无效命名: 2data, user-name, my var'],
 ARRAY['使用描述性名称', '避免使用Python关键字', '常量使用全大写'],
 ARRAY['使用关键字作为变量名', '变量名过于简短无意义', '忽略命名约定']);

-- 主题PY.4的核心概念  
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules) VALUES
('51000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000004',
 '函数参数类型', 
 'Python支持多种参数类型: 位置参数(必需)、默认参数、关键字参数、*args(可变位置参数)、**kwargs(可变关键字参数)。',
 ARRAY['def func(pos, default=value, *args, **kwargs):', '调用: func(1, 2, 3, 4, key=5)'],
 ARRAY['位置参数必须在默认参数之前', '*args捕获多余位置参数为tuple', '**kwargs捕获多余关键字参数为dict', '参数顺序: 位置 > 默认 > *args > **kwargs']);

INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, rules, common_pitfalls) VALUES
('51000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000004',
 'LEGB作用域规则', 
 'Python变量查找遵循LEGB规则: Local(局部) → Enclosing(闭包) → Global(全局) → Built-in(内置)。',
 ARRAY['Local: 函数内部定义的变量', 'Enclosing: 外层函数的变量', 'Global: 模块级别的变量', 'Built-in: Python内置的名称', '使用global关键字修改全局变量', '使用nonlocal关键字修改闭包变量'],
 ARRAY['在函数内修改全局变量忘记使用global', '混淆局部变量和全局变量', '过度使用全局变量']);

-- 主题PY.5的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules) VALUES
('51000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000005',
 'List vs Tuple vs Set vs Dict', 
 'Python四种核心数据结构的特性对比: List(可变,有序,允许重复), Tuple(不可变,有序,允许重复), Set(可变,无序,不允许重复), Dict(可变,3.7+有序,key不重复)。',
 ARRAY['list: [1, 2, 3]', 'tuple: (1, 2, 3)', 'set: {1, 2, 3}', 'dict: {\"a\": 1, \"b\": 2}'],
 ARRAY['List适合需要修改的序列', 'Tuple适合不变数据,性能更好', 'Set适合去重和成员检测', 'Dict通过key快速访问,O(1)复杂度']);

-- 主题PY.6的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules, common_pitfalls) VALUES
('51000000-0000-0000-0000-000000000006', '41000000-0000-0000-0000-000000000006',
 '文件操作最佳实践', 
 '使用with语句(上下文管理器)打开文件可以自动关闭文件,即使发生异常。',
 ARRAY['with open(\"file.txt\", \"r\") as f:', '    content = f.read()', '# 文件自动关闭'],
 ARRAY['使用with语句确保文件正确关闭', 'r模式读取,w模式写入(覆盖),a模式追加', '大文件使用readline()或迭代'],
 ARRAY['忘记关闭文件导致资源泄漏', '使用w模式意外覆盖文件', '不处理文件不存在的异常']);

-- 主题PY.7的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules) VALUES
('51000000-0000-0000-0000-000000000007', '41000000-0000-0000-0000-000000000007',
 '类的定义和实例化', 
 'Python类使用class关键字定义。__init__是构造方法,self是实例引用(类似其他语言的this)。',
 ARRAY['class ClassName:', '    def __init__(self, param):', '        self.attribute = param', 'obj = ClassName(value)'],
 ARRAY['类名使用PascalCase(首字母大写)', '__init__方法的第一个参数必须是self', 'self代表实例本身', '实例方法第一个参数都是self']);

-- =====================================================
-- 第四部分: 创建主题依赖关系
-- =====================================================

-- PY.1 → PY.2
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000002', 'required', 0.90);

-- PY.2 → PY.3
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000003', 'required', 0.85);

-- PY.2 → PY.5
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000005', 'recommended', 0.70);

-- PY.3 → PY.4
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000004', 'recommended', 0.75);

-- PY.5 → PY.6
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000006', 'recommended', 0.60);

-- PY.4 + PY.5 → PY.7
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000007', 'required', 0.80);

INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000007', 'recommended', 0.70);

-- =====================================================
-- 第五部分: 创建记忆辅助示例
-- =====================================================

-- 记忆辅助1: LEGB作用域规则(Acronym)
INSERT INTO mnemonic_devices (topic_id, mnemonic_type, content, effectiveness_rating, is_language_independent) VALUES
('41000000-0000-0000-0000-000000000004', 'acronym',
 '{"acronym": "LEGB", "full_words": ["Local", "Enclosing", "Global", "Built-in"], 
   "explanation": "记住LEGB顺序：Python变量查找从内到外，局部→闭包→全局→内置",
   "story": "Let''s Explore Global Built-ins - Python变量查找的从内到外之旅"}'::jsonb,
 0.85, TRUE);

-- 记忆辅助2: 数据结构对比表(Comparison Table)
INSERT INTO mnemonic_devices (topic_id, mnemonic_type, content, effectiveness_rating, is_language_independent) VALUES
('41000000-0000-0000-0000-000000000005', 'comparison_table',
 '{"table_title": "Python核心数据结构对比", 
   "concepts": ["List", "Tuple", "Set", "Dict"],
   "dimensions": ["可变性", "有序性", "重复元素", "索引方式", "性能特点"],
   "table_data": {
     "List": ["可变", "有序", "允许", "整数索引", "灵活但较慢"],
     "Tuple": ["不可变", "有序", "允许", "整数索引", "快速且节省内存"],
     "Set": ["可变", "无序", "不允许", "不支持", "快速查找O(1)"],
     "Dict": ["可变", "3.7+有序", "key不重复", "key索引", "快速查找O(1)"]
   },
   "key_differences": [
     "List可变、Tuple不可变，性能上Tuple更快",
     "Set自动去重，适合成员关系检测",
     "Dict通过key访问，查找时间复杂度O(1)"
   ]}'::jsonb,
 0.90, TRUE);

-- 记忆辅助3: with语句类比(Analogy)
INSERT INTO mnemonic_devices (topic_id, mnemonic_type, content, effectiveness_rating) VALUES
('41000000-0000-0000-0000-000000000006', 'analogy',
 '{"abstract_concept": "with语句自动关闭文件",
   "concrete_analogy": "自动门",
   "mapping": {
     "打开文件": "进门时门自动打开",
     "使用文件": "在房间内活动",
     "关闭文件": "离开时门自动关闭",
     "异常处理": "即使被推出去，门也会关闭"
   },
   "explanation": "with语句就像自动门：进入时自动打开(open)，离开时自动关闭(close)，即使中途出错也会确保门关上(异常安全)。",
   "limitations": "with语句需要对象支持上下文管理协议(__enter__和__exit__方法)"}'::jsonb,
 0.80);

-- =====================================================
-- 第六部分: 创建权威来源
-- =====================================================

INSERT INTO authority_sources (source_name, source_url, domain_relevance, trust_score) VALUES
('Python Official Documentation', 'https://docs.python.org/3/', 'python', 1.00),
('Python Language Reference', 'https://docs.python.org/3/reference/', 'python_syntax', 1.00),
('Python Standard Library', 'https://docs.python.org/3/library/', 'python_stdlib', 1.00),
('PEP 8 Style Guide', 'https://peps.python.org/pep-0008/', 'python_style', 0.95),
('Real Python Tutorials', 'https://realpython.com/', 'python_learning', 0.90);

-- =====================================================
-- 完成: Python编程领域样例数据
-- 主题数: 7个
-- 概念数: 7个核心概念
-- 依赖关系: 7条
-- 记忆辅助: 3个
-- =====================================================
-- =====================================================
-- 智能学习助手Agent系统 - Python编程领域样例数据
-- 描述: Python编程基础知识领域的完整样例数据
-- 领域: Python编程基础
-- 主题数: 7个
-- 概念数: 约20个
-- =====================================================

-- =====================================================
-- 第一部分: 创建知识领域 - Python编程基础
-- =====================================================

-- 假设使用现有的演示租户和学习者
-- tenant_id: '00000000-0000-0000-0000-000000000001'
-- learner_id: '10000000-0000-0000-0000-000000000001'

-- 创建学习目标: Python编程入门
INSERT INTO learning_goals (goal_id, tenant_id, learner_id, goal_type, goal_name, target_date, status, goal_metadata) VALUES
('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001',
 '10000000-0000-0000-0000-000000000001', 'skill', 'Python Programming Fundamentals', '2026-03-01', 'active',
 '{"skill_type": "programming", "total_topics": 7, "study_hours_per_week": 8}'::jsonb);

-- 创建Python编程领域
INSERT INTO knowledge_domains (domain_id, tenant_id, goal_id, domain_code, domain_name, weight_percentage, total_topics, recommended_teaching_mode) 
SELECT 
    '30000000-0000-0000-0000-000000000002'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    '20000000-0000-0000-0000-000000000002'::uuid,
    'PY',
    'Python编程基础 (Python Programming Fundamentals)',
    100.00,
    7,
    mode_id
FROM teaching_modes WHERE mode_name = 'lecture' LIMIT 1;

-- 为Python领域配置教学策略
INSERT INTO domain_teaching_strategies (tenant_id, domain_id, primary_mode_id, fallback_mode_ids, switching_rules)
SELECT 
    '00000000-0000-0000-0000-000000000001'::uuid,
    '30000000-0000-0000-0000-000000000002'::uuid,
    (SELECT mode_id FROM teaching_modes WHERE mode_name = 'lecture'),
    ARRAY[(SELECT mode_id FROM teaching_modes WHERE mode_name = 'socratic')],
    '{"consecutive_failures_threshold": 2, "auto_switch_enabled": true, "low_engagement_threshold": 0.4}'::jsonb;

-- =====================================================
-- 第二部分: 创建Python主题
-- =====================================================

-- 主题1: Python基本语法与变量
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.1', 'Python基本语法与变量',
 '掌握Python的基本语法规则、变量命名、注释、缩进等核心概念', 'easy', 60);

-- 主题2: 数据类型与运算符
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.2', '数据类型与运算符',
 '理解Python的基本数据类型(int, float, str, bool)和各种运算符(算术、比较、逻辑)', 'easy', 75);

-- 主题3: 控制结构(条件与循环)
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.3', '控制结构(条件与循环)',
 '掌握if-elif-else条件语句、for循环、while循环及控制流语句(break, continue)', 'medium', 90);

-- 主题4: 函数与参数
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.4', '函数与参数',
 '学习函数定义、参数类型(位置、默认、关键字、*args、**kwargs)、返回值和作用域', 'medium', 100);

-- 主题5: 数据结构(列表、字典、集合)
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.5', '数据结构(列表、字典、集合)',
 '掌握Python核心数据结构: list, tuple, dict, set的特性、操作和使用场景', 'medium', 120);

-- 主题6: 文件处理与异常
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.6', '文件处理与异常',
 '学习文件读写操作(open, read, write)、异常处理机制(try-except-finally)', 'medium', 90);

-- 主题7: 面向对象基础
INSERT INTO topics (topic_id, tenant_id, domain_id, topic_code, topic_name, description, difficulty_level, estimated_learning_time_minutes) VALUES
('41000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000001',
 '30000000-0000-0000-0000-000000000002', 'PY.7', '面向对象基础',
 '理解类和对象的概念、类的定义、__init__方法、实例属性和方法', 'hard', 110);

-- =====================================================
-- 第三部分: 创建概念和知识点
-- =====================================================

-- 主题PY.1的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules, common_pitfalls) VALUES
('51000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000001',
 'Python缩进规则', 
 'Python使用缩进来表示代码块,而不是大括号。标准缩进是4个空格。同一代码块的所有语句必须保持相同的缩进级别。',
 ARRAY['标准缩进 = 4个空格', 'Tab可以使用但不推荐', '不要混用空格和Tab'],
 ARRAY['缩进用于定义代码块', '函数、类、循环、条件语句都需要缩进', '缩进错误会导致IndentationError'],
 ARRAY['混用Tab和空格导致难以发现的错误', '复制代码时缩进不一致', '忘记在冒号后缩进']),

('51000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000001',
 '变量命名规范', 
 'Python变量名使用小写字母和下划线(snake_case)。变量名必须以字母或下划线开头,不能包含空格,区分大小写。',
 ARRAY['有效命名: user_name, _count, data2', '无效命名: 2data, user-name, my var'],
 ARRAY['使用描述性名称', '避免使用Python关键字', '常量使用全大写'],
 ARRAY['使用关键字作为变量名', '变量名过于简短无意义', '忽略命名约定']);

-- 主题PY.4的核心概念  
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules) VALUES
('51000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000004',
 '函数参数类型', 
 'Python支持多种参数类型: 位置参数(必需)、默认参数、关键字参数、*args(可变位置参数)、**kwargs(可变关键字参数)。',
 ARRAY['def func(pos, default=value, *args, **kwargs):', '调用: func(1, 2, 3, 4, key=5)'],
 ARRAY['位置参数必须在默认参数之前', '*args捕获多余位置参数为tuple', '**kwargs捕获多余关键字参数为dict', '参数顺序: 位置 > 默认 > *args > **kwargs']);

INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, rules, common_pitfalls) VALUES
('51000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000004',
 'LEGB作用域规则', 
 'Python变量查找遵循LEGB规则: Local(局部) → Enclosing(闭包) → Global(全局) → Built-in(内置)。',
 ARRAY['Local: 函数内部定义的变量', 'Enclosing: 外层函数的变量', 'Global: 模块级别的变量', 'Built-in: Python内置的名称', '使用global关键字修改全局变量', '使用nonlocal关键字修改闭包变量'],
 ARRAY['在函数内修改全局变量忘记使用global', '混淆局部变量和全局变量', '过度使用全局变量']);

-- 主题PY.5的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules) VALUES
('51000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000005',
 'List vs Tuple vs Set vs Dict', 
 'Python四种核心数据结构的特性对比: List(可变,有序,允许重复), Tuple(不可变,有序,允许重复), Set(可变,无序,不允许重复), Dict(可变,3.7+有序,key不重复)。',
 ARRAY['list: [1, 2, 3]', 'tuple: (1, 2, 3)', 'set: {1, 2, 3}', 'dict: {\"a\": 1, \"b\": 2}'],
 ARRAY['List适合需要修改的序列', 'Tuple适合不变数据,性能更好', 'Set适合去重和成员检测', 'Dict通过key快速访问,O(1)复杂度']);

-- 主题PY.6的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules, common_pitfalls) VALUES
('51000000-0000-0000-0000-000000000006', '41000000-0000-0000-0000-000000000006',
 '文件操作最佳实践', 
 '使用with语句(上下文管理器)打开文件可以自动关闭文件,即使发生异常。',
 ARRAY['with open(\"file.txt\", \"r\") as f:', '    content = f.read()', '# 文件自动关闭'],
 ARRAY['使用with语句确保文件正确关闭', 'r模式读取,w模式写入(覆盖),a模式追加', '大文件使用readline()或迭代'],
 ARRAY['忘记关闭文件导致资源泄漏', '使用w模式意外覆盖文件', '不处理文件不存在的异常']);

-- 主题PY.7的核心概念
INSERT INTO concepts (concept_id, topic_id, concept_name, explanation, formulas, rules) VALUES
('51000000-0000-0000-0000-000000000007', '41000000-0000-0000-0000-000000000007',
 '类的定义和实例化', 
 'Python类使用class关键字定义。__init__是构造方法,self是实例引用(类似其他语言的this)。',
 ARRAY['class ClassName:', '    def __init__(self, param):', '        self.attribute = param', 'obj = ClassName(value)'],
 ARRAY['类名使用PascalCase(首字母大写)', '__init__方法的第一个参数必须是self', 'self代表实例本身', '实例方法第一个参数都是self']);

-- =====================================================
-- 第四部分: 创建主题依赖关系
-- =====================================================

-- PY.1 → PY.2
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000001', '41000000-0000-0000-0000-000000000002', 'required', 0.90);

-- PY.2 → PY.3
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000003', 'required', 0.85);

-- PY.2 → PY.5
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000002', '41000000-0000-0000-0000-000000000005', 'recommended', 0.70);

-- PY.3 → PY.4
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000003', '41000000-0000-0000-0000-000000000004', 'recommended', 0.75);

-- PY.5 → PY.6
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000006', 'recommended', 0.60);

-- PY.4 + PY.5 → PY.7
INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000004', '41000000-0000-0000-0000-000000000007', 'required', 0.80);

INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, dependency_type, strength) VALUES
('41000000-0000-0000-0000-000000000005', '41000000-0000-0000-0000-000000000007', 'recommended', 0.70);

-- =====================================================
-- 第五部分: 创建记忆辅助示例
-- =====================================================

-- 记忆辅助1: LEGB作用域规则(Acronym)
INSERT INTO mnemonic_devices (topic_id, mnemonic_type, content, effectiveness_rating, is_language_independent) VALUES
('41000000-0000-0000-0000-000000000004', 'acronym',
 '{"acronym": "LEGB", "full_words": ["Local", "Enclosing", "Global", "Built-in"], 
   "explanation": "记住LEGB顺序：Python变量查找从内到外，局部→闭包→全局→内置",
   "story": "Let''s Explore Global Built-ins - Python变量查找的从内到外之旅"}'::jsonb,
 0.85, TRUE);

-- 记忆辅助2: 数据结构对比表(Comparison Table)
INSERT INTO mnemonic_devices (topic_id, mnemonic_type, content, effectiveness_rating, is_language_independent) VALUES
('41000000-0000-0000-0000-000000000005', 'comparison_table',
 '{"table_title": "Python核心数据结构对比", 
   "concepts": ["List", "Tuple", "Set", "Dict"],
   "dimensions": ["可变性", "有序性", "重复元素", "索引方式", "性能特点"],
   "table_data": {
     "List": ["可变", "有序", "允许", "整数索引", "灵活但较慢"],
     "Tuple": ["不可变", "有序", "允许", "整数索引", "快速且节省内存"],
     "Set": ["可变", "无序", "不允许", "不支持", "快速查找O(1)"],
     "Dict": ["可变", "3.7+有序", "key不重复", "key索引", "快速查找O(1)"]
   },
   "key_differences": [
     "List可变、Tuple不可变，性能上Tuple更快",
     "Set自动去重，适合成员关系检测",
     "Dict通过key访问，查找时间复杂度O(1)"
   ]}'::jsonb,
 0.90, TRUE);

-- 记忆辅助3: with语句类比(Analogy)
INSERT INTO mnemonic_devices (topic_id, mnemonic_type, content, effectiveness_rating) VALUES
('41000000-0000-0000-0000-000000000006', 'analogy',
 '{"abstract_concept": "with语句自动关闭文件",
   "concrete_analogy": "自动门",
   "mapping": {
     "打开文件": "进门时门自动打开",
     "使用文件": "在房间内活动",
     "关闭文件": "离开时门自动关闭",
     "异常处理": "即使被推出去，门也会关闭"
   },
   "explanation": "with语句就像自动门：进入时自动打开(open)，离开时自动关闭(close)，即使中途出错也会确保门关上(异常安全)。",
   "limitations": "with语句需要对象支持上下文管理协议(__enter__和__exit__方法)"}'::jsonb,
 0.80);

-- =====================================================
-- 第六部分: 创建权威来源
-- =====================================================

INSERT INTO authority_sources (source_name, source_url, domain_relevance, trust_score) VALUES
('Python Official Documentation', 'https://docs.python.org/3/', 'python', 1.00),
('Python Language Reference', 'https://docs.python.org/3/reference/', 'python_syntax', 1.00),
('Python Standard Library', 'https://docs.python.org/3/library/', 'python_stdlib', 1.00),
('PEP 8 Style Guide', 'https://peps.python.org/pep-0008/', 'python_style', 0.95),
('Real Python Tutorials', 'https://realpython.com/', 'python_learning', 0.90);

-- =====================================================
-- 完成: Python编程领域样例数据
-- 主题数: 7个
-- 概念数: 7个核心概念
-- 依赖关系: 7条
-- 记忆辅助: 3个
-- =====================================================
