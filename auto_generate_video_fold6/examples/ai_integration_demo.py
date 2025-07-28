#!/usr/bin/env python3
"""
AI 服務整合示例
展示如何使用新整合的 Suno.ai 和 Gemini Pro 服務
"""

import asyncio
import os
import logging
from pathlib import Path

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_gemini_integration():
    """Gemini Pro 整合示例"""
    print("\n🤖 Gemini Pro AI 服務整合示例")
    print("=" * 50)

    try:
        import sys
        import os

        sys.path.append(os.path.join(os.path.dirname(__file__), "..", "services", "ai-service"))
        from gemini_client import (
            generate_video_script,
            analyze_trends,
            GeminiClient,
            GeminiGenerationConfig,
        )

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ 請設置 GEMINI_API_KEY 環境變數")
            return

        # 1. 生成影片腳本
        print("\n📝 生成 TikTok 影片腳本...")
        script = await generate_video_script(
            topic="AI 人工智慧如何改變現代生活",
            platform="tiktok",
            style="educational",
            api_key=api_key,
        )

        if script:
            print(f"✅ 腳本生成成功:")
            print(f"```\n{script}\n```")
        else:
            print("❌ 腳本生成失敗")

        # 2. 趨勢分析
        print("\n📊 分析內容趨勢...")
        analysis = await analyze_trends(script[:200], api_key=api_key)

        if "error" not in analysis:
            print("✅ 趨勢分析成功:")
            print(f"病毒潛力: {analysis.get('viral_potential', 'N/A')}/10")
            print(f"目標受眾: {analysis.get('target_audience', 'N/A')}")
            print(f"推薦平台: {', '.join(analysis.get('recommended_platforms', []))}")
        else:
            print(f"❌ 趨勢分析失敗: {analysis.get('error')}")

        # 3. 多模態生成
        print("\n🎨 多模態內容生成...")
        async with GeminiClient(api_key=api_key) as client:
            result = await client.generate_content(
                prompt="為科技短影片創作吸引人的開場白，要求生動有趣",
                generation_config=GeminiGenerationConfig(temperature=0.9, max_output_tokens=150),
            )

            if result.success:
                print(f"✅ 開場白生成成功: {result.text}")
            else:
                print(f"❌ 開場白生成失敗: {result.error_message}")

    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
    except Exception as e:
        print(f"❌ Gemini 示例失敗: {e}")


async def demo_suno_integration():
    """Suno.ai 音樂生成整合示例"""
    print("\n🎵 Suno.ai 音樂生成服務整合示例")
    print("=" * 50)

    try:
        import sys
        import os

        sys.path.append(os.path.join(os.path.dirname(__file__), "..", "services", "music-service"))
        from suno_client import generate_music_for_video, SunoClient, MusicGenerationRequest

        api_key = os.getenv("SUNO_API_KEY")
        if not api_key:
            print("❌ 請設置 SUNO_API_KEY 環境變數")
            return

        # 1. 為影片生成背景音樂
        print("\n🎼 為科技影片生成背景音樂...")
        music_result = await generate_music_for_video(
            prompt="輕快現代的科技風背景音樂，適合短影片",
            duration=30,
            style="electronic, upbeat, modern",
            api_key=api_key,
        )

        if music_result and music_result.status == "completed":
            print("✅ 音樂生成成功!")
            print(f"音樂 ID: {music_result.id}")
            print(f"標題: {music_result.title}")
            print(f"時長: {music_result.duration}秒")
            print(f"音頻 URL: {music_result.audio_url}")

            # 下載音樂文件
            if music_result.audio_url:
                async with SunoClient(api_key=api_key) as client:
                    output_path = Path("examples/demo_music.mp3")
                    success = await client.download_audio(music_result.audio_url, output_path)

                    if success:
                        print(f"✅ 音樂文件已下載到: {output_path}")
                    else:
                        print("❌ 音樂文件下載失敗")
        else:
            print(f"❌ 音樂生成失敗: {music_result.error_message if music_result else '未知錯誤'}")

        # 2. 生成不同風格的音樂
        print("\n🎪 生成娛樂風格音樂...")
        async with SunoClient(api_key=api_key) as client:
            entertainment_request = MusicGenerationRequest(
                prompt="歡快活潑的娛樂節目背景音樂",
                duration=15,
                style="cheerful, entertainment, pop",
                instrumental=True,
                title="娛樂節目背景音樂",
            )

            entertainment_result = await client.generate_music(entertainment_request)

            if entertainment_result.status == "completed":
                print("✅ 娛樂風格音樂生成成功!")
                print(f"標題: {entertainment_result.title}")
            else:
                print(f"❌ 娛樂風格音樂生成失敗: {entertainment_result.error_message}")

    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
    except Exception as e:
        print(f"❌ Suno 示例失敗: {e}")


