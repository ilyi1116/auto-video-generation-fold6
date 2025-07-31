"""
付費服務 - Stripe 整合
處理訂閱、付款和使用量管理
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
import stripe
import os
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 FastAPI
app = FastAPI(
    title="Auto Video Payment Service",
    description="處理訂閱和付費功能",
    version="1.0.0",
)

# 設定 Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

# 安全驗證
security = HTTPBearer()

# 訂閱方案配置
SUBSCRIPTION_PLANS = {
    "standard": {
        "price_id": "price_standard_monthly",
        "name": "Standard",
        "price": 29,
        "video_limit": 50,
        "features": ["basic_ai", "community_support"],
    },
    "professional": {
        "price_id": "price_professional_monthly",
        "name": "Professional",
        "price": 99,
        "video_limit": 200,
        "features": ["advanced_ai", "priority_support", "hd_output"],
    },
    "enterprise": {
        "price_id": "price_enterprise_monthly",
        "name": "Enterprise",
        "price": 299,
        "video_limit": -1,  # 無限制
        "features": ["all_features", "dedicated_support", "api_access"],
    },
}


# 資料模型
class CheckoutSessionRequest(BaseModel):
    plan_id: str = Field(..., description="訂閱方案ID")
    user_id: str = Field(..., description="用戶ID")
    success_url: str = Field(..., description="成功頁面URL")
    cancel_url: str = Field(..., description="取消頁面URL")


class SubscriptionStatus(BaseModel):
    status: str
    plan_id: Optional[str] = None
    current_period_end: Optional[datetime] = None
    videos_used: int = 0
    video_limit: int = 0
    can_create_video: bool = False


class UsageLimits(BaseModel):
    videos_used: int
    video_limit: int
    can_create_video: bool
    reset_date: datetime


# 驗證令牌（簡化版本）
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """驗證 JWT 令牌"""
    # 這裡應該實現完整的 JWT 驗證
    # 暫時返回模擬用戶
    return {"id": "user_123", "email": "user@example.com"}


# 創建結帳會話
@app.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutSessionRequest, current_user: dict = Depends(verify_token)
):
    """創建 Stripe 結帳會話"""
    try:
        # 驗證方案
        if request.plan_id not in SUBSCRIPTION_PLANS:
            raise HTTPException(status_code=400, detail="無效的訂閱方案")

        plan = SUBSCRIPTION_PLANS[request.plan_id]

        # 創建或獲取客戶
        customer = await get_or_create_customer(current_user)

        # 創建結帳會話
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan["price_id"],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={"user_id": request.user_id, "plan_id": request.plan_id},
        )

        logger.info(f"創建結帳會話: {session.id} for user {request.user_id}")

        return {"session_id": session.id}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe 錯誤: {str(e)}")
        raise HTTPException(status_code=400, detail=f"付費處理錯誤: {str(e)}")
    except Exception as e:
        logger.error(f"創建結帳會話錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")


# 創建客戶管理會話
@app.post("/create-portal-session")
async def create_portal_session(current_user: dict = Depends(verify_token)):
    """創建客戶管理會話"""
    try:
        customer = await get_or_create_customer(current_user)

        session = stripe.billing_portal.Session.create(
            customer=customer.id, return_url="http://localhost:3000/dashboard"
        )

        return {"url": session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe 錯誤: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"無法創建管理會話: {str(e)}"
        )


# 獲取訂閱狀態
@app.get("/subscription-status", response_model=SubscriptionStatus)
async def get_subscription_status(current_user: dict = Depends(verify_token)):
    """獲取用戶訂閱狀態"""
    try:
        customer = await get_customer_by_user(current_user)

        if not customer:
            return SubscriptionStatus(
                status="inactive",
                videos_used=0,
                video_limit=3,  # 免費用戶限制
                can_create_video=True,
            )

        # 獲取活躍訂閱
        subscriptions = stripe.Subscription.list(
            customer=customer.id, status="active", limit=1
        )

        if not subscriptions.data:
            return SubscriptionStatus(
                status="inactive",
                videos_used=0,
                video_limit=3,
                can_create_video=True,
            )

        subscription = subscriptions.data[0]
        plan_id = get_plan_id_from_price(subscription.items.data[0].price.id)
        plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["standard"])

        # 獲取使用量（這裡需要實現實際的使用量查詢）
        videos_used = await get_user_video_usage(current_user["id"])

        return SubscriptionStatus(
            status="active",
            plan_id=plan_id,
            current_period_end=datetime.fromtimestamp(
                subscription.current_period_end
            ),
            videos_used=videos_used,
            video_limit=plan["video_limit"],
            can_create_video=videos_used < plan["video_limit"]
            or plan["video_limit"] == -1,
        )

    except Exception as e:
        logger.error(f"獲取訂閱狀態錯誤: {str(e)}")
        return SubscriptionStatus(
            status="error",
            videos_used=0,
            video_limit=0,
            can_create_video=False,
        )


# 獲取使用量限制
@app.get("/usage-limits", response_model=UsageLimits)
async def get_usage_limits(current_user: dict = Depends(verify_token)):
    """獲取用戶使用量限制"""
    try:
        subscription_status = await get_subscription_status(current_user)

        # 計算重置日期（每月1號）
        now = datetime.now()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)

        return UsageLimits(
            videos_used=subscription_status.videos_used,
            video_limit=subscription_status.video_limit,
            can_create_video=subscription_status.can_create_video,
            reset_date=reset_date,
        )

    except Exception as e:
        logger.error(f"獲取使用量限制錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail="無法獲取使用量資訊")


# Webhook 處理
@app.post("/webhook")
async def handle_stripe_webhook(request):
    """處理 Stripe Webhook"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )

        logger.info(f"收到 Webhook 事件: {event['type']}")

        # 處理不同類型的事件
        if event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"])
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"])
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event["data"]["object"])
        elif event["type"] == "invoice.payment_succeeded":
            await handle_payment_succeeded(event["data"]["object"])
        elif event["type"] == "invoice.payment_failed":
            await handle_payment_failed(event["data"]["object"])

        return {"status": "success"}

    except ValueError as e:
        logger.error(f"無效的載荷: {str(e)}")
        raise HTTPException(status_code=400, detail="無效的載荷")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"無效的簽名: {str(e)}")
        raise HTTPException(status_code=400, detail="無效的簽名")


