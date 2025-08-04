"""
環境配置載入器
用於根據環境變數載入對應的配置檔案
"""

import os
from pathlib import Path
from typing import Optional

def load_environment_config(env: Optional[str] = None) -> str:
    """
    載入環境特定的配置檔案
    
    Args:
        env: 環境名稱 (development, testing, production)
             如果為 None，則從 ENVIRONMENT 環境變數讀取
    
    Returns:
        配置檔案路径
    """
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    config_dir = Path(__file__).parent / 'environments'
    config_file = config_dir / f'{env}.env'
    
    if not config_file.exists():
        # 如果找不到特定環境配置，使用開發環境配置
        config_file = config_dir / 'development.env'
        print(f"Warning: {env}.env not found, using development.env")
    
    return str(config_file)

def load_dotenv_from_environment():
    """
    根據當前環境載入對應的 .env 檔案
    """
    try:
        from dotenv import load_dotenv
        config_file = load_environment_config()
        load_dotenv(config_file)
        print(f"Loaded configuration from: {config_file}")
    except ImportError:
        print("Warning: python-dotenv not installed")
    except Exception as e:
        print(f"Error loading environment config: {e}")

if __name__ == "__main__":
    # 測試配置載入
    config_file = load_environment_config()
    print(f"Current environment config: {config_file}")
