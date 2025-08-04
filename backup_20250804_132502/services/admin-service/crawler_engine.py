import asyncio
import aiohttp
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import uuid
from sqlalchemy.orm import Session

from .models import CrawlerConfig, CrawlerResult, CrawlerStatus, ScheduleType, CrawlerTaskResult
from .database import SessionLocal
from .schemas import SystemLogCreate
from .crud import crud_system_log

logger = logging.getLogger(__name__)


class WebCrawler:
    """Web 爬蟲引擎"""
    
    def __init__(self):
        self.session = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": self.user_agents[0]}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def crawl_config(self, config: CrawlerConfig) -> Dict[str, Any]:
        """執行爬蟲配置"""
        run_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        results = []
        
        logger.info(f"開始執行爬蟲配置 {config.name} (ID: {config.id})")
        
        try:
            # 獲取頁面內容
            pages_crawled = 0
            current_url = config.target_url
            
            for page_num in range(min(config.max_pages, 100)):  # 限制最大頁數
                if pages_crawled >= config.max_pages:
                    break
                
                page_result = await self._crawl_single_page(
                    config, current_url, run_id, page_num + 1
                )
                
                if page_result:
                    results.append(page_result)
                    pages_crawled += 1
                
                # 延遲處理
                if config.delay_seconds > 0:
                    await asyncio.sleep(config.delay_seconds)
                
                # 這裡可以實現分頁邏輯
                # current_url = self._get_next_page_url(...)
                break  # 暫時只爬取一頁
            
            # 更新配置的最後運行時間
            self._update_crawler_last_run(config.id)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"爬蟲配置 {config.name} 執行完成，爬取 {pages_crawled} 頁，耗時 {duration:.2f} 秒")
            
            return {
                "run_id": run_id,
                "config_id": config.id,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "pages_crawled": pages_crawled,
                "results": results,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"爬蟲配置 {config.name} 執行失敗: {e}")
            
            # 記錄錯誤日誌
            self._log_crawler_error(config.id, run_id, str(e))
            
            return {
                "run_id": run_id,
                "config_id": config.id,
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "pages_crawled": 0,
                "results": [],
                "success": False,
                "error": str(e)
            }
    
    async def _crawl_single_page(self, config: CrawlerConfig, url: str, 
                                run_id: str, page_num: int) -> Optional[CrawlerResult]:
        """爬取單個頁面"""
        
        try:
            # 準備請求頭
            headers = config.headers or {}
            if "User-Agent" not in headers:
                headers["User-Agent"] = self.user_agents[page_num % len(self.user_agents)]
            
            # 發送 HTTP 請求
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"頁面 {url} 返回狀態碼 {response.status}")
                    return None
                
                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type.lower():
                    logger.warning(f"頁面 {url} 不是 HTML 內容")
                    return None
                
                html_content = await response.text()
            
            # 解析 HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取頁面標題
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # 提取頁面文本內容
            # 移除腳本和樣式標籤
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # 使用 CSS 選擇器提取特定內容
            extracted_data = {}
            if config.css_selectors:
                for key, selector in config.css_selectors.items():
                    elements = soup.select(selector)
                    extracted_data[key] = [elem.get_text().strip() for elem in elements]
            
            # 搜索關鍵字
            keywords_found = []
            for keyword in config.keywords:
                # 使用正則表達式進行不區分大小寫的搜索
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.findall(clean_text)
                if matches:
                    keywords_found.append({
                        "keyword": keyword,
                        "count": len(matches),
                        "positions": [m.start() for m in pattern.finditer(clean_text)][:10]  # 最多記錄10個位置
                    })
            
            # 創建爬蟲結果
            result_data = {
                "config_id": config.id,
                "run_id": run_id,
                "url": url,
                "title": title_text[:500],  # 限制標題長度
                "content": clean_text[:10000],  # 限制內容長度
                "keywords_found": keywords_found,
                "metadata": {
                    "page_number": page_num,
                    "content_length": len(clean_text),
                    "extracted_data": extracted_data,
                    "response_status": response.status,
                    "content_type": content_type
                },
                "success": True,
                "scraped_at": datetime.utcnow()
            }
            
            # 保存到資料庫
            self._save_crawler_result(result_data)
            
            logger.info(f"成功爬取頁面 {url}，找到 {len(keywords_found)} 個關鍵字匹配")
            
            return result_data
        
        except asyncio.TimeoutError:
            logger.warning(f"爬取頁面 {url} 超時")
            return None
        except Exception as e:
            logger.error(f"爬取頁面 {url} 失敗: {e}")
            
            # 記錄失敗的爬蟲結果
            error_result = {
                "config_id": config.id,
                "run_id": run_id,
                "url": url,
                "success": False,
                "error_message": str(e),
                "scraped_at": datetime.utcnow()
            }
            self._save_crawler_result(error_result)
            return None
    
    def _save_crawler_result(self, result_data: Dict[str, Any]):
        """保存爬蟲結果到資料庫"""
        try:
            db = SessionLocal()
            result = CrawlerResult(**result_data)
            db.add(result)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"保存爬蟲結果失敗: {e}")
    
    def _update_crawler_last_run(self, config_id: int):
        """更新爬蟲配置的最後運行時間"""
        try:
            db = SessionLocal()
            config = db.query(CrawlerConfig).filter(CrawlerConfig.id == config_id).first()
            if config:
                config.last_run_at = datetime.utcnow()
                # 計算下次運行時間
                config.next_run_at = self._calculate_next_run_time(config)
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"更新爬蟲配置運行時間失敗: {e}")
    
    def _calculate_next_run_time(self, config: CrawlerConfig) -> Optional[datetime]:
        """計算下次運行時間"""
        now = datetime.utcnow()
        
        if config.schedule_type == ScheduleType.ONCE:
            return None
        elif config.schedule_type == ScheduleType.HOURLY:
            return now + timedelta(hours=1)
        elif config.schedule_type == ScheduleType.DAILY:
            return now + timedelta(days=1)
        elif config.schedule_type == ScheduleType.WEEKLY:
            return now + timedelta(weeks=1)
        elif config.schedule_type == ScheduleType.MONTHLY:
            return now + timedelta(days=30)
        elif config.schedule_type == ScheduleType.CUSTOM_CRON:
            # 實現 cron 表達式解析
            return now + timedelta(hours=1)  # 暫時默認1小時
        
        return None
    
    def _log_crawler_error(self, config_id: int, run_id: str, error_message: str):
        """記錄爬蟲錯誤日誌"""
        try:
            db = SessionLocal()
            log_data = SystemLogCreate(
                action="crawler_error",
                resource_type="crawler_config",
                resource_id=str(config_id),
                level="error",
                message=f"爬蟲執行失敗: {error_message}",
                details={
                    "config_id": config_id,
                    "run_id": run_id,
                    "error": error_message
                }
            )
            crud_system_log.create_log(db, log_in=log_data)
            db.close()
        except Exception as e:
            logger.error(f"記錄爬蟲錯誤日誌失敗: {e}")
    
    async def crawl_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """執行 CrawlerTask 任務"""
        run_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        results = []
        
        task_name = task_config.get("task_name", "未命名任務")
        keywords = task_config.get("keywords", [])
        target_url = task_config.get("target_url")
        max_pages = task_config.get("max_pages", 10)
        delay_seconds = task_config.get("delay_seconds", 1)
        
        logger.info(f"開始執行爬蟲任務 {task_name}")
        
        try:
            pages_crawled = 0
            
            # 如果有指定目標 URL，直接爬取
            if target_url:
                for page_num in range(min(max_pages, 100)):
                    if pages_crawled >= max_pages:
                        break
                    
                    page_result = await self._crawl_task_page(
                        task_config, target_url, run_id, page_num + 1
                    )
                    
                    if page_result:
                        results.append(page_result)
                        pages_crawled += 1
                    
                    if delay_seconds > 0:
                        await asyncio.sleep(delay_seconds)
                    
                    break  # 暫時只爬取一頁
            
            # 如果沒有指定 URL，使用關鍵字搜尋
            else:
                for keyword in keywords[:3]:  # 限制關鍵字數量
                    if pages_crawled >= max_pages:
                        break
                    
                    search_results = await self._search_keyword(keyword, run_id)
                    if search_results:
                        results.extend(search_results)
                        pages_crawled += len(search_results)
                    
                    if delay_seconds > 0:
                        await asyncio.sleep(delay_seconds)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"爬蟲任務 {task_name} 執行完成，爬取 {pages_crawled} 頁，耗時 {duration:.2f} 秒")
            
            return {
                "run_id": run_id,
                "task_name": task_name,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "pages_crawled": pages_crawled,
                "total_pages": max_pages,
                "results": results,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"爬蟲任務 {task_name} 執行失敗: {e}")
            return {
                "run_id": run_id,
                "task_name": task_name,
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "duration_seconds": 0,
                "pages_crawled": 0,
                "total_pages": max_pages,
                "results": [],
                "success": False,
                "error": str(e)
            }
    
    async def _crawl_task_page(self, task_config: Dict[str, Any], url: str, run_id: str, page_num: int) -> Optional[Dict[str, Any]]:
        """爬取任務頁面"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # 提取標題
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else "無標題"
                    
                    # 提取描述
                    description = soup.find('meta', attrs={'name': 'description'})
                    description_text = description.get('content', '') if description else ''
                    
                    # 提取正文內容
                    body_text = self._extract_text_content(soup)
                    
                    # 檢查關鍵字匹配
                    keywords = task_config.get("keywords", [])
                    matched_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in body_text.lower() or keyword.lower() in title_text.lower():
                            matched_keywords.append(keyword)
                    
                    result_data = {
                        "url": url,
                        "title": title_text,
                        "description": description_text,
                        "content": body_text[:1000],  # 限制內容長度
                        "matched_keywords": matched_keywords,
                        "scraped_at": datetime.utcnow(),
                        "page_number": page_num,
                        "success": True
                    }
                    
                    # 保存到資料庫
                    self._save_task_result(task_config, result_data, run_id)
                    
                    return result_data
                else:
                    logger.warning(f"無法爬取頁面 {url}: HTTP {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"爬取頁面 {url} 失敗: {e}")
            return None
    
    async def _search_keyword(self, keyword: str, run_id: str) -> List[Dict[str, Any]]:
        """搜尋關鍵字（模擬實現）"""
        # 這裡應該實現實際的搜尋邏輯
        # 暫時返回模擬結果
        return [{
            "url": f"https://example.com/search?q={keyword}",
            "title": f"搜尋結果：{keyword}",
            "description": f"包含關鍵字 {keyword} 的內容",
            "content": f"這是包含關鍵字 {keyword} 的模擬內容",
            "matched_keywords": [keyword],
            "scraped_at": datetime.utcnow(),
            "page_number": 1,
            "success": True
        }]
    
    def _save_task_result(self, task_config: Dict[str, Any], result_data: Dict[str, Any], run_id: str):
        """保存爬蟲任務結果到資料庫"""
        try:
            db = SessionLocal()
            
            # 獲取任務ID (如果有的話)
            task_id = task_config.get("task_id")
            if not task_id:
                # 如果沒有 task_id，嘗試通過任務名稱查找
                task_name = task_config.get("task_name")
                if task_name:
                    from .models import CrawlerTask
                    task = db.query(CrawlerTask).filter(CrawlerTask.task_name == task_name).first()
                    if task:
                        task_id = task.id
            
            if task_id:
                import json
                matched_keywords_json = json.dumps(result_data.get("matched_keywords", []), ensure_ascii=False)
                
                crawler_result = CrawlerTaskResult(
                    task_id=task_id,
                    run_id=run_id,
                    url=result_data.get("url"),
                    title=result_data.get("title"),
                    description=result_data.get("description"),
                    content=result_data.get("content"),
                    matched_keywords=matched_keywords_json,
                    page_number=result_data.get("page_number", 1),
                    success=result_data.get("success", True),
                    error_message=result_data.get("error_message")
                )
                
                db.add(crawler_result)
                db.commit()
                logger.info(f"已保存爬蟲任務結果：{result_data.get('url', 'N/A')}")
            
            db.close()
        except Exception as e:
            logger.error(f"保存爬蟲任務結果失敗: {e}")
            if db:
                db.rollback()
                db.close()


class CrawlerScheduler:
    """爬蟲排程器"""
    
    def __init__(self):
        self.running = False
        self.crawler = None
    
    async def start(self):
        """啟動排程器"""
        self.running = True
        logger.info("爬蟲排程器已啟動")
        
        while self.running:
            try:
                await self._run_scheduled_crawlers()
                # 每分鐘檢查一次
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"排程器運行錯誤: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """停止排程器"""
        self.running = False
        logger.info("爬蟲排程器已停止")
    
    async def _run_scheduled_crawlers(self):
        """運行計劃的爬蟲任務"""
        db = SessionLocal()
        
        try:
            # 獲取需要運行的爬蟲配置
            current_time = datetime.utcnow()
            due_configs = db.query(CrawlerConfig).filter(
                CrawlerConfig.status == CrawlerStatus.ACTIVE,
                CrawlerConfig.next_run_at <= current_time
            ).all()
            
            if not due_configs:
                return
            
            logger.info(f"發現 {len(due_configs)} 個需要執行的爬蟲任務")
            
            # 執行爬蟲任務
            async with WebCrawler() as crawler:
                for config in due_configs:
                    try:
                        logger.info(f"執行爬蟲配置: {config.name}")
                        result = await crawler.crawl_config(config)
                        
                        if result["success"]:
                            logger.info(f"爬蟲配置 {config.name} 執行成功")
                        else:
                            logger.error(f"爬蟲配置 {config.name} 執行失敗: {result.get('error')}")
                    
                    except Exception as e:
                        logger.error(f"執行爬蟲配置 {config.name} 時發生異常: {e}")
        
        finally:
            db.close()
    
    async def run_crawler_manually(self, config_id: int) -> Dict[str, Any]:
        """手動運行指定的爬蟲配置"""
        db = SessionLocal()
        
        try:
            config = db.query(CrawlerConfig).filter(CrawlerConfig.id == config_id).first()
            if not config:
                return {"success": False, "error": "爬蟲配置不存在"}
            
            if config.status != CrawlerStatus.ACTIVE:
                return {"success": False, "error": "爬蟲配置未啟用"}
            
            logger.info(f"手動執行爬蟲配置: {config.name}")
            
            async with WebCrawler() as crawler:
                result = await crawler.crawl_config(config)
                return result
        
        finally:
            db.close()


# 全域排程器實例
crawler_scheduler = CrawlerScheduler()


# 爬蟲管理工具函數
def start_crawler_scheduler():
    """啟動爬蟲排程器"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(crawler_scheduler.start())


