"""
教学Agent模块

该模块包含所有教学Agent的实现。
"""

from backend.agents.teaching.socratic_teacher_adapter import SocraticTeacherAdapter
from backend.agents.teaching.lecture_teaching_agent import LectureTeachingAgent

__all__ = [
    "SocraticTeacherAdapter",
    "LectureTeachingAgent",
]
