#!/usr/bin/env python3
"""
自動 Google Trends 關鍵字採集並生成短影音腳本
整合關鍵字採集與影片生成的完整自動化流程
"""

import asyncio
import logging
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import os
import sys

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoTrendsVideoGenerator:
    """自動趨勢影片生成器"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.services = {
            'trend_service': self.config.get('trend_service_url', 'http://localhost:8001'),
            'video_service': self.config.get('video_service_url', 'http://localhost:8002'),
            'ai_service': self.config.get('ai_service_url', 'http://localhost:8003')
        }
        
        self.output_dir = Path(self.config.get('output_dir', './generated_videos'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 影片生成設定
        self.video_configs = {
            'max_videos_per_run': self.config.get('max_videos_per_run', 5),
            'video_duration': self.config.get('video_duration', 30),
            'platforms': self.config.get('target_platforms', ['tiktok', 'instagram', 'youtube_shorts']),
            'categories': self.config.get('categories', ['technology', 'entertainment', 'lifestyle']),
            'languages': self.config.get('languages', ['zh-TW'])
        }
    
    def _load_config(self, config_file: str) -> dict:
        """載入配置檔案"""
        default_config = {
            'trend_service_url': 'http://localhost:8001',
            'video_service_url': 'http://localhost:8002',
            'ai_service_url': 'http://localhost:8003',
            'output_dir': './generated_videos',
            'max_videos_per_run': 5,
            'video_duration': 30,
            'target_platforms': ['tiktok'],
            'categories': ['technology', 'entertainment', 'lifestyle'],
            'languages': ['zh-TW'],
            'schedule_interval': 1800,  # 30分鐘
            'quality_threshold': 0.7
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"載入配置檔案失敗，使用預設配置: {e}")
        
        return default_config
    
    async def run_auto_generation(self):
        """執行自動生成流程"""
        try:
            logger.info("🚀 開始自動趨勢影片生成流程")
            
            # 1. 獲取熱門關鍵字
            trending_keywords = await self._fetch_trending_keywords()
            
            if not trending_keywords:
                logger.warning("未找到熱門關鍵字，跳過此次生成")
                return
            
            logger.info(f"找到 {len(trending_keywords)} 個熱門關鍵字")
            
            # 2. 選擇最佳關鍵字
            selected_keywords = await self._select_best_keywords(trending_keywords)
            
            logger.info(f"選擇了 {len(selected_keywords)} 個關鍵字進行影片生成")
            
            # 3. 批次生成影片
            generation_results = await self._batch_generate_videos(selected_keywords)
            
            # 4. 處理結果
            await self._process_results(generation_results)
            
            logger.info("✅ 自動生成流程完成")
            
        except Exception as e:
            logger.error(f"自動生成流程失敗: {e}")
            raise
    
    async def _fetch_trending_keywords(self) -> list:
        """獲取熱門關鍵字"""
        try:
            all_keywords = []
            
            # 從多個類別獲取關鍵字
            for category in self.video_configs['categories']:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.services['trend_service']}/api/trends/keywords"
                    params = {
                        'category': category,
                        'geo': 'TW'
                    }
                    
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            keywords = data.get('keywords', [])
                            logger.info(f"從 {category} 類別獲取到 {len(keywords)} 個關鍵字")
                            all_keywords.extend(keywords)
                        else:
                            logger.warning(f"獲取 {category} 類別關鍵字失敗: {resp.status}")
            
            return all_keywords
            
        except Exception as e:
            logger.error(f"獲取熱門關鍵字失敗: {e}")
            return []
    
    async def _select_best_keywords(self, keywords: list) -> list:
        """選擇最佳關鍵字"""
        try:
            # 按熱度和適合度排序
            scored_keywords = []
            
            for keyword in keywords:
                score = await self._calculate_keyword_score(keyword)
                if score >= self.config.get('quality_threshold', 0.7):
                    scored_keywords.append({
                        **keyword,
                        'score': score
                    })
            
            # 按分數排序
            scored_keywords.sort(key=lambda x: x['score'], reverse=True)
            
            # 選擇前N個
            max_videos = self.video_configs['max_videos_per_run']
            selected = scored_keywords[:max_videos]
            
            logger.info(f"選擇的關鍵字: {[k['keyword'] for k in selected]}")
            
            return selected
            
        except Exception as e:
            logger.error(f"選擇關鍵字失敗: {e}")
            return keywords[:self.video_configs['max_videos_per_run']]
    
    async def _calculate_keyword_score(self, keyword_data: dict) -> float:
        """計算關鍵字分數"""
        try:
            # 基礎分數：根據流量
            traffic_score = min(keyword_data.get('traffic', 0) / 100, 1.0)
            
            # 類別加權
            category_weights = {
                'technology': 0.9,
                'entertainment': 1.0,
                'lifestyle': 0.8,
                'sports': 0.7,
                'business': 0.6
            }
            category = keyword_data.get('category', 'lifestyle')
            category_score = category_weights.get(category, 0.5)
            
            # 關鍵字長度懲罰（太長的關鍵字不適合短影音）
            keyword_length = len(keyword_data.get('keyword', ''))
            length_score = 1.0 if keyword_length <= 20 else 0.7
            
            # 時效性加權（越新的趨勢分數越高）
            time_score = 1.0  # 默認最新
            
            # 綜合評分
            final_score = traffic_score * 0.4 + category_score * 0.3 + length_score * 0.2 + time_score * 0.1
            
            return final_score
            
        except Exception as e:
            logger.error(f"計算關鍵字分數失敗: {e}")
            return 0.5
    
    async def _batch_generate_videos(self, keywords: list) -> list:
        """批次生成影片"""
        try:
            logger.info(f"開始批次生成 {len(keywords)} 個影片")
            
            tasks = []
            for keyword_data in keywords:
                task = self._generate_single_video(keyword_data)
                tasks.append(task)
            
            # 並行執行（限制並行數量避免過載）
            semaphore = asyncio.Semaphore(3)  # 最多同時3個
            
            async def bounded_task(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[bounded_task(task) for task in tasks],
                return_exceptions=True
            )
            
            return results
            
        except Exception as e:
            logger.error(f"批次生成影片失敗: {e}")
            return []
    
    async def _generate_single_video(self, keyword_data: dict) -> dict:
        """生成單個影片"""
        try:
            keyword = keyword_data['keyword']
            logger.info(f"開始生成關鍵字 '{keyword}' 的影片")
            
            # 1. 生成腳本
            script = await self._generate_script(keyword_data)
            
            # 2. 準備影片生成請求
            video_request = {
                'keyword': keyword,
                'category': keyword_data.get('category', 'trending'),
                'script': script,
                'style': 'tiktok',
                'duration': self.video_configs['video_duration'],
                'language': self.video_configs['languages'][0],
                'platforms': self.video_configs['platforms']
            }
            
            # 3. 呼叫影片生成服務
            async with aiohttp.ClientSession() as session:
                url = f"{self.services['video_service']}/api/videos/generate-short"
                
                async with session.post(url, json=video_request) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info(f"影片 '{keyword}' 生成成功")
                        
                        # 4. 儲存結果
                        await self._save_video_result(keyword, result)
                        
                        return {
                            'keyword': keyword,
                            'status': 'success',
                            'result': result
                        }
                    else:
                        error_msg = f"影片生成失敗: {resp.status}"
                        logger.error(error_msg)
                        return {
                            'keyword': keyword,
                            'status': 'error',
                            'error': error_msg
                        }
            
        except Exception as e:
            logger.error(f"生成影片 '{keyword_data.get('keyword')}' 失敗: {e}")
            return {
                'keyword': keyword_data.get('keyword'),
                'status': 'error',
                'error': str(e)
            }
    
    async def _generate_script(self, keyword_data: dict) -> str:
        """生成影片腳本"""
        try:
            keyword = keyword_data['keyword']
            category = keyword_data.get('category', 'trending')
            
            # 呼叫 AI 服務生成腳本
            async with aiohttp.ClientSession() as session:
                url = f"{self.services['ai_service']}/api/script/generate"
                payload = {
                    'keyword': keyword,
                    'category': category,
                    'style': 'short_video',
                    'platform': 'tiktok',
                    'duration': self.video_configs['video_duration'],
                    'language': self.video_configs['languages'][0]
                }
                
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get('script', f"探索 {keyword} 的精彩世界！這個話題正在爆紅中...")
                    else:
                        # 備用腳本
                        return self._generate_fallback_script(keyword, category)
        
        except Exception as e:
            logger.error(f"生成腳本失敗: {e}")
            return self._generate_fallback_script(keyword_data['keyword'], keyword_data.get('category'))
    
    def _generate_fallback_script(self, keyword: str, category: str) -> str:
        """生成備用腳本"""
        templates = {
            'technology': f"🔥 {keyword} 正在科技界引起轟動！你知道它為什麼這麼熱門嗎？讓我們一起探索這個令人興奮的新趨勢！",
            'entertainment': f"✨ {keyword} 成為最新娛樂熱點！大家都在討論，你還沒跟上嗎？快來看看為什麼它這麼火紅！",
            'lifestyle': f"🌟 {keyword} 正在改變我們的生活方式！想知道如何跟上這個趨勢嗎？讓我告訴你所有的精彩細節！",
            'default': f"🔥 {keyword} 正在網路上爆紅！想知道為什麼大家都在談論它嗎？一起來探索這個熱門話題的奧秘！"
        }
        
        return templates.get(category, templates['default'])
    
    async def _save_video_result(self, keyword: str, result: dict):
        """儲存影片結果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = self.output_dir / f"{keyword}_{timestamp}_result.json"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"影片結果已儲存至: {result_file}")
            
        except Exception as e:
            logger.error(f"儲存影片結果失敗: {e}")
    
    async def _process_results(self, results: list):
        """處理生成結果"""
        try:
            successful = [r for r in results if isinstance(r, dict) and r.get('status') == 'success']
            failed = [r for r in results if isinstance(r, dict) and r.get('status') == 'error']
            exceptions = [r for r in results if isinstance(r, Exception)]
            
            logger.info(f"生成結果統計:")
            logger.info(f"  成功: {len(successful)}")
            logger.info(f"  失敗: {len(failed)}")
            logger.info(f"  異常: {len(exceptions)}")
            
            # 儲存總結報告
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_attempted': len(results),
                'successful': len(successful),
                'failed': len(failed),
                'exceptions': len(exceptions),
                'success_rate': len(successful) / len(results) if results else 0,
                'successful_keywords': [r['keyword'] for r in successful],
                'failed_keywords': [r['keyword'] for r in failed if 'keyword' in r]
            }
            
            summary_file = self.output_dir / f"generation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"生成總結已儲存至: {summary_file}")
            
        except Exception as e:
            logger.error(f"處理結果失敗: {e}")
    
    async def start_scheduler(self):
        """啟動排程器"""
        try:
            interval = self.config.get('schedule_interval', 1800)  # 30分鐘
            logger.info(f"啟動自動排程器，間隔: {interval} 秒")
            
            while True:
                try:
                    await self.run_auto_generation()
                except Exception as e:
                    logger.error(f"排程執行失敗: {e}")
                
                logger.info(f"等待 {interval} 秒後進行下次執行...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("收到中斷信號，停止排程器")
        except Exception as e:
            logger.error(f"排程器錯誤: {e}")

async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='自動 Google Trends 影片生成器')
    parser.add_argument('--config', '-c', help='配置檔案路徑')
    parser.add_argument('--schedule', '-s', action='store_true', help='啟動排程模式')
    parser.add_argument('--once', '-o', action='store_true', help='執行一次生成')
    
    args = parser.parse_args()
    
    generator = AutoTrendsVideoGenerator(args.config)
    
    if args.schedule:
        await generator.start_scheduler()
    elif args.once:
        await generator.run_auto_generation()
    else:
        print("請指定 --schedule 或 --once 參數")
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())