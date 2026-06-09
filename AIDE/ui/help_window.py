import tkinter as tk
from tkinter import ttk
import json
import os
import glob

def show_help_window(app):
    """Show improved help window with block information"""
    help_window = tk.Toplevel(app.root)
    help_window.title("AntimonyIDE - Code Blocks Help")
    help_window.geometry("1100x750")
    help_window.configure(bg="#f5f5f5")
    
    # Create notebook for tabs
    notebook = ttk.Notebook(help_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Tab 1: Basic Usage
    basic_tab = tk.Frame(notebook, bg="#f5f5f5")
    notebook.add(basic_tab, text="Basic Usage")
    
    # Tab 2: Code Blocks Reference
    blocks_tab = tk.Frame(notebook, bg="#f5f5f5")
    notebook.add(blocks_tab, text="Code Blocks Reference")
    
    # Tab 3: Packages
    packages_tab = tk.Frame(notebook, bg="#f5f5f5")
    notebook.add(packages_tab, text="Packages")
    
    # ===== Basic Usage Tab =====
    basic_canvas = tk.Canvas(basic_tab, bg="#f5f5f5", highlightthickness=0)
    scrollbar = tk.Scrollbar(basic_tab, orient="vertical", command=basic_canvas.yview)
    basic_content = tk.Frame(basic_canvas, bg="#f5f5f5")
    
    basic_content.bind(
        "<Configure>",
        lambda e: basic_canvas.configure(scrollregion=basic_canvas.bbox("all"))
    )
    
    basic_canvas.create_window((0, 0), window=basic_content, anchor="nw", width=1060)
    basic_canvas.configure(yscrollcommand=scrollbar.set)
    
    basic_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Basic help content
    # 在Basic Usage Tab的help_text中添加
    help_text = """
        AntimonyIDE - Quick Start Guide

        1. ADDING BLOCKS:
           • Double-click a block in the left panel to add it to canvas
           • Drag blocks from the left panel to the canvas
           • Right-click on canvas to access context menu

        2. CONNECTING BLOCKS:
           • Sequence (Ctrl+A): Connect blocks to execute in order
           • End (Ctrl+X): For control structures (if/for/while/function)
           • Continue (Ctrl+W): Connect blocks to appear on same line
           • Each button toggles between Connect/Disconnect

        3. EDITING BLOCKS:
           • Click a block to select it
           • Edit content in the right panel
           • Change colors with "Choose" button
           • Delete with Ctrl+Q (without confirmation)

        4. SHORTCUT KEYS:
           • Ctrl+S: Save project
           • Ctrl+E: Export Python code
           • Ctrl+N: New project
           • Ctrl+O: Import project
           • Ctrl+L: Load Python file
           • Ctrl+H: Show this help
           • Ctrl+Q: Delete selected block (without confirmation)
           • Ctrl+A: Toggle sequence connection
           • Ctrl+X: Toggle end connection
           • Ctrl+W: Toggle continue connection
           • Ctrl+P: Open Package Creator

        5. IMPORTING PACKAGES:
           • Use "Import Package" button to add Python packages
           • Select functions to add as blocks
           • Custom blocks are saved automatically

        6. PACKAGE CREATOR:
           • Click the "📦 Package Creator" button (Ctrl+P) to create custom packages
           • Create new blocks with custom content, templates and descriptions
           • Save as JSON files to share with others

        7. PACKAGE BLOCKS:
           • Package JSON files in the "packages" folder are automatically loaded
           • Each package provides specialized code blocks
           • View package details in the "Packages" tab of this help window
        """
    
    # Create title
    title_label = tk.Label(basic_content, text="AntimonyIDE Help",
                           font=("Arial", 16, "bold"), bg="#f5f5f5")
    title_label.pack(pady=(10, 20))
    
    # Create text widget for help content
    text_widget = tk.Text(basic_content, wrap=tk.WORD, width=85, height=30,
                         font=("Arial", 10), bg="white", relief=tk.FLAT)
    text_widget.insert("1.0", help_text)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(padx=20, pady=(0, 20), fill=tk.BOTH, expand=True)
    
    # ===== Code Blocks Reference Tab =====
    # Create search frame
    search_frame = tk.Frame(blocks_tab, bg="#f5f5f5")
    search_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Label(search_frame, text="Search:", bg="#f5f5f5", 
            font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
    
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side=tk.LEFT, padx=(0, 10))
    
    # Category filter
    tk.Label(search_frame, text="Category:", bg="#f5f5f5", 
            font=("Arial", 10)).pack(side=tk.LEFT, padx=(20, 10))
    
    category_var = tk.StringVar(value="All")
    categories = ["All"] + sorted(list(app.block_loader.available_blocks.keys()))
    category_menu = ttk.Combobox(search_frame, textvariable=category_var, 
                                 values=categories, state="readonly", width=15)
    category_menu.pack(side=tk.LEFT, padx=(0, 10))
    
    # Create treeview frame with scrollbars
    tree_frame = tk.Frame(blocks_tab)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    # Create treeview
    columns = ("category", "type", "template", "description", "usage")
    tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings")
    
    # Define headings
    tree.heading("#0", text="Block Name")
    tree.heading("category", text="Category")
    tree.heading("type", text="Type")
    tree.heading("template", text="Template")
    tree.heading("description", text="Description")
    tree.heading("usage", text="Usage Notes")
    
    # Define column widths
    tree.column("#0", width=150, minwidth=150)
    tree.column("category", width=100, minwidth=100)
    tree.column("type", width=80, minwidth=80)
    tree.column("template", width=180, minwidth=180)
    tree.column("description", width=250, minwidth=250)
    tree.column("usage", width=200, minwidth=200)
    
    # Add scrollbars
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    # Grid layout
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    
    # Load blocks into treeview
    def load_blocks():
        """Load all blocks into the treeview"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Get selected category
        selected_category = category_var.get()
        
        # Get all blocks
        all_blocks = []
        for category, blocks in app.block_loader.available_blocks.items():
            if selected_category == "All" or category == selected_category:
                for block in blocks:
                    block["category"] = category
                    # Add usage notes if available (from template or content)
                    if "template" in block and block["template"] != block.get("content", ""):
                        block["usage"] = f"Template: {block['template']}"
                    else:
                        block["usage"] = "Double-click to use"
                    all_blocks.append(block)
        
        # Sort blocks by category and name
        all_blocks.sort(key=lambda x: (x["category"], x.get("text", "")))
        
        # Add to treeview
        for block in all_blocks:
            tree.insert("", "end", 
                      text=block.get("text", "Unknown"),
                      values=(
                          block.get("category", ""),
                          block.get("type", ""),
                          block.get("template", block.get("content", "")),
                          block.get("description", ""),
                          block.get("usage", "")
                      ))
    
    def search_blocks():
        """Search blocks based on search term"""
        search_term = search_var.get().lower()
        selected_category = category_var.get()
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Get all blocks
        all_blocks = []
        for category, blocks in app.block_loader.available_blocks.items():
            if selected_category == "All" or category == selected_category:
                for block in blocks:
                    block["category"] = category
                    all_blocks.append(block)
        
        # Filter blocks if search term exists
        if search_term:
            filtered_blocks = []
            for block in all_blocks:
                text = block.get("text", "").lower()
                description = block.get("description", "").lower()
                template = block.get("template", "").lower()
                content = block.get("content", "").lower()
                block_type = block.get("type", "").lower()
                category_name = block.get("category", "").lower()
                
                if (search_term in text or 
                    search_term in description or 
                    search_term in template or
                    search_term in content or
                    search_term in block_type or
                    search_term in category_name):
                    filtered_blocks.append(block)
            all_blocks = filtered_blocks
        
        # Sort blocks
        all_blocks.sort(key=lambda x: (x["category"], x.get("text", "")))
        
        # Add to treeview
        for block in all_blocks:
            # Add usage notes if available
            if "template" in block and block["template"] != block.get("content", ""):
                usage = f"Template: {block['template']}"
            else:
                usage = "Double-click to use"
                
            tree.insert("", "end", 
                      text=block.get("text", "Unknown"),
                      values=(
                          block.get("category", ""),
                          block.get("type", ""),
                          block.get("template", block.get("content", "")),
                          block.get("description", ""),
                          usage
                      ))
    
    # Load blocks initially
    load_blocks()
    
    # Bind search
    search_entry.bind("<KeyRelease>", lambda e: search_blocks())
    category_menu.bind("<<ComboboxSelected>>", lambda e: search_blocks())
    
    # Search button
    search_btn = tk.Button(search_frame, text="Search", command=search_blocks)
    search_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    # Clear search button
    clear_btn = tk.Button(search_frame, text="Clear", 
                         command=lambda: [search_var.set(""), 
                                         category_var.set("All"),
                                         load_blocks()])
    clear_btn.pack(side=tk.LEFT)
    
    # ===== Packages Tab =====
    packages_canvas = tk.Canvas(packages_tab, bg="#f5f5f5", highlightthickness=0)
    packages_scrollbar = tk.Scrollbar(packages_tab, orient="vertical", 
                                      command=packages_canvas.yview)
    packages_content = tk.Frame(packages_canvas, bg="#f5f5f5")
    
    packages_content.bind(
        "<Configure>",
        lambda e: packages_canvas.configure(scrollregion=packages_canvas.bbox("all"))
    )
    
    packages_canvas.create_window((0, 0), window=packages_content, anchor="nw", width=1060)
    packages_canvas.configure(yscrollcommand=packages_scrollbar.set)
    
    packages_canvas.pack(side="left", fill="both", expand=True)
    packages_scrollbar.pack(side="right", fill="y")
    
    # Packages title
    packages_title = tk.Label(packages_content, text="Package Information", 
                             font=("Arial", 16, "bold"), bg="#f5f5f5")
    packages_title.pack(pady=(10, 20))
    
    # Package info text
    info_text = """Package JSON files are stored in the "packages" folder. 
Each JSON file defines code blocks for a specific package or module.

Package JSON Structure:
{
  "PackageName": [
    {
      "type": "block_type",
      "text": "Block Name",
      "content": "Code content",
      "template": "Template with placeholders",
      "description": "Description of the block"
    },
    ...
  ]
}

The package name (e.g., "Json", "Math") becomes a category in the blocks list.
"""
    
    info_label = tk.Label(packages_content, text=info_text, 
                         font=("Arial", 10), bg="#f5f5f5", justify=tk.LEFT,
                         wraplength=1000)
    info_label.pack(padx=20, pady=(0, 20))
    
    # Load and display package information
    def load_package_info():
        """Load and display package information"""
        packages_dir = "packages"
        if not os.path.exists(packages_dir):
            tk.Label(packages_content, 
                    text="No packages directory found. Create a 'packages' folder and add JSON files.",
                    bg="#f5f5f5", fg="gray", font=("Arial", 10)).pack(pady=20)
            return
        
        # Find all JSON files in packages directory
        json_files = glob.glob(os.path.join(packages_dir, "*.json"))
        
        if not json_files:
            tk.Label(packages_content, 
                    text="No package JSON files found in packages directory.",
                    bg="#f5f5f5", fg="gray", font=("Arial", 10)).pack(pady=20)
            return
        
        # Sort files alphabetically
        json_files.sort()
        
        # Display information for each package
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    package_data = json.load(f)
                
                # Get package name from filename
                package_name = os.path.basename(json_file).replace('.json', '')
                
                # Create frame for this package
                package_frame = tk.Frame(packages_content, bg="white", relief=tk.RIDGE, bd=2)
                package_frame.pack(fill=tk.X, padx=20, pady=10, ipadx=10, ipady=10)
                
                # Package header with expand/collapse
                header_frame = tk.Frame(package_frame, bg="white")
                header_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # Package name and toggle button
                name_label = tk.Label(header_frame, text=f"📦 {package_name}", 
                                     font=("Arial", 12, "bold"), bg="white", cursor="hand2")
                name_label.pack(side=tk.LEFT)
                
                # File info
                file_info = tk.Label(header_frame, 
                                    text=f"File: {os.path.basename(json_file)} | Blocks: {sum(len(blocks) for blocks in package_data.values())}",
                                    font=("Arial", 9), bg="white", fg="gray")
                file_info.pack(side=tk.RIGHT)
                
                # Content frame (initially hidden)
                content_frame = tk.Frame(package_frame, bg="white")
                
                # Display blocks for each category in the package
                for category_name, blocks in package_data.items():
                    if not isinstance(blocks, list):
                        continue
                    
                    category_frame = tk.Frame(content_frame, bg="white")
                    category_frame.pack(fill=tk.X, padx=10, pady=5)
                    
                    # Category label
                    cat_label = tk.Label(category_frame, text=f"Category: {category_name}", 
                                        font=("Arial", 10, "bold"), bg="white")
                    cat_label.pack(anchor="w", pady=(5, 5))
                    
                    # Create a table-like display for blocks
                    for i, block in enumerate(blocks):
                        block_frame = tk.Frame(category_frame, bg="#f9f9f9" if i % 2 == 0 else "#f0f0f0")
                        block_frame.pack(fill=tk.X, padx=5, pady=2)
                        
                        # Block name and type
                        name_type_frame = tk.Frame(block_frame, bg="transparent")
                        name_type_frame.pack(fill=tk.X, padx=5, pady=3)
                        
                        block_name = tk.Label(name_type_frame, text=f"• {block.get('text', 'Unknown')}", 
                                             font=("Arial", 9, "bold"), bg="transparent")
                        block_name.pack(side=tk.LEFT)
                        
                        block_type = tk.Label(name_type_frame, text=f"[{block.get('type', 'unknown')}]", 
                                             font=("Arial", 8), bg="transparent", fg="blue")
                        block_type.pack(side=tk.LEFT, padx=(5, 10))
                        
                        # Template/Content
                        template_frame = tk.Frame(block_frame, bg="transparent")
                        template_frame.pack(fill=tk.X, padx=10, pady=2)
                        
                        template_label = tk.Label(template_frame, text="Template:", 
                                                 font=("Arial", 8, "bold"), bg="transparent")
                        template_label.pack(side=tk.LEFT, anchor="n")
                        
                        template_text = tk.Text(template_frame, height=2, width=60,
                                               font=("Courier", 8), bg="#f5f5f5",
                                               relief=tk.FLAT, wrap=tk.WORD)
                        template_text.insert("1.0", block.get('template', block.get('content', 'No template')))
                        template_text.config(state=tk.DISABLED)
                        template_text.pack(side=tk.LEFT, padx=(5, 0), pady=2)
                        
                        # Description
                        if block.get('description'):
                            desc_frame = tk.Frame(block_frame, bg="transparent")
                            desc_frame.pack(fill=tk.X, padx=10, pady=(0, 3))
                            
                            desc_label = tk.Label(desc_frame, text="Description:", 
                                                 font=("Arial", 8, "bold"), bg="transparent")
                            desc_label.pack(side=tk.LEFT, anchor="n")
                            
                            desc_text = tk.Label(desc_frame, text=block['description'],
                                                font=("Arial", 8), bg="transparent",
                                                wraplength=800, justify=tk.LEFT)
                            desc_text.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
                
                # Toggle visibility function
                def toggle_content(content=content_frame, header=header_frame):
                    if content.winfo_ismapped():
                        content.pack_forget()
                        header.config(bg="white")
                    else:
                        content.pack(fill=tk.X, padx=10, pady=(0, 10))
                        header.config(bg="#f0f0f0")
                
                # Bind click to toggle
                name_label.bind("<Button-1>", lambda e, t=toggle_content: t())
                header_frame.bind("<Button-1>", lambda e, t=toggle_content: t())
                
                # Initially hide content
                content_frame.pack_forget()
                
                # Separator
                separator = tk.Frame(packages_content, height=2, bg="#e0e0e0")
                separator.pack(fill=tk.X, padx=20, pady=5)
                
            except json.JSONDecodeError as e:
                error_frame = tk.Frame(packages_content, bg="#ffeeee", relief=tk.RIDGE, bd=1)
                error_frame.pack(fill=tk.X, padx=20, pady=10)
                
                error_label = tk.Label(error_frame, 
                                      text=f"Error loading {os.path.basename(json_file)}: Invalid JSON format",
                                      font=("Arial", 10), bg="#ffeeee", fg="red")
                error_label.pack(padx=10, pady=10)
                
                error_details = tk.Label(error_frame, 
                                        text=f"Error: {str(e)}",
                                        font=("Arial", 8), bg="#ffeeee", fg="darkred")
                error_details.pack(padx=10, pady=(0, 10))
                
            except Exception as e:
                error_frame = tk.Frame(packages_content, bg="#ffeeee", relief=tk.RIDGE, bd=1)
                error_frame.pack(fill=tk.X, padx=20, pady=10)
                
                error_label = tk.Label(error_frame, 
                                      text=f"Error loading {os.path.basename(json_file)}: {str(e)}",
                                      font=("Arial", 10), bg="#ffeeee", fg="red")
                error_label.pack(padx=10, pady=10)
    
    # Load package information
    load_package_info()
    
    # Instructions for adding packages
    instructions = tk.Label(packages_content, 
                          text="To add a new package:\n1. Create a JSON file in the 'packages' folder\n2. Use the structure shown above\n3. Restart AntimonyIDE or use 'Import Package' button",
                          font=("Arial", 9), bg="#f5f5f5", fg="green", justify=tk.LEFT)
    instructions.pack(pady=20)
    
    # Close button at bottom
    close_frame = tk.Frame(help_window, bg="#f5f5f5")
    close_frame.pack(fill=tk.X, pady=(0, 10))
    
    close_btn = tk.Button(close_frame, text="Close", width=20,
                         command=help_window.destroy, bg="#4CAF50", fg="white",
                         font=("Arial", 10, "bold"))
    close_btn.pack()
    
    # Make window modal
    help_window.transient(app.root)
    help_window.grab_set()
    help_window.focus_set()
