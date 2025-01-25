import os
import re

def merge_python_files(entry_point, output_file):
    visited = set()
    merged_content = []

    def process_file(file_path):
        if file_path in visited:
            return
        visited.add(file_path)
        
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        for line in lines:
            # Skip import lines (handle manually if needed)
            if line.startswith('import ') or line.startswith('from '):
                continue
            merged_content.append(line)
        
        # Look for local imports and inline them
        for line in lines:
            match = re.match(r'from (\S+) import (\S+)', line) or re.match(r'import (\S+)', line)
            if match:
                module_name = match.group(1).replace('.', '/') + '.py'
                if os.path.exists(module_name):
                    process_file(module_name)

    process_file(entry_point)
    with open(output_file, 'w') as output:
        output.writelines(merged_content)

# Example usage
merge_python_files('btc_puzz.py', 'single_file.py')
