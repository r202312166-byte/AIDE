"""
Plugins module for OurNotepad
"""

from .package_creator import show_package_creator

# 尝试导入code_pack_plugin
try:
    from .code_pack_plugin import CodePackBlock, show_code_pack_editor, register_plugin
    __all__ = ['show_package_creator', 'CodePackBlock', 'show_code_pack_editor', 'register_plugin']
except ImportError:
    __all__ = ['show_package_creator']