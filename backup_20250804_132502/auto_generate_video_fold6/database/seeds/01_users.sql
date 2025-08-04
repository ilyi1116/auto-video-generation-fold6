-- Seed data for users and authentication system
-- This script creates initial users, roles, and sample data for development

-- Insert default roles
INSERT INTO user_roles (id, name, description, permissions, is_active) VALUES
(gen_random_uuid(), 'super_admin', 'Super Administrator with full system access', 
 '["user:read", "user:write", "user:delete", "system:manage", "video:manage", "ai:manage", "analytics:read"]', true),
(gen_random_uuid(), 'admin', 'Administrator with most system privileges', 
 '["user:read", "user:write", "video:manage", "ai:manage", "analytics:read"]', true),
(gen_random_uuid(), 'creator', 'Content creator with video generation capabilities', 
 '["user:read", "video:create", "video:read", "video:update", "ai:use"]', true),
(gen_random_uuid(), 'viewer', 'Basic user with viewing privileges', 
 '["user:read", "video:read"]', true);

-- Insert default super admin user (password: admin123456)
-- Note: In production, change this password immediately!
WITH new_user AS (
    INSERT INTO users (
        id, email, username, hashed_password, full_name, 
        is_active, is_superuser, is_verified, preferred_language
    ) VALUES (
        gen_random_uuid(),
        'admin@autovideo.com',
        'admin',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMRJqhtuGRxuVxvgl2B22WmT.W', -- admin123456
        'System Administrator',
        true,
        true,
        true,
        'en'
    ) RETURNING id
)
INSERT INTO user_role_assignments (user_id, role_id, assigned_by)
SELECT 
    new_user.id,
    ur.id,
    new_user.id
FROM new_user, user_roles ur 
WHERE ur.name = 'super_admin';

-- Insert demo creator user (password: creator123)
WITH new_user AS (
    INSERT INTO users (
        id, email, username, hashed_password, full_name, 
        is_active, is_superuser, is_verified, preferred_language,
        bio, avatar_url
    ) VALUES (
        gen_random_uuid(),
        'creator@autovideo.com',
        'demo_creator',
        '$2b$12$EIXKDfN7qibTlx.Y8OYg6.ZjQs5XZbvEQGYGv8YF8kGpE5Bm6XV6.', -- creator123
        'Demo Content Creator',
        true,
        false,
        true,
        'en',
        'Professional content creator specializing in viral short-form videos',
        'https://via.placeholder.com/150/4A90E2/FFFFFF?text=DC'
    ) RETURNING id
)
INSERT INTO user_role_assignments (user_id, role_id)
SELECT 
    new_user.id,
    ur.id
FROM new_user, user_roles ur 
WHERE ur.name = 'creator';

-- Insert sample keywords for trending analysis
INSERT INTO keywords (id, keyword, category, trending_score, search_volume, metadata) VALUES
(gen_random_uuid(), 'AI automation', 'Technology', 85, 12500, '{"platforms": ["tiktok", "youtube"], "last_spike": "2025-01-20"}'),
(gen_random_uuid(), 'productivity hacks', 'Lifestyle', 92, 18700, '{"platforms": ["tiktok", "instagram"], "demographic": "18-35"}'),
(gen_random_uuid(), 'coding tips', 'Education', 78, 9400, '{"platforms": ["youtube", "tiktok"], "engagement_rate": 8.5}'),
(gen_random_uuid(), 'morning routine', 'Lifestyle', 88, 15600, '{"platforms": ["instagram", "tiktok"], "best_time": "06:00-08:00"}'),
(gen_random_uuid(), 'small business', 'Business', 76, 11200, '{"platforms": ["linkedin", "youtube"], "target": "entrepreneurs"}'),
(gen_random_uuid(), 'healthy recipes', 'Food', 82, 14300, '{"platforms": ["instagram", "tiktok"], "seasonal": true}'),
(gen_random_uuid(), 'travel tips', 'Travel', 79, 13100, '{"platforms": ["instagram", "youtube"], "engagement_type": "saves"}'),
(gen_random_uuid(), 'crypto news', 'Finance', 71, 8900, '{"platforms": ["twitter", "youtube"], "volatility": "high"}'),
(gen_random_uuid(), 'fitness motivation', 'Health', 86, 16800, '{"platforms": ["tiktok", "instagram"], "peak_months": ["01", "06"]}'),
(gen_random_uuid(), 'DIY projects', 'Lifestyle', 84, 12900, '{"platforms": ["youtube", "pinterest"], "tools_required": true}');

-- Insert sample system tasks for demonstration
INSERT INTO system_tasks (id, task_type, status, priority, task_data, scheduled_at) VALUES
(gen_random_uuid(), 'keyword_analysis', 'completed', 1, 
 '{"keywords": ["AI automation", "productivity hacks"], "platforms": ["tiktok", "youtube"]}', 
 NOW() - INTERVAL '1 hour'),
(gen_random_uuid(), 'trend_monitoring', 'running', 2, 
 '{"monitoring_interval": "15m", "platforms": ["all"]}', 
 NOW()),
(gen_random_uuid(), 'content_cleanup', 'pending', 0, 
 '{"older_than_days": 30, "content_type": "temp_files"}', 
 NOW() + INTERVAL '1 day');

-- Insert sample user credits for demo creator
WITH demo_user AS (
    SELECT id FROM users WHERE username = 'demo_creator'
)
INSERT INTO user_credits (user_id, total_credits, used_credits, bonus_credits, expires_at)
SELECT 
    id,
    1000,  -- Starting credits
    150,   -- Used credits
    100,   -- Bonus credits
    NOW() + INTERVAL '30 days'
FROM demo_user;

-- Insert sample credit transactions
WITH demo_user AS (
    SELECT id FROM users WHERE username = 'demo_creator'
)
INSERT INTO credit_transactions (user_id, transaction_type, amount, description) VALUES
((SELECT id FROM demo_user), 'add', 1000, 'Welcome bonus credits'),
((SELECT id FROM demo_user), 'add', 100, 'Referral bonus'),
((SELECT id FROM demo_user), 'deduct', -50, 'AI script generation'),
((SELECT id FROM demo_user), 'deduct', -30, 'Voice synthesis'),
((SELECT id FROM demo_user), 'deduct', -70, 'Video generation');

-- Create audit log entries for the seeded data
INSERT INTO audit_logs (user_id, action, resource_type, details, ip_address, status) VALUES
((SELECT id FROM users WHERE username = 'admin'), 'system_seed', 'database', 
 '{"operation": "initial_seed", "tables": ["users", "user_roles", "keywords", "user_credits"]}', 
 '127.0.0.1', 'success'),
((SELECT id FROM users WHERE username = 'demo_creator'), 'user_created', 'user', 
 '{"creation_method": "seed", "role": "creator"}', 
 '127.0.0.1', 'success');