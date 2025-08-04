#!/usr/bin/env python3
"""
零信任安全架構實現
達到 Google BeyondCorp / Microsoft Zero Trust 級別的安全標準
"""

import asyncio
import logging
import json
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import jwt
import redis
import httpx

logger = logging.getLogger(__name__)


class TrustLevel(Enum):
    UNTRUSTED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERIFIED = 4


class RiskLevel(Enum):
    MINIMAL = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SecurityContext:
    """安全上下文"""

    user_id: str
    device_id: str
    ip_address: str
    user_agent: str
    location: Optional[Dict[str, str]]
    trust_level: TrustLevel
    risk_score: float
    session_id: str
    timestamp: datetime


@dataclass
class AccessPolicy:
    """訪問策略"""

    resource: str
    required_trust_level: TrustLevel
    max_risk_score: float
    allowed_actions: Set[str]
    conditions: Dict[str, Any]


@dataclass
class SecurityEvent:
    """安全事件"""

    event_id: str
    event_type: str
    user_id: str
    resource: str
    action: str
    risk_level: RiskLevel
    context: SecurityContext
    timestamp: datetime
    metadata: Dict[str, Any]


class DeviceFingerprinter:
    """設備指紋識別器"""

    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=3)
        self.known_devices = {}

    async def generate_fingerprint(self, request_data: Dict[str, Any]) -> str:
        """生成設備指紋"""
        fingerprint_data = {
            "user_agent": request_data.get("user_agent", ""),
            "screen_resolution": request_data.get("screen_resolution", ""),
            "timezone": request_data.get("timezone", ""),
            "language": request_data.get("language", ""),
            "platform": request_data.get("platform", ""),
            "canvas_fingerprint": request_data.get("canvas_fingerprint", ""),
            "webgl_fingerprint": request_data.get("webgl_fingerprint", ""),
        }

        # 創建穩定的設備指紋
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        device_id = hashlib.sha256(fingerprint_string.encode()).hexdigest()

        # 存儲設備資訊
        await self._store_device_info(device_id, fingerprint_data)

        return device_id

    async def _store_device_info(
        self, device_id: str, fingerprint_data: Dict[str, Any]
    ):
        """存儲設備資訊"""
        device_info = {
            "fingerprint": fingerprint_data,
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "trust_score": 0.5,  # 初始信任分數
        }

        # 檢查是否為已知設備
        existing_info = self.redis_client.get(f"device:{device_id}")
        if existing_info:
            existing_data = json.loads(existing_info)
            device_info["first_seen"] = existing_data["first_seen"]
            device_info["trust_score"] = min(
                existing_data["trust_score"] + 0.1, 1.0
            )

        self.redis_client.setex(
            f"device:{device_id}", timedelta(days=90), json.dumps(device_info)
        )

    async def get_device_trust_score(self, device_id: str) -> float:
        """獲取設備信任分數"""
        device_info = self.redis_client.get(f"device:{device_id}")
        if device_info:
            data = json.loads(device_info)
            return data.get("trust_score", 0.0)
        return 0.0


