#!/usr/bin/env python3
"""
團隊協作功能綜合測試
Team collaboration functionality comprehensive test
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

API_BASE = "http://localhost:8001"

def test_team_collaboration_system():
    """測試團隊協作系統的完整功能"""
    
    print("🏢 開始團隊協作系統綜合測試")
    print("=" * 80)
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # 測試案例列表
    test_cases = [
        ("API 健康檢查", test_api_health),
        ("獲取用戶列表", test_get_users),
        ("獲取特定用戶資料", test_get_user_details),
        ("更新用戶資料", test_update_user),
        ("邀請新用戶", test_invite_user),
        ("獲取團隊列表", test_get_teams),
        ("獲取團隊詳情", test_get_team_details),
        ("更新團隊資訊", test_update_team),
        ("獲取權限列表", test_get_permissions),
        ("獲取角色列表", test_get_roles),
        ("權限檢查機制", test_permission_system),
        ("用戶角色權限映射", test_user_role_permissions)
    ]
    
    # 測試數據存儲
    test_data = {}
    
    for test_name, test_func in test_cases:
        test_results["total"] += 1
        print(f"\n🧪 測試 {test_results['total']}: {test_name}")
        print("-" * 60)
        
        try:
            # 執行測試並傳入測試數據
            result = test_func(test_data)
            
            if result.get("success", False):
                test_results["passed"] += 1
                print(f"✅ {test_name} - 通過")
                
                # 保存測試數據供後續使用
                if "data" in result:
                    test_data[test_name] = result["data"]
                    
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
    print("📊 團隊協作系統測試報告")
    print("=" * 80)
    
    print(f"總測試數: {test_results['total']}")
    print(f"通過測試: {test_results['passed']}")
    print(f"失敗測試: {test_results['failed']}")
    
    success_rate = (test_results['passed'] / test_results['total']) * 100
    print(f"成功率: {success_rate:.1f}%")
    
    # 功能特色總結
    print(f"\n✅ 團隊協作系統功能特色:")
    print("   - 👥 完整的用戶管理 (CRUD 操作)")
    print("   - 🔐 基於角色的存取控制 (RBAC)")
    print("   - 🎭 靈活的角色與權限系統")
    print("   - 🏢 團隊管理與協作功能")
    print("   - ✉️ 用戶邀請與審批機制")
    print("   - 🛡️ 完整的權限檢查與安全控制")
    print("   - 📊 用戶行為與團隊統計分析")
    
    # 系統評估
    if success_rate >= 95:
        print("\n🎉 優秀！團隊協作系統功能完整且運行穩定")
        grade = "A+"
    elif success_rate >= 85:
        print("\n👍 良好！團隊協作系統基本功能正常")
        grade = "A"
    elif success_rate >= 70:
        print("\n👌 可接受！團隊協作系統需要一些改進")
        grade = "B"
    else:
        print("\n⚠️ 需要改進！團隊協作系統存在較多問題")
        grade = "C"
    
    print(f"系統評級: {grade}")
    
    return success_rate >= 80


def test_api_health(test_data):
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


def test_get_users(test_data):
    """測試獲取用戶列表"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/users", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                users = data["data"]["users"]
                roles = data["data"]["roles"] 
                permissions = data["data"]["permissions"]
                
                print(f"   獲取到 {len(users)} 個用戶")
                print(f"   系統角色: {len(roles)} 種")
                print(f"   系統權限: {len(permissions)} 個")
                
                # 分析用戶分佈
                role_counts = {}
                status_counts = {}
                for user in users:
                    role = user.get("role", "unknown")
                    status = user.get("status", "unknown")
                    role_counts[role] = role_counts.get(role, 0) + 1
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"   角色分佈: {role_counts}")
                print(f"   狀態分佈: {status_counts}")
                
                return {
                    "success": True,
                    "message": f"成功獲取 {len(users)} 個用戶",
                    "data": {"users": users, "roles": roles, "permissions": permissions}
                }
            else:
                return {"success": False, "error": data.get("error", "API返回失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"請求失敗: {str(e)}"}


def test_get_user_details(test_data):
    """測試獲取特定用戶資料"""
    if "獲取用戶列表" not in test_data:
        return {"success": False, "error": "需要先獲取用戶列表"}
    
    users = test_data["獲取用戶列表"]["users"]
    if not users:
        return {"success": False, "error": "沒有可用的用戶數據"}
    
    try:
        # 測試獲取第一個用戶的詳情
        test_user = users[0]
        user_id = test_user["id"]
        
        response = requests.get(f"{API_BASE}/api/v1/users/{user_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                user = data["data"]["user"]
                
                print(f"   用戶姓名: {user['name']}")
                print(f"   電子郵件: {user['email']}")
                print(f"   角色: {user['role']}")
                print(f"   部門: {user.get('department', 'N/A')}")
                print(f"   權限數量: {len(user.get('permissions', []))}")
                
                return {
                    "success": True,
                    "message": f"成功獲取用戶詳情: {user['name']}"
                }
            else:
                return {"success": False, "error": data.get("error", "獲取失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"獲取用戶詳情失敗: {str(e)}"}


def test_update_user(test_data):
    """測試更新用戶資料"""
    if "獲取用戶列表" not in test_data:
        return {"success": False, "error": "需要先獲取用戶列表"}
    
    users = test_data["獲取用戶列表"]["users"]
    # 找一個非管理員用戶來測試更新
    test_user = None
    for user in users:
        if user["role"] != "admin":
            test_user = user
            break
    
    if not test_user:
        return {"success": False, "error": "沒有可測試的非管理員用戶"}
    
    try:
        user_id = test_user["id"]
        
        # 準備更新數據
        update_data = {
            "name": test_user["name"] + " (已更新)",
            "department": "Test Department"
        }
        
        response = requests.put(
            f"{API_BASE}/api/v1/users/{user_id}",
            json=update_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                updated_user = data["data"]["user"]
                
                print(f"   更新前姓名: {test_user['name']}")
                print(f"   更新後姓名: {updated_user['name']}")
                print(f"   更新前部門: {test_user.get('department', 'N/A')}")
                print(f"   更新後部門: {updated_user.get('department', 'N/A')}")
                
                return {
                    "success": True,
                    "message": f"成功更新用戶: {updated_user['name']}"
                }
            else:
                return {"success": False, "error": data.get("error", "更新失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"更新用戶失敗: {str(e)}"}


def test_invite_user(test_data):
    """測試邀請新用戶"""
    try:
        # 準備邀請數據
        invitation_data = {
            "email": f"test.user.{int(time.time())}@example.com",
            "role": "member",
            "team_id": "team_001",
            "invited_by": "user_001"
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/users/invite",
            json=invitation_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                invitation = data["data"]["invitation"]
                
                print(f"   邀請ID: {invitation['id']}")
                print(f"   邀請郵箱: {invitation['email']}")
                print(f"   邀請角色: {invitation['role']}")
                print(f"   邀請狀態: {invitation['status']}")
                print(f"   過期時間: {invitation['expires_at']}")
                
                return {
                    "success": True,
                    "message": f"成功發送邀請到: {invitation['email']}",
                    "data": {"invitation": invitation}
                }
            else:
                return {"success": False, "error": data.get("error", "邀請失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"邀請用戶失敗: {str(e)}"}


def test_get_teams(test_data):
    """測試獲取團隊列表"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/teams", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                teams = data["data"]["teams"]
                
                print(f"   獲取到 {len(teams)} 個團隊")
                
                for team in teams:
                    print(f"   團隊: {team['name']} ({team['member_count']} 成員)")
                
                return {
                    "success": True,
                    "message": f"成功獲取 {len(teams)} 個團隊",
                    "data": {"teams": teams}
                }
            else:
                return {"success": False, "error": data.get("error", "API返回失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"請求失敗: {str(e)}"}


def test_get_team_details(test_data):
    """測試獲取團隊詳情"""
    if "獲取團隊列表" not in test_data:
        return {"success": False, "error": "需要先獲取團隊列表"}
    
    teams = test_data["獲取團隊列表"]["teams"]
    if not teams:
        return {"success": False, "error": "沒有可用的團隊數據"}
    
    try:
        # 測試獲取第一個團隊的詳情
        test_team = teams[0]
        team_id = test_team["id"]
        
        response = requests.get(f"{API_BASE}/api/v1/teams/{team_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                team = data["data"]["team"]
                
                print(f"   團隊名稱: {team['name']}")
                print(f"   團隊描述: {team.get('description', 'N/A')}")
                print(f"   成員數量: {team['member_count']}")
                print(f"   團隊擁有者: {team['owner_id']}")
                
                # 顯示成員詳情
                print(f"   成員列表:")
                for member in team.get("member_details", []):
                    print(f"     - {member['name']} ({member['role']})")
                
                return {
                    "success": True,
                    "message": f"成功獲取團隊詳情: {team['name']}"
                }
            else:
                return {"success": False, "error": data.get("error", "獲取失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"獲取團隊詳情失敗: {str(e)}"}


def test_update_team(test_data):
    """測試更新團隊資訊"""
    if "獲取團隊列表" not in test_data:
        return {"success": False, "error": "需要先獲取團隊列表"}
    
    teams = test_data["獲取團隊列表"]["teams"]
    if not teams:
        return {"success": False, "error": "沒有可用的團隊數據"}
    
    try:
        test_team = teams[0]
        team_id = test_team["id"]
        
        # 準備更新數據
        update_data = {
            "name": test_team["name"] + " (已更新)",
            "description": "這是更新後的團隊描述",
            "settings": {
                "allow_member_invite": True,
                "require_approval_for_publish": False
            }
        }
        
        response = requests.put(
            f"{API_BASE}/api/v1/teams/{team_id}",
            json=update_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                updated_team = data["data"]["team"]
                
                print(f"   更新前名稱: {test_team['name']}")
                print(f"   更新後名稱: {updated_team['name']}")
                print(f"   更新後描述: {updated_team.get('description', 'N/A')}")
                
                return {
                    "success": True,
                    "message": f"成功更新團隊: {updated_team['name']}"
                }
            else:
                return {"success": False, "error": data.get("error", "更新失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"更新團隊失敗: {str(e)}"}


def test_get_permissions(test_data):
    """測試獲取權限列表"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/permissions", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                permissions = data["data"]["permissions"]
                permissions_by_category = data["data"]["permissions_by_category"]
                
                print(f"   總權限數: {len(permissions)}")
                print(f"   權限類別: {len(permissions_by_category)}")
                
                for category, perms in permissions_by_category.items():
                    print(f"     {category}: {len(perms)} 個權限")
                
                return {
                    "success": True,
                    "message": f"成功獲取 {len(permissions)} 個權限",
                    "data": {"permissions": permissions}
                }
            else:
                return {"success": False, "error": data.get("error", "API返回失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"請求失敗: {str(e)}"}


def test_get_roles(test_data):
    """測試獲取角色列表"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/roles", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                roles = data["data"]["roles"]
                permissions = data["data"]["permissions"]
                
                print(f"   總角色數: {len(roles)}")
                print(f"   系統權限: {len(permissions)}")
                
                for role_id, role in roles.items():
                    print(f"     {role['name']}: {len(role['permissions'])} 個權限 (級別 {role['level']})")
                
                return {
                    "success": True,
                    "message": f"成功獲取 {len(roles)} 個角色",
                    "data": {"roles": roles, "permissions": permissions}
                }
            else:
                return {"success": False, "error": data.get("error", "API返回失敗")}
        else:
            return {"success": False, "error": f"HTTP錯誤: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"請求失敗: {str(e)}"}


def test_permission_system(test_data):
    """測試權限檢查機制"""
    if "獲取角色列表" not in test_data:
        return {"success": False, "error": "需要先獲取角色列表"}
    
    try:
        roles = test_data["獲取角色列表"]["roles"]
        permissions = test_data["獲取角色列表"]["permissions"]
        
        # 驗證角色權限邏輯
        role_levels = []
        for role_id, role in roles.items():
            role_levels.append((role_id, role["level"], len(role["permissions"])))
        
        # 按權限級別排序
        role_levels.sort(key=lambda x: x[1], reverse=True)
        
        print("   角色權限層次結構:")
        for role_id, level, perm_count in role_levels:
            role_name = roles[role_id]["name"]
            print(f"     {role_name} (級別 {level}): {perm_count} 個權限")
        
        # 驗證管理員應該有最多權限
        admin_role = roles.get("admin")
        if admin_role and admin_role["level"] == max(role["level"] for role in roles.values()):
            admin_perms = len(admin_role["permissions"])
            total_perms = len(permissions)
            
            print(f"\n   權限覆蓋率驗證:")
            print(f"     管理員權限: {admin_perms}/{total_perms} ({admin_perms/total_perms*100:.1f}%)")
            
            # 驗證權限類別分佈
            categories = set()
            for perm in permissions.values():
                categories.add(perm["category"])
            
            print(f"     權限類別: {len(categories)} 種")
            
            return {
                "success": True,
                "message": f"權限系統驗證通過，共 {len(roles)} 個角色，{len(permissions)} 個權限"
            }
        else:
            return {"success": False, "error": "管理員角色權限配置異常"}
            
    except Exception as e:
        return {"success": False, "error": f"權限系統測試失敗: {str(e)}"}


def test_user_role_permissions(test_data):
    """測試用戶角色權限映射"""
    if "獲取用戶列表" not in test_data or "獲取角色列表" not in test_data:
        return {"success": False, "error": "需要先獲取用戶和角色列表"}
    
    try:
        users = test_data["獲取用戶列表"]["users"]
        roles = test_data["獲取角色列表"]["roles"]
        
        # 驗證每個用戶的權限是否與其角色匹配
        validation_results = []
        
        for user in users:
            user_role = user.get("role")
            user_permissions = set(user.get("permissions", []))
            
            if user_role in roles:
                expected_permissions = set(roles[user_role]["permissions"])
                
                # 檢查權限是否匹配
                is_match = user_permissions == expected_permissions
                missing_perms = expected_permissions - user_permissions
                extra_perms = user_permissions - expected_permissions
                
                validation_results.append({
                    "user": user["name"],
                    "role": user_role,
                    "is_match": is_match,
                    "missing": len(missing_perms),
                    "extra": len(extra_perms)
                })
                
                print(f"   {user['name']} ({user_role}): {'✅' if is_match else '❌'}")
                if not is_match:
                    if missing_perms:
                        print(f"     缺少權限: {len(missing_perms)} 個")
                    if extra_perms:
                        print(f"     額外權限: {len(extra_perms)} 個")
        
        # 計算匹配率
        total_users = len(validation_results)
        matching_users = sum(1 for result in validation_results if result["is_match"])
        match_rate = (matching_users / total_users) * 100 if total_users > 0 else 0
        
        print(f"\n   用戶權限匹配統計:")
        print(f"     總用戶數: {total_users}")
        print(f"     匹配用戶: {matching_users}")
        print(f"     匹配率: {match_rate:.1f}%")
        
        return {
            "success": match_rate >= 90,  # 90%以上匹配率視為成功
            "message": f"用戶角色權限映射驗證完成，匹配率 {match_rate:.1f}%"
        }
        
    except Exception as e:
        return {"success": False, "error": f"用戶角色權限測試失敗: {str(e)}"}


if __name__ == "__main__":
    print("🚀 團隊協作系統綜合測試開始")
    print(f"📡 API地址: {API_BASE}")
    print(f"🕒 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_team_collaboration_system()
    
    print(f"\n🎯 測試總結: {'成功' if success else '需要改進'}")
    
    exit(0 if success else 1)