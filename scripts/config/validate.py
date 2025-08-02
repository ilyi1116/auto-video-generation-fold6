#!/usr/bin/env python3
"""
配置驗證腳本
"""
import os
from dotenv import load_dotenv


def validate_config():
    """驗證配置文件"""
    # 加載環境變量
    load_dotenv()

    required_vars = ["DATABASE_URL", "JWT_SECRET_KEY"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        return False

    print("✅ Configuration validation passed!")
    return True


if __name__ == "__main__":
    validate_config()