# 輔助函數
async def get_or_create_customer(user: dict):
    """獲取或創建 Stripe 客戶"""
    # 首先嘗試根據 email 查找現有客戶
    customers = stripe.Customer.list(email=user["email"], limit=1)

    if customers.data:
        return customers.data[0]

    # 創建新客戶
    customer = stripe.Customer.create(
        email=user["email"], metadata={"user_id": user["id"]}
    )

    return customer


async def get_customer_by_user(user: dict):
    """根據用戶獲取 Stripe 客戶"""
    customers = stripe.Customer.list(email=user["email"], limit=1)
    return customers.data[0] if customers.data else None


def get_plan_id_from_price(price_id: str) -> str:
    """根據價格ID獲取方案ID"""
    for plan_id, plan in SUBSCRIPTION_PLANS.items():
        if plan["price_id"] == price_id:
            return plan_id
    return "standard"


async def get_user_video_usage(user_id: str) -> int:
    """獲取用戶本月影片使用量"""
    # 這裡需要實現實際的資料庫查詢
    # 暫時返回模擬數據
    return 15


# Webhook 事件處理函數
async def handle_checkout_completed(session):
    """處理結帳完成事件"""
    user_id = session["metadata"]["user_id"]
    plan_id = session["metadata"]["plan_id"]

    logger.info(f"用戶 {user_id} 成功訂閱 {plan_id} 方案")

    # 這裡應該更新用戶的訂閱狀態到資料庫
    # await update_user_subscription(user_id, plan_id, 'active')


async def handle_subscription_updated(subscription):
    """處理訂閱更新事件"""
    customer_id = subscription["customer"]
    status = subscription["status"]

    logger.info(f"客戶 {customer_id} 的訂閱狀態更新為 {status}")


async def handle_subscription_deleted(subscription):
    """處理訂閱取消事件"""
    customer_id = subscription["customer"]

    logger.info(f"客戶 {customer_id} 的訂閱已取消")


async def handle_payment_succeeded(invoice):
    """處理付款成功事件"""
    customer_id = invoice["customer"]
    amount = invoice["amount_paid"]

    logger.info(f"客戶 {customer_id} 付款成功，金額: {amount}")


async def handle_payment_failed(invoice):
    """處理付款失敗事件"""
    customer_id = invoice["customer"]

    logger.info(f"客戶 {customer_id} 付款失敗")


# 健康檢查
@app.get("/health")
async def health_check():
    """服務健康檢查"""
    return {"status": "healthy", "service": "payment-service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8009)
