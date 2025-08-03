from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid

from .models import (
    AIProvider, CrawlerConfig, SocialTrendConfig, TrendingKeyword,
    SystemLog, AdminUser, CrawlerResult, AIProviderType, CrawlerStatus,
    ScheduleType, SocialPlatform, TrendTimeframe, LogLevel
)
from .schemas import (
    AIProviderCreate, AIProviderUpdate, CrawlerConfigCreate, CrawlerConfigUpdate,
    SocialTrendConfigCreate, SocialTrendConfigUpdate, TrendingKeywordCreate,
    SystemLogCreate, AdminUserCreate, AdminUserUpdate, LogQueryParams,
    TrendQueryParams, PaginationParams
)
from .security import hash_password, verify_password

logger = logging.getLogger(__name__)


class CRUDBase:
    """基礎 CRUD 操作類"""
    
    def __init__(self, model):
        self.model = model
    
    def get(self, db: Session, id: int):
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100):
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: Dict[str, Any]):
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj, obj_in: Dict[str, Any]):
        for field, value in obj_in.items():
            if value is not None:
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: int):
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class CRUDAIProvider(CRUDBase):
    """AI Provider CRUD 操作"""
    
    def __init__(self):
        super().__init__(AIProvider)
    
    def create_ai_provider(self, db: Session, *, provider_in: AIProviderCreate) -> AIProvider:
        # 檢查名稱是否已存在
        existing = db.query(AIProvider).filter(AIProvider.name == provider_in.name).first()
        if existing:
            raise ValueError(f"AI Provider '{provider_in.name}' 已存在")
        
        # 如果設為預設，取消其他預設設定
        if provider_in.is_default:
            db.query(AIProvider).filter(AIProvider.is_default == True).update(
                {"is_default": False}
            )
        
        # 加密 API Key (這裡應該使用實際的加密函數)
        encrypted_api_key = self._encrypt_api_key(provider_in.api_key)
        
        provider_data = provider_in.dict()
        provider_data["api_key"] = encrypted_api_key
        
        return self.create(db, obj_in=provider_data)
    
    def update_ai_provider(self, db: Session, *, provider_id: int, provider_in: AIProviderUpdate) -> Optional[AIProvider]:
        provider = self.get(db, provider_id)
        if not provider:
            return None
        
        update_data = provider_in.dict(exclude_unset=True)
        
        # 檢查名稱衝突
        if "name" in update_data:
            existing = db.query(AIProvider).filter(
                and_(AIProvider.name == update_data["name"], AIProvider.id != provider_id)
            ).first()
            if existing:
                raise ValueError(f"AI Provider '{update_data['name']}' 已存在")
        
        # 處理預設設定
        if update_data.get("is_default"):
            db.query(AIProvider).filter(AIProvider.is_default == True).update(
                {"is_default": False}
            )
        
        # 加密 API Key
        if "api_key" in update_data:
            update_data["api_key"] = self._encrypt_api_key(update_data["api_key"])
        
        return self.update(db, db_obj=provider, obj_in=update_data)
    
    def get_active_providers(self, db: Session) -> List[AIProvider]:
        return db.query(AIProvider).filter(AIProvider.is_active == True).all()
    
    def get_default_provider(self, db: Session) -> Optional[AIProvider]:
        return db.query(AIProvider).filter(AIProvider.is_default == True).first()
    
    def get_by_type(self, db: Session, provider_type: AIProviderType) -> List[AIProvider]:
        return db.query(AIProvider).filter(AIProvider.provider_type == provider_type).all()
    
    def test_provider_connection(self, db: Session, provider_id: int) -> bool:
        """測試 AI Provider 連接"""
        provider = self.get(db, provider_id)
        if not provider:
            return False
        
        # 這裡應該實現實際的連接測試邏輯
        # 根據不同的 provider_type 調用相應的 API
        try:
            # 模擬測試邏輯
            decrypted_api_key = self._decrypt_api_key(provider.api_key)
            # 實際測試代碼...
            return True
        except Exception as e:
            logger.error(f"測試 AI Provider {provider_id} 連接失敗: {e}")
            return False
    
    def _encrypt_api_key(self, api_key: str) -> str:
        # 實現 API Key 加密邏輯
        # 這裡應該使用 Fernet 或其他加密方法
        return api_key  # 暫時返回原值
    
    def _decrypt_api_key(self, encrypted_api_key: str) -> str:
        # 實現 API Key 解密邏輯
        return encrypted_api_key  # 暫時返回原值


