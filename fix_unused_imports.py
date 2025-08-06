#!/usr/bin/env python3
"""
Script to fix unused imports and other common flake8 issues
"""

import ast
import os
import re
import sys


def find_unused_imports(file_path):
    """Find unused imports in a Python file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse AST to find imports and usage
        tree = ast.parse(content)

        imports = {}
        imports_lines = {}

        # Collect all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = alias.name
                    imports_lines[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = f"{node.module}.{alias.name}" if node.module else alias.name
                    imports_lines[name] = node.lineno

        # Find which imports are used
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle cases like module.function
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        # Find unused imports
        unused = []
        for name in imports:
            if name not in used_names:
                unused.append((name, imports_lines[name]))

        return unused

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []


def remove_unused_imports(file_path):
    """Remove unused imports from a file"""
    try:
        unused = find_unused_imports(file_path)
        if not unused:
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Sort by line number in reverse order to avoid index shifting
        unused.sort(key=lambda x: x[1], reverse=True)

        lines_to_remove = set()
        for name, line_no in unused:
            # Check if this line contains only this import
            line_content = lines[line_no - 1].strip()
            if (
                f"import {name}" in line_content
                or f"from " in line_content
                and f" {name}" in line_content
            ):
                lines_to_remove.add(line_no - 1)

        # Remove lines
        new_lines = []
        for i, line in enumerate(lines):
            if i not in lines_to_remove:
                new_lines.append(line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        print(f"Removed {len(unused)} unused imports from {file_path}")
        return True

    except Exception as e:
        print(f"Error removing unused imports from {file_path}: {e}")
        return False


def fix_boolean_comparisons(file_path):
    """Fix == True and == False comparisons"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace == True with is True
        content = re.sub(r"== True\b", "is True", content)
        # Replace == False with is False
        content = re.sub(r"== False\b", "is False", content)
        # Replace != True with is not True
        content = re.sub(r"!= True\b", "is not True", content)
        # Replace != False with is not False
        content = re.sub(r"!= False\b", "is not False", content)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"Error fixing boolean comparisons in {file_path}: {e}")
        return False


def fix_line_lengths(file_path):
    """Fix basic line length issues"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        for line in lines:
            if len(line.rstrip()) <= 79:
                fixed_lines.append(line)
                continue

            # Try to fix common patterns
            stripped = line.rstrip()
            indent = len(line) - len(line.lstrip())
            indent_str = line[:indent]

            # Fix long import lines
            if "import " in stripped and "," in stripped:
                if stripped.strip().startswith("from ") and " import " in stripped:
                    parts = stripped.split(" import ", 1)
                    if len(parts) == 2 and "," in parts[1]:
                        from_part = parts[0]
                        imports = [imp.strip() for imp in parts[1].split(",")]
                        if len(imports) > 1:
                            fixed_lines.append(f"{from_part} import (\n")
                            for i, imp in enumerate(imports):
                                comma = "," if i < len(imports) - 1 else ","
                                fixed_lines.append(f"{indent_str}    {imp}{comma}\n")
                            fixed_lines.append(f"{indent_str})\n")
                            continue

            # For other long lines, just keep them for manual review
            fixed_lines.append(line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True

    except Exception as e:
        print(f"Error fixing line lengths in {file_path}: {e}")
        return False


def main():
    """Main function to fix various flate8 issues"""
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        # Find all Python files
        files = []
        for root, dirs, filenames in os.walk("."):
            for filename in filenames:
                if filename.endswith(".py"):
                    files.append(os.path.join(root, filename))

    print(f"Processing {len(files)} files...")

    for file_path in files:
        print(f"Processing {file_path}")

        # Skip if it's this script itself
        if file_path.endswith("fix_unused_imports.py"):
            continue

        # Fix boolean comparisons
        fix_boolean_comparisons(file_path)

        # Fix basic line lengths
        fix_line_lengths(file_path)

        # Note: Skipping unused imports for now as it's complex and risky


if __name__ == "__main__":
    main()
