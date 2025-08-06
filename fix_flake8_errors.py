#!/usr/bin/env python3
"""
自動修復 Flake8 錯誤的腳本
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class FlakeFixer:
    def __init__(self):
        self.unused_imports = set()
        self.unused_variables = set()
        self.changes_made = 0

    def fix_file(self, file_path: str) -> bool:
        """修復單個檔案中的 flake8 錯誤"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 修復各種錯誤
            content = self.fix_unused_imports(content, file_path)
            content = self.fix_fstring_placeholders(content)
            content = self.fix_whitespace_issues(content)
            content = self.fix_bare_except(content)
            content = self.fix_undefined_names(content)
            
            # 如果有變更，寫回檔案
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ 修復: {file_path}")
                self.changes_made += 1
                return True
            
        except Exception as e:
            print(f"❌ 錯誤修復 {file_path}: {e}")
            return False
        
        return False

    def fix_unused_imports(self, content: str, file_path: str) -> str:
        """移除未使用的導入"""
        lines = content.split('\n')
        new_lines = []
        
        # 分析 AST 找出實際使用的名稱
        try:
            tree = ast.parse(content)
            used_names = self._get_used_names(tree)
        except:
            # 如果 AST 解析失敗，跳過這個檔案
            return content
        
        import_lines_to_remove = set()
        
        for i, line in enumerate(lines):
            # 檢查是否是 import 語句
            if re.match(r'^\s*(from\s+\S+\s+)?import\s+', line):
                if self._is_import_unused(line, used_names):
                    import_lines_to_remove.add(i)
        
        # 保留有用的行
        for i, line in enumerate(lines):
            if i not in import_lines_to_remove:
                new_lines.append(line)
        
        return '\n'.join(new_lines)

    def _get_used_names(self, tree: ast.AST) -> Set[str]:
        """從 AST 中提取所有使用的名稱"""
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # 對於 a.b.c，我們只關心 'a'
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        return used_names

    def _is_import_unused(self, import_line: str, used_names: Set[str]) -> bool:
        """檢查 import 語句是否未被使用"""
        # 簡化的檢查邏輯
        # 對於複雜的 import 語句，保守處理
        
        # 跳過相對導入和複雜的 from import
        if 'from .' in import_line or '*' in import_line:
            return False
        
        # 提取導入的名稱
        if ' as ' in import_line:
            # import x as y 或 from x import y as z
            parts = import_line.split(' as ')
            if len(parts) == 2:
                imported_name = parts[1].strip().split(',')[0].strip()
                return imported_name not in used_names
        
        # 簡單的 import 語句
        if import_line.strip().startswith('import '):
            imported = import_line.replace('import ', '').strip()
            if '.' in imported:
                imported = imported.split('.')[0]
            return imported not in used_names
        
        # from x import y
        if 'from ' in import_line and ' import ' in import_line:
            import_part = import_line.split(' import ')[1]
            imports = [name.strip() for name in import_part.split(',')]
            
            # 檢查是否所有導入都未使用
            all_unused = True
            for imp in imports:
                if ' as ' in imp:
                    name = imp.split(' as ')[1].strip()
                else:
                    name = imp.strip()
                if name in used_names:
                    all_unused = False
                    break
            
            return all_unused
        
        return False

    def fix_fstring_placeholders(self, content: str) -> str:
        """修復 f-string 缺少佔位符的問題"""
        # 找到沒有 {} 的 f-string
        pattern = r'f["\']([^"\']*?)["\']'
        
        def replace_fstring(match):
            string_content = match.group(1)
            # 如果沒有 {} 佔位符，移除 f 前綴
            if '{' not in string_content and '}' not in string_content:
                return f'"{string_content}"' if match.group(0).startswith('f"') else f"'{string_content}'"
            return match.group(0)
        
        return re.sub(pattern, replace_fstring, content)

    def fix_whitespace_issues(self, content: str) -> str:
        """修復空白行和尾隨空格問題"""
        lines = content.split('\n')
        
        # 移除尾隨空格
        lines = [line.rstrip() for line in lines]
        
        # 移除空白行中的空格（但保留空行）
        for i, line in enumerate(lines):
            if line.strip() == '':
                lines[i] = ''
        
        return '\n'.join(lines)

    def fix_bare_except(self, content: str) -> str:
        """修復裸露的 except 語句"""
        # 將 except: 替換為 except Exception:
        content = re.sub(r'(\s+)except:\s*$', r'\1except Exception:', content, flags=re.MULTILINE)
        return content

    def fix_undefined_names(self, content: str) -> str:
        """修復未定義的名稱"""
        # 為常見的未定義名稱添加導入
        fixes = {
            'AsyncMock': 'from unittest.mock import AsyncMock',
            'Any': 'from typing import Any',
        }
        
        lines = content.split('\n')
        imports_added = set()
        
        # 檢查需要添加的導入
        for name, import_stmt in fixes.items():
            if name in content and import_stmt not in content:
                # 找到適當的位置插入導入
                for i, line in enumerate(lines):
                    if line.startswith('from ') or line.startswith('import '):
                        continue
                    elif line.strip() == '' or line.startswith('#'):
                        continue
                    else:
                        # 在第一個非導入行前插入
                        if import_stmt not in imports_added:
                            lines.insert(i, import_stmt)
                            imports_added.add(import_stmt)
                        break
        
        return '\n'.join(lines)

    def process_directory(self, directory: str):
        """處理目錄中的所有 Python 檔案"""
        python_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        print(f"找到 {len(python_files)} 個 Python 檔案")
        
        for file_path in python_files:
            self.fix_file(file_path)
        
        print(f"\n🎉 完成！共修復了 {self.changes_made} 個檔案")


def main():
    fixer = FlakeFixer()
    
    # 處理 src/ 和 scripts/ 目錄
    directories = ['src', 'scripts']
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"\n🔧 處理目錄: {directory}")
            fixer.process_directory(directory)
        else:
            print(f"⚠️  目錄不存在: {directory}")


if __name__ == "__main__":
    main()