class CRUDCrawlerConfig(CRUDBase):
    """爬蟲配置 CRUD 操作"""
    
    def __init__(self):
        super().__init__(CrawlerConfig)
    
    def create_crawler_config(self, db: Session, *, config_in: CrawlerConfigCreate) -> CrawlerConfig:
        # 檢查名稱是否已存在
        existing = db.query(CrawlerConfig).filter(CrawlerConfig.name == config_in.name).first()
        if existing:
            raise ValueError(f"爬蟲配置 '{config_in.name}' 已存在")
        
        # 計算下次運行時間
        next_run_at = self._calculate_next_run(config_in.schedule_type, config_in.schedule_config)
        
        config_data = config_in.dict()
        config_data["next_run_at"] = next_run_at
        
        return self.create(db, obj_in=config_data)
    
    def update_crawler_config(self, db: Session, *, config_id: int, config_in: CrawlerConfigUpdate) -> Optional[CrawlerConfig]:
        config = self.get(db, config_id)
        if not config:
            return None
        
        update_data = config_in.dict(exclude_unset=True)
        
        # 檢查名稱衝突
        if "name" in update_data:
            existing = db.query(CrawlerConfig).filter(
                and_(CrawlerConfig.name == update_data["name"], CrawlerConfig.id != config_id)
            ).first()
            if existing:
                raise ValueError(f"爬蟲配置 '{update_data['name']}' 已存在")
        
        # 重新計算下次運行時間
        if "schedule_type" in update_data or "schedule_config" in update_data:
            schedule_type = update_data.get("schedule_type", config.schedule_type)
            schedule_config = update_data.get("schedule_config", config.schedule_config)
            update_data["next_run_at"] = self._calculate_next_run(schedule_type, schedule_config)
        
        return self.update(db, db_obj=config, obj_in=update_data)
    
    def get_active_configs(self, db: Session) -> List[CrawlerConfig]:
        return db.query(CrawlerConfig).filter(CrawlerConfig.status == CrawlerStatus.ACTIVE).all()
    
    def get_due_configs(self, db: Session, current_time: datetime = None) -> List[CrawlerConfig]:
        if current_time is None:
            current_time = datetime.utcnow()
        
        return db.query(CrawlerConfig).filter(
            and_(
                CrawlerConfig.status == CrawlerStatus.ACTIVE,
                CrawlerConfig.next_run_at <= current_time
            )
        ).all()
    
    def update_last_run(self, db: Session, config_id: int, run_time: datetime = None):
        if run_time is None:
            run_time = datetime.utcnow()
        
        config = self.get(db, config_id)
        if config:
            next_run_at = self._calculate_next_run(config.schedule_type, config.schedule_config, run_time)
            self.update(db, db_obj=config, obj_in={"last_run_at": run_time, "next_run_at": next_run_at})
    
    def _calculate_next_run(self, schedule_type: ScheduleType, schedule_config: Optional[Dict], 
                           from_time: datetime = None) -> Optional[datetime]:
        if from_time is None:
            from_time = datetime.utcnow()
        
        if schedule_type == ScheduleType.ONCE:
            return None
        elif schedule_type == ScheduleType.HOURLY:
            return from_time + timedelta(hours=1)
        elif schedule_type == ScheduleType.DAILY:
            return from_time + timedelta(days=1)
        elif schedule_type == ScheduleType.WEEKLY:
            return from_time + timedelta(weeks=1)
        elif schedule_type == ScheduleType.MONTHLY:
            return from_time + timedelta(days=30)
        elif schedule_type == ScheduleType.CUSTOM_CRON:
            # 這裡應該實現 cron 表達式解析
            # 暫時返回每小時運行
            return from_time + timedelta(hours=1)
        
        return None


