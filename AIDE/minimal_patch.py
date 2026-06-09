import os
# save_as: minimal_patch.py
"""
最小修补文件 - 直接修补运行时的方法
"""

import types

def patch_block_loader_at_runtime(app):
    """运行时修补BlockLoader"""
    from utils.block_loader import BlockLoader
    
    # 保存原始方法
    original_load_language_packages = BlockLoader.load_language_packages
    
    def load_language_packages_fixed(self, language_mode):
        """修复的load_language_packages方法"""
        print(f"Fixed: Loading language packages for {language_mode}")
        
        # 先清空
        self.available_blocks = {}
        
        # 加载默认块
        from utils.block_loader import BlockLoader as BL
        default_blocks = BL.load_default_blocks(self)
        self.available_blocks.update(default_blocks)
        
        # 加载包
        packages_dir = "packages"
        if os.path.exists(packages_dir):
            # 定义要加载的文件
            files_to_load = []
            if language_mode == "python":
                files_to_load = ["Python.json", "Common.json"]
            elif language_mode == "html":
                files_to_load = ["HTML.json", "Common.json"]
            elif language_mode == "c_cpp":
                files_to_load = ["C_Cpp.json", "Common.json"]
            elif language_mode == "java":
                files_to_load = ["Java.json", "Common.json"]
            elif language_mode == "text":
                files_to_load = ["Common.json"]
            
            for file_name in files_to_load:
                file_path = os.path.join(packages_dir, file_name)
                if os.path.exists(file_path):
                    try:
                        import json
                        with open(file_path, 'r', encoding='utf-8') as f:
                            package_data = json.load(f)
                        
                        if isinstance(package_data, dict):
                            for category, blocks in package_data.items():
                                if category not in self.available_blocks:
                                    self.available_blocks[category] = []
                                # 添加块（简单去重）
                                for block in blocks:
                                    exists = False
                                    for existing in self.available_blocks[category]:
                                        if (existing.get("text") == block.get("text") and 
                                            existing.get("type") == block.get("type")):
                                            exists = True
                                            break
                                    if not exists:
                                        self.available_blocks[category].append(block)
                        
                        print(f"  ✓ Loaded: {file_name}")
                    except Exception as e:
                        print(f"  ✗ Error loading {file_name}: {e}")
        
        # 确保Special类别
        if "Special" not in self.available_blocks:
            self.available_blocks["Special"] = []
        
        # 确保有Code Pack块
        code_pack_exists = False
        for block in self.available_blocks.get("Special", []):
            if block.get("type") == "code_pack":
                code_pack_exists = True
                break
        
        if not code_pack_exists:
            self.available_blocks["Special"].append({
                "type": "code_pack",
                "text": "Code Pack",
                "content": "# Code Pack",
                "template": "",
                "description": "Code pack block",
                "is_code_pack": True
            })
        
        return self.available_blocks
    
    # 应用补丁
    BlockLoader.load_language_packages = load_language_packages_fixed
    app.block_loader.load_language_packages = types.MethodType(load_language_packages_fixed, app.block_loader)
    
    print("✓ BlockLoader patched at runtime")
    return app

def patch_builder_at_runtime(app):
    """运行时修补Builder"""
    
    # 保存原始方法
    original_update_blocks = app.update_blocks_for_language
    
    def update_blocks_for_language_fixed(self, language_mode):
        """修复的update_blocks_for_language方法"""
        print(f"Fixed: Updating blocks for {language_mode}")
        
        # 调用修补后的BlockLoader方法
        self.block_loader.load_language_packages(language_mode)
        
        # 更新UI
        self.update_blocks_list()
    
    # 应用补丁
    app.update_blocks_for_language = types.MethodType(update_blocks_for_language_fixed, app)
    
    print("✓ Builder patched at runtime")
    return app

def apply_minimal_patch():
    """应用最小补丁"""
    print("=" * 60)
    print("Applying Minimal Patch...")
    print("=" * 60)
    
    # 这个函数需要在app创建后调用
    print("请在创建app后调用：")
    print("""
from minimal_patch import patch_block_loader_at_runtime, patch_builder_at_runtime

app = OurNotepadBuilder(root)
app = patch_block_loader_at_runtime(app)
app = patch_builder_at_runtime(app)
    """)
    
    return True

if __name__ == "__main__":
    apply_minimal_patch()
