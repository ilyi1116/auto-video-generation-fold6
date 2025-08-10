#!/usr/bin/env python3
"""
全面的內容長度控制測試
測試多種長度範圍和模板的準確性
"""

import requests
import json
import time
import os
from typing import Dict, List, Any

API_BASE = "http://localhost:8001"

def test_comprehensive_length_control():
    """全面測試內容長度控制功能"""
    
    # 設定 DeepSeek API Key
    os.environ["DEEPSEEK_API_KEY"] = "sk-c3f868c456344ac3834249cec685c75a"
    
    test_cases = [
        # 超短內容測試
        {
            "name": "超短推文測試",
            "template_id": "social_media_post",
            "parameters": {
                "topic": "AI科技",
                "style": "casual",
                "tone": "enthusiastic",
                "target_audience": "年輕人",
                "length": "30",
                "platform": "twitter"
            },
            "expected_range": (27, 33),
            "target_accuracy": 90
        },
        
        # 短內容測試
        {
            "name": "短文案測試",
            "template_id": "social_media_post",
            "parameters": {
                "topic": "健康生活",
                "style": "friendly",
                "tone": "motivational",
                "target_audience": "上班族",
                "length": "80",
                "platform": "facebook"
            },
            "expected_range": (72, 88),
            "target_accuracy": 90
        },
        
        # 中等長度測試
        {
            "name": "中等長度測試",
            "template_id": "social_media_post", 
            "parameters": {
                "topic": "創業心得",
                "style": "professional",
                "tone": "informative",
                "target_audience": "創業者",
                "length": "150",
                "platform": "linkedin"
            },
            "expected_range": (135, 165),
            "target_accuracy": 90
        },
        
        # 長內容測試
        {
            "name": "長文案測試",
            "template_id": "social_media_post",
            "parameters": {
                "topic": "數位行銷策略",
                "style": "authoritative",
                "tone": "professional",
                "target_audience": "行銷人員",
                "length": "250",
                "platform": "linkedin"
            },
            "expected_range": (225, 275),
            "target_accuracy": 90
        }
    ]
    
    print("🎯 開始全面內容長度控制測試")
    print("=" * 80)
    print(f"測試目標: 達到90%以上的長度準確度")
    print(f"測試範圍: 30字 - 250字")
    print("=" * 80)
    
    results = []
    total_tests = 0
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 測試 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"目標長度: {test_case['parameters']['length']}字")
        print(f"容許範圍: {test_case['expected_range'][0]}-{test_case['expected_range'][1]}字")
        print(f"目標準確度: {test_case['target_accuracy']}%+")
        
        try:
            start_time = time.time()
            
            # 發送生成請求
            response = requests.post(
                f"{API_BASE}/api/v1/templates/generate",
                json={
                    "template_id": test_case["template_id"],
                    "parameters": test_case["parameters"],
                    "use_ai": True
                },
                headers={"Content-Type": "application/json"},
                timeout=60  # 增加超時時間
            )
            
            generation_time = time.time() - start_time
            total_tests += 1
            
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
                    meets_target = accuracy >= test_case["target_accuracy"]
                    
                    if is_in_range and meets_target:
                        passed_tests += 1
                        status = "✅ 通過"
                    else:
                        status = "⚠️ 未達標"
                    
                    print(f"{status}")
                    print(f"   實際長度: {actual_length}字")
                    print(f"   準確度: {accuracy:.1f}%")
                    print(f"   在範圍內: {'是' if is_in_range else '否'}")
                    print(f"   達到目標: {'是' if meets_target else '否'}")
                    print(f"   生成時間: {generation_time:.1f}秒")
                    print(f"   提供者: {result['data']['generation_info']['provider']}")
                    
                    # 顯示內容預覽
                    preview_length = min(60, len(content))
                    preview = content[:preview_length] + ("..." if len(content) > preview_length else "")
                    print(f"   內容預覽: {preview}")
                    
                    results.append({
                        "test_name": test_case["name"],
                        "target_length": target_length,
                        "actual_length": actual_length,
                        "accuracy": accuracy,
                        "in_range": is_in_range,
                        "meets_target": meets_target,
                        "generation_time": generation_time,
                        "provider": result['data']['generation_info']['provider']
                    })
                else:
                    print(f"❌ 生成失敗: {result.get('error', '未知錯誤')}")
            else:
                print(f"❌ API請求失敗: HTTP {response.status_code}")
                if response.text:
                    print(f"   錯誤詳情: {response.text[:200]}")
        
        except requests.exceptions.Timeout:
            print(f"⏱️ 測試超時 (60秒)")
        except Exception as e:
            print(f"❌ 測試失敗: {str(e)}")
        
        # 測試間隔，避免API限制
        if i < len(test_cases):
            print("⏳ 等待中...")
            time.sleep(2)
    
    # 生成詳細測試報告
    print("\n" + "=" * 80)
    print("📊 全面測試結果報告")
    print("=" * 80)
    
    if results:
        success_rate = (passed_tests / total_tests) * 100
        avg_accuracy = sum(r["accuracy"] for r in results) / len(results)
        avg_generation_time = sum(r["generation_time"] for r in results) / len(results)
        
        print(f"總測試數: {total_tests}")
        print(f"通過測試數: {passed_tests}")
        print(f"整體成功率: {success_rate:.1f}%")
        print(f"平均準確度: {avg_accuracy:.1f}%")
        print(f"平均生成時間: {avg_generation_time:.1f}秒")
        
        print("\n詳細結果:")
        print("-" * 80)
        for result in results:
            status = "✅ 優秀" if result["meets_target"] and result["in_range"] else "⚠️ 需改進"
            print(f"{status} {result['test_name']}: "
                  f"{result['actual_length']}/{result['target_length']}字 "
                  f"(準確度: {result['accuracy']:.1f}%, "
                  f"時間: {result['generation_time']:.1f}秒)")
        
        # 性能評估
        print(f"\n🎯 性能評估:")
        if success_rate >= 90:
            print("🏆 卓越! 長度控制系統達到生產級標準")
        elif success_rate >= 80:
            print("👍 優秀! 長度控制系統表現良好")
        elif success_rate >= 70:
            print("👌 良好! 長度控制系統基本滿足需求")
        else:
            print("⚠️ 需要改進! 長度控制系統需要進一步優化")
        
        if avg_generation_time <= 10:
            print("⚡ 生成速度優秀 (≤10秒)")
        elif avg_generation_time <= 20:
            print("🔄 生成速度良好 (≤20秒)")
        else:
            print("🐌 生成速度需要優化 (>20秒)")
            
        # 品質分析
        high_accuracy_count = sum(1 for r in results if r["accuracy"] >= 95)
        print(f"\n📈 品質分析:")
        print(f"高準確度測試 (≥95%): {high_accuracy_count}/{len(results)}")
        print(f"範圍內測試: {sum(1 for r in results if r['in_range'])}/{len(results)}")
        
        # 建議
        if success_rate < 90:
            print(f"\n💡 改進建議:")
            failed_tests = [r for r in results if not (r["meets_target"] and r["in_range"])]
            if failed_tests:
                print("- 需要改進的測試案例:")
                for test in failed_tests:
                    print(f"  • {test['test_name']}: 準確度 {test['accuracy']:.1f}%")
    
    else:
        print("❌ 沒有成功的測試結果")
        
    print(f"\n🔚 測試完成")
    return success_rate >= 90

if __name__ == "__main__":
    success = test_comprehensive_length_control()
    exit(0 if success else 1)