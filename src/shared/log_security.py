"""
Security Log Filter System
安全日誌過濾系統 - 防止敏感數據洩露到日誌
"""

import json
import logging
import re
from typing import Any, Dict, List, Union


class SensitiveDataFilter:
    """過濾敏感數據的日誌過濾器"""

    # 敏感數據模式
    SENSITIVE_PATTERNS = {
        "api_key": [
            r"sk-[a-zA-Z0-9]{48,}",  # OpenAI API keys
            r"sk-proj-[a-zA-Z0-9_-]{64,}",  # OpenAI project keys
            r"AIzaSy[a-zA-Z0-9_-]{33}",  # Google API keys
            r"AKIA[0-9A-Z]{16}",  # AWS access keys
            r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}",  # SendGrid API keys
            r"[a-f0-9]{32}",  # Generic 32-char hex keys
        ],
        "password": [
            r'password["\']?\s*[:=]\s*["\']?[^"\'\s]{8,}',
            r'passwd["\']?\s*[:=]\s*["\']?[^"\'\s]{8,}',
            r'pwd["\']?\s*[:=]\s*["\']?[^"\'\s]{8,}',
        ],
        "token": [
            r'token["\']?\s*[:=]\s*["\']?[^"\'\s]{20,}',
            r'jwt["\']?\s*[:=]\s*["\']?[^"\'\s]{20,}',
            r"bearer\s+[a-zA-Z0-9_-]{20,}",
        ],
        "secret": [
            r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]{16,}',
            r'private[_-]?key["\']?\s*[:=]\s*["\']?[^"\'\s]{20,}',
        ],
        "email": [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        ],
        "credit_card": [
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
        ],
        "ssn": [
            r"\b\d{3}-\d{2}-\d{4}\b",
            r"\b\d{9}\b",
        ],
    }

    def __init__(self, mask_char: str = "*", preserve_length: bool = True):
        self.mask_char = mask_char
        self.preserve_length = preserve_length
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """編譯正則表達式模式"""
        compiled = {}
        for category, patterns in self.SENSITIVE_PATTERNS.items():
            compiled[category] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        return compiled

    def mask_sensitive_data(self, text: str) -> str:
        """遮罩敏感數據"""
        if not isinstance(text, str):
            text = str(text)

        masked_text = text

        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(masked_text)
                for match in reversed(list(matches)):
                    start, end = match.span()
                    matched_text = match.group()

                    # 根據類型決定遮罩策略
                    if category == "email":
                        # Email 保留部分信息
                        masked_value = self._mask_email(matched_text)
                    elif category == "api_key":
                        # API 密鑰保留前綴
                        masked_value = self._mask_api_key(matched_text)
                    else:
                        # 其他敏感數據完全遮罩
                        if self.preserve_length:
                            masked_value = self.mask_char * len(matched_text)
                        else:
                            masked_value = f"[{category.upper()}_REDACTED]"

                    masked_text = masked_text[:start] + masked_value + masked_text[end:]

        return masked_text

    def _mask_email(self, email: str) -> str:
        """遮罩 email 地址，保留部分信息"""
        if "@" in email:
            local, domain = email.split("@", 1)
            if len(local) > 2:
                masked_local = local[:2] + self.mask_char * (len(local) - 2)
            else:
                masked_local = self.mask_char * len(local)
            return f"{masked_local}@{domain}"
        return self.mask_char * len(email)

    def _mask_api_key(self, api_key: str) -> str:
        """遮罩 API 密鑰，保留前綴"""
        if len(api_key) > 8:
            return api_key[:8] + self.mask_char * (len(api_key) - 8)
        return self.mask_char * len(api_key)

    def filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """過濾字典中的敏感數據"""
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            # 檢查鍵名是否包含敏感信息
            if self._is_sensitive_key(key):
                filtered[key] = "[REDACTED]"
            elif isinstance(value, str):
                filtered[key] = self.mask_sensitive_data(value)
            elif isinstance(value, dict):
                filtered[key] = self.filter_dict(value)
            elif isinstance(value, list):
                filtered[key] = [
                    (
                        self.filter_dict(item)
                        if isinstance(item, dict)
                        else self.mask_sensitive_data(str(item)) if isinstance(item, str) else item
                    )
                    for item in value
                ]
            else:
                filtered[key] = value

        return filtered

    def _is_sensitive_key(self, key: str) -> bool:
        """檢查鍵名是否敏感"""
        sensitive_keys = [
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "key",
            "api_key",
            "private_key",
            "jwt",
            "bearer",
            "auth",
            "credential",
            "authorization",
        ]
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in sensitive_keys)


class SecurityLogFormatter(logging.Formatter):
    """安全日誌格式化器，自動過濾敏感數據"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter = SensitiveDataFilter()

    def format(self, record: logging.LogRecord) -> str:
        # 過濾日誌消息
        if hasattr(record, "msg") and record.msg:
            record.msg = self.filter.mask_sensitive_data(str(record.msg))

        # 過濾參數
        if hasattr(record, "args") and record.args:
            filtered_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    filtered_args.append(self.filter.mask_sensitive_data(arg))
                elif isinstance(arg, dict):
                    filtered_args.append(self.filter.filter_dict(arg))
                else:
                    filtered_args.append(arg)
            record.args = tuple(filtered_args)

        return super().format(record)


class SecurityAuditLogger:
    """安全審計日誌記錄器"""

    def __init__(self, logger_name: str = "security_audit"):
        self.logger = logging.getLogger(logger_name)
        self.filter = SensitiveDataFilter()

        # 設置安全格式化器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = SecurityLogFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_auth_attempt(self, user_id: str, success: bool, ip_address: str):
        """記錄認證嘗試"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Auth attempt: {status} - User: {user_id} - IP: {ip_address}")

    def log_sensitive_operation(self, operation: str, user_id: str, details: Dict[str, Any]):
        """記錄敏感操作"""
        filtered_details = self.filter.filter_dict(details)
        self.logger.warning(
            f"Sensitive operation: {operation} - User: {user_id} - Details: {json.dumps(filtered_details)}"
        )

    def log_security_event(self, event_type: str, severity: str, details: Dict[str, Any]):
        """記錄安全事件"""
        filtered_details = self.filter.filter_dict(details)
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(f"Security event: {event_type} - Details: {json.dumps(filtered_details)}")


# 全域安全日誌記錄器實例
security_logger = SecurityAuditLogger()


def setup_secure_logging():
    """設置安全的日誌記錄"""
    # 為根日誌記錄器添加安全過濾器
    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        handler.setFormatter(
            SecurityLogFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    # 為 FastAPI 應用添加安全日誌配置
    logging.getLogger("uvicorn.access").handlers = []


def mask_url_params(url: str) -> str:
    """遮罩 URL 參數中的敏感數據"""
    filter = SensitiveDataFilter()
    return filter.mask_sensitive_data(url)


# 使用範例
if __name__ == "__main__":
    # 測試敏感數據過濾
    filter = SensitiveDataFilter()

    test_cases = [
        "API key: sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF",
        "Password: mySecretPassword123",
        "Email: user@example.com",
        "JWT token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        '{"api_key": "sk-abcd1234", "email": "test@example.com"}',
    ]

    for test in test_cases:
        print(f"Original: {test}")
        print(f"Filtered: {filter.mask_sensitive_data(test)}")
        print("-" * 50)
