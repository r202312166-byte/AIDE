import json
class CodeBlock:
    def __init__(self, block_id, block_type, x, y, width=None, height=60, text="", content=""):
        self.id = block_id
        self.type = block_type
        self.x = x
        self.y = y
        self.height = height
        self.text = text
        self.content = content

        # 计算宽度（根据内容和文本长度）
        self.width = self.calculate_width(width)

        self.color = self.get_default_color()
        self.connections = []
        self.continue_connection = None
        self.prev_connections = []
        self.next_block = None
        self.canvas_ids = (None, None)
        self.is_unclosed_tag = False
        self.end_connection = None

    def calculate_width(self, initial_width=None):
        """根据内容计算块宽度"""
        if initial_width is not None:
            return initial_width

        # 计算内容需要的宽度
        text_to_measure = self.text if self.text else self.content

        # 基本宽度加上每字符8像素
        base_width = 120
        char_width = 8

        # 计算所需宽度
        required_width = max(base_width, len(text_to_measure) * char_width)

        # 限制最大宽度
        max_width = 400
        min_width = 120

        return min(max(required_width, min_width), max_width)

    def update_content(self, new_content):
        """更新内容并重新计算宽度"""
        self.content = new_content

        # 如果内容简短，更新文本
        if "{" not in new_content and len(new_content) < 30:
            self.text = new_content
        elif not self.text or self.text == self.content:
            # 否则使用块类型作为文本
            self.text = self.type.capitalize()

        # 重新计算宽度
        self.width = self.calculate_width()
        
    def get_default_color(self):
        """返回基于块类型的默认颜色"""
        color_map = {
            "statement": "#4CAF50",
            "function": "#2196F3",
            "control": "#FF9800",
            "loop": "#9C27B0",
            "io": "#F44336",
            "variable": "#009688",
            "operator": "#FFC107",
            "import": "#607D8B",
            "gui": "#FF5722",
            "class": "#673AB7",
            "method": "#3F51B5",
            "defining": "#FF4081",
            "unclosed_tag": "#795548",
            "text": "#607D8B",
        }
        return color_map.get(self.type, "#757575")
    
    def get_connector_points(self):
        """Return connection points for the block"""
        top = (self.x + self.width/2, self.y)
        bottom = (self.x + self.width/2, self.y + self.height)
        left = (self.x, self.y + self.height/2)
        right = (self.x + self.width, self.y + self.height/2)
        
        return {
            "top": top,
            "bottom": bottom,
            "left": left,
            "right": right
        }
    
    def contains_point(self, x, y):
        """Check if point (x,y) is inside the block"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def requires_indentation(self):
        """Check if this block type requires indentation"""
        # Control, loop, defining, class, method and unclosed_tag blocks need indentation
        return self.type in ["control", "loop", "defining", "class", "method", "unclosed_tag"]
    
    def is_unclosed_html_tag(self):
        """Check if this is an unclosed HTML tag"""
        return self.type == "unclosed_tag"
    
    def move(self, dx, dy):
        """Move the block by dx, dy"""
        self.x += dx
        self.y += dy

    def to_dict(self):
        """Convert block to dictionary for serialization"""
        data = {
            "id": self.id,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "text": self.text,
            "content": self.content,
            "color": self.color,
            "connections": self.connections,
            "continue_connection": self.continue_connection,
            "prev_connections": self.prev_connections,
            "end_connection": self.end_connection,
        }

        # 添加Code Pack特定属性
        if hasattr(self, 'is_code_pack'):
            data["is_code_pack"] = self.is_code_pack
        if hasattr(self, 'pack_version'):
            data["pack_version"] = self.pack_version

        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create block from dictionary"""
        # 检查是否为Code Pack块
        if data.get("type") == "code_pack" and data.get("is_code_pack", False):
            # 尝试导入CodePackBlock类
            try:
                from plugins.code_pack_plugin import CodePackBlock
                block_cls = CodePackBlock
            except ImportError:
                # 如果插件不可用，使用普通CodeBlock
                block_cls = cls
                print("Warning: Code Pack plugin not available, using regular CodeBlock")
        else:
            block_cls = cls

        block = block_cls(
            data["id"],
            data["type"],
            data["x"],
            data["y"],
            data.get("width"),
            data.get("height", 60),
            data.get("text", ""),
            data.get("content", "")
        )

        # 设置其他属性
        block.color = data.get("color", block.color)
        block.connections = data.get("connections", [])
        block.continue_connection = data.get("continue_connection")
        block.prev_connections = data.get("prev_connections", [])
        block.is_unclosed_tag = data.get("is_unclosed_tag", False)
        block.end_connection = data.get("end_connection")

        # 设置Code Pack特定属性
        if hasattr(block, 'is_code_pack'):
            block.is_code_pack = data.get("is_code_pack", False)
        if hasattr(block, 'pack_version'):
            block.pack_version = data.get("pack_version", "1.0")

        return block