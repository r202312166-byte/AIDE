import json
import os
from tkinter import filedialog, messagebox
from core.code_block import CodeBlock

class FileHandler:
    def __init__(self, app):
        self.app = app
        self.last_save_path = None

    def save_project(self):
        """Save project directly to projects folder without dialog - uses project name"""
        project_dir = "projects"
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        # Check if file with same name exists
        save_path = os.path.join(project_dir, f"{self.app.project_name}.aide")
        
        if os.path.exists(save_path):
            # File exists, call save_project_as
            self.save_project_as()
            return

        # Save directly without asking
        self._do_save(save_path)

    def save_project_as(self):
        """Save project with dialog (original save functionality)"""
        project_dir = "projects"
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        # Through app access main app's methods and properties
        save_data = {
            "project_name": self.app.project_name,
            "blocks": {bid: block.to_dict() for bid, block in self.app.blocks.items()},
            "block_counter": self.app.block_counter,
            "sequence_lines": self.app.sequence_lines,
            "end_lines": self.app.end_lines,
            "continue_lines": self.app.continue_lines,
            "polyline_points": {f"{s},{e}": points for (s, e), points in self.app.polyline_points.items()}
        }

        filename = filedialog.asksaveasfilename(
            initialdir=project_dir,
            defaultextension=".aide",
            filetypes=[("AIDE project", "*.aide"), ("All Files", "*.*")],
            initialfile=f"{self.app.project_name}.aide"
        )

        if filename:
            self._do_save(filename)

    def _do_save(self, filename):
        """Perform the actual save operation"""
        project_dir = "projects"
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        save_data = {
            "project_name": self.app.project_name,
            "blocks": {bid: block.to_dict() for bid, block in self.app.blocks.items()},
            "block_counter": self.app.block_counter,
            "sequence_lines": self.app.sequence_lines,
            "end_lines": self.app.end_lines,
            "continue_lines": self.app.continue_lines,
            "polyline_points": {f"{s},{e}": points for (s, e), points in self.app.polyline_points.items()}
        }

        try:
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=2)
            self.last_save_path = filename
            messagebox.showinfo("Save Successful", f"Project saved to {filename}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save project: {e}")

    def import_project(self):
        """导入保存的项目（包含折点）"""
        project_dir = "projects"
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        filename = filedialog.askopenfilename(
            initialdir=project_dir,
            defaultextension=".aide",
            filetypes=[("AIDE project", "*.aide"), ("All Files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    load_data = json.load(f)

                # 清空当前项目
                self.app.blocks = {}
                self.app.sequence_lines = []
                self.app.end_lines = []
                self.app.continue_lines = []
                self.app.polyline_points = {}
                self.app.connection_lines = {}

                # 加载数据
                self.app.project_name = load_data.get("project_name", self.app.lang.get("untitled_project"))
                
                # 更新窗口标题
                self.app.root.title(f"AntimonyIDE - {self.app.project_name}")

                # 加载块
                blocks_data = load_data.get("blocks", {})
                for bid, block_data in blocks_data.items():
                    self.app.blocks[bid] = CodeBlock.from_dict(block_data)

                self.app.block_counter = load_data.get("block_counter", 0)
                self.app.sequence_lines = load_data.get("sequence_lines", [])
                self.app.end_lines = load_data.get("end_lines", [])
                self.app.continue_lines = load_data.get("continue_lines", [])

                # 加载折点
                polyline_data = load_data.get("polyline_points", {})
                for key_str, points in polyline_data.items():
                    parts = key_str.split(",")
                    if len(parts) == 2:
                        self.app.polyline_points[(parts[0], parts[1])] = points

                # 重绘所有内容
                if hasattr(self.app, 'canvas'):
                    self.app.canvas.delete("all")
                    self.app.draw_grid()
                    self.app.draw_all_blocks()

                # 清除编辑器
                self.app.deselect_all()

                messagebox.showinfo("Import Successful", f"Project imported from {filename}")

            except Exception as e:
                messagebox.showerror("Import Error", f"Could not import project: {e}")
