#!/usr/bin/env python3
"""
自動修復 flake8 錯誤的腳本
"""

import re
import subprocess
import sys
from pathlib import Path


def fix_line_length(content, max_length=79):
    """修復行長度過長的問題"""
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        if len(line) <= max_length:
            fixed_lines.append(line)
            continue

        # 如果是導入語句，嘗試拆分
        if line.strip().startswith("from ") and "import" in line:
            if "(" not in line and "," in line:
                # 拆分多個導入
                parts = line.split("import", 1)
                if len(parts) == 2:
                    prefix = parts[0] + "import ("
                    imports = [imp.strip() for imp in parts[1].split(",")]
                    fixed_lines.append(prefix)
                    for imp in imports:
                        fixed_lines.append(f"    {imp.strip()},")
                    fixed_lines.append(")")
                    continue

        # 如果是字符串，嘗試在適當位置換行
        if '"' in line or "'" in line:
            # 簡單的字符串拆分
            indent = len(line) - len(line.lstrip())
            if len(line) > max_length:
                # 尋找適當的斷點
                for i in range(max_length - 10, 40, -1):
                    if line[i] in [" ", ",", ".", "(", ")"]:
                        fixed_lines.append(line[:i] + " \\")
                        fixed_lines.append(
                            " " * (indent + 4) + line[i:].lstrip()
                        )
                        break
                else:
                    fixed_lines.append(line)  # 如果找不到好的斷點，保持原樣
            else:
                fixed_lines.append(line)
        else:
            # 對於其他行，簡單處理
            if len(line) > max_length and "(" in line:
                # 尋找括號後的位置進行換行
                paren_pos = line.find("(") + 1
                if paren_pos > 0 and paren_pos < max_length - 10:
                    before_paren = line[:paren_pos]
                    after_paren = line[paren_pos:]
                    indent = len(before_paren) - len(before_paren.lstrip()) + 4
                    fixed_lines.append(before_paren)
                    fixed_lines.append(" " * indent + after_paren)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

    return "\n".join(fixed_lines)


def remove_unused_imports(content):
    """移除明顯未使用的導入"""
    lines = content.split("\n")
    fixed_lines = []

    # 常見的未使用導入模式
    unused_patterns = [
        r"^from abc import ABC, abstractmethod\s*$",
        r"^import asyncio\s*$",
        r"^import torch\s*$",
        r"^import torchaudio\s*$",
        r"^import os\s*$",
        r"^import tempfile\s*$",
        r"^from typing import.*Optional.*$",
        r"^from typing import.*Tuple.*$",
        r"^from typing import.*Union.*$",
        r"^from datetime import datetime\s*$",
    ]

    for line in lines:
        should_remove = False
        for pattern in unused_patterns:
            if re.match(pattern, line.strip()):
                # 簡單檢查：如果導入的內容在後續代碼中出現，則保留
                import_parts = []
                if "import" in line:
                    if "from" in line:
                        # from xxx import yyy
                        parts = line.split("import", 1)
                        if len(parts) == 2:
                            import_parts = [
                                p.strip() for p in parts[1].split(",")
                            ]
                    else:
                        # import xxx
                        import_parts = [line.replace("import", "").strip()]

                # 檢查是否在內容中使用
                rest_content = "\n".join(
                    lines[lines.index(line) + 1 :]
                )  # noqa: E203
                used = False
                for part in import_parts:
                    clean_part = (
                        part.split(" as ")[0] if " as " in part else part
                    )
                    if clean_part and clean_part in rest_content:
                        used = True
                        break

                if not used:
                    should_remove = True
                break

        if not should_remove:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_bare_except(content):
    """修復裸露的 except 語句"""
    content = re.sub(r"except\s*:", "except Exception:", content)
    return content


def fix_trailing_whitespace(content):
    """移除行尾空白"""
    lines = content.split("\n")
    fixed_lines = [line.rstrip() for line in lines]
    return "\n".join(fixed_lines)


def fix_whitespace_before_colon(content):
    """修復冒號前的空白"""
    content = re.sub(r"\s+:", ":", content)
    return content


def fix_python_file(file_path):
    """修復單個 Python 檔案"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 應用修復
        content = remove_unused_imports(content)
        content = fix_line_length(content)
        content = fix_bare_except(content)
        content = fix_trailing_whitespace(content)
        content = fix_whitespace_before_colon(content)

        # 只有在內容有變化時才寫入
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ 修復: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"✗ 錯誤處理 {file_path}: {e}")
        return False


def main():
    """主函數"""
    services_dir = Path("services")
    if not services_dir.exists():
        print("錯誤: 找不到 services 目錄")
        sys.exit(1)

    fixed_count = 0
    total_count = 0

    print("開始修復 Python 檔案...")

    # 遞歸處理所有 Python 檔案
    for py_file in services_dir.rglob("*.py"):
        total_count += 1
        if fix_python_file(py_file):
            fixed_count += 1

            print("\n修復完成!")
    print(f"總檔案數: {total_count}")
    print(f"已修復: {fixed_count}")

    # 運行 flake8 檢查結果
    print("\n運行 flake8 檢查...")
    try:
        result = subprocess.run(
            [
                "flake8",
                "services/",
                "--max-line-length=79",
                "--count",
                "--statistics",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✓ 所有 flake8 檢查通過!")
        else:
            print("還有一些問題需要手動修復:")
            print(result.stdout)

    except FileNotFoundError:
        print("注意: 無法運行 flake8 檢查 (未安裝)")


if __name__ == "__main__":
    main()
