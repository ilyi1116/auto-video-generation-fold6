"""
Auto Video System GDPR 合規性模組
實現 GDPR (通用資料保護規則) 相關功能
"""

import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class DataProcessingPurpose(Enum):
    """資料處理目的"""
    SERVICE_PROVISION = "service_provision"
    LEGITIMATE_INTEREST = "legitimate_interest"
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"

class DataCategory(Enum):
    """資料類別"""
    PERSONAL_IDENTITY = "personal_identity"
    CONTACT_INFO = "contact_info"
    AUDIO_DATA = "audio_data"
    VIDEO_DATA = "video_data"
    USAGE_DATA = "usage_data"
    TECHNICAL_DATA = "technical_data"
    MARKETING_DATA = "marketing_data"

@dataclass
class ConsentRecord:
    """同意記錄"""
    user_id: int
    purpose: DataProcessingPurpose
    categories: List[DataCategory]
    granted_at: datetime
    expires_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    version: str = "1.0"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class GDPRConsentLog(Base):
    """GDPR 同意日誌表"""
    __tablename__ = "gdpr_consent_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    purpose = Column(String(100), nullable=False)
    data_categories = Column(JSON, nullable=False)
    action = Column(String(50), nullable=False)  # granted, withdrawn, updated
    timestamp = Column(DateTime, default=datetime.utcnow)
    version = Column(String(20), default="1.0")
    ip_address = Column(String(45))
    user_agent = Column(Text)
    details = Column(JSON)

class GDPRDataRequest(Base):
    """GDPR 資料請求表"""
    __tablename__ = "gdpr_data_requests"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    request_type = Column(String(50), nullable=False)  # access, rectification, erasure, portability
    status = Column(String(50), default="pending")  # pending, processing, completed, rejected
    requested_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    request_details = Column(JSON)
    response_data = Column(JSON)
    verification_token = Column(String(255))

class GDPRDataProcessingLog(Base):
    """資料處理活動日誌"""
    __tablename__ = "gdpr_processing_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    data_category = Column(String(100), nullable=False)
    processing_purpose = Column(String(100), nullable=False)
    legal_basis = Column(String(100), nullable=False)
    processor = Column(String(100), nullable=False)  # 處理系統/服務名稱
    timestamp = Column(DateTime, default=datetime.utcnow)
    retention_period = Column(Integer)  # 保留期限（天）
    details = Column(JSON)

