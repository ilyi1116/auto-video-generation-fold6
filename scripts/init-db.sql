-- 初始化資料庫腳本
-- 創建基礎資料庫和用戶 (如果不存在)

-- 創建資料庫 (在 Docker 中由 POSTGRES_DB 環境變數處理)
-- CREATE DATABASE IF NOT EXISTS auto_video_db;

-- 創建擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 用於全文搜索

-- 創建用戶角色
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'auto_video_user') THEN
      
      CREATE ROLE auto_video_user LOGIN PASSWORD 'secure_password_change_in_production';
   END IF;
END
$do$;

-- 授權
GRANT CONNECT ON DATABASE auto_video_db TO auto_video_user;
GRANT USAGE ON SCHEMA public TO auto_video_user;
GRANT CREATE ON SCHEMA public TO auto_video_user;

-- 為表格和序列授權 (將在表格創建後自動應用)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO auto_video_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO auto_video_user;

-- 創建索引 (在表格創建後)
-- 這些將由 SQLAlchemy 處理，但可以在這裡預定義一些特殊索引

-- 系統配置表的初始數據將通過應用程序插入