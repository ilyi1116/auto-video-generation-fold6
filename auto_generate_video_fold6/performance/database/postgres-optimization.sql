-- Auto Video System PostgreSQL 效能優化配置
-- 針對聲音克隆和影片生成工作負載的資料庫調優

-- ====================================
-- 1. 連接和記憶體設定
-- ====================================

-- 調整連接設定
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- 工作記憶體調整
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET hash_mem_multiplier = 2.0;

-- ====================================
-- 2. WAL 和檢查點優化
-- ====================================

-- WAL 設定優化
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET max_wal_size = '1GB';
ALTER SYSTEM SET min_wal_size = '80MB';
ALTER SYSTEM SET checkpoint_timeout = '15min';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- 同步設定（根據需求調整）
ALTER SYSTEM SET synchronous_commit = 'on';
ALTER SYSTEM SET fsync = 'on';

-- ====================================
-- 3. 查詢優化設定
-- ====================================

-- 查詢計劃器設定
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET seq_page_cost = 1.0;
ALTER SYSTEM SET cpu_tuple_cost = 0.01;
ALTER SYSTEM SET cpu_index_tuple_cost = 0.005;
ALTER SYSTEM SET cpu_operator_cost = 0.0025;

-- 統計資訊設定
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET track_activities = 'on';
ALTER SYSTEM SET track_counts = 'on';
ALTER SYSTEM SET track_io_timing = 'on';
ALTER SYSTEM SET track_functions = 'all';

-- ====================================
-- 4. 自動清理設定
-- ====================================

-- 自動清理調優
ALTER SYSTEM SET autovacuum = 'on';
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '20s';
ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;
ALTER SYSTEM SET autovacuum_analyze_threshold = 50;
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;

-- ====================================
-- 5. 日誌設定（用於效能監控）
-- ====================================

-- 慢查詢日誌
ALTER SYSTEM SET log_min_duration_statement = '1000ms';
ALTER SYSTEM SET log_checkpoints = 'on';
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
ALTER SYSTEM SET log_lock_waits = 'on';
ALTER SYSTEM SET log_temp_files = '10MB';

-- 日誌細節
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_statement = 'none';
ALTER SYSTEM SET log_duration = 'off';

-- ====================================
-- 6. 索引優化
-- ====================================

-- 用戶表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active 
ON auth_users(email) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at 
ON auth_users(created_at);