class CRUDSocialTrendConfig(CRUDBase):
    """社交媒體趨勢配置 CRUD 操作"""
    
    def __init__(self):
        super().__init__(SocialTrendConfig)
    
    def create_trend_config(self, db: Session, *, config_in: SocialTrendConfigCreate) -> SocialTrendConfig:
        # 檢查平台和地區組合是否已存在
        existing = db.query(SocialTrendConfig).filter(
            and_(
                SocialTrendConfig.platform == config_in.platform,
                SocialTrendConfig.region == config_in.region
            )
        ).first()
        if existing:
            raise ValueError(f"{config_in.platform} 平台的 {config_in.region} 地區配置已存在")
        
        # 加密 API Key
        config_data = config_in.dict()
        if config_data.get("api_key"):
            config_data["api_key"] = self._encrypt_api_key(config_data["api_key"])
        
        return self.create(db, obj_in=config_data)
    
    def get_active_configs(self, db: Session) -> List[SocialTrendConfig]:
        return db.query(SocialTrendConfig).filter(SocialTrendConfig.is_active == True).all()
    
    def get_by_platform(self, db: Session, platform: SocialPlatform) -> List[SocialTrendConfig]:
        return db.query(SocialTrendConfig).filter(SocialTrendConfig.platform == platform).all()
    
    def _encrypt_api_key(self, api_key: str) -> str:
        return api_key  # 暫時返回原值


class CRUDTrendingKeyword(CRUDBase):
    """熱門關鍵字 CRUD 操作"""
    
    def __init__(self):
        super().__init__(TrendingKeyword)
    
    def create_trending_keywords(self, db: Session, *, keywords: List[TrendingKeywordCreate]) -> List[TrendingKeyword]:
        """批量創建熱門關鍵字"""
        results = []
        for keyword_data in keywords:
            keyword = self.create(db, obj_in=keyword_data.dict())
            results.append(keyword)
        return results
    
    def get_trending_keywords(self, db: Session, *, params: TrendQueryParams) -> tuple:
        query = db.query(TrendingKeyword)
        
        # 應用過濾條件
        if params.platform:
            query = query.filter(TrendingKeyword.platform == params.platform)
        if params.timeframe:
            query = query.filter(TrendingKeyword.timeframe == params.timeframe)
        if params.region:
            query = query.filter(TrendingKeyword.region == params.region)
        if params.category:
            query = query.filter(TrendingKeyword.category == params.category)
        if params.start_date:
            query = query.filter(TrendingKeyword.trend_date >= params.start_date)
        if params.end_date:
            query = query.filter(TrendingKeyword.trend_date <= params.end_date)
        
        # 計算總數
        total = query.count()
        
        # 應用分頁和排序
        keywords = query.order_by(desc(TrendingKeyword.trend_date), asc(TrendingKeyword.rank))\
                       .offset((params.page - 1) * params.size)\
                       .limit(params.size)\
                       .all()
        
        return keywords, total
    
    def get_top_keywords(self, db: Session, platform: SocialPlatform, 
                        timeframe: TrendTimeframe, limit: int = 10) -> List[TrendingKeyword]:
        """獲取指定平台和時間範圍的熱門關鍵字"""
        return db.query(TrendingKeyword)\
                 .filter(
                     and_(
                         TrendingKeyword.platform == platform,
                         TrendingKeyword.timeframe == timeframe
                     )
                 )\
                 .order_by(asc(TrendingKeyword.rank))\
                 .limit(limit)\
                 .all()


