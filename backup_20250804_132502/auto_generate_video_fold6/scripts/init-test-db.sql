-- 測試資料庫初始化腳本
-- 為 TDD 工作流程準備測試環境

-- 建立測試專用的擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 創建用戶表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建趨勢表
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    platform VARCHAR(100) NOT NULL,
    engagement_score DECIMAL(5,2) DEFAULT 0.0,
    view_count BIGINT DEFAULT 0,
    hashtags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建影片項目表  
CREATE TABLE IF NOT EXISTS video_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    status VARCHAR(100) DEFAULT 'pending',
    workflow_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建排程任務表
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(100) DEFAULT 'scheduled',
    config JSONB,
    scheduled_time TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建發布記錄表
CREATE TABLE IF NOT EXISTS publish_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publish_id VARCHAR(255) UNIQUE NOT NULL,
    video_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    platform VARCHAR(100) NOT NULL,
    status VARCHAR(100) DEFAULT 'pending',
    platform_post_id VARCHAR(255),
    metadata JSONB,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建工作流程狀態表
CREATE TABLE IF NOT EXISTS workflow_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    status VARCHAR(100) DEFAULT 'pending',
    current_step VARCHAR(100),
    total_steps INTEGER DEFAULT 0,
    completed_steps INTEGER DEFAULT 0,
    step_results JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 測試資料清理函數
CREATE OR REPLACE FUNCTION cleanup_test_data()
RETURNS VOID AS $$
BEGIN
    -- 清理所有測試資料表
    TRUNCATE TABLE IF EXISTS users CASCADE;
    TRUNCATE TABLE IF EXISTS projects CASCADE;
    TRUNCATE TABLE IF EXISTS videos CASCADE;
    TRUNCATE TABLE IF EXISTS scripts CASCADE;
    TRUNCATE TABLE IF EXISTS voice_clones CASCADE;
    TRUNCATE TABLE IF EXISTS trends CASCADE;
    TRUNCATE TABLE IF EXISTS social_posts CASCADE;
    
    -- 重置序列
    ALTER SEQUENCE IF EXISTS users_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS projects_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS videos_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS scripts_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS voice_clones_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS trends_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS social_posts_id_seq RESTART WITH 1;
    
    RAISE NOTICE '✅ 測試資料已清理';
END;
$$ LANGUAGE plpgsql;

-- 測試資料生成函數
CREATE OR REPLACE FUNCTION create_test_data()
RETURNS VOID AS $$
BEGIN
    -- 插入測試用戶
    INSERT INTO users (user_id, email, username, hashed_password, is_active, created_at, updated_at)
    VALUES 
        ('e2e_test_user', 'e2e@test.com', 'e2e_tester', '$2b$12$test_hash', true, NOW(), NOW()),
        ('admin_user', 'admin@test.com', 'admin', '$2b$12$admin_hash', true, NOW(), NOW())
    ON CONFLICT (user_id) DO NOTHING;
    
    -- 插入測試趨勢數據
    INSERT INTO trends (keyword, platform, engagement_score, view_count, hashtags)
    VALUES 
        ('AI technology breakthrough', 'tiktok', 85.50, 1250000, ARRAY['#AI', '#technology', '#innovation']),
        ('Machine learning tutorial', 'youtube', 78.20, 890000, ARRAY['#ML', '#tutorial', '#coding']),
        ('Automation tools for business', 'tiktok', 92.10, 2100000, ARRAY['#automation', '#business', '#tools']),
        ('Tech innovation 2024', 'youtube', 73.80, 650000, ARRAY['#tech', '#innovation', '#2024']),
        ('Future of programming', 'tiktok', 88.90, 1800000, ARRAY['#programming', '#future', '#coding'])
    ON CONFLICT DO NOTHING;
    
    -- 插入測試影片項目
    INSERT INTO video_projects (project_id, user_id, title, description, status, metadata)
    VALUES 
        ('test_project_1', 'e2e_test_user', 'AI 技術突破解析', '深入分析最新的 AI 技術發展', 'completed', 
         '{"duration": 30, "quality": "1080p", "format": "mp4"}'),
        ('test_project_2', 'e2e_test_user', '自動化工具推薦', '介紹最新的商業自動化工具', 'pending',
         '{"duration": 60, "quality": "1080p", "format": "mp4"}')
    ON CONFLICT (project_id) DO NOTHING;
         
    -- 插入測試工作流程狀態
    INSERT INTO workflow_status (workflow_id, user_id, status, current_step, total_steps, completed_steps, step_results)
    VALUES 
        ('workflow_test_1', 'e2e_test_user', 'completed', 'video_composition', 7, 7,
         '{"trend_analysis": {"success": true}, "script_generation": {"success": true}, "video_composition": {"success": true}}'),
        ('workflow_test_2', 'e2e_test_user', 'in_progress', 'image_generation', 7, 3,
         '{"trend_analysis": {"success": true}, "script_generation": {"success": true}, "image_generation": {"success": false, "error": "API rate limit"}}')
    ON CONFLICT (workflow_id) DO NOTHING;
    
    RAISE NOTICE '✅ 創業者模式測試資料已建立';
END;
$$ LANGUAGE plpgsql;

-- 預設執行清理和測試資料建立
SELECT cleanup_test_data();
SELECT create_test_data();