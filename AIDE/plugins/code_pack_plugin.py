import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
from core.code_block import CodeBlock


class CodePackBlock(CodeBlock):
    """简化的Code Pack块类型，通过.txt文件设置内容"""
    
    def __init__(self, block_id, block_type, x, y, width=None, height=60, text="", content=""):
        super().__init__(block_id, block_type, x, y, width, height, text, content)
        
        # Code Pack特定属性
        self.is_code_pack = True
        self.pack_version = "1.0"
        
        # 如果文本为空，设置默认文本
        if not self.text or self.text == "code_pack":
            self.text = "Code Pack"
        
        # 设置默认颜色
        self.color = "#8E44AD"  # 紫色
    
    def get_default_color(self):
        """返回Code Pack的默认颜色"""
        return "#8E44AD"
    
    def load_from_file(self, filepath):
        """从.txt文件加载内容"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
            
            # 如果内容简短，更新显示文本
            lines = self.content.strip().split('\n')
            if len(lines) == 1 and len(lines[0]) < 30:
                self.text = lines[0]
            else:
                # 使用文件名作为显示文本
                filename = os.path.basename(filepath)
                self.text = f"Code Pack: {os.path.splitext(filename)[0]}"
            
            return True
        except Exception as e:
            messagebox.showerror("加载错误", f"无法读取文件: {e}")
            return False
    
    def to_dict(self):
        """转换为字典用于序列化"""
        data = super().to_dict()
        data["is_code_pack"] = self.is_code_pack
        data["pack_version"] = self.pack_version
        return data


def show_code_pack_editor(app, block):
    """显示简化的Code Pack编辑器（通过文件选择）"""
    # 选择.txt文件
    filename = filedialog.askopenfilename(
        title="选择文本文件",
        filetypes=[("code", ("*.py", "*.txt")), ("all files", "*.*")]
    )
    
    if filename:
        if block.load_from_file(filename):
            # 更新主应用显示
            if hasattr(app, 'draw_all_blocks'):
                app.draw_all_blocks()
            if hasattr(app, 'show_block_properties'):
                app.show_block_properties()
            messagebox.showinfo("加载成功", f"已从文件加载内容到代码包块")


def register_plugin(app):
    """注册插件到主应用"""
    # 添加Code Pack块类型到块加载器
    if hasattr(app, 'block_loader') and hasattr(app.block_loader, 'available_blocks'):
        # 确保有"Special"类别
        if "Special" not in app.block_loader.available_blocks:
            app.block_loader.available_blocks["Special"] = []
        
        # 检查是否已存在Code Pack块
        code_pack_exists = False
        for block in app.block_loader.available_blocks["Special"]:
            if block.get("text") == "Code Pack" and block.get("type") == "code_pack":
                code_pack_exists = True
                break
        
        # 如果不存在，添加Code Pack块
        if not code_pack_exists:
            code_pack_block = {
                "type": "code_pack",
                "text": "Code Pack",
                "content": "# 代码包内容\n# 双击此块，然后点击'更改内容'按钮选择.txt文件",
                "template": "",
                "description": "通过选择.txt文件来设置代码内容",
                "is_code_pack": True,
                "pack_version": "1.0"
            }
            app.block_loader.available_blocks["Special"].append(code_pack_block)
    
    # 更新块列表显示
    if hasattr(app, 'update_blocks_list'):
        app.update_blocks_list()
    
    print("简化的Code Pack插件已注册")
