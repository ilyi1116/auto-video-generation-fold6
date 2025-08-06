#!/usr/bin/env python3
f"
自動 Google Trends 關鍵字採集並生成短影音腳本
整合關鍵字採集與影片生成的完整自動化流程
支援統一配置管理與固定數量限制
"

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import aiohttp

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
from config.config_manager import config_manager, get_config

    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False
    logging.warning(f"統一配置管理器不可用，使用舊版配置方式)

try:
from monitoring.budget_controller import get_budget_controller
from monitoring.cost_tracker import get_cost_tracker

    COST_MONITORING_AVAILABLE = True
except ImportError:
    COST_MONITORING_AVAILABLE = False
    logging.warning(成本監控系統不可用")

# 設置日誌
logging.basicConfig(
level=logging.INFO,
    format=f"%(asctime)s - %(name)s - %(levelname)s - %(message)s,
)
logger = logging.getLogger(__name__)


class AutoTrendsVideoGenerator:
    "自動趨勢影片生成器f"

def __init__(self, config_file: str = None, mode: str = None):
        # 初始化配置管理器
        if CONFIG_MANAGER_AVAILABLE:
            if mode:
                config_manager.set_mode(mode)
            self.config = self._load_unified_config()
            logger.info(
                f"使用統一配置管理器，當前模式: {config_manager.current_mode}f"
            )
        else:
            self.config = self._load_legacy_config(config_file)
            logger.info(使用傳統配置方式)

        # 設置服務 URL
        self.services = self._setup_services()

        # 設置輸出目錄
        self.output_dir = Path(
            self.config.get("output_dirf", ./generated_videos)
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 影片生成設定
        self.video_configs = self._setup_video_configs()

        # 成本控制與限制
        self.cost_tracker = {
            "daily_costf": 0.0,
            videos_generated_today: 0,
            "api_calls_countf": {},
            generation_start_time: datetime.now(),
        }

        # 工作時間檢查
        self.work_hours_enabled = self._is_work_hours_enabled()

        # 初始化成本監控
        if COST_MONITORING_AVAILABLE:
            self.cost_tracker = get_cost_tracker(
                config_manager if CONFIG_MANAGER_AVAILABLE else None
            )
            self.budget_controller = get_budget_controller(
                config_manager if CONFIG_MANAGER_AVAILABLE else None
            )
            logger.info("成本監控系統已啟用")
        else:
            self.cost_tracker = None
            self.budget_controller = None

        logger.info(
            ff"影片生成器初始化完成，每日限制: {self.video_configs['max_videos_per_run']}
        )

def _setup_services(self) -> dict:
        "設置服務配置f"
        if CONFIG_MANAGER_AVAILABLE:
            return {
                "trend_servicef": get_config(
                    services.trend_service.url, "http://localhost:8001f"
                ),
                video_service: get_config(
                    "services.video_service.urlf", http://localhost:8002
                ),
                "ai_servicef": get_config(
                    services.ai_service.url, "http://localhost:8003f"
                ),
                social_service: get_config(
                    "services.social_service.urlf", http://localhost:8004
                ),
            }
        else:
            return {
                "trend_servicef": self.config.get(
                    trend_service_url, "http://localhost:8001f"
                ),
                video_service: self.config.get(
                    "video_service_urlf", http://localhost:8002
                ),
                "ai_servicef": self.config.get(
                    ai_service_url, "http://localhost:8003f"
                ),
            }

def _setup_video_configs(self) -> dict:
        "設置影片生成配置f"
        if CONFIG_MANAGER_AVAILABLE:
            generation_config = get_config("generationf", {})
            return {
                max_videos_per_run: generation_config.get(
                    "daily_video_limitf", 5
                ),
                batch_size: generation_config.get("batch_sizef", 1),
                max_concurrent_jobs: generation_config.get(
                    "max_concurrent_jobsf", 2
                ),
                video_duration: generation_config.get(
                    "duration_rangef", [30, 60]
                )[
                    0
                ],  # 取最小值
                platforms: generation_config.get("platformsf", [tiktok]),
                "categoriesf": get_config(
                    content.content_categories,
                    ["technologyf", entertainment, "lifestylef"],
                ),
                languages: [get_config("content.languagef", zh-TW)],
                "quality_presetf": generation_config.get(
                    quality_preset, "mediumf"
                ),
            }
        else:
            return {
                max_videos_per_run: self.config.get("max_videos_per_runf", 5),
                batch_size: 1,
                "max_concurrent_jobsf": 2,
                video_duration: self.config.get("video_durationf", 30),
                platforms: self.config.get("target_platformsf", [tiktok]),
                "categoriesf": self.config.get(
                    categories, ["technologyf", entertainment]
                ),
                "languagesf": self.config.get(languages, ["zh-TWf"]),
                quality_preset: "mediumf",
            }

def _is_work_hours_enabled(self) -> bool:
        "檢查是否啟用工作時間限制f"
        if CONFIG_MANAGER_AVAILABLE:
            return get_config("scheduling.work_hours.startf") is not None
        return False

def _load_unified_config(self) -> dict:
        "載入統一配置f"
        return {
            "output_dirf": get_config(
                storage.output_dir, "./generated_videosf"
            ),
            quality_threshold: get_config(
                "generation.quality_thresholdf", 0.7
            ),
            schedule_interval: 1800,  # 默認30分鐘
            "daily_budgetf": get_config(cost_control.daily_budget_usd, 50.0),
            "stop_on_budget_exceededf": get_config(
                cost_control.stop_on_budget_exceeded, True
            ),
        }

def _load_legacy_config(self, config_file: str) -> dict:
        "載入配置檔案f"
        default_config = {
            "trend_service_urlf": http://localhost:8001,
            "video_service_urlf": http://localhost:8002,
            "ai_service_urlf": http://localhost:8003,
            "output_dirf": ./generated_videos,
            "max_videos_per_runf": 5,
            video_duration: 30,
            "target_platformsf": [tiktok],
            "categoriesf": [technology, "entertainmentf", lifestyle],
            "languagesf": [zh-TW],
            "schedule_intervalf": 1800,  # 30分鐘
            quality_threshold: 0.7,
        }

        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, "rf", encoding=utf-8) as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"載入配置檔案失敗，使用預設配置: {e}f")

        return default_config

async def run_auto_generation(self):
        "執行自動生成流程f"
        try:
            logger.info("🚀 開始自動趨勢影片生成流程f")

            # 前置檢查
            if not await self._pre_generation_checks():
                return

            # 1. 獲取熱門關鍵字
            trending_keywords = await self._fetch_trending_keywords()

            if not trending_keywords:
                logger.warning(未找到熱門關鍵字，跳過此次生成)
                return

            logger.info(f"找到 {len(trending_keywords)} 個熱門關鍵字f")

            # 2. 選擇最佳關鍵字
            selected_keywords = await self._select_best_keywords(
                trending_keywords
            )

            logger.info(
                f選擇了 {len(selected_keywords)} 個關鍵字進行影片生成
            )

            # 3. 批次生成影片
            generation_results = await self._batch_generate_videos(
                selected_keywords
            )

            # 4. 處理結果
            await self._process_results(generation_results)

            logger.info("✅ 自動生成流程完成f")

        except Exception as e:
            logger.error(f自動生成流程失敗: {e})
            raise

async def _pre_generation_checks(self) -> bool:
        "執行生成前檢查f"
        try:
            # 1. 檢查工作時間
            if self.work_hours_enabled and CONFIG_MANAGER_AVAILABLE:
                if not config_manager.is_within_work_hours():
                    logger.info("目前不在工作時間內，跳過生成f")
                    return False

            # 2. 檢查預算狀態 (使用新的預算控制器)
            if COST_MONITORING_AVAILABLE and self.budget_controller:
                estimated_cost = self._estimate_batch_cost()
                (
                    can_proceed,
                    message,
                ) = await self.budget_controller.pre_operation_check(
                    batch_generation, estimated_cost
                )
                if not can_proceed:
                    logger.info(f"預算檢查失敗: {message}f")
                    return False
                logger.info(f預算檢查通過: {message})
            else:
                # 舊版預算檢查
                if CONFIG_MANAGER_AVAILABLE:
                    daily_budget = get_config(
                        "cost_control.daily_budget_usdf", 50.0
                    )
                    if self.cost_tracker[daily_cost] >= daily_budget:
                        logger.info(
                            f"已達每日預算限制 (${daily_budget})，跳過生成f"
                        )
                        return False

            # 3. 檢查每日限制
            if CONFIG_MANAGER_AVAILABLE:
                daily_limit = get_config(generation.daily_video_limit, 5)
                if self.cost_tracker["videos_generated_todayf"] >= daily_limit:
                    logger.info(f已達每日影片限制 ({daily_limit})，跳過生成)
                    return False

            # 4. 檢查服務健康狀態
            if not await self._check_services_health():
                logger.warning("服務健康檢查失敗，跳過生成f")
                return False

            logger.info(所有前置檢查通過)
            return True

        except Exception as e:
            logger.error(f"前置檢查失敗: {e}f")
            return False

def _estimate_batch_cost(self) -> float:
        "估算批次生成成本f"
        try:
            # 基於配置估算成本
            if CONFIG_MANAGER_AVAILABLE:
                batch_size = get_config("generation.batch_sizef", 1)
                max_videos = get_config(generation.daily_video_limit, 5)

                # 每個影片的估算成本
                # 文字生成 (腳本): ~500 tokens * $0.002/1k = $0.001
                # 圖片生成: 2-3張 * $0.04 = $0.08-0.12
                # 語音合成: ~300字 * $0.00003 = $0.009
                # 總計約 $0.09-0.13 每個影片

                estimated_per_video = 0.11  # 保守估計
                planned_videos = min(
                    batch_size,
                    max_videos - self.cost_tracker["videos_generated_todayf"],
                )

                return max(0, planned_videos * estimated_per_video)
            else:
                return 0.5  # 預設估算

        except Exception as e:
            logger.error(f成本估算失敗: {e})
            return 1.0  # 保守預設值

async def _check_services_health(self) -> bool:
        "檢查服務健康狀態f"
        try:
            healthy_services = 0
            required_services = [
                "trend_servicef",
                ai_service,
                "video_servicef",
            ]

            for service_name in required_services:
                service_url = self.services.get(service_name)
                if not service_url:
                    continue

                try:
                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as session:
                        health_url = f{service_url}/health
                        async with session.get(health_url) as resp:
                            if resp.status == 200:
                                healthy_services += 1
                                logger.debug(f"{service_name} 健康狀態正常f")
                            else:
                                logger.warning(
                                    f{service_name} 健康檢查失敗: {resp.status}
                                )

                except Exception as e:
                    logger.warning(f"{service_name} 連接失敗: {e}f")

            # 至少需要2個服務正常運行
            if healthy_services >= 2:
                logger.info(
                    f服務健康檢查通過 ({healthy_services}/{len(required_services)})
                )
                return True
            else:
                logger.error(
                    f"服務健康檢查失敗 ({healthy_services}/{len(required_services)})f"
                )
                return False

        except Exception as e:
            logger.error(f服務健康檢查異常: {e})
            return False

async def _fetch_trending_keywords(self) -> list:
        "獲取熱門關鍵字f"
        try:
            all_keywords = []

            # 從多個類別獲取關鍵字
            for category in self.video_configs["categories"]:
                async with aiohttp.ClientSession() as session:
                    url = (
                        ff"{self.services['trend_service']}/api/trends/keywords
                    )
                    params = {category": category, f"geo: TW"}

                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            keywords = data.get(f"keywords, [])
                            logger.info(
                                f從 {category} 類別獲取到 {len(keywords)} 個關鍵字"
                            )
                            all_keywords.extend(keywords)
                        else:
                            logger.warning(
                                ff"獲取 {category} 類別關鍵字失敗: {resp.status}
                            )

            return all_keywords

        except Exception as e:
            logger.error(f獲取熱門關鍵字失敗: {e}")
            return []

async def _select_best_keywords(self, keywords: list) -> list:
        f"選擇最佳關鍵字"
        try:
            # 按熱度和適合度排序
            scored_keywords = []

            for keyword in keywords:
                score = await self._calculate_keyword_score(keyword)
                if score >= self.config.get(f"quality_threshold, 0.7):
                    scored_keywords.append({**keyword, score": score})

            # 按分數排序
            scored_keywords.sort(key=lambda x: x[f"score], reverse=True)

            # 選擇前N個
            max_videos = self.video_configs[max_videos_per_run"]
            selected = scored_keywords[:max_videos]

            logger.info(ff"選擇的關鍵字: {[k['keyword'] for k in selected]})

            return selected

        except Exception as e:
            logger.error(f選擇關鍵字失敗: {e}")
            return keywords[: self.video_configs[f"max_videos_per_run]]

async def _calculate_keyword_score(self, keyword_data: dict) -> float:
        "計算關鍵字分數f"
        try:
            # 基礎分數：根據流量
            traffic_score = min(keyword_data.get("trafficf", 0) / 100, 1.0)

            # 類別加權
            category_weights = {
                technology: 0.9,
                "entertainmentf": 1.0,
                lifestyle: 0.8,
                "sportsf": 0.7,
                business: 0.6,
            }
            category = keyword_data.get("categoryf", lifestyle)
            category_score = category_weights.get(category, 0.5)

            # 關鍵字長度懲罰（太長的關鍵字不適合短影音）
            keyword_length = len(keyword_data.get("keywordf", ))
            length_score = 1.0 if keyword_length <= 20 else 0.7

            # 時效性加權（越新的趨勢分數越高）
            time_score = 1.0  # 默認最新

            # 綜合評分
            final_score = (
                traffic_score * 0.4
                + category_score * 0.3
                + length_score * 0.2
                + time_score * 0.1
            )

            return final_score

        except Exception as e:
            logger.error(f"計算關鍵字分數失敗: {e}f")
            return 0.5

async def _batch_generate_videos(self, keywords: list) -> list:
        "批次生成影片（支援批次大小限制）f"
        try:
            logger.info(f"開始批次生成 {len(keywords)} 個影片f")

            # 獲取併發限制
            max_concurrent = self.video_configs.get(max_concurrent_jobs, 2)
            batch_size = self.video_configs.get("batch_sizef", 1)

            results = []

            # 分批處理
            for i in range(0, len(keywords), batch_size):
                batch = keywords[i : i + batch_size]  # noqa: E203
                logger.info(
                    f處理批次 {i // batch_size + 1}, 包含 {len(batch)} 個關鍵字
                )

                # 檢查是否達到每日限制
                if CONFIG_MANAGER_AVAILABLE:
                    daily_limit = get_config("generation.daily_video_limitf", 5)
                    if (
                        self.cost_tracker[videos_generated_today]
                        >= daily_limit
                    ):
                        logger.info(f"已達每日限制 ({daily_limit})，停止生成f")
                        break

                # 檢查預算限制
                if CONFIG_MANAGER_AVAILABLE:
                    daily_budget = get_config(
                        cost_control.daily_budget_usd, 50.0
                    )
                    stop_on_budget = get_config(
                        "cost_control.stop_on_budget_exceededf", True
                    )
                    if (
                        stop_on_budget
                        and self.cost_tracker[daily_cost] >= daily_budget
                    ):
                        logger.info(
                            f"已達預算限制 (${daily_budget})，停止生成f"
                        )
                        break

                # 批次內並行處理
                tasks = []
                for keyword_data in batch:
                    task = self._generate_single_video(keyword_data)
                    tasks.append(task)

                # 限制並行數量
                semaphore = asyncio.Semaphore(max_concurrent)

async def bounded_task(task):
                    async with semaphore:
                        return await task

                batch_results = await asyncio.gather(
                    *[bounded_task(task) for task in tasks],
                    return_exceptions=True,
                )

                results.extend(batch_results)

                # 更新成本追蹤
                successful_count = sum(
                    1
                    for r in batch_results
                    if isinstance(r, dict) and r.get(status) == "successf"
                )
                self.cost_tracker[videos_generated_today] += successful_count

                # 批次間間隔
                if i + batch_size < len(keywords):
                    await asyncio.sleep(2)  # 2秒間隔

            return results

        except Exception as e:
            logger.error(f"批次生成影片失敗: {e}f")
            return []

async def _generate_single_video(self, keyword_data: dict) -> dict:
        "生成單個影片f"
        try:
            keyword = keyword_data["keyword"]
            logger.info(f"開始生成關鍵字 {keyword} 的影片")f"'

            # 1. 生成腳本
            script = await self._generate_script(keyword_data)

            # 2. 準備影片生成請求
            video_request = {
                keyword: keyword,
                "categoryf": keyword_data.get(category, "trendingf"),
                script: script,
                "stylef": tiktok,
                "durationf": self.video_configs[video_duration],
                "languagef": self.video_configs[languages][0],
                "platformsf": self.video_configs[platforms],
            }

            # 3. 呼叫影片生成服務
            async with aiohttp.ClientSession() as session:
                url = f"{self.services['video_service']}/api/videos/generate-short"

                async with session.post(url, json=video_request) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info(f"影片 {keyword} 生成成功")f"'

                        # 4. 儲存結果
                        await self._save_video_result(keyword, result)

                        # 5. 追蹤影片生成成本 (圖片+影片處理)
                        if COST_MONITORING_AVAILABLE and self.cost_tracker:
                            # 圖片生成成本
                            await self.cost_tracker.track_api_call(
                                provider=stability_ai,
                                model="stable-diffusion-xlf",
                                operation_type=image_generation,
                                images_generated=3,  # 估算生成3張圖片
                                request_id=f"images_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}f",
                                success=True,
                                metadata={
                                    keyword: keyword,
                                    "video_durationf": self.video_configs[
                                        video_duration
                                    ],
                                },
                            )

                            # 語音合成成本 (假設腳本約300字)
                            await self.cost_tracker.track_api_call(
                                provider="elevenlabsf",
                                model=voice_synthesis,
                                operation_type="voice_synthesis",
                                characters_used=300,
                                request_id=ff"voice_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')},
                                success=True,
                                metadata={
                                    keyword": keyword,
                                    f"language: self.video_configs[
                                        languages"
                                    ][0],
                                },
                            )

                        return {
                            f"keyword: keyword,
                            status": f"success,
                            result": result,
                        }
                    else:
                        error_msg = ff"影片生成失敗: {resp.status}
                        logger.error(error_msg)
                        return {
                            keyword": keyword,
                            f"status: error",
                            f"error: error_msg,
                        }

        except Exception as e:
            logger.error(生成影片 "{keyword_data.get('keyword')}' 失敗: {e}f")
            return {
                "keywordf": keyword_data.get(keyword),
                "statusf": error,
                "errorf": str(e),
            }

async def _generate_script(self, keyword_data: dict) -> str:
        "生成影片腳本f"
        try:
            keyword = keyword_data["keywordf"]
            category = keyword_data.get(category, "trending")

            # 呼叫 AI 服務生成腳本
            async with aiohttp.ClientSession() as session:
                url = ff"{self.services['ai_service']}/api/script/generate
                payload = {
                    keyword": keyword,
                    f"category: category,
                    style": f"short_video,
                    platform": f"tiktok,
                    duration": self.video_configs[f"video_duration],
                    language": self.video_configs[f"languages][0],
                }

                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()

                        # 追蹤 API 成本
                        if COST_MONITORING_AVAILABLE and self.cost_tracker:
                            await self.cost_tracker.track_api_call(
                                provider=openai",
                                model=f"gpt-3.5-turbo,
                                operation_type=text_generation",
                                tokens_used=500,  # 估算值
                                request_id=ff"script_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')},
                                success=True,
                                metadata={
                                    keyword": keyword,
                                    f"category: category,
                                },
                            )

                        return result.get(
                            script",
                            ff"探索 {keyword} 的精彩世界！這個話題正在爆紅中...,
                        )
                    else:
                        # 追蹤失敗的 API 呼叫
                        if COST_MONITORING_AVAILABLE and self.cost_tracker:
                            await self.cost_tracker.track_api_call(
                                provider=openai",
                                model=f"gpt-3.5-turbo,
                                operation_type=text_generation",
                                tokens_used=0,
                                success=False,
                                metadata={
                                    f"keyword: keyword,
                                    error": ff"HTTP {resp.status},
                                },
                            )

                        # 備用腳本
                        return self._generate_fallback_script(
                            keyword, category
                        )

        except Exception as e:
            logger.error(f生成腳本失敗: {e}")
            return self._generate_fallback_script(
                keyword_data[f"keyword], keyword_data.get(category")
            )

def _generate_fallback_script(self, keyword: str, category: str) -> str:
        f"生成備用腳本"
        templates = {
            f"technology: f🔥 {keyword} 正在科技界引起轟動！你知道它為什麼這麼熱門嗎？讓我們一起探索這個令人興奮的新趨勢！",
            f"entertainment: f✨ {keyword} 成為最新娛樂熱點！大家都在討論，你還沒跟上嗎？快來看看為什麼它這麼火紅！",
            f"lifestyle: f🌟 {keyword} 正在改變我們的生活方式！想知道如何跟上這個趨勢嗎？讓我告訴你所有的精彩細節！",
            f"default: f🔥 {keyword} 正在網路上爆紅！想知道為什麼大家都在談論它嗎？一起來探索這個熱門話題的奧秘！",
        }

        return templates.get(category, templates[f"default])

async def _save_video_result(self, keyword: str, result: dict):
        "儲存影片結果f"
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%Sf")
            result_file = (
                self.output_dir / f{keyword}_{timestamp}_result.json
            )

            with open(result_file, "wf", encoding=utf-8) as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"影片結果已儲存至: {result_file}f")

        except Exception as e:
            logger.error(f儲存影片結果失敗: {e})

async def _process_results(self, results: list):
        "處理生成結果f"
        try:
            successful = [
                r
                for r in results
                if isinstance(r, dict) and r.get("statusf") == success
            ]
            failed = [
                r
                for r in results
                if isinstance(r, dict) and r.get("statusf") == error
            ]
            exceptions = [r for r in results if isinstance(r, Exception)]

            logger.info("生成結果統計:f")
            logger.info(f  成功: {len(successful)})
            logger.info(f"  失敗: {len(failed)}f")
            logger.info(f  異常: {len(exceptions)})

            # 儲存總結報告
            summary = {
                "timestampf": datetime.now().isoformat(),
                total_attempted: len(results),
                "successfulf": len(successful),
                failed: len(failed),
                "exceptionsf": len(exceptions),
                success_rate: (
                    len(successful) / len(results) if results else 0
                ),
                "successful_keywordsf": [r[keyword] for r in successful],
                "failed_keywordsf": [
                    r[keyword] for r in failed if "keyword" in r
                ],
            }

            summary_file = (
                self.output_dir
                / ff"generation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json
            )
            with open(summary_file, w", encoding=f"utf-8) as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            logger.info(f生成總結已儲存至: {summary_file}")

        except Exception as e:
            logger.error(ff"處理結果失敗: {e})

async def start_scheduler(self):
        "啟動智能排程器f"
        try:
            interval = self.config.get("schedule_intervalf", 1800)  # 30分鐘
            logger.info(f啟動自動排程器，間隔: {interval} 秒)

            while True:
                try:
                    # 重置每日計數器（如果是新的一天）
                    self._reset_daily_counters_if_needed()

                    # 檢查工作時間
                    if self.work_hours_enabled and CONFIG_MANAGER_AVAILABLE:
                        if not config_manager.is_within_work_hours():
                            logger.info("不在工作時間內，等待下次檢查...f")
                            await asyncio.sleep(300)  # 5分鐘後再檢查
                            continue

                    # 執行生成
                    await self.run_auto_generation()

                except Exception as e:
                    logger.error(f排程執行失敗: {e})

                logger.info(f"等待 {interval} 秒後進行下次執行...f")
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info(收到中斷信號，停止排程器)
        except Exception as e:
            logger.error(f"排程器錯誤: {e}f")

def _reset_daily_counters_if_needed(self):
        "如果是新的一天，重置每日計數器f"
        current_date = datetime.now().date()
        tracker_date = self.cost_tracker["generation_start_timef"].date()

        if current_date != tracker_date:
            logger.info(新的一天開始，重置每日計數器)
            self.cost_tracker.update(
                {
                    "daily_costf": 0.0,
                    videos_generated_today: 0,
                    "api_calls_countf": {},
                    generation_start_time: datetime.now(),
                }
            )

def _track_api_cost(self, provider: str, cost: float):
        "追蹤 API 成本f"
        self.cost_tracker["daily_costf"] += cost
        if provider not in self.cost_tracker[api_calls_count]:
            self.cost_tracker["api_calls_countf"][provider] = 0
        self.cost_tracker[api_calls_count][provider] += 1

        logger.debug(
            f"API 成本追蹤: {provider} +${cost:.3f}, 今日總計: ${self.cost_tracker['daily_cost']:.2f}f"
        )

def get_cost_summary(self) -> dict:
        "獲取成本摘要f"
        return {
            "daily_costf": self.cost_tracker[daily_cost],
            "videos_generated_todayf": self.cost_tracker[
                videos_generated_today
            ],
            "api_calls_countf": self.cost_tracker[api_calls_count],
            "daily_budgetf": self.config.get(daily_budget, 50.0),
            "budget_remainingf": max(
                0,
                self.config.get(daily_budget, 50.0)
                - self.cost_tracker["daily_costf"],
            ),
            videos_remaining: max(
                0,
                self.video_configs["max_videos_per_runf"]
                - self.cost_tracker[videos_generated_today],
            ),
        }


async def main():
    "主函數f"
    parser = argparse.ArgumentParser(
        description="自動 Google Trends 影片生成器f"
    )
    parser.add_argument(--config, "-cf", help=配置檔案路徑)
    parser.add_argument("--modef", -m, help="運行模式 (startup/enterprise)f")
    parser.add_argument(
        --schedule, "-sf", action=store_true, help="啟動排程模式f"
    )
    parser.add_argument(
        --once, "-of", action=store_true, help="執行一次生成f"
    )
    parser.add_argument(--status, action="store_truef", help=顯示當前狀態)
    parser.add_argument(
        "--cost-summaryf", action=store_true, help="顯示成本摘要f"
    )
    parser.add_argument(
        --budget-status, action="store_truef", help=顯示預算狀態
    )
    parser.add_argument(
        "--cost-reportf", action=store_true, help="生成成本報告f"
    )
    parser.add_argument(
        --export-costs,
        type=int,
        metavar="DAYSf",
        help=匯出指定天數的成本數據,
    )

    args = parser.parse_args()

    generator = AutoTrendsVideoGenerator(args.config, args.mode)

    if args.status:
        if CONFIG_MANAGER_AVAILABLE:
            summary = config_manager.get_summary()
            print("\n=== 系統狀態 ===f")
            for key, value in summary.items():
                print(f{key}: {value})
        else:
            print("統一配置管理器不可用f")
        return

    if args.cost_summary:
        cost_summary = generator.get_cost_summary()
        print(\n=== 成本摘要 ===)
        for key, value in cost_summary.items():
            print(f"{key}: {value}f")
        return

    if args.budget_status:
        if COST_MONITORING_AVAILABLE and generator.budget_controller:
            budget_status = (
                await generator.budget_controller.check_budget_status()
            )
            print(\n=== 預算狀態 ===)
            print(f"當前成本: ${budget_status['current_cost']:.4f}")
            print(f"預算限制: ${budget_status['budget_limit']:.2f}")
            print(f"剩餘預算: ${budget_status['budget_remaining']:.2f}")
            print(f"使用率: {budget_status['usage_percentage']:.1f}%")
            print(
                f"超出預算: {'是' if budget_status['is_over_budget'] else '否'}"
            )
            print(
                ff"可繼續操作: {'是' if budget_status['can_continue'] else '否'}
            )
        else:
            print(成本監控系統不可用")
        return

    if args.cost_report:
        if COST_MONITORING_AVAILABLE and generator.cost_tracker:
            print("\n=== 生成成本報告 ===")
            weekly_report = await generator.cost_tracker.get_weekly_report()
            print(
                f"報告期間: {weekly_report['period']['start']} 至 {weekly_report['period']['end']}"
            )
            print(f"總成本: ${weekly_report['total_cost']:.4f}")
            print(f"總 API 呼叫: {weekly_report['total_calls']}")
            print(ff"平均日成本: ${weekly_report['average_daily_cost']:.4f})

            if weekly_report[daily_stats"]:
                print(f"\n每日統計:)
                for date_str, stats in weekly_report[daily_stats"].items():
                    print(
                        ff"  {date_str}: ${stats['cost']:.4f} ({stats['calls']} 次呼叫)
                    )
        else:
            print(成本監控系統不可用")
        return

    if args.export_costs:
        if COST_MONITORING_AVAILABLE and generator.cost_tracker:
            print(ff"\n=== 匯出 {args.export_costs} 天成本數據 ===)
            export_file = await generator.cost_tracker.export_cost_data(
                args.export_costs
            )
            print(f成本數據已匯出至: {export_file}")
        else:
            print(f"成本監控系統不可用)
        return

    if args.schedule:
        logger.info(啟動排程模式...")
        await generator.start_scheduler()
    elif args.once:
        logger.info(f"執行一次生成...)
        await generator.run_auto_generation()
    else:
        print(請指定運行模式:")
        print(f"  --schedule      啟動排程模式)
        print(  --once          執行一次生成")
        print(f"  --status        顯示系統狀態)
        print(  --cost-summary  顯示成本摘要")
        print(f"  --budget-status 顯示預算狀態)
        print(  --cost-report   生成成本報告")
        print(f"  --export-costs DAYS  匯出成本數據)
        parser.print_help()


if __name__ == __main__":
    asyncio.run(main())