async def demo_ai_orchestrator():
    """AI 服務編排器示例"""
    print("\n🎭 AI 服務編排器整合示例")
    print("=" * 50)

    try:
        from services.ai_service.ai_orchestrator import (
            AIOrchestrator,
            AIRequest,
            AITaskType,
            AIProvider,
            generate_text_with_fallback,
            generate_music_for_video,
        )

        orchestrator = AIOrchestrator()

        # 1. 文字生成（支援故障轉移）
        print("\n📖 智能文字生成（自動故障轉移）...")
        text_result = await generate_text_with_fallback(
            prompt="創作一個關於 AI 技術發展的 30 秒短影片腳本",
            primary_provider="gemini",
            fallback_provider="openai",
            temperature=0.8,
            max_tokens=200,
        )

        if text_result:
            print(f"✅ 文字生成成功: {text_result[:100]}...")
        else:
            print("❌ 文字生成失敗")

        # 2. 內容分析
        print("\n🔍 智能內容分析...")
        analysis_request = AIRequest(
            task_type=AITaskType.CONTENT_ANALYSIS,
            prompt="AI 技術正在革命性地改變我們的日常生活，從智能手機到自動駕駛汽車",
            fallback_enabled=True,
        )

        analysis_response = await orchestrator.process_request(analysis_request)

        if analysis_response.success:
            print("✅ 內容分析成功:")
            content = analysis_response.content
            if isinstance(content, dict):
                for key, value in content.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  分析結果: {content}")
        else:
            print(f"❌ 內容分析失敗: {analysis_response.error_message}")

        # 3. 音樂生成
        print("\n🎵 智能音樂生成...")
        music_content = await generate_music_for_video(
            prompt="科技感十足的背景音樂，適合產品介紹", duration=20, style="futuristic, tech"
        )

        if music_content:
            print("✅ 音樂生成成功:")
            print(f"  音頻 URL: {music_content.get('audio_url', 'N/A')}")
            print(f"  時長: {music_content.get('duration', 'N/A')}秒")
        else:
            print("❌ 音樂生成失敗")

        # 4. 提供商狀態監控
        print("\n📊 AI 服務提供商狀態...")
        status = await orchestrator.get_provider_status()

        for provider, stats in status.items():
            health_status = "🟢" if stats["healthy"] else "🔴"
            print(
                f"  {health_status} {provider}: 成功率 {stats['success_rate']:.2%}, 平均響應時間 {stats['average_response_time']:.2f}s"
            )

    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
    except Exception as e:
        print(f"❌ AI 編排器示例失敗: {e}")


async def demo_complete_workflow():
    """完整的影片生成工作流程示例"""
    print("\n🎬 完整影片生成工作流程示例")
    print("=" * 50)

    try:
        # 1. 使用 Gemini 生成腳本
        print("\n1️⃣ 使用 Gemini 生成影片腳本...")
        from services.ai_service.gemini_client import generate_video_script

        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            script = await generate_video_script(
                topic="未來科技趨勢",
                platform="youtube_shorts",
                style="professional",
                api_key=gemini_key,
            )
            print(f"✅ 腳本: {script[:100]}..." if script else "❌ 腳本生成失敗")
        else:
            script = "AI 技術正在快速發展，改變著我們的生活方式..."
            print("⚠️ 使用預設腳本（未設置 Gemini API Key）")

        # 2. 使用 Suno 生成背景音樂
        print("\n2️⃣ 使用 Suno 生成背景音樂...")
        from services.music_service.suno_client import generate_music_for_video

        suno_key = os.getenv("SUNO_API_KEY")
        if suno_key:
            music = await generate_music_for_video(
                prompt="專業科技風背景音樂",
                duration=30,
                style="professional, tech, ambient",
                api_key=suno_key,
            )
            print(
                f"✅ 音樂: {music.title if music and music.status == 'completed' else '生成中或失敗'}"
            )
        else:
            print("⚠️ 跳過音樂生成（未設置 Suno API Key）")

        # 3. 分析和優化
        print("\n3️⃣ 內容分析和優化建議...")
        from services.ai_service.ai_orchestrator import AIOrchestrator, AIRequest, AITaskType

        orchestrator = AIOrchestrator()

        trend_request = AIRequest(
            task_type=AITaskType.TREND_ANALYSIS, prompt=script, fallback_enabled=True
        )

        trend_response = await orchestrator.process_request(trend_request)

        if trend_response.success:
            print("✅ 趨勢分析完成:")
            analysis = trend_response.content
            if isinstance(analysis, dict):
                print(f"  病毒潛力: {analysis.get('viral_potential', 'N/A')}")
                print(f"  目標受眾: {analysis.get('target_audience', 'N/A')}")
            else:
                print(f"  分析結果: 已完成")
        else:
            print("❌ 趨勢分析失敗")

        print("\n🎯 完整工作流程演示完成!")
        print("這個示例展示了如何整合多個 AI 服務來創建完整的影片生成流程。")

    except Exception as e:
        print(f"❌ 完整工作流程示例失敗: {e}")