def stop_crawler_scheduler():
    """停止爬蟲排程器"""
    crawler_scheduler.stop()


async def run_crawler_config(config_id: int) -> Dict[str, Any]:
    """運行指定的爬蟲配置"""
    return await crawler_scheduler.run_crawler_manually(config_id)


def validate_crawler_config(config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """驗證爬蟲配置"""
    errors = []
    
    # 驗證 URL
    url = config_data.get("target_url")
    if not url:
        errors.append("目標 URL 不能為空")
    else:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            errors.append("目標 URL 格式無效")
    
    # 驗證關鍵字
    keywords = config_data.get("keywords", [])
    if not keywords or len(keywords) == 0:
        errors.append("至少需要一個關鍵字")
    
    # 驗證爬取參數
    max_pages = config_data.get("max_pages", 1)
    if max_pages < 1 or max_pages > 1000:
        errors.append("最大頁數必須在 1-1000 之間")
    
    delay_seconds = config_data.get("delay_seconds", 1)
    if delay_seconds < 0 or delay_seconds > 60:
        errors.append("延遲時間必須在 0-60 秒之間")
    
    # 驗證 CSS 選擇器
    css_selectors = config_data.get("css_selectors")
    if css_selectors:
        for key, selector in css_selectors.items():
            if not selector.strip():
                errors.append(f"CSS 選擇器 '{key}' 不能為空")
    
    return len(errors) == 0, errors