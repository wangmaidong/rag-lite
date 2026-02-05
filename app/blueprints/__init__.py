"""
蓝图模块
"""

from app.blueprints import auth, knowledgebase, settings, document, chat

__all__ = ["auth", "knowledgebase", "settings", "document", "chat"]