class CRUDSystemLog(CRUDBase):
    """系統日誌 CRUD 操作"""
    
    def __init__(self):
        super().__init__(SystemLog)
    
    def create_log(self, db: Session, *, log_in: SystemLogCreate) -> SystemLog:
        return self.create(db, obj_in=log_in.dict())
    
    def get_logs(self, db: Session, *, params: LogQueryParams) -> tuple:
        query = db.query(SystemLog)
        
        # 應用過濾條件
        if params.level:
            query = query.filter(SystemLog.level == params.level)
        if params.action:
            query = query.filter(SystemLog.action.ilike(f"%{params.action}%"))
        if params.resource_type:
            query = query.filter(SystemLog.resource_type == params.resource_type)
        if params.username:
            query = query.filter(SystemLog.username.ilike(f"%{params.username}%"))
        if params.start_date:
            query = query.filter(SystemLog.created_at >= params.start_date)
        if params.end_date:
            query = query.filter(SystemLog.created_at <= params.end_date)
        
        # 計算總數
        total = query.count()
        
        # 應用分頁和排序
        logs = query.order_by(desc(SystemLog.created_at))\
                   .offset((params.page - 1) * params.size)\
                   .limit(params.size)\
                   .all()
        
        return logs, total
    
    def get_dashboard_stats(self, db: Session) -> Dict[str, Any]:
        """獲取儀表板統計數據"""
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        stats = {
            "total_logs_today": db.query(SystemLog).filter(
                func.date(SystemLog.created_at) == today
            ).count(),
            "error_logs_today": db.query(SystemLog).filter(
                and_(
                    func.date(SystemLog.created_at) == today,
                    SystemLog.level.in_([LogLevel.ERROR, LogLevel.CRITICAL])
                )
            ).count(),
            "last_24h_activity": {}
        }
        
        # 獲取過去24小時的活動統計
        for i in range(24):
            hour_start = datetime.utcnow() - timedelta(hours=i+1)
            hour_end = datetime.utcnow() - timedelta(hours=i)
            count = db.query(SystemLog).filter(
                and_(
                    SystemLog.created_at >= hour_start,
                    SystemLog.created_at < hour_end
                )
            ).count()
            stats["last_24h_activity"][f"{i}h_ago"] = count
        
        return stats


class CRUDAdminUser(CRUDBase):
    """管理員用戶 CRUD 操作"""
    
    def __init__(self):
        super().__init__(AdminUser)
    
    def create_admin_user(self, db: Session, *, user_in: AdminUserCreate) -> AdminUser:
        # 檢查用戶名和郵箱是否已存在
        existing_username = db.query(AdminUser).filter(AdminUser.username == user_in.username).first()
        if existing_username:
            raise ValueError(f"用戶名 '{user_in.username}' 已存在")
        
        existing_email = db.query(AdminUser).filter(AdminUser.email == user_in.email).first()
        if existing_email:
            raise ValueError(f"郵箱 '{user_in.email}' 已存在")
        
        # 加密密碼
        hashed_password = hash_password(user_in.password)
        
        user_data = user_in.dict()
        user_data["hashed_password"] = hashed_password
        del user_data["password"]
        
        return self.create(db, obj_in=user_data)
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[AdminUser]:
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        # 更新登錄信息
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        db.commit()
        
        return user
    
    def get_by_username(self, db: Session, username: str) -> Optional[AdminUser]:
        return db.query(AdminUser).filter(AdminUser.username == username).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[AdminUser]:
        return db.query(AdminUser).filter(AdminUser.email == email).first()


# 實例化 CRUD 操作類
crud_ai_provider = CRUDAIProvider()
crud_crawler_config = CRUDCrawlerConfig()
crud_social_trend_config = CRUDSocialTrendConfig()
crud_trending_keyword = CRUDTrendingKeyword()
crud_system_log = CRUDSystemLog()
crud_admin_user = CRUDAdminUser()