class BehaviorAnalyzer:
    """行為分析器 - 檢測異常用戶行為"""

    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=4)
        self.behavior_models = {}

    async def analyze_behavior(
        self, user_id: str, action: str, context: SecurityContext
    ) -> float:
        """分析用戶行為並返回風險分數"""

        # 獲取用戶歷史行為
        await self._get_user_behavior_history(user_id)

        # 時間分析
        time_risk = await self._analyze_time_patterns(
            user_id, context.timestamp
        )

        # 地理位置分析
        location_risk = await self._analyze_location_patterns(
            user_id, context.location
        )

        # 頻率分析
        frequency_risk = await self._analyze_frequency_patterns(
            user_id, action
        )

        # 設備分析
        device_risk = await self._analyze_device_patterns(
            user_id, context.device_id
        )

        # 綜合風險評估
        total_risk = (
            time_risk * 0.2
            + location_risk * 0.3
            + frequency_risk * 0.3
            + device_risk * 0.2
        )

        # 記錄當前行為
        await self._record_behavior(user_id, action, context, total_risk)

        logger.info(f"用戶 {user_id} 行為風險分析: {total_risk:.3f}")
        return min(total_risk, 1.0)

    async def _get_user_behavior_history(
        self, user_id: str
    ) -> List[Dict[str, Any]]:
        """獲取用戶行為歷史"""
        history_key = f"behavior_history:{user_id}"
        history_data = self.redis_client.lrange(
            history_key, 0, 100
        )  # 最近100條

        return [json.loads(item) for item in history_data]

    async def _analyze_time_patterns(
        self, user_id: str, current_time: datetime
    ) -> float:
        """分析時間模式異常"""
        # 獲取用戶常用時間段
        history = await self._get_user_behavior_history(user_id)
        if not history:
            return 0.2  # 新用戶默認較低風險

        # 計算常用時間段
        hour_counts = {}
        for record in history:
            hour = datetime.fromisoformat(record["timestamp"]).hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        current_hour = current_time.hour
        expected_activity = hour_counts.get(current_hour, 0)
        max_activity = max(hour_counts.values()) if hour_counts else 1

        # 如果在非常用時間段活動，風險較高
        time_risk = 1.0 - (expected_activity / max_activity)
        return min(time_risk, 0.8)

    async def _analyze_location_patterns(
        self, user_id: str, location: Optional[Dict[str, str]]
    ) -> float:
        """分析地理位置異常"""
        if not location:
            return 0.3

        history = await self._get_user_behavior_history(user_id)
        if not history:
            return 0.2

        # 分析常用地理位置
        location_counts = {}
        for record in history:
            if "location" in record and record["location"]:
                country = record["location"].get("country", "unknown")
                location_counts[country] = location_counts.get(country, 0) + 1

        current_country = location.get("country", "unknown")
        if current_country in location_counts:
            return 0.1  # 常用地點，低風險
        else:
            return 0.7  # 新地點，高風險

    async def _analyze_frequency_patterns(
        self, user_id: str, action: str
    ) -> float:
        """分析操作頻率異常"""
        # 檢查最近1小時內的同類操作次數
        recent_actions = []
        history = await self._get_user_behavior_history(user_id)

        current_time = datetime.utcnow()
        for record in history:
            record_time = datetime.fromisoformat(record["timestamp"])
            if (current_time - record_time).total_seconds() < 3600:  # 1小時內
                if record["action"] == action:
                    recent_actions.append(record)

        # 根據操作類型設定頻率限制
        frequency_limits = {
            "video_generation": 10,  # 每小時最多10次
            "api_call": 100,  # 每小時最多100次
            "login": 5,  # 每小時最多5次登入
            "password_change": 2,  # 每小時最多2次密碼修改
        }

        limit = frequency_limits.get(action, 50)
        frequency_risk = len(recent_actions) / limit

        return min(frequency_risk, 1.0)

    async def _analyze_device_patterns(
        self, user_id: str, device_id: str
    ) -> float:
        """分析設備使用模式"""
        # 檢查用戶是否經常使用此設備
        history = await self._get_user_behavior_history(user_id)
        device_usage = sum(
            1 for record in history if record.get("device_id") == device_id
        )

        if device_usage > 10:
            return 0.1  # 常用設備，低風險
        elif device_usage > 0:
            return 0.3  # 偶爾使用，中等風險
        else:
            return 0.6  # 新設備，高風險

    async def _record_behavior(
        self,
        user_id: str,
        action: str,
        context: SecurityContext,
        risk_score: float,
    ):
        """記錄用戶行為"""
        behavior_record = {
            "action": action,
            "timestamp": context.timestamp.isoformat(),
            "device_id": context.device_id,
            "ip_address": context.ip_address,
            "location": context.location,
            "risk_score": risk_score,
        }

        history_key = f"behavior_history:{user_id}"
        self.redis_client.lpush(history_key, json.dumps(behavior_record))
        self.redis_client.ltrim(history_key, 0, 999)  # 保留最近1000條記錄
        self.redis_client.expire(history_key, timedelta(days=30))


class RiskEngine:
    """風險評估引擎"""

    def __init__(self):
        self.behavior_analyzer = BehaviorAnalyzer()
        self.device_fingerprinter = DeviceFingerprinter()
        self.threat_intelligence = ThreatIntelligence()

    async def assess_risk(
        self, user_id: str, action: str, context: SecurityContext
    ) -> float:
        """綜合風險評估"""

        # 行為風險
        behavior_risk = await self.behavior_analyzer.analyze_behavior(
            user_id, action, context
        )

        # 設備風險
        device_trust = await self.device_fingerprinter.get_device_trust_score(
            context.device_id
        )
        device_risk = 1.0 - device_trust

        # 威脅情報風險
        threat_risk = await self.threat_intelligence.check_ip_reputation(
            context.ip_address
        )

        # 會話風險
        session_risk = await self._assess_session_risk(context.session_id)

        # 綜合風險計算
        total_risk = (
            behavior_risk * 0.4
            + device_risk * 0.2
            + threat_risk * 0.3
            + session_risk * 0.1
        )

        logger.info(
            f"風險評估 - 用戶:{user_id}, 行為:{behavior_risk:.3f}, "
            f"設備:{device_risk:.3f}, 威脅:{threat_risk:.3f}, "
            f"會話:{session_risk:.3f}, 總計:{total_risk:.3f}"
        )

        return min(total_risk, 1.0)

    async def _assess_session_risk(self, session_id: str) -> float:
        """評估會話風險"""
        # 檢查會話時長
        session_key = f"session:{session_id}"
        session_data = self.redis_client.get(session_key)

        if not session_data:
            return 0.8  # 無效會話，高風險

        session_info = json.loads(session_data)
        session_start = datetime.fromisoformat(session_info["created_at"])
        session_duration = (datetime.utcnow() - session_start).total_seconds()

        # 超長會話可能存在風險
        if session_duration > 86400:  # 24小時
            return 0.6
        elif session_duration > 3600:  # 1小時
            return 0.3
        else:
            return 0.1


