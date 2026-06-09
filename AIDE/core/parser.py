import ast
import re

class PythonFileParser:
    @staticmethod
    def parse_gui_python_file(filepath):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            metadata = {}
            lines = content.split('\n')
            for line in lines:
                if line.startswith('# Frame:'):
                    metadata['frame_name'] = line.replace('# Frame:', '').strip()
                elif line.startswith('# Window Title:'):
                    metadata['window_title'] = line.replace('# Window Title:', '').strip()
                elif line.startswith('# Window Size:'):
                    metadata['window_size'] = line.replace('# Window Size:', '').strip()
            
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
            
            class_info = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {'name': node.name, 'methods': []}
                    break
            
            return {
                'metadata': metadata,
                'imports': imports,
                'class_info': class_info,
                'raw_content': content
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def extract_widgets_from_code(content):
        widgets = []
        widget_pattern = r'self\.(\w+)\s*=\s*(?:tk|ttk)\.(\w+)\([^)]*\)'
        
        for match in re.finditer(widget_pattern, content):
            var_name = match.group(1)
            widget_type = match.group(2)
            widgets.append({'var_name': var_name, 'widget_type': widget_type, 'type': 'gui_widget'})
        
        return widgets
    
    @staticmethod
    def extract_grid_layout(content):
        layouts = []
        grid_pattern = r'self\.(\w+)\.grid\(([^)]*)\)'
        
        for match in re.finditer(grid_pattern, content):
            var_name = match.group(1)
            params_str = match.group(2)
            params = {}
            param_pairs = re.findall(r'(\w+)\s*=\s*([^,]+)', params_str)
            for key, value in param_pairs:
                params[key] = value.strip()
            layouts.append({'var_name': var_name, 'method': 'grid', 'params': params})
        
        return layouts