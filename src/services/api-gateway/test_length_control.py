#!/usr/bin/env python3
"""
內容長度控制測試腳本
測試不同長度要求下的內容生成準確性
"""

import requests
import json
import time
import os
from typing import Dict, Any

API_BASE = "http://localhost:8001"

def test_content_length_control():
    """測試內容長度控制功能"""
    
    # 設定 DeepSeek API Key
    os.environ["DEEPSEEK_API_KEY"] = "sk-c3f868c456344ac3834249cec685c75a"
    
    test_cases = [
        {
            "name": "超短文案測試",
            "template_id": "social_media_post",
            "parameters": {
                "topic": "AI科技新趨勢",
                "style": "professional",
                "tone": "enthusiastic",
                "target_audience": "科技愛好者",
                "length": "50",
                "platform": "twitter"
            },
            "expected_range": (30, 70)
        },
        {
            "name": "短文案測試",
            "template_id": "social_media_post",
            "parameters": {
                "topic": "健康飲食習慣",
                "style": "friendly",
                "tone": "conversational",
                "target_audience": "一般大眾",
                "length": "100",
                "platform": "facebook"
            },
            "expected_range": (80, 120)
        },
        {
            "name": "中等長度測試",
            "template_id": "blog_post",
            "parameters": {
                "topic": "遠程工作的優缺點分析",
                "style": "authoritative",
                "tone": "informative",
                "target_audience": "職場人士",
                "length": "300",
                "platform": "blog"
            },
            "expected_range": (250, 350)
        },
        {
            "name": "長文案測試",
            "template_id": "content_marketing",
            "parameters": {
                "topic": "數位轉型策略指南",
                "style": "professional",
                "tone": "authoritative",
                "target_audience": "企業管理者",
                "length": "500",
                "platform": "linkedin"
            },
            "expected_range": (450, 550)
        },
        {
            "name": "超長文案測試",
            "template_id": "email_marketing",
            "parameters": {
                "topic": "年度產品發布會邀請",
                "style": "creative",
                "tone": "persuasive",
                "target_audience": "潛在客戶",
                "length": "1000",
                "platform": "email"
            },
            "expected_range": (900, 1100)
        }
    ]
    
    print("🎯 開始測試內容長度控制功能")
    print("=" * 60)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 測試 {i}: {test_case['name']}")
        print(f"目標長度: {test_case['parameters']['length']}字")
        print(f"預期範圍: {test_case['expected_range'][0]}-{test_case['expected_range'][1]}字")
        
        try:
            # 發送生成請求
            response = requests.post(
                f"{API_BASE}/api/v1/templates/generate",
                json={
                    "template_id": test_case["template_id"],
                    "parameters": test_case["parameters"],
                    "use_ai": True
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    content = result["data"]["content"]
                    actual_length = len(content)
                    target_length = int(test_case["parameters"]["length"])
                    min_expected, max_expected = test_case["expected_range"]
                    
                    # 計算準確度
                    accuracy = 100 * (1 - abs(actual_length - target_length) / target_length)
                    is_in_range = min_expected <= actual_length <= max_expected
                    
                    print(f"✅ 生成成功!")
                    print(f"   實際長度: {actual_length}字")
                    print(f"   準確度: {accuracy:.1f}%")
                    print(f"   在預期範圍內: {'是' if is_in_range else '否'}")
                    print(f"   提供者: {result['data']['generation_info']['provider']}")
                    
                    # 顯示部分內容預覽
                    preview = content[:100] + "..." if len(content) > 100 else content
                    print(f"   內容預覽: {preview}")
                    
                    results.append({
                        "test_name": test_case["name"],
                        "target_length": target_length,
                        "actual_length": actual_length,
                        "accuracy": accuracy,
                        "in_range": is_in_range,
                        "provider": result['data']['generation_info']['provider']
                    })
                else:
                    print(f"❌ 生成失敗: {result.get('error', '未知錯誤')}")
            else:
                print(f"❌ API請求失敗: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"❌ 測試失敗: {str(e)}")
        
        # 等待一下避免API限制
        if i < len(test_cases):
            time.sleep(1)
    
    # 生成測試報告
    print("\n" + "=" * 60)
    print("📊 測試結果報告")
    print("=" * 60)
    
    if results:
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r["in_range"])
        avg_accuracy = sum(r["accuracy"] for r in results) / total_tests
        
        print(f"總測試數: {total_tests}")
        print(f"成功測試數: {successful_tests}")
        print(f"成功率: {successful_tests/total_tests*100:.1f}%")
        print(f"平均準確度: {avg_accuracy:.1f}%")
        
        print("\n詳細結果:")
        print("-" * 60)
        for result in results:
            status = "✅" if result["in_range"] else "⚠️"
            print(f"{status} {result['test_name']}: {result['actual_length']}/{result['target_length']}字 (準確度: {result['accuracy']:.1f}%)")
        
        # 評估整體表現
        if avg_accuracy >= 90:
            print("\n🎉 優秀! 內容長度控制系統表現優異")
        elif avg_accuracy >= 80:
            print("\n👍 良好! 內容長度控制系統表現良好")
        elif avg_accuracy >= 70:
            print("\n👌 可接受! 內容長度控制系統需要微調")
        else:
            print("\n⚠️ 需要改進! 內容長度控制系統需要優化")
    
    else:
        print("❌ 沒有成功的測試結果")

if __name__ == "__main__":
    test_content_length_control()