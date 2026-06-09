import json
import os
from typing import Any


class LanguageModeManager:
    def __init__(self):
        self.current_mode = "text"  # 默认模式改为"text"模式
        self.modes = {
            "text": {  # 新增text模式
                "name": "Text",
                "file_extension": ".txt",
                "description": "Plain text mode - exports text files only",
                "export_rules": self.text_export_rule,
                "supports_special": True  # 新增：支持Special类别
            },
            "python": {
                "name": "Python",
                "file_extension": ".py",
                "description": "Python programming language",
                "export_rules": self.python_export_rule,
                "supports_special": True  # 新增：支持Special类别
            },
            "html": {
                "name": "HTML",
                "file_extension": ".html",
                "description": "HyperText Markup Language",
                "export_rules": self.html_export_rule,
                "unclosed_tag_rules": self.html_unclosed_tag_rule,
                "supports_special": True  # 新增：支持Special类别
            },
            "c_cpp": {
                "name": "C/C++",
                "file_extension": ".cpp",
                "description": "C and C++ programming languages",
                "export_rules": self.c_cpp_export_rule,
                "supports_special": True  # 新增：支持Special类别
            },
            "java": {
                "name": "Java",
                "file_extension": ".java",
                "description": "Java programming language",
                "export_rules": self.java_export_rule,
                "supports_special": True  # 新增：支持Special类别
            }
        }

        # Load language-specific packages
        self.language_packages = {}
        self.load_language_packages()

    def load_language_packages(self):
        """Load language-specific packages from packages directory"""
        packages_dir = "packages"
        if not os.path.exists(packages_dir):
            return

        # Language-specific package files
        language_files = {
            "python": ["Python.json"],
            "html": ["HTML.json"],
            "c_cpp": ["C_Cpp.json"],
            "java": ["Java.json"],
            "text": []  # text模式不需要特定包
        }

        for lang, files in language_files.items():
            self.language_packages[lang] = {}
            for file_name in files:
                file_path = os.path.join(packages_dir, file_name)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            self.language_packages[lang][file_name.replace('.json', '')] = json.load(f)
                    except Exception as e:
                        print(f"Error loading {file_name}: {e}")

    # ===== 新增text模式的导出规则 =====
    def text_export_rule(self, code_lines, blocks_dict=None, connections_dict=None):
        """Text export rule: simply return the lines as-is"""
        return code_lines
    
    def set_mode(self, mode):
        """Set current language mode"""
        if mode in self.modes:
            self.current_mode = mode
            return True
        return False
    
    def get_current_mode(self):
        """Get current language mode"""
        return self.current_mode
    
    def get_mode_info(self, mode=None):
        """Get information about a language mode"""
        if mode is None:
            mode = self.current_mode
        return self.modes.get(mode, {})
    
    def get_all_modes(self):
        """Get all available language modes"""
        return list(self.modes.keys())
    
    # ===== Export Rules =====
    
    def python_export_rule(self, code_lines, blocks_dict=None, connections_dict=None):
        """Python export rule (default - no changes)"""
        return code_lines

    def html_export_rule(self, code_lines, blocks_dict=None, connections_dict=None):
        """HTML export rule: handle unclosed tags and text blocks"""
        if blocks_dict is None:
            blocks_dict = {}
        if connections_dict is None:
            connections_dict = {}

        processed_lines: list[Any] = []

        # Build control structure map
        control_map = {}
        for control_id, end_id in connections_dict.get("end_lines", []):
            control_map[control_id] = end_id

        i = 0
        while i < len(code_lines):
            line = code_lines[i]
            stripped = line.strip()

            # 检查是否来自未闭合标签块
            for block_id, block in blocks_dict.items():
                if block.type == "unclosed_tag" and stripped == block.content.strip():
                    # 检查是否有end block连接
                    if block_id in control_map:
                        # 找到对应的end block
                        end_id = control_map[block_id]
                        # 添加闭合标签在新行
                        indent = "    " * (line.count("    "))
                        tag_name = stripped.strip("<>")
                        closing_tag = f"</{tag_name}>"

                        # 在end block位置添加闭合标签
                        for j in range(i + 1, len(code_lines)):
                            if code_lines[j].strip().lower() == "end block":
                                code_lines[j] = indent + closing_tag
                                break
                    break

            i += 1

        # 移除剩余的"end block"文本
        processed_lines = [line for line in code_lines if line.strip().lower() != "end block"]

        return processed_lines
    
    def html_unclosed_tag_rule(self, tag_content, indent_level=0):
        """Generate HTML for unclosed tags"""
        indent = "    " * indent_level
        return f"{indent}<{tag_content}>"

    def c_cpp_export_rule(self, code_lines, blocks_dict=None, connections_dict=None):
        """C/C++ export rule: add {} after structures with proper indentation"""
        if blocks_dict is None:
            blocks_dict = {}
        if connections_dict is None:
            connections_dict = {}

        processed_lines = []
        i = 0

        # Build control structure map
        control_map = {}
        for control_id, end_id in connections_dict.get("end_lines", []):
            control_map[control_id] = end_id

        while i < len(code_lines):
            line = code_lines[i]
            stripped = line.strip()

            # Check for control structures (if, for, while, etc.)
            control_structures = ["if", "for", "while", "do", "switch", "else if"]
            is_control = any(stripped.startswith(struct) for struct in control_structures)

            # Check if this line comes from a control block
            is_control_block = False
            block_id = None

            for bid, block in blocks_dict.items():
                if block.content.strip() in stripped or stripped in block.content:
                    if block.type in ["control", "loop"]:
                        is_control_block = True
                        block_id = bid
                    break

            if is_control_block and block_id:
                # This is a control structure block
                if not stripped.endswith("{"):
                    # Add opening brace
                    processed_lines.append(f"{line} {{")

                    # Check if there's an end block connection
                    if block_id in control_map:
                        # The body will be added by the blocks in between
                        pass
                    else:
                        # Empty body
                        processed_lines.append("    " * (line.count("    ") + 1) + "// TODO: Add code here")
                        processed_lines.append("    " * line.count("    ") + "}")
                else:
                    processed_lines.append(line)
            elif stripped.lower() == "end block":
                # Add closing brace on new line
                indent_level = line.count("    ")
                processed_lines.append("    " * indent_level + "}")
            else:
                processed_lines.append(line)
            i += 1

        return processed_lines

    def java_export_rule(self, code_lines, blocks_dict=None, connections_dict=None):
        """Java export rule: similar to C/C++ but with Java-specific patterns"""
        if blocks_dict is None:
            blocks_dict = {}
        if connections_dict is None:
            connections_dict = {}

        processed_lines = []
        i = 0

        # Build control structure map
        control_map = {}
        for control_id, end_id in connections_dict.get("end_lines", []):
            control_map[control_id] = end_id

        while i < len(code_lines):
            line = code_lines[i]
            stripped = line.strip()

            # Check for control structures
            control_structures = ["if", "for", "while", "do", "switch", "else if",
                                  "try", "catch", "finally", "synchronized"]
            is_control = any(stripped.startswith(struct) for struct in control_structures)

            # Check for class/method definitions
            is_definition = stripped.startswith("class ") or stripped.startswith("public ") or \
                            stripped.startswith("private ") or stripped.startswith("protected ")

            # Check if this line comes from a control or definition block
            is_special_block = False
            block_id = None

            for bid, block in blocks_dict.items():
                if block.content.strip() in stripped or stripped in block.content:
                    if block.type in ["control", "loop", "class", "method", "defining"]:
                        is_special_block = True
                        block_id = bid
                    break

            if (is_control or is_definition or is_special_block) and not stripped.endswith("{"):
                # Add opening brace
                processed_lines.append(f"{line} {{")

                # Check if there's an end block connection
                if block_id and block_id in control_map:
                    # The body will be added by the blocks in between
                    pass
                else:
                    # Empty body
                    processed_lines.append("    " * (line.count("    ") + 1) + "// TODO: Add code here")
                    processed_lines.append("    " * line.count("    ") + "}")
            elif stripped.lower() == "end block":
                # Add closing brace on new line
                indent_level = line.count("    ")
                processed_lines.append("    " * indent_level + "}")
            else:
                processed_lines.append(line)
            i += 1

        return processed_lines
    
    def apply_export_rules(self, code_lines, blocks_dict=None, connections_dict=None):
        """Apply export rules based on current language mode"""
        rule_func = self.modes[self.current_mode]["export_rules"]
        return rule_func(code_lines, blocks_dict, connections_dict)
