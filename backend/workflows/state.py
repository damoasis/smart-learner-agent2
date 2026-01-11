"""

LangGraph工作流状态模型



该模块定义了苏格拉底教学工作流的状态模型，包含会话信息、交互上下文、

知识检索结果、教学生成内容、理解检查和流程控制字段。

"""



from typing import List, Optional, Dict, Any, Literal

from datetime import datetime

from uuid import UUID

from pydantic import BaseModel, Field





class RetrievedConcept(BaseModel):

    """检索到的概念信息"""

    concept_id: UUID

    concept_name: str

    explanation: Optional[str] = None

    formulas: Optional[str] = None

    rules: Optional[str] = None

    similarity_score: float = Field(..., ge=0.0, le=1.0, description="相似度分数（0-1）")





class ComprehensionQuestion(BaseModel):

    """理解检查问题"""

    question_text: str

    expected_key_points: Optional[List[str]] = Field(default=None, description="期望的关键点")





class TeachingState(BaseModel):

    """

    苏格拉底教学工作流状态模型

    

    该状态在LangGraph工作流中流转，包含会话全生命周期的所有关键信息。

    """

    

    # ========== 会话信息 ==========

    session_id: Optional[UUID] = Field(default=None, description="当前会话ID")

    learner_id: UUID = Field(..., description="学习者ID")

    goal_id: UUID = Field(..., description="学习目标ID")

    tenant_id: UUID = Field(..., description="租户ID")

    

    # ========== 交互上下文 ==========

    current_topic_id: Optional[UUID] = Field(default=None, description="当前学习主题ID")

    question_text: Optional[str] = Field(default=None, description="学习者提出的问题")

    initial_understanding: Optional[str] = Field(

        default=None,

        description="学习者对该主题的初始理解"

    )

    

    # ========== 学习者上下文 ==========

    learner_name: Optional[str] = Field(default=None, description="学习者姓名")

    learner_preferences: Optional[Dict[str, Any]] = Field(

        default=None,

        description="学习偏好配置"

    )

    mastered_topics: List[UUID] = Field(

        default_factory=list,

        description="已掌握的主题ID列表"

    )

    knowledge_gaps: List[Dict[str, Any]] = Field(

        default_factory=list,

        description="已识别的知识缺口"

    )

    

    # ========== 知识检索结果 ==========

    retrieved_concepts: List[RetrievedConcept] = Field(

        default_factory=list,

        description="检索到的相关概念列表"

    )

    needs_validation: bool = Field(

        default=False,

        description="是否需要内容验证"

    )

    validation_items: List[str] = Field(

        default_factory=list,

        description="待验证项列表"

    )

    validation_result: Optional[Dict[str, Any]] = Field(

        default=None,

        description="验证结果"

    )

    verified_sources: List[Dict[str, Any]] = Field(

        default_factory=list,

        description="引用来源列表"

    )

    skip_validation: bool = Field(

        default=False,

        description="跳过验证标志"

    )

    

    # ========== 知识基线评估 ==========

    baseline_level: Optional[Literal["beginner", "intermediate", "advanced"]] = Field(

        default=None,

        description="知识基线水平"

    )

    baseline_assessment: Optional[str] = Field(

        default=None,

        description="基线评估详情"

    )

    

    # ========== 教学生成内容 ==========

    explanation: Optional[str] = Field(default=None, description="生成的解释内容")

    teaching_method: str = Field(default="socratic", description="使用的教学方法")

    teaching_mode_id: Optional[UUID] = Field(

        default=None,

        description="当前使用的教学模式ID"

    )

    available_teaching_modes: List[str] = Field(

        default_factory=list,

        description="可用的教学模式列表"

    )

    needs_mnemonic: bool = Field(

        default=False,

        description="是否需要记忆辅助"

    )

    mnemonic_strategy: Optional[str] = Field(

        default=None,

        description="选择的记忆策略（acronym/comparison/analogy/visual/number）"

    )

    generated_mnemonic: Optional[Dict[str, Any]] = Field(

        default=None,

        description="生成的记忆辅助内容"

    )

    mnemonic_devices: List[Dict[str, Any]] = Field(

        default_factory=list,

        description="生成的记忆辅助列表"

    )

    recommended_strategy: Optional[str] = Field(

        default=None,

        description="推荐的记忆策略"

    )

    skip_mnemonic: bool = Field(

        default=False,

        description="跳过记忆辅助标志"

    )

    

    # ========== 理解检查 ==========

    comprehension_questions: List[ComprehensionQuestion] = Field(

        default_factory=list,

        description="生成的理解检查问题列表"

    )

    learner_response: Optional[str] = Field(default=None, description="学习者的回答")

    assessment_result: Optional[Literal[

        "fully_understood",

        "partially_understood",

        "not_understood"

    ]] = Field(default=None, description="评估结果")

    assessment_details: Optional[str] = Field(

        default=None,

        description="评估详情和反馈"

    )

    

    # ========== 信心等级 ==========

    confidence_level: Optional[Literal["low", "medium", "medium_high", "high"]] = Field(

        default=None,

        description="学习者对该主题的信心等级"

    )

    key_points_understood: List[str] = Field(

        default_factory=list,

        description="已理解的关键点"

    )

    misunderstandings: List[str] = Field(

        default_factory=list,

        description="发现的误解"

    )

    

    # ========== 流程控制 ==========

    intent: Optional[Literal["learn", "practice", "progress", "review", "other"]] = Field(

        default=None,

        description="用户意图类型"

    )

    next_action: Optional[Literal["continue", "retry", "end", "adaptive_followup"]] = Field(

        default=None,

        description="下一步动作"

    )

    retry_count: int = Field(default=0, description="重试次数")

    max_retries: int = Field(default=3, description="最大重试次数")

    

    # ========== 推荐和分析（阶段二新增） ==========

    recommended_topics: List[Dict[str, Any]] = Field(

        default_factory=list,

        description="推荐的下一个主题列表"

    )

    review_reminders: List[Dict[str, Any]] = Field(

        default_factory=list,

        description="复习提醒列表"

    )

    learning_efficiency: Optional[Dict[str, Any]] = Field(

        default=None,

        description="学习效率分析结果"

    )

    

    # ========== 子Agent调用追踪（ReAct模式新增） ==========

    sub_agent_calls: List[Dict[str, Any]] = Field(

        default_factory=list,

        description="子Agent调用历史记录"

    )

    current_sub_agent: Optional[str] = Field(

        default=None,

        description="当前正在执行的子Agent名称"

    )

    sub_agent_results: Dict[str, Any] = Field(

        default_factory=dict,

        description="子Agent执行结果缓存"

    )

    

    # ========== 元数据 ==========

    timestamp: datetime = Field(default_factory=datetime.now, description="当前时间戳")

    workflow_stage: Optional[str] = Field(

        default="initialized",

        description="当前工作流阶段"

    )

    error_message: Optional[str] = Field(default=None, description="错误消息")

    

    # ========== 数据库记录ID ==========

    question_id: Optional[UUID] = Field(default=None, description="questions_asked记录ID")

    explanation_id: Optional[UUID] = Field(default=None, description="explanations记录ID")

    check_id: Optional[UUID] = Field(default=None, description="comprehension_checks记录ID")

    

    class Config:

        # 允许任意类型（用于UUID等）

        arbitrary_types_allowed = True

        # JSON序列化配置

        json_encoders = {

            datetime: lambda v: v.isoformat(),

            UUID: lambda v: str(v)

        }