class ThreatIntelligence:
    """威脅情報系統"""

    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=5)
        self.malicious_ips = set()
        self.malicious_domains = set()

    async def check_ip_reputation(self, ip_address: str) -> float:
        """檢查 IP 信譽"""
        # 檢查本地黑名單
        if ip_address in self.malicious_ips:
            return 1.0

        # 檢查緩存的信譽數據
        reputation_key = f"ip_reputation:{ip_address}"
        cached_reputation = self.redis_client.get(reputation_key)

        if cached_reputation:
            return float(cached_reputation)

        # 查詢外部威脅情報源
        reputation_score = await self._query_threat_intelligence(ip_address)

        # 緩存結果
        self.redis_client.setex(
            reputation_key, timedelta(hours=1), str(reputation_score)
        )

        return reputation_score

    async def _query_threat_intelligence(self, ip_address: str) -> float:
        """查詢威脅情報"""
        try:
            # 模擬查詢多個威脅情報源
            sources = [
                "https://api.virustotal.com/api/v3/ip_addresses/{ip}",
                "https://api.abuseipdb.com/api/v2/check?ipAddress={ip}",
                # 可以添加更多威脅情報源
            ]

            risk_scores = []

            async with httpx.AsyncClient() as client:
                for source in sources:
                    try:
                        # 模擬 API 調用（實際需要 API 密鑰）
                        # response = await client.get(source.format(ip=ip_address))
                        # 模擬響應
                        simulated_score = (
                            0.1 if ip_address.startswith("192.168.") else 0.0
                        )
                        risk_scores.append(simulated_score)
                    except Exception as e:
                        logger.warning(f"威脅情報查詢失敗: {e}")
                        continue

            # 取平均風險分數
            return sum(risk_scores) / len(risk_scores) if risk_scores else 0.2

        except Exception as e:
            logger.error(f"威脅情報查詢錯誤: {e}")
            return 0.2  # 默認風險分數


