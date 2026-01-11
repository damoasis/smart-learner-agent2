-- =====================================================
-- 样例数据：法律基础概念领域
-- 包含：1个知识领域、6个主题、18个核心概念、6条主题依赖关系、3个记忆辅助
-- UUID前缀：
--   42xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx: Law domain topics
--   52xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx: Law domain concepts
-- =====================================================

-- =====================================================
-- 第一部分：创建知识领域 - 民法基础概念
-- =====================================================

-- 插入学习目标
INSERT INTO learning_goals (
    goal_id, tenant_id, learner_id, goal_name, target_completion_date,
    is_active, created_at, updated_at
) VALUES (
    '62000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001',
    '掌握中国民法基础概念',
    CURRENT_DATE + INTERVAL '180 days',
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (goal_id) DO NOTHING;

-- 插入知识领域
INSERT INTO knowledge_domains (
    domain_id, tenant_id, domain_name, description,
    created_at, updated_at
) VALUES (
    '32000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '民法基础概念',
    '中国民法的基本原则和核心概念，包括民事法律关系、民事主体、民事权利、民事法律行为、合同法和侵权责任的基础知识',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (domain_id) DO NOTHING;

-- 插入领域教学策略
INSERT INTO domain_teaching_strategies (
    domain_id, tenant_id, strategy_description, recommended_sequence,
    created_at, updated_at
) VALUES (
    '32000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '民法学习应从基本概念入手，逐步理解法律关系、主体、权利、法律行为等核心要素，最后学习合同和侵权等具体制度。适合采用案例教学法和苏格拉底式提问。',
    ARRAY['T_LAW_001', 'T_LAW_002', 'T_LAW_003', 'T_LAW_004', 'T_LAW_005', 'T_LAW_006'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (domain_id, tenant_id) DO NOTHING;

-- =====================================================
-- 第二部分：创建6个法律主题
-- =====================================================

-- T_LAW_001: 民事法律关系
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '民事法律关系',
    '民事法律关系的概念、构成要素（主体、客体、内容）以及法律事实的分类',
    'BEGINNER',
    45,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_002: 民事主体（自然人、法人）
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '民事主体（自然人、法人）',
    '自然人的民事权利能力和民事行为能力，法人的概念、类型及设立条件',
    'BEGINNER',
    60,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_003: 民事权利类型
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '民事权利类型',
    '物权、债权、人身权、知识产权等民事权利的分类及基本特征',
    'INTERMEDIATE',
    50,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_004: 民事法律行为
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000004',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '民事法律行为',
    '民事法律行为的概念、成立要件、效力分类（有效、无效、可撤销）及代理制度',
    'INTERMEDIATE',
    70,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_005: 合同法基础
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000005',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '合同法基础',
    '合同的订立、效力、履行、变更、解除及违约责任的基本规则',
    'INTERMEDIATE',
    80,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_006: 侵权责任
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000006',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '侵权责任',
    '侵权行为的构成要件、归责原则（过错责任、无过错责任）及损害赔偿规则',
    'ADVANCED',
    75,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- =====================================================
-- 第三部分：创建18个核心概念
-- =====================================================

-- T_LAW_001 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000001',
    '42000000-0000-0000-0000-000000000001',
    '民事法律关系三要素',
    '民事法律关系由主体（权利义务的承担者）、客体（权利义务指向的对象）和内容（具体的权利义务）三要素构成。',
    ARRAY['主体：自然人、法人、非法人组织', '客体：物、行为、智力成果、人身利益', '内容：权利和义务'],
    ARRAY['三要素缺一不可', '主体必须具有民事权利能力', '客体必须合法'],
    ARRAY['买卖合同：主体是买卖双方，客体是商品，内容是交付商品和支付价款的权利义务'],
    ARRAY['混淆主体和客体', '忽略内容要素'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000002',
    '42000000-0000-0000-0000-000000000001',
    '法律事实的分类',
    '法律事实是引起民事法律关系产生、变更、消灭的客观情况，分为事件（不以人的意志为转移）和行为（人的有意识活动）。',
    ARRAY['事件：自然事件（地震、洪水）、社会事件（战争）', '行为：合法行为（民事法律行为）、违法行为（侵权行为）'],
    ARRAY['事件不以人的意志为转移', '行为分为合法和违法'],
    ARRAY['事件：因地震导致房屋损毁，保险合同生效', '行为：签订租赁合同，建立租赁关系'],
    ARRAY['混淆事件和行为', '认为所有行为都是合法的'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000003',
    '42000000-0000-0000-0000-000000000001',
    '民事权利与民事义务',
    '民事权利是法律赋予民事主体满足其利益的法律手段，民事义务是民事主体依法承担的约束。权利和义务相互对应。',
    ARRAY['权利：请求权、支配权、形成权、抗辩权', '义务：法定义务、约定义务'],
    ARRAY['权利和义务对应存在', '权利不得滥用', '义务必须履行'],
    ARRAY['债权人有请求债务人还款的权利，债务人有还款的义务'],
    ARRAY['只强调权利忽视义务', '权利滥用'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_002 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000004',
    '42000000-0000-0000-0000-000000000002',
    '民事权利能力',
    '民事权利能力是民事主体依法享有民事权利和承担民事义务的资格。自然人从出生到死亡具有民事权利能力。',
    ARRAY['自然人：从出生到死亡', '法人：从成立到终止'],
    ARRAY['人人平等享有', '不得剥夺或限制', '始于出生终于死亡'],
    ARRAY['新生儿从出生时即享有继承权'],
    ARRAY['混淆权利能力和行为能力', '认为胎儿不享有权利能力'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000005',
    '42000000-0000-0000-0000-000000000002',
    '民事行为能力',
    '民事行为能力是民事主体独立实施民事法律行为的资格。根据年龄和智力状况分为完全、限制、无民事行为能力。',
    ARRAY['完全：18周岁以上成年人', '限制：8-18周岁未成年人、不能完全辨认自己行为的成年人', '无：不满8周岁、完全不能辨认自己行为的成年人'],
    ARRAY['完全行为能力人可独立实施任何民事法律行为', '限制行为能力人可实施与其智力相适应的民事法律行为', '无行为能力人的民事法律行为由法定代理人代理'],
    ARRAY['10岁儿童可以买文具（与智力相适应），但不能独立买房'],
    ARRAY['混淆年龄界限', '认为限制行为能力人完全不能实施法律行为'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000006',
    '42000000-0000-0000-0000-000000000002',
    '法人的分类',
    '法人是具有民事权利能力和民事行为能力，依法独立享有民事权利和承担民事义务的组织。分为营利法人、非营利法人和特别法人。',
    ARRAY['营利法人：公司、企业', '非营利法人：事业单位、社会团体、基金会', '特别法人：机关法人、农村集体经济组织法人'],
    ARRAY['法人独立承担民事责任', '法人以其全部财产对债务负责', '法人设立需依法登记'],
    ARRAY['有限责任公司是营利法人，红十字会是非营利法人'],
    ARRAY['混淆法人和自然人', '认为法人不承担责任'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_003 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000007',
    '42000000-0000-0000-0000-000000000003',
    '物权与债权的区别',
    '物权是直接支配特定物的权利，具有绝对性、排他性；债权是请求特定人为或不为一定行为的权利，具有相对性。',
    ARRAY['物权：所有权、用益物权、担保物权', '债权：合同之债、侵权之债、不当得利、无因管理'],
    ARRAY['物权具有排他性，一物一权', '债权具有相对性，仅对债务人有效', '物权优先于债权'],
    ARRAY['甲对房屋享有所有权（物权），乙对甲享有租金请求权（债权）'],
    ARRAY['混淆物权和债权', '不理解物权的排他性'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000008',
    '42000000-0000-0000-0000-000000000003',
    '人身权的特征',
    '人身权是与人身不可分离、不直接具有财产内容的民事权利，包括人格权（生命权、健康权、姓名权等）和身份权（配偶权、监护权等）。',
    ARRAY['人格权：生命权、健康权、姓名权、肖像权、名誉权、隐私权', '身份权：配偶权、亲权、监护权'],
    ARRAY['人身权不可转让', '人身权不可放弃', '人身权不可继承'],
    ARRAY['未经同意使用他人肖像用于商业广告，侵犯肖像权'],
    ARRAY['混淆人格权和身份权', '认为人身权可以转让'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000009',
    '42000000-0000-0000-0000-000000000003',
    '知识产权的特征',
    '知识产权是对智力成果享有的专有权利，包括著作权、专利权、商标权等，具有专有性、地域性、时间性。',
    ARRAY['专有性：权利人独占使用', '地域性：仅在授予国有效', '时间性：保护期限有限'],
    ARRAY['知识产权需依法确认', '侵犯知识产权需承担法律责任', '知识产权可以转让和许可使用'],
    ARRAY['发明专利保护20年，实用新型和外观设计专利保护10年'],
    ARRAY['忽视知识产权的时间性', '混淆不同类型知识产权的保护期限'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_004 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000010',
    '42000000-0000-0000-0000-000000000004',
    '法律行为的有效要件',
    '民事法律行为有效需满足三要件：行为人具有相应民事行为能力；意思表示真实；不违反法律强制性规定和公序良俗。',
    ARRAY['要件一：行为能力', '要件二：意思真实', '要件三：内容合法'],
    ARRAY['三要件同时满足才有效', '欠缺任一要件导致无效或可撤销', '意思表示瑕疵包括欺诈、胁迫、重大误解'],
    ARRAY['10岁儿童购买高价电脑，因欠缺行为能力，法律行为可撤销'],
    ARRAY['混淆无效和可撤销', '忽视意思表示真实性'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000011',
    '42000000-0000-0000-0000-000000000004',
    '无效、可撤销、效力待定',
    '民事法律行为根据效力瑕疵分为：无效（自始无效）、可撤销（撤销前有效）、效力待定（需追认）。',
    ARRAY['无效：违反强制性规定、违背公序良俗、虚假表示', '可撤销：欺诈、胁迫、重大误解、显失公平', '效力待定：限制行为能力人实施的超范围行为、无权代理'],
    ARRAY['无效自始无效，不能补正', '可撤销行为在撤销前有效', '效力待定行为可经追认生效'],
    ARRAY['甲胁迫乙签订合同，乙可在一年内撤销'],
    ARRAY['混淆三种效力类型', '不理解撤销权的除斥期间'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000012',
    '42000000-0000-0000-0000-000000000004',
    '代理制度',
    '代理是代理人在代理权限内以被代理人名义实施民事法律行为，法律后果直接归属于被代理人。分为委托代理、法定代理、指定代理。',
    ARRAY['委托代理：基于被代理人授权', '法定代理：基于法律规定（父母代理子女）', '指定代理：基于人民法院或有关机关指定'],
    ARRAY['代理需有代理权', '代理人需以被代理人名义行事', '代理行为后果归属被代理人', '无权代理需追认'],
    ARRAY['父母作为未成年子女的法定代理人签订教育服务合同'],
    ARRAY['混淆代理和委托', '不理解无权代理的后果'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_005 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000013',
    '42000000-0000-0000-0000-000000000005',
    '合同的订立过程',
    '合同订立包括要约和承诺两个阶段。要约是希望与他人订立合同的意思表示，承诺是受要约人同意要约的意思表示。',
    ARRAY['要约：内容具体确定、表明经承诺即受约束', '承诺：承诺生效时合同成立'],
    ARRAY['要约可撤回或撤销（限制条件）', '承诺需在要约有效期内作出', '承诺内容应与要约一致'],
    ARRAY['甲在网站标价出售商品（要约邀请），乙下单（要约），甲确认发货（承诺）'],
    ARRAY['混淆要约和要约邀请', '不理解承诺生效时间'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000014',
    '42000000-0000-0000-0000-000000000005',
    '合同的履行原则',
    '合同履行应遵守全面履行原则（按约定履行）、诚实信用原则、情势变更原则等。',
    ARRAY['全面履行：标的、质量、数量、期限、地点、方式', '诚实信用：不损害对方利益', '情势变更：重大变化可变更或解除'],
    ARRAY['当事人应全面履行合同义务', '不得擅自变更或解除合同', '履行中应协作配合'],
    ARRAY['甲与乙约定交付100件商品，甲应按质按量按时交付，不得少交或延迟'],
    ARRAY['理解全面履行的具体要求', '忽视附随义务'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000015',
    '42000000-0000-0000-0000-000000000005',
    '违约责任',
    '违约责任是当事人不履行合同义务或履行不符合约定时应承担的民事责任，包括继续履行、采取补救措施、赔偿损失等。',
    ARRAY['继续履行：要求违约方履行合同', '赔偿损失：包括实际损失和可得利益损失', '违约金：约定或法定', '定金：双倍返还'],
    ARRAY['违约责任采用严格责任（不考虑过错）', '可约定违约金', '违约金过高可请求调整'],
    ARRAY['甲延迟交货，乙可要求甲继续交货并赔偿因延迟导致的损失'],
    ARRAY['混淆违约责任和侵权责任', '不理解可得利益损失的计算'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_006 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000016',
    '42000000-0000-0000-0000-000000000006',
    '侵权行为的构成要件',
    '一般侵权行为需满足四要件：行为违法、损害事实、因果关系、主观过错。',
    ARRAY['违法行为：违反法定义务', '损害事实：财产或人身损害', '因果关系：违法行为与损害的因果联系', '主观过错：故意或过失'],
    ARRAY['四要件同时满足构成侵权', '特殊侵权可能不要求过错（无过错责任）', '举证责任分配因侵权类型而异'],
    ARRAY['甲驾车闯红灯撞伤乙，甲的违法行为、乙的伤害、二者因果关系及甲的过失构成侵权'],
    ARRAY['混淆一般侵权和特殊侵权', '忽视因果关系的证明'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000017',
    '42000000-0000-0000-0000-000000000006',
    '归责原则',
    '侵权责任归责原则包括过错责任原则（一般原则）、无过错责任原则（特殊情形）和公平责任原则（补充原则）。',
    ARRAY['过错责任：需证明侵权人有过错', '无过错责任：不考虑过错（产品责任、环境污染、高度危险作业）', '公平责任：双方均无过错时根据公平原则分担损失'],
    ARRAY['过错责任是基本原则', '无过错责任适用于法律明确规定的情形', '公平责任适用极少'],
    ARRAY['宠物狗伤人，饲养人承担无过错责任，即使饲养人无过错也需赔偿'],
    ARRAY['混淆不同归责原则的适用范围', '不理解举证责任倒置'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000018',
    '42000000-0000-0000-0000-000000000006',
    '损害赔偿的范围',
    '侵权损害赔偿应全面赔偿受害人的损失，包括财产损失（直接损失和间接损失）和精神损害。',
    ARRAY['财产损失：直接损失（修理费、医疗费）、间接损失（误工费、护理费）', '精神损害：精神痛苦的抚慰金'],
    ARRAY['全面赔偿原则', '损益相抵规则', '过失相抵规则（受害人有过错可减轻责任）'],
    ARRAY['甲撞伤乙，赔偿医疗费、误工费、护理费，并因造成乙残疾支付精神损害抚慰金'],
    ARRAY['忽视间接损失', '不理解精神损害赔偿的适用条件'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- =====================================================
-- 第四部分：创建6条主题依赖关系
-- =====================================================

INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, strength) VALUES
('42000000-0000-0000-0000-000000000001', '42000000-0000-0000-0000-000000000002', 0.85),  -- 民事法律关系 → 民事主体
('42000000-0000-0000-0000-000000000001', '42000000-0000-0000-0000-000000000003', 0.75),  -- 民事法律关系 → 民事权利类型
('42000000-0000-0000-0000-000000000002', '42000000-0000-0000-0000-000000000004', 0.80),  -- 民事主体 → 民事法律行为
('42000000-0000-0000-0000-000000000003', '42000000-0000-0000-0000-000000000004', 0.70),  -- 民事权利类型 → 民事法律行为
('42000000-0000-0000-0000-000000000004', '42000000-0000-0000-0000-000000000005', 0.90),  -- 民事法律行为 → 合同法基础
('42000000-0000-0000-0000-000000000004', '42000000-0000-0000-0000-000000000006', 0.75)   -- 民事法律行为 → 侵权责任
ON CONFLICT (prerequisite_topic_id, dependent_topic_id) DO NOTHING;

-- =====================================================
-- 第五部分：创建3个记忆辅助示例
-- =====================================================

-- 记忆辅助1：法律行为有效三要件（Number Pattern）
INSERT INTO mnemonic_devices (
    mnemonic_id, tenant_id, concept_id, strategy_type,
    content, effectiveness_rating, usage_count,
    created_at, updated_at
) VALUES (
    '72000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '52000000-0000-0000-0000-000000000010',
    'number',
    '{
        "numbers": [3],
        "pattern": "三要件",
        "memory_phrase": "能力、真实、合法——三件齐全行为有效",
        "explanation": "记住法律行为有效的三个必备要件：行为能力、意思真实、内容合法"
    }',
    0.88,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (mnemonic_id) DO NOTHING;

-- 记忆辅助2：侵权责任四要件（Acronym）
INSERT INTO mnemonic_devices (
    mnemonic_id, tenant_id, concept_id, strategy_type,
    content, effectiveness_rating, usage_count,
    created_at, updated_at
) VALUES (
    '72000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '52000000-0000-0000-0000-000000000016',
    'acronym',
    '{
        "acronym": "违损因过",
        "full_terms": ["违法行为", "损害事实", "因果关系", "主观过错"],
        "memory_tip": "侵权四要件：违（法）损（害）因（果）过（错）",
        "explanation": "一般侵权行为的四个构成要件缩略为'违损因过'"
    }',
    0.85,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (mnemonic_id) DO NOTHING;

-- 记忆辅助3：物权与债权的区别（Comparison Table）
INSERT INTO mnemonic_devices (
    mnemonic_id, tenant_id, concept_id, strategy_type,
    content, effectiveness_rating, usage_count,
    created_at, updated_at
) VALUES (
    '72000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000001',
    '52000000-0000-0000-0000-000000000007',
    'comparison',
    '{
        "items": ["物权", "债权"],
        "dimensions": [
            {
                "name": "性质",
                "values": ["绝对权（对世权）", "相对权（对人权）"]
            },
            {
                "name": "客体",
                "values": ["特定物", "特定人的行为"]
            },
            {
                "name": "排他性",
                "values": ["具有排他性，一物一权", "不具有排他性，同一标的可多个债权"]
            },
            {
                "name": "优先性",
                "values": ["物权优先于债权", "债权后于物权"]
            }
        ],
        "memory_tip": "物权对物，债权对人；物权绝对，债权相对；物权排他，债权共存；物权优先，债权在后"
    }',
    0.90,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (mnemonic_id) DO NOTHING;

-- =====================================================
-- 第六部分：创建5个权威来源（法律领域）
-- =====================================================

INSERT INTO authoritative_sources (
    source_id, tenant_id, source_name, source_type,
    url, reliability_score, domain_tags,
    created_at, updated_at
) VALUES
(
    '82000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '中华人民共和国民法典',
    'legal_document',
    'http://www.npc.gov.cn/npc/c30834/202006/75ba6483b8344591abd07917e1d25cc8.shtml',
    0.98,
    ARRAY['民法', '法律法规', '基本法律'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '82000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '最高人民法院民法典理解与适用',
    'legal_commentary',
    'https://www.court.gov.cn/',
    0.95,
    ARRAY['民法', '司法解释', '案例指导'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '82000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000001',
    '中国法律服务网',
    'online_database',
    'https://www.12348.gov.cn/',
    0.90,
    ARRAY['法律服务', '法律咨询', '法律法规查询'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '82000000-0000-0000-0000-000000000004',
    '10000000-0000-0000-0000-000000000001',
    '北大法宝 - 法律法规数据库',
    'online_database',
    'https://www.pkulaw.com/',
    0.92,
    ARRAY['法律数据库', '法规检索', '案例分析'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '82000000-0000-0000-0000-000000000005',
    '10000000-0000-0000-0000-000000000001',
    '中国法院网 - 案例库',
    'case_database',
    'https://www.chinacourt.org/',
    0.93,
    ARRAY['司法案例', '裁判文书', '法律适用'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (source_id) DO NOTHING;

-- =====================================================
-- 完成
-- =====================================================
-- =====================================================
-- 样例数据：法律基础概念领域
-- 包含：1个知识领域、6个主题、18个核心概念、6条主题依赖关系、3个记忆辅助
-- UUID前缀：
--   42xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx: Law domain topics
--   52xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx: Law domain concepts
-- =====================================================

-- =====================================================
-- 第一部分：创建知识领域 - 民法基础概念
-- =====================================================

-- 插入学习目标
INSERT INTO learning_goals (
    goal_id, tenant_id, learner_id, goal_name, target_completion_date,
    is_active, created_at, updated_at
) VALUES (
    '62000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001',
    '掌握中国民法基础概念',
    CURRENT_DATE + INTERVAL '180 days',
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (goal_id) DO NOTHING;

-- 插入知识领域
INSERT INTO knowledge_domains (
    domain_id, tenant_id, domain_name, description,
    created_at, updated_at
) VALUES (
    '32000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '民法基础概念',
    '中国民法的基本原则和核心概念，包括民事法律关系、民事主体、民事权利、民事法律行为、合同法和侵权责任的基础知识',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (domain_id) DO NOTHING;

-- 插入领域教学策略
INSERT INTO domain_teaching_strategies (
    domain_id, tenant_id, strategy_description, recommended_sequence,
    created_at, updated_at
) VALUES (
    '32000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '民法学习应从基本概念入手，逐步理解法律关系、主体、权利、法律行为等核心要素，最后学习合同和侵权等具体制度。适合采用案例教学法和苏格拉底式提问。',
    ARRAY['T_LAW_001', 'T_LAW_002', 'T_LAW_003', 'T_LAW_004', 'T_LAW_005', 'T_LAW_006'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (domain_id, tenant_id) DO NOTHING;

-- =====================================================
-- 第二部分：创建6个法律主题
-- =====================================================

-- T_LAW_001: 民事法律关系
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '民事法律关系',
    '民事法律关系的概念、构成要素（主体、客体、内容）以及法律事实的分类',
    'BEGINNER',
    45,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_002: 民事主体（自然人、法人）
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '民事主体（自然人、法人）',
    '自然人的民事权利能力和民事行为能力，法人的概念、类型及设立条件',
    'BEGINNER',
    60,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_003: 民事权利类型
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '民事权利类型',
    '物权、债权、人身权、知识产权等民事权利的分类及基本特征',
    'INTERMEDIATE',
    50,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_004: 民事法律行为
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000004',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '民事法律行为',
    '民事法律行为的概念、成立要件、效力分类（有效、无效、可撤销）及代理制度',
    'INTERMEDIATE',
    70,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_005: 合同法基础
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000005',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '合同法基础',
    '合同的订立、效力、履行、变更、解除及违约责任的基本规则',
    'INTERMEDIATE',
    80,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- T_LAW_006: 侵权责任
INSERT INTO topics (
    topic_id, tenant_id, domain_id, topic_name, description,
    difficulty_level, estimated_learning_time_minutes,
    created_at, updated_at
) VALUES (
    '42000000-0000-0000-0000-000000000006',
    '10000000-0000-0000-0000-000000000001',
    '32000000-0000-0000-0000-000000000002',
    '侵权责任',
    '侵权行为的构成要件、归责原则（过错责任、无过错责任）及损害赔偿规则',
    'ADVANCED',
    75,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (topic_id) DO NOTHING;

-- =====================================================
-- 第三部分：创建18个核心概念
-- =====================================================

-- T_LAW_001 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000001',
    '42000000-0000-0000-0000-000000000001',
    '民事法律关系三要素',
    '民事法律关系由主体（权利义务的承担者）、客体（权利义务指向的对象）和内容（具体的权利义务）三要素构成。',
    ARRAY['主体：自然人、法人、非法人组织', '客体：物、行为、智力成果、人身利益', '内容：权利和义务'],
    ARRAY['三要素缺一不可', '主体必须具有民事权利能力', '客体必须合法'],
    ARRAY['买卖合同：主体是买卖双方，客体是商品，内容是交付商品和支付价款的权利义务'],
    ARRAY['混淆主体和客体', '忽略内容要素'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000002',
    '42000000-0000-0000-0000-000000000001',
    '法律事实的分类',
    '法律事实是引起民事法律关系产生、变更、消灭的客观情况，分为事件（不以人的意志为转移）和行为（人的有意识活动）。',
    ARRAY['事件：自然事件（地震、洪水）、社会事件（战争）', '行为：合法行为（民事法律行为）、违法行为（侵权行为）'],
    ARRAY['事件不以人的意志为转移', '行为分为合法和违法'],
    ARRAY['事件：因地震导致房屋损毁，保险合同生效', '行为：签订租赁合同，建立租赁关系'],
    ARRAY['混淆事件和行为', '认为所有行为都是合法的'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000003',
    '42000000-0000-0000-0000-000000000001',
    '民事权利与民事义务',
    '民事权利是法律赋予民事主体满足其利益的法律手段，民事义务是民事主体依法承担的约束。权利和义务相互对应。',
    ARRAY['权利：请求权、支配权、形成权、抗辩权', '义务：法定义务、约定义务'],
    ARRAY['权利和义务对应存在', '权利不得滥用', '义务必须履行'],
    ARRAY['债权人有请求债务人还款的权利，债务人有还款的义务'],
    ARRAY['只强调权利忽视义务', '权利滥用'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_002 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000004',
    '42000000-0000-0000-0000-000000000002',
    '民事权利能力',
    '民事权利能力是民事主体依法享有民事权利和承担民事义务的资格。自然人从出生到死亡具有民事权利能力。',
    ARRAY['自然人：从出生到死亡', '法人：从成立到终止'],
    ARRAY['人人平等享有', '不得剥夺或限制', '始于出生终于死亡'],
    ARRAY['新生儿从出生时即享有继承权'],
    ARRAY['混淆权利能力和行为能力', '认为胎儿不享有权利能力'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000005',
    '42000000-0000-0000-0000-000000000002',
    '民事行为能力',
    '民事行为能力是民事主体独立实施民事法律行为的资格。根据年龄和智力状况分为完全、限制、无民事行为能力。',
    ARRAY['完全：18周岁以上成年人', '限制：8-18周岁未成年人、不能完全辨认自己行为的成年人', '无：不满8周岁、完全不能辨认自己行为的成年人'],
    ARRAY['完全行为能力人可独立实施任何民事法律行为', '限制行为能力人可实施与其智力相适应的民事法律行为', '无行为能力人的民事法律行为由法定代理人代理'],
    ARRAY['10岁儿童可以买文具（与智力相适应），但不能独立买房'],
    ARRAY['混淆年龄界限', '认为限制行为能力人完全不能实施法律行为'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000006',
    '42000000-0000-0000-0000-000000000002',
    '法人的分类',
    '法人是具有民事权利能力和民事行为能力，依法独立享有民事权利和承担民事义务的组织。分为营利法人、非营利法人和特别法人。',
    ARRAY['营利法人：公司、企业', '非营利法人：事业单位、社会团体、基金会', '特别法人：机关法人、农村集体经济组织法人'],
    ARRAY['法人独立承担民事责任', '法人以其全部财产对债务负责', '法人设立需依法登记'],
    ARRAY['有限责任公司是营利法人，红十字会是非营利法人'],
    ARRAY['混淆法人和自然人', '认为法人不承担责任'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_003 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000007',
    '42000000-0000-0000-0000-000000000003',
    '物权与债权的区别',
    '物权是直接支配特定物的权利，具有绝对性、排他性；债权是请求特定人为或不为一定行为的权利，具有相对性。',
    ARRAY['物权：所有权、用益物权、担保物权', '债权：合同之债、侵权之债、不当得利、无因管理'],
    ARRAY['物权具有排他性，一物一权', '债权具有相对性，仅对债务人有效', '物权优先于债权'],
    ARRAY['甲对房屋享有所有权（物权），乙对甲享有租金请求权（债权）'],
    ARRAY['混淆物权和债权', '不理解物权的排他性'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000008',
    '42000000-0000-0000-0000-000000000003',
    '人身权的特征',
    '人身权是与人身不可分离、不直接具有财产内容的民事权利，包括人格权（生命权、健康权、姓名权等）和身份权（配偶权、监护权等）。',
    ARRAY['人格权：生命权、健康权、姓名权、肖像权、名誉权、隐私权', '身份权：配偶权、亲权、监护权'],
    ARRAY['人身权不可转让', '人身权不可放弃', '人身权不可继承'],
    ARRAY['未经同意使用他人肖像用于商业广告，侵犯肖像权'],
    ARRAY['混淆人格权和身份权', '认为人身权可以转让'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000009',
    '42000000-0000-0000-0000-000000000003',
    '知识产权的特征',
    '知识产权是对智力成果享有的专有权利，包括著作权、专利权、商标权等，具有专有性、地域性、时间性。',
    ARRAY['专有性：权利人独占使用', '地域性：仅在授予国有效', '时间性：保护期限有限'],
    ARRAY['知识产权需依法确认', '侵犯知识产权需承担法律责任', '知识产权可以转让和许可使用'],
    ARRAY['发明专利保护20年，实用新型和外观设计专利保护10年'],
    ARRAY['忽视知识产权的时间性', '混淆不同类型知识产权的保护期限'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_004 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000010',
    '42000000-0000-0000-0000-000000000004',
    '法律行为的有效要件',
    '民事法律行为有效需满足三要件：行为人具有相应民事行为能力；意思表示真实；不违反法律强制性规定和公序良俗。',
    ARRAY['要件一：行为能力', '要件二：意思真实', '要件三：内容合法'],
    ARRAY['三要件同时满足才有效', '欠缺任一要件导致无效或可撤销', '意思表示瑕疵包括欺诈、胁迫、重大误解'],
    ARRAY['10岁儿童购买高价电脑，因欠缺行为能力，法律行为可撤销'],
    ARRAY['混淆无效和可撤销', '忽视意思表示真实性'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000011',
    '42000000-0000-0000-0000-000000000004',
    '无效、可撤销、效力待定',
    '民事法律行为根据效力瑕疵分为：无效（自始无效）、可撤销（撤销前有效）、效力待定（需追认）。',
    ARRAY['无效：违反强制性规定、违背公序良俗、虚假表示', '可撤销：欺诈、胁迫、重大误解、显失公平', '效力待定：限制行为能力人实施的超范围行为、无权代理'],
    ARRAY['无效自始无效，不能补正', '可撤销行为在撤销前有效', '效力待定行为可经追认生效'],
    ARRAY['甲胁迫乙签订合同，乙可在一年内撤销'],
    ARRAY['混淆三种效力类型', '不理解撤销权的除斥期间'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000012',
    '42000000-0000-0000-0000-000000000004',
    '代理制度',
    '代理是代理人在代理权限内以被代理人名义实施民事法律行为，法律后果直接归属于被代理人。分为委托代理、法定代理、指定代理。',
    ARRAY['委托代理：基于被代理人授权', '法定代理：基于法律规定（父母代理子女）', '指定代理：基于人民法院或有关机关指定'],
    ARRAY['代理需有代理权', '代理人需以被代理人名义行事', '代理行为后果归属被代理人', '无权代理需追认'],
    ARRAY['父母作为未成年子女的法定代理人签订教育服务合同'],
    ARRAY['混淆代理和委托', '不理解无权代理的后果'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_005 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000013',
    '42000000-0000-0000-0000-000000000005',
    '合同的订立过程',
    '合同订立包括要约和承诺两个阶段。要约是希望与他人订立合同的意思表示，承诺是受要约人同意要约的意思表示。',
    ARRAY['要约：内容具体确定、表明经承诺即受约束', '承诺：承诺生效时合同成立'],
    ARRAY['要约可撤回或撤销（限制条件）', '承诺需在要约有效期内作出', '承诺内容应与要约一致'],
    ARRAY['甲在网站标价出售商品（要约邀请），乙下单（要约），甲确认发货（承诺）'],
    ARRAY['混淆要约和要约邀请', '不理解承诺生效时间'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000014',
    '42000000-0000-0000-0000-000000000005',
    '合同的履行原则',
    '合同履行应遵守全面履行原则（按约定履行）、诚实信用原则、情势变更原则等。',
    ARRAY['全面履行：标的、质量、数量、期限、地点、方式', '诚实信用：不损害对方利益', '情势变更：重大变化可变更或解除'],
    ARRAY['当事人应全面履行合同义务', '不得擅自变更或解除合同', '履行中应协作配合'],
    ARRAY['甲与乙约定交付100件商品，甲应按质按量按时交付，不得少交或延迟'],
    ARRAY['理解全面履行的具体要求', '忽视附随义务'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000015',
    '42000000-0000-0000-0000-000000000005',
    '违约责任',
    '违约责任是当事人不履行合同义务或履行不符合约定时应承担的民事责任，包括继续履行、采取补救措施、赔偿损失等。',
    ARRAY['继续履行：要求违约方履行合同', '赔偿损失：包括实际损失和可得利益损失', '违约金：约定或法定', '定金：双倍返还'],
    ARRAY['违约责任采用严格责任（不考虑过错）', '可约定违约金', '违约金过高可请求调整'],
    ARRAY['甲延迟交货，乙可要求甲继续交货并赔偿因延迟导致的损失'],
    ARRAY['混淆违约责任和侵权责任', '不理解可得利益损失的计算'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- T_LAW_006 的概念（3个）
INSERT INTO concepts (
    concept_id, topic_id, concept_name, explanation,
    formulas, rules, examples, common_pitfalls,
    created_at, updated_at
) VALUES
(
    '52000000-0000-0000-0000-000000000016',
    '42000000-0000-0000-0000-000000000006',
    '侵权行为的构成要件',
    '一般侵权行为需满足四要件：行为违法、损害事实、因果关系、主观过错。',
    ARRAY['违法行为：违反法定义务', '损害事实：财产或人身损害', '因果关系：违法行为与损害的因果联系', '主观过错：故意或过失'],
    ARRAY['四要件同时满足构成侵权', '特殊侵权可能不要求过错（无过错责任）', '举证责任分配因侵权类型而异'],
    ARRAY['甲驾车闯红灯撞伤乙，甲的违法行为、乙的伤害、二者因果关系及甲的过失构成侵权'],
    ARRAY['混淆一般侵权和特殊侵权', '忽视因果关系的证明'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000017',
    '42000000-0000-0000-0000-000000000006',
    '归责原则',
    '侵权责任归责原则包括过错责任原则（一般原则）、无过错责任原则（特殊情形）和公平责任原则（补充原则）。',
    ARRAY['过错责任：需证明侵权人有过错', '无过错责任：不考虑过错（产品责任、环境污染、高度危险作业）', '公平责任：双方均无过错时根据公平原则分担损失'],
    ARRAY['过错责任是基本原则', '无过错责任适用于法律明确规定的情形', '公平责任适用极少'],
    ARRAY['宠物狗伤人，饲养人承担无过错责任，即使饲养人无过错也需赔偿'],
    ARRAY['混淆不同归责原则的适用范围', '不理解举证责任倒置'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '52000000-0000-0000-0000-000000000018',
    '42000000-0000-0000-0000-000000000006',
    '损害赔偿的范围',
    '侵权损害赔偿应全面赔偿受害人的损失，包括财产损失（直接损失和间接损失）和精神损害。',
    ARRAY['财产损失：直接损失（修理费、医疗费）、间接损失（误工费、护理费）', '精神损害：精神痛苦的抚慰金'],
    ARRAY['全面赔偿原则', '损益相抵规则', '过失相抵规则（受害人有过错可减轻责任）'],
    ARRAY['甲撞伤乙，赔偿医疗费、误工费、护理费，并因造成乙残疾支付精神损害抚慰金'],
    ARRAY['忽视间接损失', '不理解精神损害赔偿的适用条件'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- =====================================================
-- 第四部分：创建6条主题依赖关系
-- =====================================================

INSERT INTO topic_dependencies (prerequisite_topic_id, dependent_topic_id, strength) VALUES
('42000000-0000-0000-0000-000000000001', '42000000-0000-0000-0000-000000000002', 0.85),  -- 民事法律关系 → 民事主体
('42000000-0000-0000-0000-000000000001', '42000000-0000-0000-0000-000000000003', 0.75),  -- 民事法律关系 → 民事权利类型
('42000000-0000-0000-0000-000000000002', '42000000-0000-0000-0000-000000000004', 0.80),  -- 民事主体 → 民事法律行为
('42000000-0000-0000-0000-000000000003', '42000000-0000-0000-0000-000000000004', 0.70),  -- 民事权利类型 → 民事法律行为
('42000000-0000-0000-0000-000000000004', '42000000-0000-0000-0000-000000000005', 0.90),  -- 民事法律行为 → 合同法基础
('42000000-0000-0000-0000-000000000004', '42000000-0000-0000-0000-000000000006', 0.75)   -- 民事法律行为 → 侵权责任
ON CONFLICT (prerequisite_topic_id, dependent_topic_id) DO NOTHING;

-- =====================================================
-- 第五部分：创建3个记忆辅助示例
-- =====================================================

-- 记忆辅助1：法律行为有效三要件（Number Pattern）
INSERT INTO mnemonic_devices (
    mnemonic_id, tenant_id, concept_id, strategy_type,
    content, effectiveness_rating, usage_count,
    created_at, updated_at
) VALUES (
    '72000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '52000000-0000-0000-0000-000000000010',
    'number',
    '{
        "numbers": [3],
        "pattern": "三要件",
        "memory_phrase": "能力、真实、合法——三件齐全行为有效",
        "explanation": "记住法律行为有效的三个必备要件：行为能力、意思真实、内容合法"
    }',
    0.88,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (mnemonic_id) DO NOTHING;

-- 记忆辅助2：侵权责任四要件（Acronym）
INSERT INTO mnemonic_devices (
    mnemonic_id, tenant_id, concept_id, strategy_type,
    content, effectiveness_rating, usage_count,
    created_at, updated_at
) VALUES (
    '72000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '52000000-0000-0000-0000-000000000016',
    'acronym',
    '{
        "acronym": "违损因过",
        "full_terms": ["违法行为", "损害事实", "因果关系", "主观过错"],
        "memory_tip": "侵权四要件：违（法）损（害）因（果）过（错）",
        "explanation": "一般侵权行为的四个构成要件缩略为'违损因过'"
    }',
    0.85,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (mnemonic_id) DO NOTHING;

-- 记忆辅助3：物权与债权的区别（Comparison Table）
INSERT INTO mnemonic_devices (
    mnemonic_id, tenant_id, concept_id, strategy_type,
    content, effectiveness_rating, usage_count,
    created_at, updated_at
) VALUES (
    '72000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000001',
    '52000000-0000-0000-0000-000000000007',
    'comparison',
    '{
        "items": ["物权", "债权"],
        "dimensions": [
            {
                "name": "性质",
                "values": ["绝对权（对世权）", "相对权（对人权）"]
            },
            {
                "name": "客体",
                "values": ["特定物", "特定人的行为"]
            },
            {
                "name": "排他性",
                "values": ["具有排他性，一物一权", "不具有排他性，同一标的可多个债权"]
            },
            {
                "name": "优先性",
                "values": ["物权优先于债权", "债权后于物权"]
            }
        ],
        "memory_tip": "物权对物，债权对人；物权绝对，债权相对；物权排他，债权共存；物权优先，债权在后"
    }',
    0.90,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (mnemonic_id) DO NOTHING;

-- =====================================================
-- 第六部分：创建5个权威来源（法律领域）
-- =====================================================

INSERT INTO authoritative_sources (
    source_id, tenant_id, source_name, source_type,
    url, reliability_score, domain_tags,
    created_at, updated_at
) VALUES
(
    '82000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '中华人民共和国民法典',
    'legal_document',
    'http://www.npc.gov.cn/npc/c30834/202006/75ba6483b8344591abd07917e1d25cc8.shtml',
    0.98,
    ARRAY['民法', '法律法规', '基本法律'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '82000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '最高人民法院民法典理解与适用',
    'legal_commentary',
    'https://www.court.gov.cn/',
    0.95,
    ARRAY['民法', '司法解释', '案例指导'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '82000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000001',
    '中国法律服务网',
    'online_database',
    'https://www.12348.gov.cn/',
    0.90,
    ARRAY['法律服务', '法律咨询', '法律法规查询'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '82000000-0000-0000-0000-000000000004',
    '10000000-0000-0000-0000-000000000001',
    '北大法宝 - 法律法规数据库',
    'online_database',
    'https://www.pkulaw.com/',
    0.92,
    ARRAY['法律数据库', '法规检索', '案例分析'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '82000000-0000-0000-0000-000000000005',
    '10000000-0000-0000-0000-000000000001',
    '中国法院网 - 案例库',
    'case_database',
    'https://www.chinacourt.org/',
    0.93,
    ARRAY['司法案例', '裁判文书', '法律适用'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (source_id) DO NOTHING;

-- =====================================================
-- 完成
-- =====================================================
