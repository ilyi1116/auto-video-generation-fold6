#!/usr/bin/env python3
"""
修復語法錯誤的腳本
"""

import os
import re
from pathlib import Path


class SyntaxErrorFixer:
    def __init__(self):
        self.changes_made = 0

    def fix_file(self, file_path: str) -> bool:
        """修復單個檔案中的語法錯誤"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 修復各種語法錯誤
            content = self.fix_unterminated_strings(content)
            content = self.fix_indentation_errors(content)
            content = self.fix_import_issues(content)
            
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

    def fix_unterminated_strings(self, content: str) -> str:
        """修復未終止的字符串"""
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            # 檢查是否有未終止的字符串
            if line.count('"') % 2 == 1 and not line.strip().endswith('\\'):
                # 簡單的修復：在行末添加結束引號
                if '"' in line and not line.strip().endswith('"'):
                    line = line.rstrip() + '"'
            
            if line.count("'") % 2 == 1 and not line.strip().endswith('\\'):
                # 簡單的修復：在行末添加結束引號
                if "'" in line and not line.strip().endswith("'"):
                    line = line.rstrip() + "'"
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)

    def fix_indentation_errors(self, content: str) -> str:
        """修復縮排錯誤"""
        lines = content.split('\n')
        new_lines = []
        expected_indent = 0
        
        for i, line in enumerate(lines):
            if not line.strip():
                new_lines.append('')
                continue
            
            # 檢查是否是 import 或 from 語句
            if line.strip().startswith(('import ', 'from ')):
                # import 語句應該在頂層
                new_lines.append(line.lstrip())
                continue
            
            # 檢查是否是類或函數定義
            if line.strip().startswith(('class ', 'def ', 'async def ')):
                expected_indent = 0
                new_lines.append(line.lstrip())
                continue
            
            # 檢查是否是註釋
            if line.strip().startswith('#'):
                new_lines.append(line)
                continue
            
            # 對於其他行，保持原有縮排或修復明顯錯誤
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            
            # 如果縮排看起來不對，嘗試修復
            if current_indent % 4 != 0 and current_indent > 0:
                # 調整到最近的 4 的倍數
                new_indent = (current_indent + 3) // 4 * 4
                line = ' ' * new_indent + stripped
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)

    def fix_import_issues(self, content: str) -> str:
        """修復導入相關的問題"""
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            # 修復錯誤的縮排導入
            if re.match(r'^\s+(import |from )', line):
                # 將導入移到頂層
                line = line.lstrip()
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)

    def process_files_with_errors(self):
        """處理有語法錯誤的特定檔案"""
        error_files = [
            'scripts/auto_trends_video.py',
            'scripts/optimization/frontend-performance-optimizer.py',
            'scripts/run-comprehensive-optimization.py',
            'scripts/logging/logging-integration-example.py',
            'scripts/service-communication-example.py',
            'scripts/test-phase2-system.py',
            'src/services/ai-service/ai_orchestrator.py',
            'src/services/api-gateway/app/config.py',
            'src/services/api-gateway/app/proxy.py',
            'src/services/api-gateway/app/routers.py',
            'src/services/auth-service/app/models.py',
            'src/services/common/workflow_engine_refactored.py',
            'src/services/data-service/app/database.py',
            'src/services/data-service/app/routers/process.py',
            'src/services/inference-service/app/database.py',
            'src/services/scheduler-service/test_refactored_scheduler.py',
            'src/services/scheduler-service/test_scheduler_simple.py',
            'src/services/scheduler-service/tests/test_entrepreneur_scheduler_tdd.py',
            'src/services/scheduler-service/tests/test_scheduler.py',
            'src/services/storage-service/app/models.py',
            'src/services/storage-service/app/routers/download.py',
            'src/services/storage-service/tests/test_processors.py',
            'src/services/trend-service/app/services/keyword_analyzer.py',
            'src/services/trend-service/main.py',
            'src/services/video-service/ai/gemini_client.py',
            'src/services/video-service/short_video_generator.py',
            'src/services/video-service/test_docker_validation.py',
            'src/services/video-service/test_green_with_refactored.py',
            'src/services/video-service/test_tdd_refactor.py',
            'src/services/video-service/tests/test_video_generation.py',
            'src/services/video-service/tests/test_video_service.py',
            'src/services/voice-enhancement/app/routers/cloning.py',
            'src/services/voice-enhancement/app/services/voice_cloner.py',
        ]
        
        for file_path in error_files:
            if os.path.exists(file_path):
                print(f"🔧 處理: {file_path}")
                self.fix_file(file_path)
            else:
                print(f"⚠️  檔案不存在: {file_path}")
        
        print(f"\n🎉 完成！共修復了 {self.changes_made} 個檔案")


def main():
    fixer = SyntaxErrorFixer()
    fixer.process_files_with_errors()


if __name__ == "__main__":
    main()