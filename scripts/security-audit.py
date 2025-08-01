#!/usr/bin/env python3
"""
安全性審計腳本
檢查專案中的敏感資訊洩露風險
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class SecurityAuditor:
    """安全性審計工具"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.sensitive_patterns = {
            'api_key': [
                r'api[_-]?key["\s]*[:=]["\s]*[a-zA-Z0-9_-]{10,}',
                r'apikey["\s]*[:=]["\s]*[a-zA-Z0-9_-]{10,}',
                r'key["\s]*[:=]["\s]*[a-zA-Z0-9_-]{20,}',
            ],
            'password': [
                r'password["\s]*[:=]["\s]*[^"\s]{5,}',
                r'passwd["\s]*[:=]["\s]*[^"\s]{5,}',
                r'pwd["\s]*[:=]["\s]*[^"\s]{5,}',
            ],
            'secret': [
                r'secret["\s]*[:=]["\s]*[a-zA-Z0-9_-]{10,}',
                r'private[_-]?key["\s]*[:=]["\s]*[a-zA-Z0-9_-]{10,}',
            ],
            'token': [
                r'token["\s]*[:=]["\s]*[a-zA-Z0-9_-]{10,}',
                r'access[_-]?token["\s]*[:=]["\s]*[a-zA-Z0-9_-]{10,}',
                r'bearer["\s]*[:=]["\s]*[a-zA-Z0-9_-]{10,}',
            ],
            'database': [
                r'postgresql://[^:]+:[^@]+@[^/]+/\w+',
                r'mysql://[^:]+:[^@]+@[^/]+/\w+',
                r'mongodb://[^:]+:[^@]+@[^/]+/\w+',
            ]
        }
        
        # 安全的預設值模式
        self.safe_patterns = {
            'example', 'test', 'demo', 'sample', 'placeholder',
            'your-', 'change-this', 'replace-', 'update-',
            'password', 'secret', 'key', 'token',  # 當作為值時是安全的
            'minioadmin', 'dev_password', 'analytics_api',  # 開發環境預設值
            '${', '}',  # 環境變數占位符
        }
    
    def is_safe_value(self, value: str) -> bool:
        """檢查值是否為安全的預設值"""
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in self.safe_patterns)
    
    def scan_json_file(self, file_path: Path) -> List[Dict]:
        """掃描 JSON 檔案中的敏感資訊"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 檢查原始內容中的模式
            for category, patterns in self.sensitive_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        matched_text = match.group()
                        if not self.is_safe_value(matched_text):
                            issues.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'category': category,
                                'pattern': pattern,
                                'match': matched_text[:50] + '...' if len(matched_text) > 50 else matched_text,
                                'line': content[:match.start()].count('\n') + 1
                            })
            
            # 解析 JSON 並檢查值
            try:
                data = json.loads(content)
                self._scan_json_object(data, file_path, issues)
            except json.JSONDecodeError:
                issues.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'category': 'format',
                    'match': 'Invalid JSON format',
                    'line': -1
                })
                
        except Exception as e:
            issues.append({
                'file': str(file_path.relative_to(self.project_root)),
                'category': 'error',
                'match': f'Error reading file: {e}',
                'line': -1
            })
        
        return issues
    
    def _scan_json_object(self, obj, file_path: Path, issues: List[Dict], path: str = ""):
        """遞迴掃描 JSON 物件"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # 檢查 key 名稱是否敏感
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in ['password', 'secret', 'key', 'token']):
                    if isinstance(value, str) and len(value) > 5 and not self.is_safe_value(value):
                        # 檢查是否不是明顯的預設值
                        if not any(safe in value.lower() for safe in self.safe_patterns):
                            issues.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'category': 'sensitive_key',
                                'pattern': f'Key: {key}',
                                'match': f'{key}: {str(value)[:20]}...',
                                'path': current_path,
                                'line': -1
                            })
                
                # 遞迴檢查值
                self._scan_json_object(value, file_path, issues, current_path)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                self._scan_json_object(item, file_path, issues, current_path)
    
    def scan_env_files(self) -> List[Dict]:
        """掃描環境變數檔案"""
        issues = []
        env_files = [
            self.project_root / ".env",
            self.project_root / ".env.local", 
            self.project_root / ".env.production",
            self.project_root / ".env.development",
        ]
        
        for env_file in env_files:
            if env_file.exists():
                issues.extend(self._scan_env_file(env_file))
                
        return issues
    
    def _scan_env_file(self, file_path: Path) -> List[Dict]:
        """掃描單個環境變數檔案"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # 檢查是否為敏感的環境變數
                    if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                        if len(value) > 5 and not self.is_safe_value(value):
                            issues.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'category': 'env_sensitive',
                                'pattern': f'Env var: {key}',
                                'match': f'{key}={value[:20]}...',
                                'line': line_num
                            })
                            
        except Exception as e:
            issues.append({
                'file': str(file_path.relative_to(self.project_root)),
                'category': 'error',
                'match': f'Error reading env file: {e}',
                'line': -1
            })
            
        return issues
    
    def run_audit(self) -> Dict:
        """執行完整的安全審計"""
        print("🔒 開始安全性審計...")
        
        all_issues = []
        
        # 掃描配置 JSON 檔案
        config_dir = self.project_root / "auto_generate_video_fold6" / "config"
        if config_dir.exists():
            print(f"📋 掃描配置檔案目錄: {config_dir}")
            for json_file in config_dir.glob("*.json"):
                issues = self.scan_json_file(json_file)
                all_issues.extend(issues)
        
        # 掃描環境變數檔案
        print("🔧 掃描環境變數檔案...")
        env_issues = self.scan_env_files()
        all_issues.extend(env_issues)
        
        # 分類統計
        categories = {}
        for issue in all_issues:
            category = issue['category']
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_issues': len(all_issues),
            'issues': all_issues,
            'categories': categories,
            'files_scanned': len(set(issue['file'] for issue in all_issues))
        }


def main():
    """主函數"""
    project_root = Path(__file__).parent.parent
    auditor = SecurityAuditor(project_root)
    
    results = auditor.run_audit()
    
    print(f"\n📊 安全審計結果:")
    print(f"   掃描檔案數: {results['files_scanned']}")
    print(f"   發現問題數: {results['total_issues']}")
    
    if results['categories']:
        print("\n🏷️  問題分類:")
        for category, count in results['categories'].items():
            print(f"   {category}: {count}")
    
    if results['issues']:
        print("\n⚠️  發現的問題:")
        for issue in results['issues']:
            file_name = issue['file']
            category = issue['category']
            match = issue['match']
            line = issue.get('line', -1)
            
            if line > 0:
                print(f"   📄 {file_name}:{line} [{category}] {match}")
            else:
                print(f"   📄 {file_name} [{category}] {match}")
    else:
        print("\n✅ 未發現敏感資訊洩露問題")
    
    print("\n📋 建議:")
    print("   • 所有 API 密鑰應該透過環境變數設定")
    print("   • 配置檔案中不應包含真實的密碼或密鑰")
    print("   • 使用 .env.template 檔案提供配置範本")
    print("   • 確保 .env 檔案已加入 .gitignore")
    
    # 如果發現敏感問題，返回錯誤碼
    sensitive_categories = ['api_key', 'password', 'secret', 'token', 'sensitive_key', 'env_sensitive']
    has_sensitive_issues = any(issue['category'] in sensitive_categories for issue in results['issues'])
    
    return 0 if not has_sensitive_issues else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)