import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import json
import os
import subprocess
import sys
from core.language_mode_manager import LanguageModeManager
import glob
import time
import importlib
import inspect
import threading

# Import from our packages
from core.code_block import CodeBlock
from core.parser import PythonFileParser
from core.language_manager import LanguageManager
from ui.components import create_left_section, create_middle_section, create_right_section
from utils.block_loader import BlockLoader
from utils.file_handler import FileHandler
from plugins.code_pack_plugin import CodePackBlock, show_code_pack_editor, register_plugin
CODE_PACK_PLUGIN_AVAILABLE = True
class AntimonyIDEBuilder:
    def __init__(self, root):
        self.root = root
        self.lang = LanguageManager()
        self.lang_mode = LanguageModeManager()

        # Set app title with project name
        self.project_name = self.lang.get("untitled_project")
        self.root.title(f"Antinomy - {self.project_name}")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)

        # Initialize state variables
        self.blocks = {}
        self.block_counter = 0
        self.selected_block_id = None
        self.dragging_block = None
        self.connecting_mode = False
        self.end_connecting_mode = False
        self.continue_connecting_mode = False
        self.start_connection_block = None
        self.current_category = self.lang.get("blocks_all")

        # Connection lines
        self.sequence_lines = []
        self.end_lines = []
        self.continue_lines = []

        # UI state variables
        self.dragging_from_list = False
        self.drag_block_type = None
        self.drag_block_text = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.scrolling = False
        self.scroll_start_x = 0
        self.scroll_start_y = 0

        self.current_block_type = None
        self.current_block_text = None
        self.current_block_data = None

        self.last_export_file = None

        self.polyline_points = {}
        self.dragging_polyline_point = None
        self.polyline_dot_radius = 5

        self.connection_lines = {}

        self.select_mode = False
        self.select_mode_var = tk.BooleanVar(value=False)
        self.selected_polyline_point = None
        self.polyline_drag_start = None

        self.parser = PythonFileParser()
        self.block_loader = BlockLoader()
        self.file_handler = FileHandler(self)

        self.setup_ui()
        self.setup_menu()
        self.setup_keybindings()

        self.root.update_idletasks()

        self.register_code_pack_plugin()

        self.update_blocks_for_language(self.lang_mode.current_mode)

    def register_code_pack_plugin(self):
        try:
            if CODE_PACK_PLUGIN_AVAILABLE and register_plugin:
                register_plugin(self)
            else:
                try:
                    from plugins.code_pack_plugin import register_plugin as reg_plugin
                    reg_plugin(self)
                except ImportError:
                    print("Code Pack plugin not found, but continuing without it")
        except Exception as e:
            print(f"Error registering Code Pack plugin: {e}")

    def fix_all_code_pack_blocks(self):
        fixed_count = 0
        for block_id, block in list(self.blocks.items()):
            if (block.type == "code_pack" and
                    (not hasattr(block, 'is_code_pack') or not block.is_code_pack)):
                upgraded_block = self.upgrade_to_code_pack_block(block)
                if hasattr(upgraded_block, 'is_code_pack') and upgraded_block.is_code_pack:
                    fixed_count += 1

        if fixed_count > 0:
            print(f"Fixed {fixed_count} Code Pack blocks")
            self.draw_all_blocks()

    def setup_menu(self):
        """Setup menu bar with all functionality"""
        menubar = tk.Menu(self.root)

        # ===== File Menu =====
        file_menu = tk.Menu(menubar, tearoff=0)
        
        # Project management
        file_menu.add_command(label="New Project", accelerator="Ctrl+N",
                             command=self.new_project)
        file_menu.add_command(label="Import Project", accelerator="Ctrl+O",
                             command=self.import_project)
        file_menu.add_command(label="Save Project", accelerator="Ctrl+S",
                             command=self.save_project)
        file_menu.add_command(label="Save Project As",
                             command=self.save_project_as)
        file_menu.add_separator()

        file_menu.add_command(label="Rename Project...",
                             command=self.edit_project_name_menu)
        file_menu.add_separator()
        
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        menubar.add_cascade(label="File", menu=file_menu)

        # ===== Edit Menu =====
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Delete Block", accelerator="Ctrl+Q",
                             command=self.delete_selected_block_no_confirm)
        edit_menu.add_command(label="Duplicate Block", accelerator="Ctrl+D",
                             command=lambda: self.duplicate_block(self.selected_block_id) 
                             if self.selected_block_id else None)
        edit_menu.add_separator()
        edit_menu.add_command(label="Connect Sequence", accelerator="Ctrl+A",
                             command=lambda: self.start_connection() 
                             if self.selected_block_id else None)
        edit_menu.add_command(label="Set End Block", accelerator="Ctrl+X",
                             command=lambda: self.start_end_connection() 
                             if self.selected_block_id else None)
        edit_menu.add_command(label="Insert Line", accelerator="Ctrl+W",
                             command=lambda: self.start_continue_connection() 
                             if self.selected_block_id else None)
        edit_menu.add_separator()
        
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # ===== View Menu =====
        self.view_menu = tk.Menu(menubar, tearoff=0)
        
        # Toggle panels
        self.show_block_library_var = tk.BooleanVar(value=True)
        self.show_block_editor_var = tk.BooleanVar(value=True)
        
        self.view_menu.add_checkbutton(label="Show Block Library", 
                                       variable=self.show_block_library_var,
                                       command=self.toggle_block_library)
        self.view_menu.add_checkbutton(label="Show Block Editor", 
                                       variable=self.show_block_editor_var,
                                       command=self.toggle_block_editor)
        
        menubar.add_cascade(label="View", menu=self.view_menu)

        # ===== Tools Menu =====
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Package Creator", accelerator="Ctrl+P",
                              command=self.open_package_creator)
        tools_menu.add_command(label="Import Package",
                              command=self.import_package)
        tools_menu.add_separator()
        tools_menu.add_command(label="Save as Pack",
                              command=self.save_as_pack)
        tools_menu.add_command(label="Use Pack",
                              command=self.use_pack)
        tools_menu.add_separator()
        tools_menu.add_command(label="Generate Code", accelerator="F5",
                              command=self.export_code)
        tools_menu.add_command(label="Run Code", accelerator="F6",
                              command=self.run_exported_code)
        
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # ===== Help Menu =====
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help Contents", accelerator="F1",
                             command=self.show_help)
        help_menu.add_command(label="About AntimonyIDE",
                             command=self.show_about)
        
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def setup_ui(self):
        """Setup the user interface - 改进：灵活的布局"""
        # 配置网格权重
        self.root.grid_rowconfigure(0, weight=1)

        # 配置列权重 - 使用更灵活的配置
        self.root.grid_columnconfigure(0, weight=1, minsize=250)  # 左侧
        self.root.grid_columnconfigure(1, weight=10, minsize=400)  # 中间（增加权重）
        self.root.grid_columnconfigure(2, weight=1, minsize=300)  # 右侧

        # 创建三个主要部分
        create_left_section(self)
        create_middle_section(self)
        create_right_section(self)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # 确保所有部分扩展到可用空间
        self.root.update_idletasks()
    def setup_keybindings(self):
        """Setup keyboard shortcuts - updated version"""
        shortcuts = {
            "<Control-n>": lambda e: self.new_project(),
            "<Control-o>": lambda e: self.import_project(),
            "<Control-s>": lambda e: self.save_project(),
            "<Control-e>": lambda e: self.export_code(),
            "<Control-p>": lambda e: self.open_package_creator(),
            "<Control-q>": self.delete_selected_block_no_confirm,
            "<Control-a>": lambda e: self.start_connection(),
            "<Control-x>": lambda e: self.start_end_connection(),
            "<Control-w>": lambda e: self.start_continue_connection(),
            "<Control-d>": lambda e: self.duplicate_block(self.selected_block_id)
            if self.selected_block_id else None,
            "<Control-f>": lambda e: self.update_block_content(),
            "<Control-t>": lambda e: self.toggle_select_mode(),
            "<F1>": lambda e: self.show_help(),
            "<F5>": lambda e: self.export_code(),
            "<F6>": lambda e: self.run_exported_code(),
        }

        for key, func in shortcuts.items():
            self.root.bind(key, func)
    # ===== Menu Methods =====
    def load_code_file(self):
        """Load a code file and convert each line to a code block"""
        # 询问用户是否保存当前项目
        if self.blocks:
            response = messagebox.askyesnocancel("Load Code File",
                                                 "Do you want to save the current project before loading a code file?")
            if response is None:  # Cancel
                return
            elif response:  # Yes - save
                self.save_project()

        # 打开文件对话框
        filetypes = [
            ("Python Files", "*.py"),
            ("HTML Files", "*.html;*.htm"),
            ("C/C++ Files", "*.c;*.cpp;*.h;*.hpp"),
            ("Java Files", "*.java"),
            ("Text Files", "*.txt"),
            ("All Files", "*.*")
        ]

        filename = filedialog.askopenfilename(
            title="Select Code File to Load",
            filetypes=filetypes
        )

        if not filename:
            return

        try:
            # 根据文件扩展名确定语言模式
            extension = os.path.splitext(filename)[1].lower()
            language_mode = self.determine_language_mode(extension)

            # 设置语言模式
            if not self.lang_mode.set_mode(language_mode):
                # 如果不支持该语言，切换到text模式
                self.lang_mode.set_mode("text")
                messagebox.showinfo("Unsupported Language",
                                    f"Language for {extension} files is not fully supported. Switching to Text mode.")

            # 读取文件内容
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 清空当前画布
            self.new_project()

            # 设置项目名称为文件名
            self.project_name = os.path.basename(filename)
            self.root.title(f"AntimonyIDE - {self.project_name}")

            # 在画布上放置代码块（每行一个）
            start_x = 100
            start_y = 100
            line_spacing = 80

            for i, line in enumerate(lines):
                # 去除行尾换行符
                content = line.rstrip('\n')
                if not content.strip():  # 跳过空行
                    continue

                # 创建代码块ID
                block_id = f"block_{self.block_counter}"

                # 创建文本块
                new_block = CodeBlock(
                    block_id,
                    "text",  # 使用text类型
                    start_x,
                    start_y + i * line_spacing,
                    text=f"Line {i + 1}",
                    content=content
                )

                # 添加到blocks字典
                self.blocks[block_id] = new_block
                self.block_counter += 1

                # 创建序列连接（除了第一行）
                if i > 0:
                    prev_block_id = f"block_{self.block_counter - 2}"
                    self.sequence_lines.append((prev_block_id, block_id))

            # 重绘画布
            self.draw_all_blocks()

            # 更新语言模式显示
            mode_info = self.lang_mode.get_mode_info()
            messagebox.showinfo("File Loaded",
                                f"Successfully loaded {len(lines)} lines from {filename}\n"
                                f"Language mode set to: {mode_info['name']}")

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load code file: {e}")

    def determine_language_mode(self, extension):
        """根据文件扩展名确定语言模式"""
        extension_map = {
            '.py': 'python',
            '.html': 'html',
            '.htm': 'html',
            '.c': 'c_cpp',
            '.cpp': 'c_cpp',
            '.h': 'c_cpp',
            '.hpp': 'c_cpp',
            '.java': 'java',
            '.txt': 'text',
        }

        return extension_map.get(extension, 'text')  # 默认使用text模式

    def edit_project_name_menu(self):
        """Edit project name from menu"""
        new_name = simpledialog.askstring(
            "Rename Project", 
            "Enter new project name:",
            initialvalue=self.project_name
        )
        if new_name and new_name.strip():
            self.project_name = new_name.strip()
            # Update window title
            self.root.title(f"AntimonyIDE - {self.project_name}")

    def toggle_block_library(self):
        """Toggle visibility of block library - 改进：画布自动扩展"""
        if hasattr(self, 'left_frame'):
            if self.left_frame.winfo_ismapped():
                # 隐藏左侧框架
                self.left_frame.grid_remove()

                # 重新配置网格权重：中间列占据左侧空间
                self.root.grid_columnconfigure(0, weight=0, minsize=0)
                self.root.grid_columnconfigure(1, weight=6)  # 增加中间列权重

                # 强制更新布局
                self.root.update_idletasks()

                # 更新窗口标题
                mode_info = self.lang_mode.get_mode_info()
                self.root.title(f"AntimonyIDE - {self.project_name} [{mode_info['name']}] - Code Library Hidden")
            else:
                # 显示左侧框架
                self.left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

                # 恢复网格权重
                self.root.grid_columnconfigure(0, weight=1, minsize=250)
                self.root.grid_columnconfigure(1, weight=5, minsize=400)

                # 强制更新布局
                self.root.update_idletasks()

                # 恢复窗口标题
                mode_info = self.lang_mode.get_mode_info()
                self.root.title(f"AntimonyIDE - {self.project_name} [{mode_info['name']}]")

            # 更新画布网格以适应新的大小
            self.draw_grid()

    def toggle_block_editor(self):
        """Toggle visibility of block editor - 改进：画布自动扩展"""
        if not hasattr(self, 'right_frame'):
            return

        if self.right_frame.winfo_ismapped():
            # 隐藏右侧编辑器
            self.right_frame.grid_remove()

            # 调整网格权重：中间列占据右侧空间
            self.root.grid_columnconfigure(2, weight=0, minsize=0)
            self.root.grid_columnconfigure(1, weight=6)  # 增加中间列权重

            # 强制更新布局
            self.root.update_idletasks()

            # 更新窗口标题
            mode_info = self.lang_mode.get_mode_info()
            self.root.title(f"AntimonyIDE - {self.project_name} [{mode_info['name']}] - Block Editor Hidden")
        else:
            # 显示右侧编辑器
            self.right_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

            # 恢复网格权重
            self.root.grid_columnconfigure(2, weight=1, minsize=300)
            self.root.grid_columnconfigure(1, weight=5, minsize=400)

            # 强制更新布局
            self.root.update_idletasks()

            # 恢复窗口标题
            mode_info = self.lang_mode.get_mode_info()
            self.root.title(f"AntimonyIDE - {self.project_name} [{mode_info['name']}]")

        # 更新画布网格以适应新的大小
        self.draw_grid()

    def adjust_canvas_after_hide(self):
        """在隐藏编辑器后调整画布大小"""
        if not hasattr(self, 'canvas') or not hasattr(self, 'middle_frame'):
            return
        
        # 获取当前中间框架的宽度
        middle_width = self.middle_frame.winfo_width()
        
        # 获取中间框架的内部尺寸
        middle_inner_width = middle_width - 20  # 减去padding
        
        # 获取画布框架
        canvas_frame = self.canvas.master
        
        # 设置画布框架的最小宽度
        if middle_inner_width > 100:
            # 重新配置画布框架的列
            canvas_frame.grid_columnconfigure(0, weight=1)
            
            # 重新配置滚动条
            for child in canvas_frame.winfo_children():
                if isinstance(child, tk.Scrollbar):
                    if child.cget("orient") == "vertical":
                        child.grid(row=0, column=1, sticky="ns")
                    elif child.cget("orient") == "horizontal":
                        child.grid(row=1, column=0, sticky="ew")
            
            # 强制更新
            self.root.update_idletasks()
            self.draw_grid()

    def change_programming_mode(self, mode):
        """Change programming language mode"""
        if self.lang_mode.set_mode(mode):
            mode_info = self.lang_mode.get_mode_info(mode)

            # Update window title
            self.root.title(f"AntimonyIDE - {self.project_name} [{mode_info['name']}]")

            # Update blocks for the new language
            self.update_blocks_for_language(mode)

            # Update radio button variable
            self.prog_mode_var.set(mode)

    def update_blocks_for_language(self, language_mode):
        """Update available blocks based on language mode - 修复版本"""
        print(f"Updating blocks for language: {language_mode}")

        # 先备份自定义包
        custom_packages = {}
        default_categories = [
            "Text Blocks", "Statements", "Control Flow", "Loops",
            "Functions", "I/O", "Variables", "Operators", "Imports", "Special"
        ]

        # 分离自定义包
        for category, blocks in list(self.block_loader.available_blocks.items()):
            if category not in default_categories:
                custom_packages[category] = blocks

        # 现在清空并重新加载语言特定包
        self.block_loader.available_blocks = {}

        # 根据语言模式加载包
        if language_mode == "text":
            # 设置文本块
            text_blocks = {
                "Text Blocks": [
                    {"type": "text", "text": "Text Line", "content": "Enter text here",
                     "template": "Enter text here", "description": "A line of text"},
                    {"type": "text", "text": "Comment", "content": "# Comment",
                     "template": "# {comment}", "description": "Add a comment"},
                    {"type": "text", "text": "Header", "content": "# Header",
                     "template": "# {header}", "description": "Section header"},
                ],
                "Special": []
            }
            self.block_loader.available_blocks.update(text_blocks)
        else:
            # 加载语言特定包
            self.block_loader.load_language_packages(language_mode)

        # 重新添加自定义包
        for category, blocks in custom_packages.items():
            if category not in self.block_loader.available_blocks:
                self.block_loader.available_blocks[category] = []

            # 添加块，避免重复
            for block in blocks:
                exists = False
                for existing_block in self.block_loader.available_blocks[category]:
                    if (existing_block.get("text") == block.get("text") and
                            existing_block.get("type") == block.get("type")):
                        exists = True
                        break

                if not exists:
                    self.block_loader.available_blocks[category].append(block)

        # 确保Special类别有Code Pack块
        if "Special" not in self.block_loader.available_blocks:
            self.block_loader.available_blocks["Special"] = []

        code_pack_exists = False
        for block in self.block_loader.available_blocks["Special"]:
            if block.get("type") == "code_pack":
                code_pack_exists = True
                break

        if not code_pack_exists:
            code_pack_block = {
                "type": "code_pack",
                "text": "Code Pack",
                "content": "# Code Pack content\n# Double-click to edit",
                "template": "",
                "description": "A reusable container for code blocks",
                "is_code_pack": True,
                "pack_version": "1.0"
            }
            self.block_loader.available_blocks["Special"].append(code_pack_block)

        # 更新块列表
        self.update_blocks_list()

        print(f"Available categories: {list(self.block_loader.available_blocks.keys())}")

    def show_about(self):
        """Show about dialog for AntimonyIDE"""
        messagebox.showinfo("About AntimonyIDE",
                          "AntimonyIDE\n"
                          "A visual block-based programming environment\n"
                          "Version 1.0\n\n"
                          "Create programs using visual blocks\n"
                          "Supports multiple programming languages")

    def run_exported_code(self):
        """Run the last exported code"""
        if hasattr(self, 'last_export_file') and os.path.exists(self.last_export_file):
            if self.lang_mode.current_mode == "python":
                self.run_python_code(self.last_export_file)
            else:
                messagebox.showinfo("Cannot Run", 
                                  f"{self.lang_mode.get_mode_info()['name']} code cannot be run directly.\n"
                                  f"File: {self.last_export_file}")
        else:
            messagebox.showwarning("No Exported File", 
                                  "No code has been exported yet.\n"
                                  "Please export your project first.")

    # ===== Canvas Drawing Methods =====

    def draw_grid(self):
        """Draw grid lines on the canvas - 改进：自适应画布大小"""
        self.canvas.delete("grid_line")

        # 获取画布当前的实际尺寸
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 如果画布还没有实际大小，使用默认值
        if canvas_width < 10:
            canvas_width = 800
        if canvas_height < 10:
            canvas_height = 600

        # 计算滚动区域，使其至少为当前画布大小的3倍
        scroll_region_width = max(canvas_width * 3, 2000)
        scroll_region_height = max(canvas_height * 3, 2000)

        # 设置新的滚动区域（居中对齐）
        center_x = scroll_region_width // 2
        center_y = scroll_region_height // 2

        x1 = center_x - canvas_width * 1.5
        y1 = center_y - canvas_height * 1.5
        x2 = center_x + canvas_width * 1.5
        y2 = center_y + canvas_height * 1.5

        self.canvas.config(scrollregion=(x1, y1, x2, y2))

        # 获取当前可见区域
        visible_x1 = int(self.canvas.canvasx(0))
        visible_y1 = int(self.canvas.canvasy(0))
        visible_x2 = int(self.canvas.canvasx(canvas_width))
        visible_y2 = int(self.canvas.canvasy(canvas_height))

        # 扩展可见区域以确保覆盖
        visible_x1 = min(visible_x1, x1)
        visible_y1 = min(visible_y1, y1)
        visible_x2 = max(visible_x2, x2)
        visible_y2 = max(visible_y2, y2)

        # 绘制细网格线（20像素间隔）
        for x in range(int(visible_x1) - int(visible_x1) % 20, int(visible_x2) + 20, 20):
            self.canvas.create_line(x, visible_y1, x, visible_y2,
                                    fill="#f0f0f0", width=1,
                                    tags="grid_line", dash=(1, 1))

        for y in range(int(visible_y1) - int(visible_y1) % 20, int(visible_y2) + 20, 20):
            self.canvas.create_line(visible_x1, y, visible_x2, y,
                                    fill="#f0f0f0", width=1,
                                    tags="grid_line", dash=(1, 1))

        # 绘制粗网格线（100像素间隔）
        for x in range(int(visible_x1) - int(visible_x1) % 100, int(visible_x2) + 100, 100):
            self.canvas.create_line(x, visible_y1, x, visible_y2,
                                    fill="#d0d0d0", width=2,
                                    tags="grid_line")

        for y in range(int(visible_y1) - int(visible_y1) % 100, int(visible_y2) + 100, 100):
            self.canvas.create_line(visible_x1, y, visible_x2, y,
                                    fill="#d0d0d0", width=2,
                                    tags="grid_line")

        # 绘制坐标轴（每500像素）
        for x in range(int(visible_x1) - int(visible_x1) % 500, int(visible_x2) + 500, 500):
            self.canvas.create_line(x, visible_y1, x, visible_y2,
                                    fill="#a0a0a0", width=3,
                                    tags="grid_line")
            # 添加坐标标签
            if x != 0:
                self.canvas.create_text(x, visible_y1 - 10, text=str(x),
                                        fill="#808080", font=("Arial", 8),
                                        tags="grid_line")

        for y in range(int(visible_y1) - int(visible_y1) % 500, int(visible_y2) + 500, 500):
            self.canvas.create_line(visible_x1, y, visible_x2, y,
                                    fill="#a0a0a0", width=3,
                                    tags="grid_line")
            # 添加坐标标签
            if y != 0:
                self.canvas.create_text(visible_x1 - 10, y, text=str(y),
                                        fill="#808080", font=("Arial", 8),
                                        tags="grid_line")

        # 确保网格在所有元素后面
        self.canvas.tag_lower("grid_line")

    def on_canvas_configure(self, event):
        """当画布大小变化时重新绘制网格"""
        # 只有在大小变化明显时才重绘网格，避免频繁重绘
        current_size = (event.width, event.height)
        if (abs(current_size[0] - getattr(self, 'last_canvas_size', (0, 0))[0]) > 10 or
                abs(current_size[1] - getattr(self, 'last_canvas_size', (0, 0))[1]) > 10):
            self.last_canvas_size = current_size
            self.draw_grid()
    
    def draw_block(self, block):
        """Draw a block on the canvas"""
        # Remove existing block items
        if block.canvas_ids[0]:
            self.canvas.delete(block.canvas_ids[0])
        if block.canvas_ids[1]:
            self.canvas.delete(block.canvas_ids[1])
        
        # Draw block rectangle
        rect_id = self.canvas.create_rectangle(
            block.x, block.y, 
            block.x + block.width, block.y + block.height,
            fill=block.color, outline="black", width=2,
            tags=("block", "block_rect", block.id)
        )
        
        # Draw block text
        text_id = self.canvas.create_text(
            block.x + block.width/2, block.y + block.height/2,
            text=block.text, fill="white", font=("Arial", 10, "bold"),
            tags=("block", "block_text", block.id)
        )
        
        # Store canvas IDs
        block.canvas_ids = (rect_id, text_id)
        
        # Bring to front if selected
        if self.selected_block_id == block.id:
            self.highlight_selected_block()

    def update_block_content(self):
        """Update content of selected block (Ctrl-F shortcut)"""
        if not self.selected_block_id or self.selected_block_id not in self.blocks:
            return

        # 在编辑器框架中查找文本框
        if hasattr(self, 'editor_frame'):
            # 查找文本框
            for widget in self.editor_frame.winfo_children():
                if isinstance(widget, tk.Text):
                    # 获取内容并更新块
                    block = self.blocks[self.selected_block_id]
                    block.content = widget.get("1.0", tk.END).strip()

                    # 更新块文本（如果是简单语句）
                    if "{" not in block.content and len(block.content) < 30:
                        block.text = block.content

                    # 重绘块
                    self.draw_all_blocks()
                    self.highlight_selected_block()

                    # 显示更新消息
                    self.show_temp_message("Block content updated")
                    return

        # 如果没有找到文本框，显示错误消息
        messagebox.showinfo("No Block Selected", "Select a block to edit first.")

    def show_temp_message(self, message):
        """显示临时消息"""
        if hasattr(self, 'canvas'):
            # 在画布上显示临时消息
            self.canvas.delete("temp_message")
            self.canvas.create_text(
                self.canvas.winfo_width() // 2, 20,
                text=message, fill="green", font=("Arial", 10, "bold"),
                tags="temp_message"
            )
            # 2秒后清除消息
            self.root.after(2000, lambda: self.canvas.delete("temp_message"))

    def draw_all_blocks(self):
        """Draw all blocks on the canvas"""
        # Clear all block-related items
        self.canvas.delete("block")
        self.canvas.delete("block_text")
        self.canvas.delete("block_rect")
        self.canvas.delete("connection")
        self.canvas.delete("highlight")
        
        # Draw all blocks
        for block_id, block in self.blocks.items():
            self.draw_block(block)
        
        # Draw all connections
        self.draw_all_connections()
        
        # Update the canvas display
        self.canvas.update_idletasks()

    def draw_all_connections(self):
        """绘制所有连接线（包括折线）"""
        # 清除现有连接线
        self.canvas.delete("connection")
        self.canvas.delete("polyline_dot")

        # 绘制序列线
        for start_id, end_id in self.sequence_lines:
            self.draw_connection(start_id, end_id, "black")

        # 绘制结束线
        for control_id, end_id in self.end_lines:
            self.draw_connection(control_id, end_id, "red")

        # 绘制继续线
        for start_id, end_id in self.continue_lines:
            self.draw_connection(start_id, end_id, "blue")

        # 如果在选择模式下，高亮显示所有折点
        if self.select_mode:
            self.highlight_all_polyline_points()

    def draw_connection(self, start_id, end_id, color="black"):
        """绘制连接线（支持折线）"""
        if start_id not in self.blocks or end_id not in self.blocks:
            return

        # 删除旧的连接线
        if (start_id, end_id) in self.connection_lines:
            for line_id in self.connection_lines[(start_id, end_id)]:
                self.canvas.delete(line_id)
            del self.connection_lines[(start_id, end_id)]

        start_block = self.blocks[start_id]
        end_block = self.blocks[end_id]

        # 获取连接点
        start_points = start_block.get_connector_points()
        end_points = end_block.get_connector_points()

        # 确定连接方向
        start_point = start_points["bottom"]
        end_point = end_points["top"]

        # 检查是否有折点
        polyline_key = (start_id, end_id)
        points = [start_point]

        if polyline_key in self.polyline_points and self.polyline_points[polyline_key]:
            # 添加折点
            points.extend(self.polyline_points[polyline_key])
        points.append(end_point)

        # 绘制折线
        line_ids = []
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            # 绘制线段
            line_id = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color, width=2, arrow=tk.LAST if i == len(points) - 2 else "none",
                tags=("connection", f"conn_{start_id}_{end_id}", f"segment_{i}")
            )
            line_ids.append(line_id)

            # 绑定双击事件添加折点
            self.canvas.tag_bind(line_id, "<Double-Button-1>",
                                 lambda e, s=start_id, eid=end_id, seg=i:
                                 self.add_polyline_point(s, eid, seg, e.x, e.y))

        # 保存连接线ID
        self.connection_lines[polyline_key] = line_ids

        # 绘制折点（如果有）
        self.draw_polyline_points(start_id, end_id, color)

    def draw_polyline_points(self, start_id, end_id, color="black"):
        """绘制折线上的可拖动点"""
        polyline_key = (start_id, end_id)

        # 删除旧的折点
        self.canvas.delete(f"polyline_{start_id}_{end_id}")

        if polyline_key in self.polyline_points and self.polyline_points[polyline_key]:
            points = self.polyline_points[polyline_key]
            for i, (x, y) in enumerate(points):
                # 绘制可拖动的小圆点
                dot_id = self.canvas.create_oval(
                    x - self.polyline_dot_radius, y - self.polyline_dot_radius,
                    x + self.polyline_dot_radius, y + self.polyline_dot_radius,
                    fill="yellow", outline="black", width=2,
                    tags=("polyline_dot", f"polyline_{start_id}_{end_id}", f"dot_{i}")
                )

                # 绑定拖动事件
                self.canvas.tag_bind(dot_id, "<Button-1>",
                                     lambda e, s=start_id, eid=end_id, idx=i:
                                     self.start_drag_polyline_point(s, eid, idx))
                self.canvas.tag_bind(dot_id, "<B1-Motion>",
                                     lambda e, s=start_id, eid=end_id, idx=i:
                                     self.drag_polyline_point(s, eid, idx, e))
                self.canvas.tag_bind(dot_id, "<ButtonRelease-1>",
                                     lambda e, s=start_id, eid=end_id:
                                     self.stop_drag_polyline_point(s, eid))

    def add_polyline_point(self, start_id, end_id, segment_index, x, y):
        """在线段上添加折点"""
        # 转换为画布坐标
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)

        polyline_key = (start_id, end_id)

        # 初始化折点列表（如果不存在）
        if polyline_key not in self.polyline_points:
            self.polyline_points[polyline_key] = []

        # 在指定位置插入折点
        self.polyline_points[polyline_key].insert(segment_index + 1, (canvas_x, canvas_y))

        # 重新绘制连接线
        self.draw_connection(start_id, end_id, "black")

        # 重新绘制所有连接
        self.draw_all_connections()

    def start_drag_polyline_point(self, start_id, end_id, point_index):
        """开始拖动折点"""
        self.dragging_polyline_point = (start_id, end_id, point_index)

    def drag_polyline_point(self, start_id, end_id, point_index, event):
        """拖动折点"""
        if not self.dragging_polyline_point:
            return

        # 转换为画布坐标并对齐到网格
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        canvas_x = (canvas_x // 20) * 20
        canvas_y = (canvas_y // 20) * 20

        polyline_key = (start_id, end_id)

        if (polyline_key in self.polyline_points and
                point_index < len(self.polyline_points[polyline_key])):
            # 更新折点位置
            self.polyline_points[polyline_key][point_index] = (canvas_x, canvas_y)

            # 重新绘制连接线
            self.draw_connection(start_id, end_id, "black")
            
            # 重新绘制所有连接线以确保所有线段都更新
            self.draw_all_connections()

    def stop_drag_polyline_point(self, start_id, end_id):
        """停止拖动折点"""
        self.dragging_polyline_point = None
        # 重新绘制所有连接线
        self.draw_all_connections()

    def toggle_select_mode(self):
        """切换选择模式"""
        self.select_mode = not self.select_mode
        self.select_mode_var.set(self.select_mode)
        
        if self.select_mode:
            self.canvas.config(cursor="crosshair")
            # 高亮显示所有折点
            self.highlight_all_polyline_points()
        else:
            self.canvas.config(cursor="")
            # 清除高亮
            self.canvas.delete("polyline_highlight")
            self.canvas.delete("selected_point")
            self.selected_polyline_point = None
            self.polyline_drag_start = None

    def highlight_all_polyline_points(self):
        """高亮显示所有折线点"""
        self.canvas.delete("polyline_highlight")
        
        for (start_id, end_id), points in self.polyline_points.items():
            for i, (x, y) in enumerate(points):
                # 绘制高亮点
                highlight_id = self.canvas.create_oval(
                    x - 8, y - 8, x + 8, y + 8,
                    fill="yellow", outline="red", width=2,
                    tags=("polyline_highlight", f"highlight_{start_id}_{end_id}_{i}")
                )
                
                # 绑定点击事件
                self.canvas.tag_bind(highlight_id, "<Button-1>",
                                   lambda e, s=start_id, eid=end_id, idx=i:
                                   self.select_polyline_point(s, eid, idx))

    def select_polyline_point(self, start_id, end_id, point_index):
        """选择折线点"""
        if not self.select_mode:
            return
        
        # 清除之前的选择
        self.canvas.delete("selected_point")
        
        # 设置当前选中的折点
        self.selected_polyline_point = (start_id, end_id, point_index)
        
        # 获取点坐标
        points = self.polyline_points.get((start_id, end_id), [])
        if point_index < len(points):
            x, y = points[point_index]
            
            # 绘制选中的点（更大、更明显的标记）
            self.canvas.create_oval(
                x - 10, y - 10, x + 10, y + 10,
                fill="orange", outline="darkred", width=3,
                tags="selected_point"
            )
            
            # 显示坐标信息
            info_text = f"Point [{point_index}]: ({int(x)}, {int(y)})"
            self.canvas.create_text(x, y - 20, text=info_text,
                                   fill="darkred", font=("Arial", 9, "bold"),
                                   tags="selected_point")

    def canvas_click(self, event):
        """Handle canvas click events - 改进：添加选择模式支持"""
        # Convert to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # 检查选择模式
        if self.select_mode:
            # 在折线点选择模式下，主要处理折点选择
            # 如果没有选择到折点，则检查是否点击了其他元素
            clicked_on_polyline = False
            
            # 检查是否点击了折线点高亮区域
            for (start_id, end_id), points in self.polyline_points.items():
                for i, (px, py) in enumerate(points):
                    if abs(px - x) < 8 and abs(py - y) < 8:
                        self.select_polyline_point(start_id, end_id, i)
                        clicked_on_polyline = True
                        break
                if clicked_on_polyline:
                    break
            
            if clicked_on_polyline:
                return
        
        # Check if we're in connecting mode
        if self.connecting_mode:
            self.handle_connection_click(x, y)
            return

        if self.end_connecting_mode:
            self.handle_end_connection_click(x, y)
            return

        # Check if we're in continue connecting mode
        if self.continue_connecting_mode:
            self.handle_continue_click(x, y)
            return

        # Check if clicked on a block
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            # Use a simple check for point containment
            if (block.x <= x <= block.x + block.width and
                    block.y <= y <= block.y + block.height):
                clicked_block_id = block_id
                break

        if clicked_block_id:
            # Select the block
            self.select_block(clicked_block_id)

            # Start dragging
            self.dragging_block = clicked_block_id
            block = self.blocks[clicked_block_id]
            self.drag_start_x = x - block.x
            self.drag_start_y = y - block.y
        else:
            # Deselect all
            self.deselect_all()
    
    def canvas_drag(self, event):
        """Handle canvas drag events - 改进：添加折点拖动支持"""
        # 如果选择模式并且有选中的折点，拖动折点
        if self.select_mode and self.selected_polyline_point:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            start_id, end_id, point_index = self.selected_polyline_point
            
            # 对齐到网格
            x = (x // 20) * 20
            y = (y // 20) * 20
            
            # 更新折点位置
            if (start_id, end_id) in self.polyline_points:
                if point_index < len(self.polyline_points[(start_id, end_id)]):
                    self.polyline_points[(start_id, end_id)][point_index] = (x, y)
                    
                    # 重新绘制连接线
                    self.draw_connection(start_id, end_id, "black")
                    
                    # 重新绘制所有连接
                    self.draw_all_connections()
                    
                    # 更新高亮显示
                    self.highlight_all_polyline_points()
                    self.select_polyline_point(start_id, end_id, point_index)
            
            return
        
        # If we're not dragging a block, check for scrolling
        if not self.dragging_block:
            if self.scrolling:
                dx = event.x - self.scroll_start_x
                dy = event.y - self.scroll_start_y
                self.canvas.scan_dragto(dx, dy, gain=1)
                self.scroll_start_x = event.x
                self.scroll_start_y = event.y
                self.draw_grid()
            return
        
        # Convert to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Calculate new position (snapped to grid)
        new_x = (x - self.drag_start_x) // 20 * 20
        new_y = (y - self.drag_start_y) // 20 * 20
        
        # Move the block
        block = self.blocks[self.dragging_block]
        
        # Only move if position changed
        if new_x != block.x or new_y != block.y:
            block.move(new_x - block.x, new_y - block.y)
            
            # Update block position directly on canvas
            rect_id, text_id = block.canvas_ids
            self.canvas.coords(rect_id, block.x, block.y, 
                              block.x + block.width, block.y + block.height)
            self.canvas.coords(text_id, block.x + block.width/2, 
                              block.y + block.height/2)
            
            # Redraw connections
            self.draw_all_connections()
            self.highlight_selected_block()

    def canvas_release(self, event):
        """Handle canvas release events"""
        # 重置折点拖动状态
        self.polyline_drag_start = None

        if self.dragging_block:
            # Ensure block is properly snapped to grid
            block = self.blocks[self.dragging_block]
            block.x = (block.x // 20) * 20
            block.y = (block.y // 20) * 20

            # Update block position
            rect_id, text_id = block.canvas_ids
            self.canvas.coords(rect_id, block.x, block.y,
                               block.x + block.width, block.y + block.height)
            self.canvas.coords(text_id, block.x + block.width / 2,
                               block.y + block.height / 2)

        self.dragging_block = None
        self.scrolling = False

        # 只有在拖动或滚动后需要时才重新绘制网格
        if hasattr(self, 'last_scroll_position'):
            # 只在滚动位置变化较大时才重绘网格
            current_x = self.canvas.canvasx(0)
            current_y = self.canvas.canvasy(0)
            if (abs(current_x - self.last_scroll_position[0]) > 100 or
                    abs(current_y - self.last_scroll_position[1]) > 100):
                self.draw_grid()
                self.last_scroll_position = (current_x, current_y)
    
    def canvas_right_click(self, event):
        """Handle canvas right-click events"""
        # Convert to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if clicked on a block
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            if block.contains_point(x, y):
                clicked_block_id = block_id
                break
        
        if clicked_block_id:
            # Show context menu
            self.show_block_context_menu(clicked_block_id, event)
        else:
            # Start scrolling
            self.scroll_start(event)
    
    def scroll_start(self, event):
        """Start scrolling the canvas"""
        self.canvas.scan_mark(event.x, event.y)
        self.scrolling = True
        self.scroll_start_x = event.x
        self.scroll_start_y = event.y
    
    def scroll_move(self, event):
        """Scroll the canvas"""
        if self.scrolling:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self.draw_grid()  # Redraw grid for new view
    
    # ===== Block Management Methods =====
    
    def select_block(self, block_id):
        """Select a block"""
        self.selected_block_id = block_id
        self.show_block_properties()
        self.highlight_selected_block()

    def deselect_all(self):
        """Deselect all blocks"""
        self.selected_block_id = None
        if hasattr(self, 'canvas'):
            self.canvas.delete("highlight")

        # Clear editor
        if hasattr(self, 'editor_frame'):
            # 清理鼠标滚轮绑定
            if hasattr(self.editor_frame, 'cleanup'):
                self.editor_frame.cleanup()

            for widget in self.editor_frame.winfo_children():
                widget.destroy()

            tk.Label(self.editor_frame, text=self.lang.get("select_block"),
                     fg="gray", font=("Arial", 12)).pack(expand=True)
    
    def highlight_selected_block(self):
        """Highlight the selected block"""
        if not hasattr(self, 'canvas'):
            return
            
        self.canvas.delete("highlight")
        
        if self.selected_block_id and self.selected_block_id in self.blocks:
            block = self.blocks[self.selected_block_id]
            
            # Draw highlight rectangle
            self.canvas.create_rectangle(
                block.x - 2, block.y - 2,
                block.x + block.width + 2, block.y + block.height + 2,
                outline="yellow", width=3, tags="highlight"
            )
            
            # Bring selected block to front
            rect_id, text_id = block.canvas_ids
            self.canvas.tag_raise(rect_id)
            self.canvas.tag_raise(text_id)
            self.canvas.tag_raise("highlight")
    
    # ===== Blocks List Methods =====

    def update_blocks_list(self, event=None):
        """Update the blocks list based on selected category"""
        if not hasattr(self, 'blocks_tree'):
            return

        # Clear treeview
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)

        category = self.category_var.get()

        # Update category dropdown values if needed
        if hasattr(self, 'category_dropdown'):
            categories = [self.lang.get("blocks_all")]
            for cat in self.block_loader.available_blocks.keys():
                categories.append(cat)
            self.category_dropdown['values'] = categories

        if category == self.lang.get("blocks_all") or category == "All":
            # Add all blocks by category
            for cat_name, blocks in self.block_loader.available_blocks.items():
                parent = self.blocks_tree.insert("", "end", text=cat_name, open=True)
                for block in blocks:
                    self.blocks_tree.insert(parent, "end", text=block["text"], values=(block["type"],))
        else:
            # Add blocks from specific category
            if category in self.block_loader.available_blocks:
                parent = self.blocks_tree.insert("", "end", text=category, open=True)
                for block in self.block_loader.available_blocks.get(category, []):
                    self.blocks_tree.insert(parent, "end", text=block["text"], values=(block["type"],))
    
    def select_block_from_list(self, event):
        """When a block is selected from the list"""
        if not hasattr(self, 'blocks_tree'):
            return
            
        selection = self.blocks_tree.selection()
        if selection:
            item = self.blocks_tree.item(selection[0])
            # Check if it's a block (not a category)
            if item["values"]:  # Has type value
                self.current_block_type = item["values"][0]
                self.current_block_text = item["text"]
                # Find the block data
                for category, blocks in self.block_loader.available_blocks.items():
                    for block in blocks:
                        if block["text"] == self.current_block_text and block["type"] == self.current_block_type:
                            self.current_block_data = block
                            break

    def add_block_from_list(self, event):
        """Add a block from the list to the canvas on double-click"""
        if not hasattr(self, 'blocks_tree') or not hasattr(self, 'canvas'):
            return

        selection = self.blocks_tree.selection()
        if not selection:
            return

        item = self.blocks_tree.item(selection[0])
        # Check if it's a block (not a category)
        if not item["values"]:
            return

        # Find the block data
        block_text = item["text"]
        block_type = item["values"][0]

        for category, blocks in self.block_loader.available_blocks.items():
            for block in blocks:
                if block["text"] == block_text and block["type"] == block_type:
                    # Place at center of visible canvas
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()

                    if canvas_width > 1 and canvas_height > 1:
                        # Get center of visible area
                        x = self.canvas.canvasx(canvas_width // 2)
                        y = self.canvas.canvasy(canvas_height // 2)
                    else:
                        # Default position
                        x, y = 100, 100

                    # Snap to grid
                    x = (x // 20) * 20
                    y = (y // 20) * 20

                    # Create block ID
                    block_id = f"block_{self.block_counter}"

                    # 特殊处理Code Pack块
                    if block["type"] == "code_pack":
                        try:
                            from plugins.code_pack_plugin import CodePackBlock
                            new_block = CodePackBlock(
                                block_id,
                                block["type"],
                                x, y,
                                text=block["text"],
                                content=block["content"]
                            )
                            # 确保is_code_pack属性被正确设置
                            new_block.is_code_pack = True
                        except ImportError as e:
                            print(f"Failed to create CodePackBlock: {e}")
                            new_block = CodeBlock(
                                block_id,
                                block["type"],
                                x, y,
                                text=block["text"],
                                content=block["content"]
                            )
                    else:
                        new_block = CodeBlock(
                            block_id,
                            block["type"],
                            x, y,
                            text=block["text"],
                            content=block["content"]
                        )

                    # Add to blocks dictionary
                    self.blocks[block_id] = new_block
                    self.block_counter += 1

                    # Draw block on canvas
                    self.draw_block(new_block)

                    # Select the new block
                    self.select_block(block_id)
                    return

    def start_drag_from_list(self, event):
        """Start dragging from the blocks list"""
        if not hasattr(self, 'blocks_tree'):
            return
            
        selection = self.blocks_tree.selection()
        if not selection:
            return
        
        item = self.blocks_tree.item(selection[0])
        # Check if it's a block (not a category)
        if item["values"]:  # Has type value
            self.dragging_from_list = True
            self.drag_block_type = item["values"][0]
            self.drag_block_text = item["text"]
            self.drag_start_x = event.x
            self.drag_start_y = event.y
    
    def drag_from_list(self, event):
        """Drag from the blocks list"""
        if not hasattr(self, 'blocks_tree'):
            return
            
        if not self.dragging_from_list:
            return
        
        # Check if we've moved enough to consider it a drag
        if (abs(event.x - self.drag_start_x) > 5 or 
            abs(event.y - self.drag_start_y) > 5):
            # We're dragging, change cursor
            self.blocks_tree.config(cursor="hand2")
    
    def end_drag_from_list(self, event):
        """End dragging from the blocks list and place block on canvas"""
        if not hasattr(self, 'blocks_tree') or not hasattr(self, 'canvas'):
            return
            
        if not self.dragging_from_list:
            return
        
        self.dragging_from_list = False
        self.blocks_tree.config(cursor="")
        
        # Check if mouse is over canvas
        canvas_x = self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_rooty()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        
        # Check if mouse is over canvas
        if (canvas_x <= mouse_x <= canvas_x + canvas_width and
                canvas_y <= mouse_y <= canvas_y + canvas_height):

            # Convert to canvas coordinates
            x = self.canvas.canvasx(mouse_x - canvas_x)
            y = self.canvas.canvasy(mouse_y - canvas_y)

            # Snap to grid
            x = (x // 20) * 20
            y = (y // 20) * 20

            # Find the block data
            for category, blocks in self.block_loader.available_blocks.items():
                for block in blocks:
                    if (block["text"] == self.drag_block_text and
                            block["type"] == self.drag_block_type):

                        # Create block ID
                        block_id = f"block_{self.block_counter}"

                        # 特殊处理Code Pack块
                        if block["type"] == "code_pack":
                            try:
                                from plugins.code_pack_plugin import CodePackBlock
                                new_block = CodePackBlock(
                                    block_id,
                                    block["type"],
                                    x, y,
                                    text=block["text"],
                                    content=block["content"]
                                )
                                # 确保is_code_pack属性被正确设置
                                new_block.is_code_pack = True
                            except ImportError as e:
                                print(f"Failed to create CodePackBlock: {e}")
                                new_block = CodeBlock(
                                    block_id,
                                    block["type"],
                                    x, y,
                                    text=block["text"],
                                    content=block["content"]
                                )
                        else:
                            new_block = CodeBlock(
                                block_id,
                                block["type"],
                                x, y,
                                text=block["text"],
                                content=block["content"]
                            )

                        # Add to blocks dictionary
                        self.blocks[block_id] = new_block
                        self.block_counter += 1

                        # Draw block on canvas
                        self.draw_block(new_block)

                        # Select the new block
                        self.select_block(block_id)
                        break

    def upgrade_to_code_pack_block(self, block):
        """将普通的CodeBlock升级为CodePackBlock"""
        try:
            from plugins.code_pack_plugin import CodePackBlock

            # 创建新的CodePackBlock，继承原块的所有属性
            code_pack_block = CodePackBlock(
                block.id,
                "code_pack",  # 设置为code_pack类型
                block.x, block.y,
                block.width, block.height,
                block.text, block.content
            )

            # 复制所有属性
            code_pack_block.color = block.color
            code_pack_block.connections = block.connections
            code_pack_block.continue_connection = block.continue_connection
            code_pack_block.prev_connections = block.prev_connections
            code_pack_block.is_unclosed_tag = block.is_unclosed_tag
            code_pack_block.end_connection = block.end_connection
            code_pack_block.canvas_ids = block.canvas_ids

            # 确保is_code_pack属性被设置
            code_pack_block.is_code_pack = True
            code_pack_block.pack_version = "1.0"

            # 替换原块
            self.blocks[block.id] = code_pack_block

            return code_pack_block
        except ImportError as e:
            print(f"Failed to upgrade to CodePackBlock: {e}")
            return block
    
    # ===== Block Editor Methods =====
    def show_code_pack_properties(self, block):
        """显示Code Pack块的属性"""
        # 确保块是CodePackBlock类型
        if not hasattr(block, 'is_code_pack') or not block.is_code_pack:
            # 尝试升级为CodePackBlock
            block = self.upgrade_to_code_pack_block(block)

            # 如果升级失败，显示错误信息
            if not hasattr(block, 'is_code_pack') or not block.is_code_pack:
                # 创建主框架
                main_frame = tk.Frame(self.editor_frame, bg="white")
                main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                tk.Label(main_frame, text="⚠️ Code Pack Plugin Error",
                         font=("Arial", 14, "bold"), bg="white", fg="red").pack(pady=20)

                tk.Label(main_frame, text="Cannot open Code Pack sub-editor.\nCode Pack plugin is not available.",
                         font=("Arial", 10), bg="white", fg="gray", wraplength=300).pack(pady=10)
                return

        # 创建主框架
        main_frame = tk.Frame(self.editor_frame, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        tk.Label(main_frame, text=f"Code Pack: {block.text}",
                 font=("Arial", 14, "bold"), bg="white", fg="#8E44AD").pack(pady=10)

        # 描述
        tk.Label(main_frame, text="A reusable container for code blocks",
                 font=("Arial", 10), bg="white", fg="gray").pack(pady=5)

        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # 文本编辑
        tk.Label(main_frame, text="Display Text:",
                 font=("Arial", 10, "bold"), bg="white").pack(anchor="w", pady=5)

        text_var = tk.StringVar(value=block.text)
        text_entry = tk.Entry(main_frame, textvariable=text_var, width=40)
        text_entry.pack(pady=5)

        def update_text():
            new_text = text_var.get().strip()
            if new_text:
                block.text = new_text
                # 更新画布显示
                if hasattr(self, 'canvas'):
                    self.draw_all_blocks()
                    self.highlight_selected_block()

        tk.Button(main_frame, text="Update Text", command=update_text,
                  width=15).pack(pady=10)

        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # 子编辑器按钮
        tk.Label(main_frame, text="Content Editor:",
                 font=("Arial", 10, "bold"), bg="white").pack(anchor="w", pady=5)

        tk.Label(main_frame, text="Click below to edit the internal content of this Code Pack",
                 font=("Arial", 9), bg="white", fg="gray", wraplength=300).pack(pady=5)

        def open_sub_editor():
            try:
                from plugins.code_pack_plugin import show_code_pack_editor
                show_code_pack_editor(self, block)
            except ImportError as e:
                messagebox.showerror("Plugin Missing",
                                     f"Code Pack plugin not available: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open sub-editor: {e}")

        editor_btn = tk.Button(main_frame, text="🛠️ Open Sub-Editor",
                               command=open_sub_editor,
                               bg="#8E44AD", fg="white", font=("Arial", 10, "bold"),
                               height=2, width=20)
        editor_btn.pack(pady=15)

        # 信息显示
        try:
            pack_data = block.get_pack_data()
            if pack_data:
                block_count = len(pack_data.get("blocks", {}))
                tk.Label(main_frame,
                         text=f"Contains: {block_count} internal block(s)",
                         font=("Arial", 9), bg="white").pack(pady=5)
        except Exception as e:
            print(f"Error getting pack data: {e}")

        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # 删除按钮
        delete_btn = tk.Button(main_frame, text="Delete Code Pack",
                               bg="#ffcccc", fg="black",
                               command=lambda: self.delete_block_without_confirm(block.id),
                               width=20)
        delete_btn.pack(pady=10)

    # 在builder.py中添加新方法
    def open_code_pack_sub_editor(self, block):
        """打开Code Pack子编辑器"""
        try:
            # 检查插件是否可用
            if CODE_PACK_PLUGIN_AVAILABLE and show_code_pack_editor:
                show_code_pack_editor(self, block)
            else:
                # 如果插件不可用，尝试动态导入
                try:
                    from plugins.code_pack_plugin import show_code_pack_editor as show_editor
                    show_editor(self, block)
                except ImportError:
                    messagebox.showerror("Plugin Missing",
                                         "Code Pack plugin not available.\n"
                                         "Make sure plugins/code_pack_plugin.py exists.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open sub-editor: {e}")

    def show_simple_code_pack_editor(self, block):
        """显示简化的Code Pack编辑器"""
        # 创建主框架
        main_frame = tk.Frame(self.editor_frame, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        tk.Label(main_frame, text=f"Code Pack: {block.text}",
                 font=("Arial", 14, "bold"), bg="white", fg="#8E44AD").pack(pady=10)

        # 描述
        tk.Label(main_frame, text="通过选择.txt文件来设置代码内容",
                 font=("Arial", 10), bg="white", fg="gray").pack(pady=5)

        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # 当前内容预览
        tk.Label(main_frame, text="当前内容预览:",
                 font=("Arial", 10, "bold"), bg="white").pack(anchor="w", pady=5)

        # 创建文本框显示内容（只读）
        content_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 添加滚动条
        text_scrollbar = tk.Scrollbar(content_frame)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        content_text = tk.Text(content_frame, height=10, width=45,
                               wrap=tk.WORD, font=("Courier", 9),
                               yscrollcommand=text_scrollbar.set)
        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.config(command=content_text.yview)

        # 插入内容
        content_text.insert("1.0", block.content)
        content_text.config(state=tk.DISABLED)  # 设置为只读

        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # 更改内容按钮
        def change_content():
            try:
                from plugins.code_pack_plugin import show_code_pack_editor
                show_code_pack_editor(self, block)
            except ImportError as e:
                messagebox.showerror("插件错误", f"Code Pack插件不可用: {e}")

        change_btn = tk.Button(main_frame, text="📄 更改内容",
                               command=change_content,
                               bg="#8E44AD", fg="white", font=("Arial", 10, "bold"),
                               height=2, width=20)
        change_btn.pack(pady=15)

        # 手动编辑按钮（可选）
        def manual_edit():
            # 创建编辑窗口
            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"编辑Code Pack内容: {block.text}")
            edit_window.geometry("800x600")

            # 创建文本框
            edit_text = tk.Text(edit_window, wrap=tk.WORD, font=("Courier", 10))
            edit_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 插入当前内容
            edit_text.insert("1.0", block.content)

            # 添加按钮框架
            button_frame = tk.Frame(edit_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            def save_content():
                block.content = edit_text.get("1.0", tk.END).strip()
                # 更新显示
                self.draw_all_blocks()
                self.show_block_properties()
                edit_window.destroy()
                messagebox.showinfo("保存成功", "代码包内容已更新")

            tk.Button(button_frame, text="保存", command=save_content,
                      bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=5)

            tk.Button(button_frame, text="取消", command=edit_window.destroy,
                      bg="#f44336", fg="white", width=15).pack(side=tk.LEFT, padx=5)

        tk.Button(main_frame, text="✏️ 手动编辑",
                  command=manual_edit, width=15).pack(pady=5)

        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # 文本编辑
        tk.Label(main_frame, text="显示文本:",
                 font=("Arial", 10, "bold"), bg="white").pack(anchor="w", pady=5)

        text_var = tk.StringVar(value=block.text)
        text_entry = tk.Entry(main_frame, textvariable=text_var, width=40)
        text_entry.pack(pady=5)

        def update_text():
            new_text = text_var.get().strip()
            if new_text:
                block.text = new_text
                # 更新画布显示
                if hasattr(self, 'canvas'):
                    self.draw_all_blocks()
                    self.highlight_selected_block()

        tk.Button(main_frame, text="更新显示文本", command=update_text,
                  width=15).pack(pady=10)

        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # 删除按钮
        delete_btn = tk.Button(main_frame, text="删除Code Pack",
                               bg="#ffcccc", fg="black",
                               command=lambda: self.delete_block_without_confirm(block.id),
                               width=20)
        delete_btn.pack(pady=10)

        # 注意信息
        tk.Label(main_frame,
                 text="注意：代码包内容在导出时会自动正确缩进",
                 font=("Arial", 8), bg="white", fg="green").pack(pady=5)

    def show_block_properties(self):
        """显示选中块的属性 - 改进：支持Code Pack块"""
        if not self.selected_block_id or self.selected_block_id not in self.blocks:
            return

        # 清空编辑器框架
        if hasattr(self, 'editor_frame'):
            for widget in self.editor_frame.winfo_children():
                widget.destroy()

        block = self.blocks[self.selected_block_id]

        # 检查是否为Code Pack块
        is_code_pack = False

        # 检查类型
        if block.type == "code_pack":
            is_code_pack = True
        # 检查属性
        elif hasattr(block, 'is_code_pack') and block.is_code_pack:
            is_code_pack = True

        # 如果块是Code Pack类型但不是CodePackBlock实例，尝试升级
        if is_code_pack and not hasattr(block, 'load_from_file'):
            # 尝试导入并升级
            try:
                from plugins.code_pack_plugin import CodePackBlock
                # 创建新的CodePackBlock，继承原块的所有属性
                code_pack_block = CodePackBlock(
                    block.id,
                    "code_pack",
                    block.x, block.y,
                    block.width, block.height,
                    block.text, block.content
                )
                # 复制所有属性
                code_pack_block.color = block.color
                code_pack_block.connections = block.connections
                code_pack_block.continue_connection = block.continue_connection
                code_pack_block.prev_connections = block.prev_connections
                code_pack_block.is_unclosed_tag = block.is_unclosed_tag
                code_pack_block.end_connection = block.end_connection
                code_pack_block.canvas_ids = block.canvas_ids

                # 替换原块
                self.blocks[block.id] = code_pack_block
                block = code_pack_block
            except ImportError:
                # 如果插件不可用，保持原块
                pass

        # 如果块是Code Pack，显示简化的编辑器
        if is_code_pack and hasattr(block, 'load_from_file'):
            self.show_simple_code_pack_editor(block)
            return

        # ... (原有的普通块编辑代码保持不变)

        # ... 原有的普通块编辑代码 ...
        # ... [保持原有代码不变] ...

        # 创建主框架
        main_frame = tk.Frame(self.editor_frame, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0

        # 块类型标签
        tk.Label(main_frame, text=f"Block: {block.text}",
                 font=("Arial", 12, "bold"), bg="white").grid(row=row, column=0, columnspan=2, pady=10, sticky="w")
        row += 1

        # 内容编辑器
        tk.Label(main_frame, text=self.lang.get("content"),
                 font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, sticky="w", pady=5)
        row += 1

        # 内容文本框
        content_text = tk.Text(main_frame, height=12, width=45, wrap=tk.WORD, font=("Courier", 10))
        content_text.insert("1.0", block.content)
        content_text.grid(row=row, column=0, columnspan=2, pady=5, sticky="nsew")
        row += 1

        def update_content():
            # 使用块的update_content方法
            block.update_content(content_text.get("1.0", tk.END).strip())

            # 重绘块
            if hasattr(self, 'canvas'):
                self.draw_all_blocks()
                self.highlight_selected_block()

        # 更新按钮
        update_btn = tk.Button(main_frame, text=self.lang.get("update"), command=update_content,
                               width=20, bg="#4CAF50", fg="white")
        update_btn.grid(row=row, column=0, columnspan=2, pady=10, sticky="ew")
        row += 1

        # 配置网格权重
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # 颜色编辑器
        tk.Label(main_frame, text=self.lang.get("color"),
                 font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, sticky="w", pady=5)

        color_frame = tk.Frame(main_frame, bg="white")
        color_frame.grid(row=row, column=1, pady=5, sticky="w")

        color_btn = tk.Button(color_frame, text=self.lang.get("choose"), width=10,
                              command=lambda: self.choose_block_color(block))
        color_btn.pack(side=tk.LEFT, padx=2)

        color_display = tk.Label(color_frame, text="     ", bg=block.color, relief="sunken", width=10)
        color_display.pack(side=tk.LEFT, padx=2)
        row += 1

        # 连接按钮部分
        tk.Label(main_frame, text=self.lang.get("connections"),
                 font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, columnspan=2, pady=(15, 5), sticky="w")
        row += 1

        # 确定当前连接状态
        has_sequence = False
        for start_id, end_id in self.sequence_lines:
            if start_id == self.selected_block_id:
                has_sequence = True
                break

        has_end = False
        for control_id, end_id in self.end_lines:
            if control_id == self.selected_block_id:
                has_end = True
                break

        has_continue = False
        for start_id, end_id in self.continue_lines:
            if start_id == self.selected_block_id:
                has_continue = True
                break

        # 序列连接按钮
        seq_text = self.lang.get("disconnect_sequence") if has_sequence else self.lang.get("connect_sequence")
        seq_btn = tk.Button(main_frame, text=seq_text,
                            command=lambda: self.toggle_sequence_connection(),
                            width=30)
        seq_btn.grid(row=row, column=0, columnspan=2, pady=5, sticky="ew")
        row += 1

        # 结束连接按钮（针对需要缩进的块）
        if block.requires_indentation():
            end_text = self.lang.get("disconnect_end") if has_end else self.lang.get("set_end_block")
            end_btn = tk.Button(main_frame, text=end_text,
                                command=lambda: self.toggle_end_connection(),
                                width=30)
            end_btn.grid(row=row, column=0, columnspan=2, pady=5, sticky="ew")
            row += 1

        # 继续连接按钮
        continue_text = self.lang.get("discontinue_line") if has_continue else self.lang.get("continue_line")
        continue_btn = tk.Button(main_frame, text=continue_text,
                                 command=lambda: self.toggle_continue_connection(),
                                 width=30)
        continue_btn.grid(row=row, column=0, columnspan=2, pady=5, sticky="ew")
        row += 1

        # 显示当前连接
        if has_sequence or has_end or has_continue:
            tk.Label(main_frame, text=self.lang.get("current_connections"),
                     font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, columnspan=2, pady=(15, 5),
                                                                  sticky="w")
            row += 1

            # 显示序列连接
            if has_sequence:
                tk.Label(main_frame, text=self.lang.get("sequence_to"),
                         bg="white", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w",
                                                                     pady=(0, 2))
                row += 1
                for start_id, end_id in self.sequence_lines:
                    if start_id == self.selected_block_id and end_id in self.blocks:
                        conn_block = self.blocks[end_id]
                        tk.Label(main_frame, text=f"  • {conn_block.text}",
                                 bg="white", font=("Arial", 9)).grid(row=row, column=0, columnspan=2, sticky="w")
                        row += 1

            # 显示结束连接
            if has_end:
                tk.Label(main_frame, text=self.lang.get("end_block"),
                         bg="white", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w",
                                                                     pady=(5, 2))
                row += 1
                for control_id, end_id in self.end_lines:
                    if control_id == self.selected_block_id and end_id in self.blocks:
                        conn_block = self.blocks[end_id]
                        tk.Label(main_frame, text=f"  • {conn_block.text}",
                                 bg="white", font=("Arial", 9)).grid(row=row, column=0, columnspan=2, sticky="w")
                        row += 1

            # 显示继续连接
            if has_continue:
                tk.Label(main_frame, text=self.lang.get("continue_to"),
                         bg="white", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w",
                                                                     pady=(5, 2))
                row += 1
                for start_id, end_id in self.continue_lines:
                    if start_id == self.selected_block_id and end_id in self.blocks:
                        conn_block = self.blocks[end_id]
                        tk.Label(main_frame, text=f"  • {conn_block.text}",
                                 bg="white", font=("Arial", 9)).grid(row=row, column=0, columnspan=2, sticky="w")
                        row += 1

        # 删除按钮
        delete_btn = tk.Button(main_frame, text=self.lang.get("delete_block"),
                               bg="#ffcccc", fg="black",
                               command=lambda: self.delete_block_without_confirm(block.id),
                               width=30)
        delete_btn.grid(row=row, column=0, columnspan=2, pady=(20, 10), sticky="ew")

        # 配置网格权重
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # 让文本框行扩展

        # 绑定Ctrl-F快捷键
        def on_ctrl_f(event):
            update_content()
            return "break"  # 阻止默认行为

        content_text.bind("<Control-f>", on_ctrl_f)
        content_text.bind("<Control-F>", on_ctrl_f)

        # 焦点设置到文本框
        content_text.focus_set()

    def choose_block_color(self, block):
        """Change the color of a block"""
        color = colorchooser.askcolor(title="Choose block color")
        if color and color[1]:
            block.color = color[1]
            if hasattr(self, 'canvas'):
                self.draw_all_blocks()
                self.highlight_selected_block()
    
    # ===== Connection Methods =====
    
    def start_connection(self, start_block_id=None):
        """Start connecting blocks (sequence line)"""
        if start_block_id is None:
            if self.selected_block_id:
                start_block_id = self.selected_block_id
            else:
                return
        
        if start_block_id not in self.blocks:
            return
        
        # Check if block already has sequence connections
        block = self.blocks[start_block_id]
        if block.connections:
            # Delete message box, disconnect directly
            self.disconnect_sequence(start_block_id)
        
        self.connecting_mode = True
        self.start_connection_block = start_block_id
        self.canvas.config(cursor="cross")
        
        # Bind escape key to cancel
        self.root.bind("<Escape>", self.cancel_connection)
    
    def start_end_connection(self, control_block_id=None):
        """Start connecting end block (for if/for/while/function)"""
        if control_block_id is None:
            if self.selected_block_id:
                control_block_id = self.selected_block_id
            else:
                return
        
        if control_block_id not in self.blocks:
            return
        
        block = self.blocks[control_block_id]
        if not block.requires_indentation():
            messagebox.showwarning("Invalid Block", 
                                 "This block type does not require an end connection.")
            return
        
        # Check if block already has an end connection
        if block.end_connection:
            # Delete message box, disconnect directly
            self.disconnect_end(control_block_id)
        
        self.end_connecting_mode = True
        self.start_connection_block = control_block_id
        self.canvas.config(cursor="cross")
        
        # Bind escape key to cancel
        self.root.bind("<Escape>", self.cancel_connection)

    def start_continue_connection(self, block_id=None):
        """Start connecting continue line"""
        if block_id is None:
            if self.selected_block_id:
                block_id = self.selected_block_id
            else:
                return

        if block_id not in self.blocks:
            return

        # Check if block already has a continue connection
        block = self.blocks[block_id]
        if block.continue_connection:
            # Delete message box, disconnect directly
            self.disconnect_continue_line(block_id)

        self.continue_connecting_mode = True
        self.start_connection_block = block_id
        self.canvas.config(cursor="cross")

        # Bind escape key to cancel
        self.root.bind("<Escape>", self.cancel_continue_connection)

    def handle_connection_click(self, x, y):
        """Handle click when in connecting mode"""
        # Find clicked block
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            if (block.x <= x <= block.x + block.width and
                    block.y <= y <= block.y + block.height):
                clicked_block_id = block_id
                break

        if clicked_block_id and clicked_block_id != self.start_connection_block:
            # Add connection
            start_block = self.blocks[self.start_connection_block]

            if clicked_block_id not in start_block.connections:
                start_block.connections.append(clicked_block_id)

                # Add to sequence lines
                if (self.start_connection_block, clicked_block_id) not in self.sequence_lines:
                    self.sequence_lines.append((self.start_connection_block, clicked_block_id))

                # Redraw connections
                self.draw_all_connections()

        # Reset connection mode
        self.cancel_connection()

    def handle_end_connection_click(self, x, y):
        """Handle click when in end connecting mode"""
        # Find clicked block
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            if (block.x <= x <= block.x + block.width and
                    block.y <= y <= block.y + block.height):
                clicked_block_id = block_id
                break

        if clicked_block_id and clicked_block_id != self.start_connection_block:
            # Set end connection
            control_block = self.blocks[self.start_connection_block]
            control_block.end_connection = clicked_block_id

            # Add to end lines
            if (self.start_connection_block, clicked_block_id) not in self.end_lines:
                self.end_lines.append((self.start_connection_block, clicked_block_id))

            # Redraw connections
            self.draw_all_connections()

        # Reset end connection mode
        self.cancel_connection()

    def handle_continue_click(self, x, y):
        """Handle click when in continue connecting mode"""
        clicked_block_id = None
        for block_id, block in self.blocks.items():
            if (block.x <= x <= block.x + block.width and
                    block.y <= y <= block.y + block.height):
                clicked_block_id = block_id
                break

        if clicked_block_id and clicked_block_id != self.start_connection_block:
            # Check if start block already has a continue connection
            start_block = self.blocks[self.start_connection_block]
            if start_block.continue_connection:
                # Remove old connection
                old_end_id = start_block.continue_connection
                # Remove from continue lines
                self.continue_lines = [(s, e) for s, e in self.continue_lines if s != self.start_connection_block]

            # Add continue connection
            start_block.continue_connection = clicked_block_id

            # Add to continue lines
            if (self.start_connection_block, clicked_block_id) not in self.continue_lines:
                self.continue_lines.append((self.start_connection_block, clicked_block_id))

            # Update the end block to have a prev connection
            end_block = self.blocks[clicked_block_id]
            if self.start_connection_block not in end_block.prev_connections:
                end_block.prev_connections.append(self.start_connection_block)

            # Redraw everything
            self.draw_all_blocks()

            # Update the editor to show the new connection
            if self.selected_block_id:
                self.show_block_properties()

        # Reset connection mode
        self.cancel_continue_connection()
    
    def cancel_connection(self, event=None):
        """Cancel connection mode"""
        self.connecting_mode = False
        self.end_connecting_mode = False
        self.start_connection_block = None
        self.canvas.config(cursor="")
        self.root.unbind("<Escape>")

    def cancel_continue_connection(self, event=None):
        """Cancel continue connection mode"""
        self.continue_connecting_mode = False
        self.start_connection_block = None
        self.canvas.config(cursor="")
        self.root.unbind("<Escape>")
    
    def toggle_sequence_connection(self, event=None):
        """Toggle sequence connection for selected block"""
        if self.selected_block_id:
            block = self.blocks[self.selected_block_id]
            has_sequence = len(block.connections) > 0
            if has_sequence:
                self.disconnect_sequence(self.selected_block_id)
            else:
                self.start_connection()
    
    def toggle_end_connection(self, event=None):
        """Toggle end connection for selected block"""
        if self.selected_block_id:
            block = self.blocks[self.selected_block_id]
            if block.requires_indentation():
                has_end = block.end_connection is not None
                if has_end:
                    self.disconnect_end(self.selected_block_id)
                else:
                    self.start_end_connection()
    
    def toggle_continue_connection(self, event=None):
        """Toggle continue connection for selected block"""
        if self.selected_block_id:
            block = self.blocks[self.selected_block_id]
            has_continue = block.continue_connection is not None
            if has_continue:
                self.disconnect_continue_line(self.selected_block_id)
            else:
                self.start_continue_connection()
    
    def disconnect_sequence(self, block_id):
        """Disconnect sequence line from block"""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            # Remove all connections from this block
            for conn_id in block.connections[:]:
                self.sequence_lines = [(s, e) for s, e in self.sequence_lines if not (s == block_id and e == conn_id)]
                block.connections.remove(conn_id)
            self.draw_all_connections()
    
    def disconnect_end(self, block_id):
        """Disconnect end line from block"""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            if block.end_connection:
                # Remove from end lines
                self.end_lines = [(c, e) for c, e in self.end_lines if c != block_id]
                block.end_connection = None
                self.draw_all_connections()
    
    def disconnect_continue_line(self, block_id):
        """Disconnect continue line from block"""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            if block.continue_connection:
                # Remove from continue lines
                self.continue_lines = [(s, e) for s, e in self.continue_lines if s != block_id]
                block.continue_connection = None
                self.draw_all_connections()
    
    # ===== Block Operations =====
    
    def show_block_context_menu(self, block_id, event):
        """Show context menu for a block"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Delete", command=lambda: self.delete_block(block_id))
        
        block = self.blocks[block_id]
        
        # Check current connection states
        has_sequence = len(block.connections) > 0
        has_end = block.end_connection is not None
        has_continue = block.continue_connection is not None
        
        # Sequence connection toggle
        seq_text = "Disconnect Sequence" if has_sequence else "Connect Sequence"
        menu.add_command(label=seq_text, 
                        command=lambda: self.start_connection(block_id))
        
        # End connection toggle for blocks that require indentation
        if block.requires_indentation():
            end_text = "Disconnect End" if has_end else "Connect End"
            menu.add_command(label=end_text, 
                           command=lambda: self.start_end_connection(block_id))
        
        # Continue connection toggle
        continue_text = "Disconnect Continue" if has_continue else "Continue Line"
        menu.add_command(label=continue_text, 
                        command=lambda: self.start_continue_connection(block_id))
        
        menu.add_separator()
        menu.add_command(label="Duplicate", command=lambda: self.duplicate_block(block_id))
        
        # Show the menu
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def delete_block(self, block_id):
        """Delete a block with confirmation (for UI button)"""
        if block_id not in self.blocks:
            return
        
        response = messagebox.askyesno("Delete Block", 
                                      f"Are you sure you want to delete block '{self.blocks[block_id].text}'?")
        if response:
            self._delete_block_impl(block_id)
    
    def delete_block_without_confirm(self, block_id):
        """Delete a block without confirmation (for keyboard shortcut)"""
        if block_id in self.blocks:
            self._delete_block_impl(block_id)
    
    def delete_selected_block(self, event=None):
        """Delete the selected block with confirmation (UI button)"""
        if self.selected_block_id:
            self.delete_block(self.selected_block_id)
    
    def delete_selected_block_no_confirm(self, event=None):
        """Delete the selected block without confirmation (keyboard shortcut)"""
        if self.selected_block_id:
            self.delete_block_without_confirm(self.selected_block_id)

    def _delete_block_impl(self, block_id):
        """内部实现：删除块（同时删除相关折点）"""
        # 删除相关的连接线折点
        keys_to_remove = []
        for (start_id, end_id) in list(self.polyline_points.keys()):
            if start_id == block_id or end_id == block_id:
                keys_to_remove.append((start_id, end_id))

        for key in keys_to_remove:
            del self.polyline_points[key]

        # 删除相关的连接线ID
        keys_to_remove = []
        for key in list(self.connection_lines.keys()):
            if key[0] == block_id or key[1] == block_id:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.connection_lines[key]

        # 原有的删除逻辑...
        self.sequence_lines = [(s, e) for s, e in self.sequence_lines if s != block_id and e != block_id]
        self.end_lines = [(c, e) for c, e in self.end_lines if c != block_id and e != block_id]
        self.continue_lines = [(s, e) for s, e in self.continue_lines if s != block_id and e != block_id]

        # 从其他块的连接中移除
        for other_id, other_block in self.blocks.items():
            if block_id in other_block.connections:
                other_block.connections.remove(block_id)
            if other_block.end_connection == block_id:
                other_block.end_connection = None
            if other_block.continue_connection == block_id:
                other_block.continue_connection = None

        # 删除画布上的块
        if hasattr(self, 'canvas'):
            self.canvas.delete("block")
            self.canvas.delete("block_text")
            self.canvas.delete("polyline_dot")

        del self.blocks[block_id]

        # 重绘
        if hasattr(self, 'canvas'):
            self.draw_all_blocks()

        # 清除选择
        if self.selected_block_id == block_id:
            self.deselect_all()
    
    def duplicate_block(self, block_id):
        """Duplicate a block"""
        if block_id not in self.blocks:
            return
        
        original = self.blocks[block_id]
        
        # Create new block with offset
        new_id = f"block_{self.block_counter}"
        new_block = CodeBlock(
            new_id,
            original.type,
            original.x + 40, original.y + 40,
            original.width, original.height,
            original.text, original.content
        )
        new_block.color = original.color
        
        # Add to blocks
        self.blocks[new_id] = new_block
        self.block_counter += 1
        
        # Draw the new block
        if hasattr(self, 'canvas'):
            self.draw_block(new_block)
        
        # Select the new block
        self.select_block(new_id)
    
    # ===== File Operations =====
    
    def new_project(self):
        """Create a new project"""
        if self.blocks:
            response = messagebox.askyesnocancel("New Project", 
                                                "Do you want to save the current project before clearing?")
            if response is None:  # Cancel
                return
            elif response:  # Yes - save
                self.save_project()
        
        # Clear everything
        self.blocks = {}
        self.block_counter = 0
        self.selected_block_id = None
        self.sequence_lines = []
        self.end_lines = []
        self.continue_lines = []
        self.polyline_points = {}
        self.connection_lines = {}
        
        # 重置选择模式
        self.select_mode = False
        self.select_mode_var.set(False)
        self.selected_polyline_point = None
        
        # Reset project name
        self.project_name = self.lang.get("untitled_project")
        self.root.title(f"AntimonyIDE - {self.project_name}")
        
        # Clear canvas
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")
            self.draw_grid()
        
        # Clear editor
        self.deselect_all()
    
    def save_project(self):
        """Save the project to a file - Save as functionality"""
        self.file_handler.save_project_as()
    
    def save_project_as(self):
        """Save project with a new name - calls the original save dialog"""
        self.file_handler.save_project_as()
    
    def import_project(self):
        """Import a saved project"""
        self.file_handler.import_project()
    
    def export_code(self):
        """Export code based on current language mode"""
        if not self.blocks:
            messagebox.showwarning("No Blocks", "There are no blocks to export.")
            return

        # Generate code with proper indentation
        code_lines = self.generate_code_with_indentation()

        # Apply language-specific export rules
        processed_lines = self.lang_mode.apply_export_rules(
            code_lines, 
            self.blocks, 
            {"end_lines": self.end_lines}
        )

        # Get current language mode info
        mode_info = self.lang_mode.get_mode_info()
        file_extension = mode_info["file_extension"]

        # Generate full code
        code = "\n".join(processed_lines)
        header = self.generate_code_header()
        full_code = header + code

        # Ask for filename
        filename = filedialog.asksaveasfilename(
            defaultextension=file_extension,
            filetypes=[(f"{mode_info['name']} Files", f"*{file_extension}"), ("All Files", "*.*")],
            initialfile=f"{self.project_name}{file_extension}"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_code)
                
                # Save as last exported file
                self.last_export_file = filename
                
                messagebox.showinfo("Export Successful",
                                  f"{mode_info['name']} code exported to {filename}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export file: {e}")

    def generate_code_header(self):
        """Generate code header based on language mode"""
        mode_info = self.lang_mode.get_mode_info()

        headers = {
            "python": f"""""",
            "html": f"""""",
            "c_cpp": f"""""",
            "java": f""""""
        }

        return headers.get(self.lang_mode.current_mode, "")
    
    def generate_code_with_indentation(self):
        """Generate Python code with proper indentation"""
        # Build connection maps
        next_map = {}
        for start_id, end_id in self.sequence_lines:
            if start_id not in next_map:
                next_map[start_id] = []
            next_map[start_id].append(end_id)
        
        # Build end block map
        end_map = {}
        for control_id, end_id in self.end_lines:
            end_map[control_id] = end_id
        
        # Build continue line map
        continue_map = {}
        for start_id, end_id in self.continue_lines:
            continue_map[start_id] = end_id
        
        # Find start blocks (blocks with no incoming connections)
        incoming = {}
        for start_id, end_id in self.sequence_lines:
            incoming[end_id] = incoming.get(end_id, 0) + 1
        
        start_blocks = []
        for block_id, block in self.blocks.items():
            if block_id not in incoming:
                # Check if it's not an end block
                is_end_block = False
                for control_id, end_id in self.end_lines:
                    if end_id == block_id:
                        is_end_block = True
                        break
                if not is_end_block:
                    start_blocks.append(block_id)
        
        # If no start blocks, use all non-end blocks
        if not start_blocks:
            for block_id, block in self.blocks.items():
                is_end_block = False
                for control_id, end_id in self.end_lines:
                    if end_id == block_id:
                        is_end_block = True
                        break
                if not is_end_block:
                    start_blocks.append(block_id)
        
        # Generate code
        code_lines = []
        code_lines.append(f"# Code generated from AntimonyIDE project: {self.project_name}")
        code_lines.append("# Generated on: " + time.strftime("%Y-%m-%d %H:%M:%S"))
        code_lines.append("")
        
        # Track visited blocks and current indentation
        visited = set()
        
        # Stack to track nested control structures
        control_stack = []  # Each element is (control_block_id, indent_level_when_started)
        
        def process_block(block_id, current_indent, is_continue=False):
            """Process a block and return its lines"""
            if block_id in visited:
                return []
            
            visited.add(block_id)
            block = self.blocks[block_id]
            lines = []
            
            # Check if this is an end block for a control structure
            for i, (control_id, start_indent) in enumerate(control_stack):
                if end_map.get(control_id) == block_id:
                    # This is the end block for this control structure
                    # Remove this control from stack
                    control_stack.pop(i)
                    # End block should be at the control's starting indent level
                    current_indent = start_indent
                    break
            
            # Get the block's content with current indentation
            content_lines = block.content.split('\n')
            
            if is_continue:
                # For continue blocks, add to the last line
                if lines and content_lines:
                    lines[-1] = lines[-1].rstrip() + " " + content_lines[0].strip()
                    for line in content_lines[1:]:
                        if line.strip():  # Skip empty lines
                            indent_str = "    " * current_indent
                            lines.append(f"{indent_str}{line}")
                elif content_lines:
                    for line in content_lines:
                        if line.strip():
                            indent_str = "    " * current_indent
                            lines.append(f"{indent_str}{line}")
            else:
                # Normal block
                for line in content_lines:
                    if line.strip():  # Skip empty lines
                        indent_str = "    " * current_indent
                        lines.append(f"{indent_str}{line}")
            
            # Check if this block requires indentation
            if block.requires_indentation() and block_id in end_map:
                # Push onto stack
                control_stack.append((block_id, current_indent))
                # Increase indent for next blocks
                next_indent = current_indent + 1
            else:
                next_indent = current_indent
            
            # Process continue connection first (same line)
            if block_id in continue_map:
                next_id = continue_map[block_id]
                continue_lines = process_block(next_id, current_indent, is_continue=True)
                if continue_lines:
                    # Merge with last line if possible
                    if lines and continue_lines:
                        lines[-1] = lines[-1].rstrip() + " " + continue_lines[0].strip()
                        lines.extend(continue_lines[1:])
                    else:
                        lines.extend(continue_lines)
            
            # Process connected blocks
            if block_id in next_map:
                for next_id in next_map[block_id]:
                    # Check if next block is already an end block for something in stack
                    is_end = False
                    for control_id, start_indent in control_stack:
                        if end_map.get(control_id) == next_id:
                            is_end = True
                            # Process end block at control's indent level
                            next_lines = process_block(next_id, start_indent)
                            lines.extend(next_lines)
                            break
                    
                    if not is_end:
                        next_lines = process_block(next_id, next_indent)
                        lines.extend(next_lines)
            
            return lines
        
        # Process all start blocks
        for start_id in start_blocks:
            result = process_block(start_id, 0)
            if result:
                code_lines.extend(result)
        
        # Add any unvisited blocks
        for block_id, block in self.blocks.items():
            if block_id not in visited:
                code_lines.append(block.content)
        
        return code_lines
    
    def run_python_code(self, filename):
        """Run the exported Python code"""
        try:
            # Check if running in .exe environment
            if getattr(sys, 'frozen', False):
                # In .exe environment, sys.executable points to .exe itself
                # We need to find system Python interpreter
                import shutil
                
                # Try possible Python interpreter commands
                python_commands = ['python', 'python3', 'py']
                
                for cmd in python_commands:
                    if shutil.which(cmd):
                        # Run script with found Python interpreter
                        result = subprocess.run([cmd, filename], 
                                              capture_output=True, text=True)
                        break
                else:
                    # No Python interpreter found
                    self.root.after(0, messagebox.showerror, 
                                   "Python Not Found",
                                   "Could not find Python interpreter on your system.\n"
                                   "Please make sure Python is installed and in your PATH.")
                    return
            else:
                # In development environment, use sys.executable
                result = subprocess.run([sys.executable, filename], 
                                      capture_output=True, text=True)
            
            # Update UI in main thread
            self.root.after(0, self._show_run_output, filename, result)
            
        except FileNotFoundError:
            self.root.after(0, messagebox.showerror, 
                           "Python Not Found",
                           "Could not find Python interpreter on your system.\n"
                           "Please make sure Python is installed and in your PATH.")
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Run Error", f"Could not run Python code: {e}")

    def _show_run_output(self, filename, result):
        """Show run output in main thread"""
        # Show output
        output_window = tk.Toplevel(self.root)
        output_window.title(f"Output: {os.path.basename(filename)}")
        output_window.geometry("600x400")
        
        # Create text widget for output
        text_widget = tk.Text(output_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add output
        text_widget.insert("1.0", f"Output:\n{result.stdout}")
        if result.stderr:
            text_widget.insert(tk.END, f"\n\nErrors:\n{result.stderr}")
        
        # Make text read-only
        text_widget.config(state=tk.DISABLED)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(text_widget)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

    def import_package(self):
        """Import package(s) from packages folder with a dialog window"""
        import glob
        
        # Get list of JSON files in packages folder
        packages_dir = "packages"
        if not os.path.exists(packages_dir):
            os.makedirs(packages_dir)
        
        json_files = glob.glob(os.path.join(packages_dir, "*.json"))
        
        # Create a dialog window with listbox
        dialog = tk.Toplevel(self.root)
        dialog.title("Import Package")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Label
        tk.Label(dialog, text="Select package(s) to import:").pack(pady=10)
        
        # Listbox with multi-select
        listbox_frame = tk.Frame(dialog)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE)
        scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate listbox with package names
        for json_file in json_files:
            listbox.insert(tk.END, os.path.basename(json_file))
        
        selected_files = []
        
        def load_selected():
            """Load selected package files"""
            indices = listbox.curselection()
            if not indices:
                messagebox.showwarning("No Selection", "Please select at least one package.")
                return
            
            imported_count = 0
            for idx in indices:
                filename = os.path.join(packages_dir, listbox.get(idx))
                try:
                    default_category = os.path.basename(filename).replace('.json', '')
                    category_name = simpledialog.askstring(
                        "Package Category",
                        f"Enter category name for {os.path.basename(filename)}:",
                        initialvalue=default_category
                    )
                    
                    if category_name:
                        added_count, actual_category = self.block_loader.add_custom_package(filename, category_name)
                        if added_count > 0:
                            imported_count += added_count
                except Exception as e:
                    messagebox.showerror("Import Error", f"Could not import {filename}:\n{str(e)}")
            
            if imported_count > 0:
                self.update_blocks_list()
                if hasattr(self, 'category_dropdown'):
                    categories = [self.lang.get("blocks_all")]
                    for category in self.block_loader.available_blocks.keys():
                        categories.append(category)
                    self.category_dropdown['values'] = categories
                messagebox.showinfo("Import Complete", f"Successfully imported {imported_count} block(s).")
            
            dialog.destroy()
        
        def browse_external():
            """Browse for external JSON files and copy to packages folder"""
            filenames = filedialog.askopenfilenames(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                title="Select Package JSON Files"
            )
            
            if filenames:
                copied_count = 0
                for filename in filenames:
                    dest = os.path.join(packages_dir, os.path.basename(filename))
                    try:
                        import shutil
                        shutil.copy2(filename, dest)
                        copied_count += 1
                    except Exception as e:
                        messagebox.showerror("Copy Error", f"Could not copy {filename}:\n{str(e)}")
                
                if copied_count > 0:
                    # Refresh listbox
                    listbox.delete(0, tk.END)
                    json_files = glob.glob(os.path.join(packages_dir, "*.json"))
                    for json_file in json_files:
                        listbox.insert(tk.END, os.path.basename(json_file))
                    messagebox.showinfo("Copy Complete", f"Copied {copied_count} file(s) to packages folder.")
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Load Selected", command=load_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Browse External...", command=browse_external).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Update blocks list after import
        if hasattr(self, 'update_blocks_list'):
            self.update_blocks_list()
    
    # ===== Package Creator Methods =====

    def open_package_creator(self):
        """Open package creator tool"""
        try:
            # Dynamically import package creator
            from plugins.package_creator import show_package_creator
            show_package_creator(self)
        except ImportError as e:
            messagebox.showerror("Plugin Error", 
                               f"Package Creator plugin not found: {e}\n"
                               f"Make sure plugins/package_creator.py exists.")
        except Exception as e:
            messagebox.showerror("Plugin Error", f"Could not open Package Creator: {e}")
    
    # ===== Help Methods =====
    
    def show_help(self):
        """Show improved help window with block information"""
        # Import here to avoid circular imports
        from ui.help_window import show_help_window
        show_help_window(self)
