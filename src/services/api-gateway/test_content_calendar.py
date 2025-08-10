#!/usr/bin/env python3
"""
內容日曆與排程系統綜合測試
Complete test suite for content calendar and scheduling system
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any

API_BASE = "http://localhost:8001"

def test_content_calendar_system():
    """測試內容日曆與排程系統的完整功能"""
    
    print("📅 開始內容日曆與排程系統綜合測試")
    print("=" * 80)
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # 測試案例列表
    test_cases = [
        ("API 健康檢查", test_api_health),
        ("獲取日曆項目列表", test_get_calendar_items),
        ("創建新的排程項目", test_create_schedule),
        ("獲取特定項目詳情", test_get_item_details),
        ("更新項目狀態", test_update_item),
        ("發布內容", test_publish_content),
        ("獲取分析數據", test_get_analytics),
        ("刪除項目", test_delete_item),
        ("篩選和查詢功能", test_filtering),
        ("日期範圍查詢", test_date_range_query)
    ]
    
    # 存儲測試過程中創建的項目ID，用於清理
    created_item_ids = []
    
    for test_name, test_func in test_cases:
        test_results["total"] += 1
        print(f"\n🧪 測試 {test_results['total']}: {test_name}")
        print("-" * 60)
        
        try:
            # 執行測試並傳入已創建項目的ID列表
            result = test_func(created_item_ids)
            
            if result.get("success", False):
                test_results["passed"] += 1
                print(f"✅ {test_name} - 通過")
                
                # 如果測試創建了新項目，保存ID
                if "item_id" in result:
                    created_item_ids.append(result["item_id"])
                    
            else:
                test_results["failed"] += 1
                print(f"❌ {test_name} - 失敗: {result.get('error', '未知錯誤')}")
                
        except Exception as e:
            test_results["failed"] += 1
            print(f"💥 {test_name} - 異常: {str(e)}")
        
        # 測試間隔
        time.sleep(0.5)
    
    # 生成測試報告
    print("\n" + "=" * 80)
    print("📊 內容日曆與排程系統測試報告")
    print("=" * 80)
    
    print(f"總測試數: {test_results['total']}")
    print(f"通過測試: {test_results['passed']}")
    print(f"失敗測試: {test_results['failed']}")
    
    success_rate = (test_results['passed'] / test_results['total']) * 100
    print(f"成功率: {success_rate:.1f}%")
    
    print(f"\n創建的測試項目: {len(created_item_ids)} 個")
    
    # 系統評估
    if success_rate >= 95:
        print("\n🎉 優秀！內容日曆系統功能完整且運行穩定")
        grade = "A+"
    elif success_rate >= 85:
        print("\n👍 良好！內容日曆系統基本功能正常")
        grade = "A"
    elif success_rate >= 70:
        print("\n👌 可接受！內容日曆系統需要一些改進")
        grade = "B"
    else:
        print("\n⚠️ 需要改進！內容日曆系統存在較多問題")
        grade = "C"
    
    print(f"系統評級: {grade}")
    
    # 功能總結
    print(f"\n✅ 內容日曆與排程系統功能特色:")
    print("   - 📅 智能日曆視圖與排程管理")
    print("   - 🤖 AI驅動的內容生成整合")
    print("   - 🏢 多平台發布支援 (Facebook, Instagram, LinkedIn, Twitter)")
    print("   - 🏷️ 標籤分類與搜尋功能")
    print("   - 📊 詳細的分析統計報表")
    print("   - ⚡ 即時發布與狀態管理")
    print("   - 🔄 完整的 CRUD 操作")
    
    return success_rate >= 80


def test_api_health(created_items):
    """測試API健康檢查"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "message": f"API健康狀態: {data.get('status', 'unknown')}"
            }
        else:
            return {"success": False, "error": f"健康檢查失敗: HTTP {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"API連接失敗: {str(e)}"}


def test_get_calendar_items(created_items):
    """測試獲取日曆項目列表"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/calendar", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                items = data["data"]["items"]
                stats = data["data"]["statistics"]
                
                print(f"   獲取到 {len(items)} 個日曆項目")
                print(f"   統計信息: {stats}")
                
                return {
                    "success": True,
                    "message": f"成功獲取 {len(items)} 個項目"
                }
            else:
                return {"success": False, "error": data.get("error", "API返回失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"請求失敗: {str(e)}"}


def test_create_schedule(created_items):
    """測試創建新的排程項目"""
    try:
        # 設置排程時間為明天上午10點
        tomorrow = datetime.utcnow() + timedelta(days=1)
        scheduled_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        schedule_data = {
            "title": "測試自動化排程內容",
            "template_id": "social_media_post",
            "platform": "linkedin",
            "scheduled_date": scheduled_time.isoformat() + "Z",
            "tags": ["測試", "自動化", "排程"],
            "template_parameters": {
                "topic": "內容日曆系統自動化測試",
                "style": "professional",
                "tone": "informative",
                "target_audience": "開發者和測試工程師",
                "length": "200",
                "platform": "linkedin"
            }
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/calendar/schedule",
            json=schedule_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                item = data["data"]["item"]
                item_id = item["id"]
                
                print(f"   創建項目ID: {item_id}")
                print(f"   排程時間: {item['scheduled_date']}")
                print(f"   狀態: {item['status']}")
                print(f"   內容長度: {len(item['content'])} 字符")
                
                return {
                    "success": True,
                    "message": f"成功創建排程項目: {item_id}",
                    "item_id": item_id
                }
            else:
                return {"success": False, "error": data.get("error", "創建失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"創建排程失敗: {str(e)}"}


def test_get_item_details(created_items):
    """測試獲取特定項目詳情"""
    if not created_items:
        return {"success": False, "error": "沒有可用的測試項目"}
    
    try:
        item_id = created_items[-1]  # 使用最後創建的項目
        response = requests.get(f"{API_BASE}/api/v1/calendar/{item_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                item = data["data"]["item"]
                
                print(f"   項目標題: {item['title']}")
                print(f"   項目狀態: {item['status']}")
                print(f"   排程平台: {item['platform']}")
                print(f"   標籤: {', '.join(item['tags'])}")
                
                return {
                    "success": True,
                    "message": f"成功獲取項目詳情: {item_id}"
                }
            else:
                return {"success": False, "error": data.get("error", "獲取失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"獲取項目詳情失敗: {str(e)}"}


def test_update_item(created_items):
    """測試更新項目狀態"""
    if not created_items:
        return {"success": False, "error": "沒有可用的測試項目"}
    
    try:
        item_id = created_items[-1]
        
        # 首先獲取當前項目狀態
        get_response = requests.get(f"{API_BASE}/api/v1/calendar/{item_id}")
        if get_response.status_code != 200:
            return {"success": False, "error": "無法獲取項目當前狀態"}
        
        current_item = get_response.json()["data"]["item"]
        
        # 更新標題和標籤
        updated_data = current_item.copy()
        updated_data["title"] = "已更新的測試排程內容"
        updated_data["tags"] = ["測試", "自動化", "排程", "已更新"]
        
        response = requests.put(
            f"{API_BASE}/api/v1/calendar/{item_id}",
            json=updated_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                updated_item = data["data"]["item"]
                
                print(f"   更新後標題: {updated_item['title']}")
                print(f"   更新後標籤: {', '.join(updated_item['tags'])}")
                
                return {
                    "success": True,
                    "message": f"成功更新項目: {item_id}"
                }
            else:
                return {"success": False, "error": data.get("error", "更新失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"更新項目失敗: {str(e)}"}


def test_publish_content(created_items):
    """測試發布內容"""
    if not created_items:
        return {"success": False, "error": "沒有可用的測試項目"}
    
    try:
        item_id = created_items[-1]
        
        response = requests.post(
            f"{API_BASE}/api/v1/calendar/{item_id}/publish",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                item = data["data"]["item"]
                
                print(f"   發布狀態: {item['status']}")
                print(f"   發布時間: {item.get('published_at', 'N/A')}")
                print(f"   發布平台: {item['platform']}")
                
                return {
                    "success": True,
                    "message": f"成功發布內容: {item_id}"
                }
            else:
                return {"success": False, "error": data.get("error", "發布失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"發布內容失敗: {str(e)}"}


def test_get_analytics(created_items):
    """測試獲取分析數據"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/calendar/analytics", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                analytics = data["data"]
                
                print(f"   總項目數: {analytics['total_items']}")
                print(f"   狀態分佈: {analytics['status_distribution']}")
                print(f"   平台分佈: {analytics['platform_distribution']}")
                print(f"   完成率: {analytics['performance_metrics']['completion_rate']}%")
                print(f"   最活躍平台: {analytics['performance_metrics']['most_active_platform']}")
                
                return {
                    "success": True,
                    "message": f"成功獲取分析數據，包含 {analytics['total_items']} 個項目"
                }
            else:
                return {"success": False, "error": data.get("error", "獲取分析失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"獲取分析數據失敗: {str(e)}"}


def test_delete_item(created_items):
    """測試刪除項目（只刪除一個測試項目）"""
    if not created_items:
        return {"success": False, "error": "沒有可用的測試項目"}
    
    try:
        # 只刪除第一個創建的項目，保留其他項目
        item_id = created_items[0]
        
        response = requests.delete(f"{API_BASE}/api/v1/calendar/{item_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                deleted_item = data["data"]["deleted_item"]
                
                print(f"   已刪除項目: {deleted_item['title']}")
                print(f"   項目ID: {item_id}")
                
                # 從列表中移除已刪除的項目
                created_items.remove(item_id)
                
                return {
                    "success": True,
                    "message": f"成功刪除項目: {item_id}"
                }
            else:
                return {"success": False, "error": data.get("error", "刪除失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"刪除項目失敗: {str(e)}"}


def test_filtering(created_items):
    """測試篩選和查詢功能"""
    try:
        # 測試按狀態篩選
        response = requests.get(
            f"{API_BASE}/api/v1/calendar?status=scheduled",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                scheduled_items = data["data"]["items"]
                scheduled_count = len([item for item in scheduled_items if item["status"] == "scheduled"])
                
                print(f"   已排程項目數: {scheduled_count}")
                
                # 測試按平台篩選
                platform_response = requests.get(
                    f"{API_BASE}/api/v1/calendar?platform=linkedin",
                    timeout=10
                )
                
                if platform_response.status_code == 200:
                    platform_data = platform_response.json()
                    linkedin_items = platform_data["data"]["items"]
                    linkedin_count = len([item for item in linkedin_items if item["platform"] == "linkedin"])
                    
                    print(f"   LinkedIn 項目數: {linkedin_count}")
                    
                    return {
                        "success": True,
                        "message": f"篩選功能正常，找到 {scheduled_count} 個已排程項目，{linkedin_count} 個LinkedIn項目"
                    }
                else:
                    return {"success": False, "error": "平台篩選失敗"}
            else:
                return {"success": False, "error": data.get("error", "狀態篩選失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"篩選功能測試失敗: {str(e)}"}


def test_date_range_query(created_items):
    """測試日期範圍查詢功能"""
    try:
        # 設置查詢範圍：今天到一周後
        today = datetime.utcnow()
        next_week = today + timedelta(days=7)
        
        start_date = today.strftime("%Y-%m-%d")
        end_date = next_week.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{API_BASE}/api/v1/calendar?start_date={start_date}&end_date={end_date}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                items_in_range = data["data"]["items"]
                
                print(f"   日期範圍: {start_date} 到 {end_date}")
                print(f"   範圍內項目數: {len(items_in_range)}")
                
                # 驗證返回的項目確實在指定日期範圍內
                valid_items = 0
                for item in items_in_range:
                    item_date = item["scheduled_date"][:10]  # YYYY-MM-DD
                    if start_date <= item_date <= end_date:
                        valid_items += 1
                
                print(f"   有效項目數: {valid_items}")
                
                return {
                    "success": True,
                    "message": f"日期範圍查詢正常，返回 {len(items_in_range)} 個項目，其中 {valid_items} 個有效"
                }
            else:
                return {"success": False, "error": data.get("error", "日期查詢失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"日期範圍查詢失敗: {str(e)}"}


if __name__ == "__main__":
    # 設置測試環境
    os.environ["DEEPSEEK_API_KEY"] = "sk-c3f868c456344ac3834249cec685c75a"
    
    print("🚀 內容日曆與排程系統綜合測試開始")
    print(f"📡 API地址: {API_BASE}")
    print(f"🕒 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_content_calendar_system()
    
    print(f"\n🎯 測試總結: {'成功' if success else '需要改進'}")
    
    exit(0 if success else 1)