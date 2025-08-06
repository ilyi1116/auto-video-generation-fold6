#!/usr/bin/env python3
"""
修復剩餘語法錯誤的腳本
"""

import os
import re
from pathlib import Path


def fix_syntax_errors():
    """修復特定的語法錯誤"""
    
    fixes = [
        # 修復縮排錯誤 - 將錯誤的縮排移到頂層
        {
            'file': 'scripts/auto_trends_video.py',
            'line': 24,
            'fix': lambda content: content.replace('\t\tpass', '    pass')
        },
        
        # 修復其他文件的類似問題...
    ]
    
    # 通用修復規則
    files_to_fix = [
        'scripts/auto_trends_video.py',
        'scripts/logging/logging-integration-example.py',
        'scripts/optimization/frontend-performance-optimizer.py',
        'scripts/run-comprehensive-optimization.py',
        'scripts/service-communication-example.py',
        'scripts/test-phase2-system.py',
        'src/services/ai-service/ai_orchestrator.py',
        'src/services/api-gateway/app/proxy.py',
        'src/services/api-gateway/app/routers.py',
        'src/services/auth-service/app/models.py',
        'src/services/common/workflow_engine_refactored.py',
        'src/services/data-service/app/database.py',
        'src/services/data-service/app/routers/process.py',
        'src/services/inference-service/app/database.py',
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 修復常見的語法錯誤
                content = fix_common_syntax_issues(content)
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ 修復: {file_path}")
                    
            except Exception as e:
                print(f"❌ 錯誤修復 {file_path}: {e}")


def fix_common_syntax_issues(content: str) -> str:
    """修復常見的語法問題"""
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        original_line = line
        
        # 修復未終止的字符串（簡單情況）
        if line.count('"') % 2 == 1 and not line.strip().endswith('\\'):
            if '"' in line and not line.rstrip().endswith('"'):
                line = line.rstrip() + '"'
        
        if line.count("'") % 2 == 1 and not line.strip().endswith('\\'):
            if "'" in line and not line.rstrip().endswith("'"):
                line = line.rstrip() + "'"
        
        # 修復錯誤的引號組合
        line = re.sub(r'"\'([^\']*?)\'', r'"\1"', line)  # 修復 "'text'" 為 "text"
        line = re.sub(r'\'"([^"]*?)"\'', r'"\1"', line)  # 修復 '"text"' 為 "text"
        
        # 修復縮排問題
        if line.strip() and not line.startswith('#'):
            # 如果行開始有奇怪的縮排，嘗試修復
            if re.match(r'^[ \t]+[a-zA-Z_]', line):
                # 檢查是否是 import 語句
                if 'import ' in line or 'from ' in line:
                    line = line.lstrip()  # import 語句移到頂層
                else:
                    # 標準化縮排為 4 的倍數
                    stripped = line.lstrip()
                    indent_level = (len(line) - len(stripped) + 3) // 4
                    line = '    ' * indent_level + stripped
        
        # 修復語法錯誤
        line = fix_specific_syntax_errors(line, i + 1)
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)


def fix_specific_syntax_errors(line: str, line_num: int) -> str:
    """修復特定的語法錯誤"""
    
    # 修復逗號相關的語法錯誤
    line = re.sub(r'(\w+)\'([^\']*?)\'(\w+)', r'\1"\2"\3', line)
    
    # 修復 f-string 中的引號問題
    line = re.sub(r'f"([^"]*?)="{([^}]*?)}\', r'f"\1={{\2}}"', line)
    
    # 修復其他常見的語法錯誤
    if 'try:' in line and line.strip() == 'try:':
        # 確保 try 後面有縮排的內容
        pass
    
    return line


if __name__ == "__main__":
    print("🔧 修復剩餘的語法錯誤...")
    fix_syntax_errors()
    print("✅ 完成語法錯誤修復")