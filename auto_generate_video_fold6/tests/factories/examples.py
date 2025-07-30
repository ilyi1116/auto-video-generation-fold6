# 測試數據工廠使用範例
# 展示如何在 TDD 開發中使用工廠

from typing import Dict, Any
from .user_factory import UserFactory, create_test_users_scenario
from .project_factory import ProjectFactory, create_test_projects_scenario
from .video_factory import VideoFactory, create_test_videos_scenario
from .script_factory import ScriptFactory, create_test_scripts_scenario
from .voice_factory import VoiceCloneFactory, create_test_voices_scenario

# TDD 範例 1: RED 階段測試
def example_red_phase_test():
    """
    RED 階段範例：撰寫會失敗的測試
    使用工廠建立無效數據來測試驗證邏輯
    """
    
    # 建立無效用戶數據來測試驗證
    invalid_user = UserFactory.create_for_red_phase()
    
    # 這些數據應該導致測試失敗
    assert invalid_user.email == "invalid-email"  # 無效 email 格式
    assert invalid_user.username == ""  # 空用戶名
    
    print("RED 階段：建立了會導致測試失敗的無效數據")

# TDD 範例 2: GREEN 階段測試
def example_green_phase_test():
    """
    GREEN 階段範例：建立讓測試通過的最簡數據
    """
    
    # 建立最簡有效數據
    valid_user = UserFactory.create_for_green_phase()
    valid_project = ProjectFactory.create_for_green_phase()
    valid_script = ScriptFactory.create_for_green_phase()
    
    # 這些數據應該讓測試通過
    assert valid_user.username == "testuser"
    assert valid_user.email == "test@example.com"
    assert valid_project.title == "測試專案"
    assert valid_script.content == "這是一個測試腳本的內容。"
    
    print("GREEN 階段：建立了讓測試通過的最簡數據")

# TDD 範例 3: REFACTOR 階段測試
def example_refactor_phase_test():
    """
    REFACTOR 階段範例：確保重構後行為不變
    """
    
    # 建立穩定的測試數據確保重構不破壞功能
    user = UserFactory.create_for_refactor_phase()
    project = ProjectFactory.create_for_refactor_phase()
    
    # 在重構前後，這些斷言應該保持相同結果
    assert user.is_active is True
    assert project.status in ['draft', 'in_progress', 'completed']
    
    print("REFACTOR 階段：確保重構後測試仍然通過")

# 複雜場景範例：完整用戶工作流程測試
def example_complete_user_workflow():
    """
    複雜場景範例：模擬完整的用戶工作流程
    從用戶建立到專案完成的端到端測試
    """
    
    # 1. 建立測試用戶
    user = UserFactory.create_premium_user()
    
    # 2. 為用戶建立專案
    project = ProjectFactory.create_draft_project(user_id=user.id)
    
    # 3. 為專案建立腳本
    script = ScriptFactory.create_educational_script(
        project_id=project.id,
        user_id=user.id
    )
    
    # 4. 建立語音克隆
    voice = VoiceCloneFactory.create_ready_voice(user_id=user.id)
    
    # 5. 生成影片
    video = VideoFactory.create_completed_video(project_id=project.id)
    
    # 驗證完整工作流程
    assert user.is_premium is True
    assert project.user_id == user.id
    assert script.project_id == project.id
    assert voice.user_id == user.id
    assert video.project_id == project.id
    
    print(f"完整工作流程測試：用戶 {user.username} 成功完成影片製作")
    
    return {
        'user': user,
        'project': project,
        'script': script,
        'voice': voice,
        'video': video
    }

