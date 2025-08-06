#!/usr/bin/env python3
"""
修復剩餘的語法錯誤
重點處理字符串、引號和縮進問題
"""
import ast
import re
from pathlib import Path


def fix_file_content(file_path):
    """修復文件中的語法錯誤"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return False, "File encoding error"

    original_content = content

    # 修復常見的f-string和字符串引號問題
    # 修復 f" 後面沒有對應結束引號的問題
    content = re.sub(r'f"([^"]*)"([^"\']*)[\'"]?', r'f"\1\2"', content)

    # 修復單獨的 f" 開始
    content = re.sub(r'^(\s*)f"$', r'\1"""', content, flags=re.MULTILINE)

    # 修復缺失的引號結束
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        pass

        # 修復常見的字符串問題
        if line.strip().endswith('f"') or line.strip().endswith('"f'):
            line = line.rstrip('f"').rstrip('"f') + '""'

        # 修復缺少開始引號的情況
        if re.search(r'[^"\']\s*[a-zA-Z_][a-zA-Z0-9_]*\s*"', line):
            line = re.sub(r'([^"\']\s*)([a-zA-Z_][a-zA-Z0-9_]*\s*)"', r'\1"\2"', line)

        # 修復字典key缺少引號
        line = re.sub(r"(\{|,\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', line)

        # 修復布爾值、None等被錯誤加引號
        line = re.sub(r'"(True|False|None)"', r"\1", line)

        # 修復數字被錯誤加引號
        line = re.sub(r'"(\d+)"(?=\s*[,})\]])', r"\1", line)

        # 修復縮進問題 - 如果一行突然有錯誤的縮進
        if line.strip() and i > 0:
            prev_line = lines[i - 1]
            if prev_line.strip() and not prev_line.strip().endswith(":"):
                # 如果當前行縮進但前一行不是冒號結尾，可能是錯誤縮進
                if line.startswith("    ") and not prev_line.startswith("    "):
                    line = line.lstrip()

        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # 修復try-except塊
    content = re.sub(r"try:\s*\n\s*except", "try:\n    pass\nexcept", content)

    # 修復空的類和函數定義
    content = re.sub(r"(def [^:]+:)\s*\n(?=\s*(def|class|\n))", r"\1\n    pass\n", content)
    content = re.sub(r"(class [^:]+:)\s*\n(?=\s*(def|class|\n))", r"\1\n    pass\n", content)

    # 如果有變化，保存文件
    if content != original_content:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, None
        except Exception as e:
            return False, f"Write error: {e}"

    return False, "No changes needed"


def main():
    """主函數"""
    project_root = Path(__file__).parent.parent

    # 重點修復有語法錯誤的文件
    problematic_files = [
        "src/services/ai-service/ai_orchestrator.py",
        "src/services/api-gateway/app/routers.py",
        "src/services/api-gateway/app/proxy.py",
        "src/services/trend-service/main.py",
        "src/services/video-service/short_video_generator.py",
        "src/services/video-service/ai/gemini_client.py",
        "src/services/auth-service/app/models.py",
        "scripts/run-comprehensive-optimization.py",
    ]

    fixed_count = 0
    total_count = len(problematic_files)

    print(f"修復 {total_count} 個有語法錯誤的文件...")

    for file_path in problematic_files:
        full_path = project_root / file_path

        if not full_path.exists():
            print(f"跳過不存在的文件: {file_path}")
            continue

        # 檢查原始語法
        is_valid_before, error_before = check_syntax(full_path)

        if is_valid_before:
            print(f"✅ {file_path} - 語法已正確")
            continue

        print(f"🔧 修復 {file_path}")
        print(f"   原始錯誤: {error_before}")

        # 嘗試修復
        fixed, fix_error = fix_file_content(full_path)

        if fix_error and "No changes needed" not in fix_error:
            print(f"   修復失敗: {fix_error}")
            continue

        # 檢查修復後的語法
        is_valid_after, error_after = check_syntax(full_path)

        if is_valid_after:
            print("   ✅ 修復成功")
            fixed_count += 1
        else:
            print(f"   ❌ 修復失敗: {error_after}")

    print(f"\n修復結果: {fixed_count}/{total_count} 個文件已修復")


def check_syntax(file_path):
    """檢查文件語法"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    main()
