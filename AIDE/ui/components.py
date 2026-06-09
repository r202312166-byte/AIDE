import tkinter as tk
from tkinter import ttk


def create_left_section(app):
    """Create the left section with blocks list - increased height"""
    left_frame = tk.LabelFrame(app.root, text="Code Blocks", padx=10, pady=10)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # 保存引用
    app.left_frame = left_frame

    # Category selection
    category_frame = tk.Frame(left_frame)
    category_frame.pack(fill="x", pady=(0, 5))

    tk.Label(category_frame, text=app.lang.get("category")).pack(side="left", padx=(0, 5))

    app.category_var = tk.StringVar(value=app.lang.get("blocks_all"))

    # Get categories from available blocks
    categories = [app.lang.get("blocks_all")]
    for category in app.block_loader.available_blocks.keys():
        categories.append(category)

    app.category_dropdown = ttk.Combobox(category_frame, textvariable=app.category_var,
                                         values=categories, state="readonly", width=15)
    app.category_dropdown.pack(side="left")
    app.category_dropdown.bind("<<ComboboxSelected>>", lambda e: app.update_blocks_list())

    # Import package button
    tk.Button(category_frame, text=app.lang.get("import_package"),
              command=app.import_package, width=12).pack(side="right", padx=(5, 0))

    # Blocks list with scrollbar - increased height
    list_frame = tk.Frame(left_frame)
    list_frame.pack(fill="both", expand=True)

    # Create treeview for blocks - remove fixed height, use fill/expand
    app.blocks_tree = ttk.Treeview(list_frame)
    app.blocks_tree.pack(side="left", fill="both", expand=True)

    # Configure treeview
    app.blocks_tree["columns"] = ("type",)
    app.blocks_tree.column("#0", width=150, minwidth=150)
    app.blocks_tree.column("type", width=80, minwidth=80)

    app.blocks_tree.heading("#0", text="Block")
    app.blocks_tree.heading("type", text="Type")

    # Add scrollbar
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=app.blocks_tree.yview)
    scrollbar.pack(side="right", fill="y")
    app.blocks_tree.configure(yscrollcommand=scrollbar.set)

    # Bind selection event
    app.blocks_tree.bind("<<TreeviewSelect>>", app.select_block_from_list)
    app.blocks_tree.bind("<Double-1>", app.add_block_from_list)

    # Bind drag events for treeview
    app.blocks_tree.bind("<ButtonPress-1>", app.start_drag_from_list)
    app.blocks_tree.bind("<B1-Motion>", app.drag_from_list)
    app.blocks_tree.bind("<ButtonRelease-1>", app.end_drag_from_list)

    # Update blocks list
    app.update_blocks_list()

    # Instructions - at bottom
    tk.Label(left_frame, text=app.lang.get("drag_to_canvas"),
             fg="gray", justify="center").pack(side="bottom", pady=(5, 0))

    # Make left frame expand
    left_frame.rowconfigure(0, weight=1)


def create_middle_section(app):
    """Create the middle section with design canvas - 改进：自适应扩展"""
    app.middle_frame = tk.LabelFrame(app.root, text=app.lang.get("workspace"), padx=10, pady=10)
    app.middle_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    # 配置中间框架网格
    app.middle_frame.grid_rowconfigure(0, weight=1)
    app.middle_frame.grid_columnconfigure(0, weight=1)

    # 创建画布容器
    canvas_container = tk.Frame(app.middle_frame)
    canvas_container.grid(row=0, column=0, sticky="nsew")
    canvas_container.grid_rowconfigure(0, weight=1)
    canvas_container.grid_columnconfigure(0, weight=1)

    # 创建画布
    app.canvas = tk.Canvas(canvas_container, bg="white", scrollregion=(0, 0, 4000, 5000))

    # 创建滚动条
    v_scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=app.canvas.yview)
    h_scrollbar = tk.Scrollbar(canvas_container, orient="horizontal", command=app.canvas.xview)
    app.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # 使用grid布局
    app.canvas.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    # 保存canvas_container引用
    app.canvas_container = canvas_container

    # 绘制网格
    app.draw_grid()

    # 初始化变量
    app.drag_start_x = 0
    app.drag_start_y = 0
    app.scrolling = False
    app.polyline_selected = False

    # 绑定事件
    app.canvas.bind("<Button-1>", app.canvas_click)
    app.canvas.bind("<B1-Motion>", app.canvas_drag)
    app.canvas.bind("<ButtonRelease-1>", app.canvas_release)
    app.canvas.bind("<Button-3>", app.canvas_right_click)
    app.canvas.bind("<ButtonPress-2>", app.scroll_start)
    app.canvas.bind("<B2-Motion>", app.scroll_move)
    app.canvas.bind("<ButtonPress-3>", app.scroll_start)
    app.canvas.bind("<B3-Motion>", app.scroll_move)

    # 只在大小变化明显时才重绘网格，避免频繁重绘
    app.last_canvas_size = (0, 0)

    def on_canvas_configure(event):
        current_size = (event.width, event.height)
        # 只有当画布大小变化超过50像素时才重绘网格
        if (abs(current_size[0] - app.last_canvas_size[0]) > 50 or
                abs(current_size[1] - app.last_canvas_size[1]) > 50):
            app.last_canvas_size = current_size
            app.draw_grid()

    app.canvas.bind("<Configure>", on_canvas_configure)

    # 选择模式按钮
    select_mode_frame = tk.Frame(app.middle_frame)
    select_mode_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

    app.select_mode_var = tk.BooleanVar(value=False)
    select_mode_btn = tk.Checkbutton(select_mode_frame, text="Select Mode",
                                     variable=app.select_mode_var,
                                     command=app.toggle_select_mode)
    select_mode_btn.pack(side=tk.LEFT)

    # 配置网格权重
    canvas_container.grid_columnconfigure(0, weight=1)
    canvas_container.grid_rowconfigure(0, weight=1)


def create_right_section(app):
    """Create the right section with block editor - 改进：更窄的编辑器"""
    app.right_frame = tk.LabelFrame(app.root, text="Block Editor", padx=10, pady=10)
    app.right_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

    # 设置右侧框架的宽度
    app.right_frame.config(width=350)

    # 配置右侧框架权重
    app.right_frame.grid_propagate(False)  # 防止子组件改变框架大小
    app.right_frame.grid_rowconfigure(0, weight=1)
    app.right_frame.grid_columnconfigure(0, weight=1)

    # 创建主要容器框架
    main_container = tk.Frame(app.right_frame)
    main_container.grid(row=0, column=0, sticky="nsew")
    main_container.grid_rowconfigure(0, weight=1)
    main_container.grid_columnconfigure(0, weight=1)

    # 添加滚动框架
    canvas = tk.Canvas(main_container, highlightthickness=0, width=330)
    scrollbar = tk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    # 配置滚动
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=330)
    canvas.configure(yscrollcommand=scrollbar.set)

    # 网格布局
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # 配置网格权重
    main_container.grid_rowconfigure(0, weight=1)
    main_container.grid_columnconfigure(0, weight=1)
    main_container.grid_columnconfigure(1, weight=0)

    # 存储可滚动的编辑器框架
    app.editor_frame = scrollable_frame

    # 初始显示
    tk.Label(app.editor_frame, text=app.lang.get("select_block"),
             fg="gray", font=("Arial", 12), pady=20).pack(expand=True)

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