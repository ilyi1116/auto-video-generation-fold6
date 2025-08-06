#!/usr/bin/env python3
"""
批量修復常見的語法錯誤
"""
import ast
import re
from pathlib import Path


def check_syntax(file_path):
    """檢查文件語法是否正確"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except Exception as e:
        return False, str(e)


def fix_common_syntax_errors(file_path):
    """修復常見語法錯誤"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # 修復常見的引號錯誤
    content = re.sub(r'"([^"]*)"([^"\']*)[\'"]([^"\']*)"[\'"]?[\'"]?', r'f"\1\2\3"', content)

    # 修復缺少導入語句的錯誤
    if "APIRouter," in content and "from fastapi import" not in content:
        content = re.sub(
            r"import structlog\n\s*APIRouter,",
            "import structlog\nfrom fastapi import (\n    APIRouter,",
            content,
        )

    # 修復縮進錯誤（簡單情況）
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # 如果行以多個空格開始但前一行不是縮進的，可能是錯誤
        if line.strip() and line.startswith("    ") and i > 0:
            prev_line = lines[i - 1].strip()
            if prev_line and not lines[i - 1].startswith("    ") and not prev_line.endswith(":"):
                # 移除錯誤的縮進
                line = line.lstrip()

        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # 如果內容有變化，保存文件
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    return False


def main():
    """主函數"""
    project_root = Path(__file__).parent.parent

    # 查找所有Python文件
    python_files = []
    for pattern in ["**/*.py"]:
        python_files.extend(project_root.glob(pattern))

    syntax_errors = []
    fixed_files = []

    print(f"檢查 {len(python_files)} 個 Python 文件...")

    for file_path in python_files:
        # 跳過某些目錄
        if any(skip in str(file_path) for skip in [".git", "__pycache__", ".pytest_cache"]):
            continue

        is_valid, error = check_syntax(file_path)
        if not is_valid:
            syntax_errors.append((file_path, error))
            print(f"語法錯誤: {file_path}")
            print(f"  錯誤: {error}")

            # 嘗試修復
            if fix_common_syntax_errors(file_path):
                fixed_files.append(file_path)
                print(f"  已修復: {file_path}")

                # 重新檢查
                is_valid_after, _ = check_syntax(file_path)
                if is_valid_after:
                    print(f"  ✅ 修復成功")
                else:
                    print(f"  ❌ 修復失敗，需要手動處理")

    print(f"\n總結:")
    print(f"- 檢查文件: {len(python_files)}")
    print(f"- 發現語法錯誤: {len(syntax_errors)}")
    print(f"- 自動修復: {len(fixed_files)}")

    if syntax_errors:
        print(f"\n仍有 {len(syntax_errors) - len(fixed_files)} 個文件需要手動修復:")
        for file_path, error in syntax_errors:
            if file_path not in fixed_files:
                print(f"  {file_path}: {error}")


if __name__ == "__main__":
    main()
