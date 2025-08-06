"""
配置管理系統
提供集中化的配置管理、熱更新和版本控制功能
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import aiofiles
import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """配置文件格式"""

    JSON = "json"
    YAML = "yaml"
    ENV = "env"


class ConfigScope(Enum):
    """配置作用域"""

    GLOBAL = "global"  # 全局配置
    SERVICE = "service"  # 服務配置
    FEATURE = "feature"  # 功能配置
    USER = "user"  # 用戶配置


@dataclass
class ConfigMetadata:
    """配置元數據"""

    name: str
    scope: ConfigScope
    format: ConfigFormat
    version: str
    last_modified: datetime
    checksum: str
    description: str = ""
    encrypted: bool = False
    requires_restart: bool = False


@dataclass
class ConfigChange:
    """配置變更記錄"""

    config_name: str
    old_value: Any
    new_value: Any
    changed_by: str
    timestamp: datetime
    change_type: str  # create, update, delete


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件監控處理器"""

    def __init__(self, config_manager):
        self.config_manager = config_manager

    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(self.config_manager._handle_file_change(event.src_path))


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = "/data/data/com.termux/files/home/myProject/config"):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目錄
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 配置緩存
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, ConfigMetadata] = {}
        self._change_listeners: Dict[str, List[Callable]] = {}
        self._change_history: List[ConfigChange] = []

        # 文件監控
        self._observer = Observer()
        self._file_handler = ConfigFileHandler(self)

        # 加密密鑰（應該從環境變數或密鑰管理服務獲取）
        self._encryption_key = os.getenv(
            "CONFIG_ENCRYPTION_KEY", "default-key-change-in-production"
        )

        # 啟動文件監控
        self._start_file_monitoring()

        # 載入所有配置
        asyncio.create_task(self._load_all_configs())

    def _start_file_monitoring(self):
        """啟動文件監控"""
        try:
            self._observer.schedule(self._file_handler, str(self.config_dir), recursive=True)
            self._observer.start()
            logger.info("配置文件監控已啟動")
        except Exception as e:
            logger.error(f"啟動文件監控失敗: {e}")

    def _calculate_checksum(self, content: str) -> str:
        """計算配置內容的校驗和"""
        return hashlib.sha256(content.encode()).hexdigest()

    def _encrypt_content(self, content: str) -> str:
        """加密配置內容"""
        # 簡單的加密實現，生產環境應使用更安全的加密方法
        import base64

        from cryptography.fernet import Fernet

        # 生成密鑰
        key = base64.urlsafe_b64encode(self._encryption_key.ljust(32)[:32].encode())
        fernet = Fernet(key)

        return fernet.encrypt(content.encode()).decode()

    def _decrypt_content(self, encrypted_content: str) -> str:
        """解密配置內容"""
        import base64

        from cryptography.fernet import Fernet

        try:
            key = base64.urlsafe_b64encode(self._encryption_key.ljust(32)[:32].encode())
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_content.encode()).decode()
        except Exception as e:
            logger.error(f"解密配置失敗: {e}")
            raise

    def _parse_config_content(self, content: str, format: ConfigFormat) -> Dict[str, Any]:
        """解析配置內容"""
        try:
            if format == ConfigFormat.JSON:
                return json.loads(content)
            elif format == ConfigFormat.YAML:
                return yaml.safe_load(content) or {}
            elif format == ConfigFormat.ENV:
                # 簡單的 .env 解析
                config = {}
                for line in content.strip().split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip().strip("\"'")
                return config
            else:
                raise ValueError(f"不支持的配置格式: {format}")
        except Exception as e:
            logger.error(f"解析配置內容失敗: {e}")
            raise

    def _serialize_config_content(self, config: Dict[str, Any], format: ConfigFormat) -> str:
        """序列化配置內容"""
        try:
            if format == ConfigFormat.JSON:
                return json.dumps(config, indent=2, ensure_ascii=False)
            elif format == ConfigFormat.YAML:
                return yaml.dump(config, default_flow_style=False, allow_unicode=True)
            elif format == ConfigFormat.ENV:
                lines = []
                for key, value in config.items():
                    # 處理特殊字符
                    if isinstance(value, str) and (" " in value or '"' in value):
                        value = f'"{value}"'
                    lines.append(f"{key}={value}")
                return "\n".join(lines)
            else:
                raise ValueError(f"不支持的配置格式: {format}")
        except Exception as e:
            logger.error(f"序列化配置內容失敗: {e}")
            raise

    async def _load_all_configs(self):
        """載入所有配置文件"""
        try:
            for file_path in self.config_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix in [".json", ".yaml", ".yml", ".env"]:
                    await self._load_config_file(file_path)
            logger.info(f"已載入 {len(self._configs)} 個配置文件")
        except Exception as e:
            logger.error(f"載入配置文件失敗: {e}")

    async def _load_config_file(self, file_path: Path):
        """載入單個配置文件"""
        try:
            config_name = self._get_config_name(file_path)

            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # 檢查是否為加密文件
            is_encrypted = file_path.name.endswith(".encrypted")
            if is_encrypted:
                content = self._decrypt_content(content)

            # 確定文件格式
            if file_path.suffix in [".yaml", ".yml"]:
                format = ConfigFormat.YAML
            elif file_path.suffix == ".json":
                format = ConfigFormat.JSON
            elif file_path.suffix == ".env":
                format = ConfigFormat.ENV
            else:
                format = ConfigFormat.JSON  # 默認

            # 解析配置
            config_data = self._parse_config_content(content, format)

            # 創建元數據
            stat = file_path.stat()
            metadata = ConfigMetadata(
                name=config_name,
                scope=self._determine_scope(file_path),
                format=format,
                version="1.0.0",  # 可以從配置中讀取
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                checksum=self._calculate_checksum(content),
                encrypted=is_encrypted,
            )

            # 存儲配置和元數據
            self._configs[config_name] = config_data
            self._metadata[config_name] = metadata

            logger.debug(f"已載入配置: {config_name}")

        except Exception as e:
            logger.error(f"載入配置文件 {file_path} 失敗: {e}")

    def _get_config_name(self, file_path: Path) -> str:
        """獲取配置名稱"""
        # 移除加密後綴
        name = file_path.name
        if name.endswith(".encrypted"):
            name = name[:-10]  # 移除 .encrypted

        # 移除文件擴展名
        return Path(name).stem

    def _determine_scope(self, file_path: Path) -> ConfigScope:
        """確定配置作用域"""
        relative_path = file_path.relative_to(self.config_dir)

        if "global" in str(relative_path):
            return ConfigScope.GLOBAL
        elif "service" in str(relative_path):
            return ConfigScope.SERVICE
        elif "feature" in str(relative_path):
            return ConfigScope.FEATURE
        elif "user" in str(relative_path):
            return ConfigScope.USER
        else:
            return ConfigScope.GLOBAL

    async def _handle_file_change(self, file_path: str):
        """處理文件變更"""
        try:
            path = Path(file_path)
            if path.is_file() and path.suffix in [".json", ".yaml", ".yml", ".env"]:
                config_name = self._get_config_name(path)

                # 重新載入配置
                old_config = self._configs.get(config_name, {}).copy()
                await self._load_config_file(path)
                new_config = self._configs.get(config_name, {})

                # 記錄變更
                if old_config != new_config:
                    change = ConfigChange(
                        config_name=config_name,
                        old_value=old_config,
                        new_value=new_config,
                        changed_by="file_watcher",
                        timestamp=datetime.utcnow(),
                        change_type="update",
                    )
                    self._change_history.append(change)

                    # 通知監聽器
                    await self._notify_listeners(config_name, old_config, new_config)

                    logger.info(f"配置 {config_name} 已熱更新")
        except Exception as e:
            logger.error(f"處理文件變更失敗: {e}")

    async def _notify_listeners(self, config_name: str, old_value: Any, new_value: Any):
        """通知配置變更監聽器"""
        listeners = self._change_listeners.get(config_name, [])
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(config_name, old_value, new_value)
                else:
                    listener(config_name, old_value, new_value)
            except Exception as e:
                logger.error(f"配置變更監聽器執行失敗: {e}")

    async def get_config(self, name: str, default: Any = None) -> Any:
        """獲取配置"""
        return self._configs.get(name, default)

    async def get_config_value(self, config_name: str, key_path: str, default: Any = None) -> Any:
        """
        獲取配置中的特定值

        Args:
            config_name: 配置名稱
            key_path: 鍵路徑，支持點號分隔，如 'database.host'
            default: 默認值
        """
        config = self._configs.get(config_name)
        if not config:
            return default

        # 支持點號分隔的鍵路徑
        keys = key_path.split(".")
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    async def set_config(
        self,
        name: str,
        config: Dict[str, Any],
        scope: ConfigScope = ConfigScope.GLOBAL,
        format: ConfigFormat = ConfigFormat.JSON,
        encrypt: bool = False,
        changed_by: str = "system",
    ) -> bool:
        """
        設置配置

        Args:
            name: 配置名稱
            config: 配置內容
            scope: 配置作用域
            format: 配置格式
            encrypt: 是否加密
            changed_by: 變更者
        """
        try:
            old_config = self._configs.get(name, {}).copy()

            # 更新配置緩存
            self._configs[name] = config

            # 創建或更新元數據
            metadata = ConfigMetadata(
                name=name,
                scope=scope,
                format=format,
                version="1.0.0",
                last_modified=datetime.utcnow(),
                checksum=self._calculate_checksum(json.dumps(config)),
                encrypted=encrypt,
            )
            self._metadata[name] = metadata

            # 保存到文件
            await self._save_config_to_file(name, config, metadata)

            # 記錄變更
            change = ConfigChange(
                config_name=name,
                old_value=old_config,
                new_value=config,
                changed_by=changed_by,
                timestamp=datetime.utcnow(),
                change_type="update" if old_config else "create",
            )
            self._change_history.append(change)

            # 通知監聽器
            await self._notify_listeners(name, old_config, config)

            logger.info(f"配置 {name} 已更新")
            return True

        except Exception as e:
            logger.error(f"設置配置 {name} 失敗: {e}")
            return False

    async def _save_config_to_file(
        self, name: str, config: Dict[str, Any], metadata: ConfigMetadata
    ):
        """保存配置到文件"""
        try:
            # 確定文件路徑
            scope_dir = self.config_dir / metadata.scope.value
            scope_dir.mkdir(exist_ok=True)

            # 確定文件名和擴展名
            if metadata.format == ConfigFormat.JSON:
                ext = ".json"
            elif metadata.format == ConfigFormat.YAML:
                ext = ".yaml"
            elif metadata.format == ConfigFormat.ENV:
                ext = ".env"
            else:
                ext = ".json"

            if metadata.encrypted:
                ext += ".encrypted"

            file_path = scope_dir / f"{name}{ext}"

            # 序列化配置
            content = self._serialize_config_content(config, metadata.format)

            # 加密（如果需要）
            if metadata.encrypted:
                content = self._encrypt_content(content)

            # 寫入文件
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

            logger.debug(f"配置已保存到: {file_path}")

        except Exception as e:
            logger.error(f"保存配置文件失敗: {e}")
            raise

    async def delete_config(self, name: str, changed_by: str = "system") -> bool:
        """刪除配置"""
        try:
            if name not in self._configs:
                return False

            old_config = self._configs[name].copy()

            # 從緩存中移除
            del self._configs[name]
            metadata = self._metadata.get(name)
            if metadata:
                del self._metadata[name]

            # 刪除文件
            if metadata:
                scope_dir = self.config_dir / metadata.scope.value
                file_pattern = f"{name}.*"
                for file_path in scope_dir.glob(file_pattern):
                    file_path.unlink()

            # 記錄變更
            change = ConfigChange(
                config_name=name,
                old_value=old_config,
                new_value=None,
                changed_by=changed_by,
                timestamp=datetime.utcnow(),
                change_type="delete",
            )
            self._change_history.append(change)

            # 通知監聽器
            await self._notify_listeners(name, old_config, None)

            logger.info(f"配置 {name} 已刪除")
            return True

        except Exception as e:
            logger.error(f"刪除配置 {name} 失敗: {e}")
            return False

    def add_change_listener(self, config_name: str, listener: Callable):
        """添加配置變更監聽器"""
        if config_name not in self._change_listeners:
            self._change_listeners[config_name] = []
        self._change_listeners[config_name].append(listener)

    def remove_change_listener(self, config_name: str, listener: Callable):
        """移除配置變更監聽器"""
        if config_name in self._change_listeners:
            try:
                self._change_listeners[config_name].remove(listener)
            except ValueError:
                pass

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有配置"""
        return self._configs.copy()

    def get_config_metadata(self, name: str) -> Optional[ConfigMetadata]:
        """獲取配置元數據"""
        return self._metadata.get(name)

    def get_all_metadata(self) -> Dict[str, ConfigMetadata]:
        """獲取所有配置元數據"""
        return self._metadata.copy()

    def get_change_history(
        self, config_name: Optional[str] = None, limit: int = 100
    ) -> List[ConfigChange]:
        """獲取配置變更歷史"""
        history = self._change_history

        if config_name:
            history = [change for change in history if change.config_name == config_name]

        # 返回最近的變更
        return sorted(history, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def reload_config(self, name: str) -> bool:
        """重新載入配置"""
        try:
            # 查找配置文件
            for file_path in self.config_dir.rglob(f"{name}.*"):
                if file_path.is_file():
                    await self._load_config_file(file_path)
                    return True
            return False
        except Exception as e:
            logger.error(f"重新載入配置 {name} 失敗: {e}")
            return False

    async def validate_config(self, name: str, schema: Dict[str, Any]) -> List[str]:
        """
        驗證配置

        Args:
            name: 配置名稱
            schema: 配置模式

        Returns:
            驗證錯誤列表
        """
        errors = []
        config = self._configs.get(name)

        if not config:
            errors.append(f"配置 {name} 不存在")
            return errors

        # 簡單的模式驗證
        try:
            self._validate_against_schema(config, schema, "")
        except ValueError as e:
            errors.append(str(e))

        return errors

    def _validate_against_schema(self, data: Any, schema: Dict[str, Any], path: str):
        """根據模式驗證數據"""
        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "string" and not isinstance(data, str):
                raise ValueError(f"{path}: 期望字符串，得到 {type(data).__name__}")
            elif expected_type == "number" and not isinstance(data, (int, float)):
                raise ValueError(f"{path}: 期望數字，得到 {type(data).__name__}")
            elif expected_type == "boolean" and not isinstance(data, bool):
                raise ValueError(f"{path}: 期望布爾值，得到 {type(data).__name__}")
            elif expected_type == "object" and not isinstance(data, dict):
                raise ValueError(f"{path}: 期望對象，得到 {type(data).__name__}")

        if "required" in schema and isinstance(data, dict):
            for required_field in schema["required"]:
                if required_field not in data:
                    raise ValueError(f"{path}: 缺少必需字段 {required_field}")

        if "properties" in schema and isinstance(data, dict):
            for key, value in data.items():
                if key in schema["properties"]:
                    self._validate_against_schema(
                        value, schema["properties"][key], f"{path}.{key}" if path else key
                    )

    def stop(self):
        """停止配置管理器"""
        try:
            self._observer.stop()
            self._observer.join()
            logger.info("配置管理器已停止")
        except Exception as e:
            logger.error(f"停止配置管理器失敗: {e}")


# 全局配置管理器實例
config_manager = ConfigManager()


# 配置裝飾器
def config_value(config_name: str, key_path: str, default: Any = None):
    """配置值裝飾器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 獲取配置值並注入到函數中
            value = await config_manager.get_config_value(config_name, key_path, default)
            kwargs["config_value"] = value
            return (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

        return wrapper

    return decorator