-- 音頻文件表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audio_files_user_status 
ON audio_files(user_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audio_files_created_at 
ON audio_files(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audio_files_size 
ON audio_files(file_size);

-- 訓練任務表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_jobs_user_status 
ON training_jobs(user_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_jobs_created_status 
ON training_jobs(created_at, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_jobs_priority 
ON training_jobs(priority DESC, created_at);

-- 推論請求表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inference_requests_user_created 
ON inference_requests(user_id, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inference_requests_status_priority 
ON inference_requests(status, priority DESC);

-- 影片項目表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_video_projects_user_status 
ON video_projects(user_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_video_projects_created_at 
ON video_projects(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_video_projects_title_search 
ON video_projects USING gin(to_tsvector('english', title));

-- 社群媒體發布表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_social_posts_user_platform 
ON social_media_posts(user_id, platform);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_social_posts_scheduled_at 
ON social_media_posts(scheduled_at) WHERE status = 'scheduled';

-- 分析數據表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_user_event 
ON analytics_events(user_id, event_type, timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_timestamp 
ON analytics_events(timestamp);

-- ====================================
-- 7. 分區表設定（針對大量數據）
-- ====================================

-- 分析事件表按月分區
CREATE TABLE IF NOT EXISTS analytics_events_partitioned (
    LIKE analytics_events INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- 創建分區（最近6個月）
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    start_date := DATE_TRUNC('month', NOW() - INTERVAL '6 months');
    
    FOR i IN 0..11 LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'analytics_events_' || TO_CHAR(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF analytics_events_partitioned 
                       FOR VALUES FROM (%L) TO (%L)', 
                       partition_name, start_date, end_date);
        
        start_date := end_date;
    END LOOP;
END $$;

-- ====================================
-- 8. 物化視圖（加速複雜查詢）
-- ====================================

-- 用戶統計物化視圖
CREATE MATERIALIZED VIEW IF NOT EXISTS user_statistics AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(DISTINCT af.id) as total_audio_files,
    COUNT(DISTINCT tj.id) as total_training_jobs,
    COUNT(DISTINCT ir.id) as total_inference_requests,
    COUNT(DISTINCT vp.id) as total_video_projects,
    AVG(CASE WHEN tj.status = 'completed' THEN tj.duration_seconds END) as avg_training_time,
    SUM(af.file_size) as total_storage_used,
    MAX(u.last_login_at) as last_activity
FROM auth_users u
LEFT JOIN audio_files af ON u.id = af.user_id
LEFT JOIN training_jobs tj ON u.id = tj.user_id
LEFT JOIN inference_requests ir ON u.id = ir.user_id
LEFT JOIN video_projects vp ON u.id = vp.user_id
WHERE u.is_active = true
GROUP BY u.id, u.email;

CREATE UNIQUE INDEX ON user_statistics (user_id);

-- 每日統計物化視圖
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_statistics AS
SELECT 
    DATE(created_at) as date,
    'audio_upload' as metric_type,
    COUNT(*) as count,
    SUM(file_size) as total_size
FROM audio_files
GROUP BY DATE(created_at)
UNION ALL
SELECT 
    DATE(created_at) as date,
    'training_job' as metric_type,
    COUNT(*) as count,
    NULL as total_size
FROM training_jobs
GROUP BY DATE(created_at)
UNION ALL
SELECT 
    DATE(created_at) as date,
    'inference_request' as metric_type,
    COUNT(*) as count,
    NULL as total_size
FROM inference_requests
GROUP BY DATE(created_at);

CREATE INDEX ON daily_statistics (date, metric_type);

-- ====================================
-- 9. 函數和觸發器優化
-- ====================================

-- 自動更新 updated_at 的函數
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 為主要表添加自動更新觸發器
DO $$
DECLARE
    table_name TEXT;
    tables TEXT[] := ARRAY[
        'auth_users', 'audio_files', 'training_jobs', 
        'inference_requests', 'video_projects', 'social_media_posts'
    ];
BEGIN
    FOREACH table_name IN ARRAY tables
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trigger_update_updated_at ON %I;
            CREATE TRIGGER trigger_update_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        ', table_name, table_name);
    END LOOP;
END $$;

-- ====================================
-- 10. 定期維護腳本
-- ====================================

-- 物化視圖更新函數
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_statistics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_statistics;
    
    -- 記錄更新時間
    INSERT INTO maintenance_log (operation, completed_at) 
    VALUES ('refresh_materialized_views', NOW());
END;
$$ LANGUAGE plpgsql;

-- 清理舊分區函數
CREATE OR REPLACE FUNCTION cleanup_old_partitions()
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    cutoff_date DATE := NOW() - INTERVAL '12 months';
BEGIN
    FOR partition_name IN 
        SELECT schemaname||'.'||tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'analytics_events_%'
        AND tablename < 'analytics_events_' || TO_CHAR(cutoff_date, 'YYYY_MM')
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || partition_name;
        RAISE NOTICE 'Dropped partition: %', partition_name;
    END LOOP;
    
    INSERT INTO maintenance_log (operation, completed_at) 
    VALUES ('cleanup_old_partitions', NOW());
END;
$$ LANGUAGE plpgsql;

-- ====================================
-- 11. 監控和統計表
-- ====================================

-- 維護日誌表
CREATE TABLE IF NOT EXISTS maintenance_log (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(100) NOT NULL,
    completed_at TIMESTAMP DEFAULT NOW(),
    details JSONB
);

-- 查詢效能統計表
CREATE TABLE IF NOT EXISTS query_performance_log (
    id SERIAL PRIMARY KEY,
    query_hash TEXT NOT NULL,
    query_text TEXT,
    execution_time_ms NUMERIC,
    rows_returned INTEGER,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON query_performance_log (query_hash, recorded_at);
CREATE INDEX ON query_performance_log (execution_time_ms DESC);

-- ====================================
-- 完成設定
-- ====================================

-- 重新載入配置（需要重啟）
SELECT pg_reload_conf();

-- 更新統計資訊
ANALYZE;

-- 記錄優化完成
INSERT INTO maintenance_log (operation, details) 
VALUES (
    'database_optimization_applied', 
    jsonb_build_object(
        'version', '1.0',
        'applied_at', NOW(),
        'optimizations', ARRAY[
            'connection_settings',
            'wal_optimization', 
            'query_optimization',
            'autovacuum_tuning',
            'indexing_strategy',
            'partitioning',
            'materialized_views'
        ]
    )
);

-- 顯示完成訊息
DO $$
BEGIN
    RAISE NOTICE '✅ PostgreSQL 效能優化完成！';
    RAISE NOTICE '📊 建議重啟 PostgreSQL 以套用所有設定';
    RAISE NOTICE '🔍 使用以下查詢監控效能：';
    RAISE NOTICE '   - SELECT * FROM user_statistics;';
    RAISE NOTICE '   - SELECT * FROM daily_statistics;';
    RAISE NOTICE '   - SELECT * FROM maintenance_log ORDER BY completed_at DESC;';
END $$;