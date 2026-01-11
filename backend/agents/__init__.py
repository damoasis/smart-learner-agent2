"""  

智能学习助手Agent模块

包含各种教学和评估Agent的实现



ReAct模式：

- backend.agents.react: ReAct Agent实现

- backend.agents.tools: 工具函数集合



传统模式（兼容）：

- backend.agents.socratic_teacher等: 旧Agent类（已迁移到ReAct）

"""



# ReAct Agent导出

from backend.agents import react

from backend.agents import tools



__all__ = [

    # ReAct模块

    "react",

    "tools",

]