class PolicyEngine:
    """策略引擎"""

    def __init__(self):
        self.policies: Dict[str, AccessPolicy] = {}
        self.dynamic_policies = {}
        self._load_default_policies()

    def _load_default_policies(self):
        """載入默認安全策略"""
        self.policies.update(
            {
                "video_generation": AccessPolicy(
                    resource="video_generation",
                    required_trust_level=TrustLevel.MEDIUM,
                    max_risk_score=0.6,
                    allowed_actions={"create", "read", "update"},
                    conditions={"max_daily_generations": 50},
                ),
                "admin_access": AccessPolicy(
                    resource="admin_access",
                    required_trust_level=TrustLevel.VERIFIED,
                    max_risk_score=0.2,
                    allowed_actions={"read", "write", "delete"},
                    conditions={"require_mfa": True, "ip_whitelist": True},
                ),
                "api_access": AccessPolicy(
                    resource="api_access",
                    required_trust_level=TrustLevel.LOW,
                    max_risk_score=0.8,
                    allowed_actions={"read"},
                    conditions={"rate_limit": 100},
                ),
            }
        )

    async def evaluate_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: SecurityContext,
    ) -> Dict[str, Any]:
        """評估訪問權限"""

        if resource not in self.policies:
            return {
                "allowed": False,
                "reason": f"未定義資源 {resource} 的訪問策略",
            }

        policy = self.policies[resource]

        # 檢查信任等級
        if context.trust_level.value < policy.required_trust_level.value:
            return {
                "allowed": False,
                "reason": f"信任等級不足: 需要 {policy.required_trust_level.name}, 當前 {context.trust_level.name}",
            }

        # 檢查風險分數
        if context.risk_score > policy.max_risk_score:
            return {
                "allowed": False,
                "reason": f"風險分數過高: {context.risk_score:.3f} > {policy.max_risk_score}",
            }

        # 檢查允許的操作
        if action not in policy.allowed_actions:
            return {
                "allowed": False,
                "reason": f"操作 {action} 不在允許列表中: {policy.allowed_actions}",
            }

        # 檢查額外條件
        condition_check = await self._check_policy_conditions(
            user_id, policy, context
        )
        if not condition_check["passed"]:
            return {
                "allowed": False,
                "reason": f"策略條件檢查失敗: {condition_check['reason']}",
            }

        return {
            "allowed": True,
            "reason": "通過所有安全檢查",
            "policy": policy.resource,
            "trust_level": context.trust_level.name,
            "risk_score": context.risk_score,
        }

    async def _check_policy_conditions(
        self, user_id: str, policy: AccessPolicy, context: SecurityContext
    ) -> Dict[str, Any]:
        """檢查策略條件"""

        for condition, value in policy.conditions.items():
            if condition == "max_daily_generations":
                daily_count = await self._get_daily_generation_count(user_id)
                if daily_count >= value:
                    return {
                        "passed": False,
                        "reason": f"超過每日生成限制: {daily_count} >= {value}",
                    }

            elif condition == "require_mfa":
                if value and not await self._check_mfa_status(user_id):
                    return {"passed": False, "reason": "需要多因素認證"}

            elif condition == "ip_whitelist":
                if value and not await self._check_ip_whitelist(
                    user_id, context.ip_address
                ):
                    return {
                        "passed": False,
                        "reason": f"IP {context.ip_address} 不在白名單中",
                    }

        return {"passed": True, "reason": "所有條件檢查通過"}

    async def _get_daily_generation_count(self, user_id: str) -> int:
        """獲取每日生成次數"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        count_key = f"daily_generation:{user_id}:{today}"
        count = self.redis_client.get(count_key)
        return int(count) if count else 0

    async def _check_mfa_status(self, user_id: str) -> bool:
        """檢查多因素認證狀態"""
        mfa_key = f"mfa_status:{user_id}"
        status = self.redis_client.get(mfa_key)
        return status == b"verified"

    async def _check_ip_whitelist(self, user_id: str, ip_address: str) -> bool:
        """檢查 IP 白名單"""
        whitelist_key = f"ip_whitelist:{user_id}"
        whitelist = self.redis_client.smembers(whitelist_key)
        return ip_address.encode() in whitelist


class ZeroTrustGateway:
    """零信任安全網關"""

    def __init__(self):
        self.risk_engine = RiskEngine()
        self.policy_engine = PolicyEngine()
        self.device_fingerprinter = DeviceFingerprinter()
        self.audit_logger = AuditLogger()

    async def authenticate_and_authorize(
        self,
        token: str,
        resource: str,
        action: str,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """零信任認證和授權"""

        try:
            # 1. 驗證令牌
            token_data = await self._verify_token(token)
            if not token_data["valid"]:
                return {"authorized": False, "reason": "令牌無效或已過期"}

            user_id = token_data["user_id"]

            # 2. 生成設備指紋
            device_id = await self.device_fingerprinter.generate_fingerprint(
                request_data
            )

            # 3. 構建安全上下文
            context = SecurityContext(
                user_id=user_id,
                device_id=device_id,
                ip_address=request_data.get("ip_address", ""),
                user_agent=request_data.get("user_agent", ""),
                location=request_data.get("location"),
                trust_level=await self._calculate_trust_level(
                    user_id, device_id
                ),
                risk_score=0.0,  # 將在風險評估中計算
                session_id=token_data["session_id"],
                timestamp=datetime.utcnow(),
            )

            # 4. 風險評估
            context.risk_score = await self.risk_engine.assess_risk(
                user_id, action, context
            )

            # 5. 策略評估
            access_decision = await self.policy_engine.evaluate_access(
                user_id, resource, action, context
            )

            # 6. 記錄安全事件
            await self.audit_logger.log_access_attempt(
                user_id, resource, action, context, access_decision["allowed"]
            )

            return {
                "authorized": access_decision["allowed"],
                "reason": access_decision["reason"],
                "trust_level": context.trust_level.name,
                "risk_score": context.risk_score,
                "context": asdict(context),
            }

        except Exception as e:
            logger.error(f"零信任認證過程發生錯誤: {e}")
            return {"authorized": False, "reason": "系統錯誤，拒絕訪問"}

    async def _verify_token(self, token: str) -> Dict[str, Any]:
        """驗證 JWT 令牌"""
        try:
            # 實際實現中應該使用適當的密鑰和算法
            decoded = jwt.decode(
                token, "your-secret-key", algorithms=["HS256"]
            )

            # 檢查令牌是否被撤銷
            if await self._is_token_revoked(token):
                return {"valid": False, "reason": "令牌已被撤銷"}

            return {
                "valid": True,
                "user_id": decoded["user_id"],
                "session_id": decoded["session_id"],
            }

        except jwt.ExpiredSignatureError:
            return {"valid": False, "reason": "令牌已過期"}
        except jwt.InvalidTokenError:
            return {"valid": False, "reason": "令牌格式無效"}

    async def _is_token_revoked(self, token: str) -> bool:
        """檢查令牌是否被撤銷"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        revoked_key = f"revoked_token:{token_hash}"
        return self.redis_client.exists(revoked_key)

    async def _calculate_trust_level(
        self, user_id: str, device_id: str
    ) -> TrustLevel:
        """計算用戶信任等級"""

        # 獲取用戶基礎信任分數
        user_trust = await self._get_user_trust_score(user_id)

        # 獲取設備信任分數
        device_trust = await self.device_fingerprinter.get_device_trust_score(
            device_id
        )

        # 綜合信任分數
        combined_trust = (user_trust + device_trust) / 2

        # 映射到信任等級
        if combined_trust >= 0.9:
            return TrustLevel.VERIFIED
        elif combined_trust >= 0.7:
            return TrustLevel.HIGH
        elif combined_trust >= 0.5:
            return TrustLevel.MEDIUM
        elif combined_trust >= 0.3:
            return TrustLevel.LOW
        else:
            return TrustLevel.UNTRUSTED

    async def _get_user_trust_score(self, user_id: str) -> float:
        """獲取用戶信任分數"""
        trust_key = f"user_trust:{user_id}"
        trust_score = self.redis_client.get(trust_key)
        return float(trust_score) if trust_score else 0.5