class GDPRComplianceManager:
    """GDPR 合規性管理器"""
    
    def __init__(self, db_session):
        self.db = db_session
        
    async def record_consent(self, consent: ConsentRecord) -> bool:
        """記錄用戶同意"""
        try:
            log_entry = GDPRConsentLog(
                user_id=consent.user_id,
                purpose=consent.purpose.value,
                data_categories=[cat.value for cat in consent.categories],
                action="granted",
                timestamp=consent.granted_at,
                version=consent.version,
                ip_address=consent.ip_address,
                user_agent=consent.user_agent,
                details={
                    "expires_at": consent.expires_at.isoformat() if consent.expires_at else None
                }
            )
            
            self.db.add(log_entry)
            await self.db.commit()
            
            logger.info(f"Consent recorded for user {consent.user_id}, purpose: {consent.purpose.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            await self.db.rollback()
            return False
    
    async def withdraw_consent(self, user_id: int, purpose: DataProcessingPurpose) -> bool:
        """撤回同意"""
        try:
            log_entry = GDPRConsentLog(
                user_id=user_id,
                purpose=purpose.value,
                data_categories=[],
                action="withdrawn",
                timestamp=datetime.utcnow()
            )
            
            self.db.add(log_entry)
            await self.db.commit()
            
            logger.info(f"Consent withdrawn for user {user_id}, purpose: {purpose.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to withdraw consent: {e}")
            await self.db.rollback()
            return False
    
    async def check_consent(self, user_id: int, purpose: DataProcessingPurpose) -> bool:
        """檢查同意狀態"""
        try:
            # 查找最新的同意記錄
            latest_consent = self.db.query(GDPRConsentLog).filter(
                GDPRConsentLog.user_id == user_id,
                GDPRConsentLog.purpose == purpose.value
            ).order_by(GDPRConsentLog.timestamp.desc()).first()
            
            if not latest_consent:
                return False
            
            # 檢查是否已撤回
            if latest_consent.action == "withdrawn":
                return False
            
            return latest_consent.action == "granted"
            
        except Exception as e:
            logger.error(f"Failed to check consent: {e}")
            return False
    
    async def log_data_processing(self, user_id: int, category: DataCategory, 
                                purpose: DataProcessingPurpose, legal_basis: str,
                                processor: str, retention_days: int = None,
                                details: Dict = None) -> bool:
        """記錄資料處理活動"""
        try:
            log_entry = GDPRDataProcessingLog(
                user_id=user_id,
                data_category=category.value,
                processing_purpose=purpose.value,
                legal_basis=legal_basis,
                processor=processor,
                retention_period=retention_days,
                details=details or {}
            )
            
            self.db.add(log_entry)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log data processing: {e}")
            await self.db.rollback()
            return False

class DataRequestHandler:
    """資料請求處理器"""
    
    def __init__(self, db_session, user_service, data_service):
        self.db = db_session
        self.user_service = user_service
        self.data_service = data_service
    
    async def create_data_request(self, user_id: int, request_type: str, 
                                details: Dict = None) -> str:
        """創建資料請求"""
        try:
            # 生成驗證令牌
            verification_token = self._generate_verification_token(user_id, request_type)
            
            request = GDPRDataRequest(
                user_id=user_id,
                request_type=request_type,
                request_details=details or {},
                verification_token=verification_token
            )
            
            self.db.add(request)
            await self.db.commit()
            
            logger.info(f"Data request created for user {user_id}, type: {request_type}")
            return verification_token
            
        except Exception as e:
            logger.error(f"Failed to create data request: {e}")
            await self.db.rollback()
            raise
    
    async def process_data_access_request(self, request_id: int) -> Dict:
        """處理資料存取請求"""
        try:
            request = self.db.query(GDPRDataRequest).filter(
                GDPRDataRequest.id == request_id,
                GDPRDataRequest.request_type == "access"
            ).first()
            
            if not request:
                raise ValueError("Request not found")
            
            # 更新狀態
            request.status = "processing"
            await self.db.commit()
            
            # 收集用戶資料
            user_data = await self._collect_user_data(request.user_id)
            
            # 更新請求結果
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            request.response_data = user_data
            await self.db.commit()
            
            return user_data
            
        except Exception as e:
            logger.error(f"Failed to process data access request: {e}")
            if request:
                request.status = "failed"
                await self.db.commit()
            raise
    
    async def process_data_erasure_request(self, request_id: int) -> bool:
        """處理資料刪除請求（被遺忘權）"""
        try:
            request = self.db.query(GDPRDataRequest).filter(
                GDPRDataRequest.id == request_id,
                GDPRDataRequest.request_type == "erasure"
            ).first()
            
            if not request:
                raise ValueError("Request not found")
            
            # 更新狀態
            request.status = "processing"
            await self.db.commit()
            
            # 執行資料刪除
            deleted_data = await self._delete_user_data(request.user_id)
            
            # 更新請求結果
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            request.response_data = {"deleted_items": deleted_data}
            await self.db.commit()
            
            logger.info(f"Data erasure completed for user {request.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process data erasure request: {e}")
            if request:
                request.status = "failed"
                await self.db.commit()
            return False
    
    async def process_data_portability_request(self, request_id: int) -> bytes:
        """處理資料可攜性請求"""
        try:
            request = self.db.query(GDPRDataRequest).filter(
                GDPRDataRequest.id == request_id,
                GDPRDataRequest.request_type == "portability"
            ).first()
            
            if not request:
                raise ValueError("Request not found")
            
            # 更新狀態
            request.status = "processing"
            await self.db.commit()
            
            # 導出用戶資料
            export_data = await self._export_user_data(request.user_id)
            
            # 生成 JSON 檔案
            export_json = json.dumps(export_data, ensure_ascii=False, indent=2)
            export_bytes = export_json.encode('utf-8')
            
            # 更新請求結果
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            request.response_data = {"export_size": len(export_bytes)}
            await self.db.commit()
            
            return export_bytes
            
        except Exception as e:
            logger.error(f"Failed to process data portability request: {e}")
            if request:
                request.status = "failed"
                await self.db.commit()
            raise
    
    async def _collect_user_data(self, user_id: int) -> Dict:
        """收集用戶所有資料"""
        user_data = {
            "user_profile": await self.user_service.get_user_profile(user_id),
            "audio_files": await self.data_service.get_user_audio_files(user_id),
            "training_jobs": await self.data_service.get_user_training_jobs(user_id),
            "video_projects": await self.data_service.get_user_video_projects(user_id),
            "social_accounts": await self.data_service.get_user_social_accounts(user_id),
            "usage_analytics": await self.data_service.get_user_analytics(user_id),
            "consent_history": await self._get_user_consent_history(user_id),
            "processing_logs": await self._get_user_processing_logs(user_id)
        }
        
        return user_data
    
    async def _delete_user_data(self, user_id: int) -> List[str]:
        """刪除用戶資料"""
        deleted_items = []
        
        try:
            # 刪除音頻檔案
            audio_count = await self.data_service.delete_user_audio_files(user_id)
            if audio_count > 0:
                deleted_items.append(f"audio_files: {audio_count}")
            
            # 刪除訓練任務
            training_count = await self.data_service.delete_user_training_jobs(user_id)
            if training_count > 0:
                deleted_items.append(f"training_jobs: {training_count}")
            
            # 刪除影片專案
            video_count = await self.data_service.delete_user_video_projects(user_id)
            if video_count > 0:
                deleted_items.append(f"video_projects: {video_count}")
            
            # 刪除社群媒體帳號連結
            social_count = await self.data_service.delete_user_social_accounts(user_id)
            if social_count > 0:
                deleted_items.append(f"social_accounts: {social_count}")
            
            # 匿名化分析資料（保留聚合統計）
            analytics_count = await self.data_service.anonymize_user_analytics(user_id)
            if analytics_count > 0:
                deleted_items.append(f"analytics_anonymized: {analytics_count}")
            
            # 最後刪除用戶帳號
            await self.user_service.delete_user_account(user_id)
            deleted_items.append("user_account: 1")
            
        except Exception as e:
            logger.error(f"Error during data deletion: {e}")
            raise
        
        return deleted_items
    
    async def _export_user_data(self, user_id: int) -> Dict:
        """導出用戶資料"""
        return await self._collect_user_data(user_id)
    
    async def _get_user_consent_history(self, user_id: int) -> List[Dict]:
        """獲取用戶同意歷史"""
        consents = self.db.query(GDPRConsentLog).filter(
            GDPRConsentLog.user_id == user_id
        ).order_by(GDPRConsentLog.timestamp.desc()).all()
        
        return [
            {
                "purpose": consent.purpose,
                "data_categories": consent.data_categories,
                "action": consent.action,
                "timestamp": consent.timestamp.isoformat(),
                "version": consent.version
            }
            for consent in consents
        ]
    
    async def _get_user_processing_logs(self, user_id: int) -> List[Dict]:
        """獲取用戶資料處理日誌"""
        logs = self.db.query(GDPRDataProcessingLog).filter(
            GDPRDataProcessingLog.user_id == user_id
        ).order_by(GDPRDataProcessingLog.timestamp.desc()).limit(100).all()
        
        return [
            {
                "data_category": log.data_category,
                "processing_purpose": log.processing_purpose,
                "legal_basis": log.legal_basis,
                "processor": log.processor,
                "timestamp": log.timestamp.isoformat(),
                "retention_period": log.retention_period
            }
            for log in logs
        ]
    
    def _generate_verification_token(self, user_id: int, request_type: str) -> str:
        """生成驗證令牌"""
        content = f"{user_id}:{request_type}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()

class DataRetentionManager:
    """資料保留管理器"""
    
    def __init__(self, db_session, data_service):
        self.db = db_session
        self.data_service = data_service
        
        # 資料保留政策（天數）
        self.retention_policies = {
            DataCategory.AUDIO_DATA: 1095,  # 3年
            DataCategory.VIDEO_DATA: 1095,  # 3年
            DataCategory.USAGE_DATA: 730,   # 2年
            DataCategory.TECHNICAL_DATA: 365,  # 1年
            DataCategory.MARKETING_DATA: 1095,  # 3年（除非撤回同意）
        }
    
    async def check_retention_compliance(self) -> Dict:
        """檢查資料保留合規性"""
        compliance_report = {
            "checked_at": datetime.utcnow().isoformat(),
            "violations": [],
            "actions_taken": []
        }
        
        for category, retention_days in self.retention_policies.items():
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # 查找過期資料
            expired_logs = self.db.query(GDPRDataProcessingLog).filter(
                GDPRDataProcessingLog.data_category == category.value,
                GDPRDataProcessingLog.timestamp < cutoff_date
            ).all()
            
            if expired_logs:
                compliance_report["violations"].append({
                    "category": category.value,
                    "expired_count": len(expired_logs),
                    "cutoff_date": cutoff_date.isoformat()
                })
                
                # 執行清理動作
                await self._cleanup_expired_data(category, expired_logs)
                compliance_report["actions_taken"].append({
                    "category": category.value,
                    "cleaned_records": len(expired_logs)
                })
        
        return compliance_report
    
    async def _cleanup_expired_data(self, category: DataCategory, expired_logs: List):
        """清理過期資料"""
        try:
            for log in expired_logs:
                if category == DataCategory.AUDIO_DATA:
                    await self.data_service.delete_expired_audio_files(log.user_id, log.timestamp)
                elif category == DataCategory.VIDEO_DATA:
                    await self.data_service.delete_expired_video_files(log.user_id, log.timestamp)
                elif category == DataCategory.USAGE_DATA:
                    await self.data_service.anonymize_expired_usage_data(log.user_id, log.timestamp)
                
                # 刪除處理日誌記錄
                self.db.delete(log)
            
            await self.db.commit()
            logger.info(f"Cleaned up {len(expired_logs)} expired records for {category.value}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            await self.db.rollback()

# 使用範例
async def example_usage():
    """GDPR 合規性使用範例"""
    
    # 初始化資料庫會話
    # db_session = get_db_session()
    
    # 初始化 GDPR 管理器
    # compliance_manager = GDPRComplianceManager(db_session)
    
    # 記錄用戶同意
    consent = ConsentRecord(
        user_id=123,
        purpose=DataProcessingPurpose.SERVICE_PROVISION,
        categories=[DataCategory.PERSONAL_IDENTITY, DataCategory.AUDIO_DATA],
        granted_at=datetime.utcnow(),
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0..."
    )
    
    # await compliance_manager.record_consent(consent)
    
    # 記錄資料處理活動
    # await compliance_manager.log_data_processing(
    #     user_id=123,
    #     category=DataCategory.AUDIO_DATA,
    #     purpose=DataProcessingPurpose.SERVICE_PROVISION,
    #     legal_basis="consent",
    #     processor="audio-processing-service",
    #     retention_days=1095
    # )
    
    print("GDPR compliance example completed")

if __name__ == "__main__":
    asyncio.run(example_usage())