# 批次數據測試範例
def example_batch_data_test():
    """
    批次數據測試範例：測試大量數據的處理
    """
    
    # 建立測試用戶
    user = UserFactory.create()
    
    # 批次建立專案
    projects = [
        ProjectFactory.create(user_id=user.id, title=f"批次專案 {i}")
        for i in range(5)
    ]
    
    # 為每個專案建立影片
    videos = []
    for project in projects:
        video = VideoFactory.create_completed_video(project_id=project.id)
        videos.append(video)
    
    # 驗證批次數據
    assert len(projects) == 5
    assert len(videos) == 5
    assert all(p.user_id == user.id for p in projects)
    assert all(v.project_id in [p.id for p in projects] for v in videos)
    
    print(f"批次數據測試：為用戶建立了 {len(projects)} 個專案和 {len(videos)} 個影片")

# 邊界條件測試範例
def example_edge_case_test():
    """
    邊界條件測試範例：測試極限情況
    """
    
    # 建立最小有效數據
    minimal_user = UserFactory.create(
        username="a",  # 最短用戶名
        video_count=0,  # 最少影片數
        follower_count=0  # 最少追蹤者
    )
    
    # 建立最大有效數據
    maximal_user = UserFactory.create(
        username="a" * 50,  # 最長用戶名
        video_count=9999,  # 最多影片數
        follower_count=999999  # 最多追蹤者
    )
    
    # 驗證邊界條件
    assert len(minimal_user.username) == 1
    assert len(maximal_user.username) == 50
    assert minimal_user.video_count == 0
    assert maximal_user.video_count == 9999
    
    print("邊界條件測試：驗證了最小和最大有效值")

# 工廠註冊表範例
def example_factory_registry_usage():
    """
    工廠註冊表使用範例：動態取得工廠
    """
    from .base_factory import FactoryRegistry
    
    # 列出所有註冊的工廠
    factories = FactoryRegistry.list_all()
    print(f"已註冊的工廠: {list(factories.keys())}")
    
    # 動態取得工廠並建立數據
    user_factory = FactoryRegistry.get('user')
    if user_factory:
        user = user_factory.create()
        print(f"透過註冊表建立用戶: {user.username}")

# 測試數據清理範例
def example_test_cleanup():
    """
    測試數據清理範例：確保測試間的隔離
    """
    
    # 建立測試場景
    users_scenario = create_test_users_scenario()
    projects_scenario = create_test_projects_scenario()
    
    # 執行測試邏輯...
    
    # 清理測試數據
    from .user_factory import cleanup_test_users
    from .project_factory import cleanup_test_projects
    
    cleanup_test_users(users_scenario)
    cleanup_test_projects(projects_scenario)
    
    print("測試數據已清理，確保測試隔離")

# 效能測試數據範例
def example_performance_test_data():
    """
    效能測試數據範例：建立大量數據進行效能測試
    """
    
    import time
    
    start_time = time.time()
    
    # 快速建立大量測試數據
    users = [UserFactory.create() for _ in range(100)]
    projects = [ProjectFactory.create() for _ in range(500)]
    videos = [VideoFactory.create() for _ in range(1000)]
    
    end_time = time.time()
    
    print(f"效能測試：在 {end_time - start_time:.2f} 秒內建立了:")
    print(f"- {len(users)} 個用戶")
    print(f"- {len(projects)} 個專案") 
    print(f"- {len(videos)} 個影片")

# 主要範例執行函數
def run_all_examples():
    """執行所有範例"""
    
    print("🧬 TDD 測試數據工廠範例")
    print("=" * 50)
    
    try:
        example_red_phase_test()
        print()
        
        example_green_phase_test()
        print()
        
        example_refactor_phase_test()
        print()
        
        workflow_data = example_complete_user_workflow()
        print()
        
        example_batch_data_test()
        print()
        
        example_edge_case_test()
        print()
        
        example_factory_registry_usage()
        print()
        
        example_test_cleanup()
        print()
        
        example_performance_test_data()
        
        print("=" * 50)
        print("✅ 所有測試數據工廠範例執行完成！")
        
    except Exception as e:
        print(f"❌ 範例執行失敗: {e}")

if __name__ == "__main__":
    run_all_examples()