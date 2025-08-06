import logging
import sys
from pathlib import Path


def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """設置日誌記錄器"""

    # 創建日誌目錄
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 創建格式化器
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 創建記錄器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重複添加處理器
    if logger.handlers:
        return logger

    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件處理器
    if log_file:
        file_handler = logging.FileHandler(log_dir / log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 創建默認記錄器
logger = setup_logger("auto_video_system")
