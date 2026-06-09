"""
UI module for OurNotepad containing GUI components and windows.
"""

from .builder import OurNotepadBuilder  # 更改导入名称
from .components import *
from .help_window import show_help_window

# 导入包创建器
try:
    from plugins.package_creator import show_package_creator
except ImportError:
    # 如果插件不存在，提供存根函数
    def show_package_creator(app):
        from tkinter import messagebox
        messagebox.showerror("Plugin Missing", 
                           "Package Creator plugin not found.\n"
                           "Make sure plugins/package_creator.py exists.")

__all__ = ['OurNotepadBuilder', 'show_help_window', 'show_package_creator']  # 更改导出名称