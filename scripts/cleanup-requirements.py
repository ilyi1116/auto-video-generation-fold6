#!/usr/bin/env python3
"""
清理重複的 requirements.txt 文件
系統已統一到 pyproject.toml，這些 requirements.txt 文件不再需要
"""

import os
import shutil
from pathlib import Path
from typing import List, Set


class RequirementsCleanup:
    """Requirements 文件清理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.files_to_remove: List[Path] = []
        self.protected_files: Set[str] = {
            # 保護新結構中的文件（如果存在）
            "src/services/*/requirements*.txt",
            # 保護遺留和備份目錄
            "legacy/*/requirements*.txt", 
            "backup_*/requirements*.txt"
        }
        
    def find_requirements_files(self) -> List[Path]:
        """查找所有 requirements.txt 文件"""
        requirements_files = []
        
        # 查找所有 requirements*.txt 文件
        for requirements_file in self.project_root.rglob("requirements*.txt"):
            requirements_files.append(requirements_file)
            
        return requirements_files
    
    def categorize_files(self, files: List[Path]) -> dict:
        """分類文件：需要移除的、需要保護的、需要檢查的"""
        categories = {
            "remove": [],  # 舊結構中的文件，可以安全移除
            "protect": [], # 新結構、遺留、備份中的文件，需要保護
            "review": []   # 需要手動檢查的文件
        }
        
        for file_path in files:
            relative_path = file_path.relative_to(self.project_root)
            path_str = str(relative_path)
            
            # 保護遺留和備份目錄
            if any(pattern in path_str for pattern in ["legacy/", "backup_", "src/services/"]):
                categories["protect"].append(file_path)
            # 舊 services/ 結構 - 可以移除
            elif path_str.startswith("services/"):
                categories["remove"].append(file_path)
            # 舊 backend/ 結構 - 可以移除  
            elif path_str.startswith("backend/"):
                categories["remove"].append(file_path)
            # 舊專案根目錄結構 - 可以移除
            elif any(pattern in path_str for pattern in ["auto_generate_video_fold", ".old/"]):
                categories["remove"].append(file_path)
            # 基礎設施監控文件 - 可以移除（已統一到 pyproject.toml）
            elif path_str.startswith("infra/monitoring/"):
                categories["remove"].append(file_path)
            # scripts 目錄下的 requirements.txt - 可以移除
            elif path_str == "scripts/requirements.txt":
                categories["remove"].append(file_path)
            # 其他文件需要檢查
            else:
                categories["review"].append(file_path)
                
        return categories
    
    def preview_cleanup(self):
        """預覽清理操作"""
        print("🔍 掃描 requirements.txt 文件...")
        
        all_files = self.find_requirements_files()
        categories = self.categorize_files(all_files)
        
        print(f"\n📊 發現 {len(all_files)} 個 requirements 文件:")
        print(f"   🗑️  可安全移除: {len(categories['remove'])} 個")
        print(f"   🛡️  受保護: {len(categories['protect'])} 個")
        print(f"   🔍 需要檢查: {len(categories['review'])} 個")
        
        if categories["remove"]:
            print("\n🗑️ 將要移除的文件:")
            for file_path in categories["remove"]:
                print(f"   - {file_path.relative_to(self.project_root)}")
        
        if categories["protect"]:
            print("\n🛡️ 受保護的文件:")
            for file_path in categories["protect"][:10]:  # 只顯示前10個
                print(f"   - {file_path.relative_to(self.project_root)}")
            if len(categories["protect"]) > 10:
                print(f"   ... 還有 {len(categories['protect']) - 10} 個文件")
        
        if categories["review"]:
            print("\n🔍 需要手動檢查的文件:")
            for file_path in categories["review"]:
                print(f"   - {file_path.relative_to(self.project_root)}")
                
        return categories
    
    def safe_remove_file(self, file_path: Path) -> bool:
        """安全移除文件"""
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"   ❌ 移除失败 {file_path}: {e}")
            return False
    
    def execute_cleanup(self, categories: dict, confirm: bool = False):
        """執行清理操作"""
        if not confirm:
            print("\n⚠️  這是預覽模式。要執行清理，請使用 --confirm 參數")
            return
            
        print("\n🧹 開始清理 requirements.txt 文件...")
        
        removed_count = 0
        failed_count = 0
        
        for file_path in categories["remove"]:
            if self.safe_remove_file(file_path):
                print(f"   ✅ 已移除: {file_path.relative_to(self.project_root)}")
                removed_count += 1
            else:
                failed_count += 1
        
        print(f"\n📊 清理完成:")
        print(f"   ✅ 成功移除: {removed_count} 個文件")
        if failed_count > 0:
            print(f"   ❌ 移除失败: {failed_count} 個文件")
        
        # 清理空目錄
        self.cleanup_empty_directories()
        
        print(f"\n🎉 Requirements 文件清理完成！")
        print(f"系統現在統一使用 pyproject.toml 管理依賴。")
    
    def cleanup_empty_directories(self):
        """清理空目錄"""
        print("\n🧹 清理空目錄...")
        
        directories_to_check = [
            self.project_root / "services",
            self.project_root / "backend"
        ]
        
        for dir_path in directories_to_check:
            if dir_path.exists() and dir_path.is_dir():
                try:
                    # 檢查目錄是否為空
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        print(f"   ✅ 已移除空目錄: {dir_path.relative_to(self.project_root)}")
                except OSError:
                    # 目錄不為空，跳過
                    pass


def main():
    import sys
    
    cleanup = RequirementsCleanup()
    
    # 預覽清理操作
    categories = cleanup.preview_cleanup()
    
    # 檢查是否有確認參數
    confirm = "--confirm" in sys.argv
    
    # 執行清理
    cleanup.execute_cleanup(categories, confirm=confirm)
    
    if not confirm:
        print(f"\n💡 如果確認要執行清理，請運行:")
        print(f"   python scripts/cleanup-requirements.py --confirm")


if __name__ == "__main__":
    main()