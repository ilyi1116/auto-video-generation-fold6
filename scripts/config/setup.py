#!/usr/bin/env python3
"""
配置設置腳本
"""
import os
import shutil
from pathlib import Path

def setup_config():
    """設置配置文件"""
    print("Setting up configuration...")

    # 創建必要的目錄
    directories = [
        'backend/shared/config',
        'logs',
        'data'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # 複製環境配置文件
    env_files = ['env.development', 'env.production', 'env.test']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            shutil.copy(env_file, f'.env.{env_file.split(".")[-1]}')
            print(f"✅ Copied {env_file}")

    print("✅ Configuration setup completed!")

if __name__ == "__main__":
    setup_config() 