class WorkflowConfig(BaseModel):

    """工作流配置"""

    

    # OpenAI配置

    openai_api_key: str

    openai_model: str = Field(default="gpt-4-turbo-preview", description="LLM模型")

    openai_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")

    openai_max_tokens: int = Field(default=500, gt=0, description="最大token数")

    

    # 向量检索配置

    vector_search_top_k: int = Field(default=5, gt=0, description="返回最相关的概念数")

    vector_similarity_threshold: float = Field(

        default=0.7,

        ge=0.0,

        le=1.0,

        description="相似度阈值"

    )

    

    # 教学配置

    explanation_max_length: int = Field(default=200, gt=0, description="解释最大字数")

    num_comprehension_questions: int = Field(

        default=2,

        ge=1,

        le=5,

        description="理解检查问题数量"

    )

    max_retry_attempts: int = Field(default=3, gt=0, description="最大重试次数")

    

    # 数据库配置

    database_url: str

    

    class Config:

        # 环境变量前缀

        env_prefix = ""





def create_initial_state(

    learner_id: UUID,

    goal_id: UUID,

    tenant_id: UUID,

    question_text: Optional[str] = None,

    initial_understanding: Optional[str] = None

) -> TeachingState:

    """

    创建初始的教学状态

    

    Args:

        learner_id: 学习者ID

        goal_id: 学习目标ID

        tenant_id: 租户ID

        question_text: 初始问题（可选）

        initial_understanding: 初始理解（可选）

    

    Returns:

        初始化的TeachingState对象

    """

    return TeachingState(

        learner_id=learner_id,

        goal_id=goal_id,

        tenant_id=tenant_id,

        question_text=question_text,

        initial_understanding=initial_understanding,

        workflow_stage="initialized"

    )

