-- Video Generation System Database Schema
-- 擴展現有聲音克隆系統為短影音生成系統

-- 影片項目表
CREATE TABLE IF NOT EXISTS video_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- draft, processing, completed, failed, published
    settings JSONB DEFAULT '{}', -- 影片參數設定
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 關鍵字管理表
CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    trending_score INTEGER DEFAULT 0,
    search_volume INTEGER DEFAULT 0,
    last_analyzed TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 項目關鍵字關聯表
CREATE TABLE IF NOT EXISTS project_keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    keyword_id UUID NOT NULL,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES video_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
    UNIQUE(project_id, keyword_id)
);

-- 腳本生成記錄表
CREATE TABLE IF NOT EXISTS scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    content TEXT NOT NULL,
    style VARCHAR(100), -- engaging, informative, humorous
    duration_seconds INTEGER,
    ai_model VARCHAR(100), -- gemini-pro, gpt-4, etc.
    generation_params JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'generated', -- generated, approved, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES video_projects(id) ON DELETE CASCADE
);

-- 語音合成記錄表
CREATE TABLE IF NOT EXISTS voice_synthesis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    script_id UUID NOT NULL,
    voice_style VARCHAR(100), -- natural, professional, energetic
    audio_file_path VARCHAR(500),
    duration_seconds FLOAT,
    ai_service VARCHAR(100), -- suno-ai-pro, elevenlabs, etc.
    synthesis_params JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
);

-- 圖像生成記錄表
CREATE TABLE IF NOT EXISTS image_generation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    prompt TEXT NOT NULL,
    style VARCHAR(100), -- modern, vintage, minimalist
    aspect_ratio VARCHAR(20), -- 9:16, 16:9, 1:1
    image_file_path VARCHAR(500),
    ai_service VARCHAR(100), -- stable-diffusion, dall-e, midjourney
    generation_params JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES video_projects(id) ON DELETE CASCADE
);

-- 影片生成記錄表
CREATE TABLE IF NOT EXISTS video_generation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    script_id UUID,
    voice_id UUID,
    video_file_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    duration_seconds FLOAT,
    resolution VARCHAR(20), -- 720p, 1080p, 4k
    aspect_ratio VARCHAR(20),
    file_size_mb FLOAT,
    processing_params JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    FOREIGN KEY (project_id) REFERENCES video_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (script_id) REFERENCES scripts(id),
    FOREIGN KEY (voice_id) REFERENCES voice_synthesis(id)
);

-- 社交平台配置表
CREATE TABLE IF NOT EXISTS social_platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    platform VARCHAR(50) NOT NULL, -- tiktok, youtube, instagram
    platform_user_id VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    account_info JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, platform)
);

-- 發布排程表
CREATE TABLE IF NOT EXISTS publish_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    platform_id UUID NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    title VARCHAR(255),
    description TEXT,
    tags TEXT[], -- 標籤陣列
    privacy_setting VARCHAR(50) DEFAULT 'public', -- public, private, unlisted
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, publishing, published, failed
    platform_post_id VARCHAR(255), -- 發布後的平台ID
    published_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES video_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES social_platforms(id) ON DELETE CASCADE
);

-- 趨勢分析表
CREATE TABLE IF NOT EXISTS trend_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword_id UUID NOT NULL,
    platform VARCHAR(50) NOT NULL,
    analysis_date DATE NOT NULL,
    view_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    share_count BIGINT DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0,
    trending_score INTEGER DEFAULT 0,
    analysis_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
    UNIQUE(keyword_id, platform, analysis_date)
);

-- 使用者點數系統表 (可選功能)
CREATE TABLE IF NOT EXISTS user_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    total_credits INTEGER DEFAULT 0,
    used_credits INTEGER DEFAULT 0,
    bonus_credits INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 點數使用記錄表
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    project_id UUID,
    transaction_type VARCHAR(50) NOT NULL, -- deduct, add, bonus
    amount INTEGER NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES video_projects(id)
);

-- 系統任務記錄表
CREATE TABLE IF NOT EXISTS system_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(100) NOT NULL, -- keyword_analysis, video_generation, publishing
    entity_id UUID, -- 關聯的項目或其他實體ID
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed, retrying
    priority INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    task_data JSONB DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引提高查詢效能
CREATE INDEX IF NOT EXISTS idx_video_projects_user_id ON video_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_video_projects_status ON video_projects(status);
CREATE INDEX IF NOT EXISTS idx_keywords_trending_score ON keywords(trending_score DESC);
CREATE INDEX IF NOT EXISTS idx_scripts_project_id ON scripts(project_id);
CREATE INDEX IF NOT EXISTS idx_voice_synthesis_script_id ON voice_synthesis(script_id);
CREATE INDEX IF NOT EXISTS idx_image_generation_project_id ON image_generation(project_id);
CREATE INDEX IF NOT EXISTS idx_video_generation_project_id ON video_generation(project_id);
CREATE INDEX IF NOT EXISTS idx_publish_schedule_scheduled_time ON publish_schedule(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_date ON trend_analysis(analysis_date DESC);
CREATE INDEX IF NOT EXISTS idx_system_tasks_status ON system_tasks(status);
CREATE INDEX IF NOT EXISTS idx_system_tasks_scheduled_at ON system_tasks(scheduled_at);

-- 觸發器：自動更新 updated_at 欄位
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_video_projects_updated_at BEFORE UPDATE
    ON video_projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_social_platforms_updated_at BEFORE UPDATE
    ON social_platforms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();