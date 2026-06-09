import tkinter as tk
from ui import OurNotepadBuilder
from minimal_patch import patch_block_loader_at_runtime, patch_builder_at_runtime

def main():
    root = tk.Tk()
    app = OurNotepadBuilder(root)
    
    # 应用运行时补丁
    app = patch_block_loader_at_runtime(app)
    app = patch_builder_at_runtime(app)
    
    # 重新加载块
    app.update_blocks_for_language(app.lang_mode.current_mode)
    
    root.mainloop()

if __name__ == "__main__":
    main()