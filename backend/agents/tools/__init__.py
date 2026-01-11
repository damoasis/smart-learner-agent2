"""
工具函数集合

所有工具函数使用@tool装饰器，可被LangGraph ReAct Agent调用。
"""

from backend.agents.tools.socratic_teacher_tools import (
    evaluate_knowledge_baseline,
    search_related_concepts,
    generate_socratic_explanation,
    generate_comprehension_questions,
    generate_adaptive_followup
)

from backend.agents.tools.knowledge_assessor_tools import (
    extract_key_points,
    identify_misunderstandings,
    assess_understanding_level,
    decide_next_action
)

from backend.agents.tools.progress_tracker_tools import (
    query_mastery_records,
    query_knowledge_gaps,
    calculate_efficiency_metrics,
    recommend_review_topics,
    recommend_next_topics
)

from backend.agents.tools.content_validator_tools import (
    search_verification_sources,
    extract_web_content,
    validate_against_sources,
    save_verified_content
)

from backend.agents.tools.mnemonic_generator_tools import (
    analyze_concept_features,
    select_mnemonic_strategy,
    generate_acronym,
    generate_analogy,
    generate_comparison,
    generate_visual,
    generate_number_pattern,
    save_mnemonic_device
)

__all__ = [
    # SocraticTeacher工具
    "evaluate_knowledge_baseline",
    "search_related_concepts",
    "generate_socratic_explanation",
    "generate_comprehension_questions",
    "generate_adaptive_followup",
    
    # KnowledgeAssessor工具
    "extract_key_points",
    "identify_misunderstandings",
    "assess_understanding_level",
    "decide_next_action",
    
    # ProgressTracker工具
    "query_mastery_records",
    "query_knowledge_gaps",
    "calculate_efficiency_metrics",
    "recommend_review_topics",
    "recommend_next_topics",
    
    # ContentValidator工具
    "search_verification_sources",
    "extract_web_content",
    "validate_against_sources",
    "save_verified_content",
    
    # MnemonicGenerator工具
    "analyze_concept_features",
    "select_mnemonic_strategy",
    "generate_acronym",
    "generate_analogy",
    "generate_comparison",
    "generate_visual",
    "generate_number_pattern",
    "save_mnemonic_device"
]
"""
Agent工具集导出
"""

from .socratic_teacher_tools import (
    evaluate_knowledge_baseline,
    search_related_concepts,
    generate_socratic_explanation,
    generate_comprehension_questions,
    generate_adaptive_followup
)

from .knowledge_assessor_tools import (
    extract_key_points,
    identify_misunderstandings,
    assess_understanding_level,
    decide_next_action
)

__all__ = [
    # SocraticTeacher tools
    "evaluate_knowledge_baseline",
    "search_related_concepts",
    "generate_socratic_explanation",
    "generate_comprehension_questions",
    "generate_adaptive_followup",
    # KnowledgeAssessor tools
    "extract_key_points",
    "identify_misunderstandings",
    "assess_understanding_level",
    "decide_next_action",
]
