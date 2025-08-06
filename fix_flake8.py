#!/usr/bin/env python3
"""
Script to automatically fix common flake8 issues
"""

import os


def fix_whitespace_issues(file_path):
    """Fix W291, W293 whitespace issues"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        for line in lines:
            # Fix W291: trailing whitespace
            # Fix W293: blank line contains whitespace
            fixed_line = line.rstrip() + "\n" if line.strip() else "\n"
            fixed_lines.append(fixed_line)

        # Ensure file ends with newline (W292)
        if fixed_lines and not fixed_lines[-1].endswith("\n"):
            fixed_lines[-1] += "\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        print(f"Fixed whitespace issues in {file_path}")
        return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def fix_line_length_simple(file_path):
    """Fix simple line length issues"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            if len(line) <= 79:
                fixed_lines.append(line)
                continue

            # Simple fixes for common patterns
            if "import " in line and ", " in line:
                # Break long import lines
                if line.strip().startswith("from ") and " import " in line:
                    parts = line.split(" import ")
                    if len(parts) == 2:
                        from_part = parts[0]
                        imports = parts[1].split(", ")
                        if len(imports) > 1:
                            fixed_lines.append(from_part + " import (")
                            for i, imp in enumerate(imports):
                                if i == len(imports) - 1:
                                    fixed_lines.append(f"    {imp.strip()},")
                                else:
                                    fixed_lines.append(f"    {imp.strip()},")
                            fixed_lines.append(")")
                            continue

            # For other long lines, keep as is for manual review
            fixed_lines.append(line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fixed_lines))

        return True
    except Exception as e:
        print(f"Error fixing line length in {file_path}: {e}")
        return False


def main():
    """Fix flake8 issues in Python files"""

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files")

    for file_path in python_files:
        print(f"Processing {file_path}")
        fix_whitespace_issues(file_path)


if __name__ == "__main__":
    main()
