import json
import os
import glob


class BlockLoader:
    def __init__(self):
        self.available_blocks = self.load_default_blocks()
        self.custom_blocks_file = "custom_blocks.json"
        self.custom_package_paths = []  # 存储包路径
        self.load_custom_blocks()

    def load_language_packages(self, language_mode):
        """根据语言模式加载相应的包 - 修复版本"""
        # 先清空现有块
        self.available_blocks = {}

        # 加载默认块
        default_blocks = self.load_default_blocks()
        self.available_blocks.update(default_blocks)

        # 获取包目录
        packages_dir = "packages"
        if not os.path.exists(packages_dir):
            print(f"Packages directory not found: {packages_dir}")
            return self.available_blocks

        # 定义语言与包文件的映射
        language_files = {
            "python": ["Python.json", "Common.json"],
            "html": ["HTML.json", "Common.json"],
            "c_cpp": ["C_Cpp.json", "Common.json"],
            "java": ["Java.json", "Common.json"],
            "text": ["Common.json"]  # text模式也加载通用包
        }

        # 获取当前语言的文件列表
        files_to_load = language_files.get(language_mode, [])

        for file_name in files_to_load:
            file_path = os.path.join(packages_dir, file_name)
            if os.path.exists(file_path):
                try:
                    # 加载包文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)

                    # 处理包数据
                    if isinstance(package_data, dict):
                        for category, blocks in package_data.items():
                            if category not in self.available_blocks:
                                self.available_blocks[category] = []

                            # 添加块到类别
                            for block in blocks:
                                # 检查是否已存在
                                exists = False
                                for existing_block in self.available_blocks[category]:
                                    if (existing_block.get("text") == block.get("text") and
                                            existing_block.get("type") == block.get("type")):
                                        exists = True
                                        break

                                if not exists:
                                    self.available_blocks[category].append(block)

                    print(f"  ✓ Loaded: {file_name}")
                except Exception as e:
                    print(f"  ✗ Error loading {file_name}: {e}")
            else:
                print(f"  ⚠ File not found: {file_name}")

        # 确保Special类别存在
        if "Special" not in self.available_blocks:
            self.available_blocks["Special"] = []

        # 确保Special类别中有Code Pack块
        code_pack_exists = False
        for block in self.available_blocks["Special"]:
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
            self.available_blocks["Special"].append(code_pack_block)

        return self.available_blocks

    def load_default_blocks(self):
        """Load default code blocks with corrected types"""
        blocks = {
            "Special": [
                {"type": "code_pack", "text": "Code Pack", 
                 "content": "# 代码包内容\n# 双击此块，然后点击'更改内容'按钮选择.txt文件",
                 "template": "",
                 "description": "通过选择.txt文件来设置代码内容",
                 "is_code_pack": True,
                 "pack_version": "1.0"}
            ],
            "Operators": [
                {"type": "operator", "text": "Add (+)", "content": "{a} + {b}", "template": "{a} + {b}",
                 "description": "Add two values."},
                {"type": "operator", "text": "Subtract (-)", "content": "{a} - {b}", "template": "{a} - {b}",
                 "description": "Subtract b from a."},
                {"type": "operator", "text": "Multiply (*)", "content": "{a} * {b}", "template": "{a} * {b}",
                 "description": "Multiply two values."},
                {"type": "operator", "text": "Divide (/)", "content": "{a} / {b}", "template": "{a} / {b}",
                 "description": "Divide a by b."},
                {"type": "operator", "text": "Equal (==)", "content": "{a} == {b}", "template": "{a} == {b}",
                 "description": "Check if two values are equal."},
            ],
        }
        return blocks

    def load_package_file(self, file_path, category_name=None):
        """Load a single package JSON file"""
        try:
            with open(file_path, 'r') as f:
                package_data = json.load(f)

            # If category_name not provided, use filename
            if not category_name:
                category_name = os.path.basename(file_path).replace('.json', '')

            # Process the package data
            added_count = 0

            # Package JSON can have different structures:
            # Option 1: Direct list of blocks
            # Option 2: Dictionary with category as key
            if isinstance(package_data, dict):
                # If it's a dict, each key is a category
                for category, blocks in package_data.items():
                    if isinstance(blocks, list):
                        # Use the provided category name or the dict key
                        use_category = category_name if category == list(package_data.keys())[0] else category

                        # Add to available blocks
                        if use_category not in self.available_blocks:
                            self.available_blocks[use_category] = []

                        # Check for duplicates
                        existing_block_texts = [b["text"] for b in self.available_blocks[use_category]]
                        for block in blocks:
                            if block.get("text") not in existing_block_texts:
                                self.available_blocks[use_category].append(block)
                                added_count += 1
            elif isinstance(package_data, list):
                # If it's a list, use the provided category name
                if category_name not in self.available_blocks:
                    self.available_blocks[category_name] = []

                # Check for duplicates
                existing_block_texts = [b["text"] for b in self.available_blocks[category_name]]
                for block in package_data:
                    if block.get("text") not in existing_block_texts:
                        self.available_blocks[category_name].append(block)
                        added_count += 1

            return added_count, category_name

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading package: {str(e)}")

    def load_all_packages(self, packages_dir="packages"):
        """Load all package files from a directory (for backward compatibility)"""
        total_added = 0
        if os.path.exists(packages_dir):
            for package_file in glob.glob(os.path.join(packages_dir, "*.json")):
                try:
                    added, _ = self.load_package_file(package_file)
                    total_added += added
                    print(f"Loaded package: {os.path.basename(package_file)}")
                except Exception as e:
                    print(f"Error loading package {package_file}: {e}")
        return total_added

    def load_custom_blocks(self):
        """Load custom blocks from file - 改进2: 只保存包路径"""
        print(f"Looking for custom blocks file: {self.custom_blocks_file}")
        
        if os.path.exists(self.custom_blocks_file):
            try:
                print(f"Found custom blocks file: {self.custom_blocks_file}")
                with open(self.custom_blocks_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                
                print(f"Loaded custom blocks data: {saved_data}")
                
                # 检查是新格式(只包含路径)还是旧格式(包含完整块数据)
                if isinstance(saved_data, dict) and "package_paths" in saved_data:
                    # 新格式: 只包含包路径
                    self.custom_package_paths = saved_data.get("package_paths", [])
                    
                    print(f"Found {len(self.custom_package_paths)} package paths to load")
                    
                    # 加载每个包
                    for package_path in self.custom_package_paths:
                        if os.path.exists(package_path):
                            try:
                                print(f"Loading package: {package_path}")
                                added_count, category = self.load_package_file(package_path)
                                print(f"  -> Added {added_count} blocks to category '{category}'")
                            except Exception as e:
                                print(f"Error loading custom package {package_path}: {e}")
                        else:
                            print(f"Custom package not found: {package_path}")
                else:
                    # 旧格式: 包含完整块数据，转换为新格式
                    print("Converting old custom blocks format to new format...")
                    # 这里可以添加转换逻辑，但为了简单起见，我们只清空旧数据
                    self.custom_package_paths = []
                    
            except json.JSONDecodeError as e:
                print(f"Error decoding custom blocks file: {e}")
                self.custom_package_paths = []
            except Exception as e:
                print(f"Error loading custom blocks: {e}")
                self.custom_package_paths = []
        else:
            print(f"Custom blocks file not found: {self.custom_blocks_file}")

    def save_custom_blocks(self):
        """Save custom blocks to file - 改进2: 只保存包路径"""
        try:
            # 只保存包路径，而不是完整的块数据
            save_data = {
                "package_paths": self.custom_package_paths,
                "version": "1.0",  # 添加版本标识
                "loaded_at": "2026-01-23"  # 添加时间戳用于调试
            }
            
            print(f"Saving custom blocks to: {self.custom_blocks_file}")
            print(f"  Package paths: {self.custom_package_paths}")
            
            with open(self.custom_blocks_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            print("Custom blocks saved successfully")
            
        except Exception as e:
            print(f"Error saving custom blocks: {e}")

    def add_custom_package(self, file_path, category_name=None):
        """添加自定义包并保存路径"""
        print(f"Adding custom package: {file_path}, category: {category_name}")
        
        # 检查路径是否已存在
        if file_path in self.custom_package_paths:
            # 包已存在，重新加载
            print(f"Package already exists: {file_path}, reloading...")
            # 可以先移除旧的，然后重新加载
            self.custom_package_paths.remove(file_path)
        
        # 加载包
        try:
            added_count, actual_category = self.load_package_file(file_path, category_name)
            
            if added_count > 0:
                # 添加路径到列表
                self.custom_package_paths.append(file_path)
                # 保存更新后的路径列表
                self.save_custom_blocks()
                
                print(f"Successfully added {added_count} blocks to category '{actual_category}'")
            else:
                print("No new blocks were added (all blocks already exist)")
            
            return added_count, actual_category
            
        except Exception as e:
            print(f"Error adding custom package: {e}")
            return 0, category_name
