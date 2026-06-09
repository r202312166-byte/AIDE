"""
Package Creator Plugin for OurNotepad
Allows users to create and edit code block packages
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import copy


class PackageCreator:
    def __init__(self, app):
        """Initialize Package Creator"""
        self.app = app
        self.package_file = None
        self.package_data = {}
        self.current_category = ""
        self.selected_block_index = -1
        
        # 创建主窗口
        self.create_window()

    def create_window(self):
        """Create package creator window"""
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Package Creator - OurNotepad")
        self.window.geometry("1200x600")  # 增加宽度
        self.window.minsize(1000, 600)

        # 设置图标（如果可用）
        try:
            self.window.iconbitmap("icon.ico")
        except:
            pass

        # 创建UI
        self.create_ui()

        # 使窗口模态
        self.window.transient(self.app.root)
        self.window.grab_set()
        self.window.focus_set()

        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def create_ui(self):
        """Create user interface"""
        # 主容器
        main_container = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== 左侧面板：块列表 =====
        left_frame = tk.Frame(main_container, relief=tk.RIDGE, bd=2)
        main_container.add(left_frame, width=300)

        # ===== 中间面板：类别管理 =====
        middle_frame = tk.Frame(main_container, relief=tk.RIDGE, bd=2)
        main_container.add(middle_frame, width=300)

        # ===== 右侧面板：块编辑器 =====
        right_frame = tk.Frame(main_container, relief=tk.RIDGE, bd=2)
        main_container.add(right_frame, width=600)

        # ===== 左侧面板：块列表 =====
        tk.Label(left_frame, text="Blocks in Category",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # 块列表和滚动条
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.block_listbox = tk.Listbox(list_frame, height=25)
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)

        self.block_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.block_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.block_listbox.yview)

        self.block_listbox.bind("<<ListboxSelect>>", self.select_block)

        # 块操作按钮
        block_btn_frame = tk.Frame(left_frame)
        block_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(block_btn_frame, text="Add Block",
                  command=self.add_block, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(block_btn_frame, text="Delete Block",
                  command=self.delete_block, width=12).pack(side=tk.LEFT, padx=2)

        move_frame = tk.Frame(left_frame)
        move_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(move_frame, text="Move Up",
                  command=self.move_block_up, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(move_frame, text="Move Down",
                  command=self.move_block_down, width=12).pack(side=tk.LEFT, padx=2)

        # ===== 中间面板：包和类别管理 =====
        tk.Label(middle_frame, text="Package Manager",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # 文件操作按钮
        file_frame = tk.Frame(middle_frame)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(file_frame, text="New Package",
                  command=self.new_package, width=15).pack(side=tk.TOP, pady=2)
        tk.Button(file_frame, text="Load Package",
                  command=self.load_package, width=15).pack(side=tk.TOP, pady=2)
        tk.Button(file_frame, text="Save Package",
                  command=self.save_package, width=15).pack(side=tk.TOP, pady=2)
        tk.Button(file_frame, text="Save As...",
                  command=self.save_package_as, width=15).pack(side=tk.TOP, pady=2)

        # 当前文件信息
        self.file_label = tk.Label(middle_frame, text="No package loaded",
                                   fg="gray", font=("Arial", 9))
        self.file_label.pack(pady=5)

        # 类别管理
        category_frame = tk.LabelFrame(middle_frame, text="Categories", padx=10, pady=10)
        category_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 类别列表
        self.category_listbox = tk.Listbox(category_frame, height=12)
        self.category_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.category_listbox.bind("<<ListboxSelect>>", self.select_category)

        # 类别操作按钮
        cat_btn_frame = tk.Frame(category_frame)
        cat_btn_frame.pack(fill=tk.X)

        tk.Button(cat_btn_frame, text="Add Category",
                  command=self.add_category, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(cat_btn_frame, text="Rename",
                  command=self.rename_category, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(cat_btn_frame, text="Delete",
                  command=self.delete_category, width=12).pack(side=tk.LEFT, padx=2)

        # ===== 右侧面板：块编辑器 =====
        tk.Label(right_frame, text="Block Editor",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # 创建可滚动的编辑器区域
        editor_canvas = tk.Canvas(right_frame, bg="white", highlightthickness=0)
        editor_scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL,
                                        command=editor_canvas.yview)
        self.editor_frame = tk.Frame(editor_canvas, bg="white")

        self.editor_frame.bind(
            "<Configure>",
            lambda e: editor_canvas.configure(scrollregion=editor_canvas.bbox("all"))
        )

        editor_canvas.create_window((0, 0), window=self.editor_frame, anchor="nw", width=580)
        editor_canvas.configure(yscrollcommand=editor_scrollbar.set)

        editor_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        editor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # 初始显示空编辑器
        self.show_empty_editor()
        
    def show_empty_editor(self):
        """Show empty editor state"""
        for widget in self.editor_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.editor_frame, text="Select a block to edit", 
                fg="gray", font=("Arial", 11), bg="white").pack(expand=True)
        
    def create_editor_fields(self):
        """Create block editor fields"""
        for widget in self.editor_frame.winfo_children():
            widget.destroy()
        
        row = 0
        
        # 类型选择
        tk.Label(self.editor_frame, text="Type:", 
                font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, 
                                                            sticky="w", pady=5, padx=10)
        
        block_types = [
            "statement", "function", "control", "loop", "io", 
            "variable", "operator", "import", "gui", "class", 
            "method", "defining", "unclosed_tag", "text"
        ]
        
        self.type_var = tk.StringVar(value="statement")
        type_dropdown = ttk.Combobox(self.editor_frame, textvariable=self.type_var,
                                    values=block_types, state="readonly", width=20)
        type_dropdown.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        
        # 块文本
        tk.Label(self.editor_frame, text="Display Text:", 
                font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, 
                                                            sticky="w", pady=5, padx=10)
        
        self.text_var = tk.StringVar()
        text_entry = tk.Entry(self.editor_frame, textvariable=self.text_var, width=40)
        text_entry.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        
        # 内容
        tk.Label(self.editor_frame, text="Content:", 
                font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, 
                                                           sticky="w", pady=5, padx=10)
        
        self.content_text = tk.Text(self.editor_frame, height=6, width=50)
        self.content_text.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        
        # 模板
        tk.Label(self.editor_frame, text="Template (optional):", 
                font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, 
                                                           sticky="w", pady=5, padx=10)
        
        self.template_text = tk.Text(self.editor_frame, height=4, width=50)
        self.template_text.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        
        # 描述
        tk.Label(self.editor_frame, text="Description:", 
                font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, 
                                                           sticky="w", pady=5, padx=10)
        
        self.description_text = tk.Text(self.editor_frame, height=4, width=50)
        self.description_text.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        
        # 占位符提示
        tk.Label(self.editor_frame, text="Placeholders:", 
                font=("Arial", 10, "bold"), bg="white").grid(row=row, column=0, 
                                                           sticky="w", pady=5, padx=10)
        
        placeholders_frame = tk.Frame(self.editor_frame, bg="white")
        placeholders_frame.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        
        placeholders_text = """Use {placeholders} in content and template:
  • {variable} - User-defined variable
  • {value} - Any value
  • {condition} - Boolean condition
  • {name} - Function/class name
  • {params} - Function parameters
  • {args} - Function arguments
  • {iterable} - List or range
  • {item} - Loop item"""
        
        tk.Label(placeholders_frame, text=placeholders_text, 
                bg="white", justify=tk.LEFT, font=("Courier", 9)).pack(anchor="w")
        row += 1
        
        # 保存按钮
        save_frame = tk.Frame(self.editor_frame, bg="white")
        save_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        tk.Button(save_frame, text="Save Block", 
                 command=self.save_current_block, width=20,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(save_frame, text="Duplicate Block", 
                 command=self.duplicate_block, width=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(save_frame, text="Test in IDE", 
                 command=self.test_block, width=20,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        
        # 绑定Ctrl+S保存
        self.editor_frame.bind_all("<Control-s>", lambda e: self.save_current_block())
        
    # ===== 包文件操作 =====
    
    def new_package(self):
        """Create a new package"""
        # 询问包名称
        package_name = simpledialog.askstring("New Package", 
                                            "Enter package name (e.g., 'Math', 'Json'):")
        if not package_name:
            return
        
        # 清空当前数据
        self.package_file = None
        self.package_data = {}
        self.current_category = package_name
        
        # 初始化数据结构
        self.package_data[self.current_category] = []
        
        # 更新UI
        self.update_category_list()
        self.update_block_list()
        self.file_label.config(text=f"New package: {package_name}")
        self.show_empty_editor()
        
    def load_package(self):
        """Load a package from JSON file"""
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Select Package File"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.package_data = json.load(f)
            
            self.package_file = filename
            self.current_category = list(self.package_data.keys())[0] if self.package_data else ""
            
            # 更新UI
            self.update_category_list()
            self.update_block_list()
            self.file_label.config(text=f"Loaded: {os.path.basename(filename)}")
            self.show_empty_editor()
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Load Error", f"Invalid JSON format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load package: {str(e)}")
    
    def save_package(self):
        """Save current package"""
        if not self.package_data:
            messagebox.showwarning("No Package", "No package data to save.")
            return
        
        if not self.package_file:
            self.save_package_as()
            return
        
        try:
            with open(self.package_file, 'w', encoding='utf-8') as f:
                json.dump(self.package_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Save Successful", 
                              f"Package saved to {self.package_file}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save package: {str(e)}")
    
    def save_package_as(self):
        """Save current package with new filename"""
        if not self.package_data:
            messagebox.showwarning("No Package", "No package data to save.")
            return
        
        # 建议保存在packages目录
        packages_dir = "packages"
        if not os.path.exists(packages_dir):
            os.makedirs(packages_dir)
        
        # 获取默认文件名
        default_name = self.current_category if self.current_category else "NewPackage"
        default_path = os.path.join(packages_dir, f"{default_name}.json")
        
        filename = filedialog.asksaveasfilename(
            initialdir=packages_dir,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile=os.path.basename(default_path)
        )
        
        if filename:
            self.package_file = filename
            self.save_package()
    
    # ===== 类别管理 =====
    
    def update_category_list(self):
        """Update category listbox"""
        self.category_listbox.delete(0, tk.END)
        for category in self.package_data.keys():
            self.category_listbox.insert(tk.END, category)
        
        # 如果有类别，选中第一个
        if self.package_data:
            self.category_listbox.selection_set(0)
            self.current_category = self.category_listbox.get(0)
    
    def select_category(self, event):
        """Handle category selection"""
        selection = self.category_listbox.curselection()
        if selection:
            self.current_category = self.category_listbox.get(selection[0])
            self.update_block_list()
            self.show_empty_editor()
    
    def add_category(self):
        """Add a new category"""
        category_name = simpledialog.askstring("Add Category", "Enter category name:")
        if category_name and category_name.strip():
            category_name = category_name.strip()
            if category_name not in self.package_data:
                self.package_data[category_name] = []
                self.update_category_list()
                
                # 选中新类别
                index = list(self.package_data.keys()).index(category_name)
                self.category_listbox.selection_clear(0, tk.END)
                self.category_listbox.selection_set(index)
                self.category_listbox.see(index)
                
                self.current_category = category_name
                self.update_block_list()
            else:
                messagebox.showwarning("Category Exists", 
                                      f"Category '{category_name}' already exists.")
    
    def rename_category(self):
        """Rename selected category"""
        selection = self.category_listbox.curselection()
        if not selection:
            return
        
        old_name = self.category_listbox.get(selection[0])
        new_name = simpledialog.askstring("Rename Category", 
                                         f"Enter new name for '{old_name}':",
                                         initialvalue=old_name)
        
        if new_name and new_name.strip() and new_name != old_name:
            new_name = new_name.strip()
            
            # 检查名称是否已存在
            if new_name in self.package_data:
                messagebox.showwarning("Name Exists", 
                                      f"Category '{new_name}' already exists.")
                return
            
            # 重命名
            self.package_data[new_name] = self.package_data.pop(old_name)
            
            # 如果这是当前类别，更新
            if self.current_category == old_name:
                self.current_category = new_name
            
            self.update_category_list()
    
    def delete_category(self):
        """Delete selected category"""
        selection = self.category_listbox.curselection()
        if not selection:
            return
        
        category_name = self.category_listbox.get(selection[0])
        
        response = messagebox.askyesno("Delete Category", 
                                      f"Are you sure you want to delete category '{category_name}'?\n"
                                      f"This will delete {len(self.package_data[category_name])} blocks.")
        
        if response:
            # 删除类别
            del self.package_data[category_name]
            
            # 如果删除的是当前类别，选择另一个类别
            if self.current_category == category_name:
                if self.package_data:
                    self.current_category = list(self.package_data.keys())[0]
                else:
                    self.current_category = ""
            
            self.update_category_list()
            self.update_block_list()
            self.show_empty_editor()
    
    # ===== 块管理 =====

    def update_block_list(self):
        """Update block listbox"""
        self.block_listbox.delete(0, tk.END)
        self.selected_block_index = -1

        if self.current_category and self.current_category in self.package_data:
            for i, block in enumerate(self.package_data[self.current_category]):
                block_text = block.get("text", "Unnamed Block")
                block_type = block.get("type", "unknown")
                self.block_listbox.insert(tk.END, f"{i + 1}. {block_text} [{block_type}]")
    
    def select_block(self, event):
        """Handle block selection"""
        selection = self.block_listbox.curselection()
        if selection:
            self.selected_block_index = selection[0]
            self.load_block_editor(self.selected_block_index)
    
    def load_block_editor(self, index):
        """Load block data into editor"""
        if not self.current_category or index < 0:
            return
        
        blocks = self.package_data.get(self.current_category, [])
        if index >= len(blocks):
            return
        
        block = blocks[index]
        
        # 创建编辑器字段（如果尚未创建）
        if not hasattr(self, 'type_var'):
            self.create_editor_fields()
        
        # 加载数据
        self.type_var.set(block.get("type", "statement"))
        self.text_var.set(block.get("text", ""))
        
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", block.get("content", ""))
        
        self.template_text.delete("1.0", tk.END)
        self.template_text.insert("1.0", block.get("template", ""))
        
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", block.get("description", ""))
    
    def save_current_block(self):
        """Save current block data"""
        if not hasattr(self, 'type_var') or self.selected_block_index < 0:
            messagebox.showwarning("No Block Selected", "Please select a block to edit.")
            return
        
        # 验证数据
        block_text = self.text_var.get().strip()
        if not block_text:
            messagebox.showwarning("Missing Text", "Block text is required.")
            return
        
        block_content = self.content_text.get("1.0", tk.END).strip()
        if not block_content:
            messagebox.showwarning("Missing Content", "Block content is required.")
            return
        
        # 创建块数据
        block_data = {
            "type": self.type_var.get(),
            "text": block_text,
            "content": block_content,
            "template": self.template_text.get("1.0", tk.END).strip(),
            "description": self.description_text.get("1.0", tk.END).strip()
        }
        
        # 如果模板为空，使用内容作为模板
        if not block_data["template"]:
            block_data["template"] = block_content
        
        # 保存到数据
        blocks = self.package_data[self.current_category]
        if self.selected_block_index < len(blocks):
            blocks[self.selected_block_index] = block_data
        else:
            blocks.append(block_data)
        
        # 更新列表
        self.update_block_list()
        
        # 重新选择当前块
        self.block_listbox.selection_set(self.selected_block_index)
        self.block_listbox.see(self.selected_block_index)
        
        messagebox.showinfo("Block Saved", "Block data saved successfully.")
    
    def add_block(self):
        """Add a new block"""
        if not self.current_category:
            messagebox.showwarning("No Category", "Please select or create a category first.")
            return
        
        # 创建编辑器字段（如果尚未创建）
        if not hasattr(self, 'type_var'):
            self.create_editor_fields()
        
        # 清空编辑器
        self.type_var.set("statement")
        self.text_var.set("")
        self.content_text.delete("1.0", tk.END)
        self.template_text.delete("1.0", tk.END)
        self.description_text.delete("1.0", tk.END)
        
        # 设置选中索引为新块
        blocks = self.package_data[self.current_category]
        self.selected_block_index = len(blocks)
        
        # 添加到列表
        self.block_listbox.insert(tk.END, "New Block [statement]")
        self.block_listbox.selection_set(self.selected_block_index)
        self.block_listbox.see(self.selected_block_index)
        
        # 显示默认值
        self.content_text.insert("1.0", "# Enter block content here")
        self.template_text.insert("1.0", "# Enter template here (optional)")
        self.description_text.insert("1.0", "Description of the block")
    
    def delete_block(self):
        """Delete selected block"""
        if self.selected_block_index < 0:
            messagebox.showwarning("No Block Selected", "Please select a block to delete.")
            return
        
        response = messagebox.askyesno("Delete Block", 
                                      "Are you sure you want to delete this block?")
        
        if response:
            blocks = self.package_data[self.current_category]
            if self.selected_block_index < len(blocks):
                del blocks[self.selected_block_index]
                self.update_block_list()
                self.show_empty_editor()
    
    def move_block_up(self):
        """Move selected block up"""
        if self.selected_block_index <= 0:
            return
        
        blocks = self.package_data[self.current_category]
        if self.selected_block_index < len(blocks):
            # 交换位置
            blocks[self.selected_block_index], blocks[self.selected_block_index - 1] = \
                blocks[self.selected_block_index - 1], blocks[self.selected_block_index]
            
            self.selected_block_index -= 1
            self.update_block_list()
            
            # 重新选择
            self.block_listbox.selection_set(self.selected_block_index)
            self.block_listbox.see(self.selected_block_index)
    
    def move_block_down(self):
        """Move selected block down"""
        blocks = self.package_data[self.current_category]
        if self.selected_block_index < len(blocks) - 1:
            # 交换位置
            blocks[self.selected_block_index], blocks[self.selected_block_index + 1] = \
                blocks[self.selected_block_index + 1], blocks[self.selected_block_index]
            
            self.selected_block_index += 1
            self.update_block_list()
            
            # 重新选择
            self.block_listbox.selection_set(self.selected_block_index)
            self.block_listbox.see(self.selected_block_index)
    
    def duplicate_block(self):
        """Duplicate current block"""
        if self.selected_block_index < 0:
            messagebox.showwarning("No Block Selected", "Please select a block to duplicate.")
            return
        
        blocks = self.package_data[self.current_category]
        if self.selected_block_index < len(blocks):
            # 复制块
            original_block = blocks[self.selected_block_index]
            new_block = copy.deepcopy(original_block)
            
            # 修改文本（添加"Copy"后缀）
            if "text" in new_block:
                new_block["text"] = f"{new_block['text']} (Copy)"
            
            # 插入到原块之后
            blocks.insert(self.selected_block_index + 1, new_block)
            
            self.selected_block_index += 1
            self.update_block_list()
            
            # 重新选择
            self.block_listbox.selection_set(self.selected_block_index)
            self.block_listbox.see(self.selected_block_index)
            self.load_block_editor(self.selected_block_index)
    
    def test_block(self):
        """Test current block in IDE"""
        if not hasattr(self, 'type_var') or self.selected_block_index < 0:
            messagebox.showwarning("No Block", "Please create or select a block first.")
            return
        
        # 获取块数据
        block_data = {
            "type": self.type_var.get(),
            "text": self.text_var.get().strip() or "Test Block",
            "content": self.content_text.get("1.0", tk.END).strip() or "# Test content",
            "template": self.template_text.get("1.0", tk.END).strip(),
            "description": self.description_text.get("1.0", tk.END).strip()
        }
        
        # 创建临时块进行测试
        if hasattr(self.app, 'blocks') and hasattr(self.app, 'block_counter'):
            # 计算位置（在画布中央）
            canvas_width = self.app.canvas.winfo_width()
            canvas_height = self.app.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                x = self.app.canvas.canvasx(canvas_width // 2)
                y = self.app.canvas.canvasy(canvas_height // 2)
            else:
                x, y = 200, 200
            
            # 创建块ID
            block_id = f"test_block_{self.app.block_counter}"
            
            # 创建测试块
            test_block = self.app.blocks[block_id] = type('CodeBlock', (), {})()
            test_block.id = block_id
            test_block.type = block_data["type"]
            test_block.x = x
            test_block.y = y
            test_block.width = 120
            test_block.height = 60
            test_block.text = block_data["text"]
            test_block.content = block_data["content"]
            test_block.color = "#4CAF50"  # 绿色，表示测试块
            
            # 增加块计数器
            self.app.block_counter += 1
            
            # 绘制块
            self.app.draw_block(test_block)
            
            # 选中新块
            self.app.select_block(block_id)
            
            messagebox.showinfo("Block Added", 
                              f"Test block '{block_data['text']}' added to workspace.\n"
                              f"You can now test it in the IDE.")
        else:
            messagebox.showinfo("Block Data", 
                              f"Type: {block_data['type']}\n"
                              f"Text: {block_data['text']}\n"
                              f"Content: {block_data['content']}")
    
    def close_window(self):
        """Close package creator window"""
        # 检查是否有未保存的更改
        if self.package_data and self.package_file:
            response = messagebox.askyesnocancel("Save Changes", 
                                               "Save changes to current package before closing?")
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_package()
        
        # 释放窗口
        self.window.grab_release()
        self.window.destroy()


def show_package_creator(app):
    """Show package creator window"""
    # 检查是否已有打开的窗口
    for child in app.root.winfo_children():
        if isinstance(child, tk.Toplevel) and child.title().startswith("Package Creator"):
            child.lift()
            return

    # 创建新窗口
    PackageCreator(app)