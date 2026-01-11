"""
智能学习助手CLI主程序

提供交互式命令行界面，允许学习者进行苏格拉底式学习会话。
"""

import os
import sys
from uuid import UUID
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.services.vector_search import create_vector_search_service
from backend.workflows.teaching_workflow import create_teaching_workflow
from backend.workflows.state import TeachingState
from backend.services.database import LearnerService, DatabaseService
from backend.models.learner import Learner, LearningGoal


# 加载环境变量
load_dotenv()

# 初始化Rich Console
console = Console()


class SmartLearnerCLI:
    """智能学习助手CLI应用"""
    
    def __init__(self):
        """初始化CLI应用"""
        # 初始化数据库连接
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            console.print("[red]错误：DATABASE_URL环境变量未设置[/red]")
            sys.exit(1)
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 租户ID（阶段一使用固定租户）
        self.tenant_id = UUID(os.getenv("DEFAULT_TENANT_ID", "00000000-0000-0000-0000-000000000001"))
        
        # 当前会话状态
        self.current_state: Optional[TeachingState] = None
        self.learner_id: Optional[UUID] = None
        self.goal_id: Optional[UUID] = None
        self.teaching_mode: str = "socratic"  # 默认苏格拉底式
    
    def show_welcome(self):
        """显示欢迎界面"""
        welcome_text = """
# 🎓 智能学习助手 (Smart Learner Agent)

欢迎使用基于苏格拉底教学法的智能学习系统！

## 功能特点：
- 📚 个性化教学：根据你的水平调整解释深度
- 💡 引导式学习：通过提问帮助你深入理解
- 📊 进度追踪：实时追踪你的学习进度
- 🔍 智能检索：基于向量语义搜索相关知识

## 支持的命令：
- `/progress` - 查看学习进度（含效率分析、复习提醒、推荐）
- `/mode` - 选择教学模式（苏格拉底式/讲授式）
- `/mnemonic` - 显示记忆辅助
- `/sources` - 显示来源引用
- `/help` - 显示帮助信息
- `/end` - 结束当前会话

让我们开始学习吧！
        """
        console.print(Panel(Markdown(welcome_text), title="欢迎", border_style="cyan"))
    
    def select_learner(self) -> Optional[UUID]:
        """
        选择或创建学习者
        
        Returns:
            学习者ID，如果取消则返回None
        """
        console.print("\n[bold cyan]步骤 1: 选择学习者[/bold cyan]")
        
        email = Prompt.ask("请输入你的邮箱地址")
        
        # 查询学习者
        with self.SessionLocal() as session:
            learner_service = LearnerService(DatabaseService(session))
            learner = learner_service.get_learner_by_email(self.tenant_id, email)
            
            if learner:
                console.print(f"[green]找到学习者：{learner.name}[/green]")
                return learner.learner_id
            else:
                console.print("[yellow]未找到该邮箱对应的学习者[/yellow]")
                
                if Confirm.ask("是否创建新的学习者账户？"):
                    name = Prompt.ask("请输入你的姓名")
                    
                    # 创建新学习者
                    new_learner = Learner(
                        learner_id=UUID(int=0),  # 临时ID
                        tenant_id=self.tenant_id,
                        name=name,
                        email=email,
                        native_language="zh-CN"
                    )
                    
                    db_service = DatabaseService(session)
                    created_learner = db_service.create(new_learner)
                    session.commit()
                    
                    console.print(f"[green]成功创建学习者：{created_learner.name}[/green]")
                    return created_learner.learner_id
                else:
                    return None
    
    def select_goal(self, learner_id: UUID) -> Optional[UUID]:
        """
        选择学习目标
        
        Args:
            learner_id: 学习者ID
        
        Returns:
            学习目标ID，如果取消则返回None
        """
        console.print("\n[bold cyan]步骤 2: 选择学习目标[/bold cyan]")
        
        with self.SessionLocal() as session:
            learner_service = LearnerService(DatabaseService(session))
            active_goal = learner_service.get_active_learning_goal(learner_id)
            
            if active_goal:
                console.print(f"[green]当前活跃目标：{active_goal.goal_name}[/green]")
                
                if Confirm.ask("使用此学习目标？", default=True):
                    return active_goal.goal_id
            
            # TODO: 这里可以添加创建新目标的功能
            console.print("[yellow]暂不支持创建新的学习目标，请先在数据库中设置[/yellow]")
            return None
    
    def start_session(self):
        """开始新的学习会话"""
        # 选择学习者
        self.learner_id = self.select_learner()
        if not self.learner_id:
            console.print("[red]未选择学习者，退出[/red]")
            return False
        
        # 选择学习目标
        self.goal_id = self.select_goal(self.learner_id)
        if not self.goal_id:
            console.print("[red]未选择学习目标，退出[/red]")
            return False
        
        console.print("\n[bold green]✓ 会话准备就绪！[/bold green]")
        console.print("[dim]你可以开始提问了。输入 /help 查看可用命令。[/dim]\n")
        
        return True
    
    def handle_question(self, question: str):
        """
        处理学习者的问题
        
        Args:
            question: 学习者的问题
        """
        with self.SessionLocal() as session:
            # 创建服务
            vector_search = create_vector_search_service(session)
            workflow = create_teaching_workflow(session, vector_search)
            
            # 执行工作流（到wait_for_response节点）
            console.print("[dim]正在思考...[/dim]")
            
            try:
                state = workflow.run(
                    learner_id=self.learner_id,
                    goal_id=self.goal_id,
                    tenant_id=self.tenant_id,
                    question_text=question
                )

                # 显示解释(若有)
                self._display_explanation(state)

                # 如果生成了理解检查问题,进入交互式评估流程
                if state.comprehension_questions:
                    self._display_comprehension_questions(state)

                    learner_response = Prompt.ask("\n[bold cyan]你的回答[/bold cyan]")

                    console.print("[dim]正在评估你的回答...[/dim]")
                    final_state = workflow.continue_with_response(state, learner_response)

                    self._display_assessment_feedback(final_state)
                    self.current_state = final_state
                else:
                    # 非交互型请求(如进度/评估/复习等): 直接保存当前状态
                    if state.assessment_result:
                        self._display_assessment_feedback(state)
                    self.current_state = state

            except Exception as e:
                console.print(f"[red]错误：{str(e)}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    def _display_explanation(self, state: TeachingState):
        """显示解释内容"""
        if state.explanation:
            console.print("\n" + "="*60)
            console.print(Panel(
                state.explanation,
                title="💡 解释",
                border_style="blue"
            ))
    
    def _display_comprehension_questions(self, state: TeachingState):
        """显示理解检查问题"""
        if state.comprehension_questions:
            console.print("\n[bold yellow]📝 理解检查：[/bold yellow]")
            for i, q in enumerate(state.comprehension_questions, 1):
                console.print(f"  {i}. {q.question_text}")
    
    def _display_assessment_feedback(self, state: TeachingState):
        """显示评估反馈"""
        console.print("\n" + "="*60)
        
        result_map = {
            "fully_understood": ("✅ 完全理解", "green"),
            "partially_understood": ("⚠️  部分理解", "yellow"),
            "not_understood": ("❌ 未理解", "red")
        }
        
        result_text, color = result_map.get(
            state.assessment_result,
            ("未知", "white")
        )
        
        console.print(f"[bold {color}]{result_text}[/bold {color}]")
        
        if state.assessment_details:
            console.print(f"[dim]{state.assessment_details}[/dim]")
        
        if state.confidence_level:
            console.print(f"信心等级：[bold]{state.confidence_level}[/bold]")
    
    def show_progress(self):
        """显示学习进度（阶段二增强：含效率分析、复习提醒、推荐）"""
        if not self.learner_id:
            console.print("[red]请先开始一个学习会话[/red]")
            return
        
        with self.SessionLocal() as session:
            from backend.agents.react.progress_tracker_agent import ProgressTracker
            tracker = ProgressTracker(session)
            
            try:
                # 基础进度摘要
                progress = tracker.generate_progress_summary(
                    self.learner_id,
                    self.tenant_id
                )
                
                # 学习效率分析（阶段二新增）
                efficiency = tracker.analyze_learning_efficiency(
                    self.learner_id,
                    self.tenant_id,
                    time_range_days=30  # 最近30天
                )
                
                # 复习提醒（阶段二新增）
                reviews = tracker.get_review_recommendations(
                    self.learner_id,
                    self.tenant_id,
                    max_items=5
                )
                
                # 下一步推荐（阶段二新增）
                recommendations = tracker.recommend_next_topics(
                    self.learner_id,
                    self.tenant_id,
                    self.goal_id,
                    max_recommendations=3
                )
                
                console.print("\n[bold cyan]📊 学习进度总览[/bold cyan]\n")
                
                # 1. 统计摘要
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("指标")
                table.add_column("数值")
                
                table.add_row("已掌握主题", str(progress["total_mastered_topics"]))
                table.add_row("高信心主题", str(progress["high_confidence_topics"]))
                table.add_row("知识缺口", str(progress["total_knowledge_gaps"]))
                
                console.print(table)
                
                # 2. 学习效率分析（阶段二新增）
                console.print("\n[bold cyan]⚡ 学习效率分析（最近30天）[/bold cyan]")
                eff_table = Table(show_header=True, header_style="bold yellow")
                eff_table.add_column("指标")
                eff_table.add_column("数值")
                
                eff_table.add_row("平均掌握时间", f"{efficiency['average_mastery_time_days']:.1f}天")
                eff_table.add_row("首次正确率", f"{efficiency['first_time_correct_rate']*100:.0f}%")
                eff_table.add_row("总学习时长", f"{efficiency['total_learning_hours']:.1f}小时")
                eff_table.add_row("学习节奏", efficiency['learning_pace'])
                
                console.print(eff_table)
                
                if efficiency['improvement_suggestions']:
                    console.print("\n[bold yellow]💡 改进建议：[/bold yellow]")
                    for suggestion in efficiency['improvement_suggestions']:
                        console.print(f"  • {suggestion}")
                
                # 3. 复习提醒（阶段二新增）
                if reviews:
                    console.print("\n[bold orange]📅 需要复习的主题：[/bold orange]")
                    for review in reviews:
                        urgency = "🔴" if review['urgency_score'] > 0.7 else "🟡" if review['urgency_score'] > 0.5 else "🟢"
                        console.print(f"  {urgency} {review['topic_name']}")
                        console.print(f"     距上次复习：{review['days_since_review']}天 | 建议：{review['recommended_action']}")
                
                # 4. 已掌握的主题
                if progress["mastery_by_confidence_level"]["high"]:
                    console.print("\n[bold green]🎯 高信心主题：[/bold green]")
                    for topic in progress["mastery_by_confidence_level"]["high"][:5]:
                        console.print(f"  • {topic['topic_name']}")
                
                # 5. 知识缺口
                if progress["knowledge_gaps"]:
                    console.print("\n[bold red]⚠️  知识缺口：[/bold red]")
                    for gap in progress["knowledge_gaps"][:3]:
                        console.print(f"  • {gap['topic_name']}: {gap['description']}")
                
                # 6. 下一步学习推荐（阶段二新增）
                if recommendations:
                    console.print("\n[bold cyan]🎯 推荐学习的主题：[/bold cyan]")
                    for i, rec in enumerate(recommendations, 1):
                        console.print(f"\n  {i}. [bold]{rec['topic_name']}[/bold]")
                        console.print(f"     推荐理由：{rec['recommendation_reason']}")
                        console.print(f"     难度：{rec['estimated_difficulty']} | 预计时长：{rec['estimated_time_hours']}小时")
                        console.print(f"     推荐评分：{rec['recommendation_score']:.2f}")
                
            except Exception as e:
                console.print(f"[red]获取进度失败：{str(e)}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    def select_teaching_mode(self):
        """选择教学模式（阶段二新增）"""
        console.print("\n[bold cyan]📚 选择教学模式[/bold cyan]\n")
        
        mode_info = {
            "socratic": {
                "name": "苏格拉底式（引导式）",
                "description": "通过提问引导你深入思考，适合概念理解",
                "features": ["互动性高", "深入探索", "适合新概念"]
            },
            "lecture": {
                "name": "讲授式（系统化）",
                "description": "系统化讲解知识体系，适合快速学习",
                "features": ["结构清晰", "内容全面", "适合高级学习者"]
            }
        }
        
        # 显示当前模式
        current_mode_name = mode_info[self.teaching_mode]["name"]
        console.print(f"[green]当前模式：{current_mode_name}[/green]\n")
        
        # 显示模式选项
        console.print("[bold]可用模式：[/bold]")
        console.print("  1. 苏格拉底式（引导式）- 通过提问引导思考")
        console.print("  2. 讲授式（系统化）- 系统化讲解知识")
        
        choice = Prompt.ask("\n选择模式 (1/2)", choices=["1", "2"], default="1")
        
        new_mode = "socratic" if choice == "1" else "lecture"
        
        if new_mode != self.teaching_mode:
            self.teaching_mode = new_mode
            console.print(f"\n[green]✓ 已切换到：{mode_info[new_mode]['name']}[/green]")
        else:
            console.print(f"\n[yellow]保持当前模式：{mode_info[new_mode]['name']}[/yellow]")
    
    def show_mnemonic(self):
        """显示记忆辅助（阶段二新增）"""
        if not self.current_state or not self.current_state.generated_mnemonic:
            console.print("[yellow]当前没有可用的记忆辅助[/yellow]")
            console.print("[dim]提示：在学习过程中，系统会自动为重要概念生成记忆辅助[/dim]")
            return
        
        mnemonic = self.current_state.generated_mnemonic
        strategy = self.current_state.mnemonic_strategy
        
        console.print("\n[bold cyan]🧠 记忆辅助[/bold cyan]\n")
        console.print(f"[bold]策略类型：[/bold]{strategy}")
        
        # 根据策略类型显示不同内容
        if strategy == "acronym":
            console.print(f"\n[bold green]缩略词：[/bold green]{mnemonic.get('acronym', '')}")
            console.print(f"[bold]完整术语：[/bold]")
            for term in mnemonic.get('full_terms', []):
                console.print(f"  • {term}")
            console.print(f"\n💡 {mnemonic.get('memory_tip', '')}")
        
        elif strategy == "comparison":
            console.print(f"\n[bold green]{mnemonic.get('table_title', '对比表')}[/bold green]")
            # 简化显示对比表
            items = mnemonic.get('items', [])
            console.print(f"\n对比项目：{', '.join(items)}")
            console.print(f"\n关键差异：")
            for diff in mnemonic.get('key_differences', []):
                console.print(f"  • {diff}")
        
        elif strategy == "analogy":
            console.print(f"\n[bold green]类比：[/bold green]{mnemonic.get('concrete_analogy', '')}")
            console.print(f"\n{mnemonic.get('explanation', '')}")
            if mnemonic.get('limitations'):
                console.print(f"\n[dim]⚠️  类比局限性：{mnemonic['limitations']}[/dim]")
        
        elif strategy == "visual":
            console.print(f"\n[bold green]视觉联想：[/bold green]{mnemonic.get('visual_description', '')}")
            if mnemonic.get('mermaid_diagram'):
                console.print(f"\n[dim]流程图：[/dim]")
                console.print(f"[dim]{mnemonic['mermaid_diagram']}[/dim]")
            console.print(f"\n💡 {mnemonic.get('usage_instruction', '')}")
        
        elif strategy == "number":
            numbers = mnemonic.get('numbers', [])
            pattern = mnemonic.get('pattern', '')
            console.print(f"\n[bold green]数字模式：[/bold green]{pattern}")
            console.print(f"\n💡 {mnemonic.get('memory_phrase', '')}")
            if mnemonic.get('associations'):
                console.print(f"\n[bold]数字含义：[/bold]")
                for num, meaning in mnemonic['associations'].items():
                    console.print(f"  • {num}: {meaning}")
    
    def show_sources(self):
        """显示来源引用（阶段二新增）"""
        if not self.current_state or not self.current_state.verified_sources:
            console.print("[yellow]当前没有可用的来源引用[/yellow]")
            console.print("[dim]提示：对于需要验证的内容（如数据、法规等），系统会自动标注权威来源[/dim]")
            return
        
        console.print("\n[bold cyan]📚 权威来源引用[/bold cyan]\n")
        
        if self.current_state.validation_result:
            validation = self.current_state.validation_result
            confidence = validation.get('confidence_score', 0)
            
            if confidence >= 0.8:
                console.print("[green]✅ 内容已验证[/green]")
            elif confidence >= 0.6:
                console.print("[yellow]⚠️  内容部分验证[/yellow]")
            else:
                console.print("[red]❗ 内容未充分验证[/red]")
            
            console.print(f"置信度：{confidence*100:.0f}%\n")
        
        console.print("[bold]引用来源：[/bold]")
        for i, source in enumerate(self.current_state.verified_sources, 1):
            console.print(f"\n{i}. [bold]{source.get('title', '未知来源')}[/bold]")
            console.print(f"   {source.get('url', '')}")
            if source.get('score'):
                console.print(f"   相关度：{source['score']*100:.0f}%")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
# 📖 帮助信息

## 使用方法：
1. 输入你的问题，按回车发送
2. 阅读解释后，回答理解检查问题
3. 根据反馈继续学习

## 可用命令：
- `/progress` - 查看学习进度（含效率分析、复习提醒、推荐主题）
- `/mode` - 选择教学模式（苏格拉底式/讲授式）
- `/mnemonic` - 显示当前概念的记忆辅助
- `/sources` - 显示来源引用
- `/help` - 显示此帮助信息
- `/end` - 结束当前会话并退出

## 提示：
- 尽量详细描述你的问题
- 用自己的话回答检查问题
- 如果不理解，可以继续提问
- 使用 `/mode` 可以切换不同的教学风格
        """
        console.print(Panel(Markdown(help_text), title="帮助", border_style="green"))
    
    def run(self):
        """运行CLI应用"""
        self.show_welcome()
        
        # 开始会话
        if not self.start_session():
            return
        
        # 主循环
        while True:
            try:
                question = Prompt.ask("\n[bold green]你的问题[/bold green]")
                
                if not question.strip():
                    continue
                
                # 处理特殊命令
                if question.strip().lower() in ["/end", "/quit", "/exit"]:
                    console.print("[yellow]结束会话，再见！[/yellow]")
                    break
                
                elif question.strip().lower() == "/progress":
                    self.show_progress()
                    continue
                
                elif question.strip().lower() == "/mode":
                    self.select_teaching_mode()
                    continue
                
                elif question.strip().lower() == "/mnemonic":
                    self.show_mnemonic()
                    continue
                
                elif question.strip().lower() == "/sources":
                    self.show_sources()
                    continue
                
                elif question.strip().lower() == "/help":
                    self.show_help()
                    continue
                
                # 处理正常问题
                self.handle_question(question)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]检测到中断，正在退出...[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]发生错误：{str(e)}[/red]")
                if Confirm.ask("是否继续？"):
                    continue
                else:
                    break


def main():
    """CLI入口函数"""
    try:
        cli = SmartLearnerCLI()
        cli.run()
    except Exception as e:
        console.print(f"[red]致命错误：{str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