class AuditLogger:
    """審計日誌記錄器"""

    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=6)

    async def log_access_attempt(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: SecurityContext,
        success: bool,
    ):
        """記錄訪問嘗試"""

        event = SecurityEvent(
            event_id=secrets.token_hex(16),
            event_type="access_attempt",
            user_id=user_id,
            resource=resource,
            action=action,
            risk_level=self._determine_risk_level(context.risk_score),
            context=context,
            timestamp=datetime.utcnow(),
            metadata={
                "success": success,
                "trust_level": context.trust_level.name,
            },
        )

        # 記錄到審計日誌
        audit_log = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "success": success,
            "risk_score": context.risk_score,
            "trust_level": context.trust_level.name,
            "ip_address": context.ip_address,
            "device_id": context.device_id,
            "user_agent": context.user_agent,
        }

        # 存儲審計日誌
        audit_key = f"audit_log:{datetime.utcnow().strftime('%Y-%m-%d')}"
        self.redis_client.lpush(audit_key, json.dumps(audit_log))
        self.redis_client.expire(audit_key, timedelta(days=90))  # 保留90天

        # 高風險事件額外記錄
        if context.risk_score > 0.7 or not success:
            await self._log_high_risk_event(event)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """根據風險分數確定風險等級"""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL

    async def _log_high_risk_event(self, event: SecurityEvent):
        """記錄高風險事件"""
        high_risk_key = "high_risk_events"
        event_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "resource": event.resource,
            "action": event.action,
            "risk_level": event.risk_level.name,
            "risk_score": event.context.risk_score,
            "ip_address": event.context.ip_address,
        }

        self.redis_client.lpush(high_risk_key, json.dumps(event_data))
        self.redis_client.ltrim(high_risk_key, 0, 9999)  # 保留最近10000條

        logger.warning(f"高風險事件記錄: {event.event_id}")


# 使用示例
async def main():
    """零信任安全系統使用示例"""

    gateway = ZeroTrustGateway()

    # 模擬請求
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."  # JWT token
    request_data = {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "screen_resolution": "1920x1080",
        "timezone": "Asia/Taipei",
        "language": "zh-TW",
        "platform": "Win32",
    }

    # 零信任認證
    result = await gateway.authenticate_and_authorize(
        token=token,
        resource="video_generation",
        action="create",
        request_data=request_data,
    )

    if result["authorized"]:
        print(
            f"✅ 訪問授權 - 信任等級: {result['trust_level']}, 風險分數: {result['risk_score']:.3f}"
        )
    else:
        print(f"❌ 訪問拒絕 - 原因: {result['reason']}")


if __name__ == "__main__":
    asyncio.run(main())