async def demo_cost_tracking():
    """成本追蹤示例"""
    print("\n💰 成本追蹤和監控示例")
    print("=" * 50)

    try:
        from monitoring.cost_tracker import get_cost_tracker

        cost_tracker = get_cost_tracker()

        # 模擬 API 呼叫記錄
        print("\n📝 記錄模擬 API 呼叫...")

        # Gemini API 呼叫
        await cost_tracker.track_api_call(
            provider="google",
            model="gemini-pro",
            operation_type="text_generation",
            tokens_used=500,
            success=True,
            metadata={"request_type": "script_generation"},
        )

        # Suno API 呼叫
        await cost_tracker.track_api_call(
            provider="suno",
            model="chirp-v3",
            operation_type="music_generation",
            tokens_used=30,  # 30秒音樂
            success=True,
            metadata={"duration": 30, "style": "tech"},
        )

        print("✅ API 呼叫記錄完成")

        # 檢查預算狀態
        print("\n📊 檢查當前預算狀態...")
        budget_status = await cost_tracker.check_budget_status()

        print(f"今日預算: ${budget_status['budget_limit']:.2f}")
        print(f"已使用: ${budget_status['current_cost']:.2f}")
        print(f"剩餘: ${budget_status['remaining_budget']:.2f}")
        print(f"使用率: {budget_status['usage_percentage']:.1f}%")

        # 獲取每日摘要
        print("\n📈 今日成本摘要...")
        from datetime import date

        daily_summary = await cost_tracker.get_daily_summary(date.today())

        print(f"總成本: ${daily_summary.total_cost:.2f}")
        print(f"API 呼叫次數: {daily_summary.api_calls_count}")
        print("提供商分布:")
        for provider, cost in daily_summary.providers_breakdown.items():
            print(f"  {provider}: ${cost:.2f}")

    except Exception as e:
        print(f"❌ 成本追蹤示例失敗: {e}")


async def main():
    """主示例函數"""
    print("🚀 AI 服務整合完整示例")
    print("=" * 80)

    # 檢查環境變數
    required_keys = ["GEMINI_API_KEY", "SUNO_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]

    if missing_keys:
        print("⚠️ 缺少以下環境變數，部分功能可能無法正常工作:")
        for key in missing_keys:
            print(f"  - {key}")
        print()

    # 創建示例輸出目錄
    Path("examples").mkdir(exist_ok=True)

    try:
        # 執行所有示例
        await demo_gemini_integration()
        await demo_suno_integration()
        await demo_ai_orchestrator()
        await demo_complete_workflow()
        await demo_cost_tracking()

        print("\n🎉 所有示例執行完成!")
        print("\n📚 更多信息:")
        print("  - 查看 services/ai-service/ 了解 AI 服務整合")
        print("  - 查看 services/music-service/ 了解音樂生成服務")
        print("  - 查看 monitoring/ 了解成本追蹤和監控")
        print("  - 查看 config/ 了解配置管理")

    except KeyboardInterrupt:
        print("\n\n⏹️ 示例被用戶中斷")
    except Exception as e:
        print(f"\n❌ 示例執行失敗: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
