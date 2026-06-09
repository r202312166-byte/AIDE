"""
Core module for OurNotepad containing base classes and parsers.
"""

from .code_block import CodeBlock
from .parser import PythonFileParser
from .language_manager import LanguageManager
from .language_mode_manager import LanguageModeManager

__all__ = ['CodeBlock', 'PythonFileParser', 'LanguageManager', 'LanguageModeManager']