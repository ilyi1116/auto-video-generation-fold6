"""
創業者模式自動影片生成工作流程引擎
專為創業者自動化內容生成和獲利優化設計

核心功能：
1. 自動趨勢分析和關鍵字選擇
2. 腳本生成和內容最佳化
3. 多媒體資產生成（圖像、語音、影片）
4. 平台優化和自動發布
5. 成本控制和 ROI 追蹤
"""

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """工作流程階段枚舉"""

    INITIALIZATION = "initialization"
    TREND_ANALYSIS = "trend_analysis"
    KEYWORD_SELECTION = "keyword_selection"
    SCRIPT_GENERATION = "script_generation"
    ASSET_GENERATION = "asset_generation"
    VIDEO_COMPOSITION = "video_composition"
    PLATFORM_OPTIMIZATION = "platform_optimization"
    PUBLISHING = "publishing"
    ANALYTICS_TRACKING = "analytics_tracking"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    """工作流程狀態枚舉"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EntrepreneurWorkflowConfig:
    """創業者工作流程配置"""

    # 內容設定
    daily_video_count: int = 3
    target_categories: List[str] = field(
        default_factory=lambda: ["technology", "entertainment", "lifestyle"]
    )
    target_platforms: List[str] = field(
        default_factory=lambda: ["tiktok", "youtube-shorts"]
    )
    video_duration: int = 30  # 秒
    language: str = "zh-TW"

    # 品質控制
    min_trend_score: float = 0.7
    content_quality_threshold: float = 0.8
    monetization_threshold: float = 0.6

    # 成本控制
    daily_budget: float = 10.0
    cost_per_video_limit: float = 5.0
    stop_on_budget_exceeded: bool = True

    # 時間控制
    operating_hours: Dict[str, str] = field(
        default_factory=lambda: {"start": "09:00", "end": "18:00"}
    )
    max_workflow_duration: int = 1800  # 30分鐘

    # 發布設定
    auto_publish: bool = False
    scheduled_publishing: bool = True
    optimal_publishing_times: List[str] = field(
        default_factory=lambda: ["10:00", "14:00", "18:00"]
    )

    # 進階設定
    retry_attempts: int = 3
    parallel_workflows: int = 2
    quality_check_enabled: bool = True


@dataclass
class WorkflowMetrics:
    """工作流程指標"""

    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_duration: Optional[timedelta] = None
    stage_durations: Dict[str, float] = field(default_factory=dict)
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    total_cost: float = 0.0
    success_rate: float = 0.0
    quality_score: float = 0.0
    monetization_potential: float = 0.0


@dataclass
class GeneratedAssets:
    """生成的資產"""

    script: Optional[str] = None
    images: List[str] = field(default_factory=list)
    audio_file: Optional[str] = None
    video_file: Optional[str] = None
    thumbnail: Optional[str] = None
    captions: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntrepreneurWorkflowRequest:
    """創業者工作流程請求"""

    user_id: str
    workflow_type: str = "entrepreneur_auto"
    config: EntrepreneurWorkflowConfig = field(
        default_factory=EntrepreneurWorkflowConfig
    )
    priority: int = 1  # 1=高, 2=中, 3=低
    tags: List[str] = field(default_factory=list)
    custom_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntrepreneurWorkflowResult:
    """創業者工作流程結果"""

    workflow_id: str
    request: EntrepreneurWorkflowRequest
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_stage: WorkflowStage = WorkflowStage.INITIALIZATION
    progress_percentage: int = 0
    estimated_completion: Optional[datetime] = None
    generated_assets: GeneratedAssets = field(default_factory=GeneratedAssets)
    metrics: WorkflowMetrics = field(default_factory=WorkflowMetrics)
    error_message: Optional[str] = None
    stage_outputs: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class EntrepreneurWorkflowEngine:
    """創業者模式工作流程引擎"""

    def __init__(self):
        self.workflows: Dict[str, EntrepreneurWorkflowResult] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        self.stage_handlers: Dict[WorkflowStage, Callable] = {}
        self.daily_stats = {
            "videos_generated": 0,
            "total_cost": 0.0,
            "success_count": 0,
            "failure_count": 0,
        }

        # 註冊階段處理器
        self._register_stage_handlers()

        logger.info("創業者工作流程引擎已初始化")

    def _register_stage_handlers(self):
        """註冊各階段處理器"""
        self.stage_handlers = {
            WorkflowStage.INITIALIZATION: self._handle_initialization,
            WorkflowStage.TREND_ANALYSIS: self._handle_trend_analysis,
            WorkflowStage.KEYWORD_SELECTION: self._handle_keyword_selection,
            WorkflowStage.SCRIPT_GENERATION: self._handle_script_generation,
            WorkflowStage.ASSET_GENERATION: self._handle_asset_generation,
            WorkflowStage.VIDEO_COMPOSITION: self._handle_video_composition,
            WorkflowStage.PLATFORM_OPTIMIZATION: self._handle_platform_optimization,
            WorkflowStage.PUBLISHING: self._handle_publishing,
            WorkflowStage.ANALYTICS_TRACKING: self._handle_analytics_tracking,
        }

    async def create_workflow(
        self, request: EntrepreneurWorkflowRequest
    ) -> str:
        """創建新的工作流程"""
        try:
            workflow_id = str(uuid.uuid4())

            # 預估完成時間
            estimated_duration = request.config.max_workflow_duration
            estimated_completion = datetime.utcnow() + timedelta(
                seconds=estimated_duration
            )

            result = EntrepreneurWorkflowResult(
                workflow_id=workflow_id,
                request=request,
                estimated_completion=estimated_completion,
            )

            self.workflows[workflow_id] = result

            logger.info(f"創建創業者工作流程: {workflow_id}")

            return workflow_id

        except Exception as e:
            logger.error(f"創建工作流程失敗: {e}")
            raise

    async def execute_workflow(self, workflow_id: str) -> None:
        """執行工作流程（異步）"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流程不存在: {workflow_id}")

        # 檢查是否已在執行
        if workflow_id in self.running_workflows:
            logger.warning(f"工作流程已在執行中: {workflow_id}")
            return

        # 創建異步任務
        task = asyncio.create_task(self._execute_workflow_async(workflow_id))
        self.running_workflows[workflow_id] = task

        try:
            await task
        finally:
            # 清理執行中的任務
            if workflow_id in self.running_workflows:
                del self.running_workflows[workflow_id]

    async def _execute_workflow_async(self, workflow_id: str) -> None:
        """異步執行工作流程"""
        result = self.workflows[workflow_id]

        try:
            result.status = WorkflowStatus.RUNNING
            result.metrics.start_time = datetime.utcnow()

            # 執行各個階段
            stages = [
                WorkflowStage.INITIALIZATION,
                WorkflowStage.TREND_ANALYSIS,
                WorkflowStage.KEYWORD_SELECTION,
                WorkflowStage.SCRIPT_GENERATION,
                WorkflowStage.ASSET_GENERATION,
                WorkflowStage.VIDEO_COMPOSITION,
                WorkflowStage.PLATFORM_OPTIMIZATION,
            ]

            # 根據配置決定是否包含發布階段
            if result.request.config.auto_publish:
                stages.append(WorkflowStage.PUBLISHING)

            stages.append(WorkflowStage.ANALYTICS_TRACKING)

            total_stages = len(stages)

            for i, stage in enumerate(stages):
                result.current_stage = stage
                result.progress_percentage = int((i / total_stages) * 100)
                result.updated_at = datetime.utcnow()

                logger.info(
                    f"執行階段 {stage.value} - 工作流程: {workflow_id}"
                )

                stage_start_time = datetime.utcnow()

                # 執行階段處理器
                if stage in self.stage_handlers:
                    await self.stage_handlers[stage](result)
                else:
                    logger.warning(f"未找到階段處理器: {stage.value}")

                # 記錄階段執行時間
                stage_duration = (
                    datetime.utcnow() - stage_start_time
                ).total_seconds()
                result.metrics.stage_durations[stage.value] = stage_duration

                # 檢查是否被取消
                if result.status == WorkflowStatus.CANCELLED:
                    logger.info(f"工作流程已被取消: {workflow_id}")
                    return

                # 檢查預算限制
                if result.request.config.stop_on_budget_exceeded:
                    if (
                        result.metrics.total_cost
                        > result.request.config.daily_budget
                    ):
                        result.status = WorkflowStatus.FAILED
                        result.error_message = "超出預算限制"
                        logger.warning(f"工作流程超出預算: {workflow_id}")
                        return

            # 工作流程完成
            result.status = WorkflowStatus.COMPLETED
            result.current_stage = WorkflowStage.COMPLETED
            result.progress_percentage = 100
            result.metrics.end_time = datetime.utcnow()
            result.metrics.total_duration = (
                result.metrics.end_time - result.metrics.start_time
            )

            # 更新統計
            self.daily_stats["videos_generated"] += 1
            self.daily_stats["total_cost"] += result.metrics.total_cost
            self.daily_stats["success_count"] += 1

            logger.info(f"工作流程完成: {workflow_id}")

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.current_stage = WorkflowStage.FAILED
            result.error_message = str(e)
            result.metrics.end_time = datetime.utcnow()

            self.daily_stats["failure_count"] += 1

            logger.error(f"工作流程執行失敗: {workflow_id} - {e}")

    async def _handle_initialization(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理初始化階段"""
        try:
            # 驗證配置
            config = result.request.config

            # 檢查每日限制
            if (
                self.daily_stats["videos_generated"]
                >= config.daily_video_count
            ):
                raise Exception("已達每日影片生成限制")

            # 檢查預算
            if self.daily_stats["total_cost"] >= config.daily_budget:
                raise Exception("已達每日預算限制")

            # 初始化資產結構
            result.generated_assets = GeneratedAssets()

            # 記錄初始化信息
            result.stage_outputs["initialization"] = {
                "config_validated": True,
                "daily_quota_available": config.daily_video_count
                - self.daily_stats["videos_generated"],
                "budget_remaining": config.daily_budget
                - self.daily_stats["total_cost"],
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"初始化完成 - 工作流程: {result.workflow_id}")

        except Exception as e:
            logger.error(f"初始化階段失敗: {e}")
            raise

    async def _handle_trend_analysis(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理趨勢分析階段"""
        try:
            # 模擬趨勢分析 API 調用
            await asyncio.sleep(2)  # 模擬 API 延遲

            # 模擬獲取熱門趨勢
            trending_topics = [
                {
                    "keyword": "AI 自動化工具",
                    "category": "technology",
                    "trend_score": 0.85,
                    "monetization_potential": 0.9,
                    "competition_level": "medium",
                },
                {
                    "keyword": "短影音創作技巧",
                    "category": "entertainment",
                    "trend_score": 0.78,
                    "monetization_potential": 0.85,
                    "competition_level": "low",
                },
                {
                    "keyword": "居家工作效率",
                    "category": "lifestyle",
                    "trend_score": 0.72,
                    "monetization_potential": 0.7,
                    "competition_level": "medium",
                },
            ]

            # 篩選符合條件的趨勢
            qualified_trends = [
                trend
                for trend in trending_topics
                if trend["trend_score"]
                >= result.request.config.min_trend_score
                and trend["monetization_potential"]
                >= result.request.config.monetization_threshold
            ]

            result.stage_outputs["trend_analysis"] = {
                "total_trends_analyzed": len(trending_topics),
                "qualified_trends": qualified_trends,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

            # 估算成本
            api_cost = 0.002  # $0.002 for trend analysis API
            result.metrics.cost_breakdown["trend_analysis"] = api_cost
            result.metrics.total_cost += api_cost

            logger.info(
                f"趨勢分析完成，找到 {len(qualified_trends)} 個合格趨勢"
            )

        except Exception as e:
            logger.error(f"趨勢分析階段失敗: {e}")
            raise

    async def _handle_keyword_selection(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理關鍵字選擇階段"""
        try:
            qualified_trends = result.stage_outputs["trend_analysis"][
                "qualified_trends"
            ]

            if not qualified_trends:
                raise Exception("沒有符合條件的趨勢關鍵字")

            # 選擇最佳關鍵字（按獲利潛力排序）
            selected_trend = max(
                qualified_trends, key=lambda x: x["monetization_potential"]
            )

            result.stage_outputs["keyword_selection"] = {
                "selected_keyword": selected_trend["keyword"],
                "selected_category": selected_trend["category"],
                "trend_score": selected_trend["trend_score"],
                "monetization_potential": selected_trend[
                    "monetization_potential"
                ],
                "competition_level": selected_trend["competition_level"],
                "selection_timestamp": datetime.utcnow().isoformat(),
            }

            result.metrics.monetization_potential = selected_trend[
                "monetization_potential"
            ]

            logger.info(f"選擇關鍵字: {selected_trend['keyword']}")

        except Exception as e:
            logger.error(f"關鍵字選擇階段失敗: {e}")
            raise

    async def _handle_script_generation(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理腳本生成階段"""
        try:
            keyword_data = result.stage_outputs["keyword_selection"]
            keyword = keyword_data["selected_keyword"]
            category = keyword_data["selected_category"]

            # 模擬 AI 腳本生成
            await asyncio.sleep(3)  # 模擬 AI API 延遲

            # 生成腳本內容
            script_templates = {
                "technology": f"🔥 {keyword} \
                    正在科技界掀起革命！想知道它如何改變我們的未來嗎？這個視頻將帶你深入了解最新技術趨勢，讓你走在時代前端！",
                "entertainment": f"✨ 最新熱門話題 {keyword} \
                    來了！大家都在討論的內容，你還沒跟上嗎？讓我們一起探索這個引爆全網的精彩內容！",
                "lifestyle": f"🌟 {keyword} \
                    正在改變我們的生活方式！想要提升生活品質嗎？這些實用技巧和建議，絕對讓你的日常更加精彩！",
            }

            script = script_templates.get(
                category, f"探索 {keyword} 的奧秘，發現更多精彩內容！"
            )

            # 生成相關標籤
            hashtags = [
                f"#{keyword.replace(' ', '')}",
                f"#{category}",
                "#熱門趋势",
                "#必看内容",
                "#涨知识",
            ]

            result.generated_assets.script = script
            result.generated_assets.hashtags = hashtags

            result.stage_outputs["script_generation"] = {
                "script_length": len(script),
                "hashtags_count": len(hashtags),
                "quality_score": 0.85,  # 模擬品質分數
                "generation_timestamp": datetime.utcnow().isoformat(),
            }

            # 估算成本（基於 tokens）
            estimated_tokens = len(script) // 4  # 粗略估算
            script_cost = estimated_tokens * 0.000002  # GPT-3.5 pricing
            result.metrics.cost_breakdown["script_generation"] = script_cost
            result.metrics.total_cost += script_cost

            result.metrics.quality_score = 0.85

            logger.info(f"腳本生成完成，長度: {len(script)} 字符")

        except Exception as e:
            logger.error(f"腳本生成階段失敗: {e}")
            raise

    async def _handle_asset_generation(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理資產生成階段（圖像、語音）"""
        try:
            keyword_data = result.stage_outputs["keyword_selection"]
            keyword = keyword_data["selected_keyword"]

            # 模擬並行生成圖像和語音
            image_task = self._generate_images(keyword, result)
            audio_task = self._generate_audio(
                result.generated_assets.script, result
            )

            await asyncio.gather(image_task, audio_task)

            result.stage_outputs["asset_generation"] = {
                "images_generated": len(result.generated_assets.images),
                "audio_generated": result.generated_assets.audio_file
                is not None,
                "generation_timestamp": datetime.utcnow().isoformat(),
            }

            logger.info("多媒體資產生成完成")

        except Exception as e:
            logger.error(f"資產生成階段失敗: {e}")
            raise

    async def _generate_images(
        self, keyword: str, result: EntrepreneurWorkflowResult
    ) -> None:
        """生成圖像資產"""
        try:
            # 模擬圖像生成 API
            await asyncio.sleep(5)  # 模擬生成時間

            # 生成 3 張圖像
            images = []
            for i in range(3):
                image_url = f"https://generated-images.example \
                    .com/{keyword}_{i + 1}_{result.workflow_id}.jpg"
                images.append(image_url)

            result.generated_assets.images = images

            # 估算圖像生成成本
            image_cost = 3 * 0.04  # Stable Diffusion 估算價格
            result.metrics.cost_breakdown["image_generation"] = image_cost
            result.metrics.total_cost += image_cost

            logger.info(f"生成 {len(images)} 張圖像")

        except Exception as e:
            logger.error(f"圖像生成失敗: {e}")
            raise

    async def _generate_audio(
        self, script: str, result: EntrepreneurWorkflowResult
    ) -> None:
        """生成語音資產"""
        try:
            # 模擬語音合成 API
            await asyncio.sleep(4)  # 模擬生成時間

            audio_url = f"https://generated-audio.example \
                .com/audio_{result.workflow_id}.mp3"
            result.generated_assets.audio_file = audio_url

            # 估算語音合成成本
            character_count = len(script)
            audio_cost = character_count * 0.000015  # ElevenLabs 估算價格
            result.metrics.cost_breakdown["audio_generation"] = audio_cost
            result.metrics.total_cost += audio_cost

            logger.info(f"生成語音檔案，字符數: {character_count}")

        except Exception as e:
            logger.error(f"語音生成失敗: {e}")
            raise

    async def _handle_video_composition(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理影片合成階段"""
        try:
            # 模擬影片合成
            await asyncio.sleep(6)  # 模擬合成時間

            video_url = f"https://generated-videos.example \
                .com/video_{result.workflow_id}.mp4"
            thumbnail_url = f"https://generated-videos.example \
                .com/thumb_{result.workflow_id}.jpg"

            result.generated_assets.video_file = video_url
            result.generated_assets.thumbnail = thumbnail_url

            # 生成字幕
            result.generated_assets.captions = result.generated_assets.script

            result.stage_outputs["video_composition"] = {
                "video_duration": result.request.config.video_duration,
                "video_url": video_url,
                "thumbnail_url": thumbnail_url,
                "composition_timestamp": datetime.utcnow().isoformat(),
            }

            # 估算影片處理成本
            video_cost = 0.05  # 影片處理估算成本
            result.metrics.cost_breakdown["video_composition"] = video_cost
            result.metrics.total_cost += video_cost

            logger.info("影片合成完成")

        except Exception as e:
            logger.error(f"影片合成階段失敗: {e}")
            raise

    async def _handle_platform_optimization(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理平台優化階段"""
        try:
            platforms = result.request.config.target_platforms

            platform_optimizations = {}

            for platform in platforms:
                optimization = await self._optimize_for_platform(
                    platform, result
                )
                platform_optimizations[platform] = optimization

            result.stage_outputs["platform_optimization"] = {
                "optimized_platforms": list(platforms),
                "optimizations": platform_optimizations,
                "optimization_timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"平台優化完成，覆蓋 {len(platforms)} 個平台")

        except Exception as e:
            logger.error(f"平台優化階段失敗: {e}")
            raise

    async def _optimize_for_platform(
        self, platform: str, result: EntrepreneurWorkflowResult
    ) -> Dict[str, Any]:
        """為特定平台優化內容"""

        platform_specs = {
            "tiktok": {
                "aspect_ratio": "9:16",
                "max_duration": 60,
                "hashtag_limit": 10,
                "title_length": 150,
            },
            "youtube-shorts": {
                "aspect_ratio": "9:16",
                "max_duration": 60,
                "hashtag_limit": 15,
                "title_length": 100,
            },
            "instagram-reels": {
                "aspect_ratio": "9:16",
                "max_duration": 90,
                "hashtag_limit": 30,
                "title_length": 125,
            },
        }

        specs = platform_specs.get(platform, platform_specs["tiktok"])

        # 調整標題和標籤
        keyword_data = result.stage_outputs["keyword_selection"]
        title = f"{keyword_data['selected_keyword']} - 必看趨勢解析"

        hashtags = result.generated_assets.hashtags[: specs["hashtag_limit"]]

        return {
            "platform": platform,
            "title": title[: specs["title_length"]],
            "hashtags": hashtags,
            "aspect_ratio": specs["aspect_ratio"],
            "duration": min(
                result.request.config.video_duration, specs["max_duration"]
            ),
        }

    async def _handle_publishing(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理發布階段"""
        if not result.request.config.auto_publish:
            return

        try:
            platforms = result.request.config.target_platforms
            published_platforms = []

            for platform in platforms:
                # 模擬發布 API 調用
                await asyncio.sleep(2)

                # 模擬發布成功
                published_platforms.append(platform)
                logger.info(f"成功發布到 {platform}")

            result.stage_outputs["publishing"] = {
                "published_platforms": published_platforms,
                "publishing_timestamp": datetime.utcnow().isoformat(),
                "auto_published": True,
            }

        except Exception as e:
            logger.error(f"發布階段失敗: {e}")
            # 發布失敗不影響整個工作流程
            result.stage_outputs["publishing"] = {
                "published_platforms": [],
                "error": str(e),
                "auto_published": False,
            }

    async def _handle_analytics_tracking(
        self, result: EntrepreneurWorkflowResult
    ) -> None:
        """處理分析追蹤階段"""
        try:
            # 設置分析追蹤
            tracking_data = {
                "workflow_id": result.workflow_id,
                "keyword": result.stage_outputs["keyword_selection"][
                    "selected_keyword"
                ],
                "platforms": result.request.config.target_platforms,
                "tracking_start": datetime.utcnow().isoformat(),
                "metrics_to_track": [
                    "views",
                    "likes",
                    "shares",
                    "comments",
                    "ctr",
                    "revenue",
                ],
            }

            result.stage_outputs["analytics_tracking"] = tracking_data

            logger.info("分析追蹤設置完成")

        except Exception as e:
            logger.error(f"分析追蹤階段失敗: {e}")
            raise

    def get_workflow_status(
        self, workflow_id: str
    ) -> Optional[EntrepreneurWorkflowResult]:
        """獲取工作流程狀態"""
        return self.workflows.get(workflow_id)

    def get_daily_stats(self) -> Dict[str, Any]:
        """獲取每日統計"""
        return {
            **self.daily_stats,
            "success_rate": (
                self.daily_stats["success_count"]
                / max(
                    self.daily_stats["success_count"]
                    + self.daily_stats["failure_count"],
                    1,
                )
            )
            * 100,
            "average_cost_per_video": (
                self.daily_stats["total_cost"]
                / max(self.daily_stats["videos_generated"], 1)
            ),
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流程"""
        if workflow_id not in self.workflows:
            return False

        result = self.workflows[workflow_id]
        result.status = WorkflowStatus.CANCELLED
        result.updated_at = datetime.utcnow()

        # 取消執行中的任務
        if workflow_id in self.running_workflows:
            task = self.running_workflows[workflow_id]
            task.cancel()
            del self.running_workflows[workflow_id]

        logger.info(f"工作流程已取消: {workflow_id}")
        return True

    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """清理已完成的工作流程"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        workflows_to_remove = [
            workflow_id
            for workflow_id, result in self.workflows.items()
            if result.status
            in [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.CANCELLED,
            ]
            and result.updated_at < cutoff_time
        ]

        for workflow_id in workflows_to_remove:
            del self.workflows[workflow_id]

        logger.info(f"清理了 {len(workflows_to_remove)} 個舊工作流程")
        return len(workflows_to_remove)
