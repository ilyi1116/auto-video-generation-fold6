"""
密碼管理器

提供密碼加密、驗證、強度檢查和安全策略管理功能。
"""

import hashlib
import secrets
import string
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from passlib.context import CryptContext
from passlib.hash import bcrypt
import zxcvbn

from .models import PasswordPolicy

logger = logging.getLogger(__name__)


class PasswordManager:
    """密碼管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 密碼加密上下文
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12
        )
        
        # 默認密碼策略
        self.default_policy = PasswordPolicy(
            min_length=self.config.get("min_length", 8),
            max_length=self.config.get("max_length", 128),
            require_uppercase=self.config.get("require_uppercase", True),
            require_lowercase=self.config.get("require_lowercase", True),
            require_numbers=self.config.get("require_numbers", True),
            require_special_chars=self.config.get("require_special_chars", True),
            forbidden_patterns=self.config.get("forbidden_patterns", [
                "password", "123456", "qwerty", "admin", "root", "guest"
            ]),
            max_age_days=self.config.get("max_age_days", 90),
            prevent_reuse_count=self.config.get("prevent_reuse_count", 5)
        )
        
        # 密碼歷史記錄 (用戶ID -> 密碼哈希列表)
        self.password_history: Dict[str, List[str]] = {}
        
        # 常見弱密碼列表
        self.common_passwords = self._load_common_passwords()
        
        logger.info("密碼管理器初始化完成")
    
    def _load_common_passwords(self) -> List[str]:
        """加載常見弱密碼列表"""
        common_passwords = [
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "dragon", "shadow",
            "master", "666666", "123123", "654321", "superman",
            "1qaz2wsx", "7777777", "123qwe", "zxcvbnm", "121212"
        ]
        return common_passwords
    
    def hash_password(self, password: str) -> str:
        """
        加密密碼
        
        Args:
            password: 明文密碼
            
        Returns:
            加密後的密碼哈希
        """
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            logger.error(f"密碼加密失敗: {e}")
            raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        驗證密碼
        
        Args:
            plain_password: 明文密碼
            hashed_password: 加密後的密碼哈希
            
        Returns:
            密碼是否正確
        """
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"密碼驗證失敗: {e}")
            return False
    
    def generate_secure_password(self, length: int = 16) -> str:
        """
        生成安全密碼
        
        Args:
            length: 密碼長度
            
        Returns:
            生成的安全密碼
        """
        if length < 8:
            length = 8
        
        # 確保密碼包含各種字符類型
        chars = []
        chars.extend(secrets.choice(string.ascii_uppercase) for _ in range(2))
        chars.extend(secrets.choice(string.ascii_lowercase) for _ in range(2))
        chars.extend(secrets.choice(string.digits) for _ in range(2))
        chars.extend(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?") for _ in range(2))
        
        # 填充剩餘長度
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        chars.extend(secrets.choice(all_chars) for _ in range(length - len(chars)))
        
        # 隨機打亂
        secrets.SystemRandom().shuffle(chars)
        
        return ''.join(chars)
    
    def check_password_strength(self, password: str, username: str = None) -> Dict[str, Any]:
        """
        檢查密碼強度
        
        Args:
            password: 要檢查的密碼
            username: 用戶名（用於檢查是否包含用戶名）
            
        Returns:
            密碼強度分析結果
        """
        try:
            # 使用 zxcvbn 進行密碼強度分析
            result = zxcvbn.zxcvbn(password, user_inputs=[username] if username else [])
            
            # 基本強度檢查
            strength_checks = {
                "length_ok": len(password) >= self.default_policy.min_length,
                "has_uppercase": bool(re.search(r'[A-Z]', password)),
                "has_lowercase": bool(re.search(r'[a-z]', password)),
                "has_numbers": bool(re.search(r'\d', password)),
                "has_special": bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password)),
                "not_common": password.lower() not in self.common_passwords,
                "no_username": not username or username.lower() not in password.lower()
            }
            
            # 計算強度分數
            strength_score = result["score"]  # 0-4
            strength_labels = ["非常弱", "弱", "一般", "強", "非常強"]
            
            return {
                "score": strength_score,
                "label": strength_labels[strength_score],
                "feedback": result["feedback"]["suggestions"],
                "crack_time": result["crack_times_display"]["offline_slow_hashing_1e4_per_second"],
                "checks": strength_checks,
                "is_strong": strength_score >= 3 and all(strength_checks.values()),
                "warnings": result["feedback"]["warning"] if result["feedback"]["warning"] else None
            }
            
        except Exception as e:
            logger.error(f"密碼強度檢查失敗: {e}")
            return {
                "score": 0,
                "label": "檢查失敗",
                "feedback": ["密碼強度檢查失敗"],
                "crack_time": "未知",
                "checks": {},
                "is_strong": False,
                "warnings": "密碼強度檢查失敗"
            }
    
    def validate_password_policy(self, password: str, policy: Optional[PasswordPolicy] = None) -> Tuple[bool, List[str]]:
        """
        驗證密碼是否符合策略
        
        Args:
            password: 要檢查的密碼
            policy: 密碼策略（默認使用系統策略）
            
        Returns:
            (是否符合策略, 錯誤信息列表)
        """
        if not policy:
            policy = self.default_policy
        
        errors = []
        
        # 長度檢查
        if len(password) < policy.min_length:
            errors.append(f"密碼長度至少需要 {policy.min_length} 個字符")
        
        if len(password) > policy.max_length:
            errors.append(f"密碼長度不能超過 {policy.max_length} 個字符")
        
        # 字符類型檢查
        if policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("密碼必須包含大寫字母")
        
        if policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("密碼必須包含小寫字母")
        
        if policy.require_numbers and not re.search(r'\d', password):
            errors.append("密碼必須包含數字")
        
        if policy.require_special_chars and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            errors.append("密碼必須包含特殊字符")
        
        # 禁用模式檢查
        for pattern in policy.forbidden_patterns:
            if pattern.lower() in password.lower():
                errors.append(f"密碼不能包含常見模式: {pattern}")
        
        return len(errors) == 0, errors
    
    def check_password_reuse(self, user_id: str, new_password: str) -> bool:
        """
        檢查密碼是否重複使用
        
        Args:
            user_id: 用戶ID
            new_password: 新密碼
            
        Returns:
            是否重複使用（True表示重複）
        """
        if user_id not in self.password_history:
            return False
        
        new_hash = self.hash_password(new_password)
        history = self.password_history[user_id]
        
        for old_hash in history:
            if self.verify_password(new_password, old_hash):
                return True
        
        return False
    
    def add_password_to_history(self, user_id: str, password_hash: str):
        """
        添加密碼到歷史記錄
        
        Args:
            user_id: 用戶ID
            password_hash: 密碼哈希
        """
        if user_id not in self.password_history:
            self.password_history[user_id] = []
        
        history = self.password_history[user_id]
        history.append(password_hash)
        
        # 保持歷史記錄數量限制
        max_history = self.default_policy.prevent_reuse_count
        if len(history) > max_history:
            self.password_history[user_id] = history[-max_history:]
    
    def is_password_expired(self, password_created_at: datetime) -> bool:
        """
        檢查密碼是否過期
        
        Args:
            password_created_at: 密碼創建時間
            
        Returns:
            是否過期
        """
        if not self.default_policy.max_age_days:
            return False
        
        expiry_date = password_created_at + timedelta(days=self.default_policy.max_age_days)
        return datetime.utcnow() > expiry_date
    
    def generate_password_reset_token(self, user_id: str) -> str:
        """
        生成密碼重置令牌
        
        Args:
            user_id: 用戶ID
            
        Returns:
            重置令牌
        """
        # 生成隨機令牌
        token = secrets.token_urlsafe(32)
        
        # 這裡應該將令牌存儲到數據庫，並設置過期時間
        # 為了示例，我們只返回令牌
        
        logger.info(f"為用戶 {user_id} 生成密碼重置令牌")
        return token
    
    def validate_password_reset_token(self, token: str) -> Optional[str]:
        """
        驗證密碼重置令牌
        
        Args:
            token: 重置令牌
            
        Returns:
            用戶ID（如果令牌有效）
        """
        # 這裡應該從數據庫驗證令牌
        # 為了示例，我們返回 None
        
        logger.info(f"驗證密碼重置令牌: {token[:8]}...")
        return None
    
    def get_password_policy(self) -> PasswordPolicy:
        """獲取當前密碼策略"""
        return self.default_policy
    
    def update_password_policy(self, policy: PasswordPolicy):
        """更新密碼策略"""
        self.default_policy = policy
        logger.info("密碼策略已更新")
    
    def get_password_requirements(self) -> Dict[str, Any]:
        """獲取密碼要求說明"""
        policy = self.default_policy
        
        requirements = []
        if policy.min_length:
            requirements.append(f"至少 {policy.min_length} 個字符")
        if policy.require_uppercase:
            requirements.append("包含大寫字母")
        if policy.require_lowercase:
            requirements.append("包含小寫字母")
        if policy.require_numbers:
            requirements.append("包含數字")
        if policy.require_special_chars:
            requirements.append("包含特殊字符")
        
        return {
            "requirements": requirements,
            "forbidden_patterns": policy.forbidden_patterns,
            "max_age_days": policy.max_age_days,
            "prevent_reuse_count": policy.prevent_reuse_count
        }
    
    def clear_password_history(self, user_id: str):
        """清除用戶密碼歷史"""
        if user_id in self.password_history:
            del self.password_history[user_id]
            logger.info(f"已清除用戶 {user_id} 的密碼歷史")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取密碼管理統計"""
        return {
            "total_users_with_history": len(self.password_history),
            "total_password_entries": sum(len(history) for history in self.password_history.values()),
            "policy": self.default_policy.to_dict()
        }


# 全局密碼管理器實例
password_manager = PasswordManager()


def init_password_manager(config: Optional[Dict[str, Any]] = None) -> PasswordManager:
    """初始化密碼管理器"""
    global password_manager
    password_manager = PasswordManager(config)
    return password_manager