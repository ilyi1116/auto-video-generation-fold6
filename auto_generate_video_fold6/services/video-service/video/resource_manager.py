"""
資源管理器

TDD Green 階段：最小實作讓測試通過
"""

import os
import tempfile


class ResourceManager:
    """資源管理器 - 最小實作"""

    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.initial_file_count = self.count_temporary_files()

    def count_temporary_files(self) -> int:
        """計算臨時檔案數量 - 最小實作"""
        try:
            temp_files = [
                f
                for f in os.listdir(self.temp_dir)
                if f.startswith("video_")
                or f.startswith("audio_")
                or f.startswith("image_")
            ]
            return len(temp_files)
        except (OSError, PermissionError):
            return 0

    def get_memory_usage(self) -> float:
        """取得記憶體使用量 - 最小實作"""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            # 如果沒有 psutil，返回模擬值
            return 50.0  # MB

    def cleanup_temp_files(self, workflow_id: str) -> int:
        """清理臨時檔案 - 最小實作"""
        cleaned_count = 0
        try:
            for filename in os.listdir(self.temp_dir):
                if workflow_id in filename:
                    file_path = os.path.join(self.temp_dir, filename)
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                    except OSError:
                        pass
        except (OSError, PermissionError):
            pass

        return cleaned_count
