-- 測試資料庫初始化腳本
-- 為 TDD 工作流程準備測試環境

-- 建立測試用戶和資料庫
CREATE USER IF NOT EXISTS test_user WITH PASSWORD 'test_password';
CREATE DATABASE IF NOT EXISTS test_db OWNER test_user;

-- 切換到測試資料庫
\c test_db;

-- 賦予測試用戶完整權限
GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;

-- 建立測試專用的擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

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
    INSERT INTO users (id, email, username, hashed_password, is_active, created_at, updated_at)
    VALUES 
        (gen_random_uuid(), 'test@example.com', 'testuser', '$2b$12$test_hash', true, NOW(), NOW()),
        (gen_random_uuid(), 'admin@example.com', 'admin', '$2b$12$admin_hash', true, NOW(), NOW())
    ON CONFLICT (email) DO NOTHING;
    
    RAISE NOTICE '✅ 測試資料已建立';
END;
$$ LANGUAGE plpgsql;

-- 預設執行清理和測試資料建立
SELECT cleanup_test_data();
SELECT create_test_data();