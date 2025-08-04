-- Seed data for video projects and related tables
-- This creates sample video projects, scripts, and generation records

-- Get demo user ID for reference
-- Sample video projects
WITH demo_user AS (
    SELECT id FROM users WHERE username = 'demo_creator'
)
INSERT INTO video_projects (id, user_id, title, description, status, settings) VALUES
-- Completed project
(gen_random_uuid(), 
 (SELECT id FROM demo_user), 
 '5 AI Tools That Will Change Your Life in 2025',
 'A comprehensive guide to the most impactful AI tools for productivity, creativity, and business growth',
 'completed',
 '{
   "aspect_ratio": "9:16",
   "duration": 60,
   "style": "engaging",
   "target_audience": "entrepreneurs",
   "voice_style": "energetic",
   "music": true,
   "captions": true
 }'),

-- Processing project
(gen_random_uuid(), 
 (SELECT id FROM demo_user), 
 'Morning Routines of Successful Entrepreneurs',
 'Discover the daily habits that top entrepreneurs use to maximize their productivity',
 'processing',
 '{
   "aspect_ratio": "9:16",
   "duration": 45,
   "style": "informative",
   "target_audience": "business",
   "voice_style": "professional",
   "music": true,
   "captions": true
 }'),

-- Draft project
(gen_random_uuid(), 
 (SELECT id FROM demo_user), 
 'Healthy Meal Prep Ideas for Busy People',
 'Quick and nutritious meal prep strategies for people with hectic schedules',
 'draft',
 '{
   "aspect_ratio": "9:16",
   "duration": 30,
   "style": "practical",
   "target_audience": "health-conscious",
   "voice_style": "friendly",
   "music": false,
   "captions": true
 }');

-- Insert project keywords relationships
WITH project_keywords AS (
    SELECT 
        vp.id as project_id,
        k.id as keyword_id,
        CASE 
            WHEN vp.title LIKE '%AI%' THEN 1.0
            WHEN vp.title LIKE '%Entrepreneur%' THEN 0.9
            WHEN vp.title LIKE '%Healthy%' THEN 0.8
            ELSE 0.5
        END as weight
    FROM video_projects vp
    CROSS JOIN keywords k
    WHERE 
        (vp.title LIKE '%AI%' AND k.keyword IN ('AI automation', 'productivity hacks', 'small business')) OR
        (vp.title LIKE '%Entrepreneur%' AND k.keyword IN ('morning routine', 'productivity hacks', 'small business')) OR
        (vp.title LIKE '%Healthy%' AND k.keyword IN ('healthy recipes', 'morning routine'))
)
INSERT INTO project_keywords (project_id, keyword_id, weight)
SELECT project_id, keyword_id, weight FROM project_keywords;

-- Insert sample scripts
WITH demo_projects AS (
    SELECT id, title FROM video_projects WHERE user_id = (SELECT id FROM users WHERE username = 'demo_creator')
)
INSERT INTO scripts (id, project_id, content, style, duration_seconds, ai_model, generation_params, status) VALUES
-- Script for AI Tools project
((SELECT gen_random_uuid()),
 (SELECT id FROM demo_projects WHERE title LIKE '%AI Tools%'),
 'Are you ready to supercharge your productivity? Today I''m sharing 5 AI tools that will literally change how you work in 2025.

First up - ChatGPT for content creation. This isn''t just for writing emails anymore. Use it to brainstorm ideas, create outlines, and even debug your thinking process.

Second - Notion AI for organization. It can summarize your notes, create action items, and help you structure your thoughts better than ever before.

Third - Canva''s AI designer. Create professional graphics in seconds. Just describe what you want and watch the magic happen.

Fourth - Calendly''s AI scheduling assistant. It learns your preferences and automatically optimizes your calendar for maximum productivity.

Finally - Zapier''s AI automation. Connect all your apps and let AI handle the repetitive tasks while you focus on what matters.

The future is here, and these tools are your competitive advantage. Which one will you try first? Let me know in the comments!',
 'engaging',
 58,
 'gpt-4',
 '{"temperature": 0.7, "max_tokens": 500, "style_prompts": ["energetic", "conversational", "actionable"]}',
 'approved'),

-- Script for Morning Routines project
((SELECT gen_random_uuid()),
 (SELECT id FROM demo_projects WHERE title LIKE '%Morning Routines%'),
 'What if I told you that the first hour of your day determines your entire success? I''ve studied the morning routines of 50 successful entrepreneurs, and here are the 3 patterns that showed up every single time.

Pattern #1: They all wake up at least 2 hours before they need to be anywhere. This isn''t about being a morning person - it''s about owning your morning instead of letting it own you.

Pattern #2: They start with movement. Not necessarily a full workout, but something to get their blood flowing. It could be stretching, a walk, or even just jumping jacks.

Pattern #3: They plan their top 3 priorities before checking any messages. No phone, no email, no social media until they''ve mapped out what success looks like for that day.

The magic isn''t in any single habit - it''s in creating a routine that makes you feel powerful and in control before the world starts making demands on your time.

Start with just one of these tomorrow. Which one resonates with you most?',
 'informative',
 43,
 'gpt-4',
 '{"temperature": 0.6, "max_tokens": 450, "style_prompts": ["professional", "inspiring", "research-backed"]}',
 'generated');

-- Insert voice synthesis records
WITH demo_scripts AS (
    SELECT s.id, s.project_id FROM scripts s
    JOIN video_projects vp ON s.project_id = vp.id
    WHERE vp.user_id = (SELECT id FROM users WHERE username = 'demo_creator')
)
INSERT INTO voice_synthesis (id, script_id, voice_style, audio_file_path, duration_seconds, ai_service, synthesis_params, status) VALUES
-- Voice for AI Tools script
(gen_random_uuid(),
 (SELECT id FROM demo_scripts WHERE project_id = (SELECT id FROM video_projects WHERE title LIKE '%AI Tools%')),
 'energetic',
 '/storage/audio/ai_tools_voice_001.mp3',
 58.2,
 'elevenlabs',
 '{"voice_id": "pNInz6obpgDQGcFmaJgB", "stability": 0.75, "similarity_boost": 0.85, "style": 0.3}',
 'completed'),

-- Voice for Morning Routines script
(gen_random_uuid(),
 (SELECT id FROM demo_scripts WHERE project_id = (SELECT id FROM video_projects WHERE title LIKE '%Morning Routines%')),
 'professional',
 '/storage/audio/morning_routine_voice_001.mp3',
 43.7,
 'elevenlabs',
 '{"voice_id": "21m00Tcm4TlvDq8ikWAM", "stability": 0.8, "similarity_boost": 0.75, "style": 0.2}',
 'completed');

-- Insert image generation records
WITH demo_projects AS (
    SELECT id, title FROM video_projects WHERE user_id = (SELECT id FROM users WHERE username = 'demo_creator')
)
INSERT INTO image_generation (id, project_id, prompt, style, aspect_ratio, image_file_path, ai_service, generation_params, status) VALUES
-- Images for AI Tools project
(gen_random_uuid(),
 (SELECT id FROM demo_projects WHERE title LIKE '%AI Tools%'),
 'Modern minimalist workspace with laptop, AI interface, futuristic holographic elements, clean design, professional lighting',
 'modern',
 '9:16',
 '/storage/images/ai_tools_bg_001.jpg',
 'stable-diffusion',
 '{"model": "sdxl-1.0", "steps": 50, "guidance_scale": 7.5, "seed": 12345}',
 'completed'),

(gen_random_uuid(),
 (SELECT id FROM demo_projects WHERE title LIKE '%AI Tools%'),
 'Abstract representation of AI and productivity, geometric shapes, blue and purple gradient, tech aesthetic',
 'modern',
 '9:16',
 '/storage/images/ai_tools_overlay_001.jpg',
 'stable-diffusion',
 '{"model": "sdxl-1.0", "steps": 50, "guidance_scale": 7.5, "seed": 67890}',
 'completed'),

-- Images for Morning Routines project
(gen_random_uuid(),
 (SELECT id FROM demo_projects WHERE title LIKE '%Morning Routines%'),
 'Serene morning scene, sunrise through window, coffee cup, journal, peaceful atmosphere, warm lighting',
 'modern',
 '9:16',
 '/storage/images/morning_routine_bg_001.jpg',
 'stable-diffusion',
 '{"model": "sdxl-1.0", "steps": 50, "guidance_scale": 7.5, "seed": 11111}',
 'processing');

-- Insert video generation records
WITH demo_data AS (
    SELECT 
        vp.id as project_id,
        s.id as script_id,
        vs.id as voice_id
    FROM video_projects vp
    JOIN scripts s ON vp.id = s.project_id
    JOIN voice_synthesis vs ON s.id = vs.script_id
    WHERE vp.user_id = (SELECT id FROM users WHERE username = 'demo_creator')
      AND vp.status = 'completed'
)
INSERT INTO video_generation (id, project_id, script_id, voice_id, video_file_path, thumbnail_path, 
                            duration_seconds, resolution, aspect_ratio, file_size_mb, processing_params, 
                            status, completed_at) VALUES
(gen_random_uuid(),
 (SELECT project_id FROM demo_data WHERE project_id = (SELECT id FROM video_projects WHERE title LIKE '%AI Tools%')),
 (SELECT script_id FROM demo_data WHERE project_id = (SELECT id FROM video_projects WHERE title LIKE '%AI Tools%')),
 (SELECT voice_id FROM demo_data WHERE project_id = (SELECT id FROM video_projects WHERE title LIKE '%AI Tools%')),
 '/storage/videos/ai_tools_final_001.mp4',
 '/storage/thumbnails/ai_tools_thumb_001.jpg',
 58.2,
 '1080p',
 '9:16',
 12.4,
 '{"transitions": ["fade", "slide"], "music_volume": 0.3, "caption_style": "modern", "brand_overlay": true}',
 'completed',
 NOW() - INTERVAL '2 hours');

-- Insert social platform configurations (demo setup)
WITH demo_user AS (
    SELECT id FROM users WHERE username = 'demo_creator'
)
INSERT INTO social_platforms (id, user_id, platform, platform_user_id, account_info, is_active) VALUES
(gen_random_uuid(), 
 (SELECT id FROM demo_user), 
 'tiktok', 
 'demo_creator_tiktok',
 '{"followers": 15420, "verified": false, "bio": "AI & Productivity Tips 🤖✨", "profile_pic": "https://via.placeholder.com/150"}',
 true),
(gen_random_uuid(), 
 (SELECT id FROM demo_user), 
 'youtube', 
 'demo_creator_yt',
 '{"subscribers": 8750, "verified": false, "channel_name": "ProductivityAI Hub", "category": "Education"}',
 true),
(gen_random_uuid(), 
 (SELECT id FROM demo_user), 
 'instagram', 
 'demo_creator_ig',
 '{"followers": 12300, "verified": false, "bio": "Making AI Simple for Everyone 🚀", "posts": 89}',
 false);

-- Insert sample publish schedule
WITH demo_video AS (
    SELECT vg.id as video_id, vg.project_id
    FROM video_generation vg
    JOIN video_projects vp ON vg.project_id = vp.id
    WHERE vp.title LIKE '%AI Tools%' AND vg.status = 'completed'
),
demo_platforms AS (
    SELECT id, platform FROM social_platforms WHERE user_id = (SELECT id FROM users WHERE username = 'demo_creator')
)
INSERT INTO publish_schedule (id, project_id, platform_id, scheduled_time, title, description, tags, status) VALUES
-- TikTok scheduling
(gen_random_uuid(),
 (SELECT project_id FROM demo_video),
 (SELECT id FROM demo_platforms WHERE platform = 'tiktok'),
 NOW() + INTERVAL '4 hours',
 '5 AI Tools That Will Change Your Life in 2025',
 'These AI tools are game-changers for productivity! 🤖✨ Which one will you try first? #AI #ProductivityHacks #TechTips #AITools #Automation',
 '["AI", "productivity", "tools", "2025", "automation", "tech", "business"]',
 'scheduled'),

-- YouTube scheduling
(gen_random_uuid(),
 (SELECT project_id FROM demo_video),
 (SELECT id FROM demo_platforms WHERE platform = 'youtube'),
 NOW() + INTERVAL '1 day',
 '5 Game-Changing AI Tools for 2025 | Productivity Revolution',
 'Discover the 5 most powerful AI tools that will revolutionize your productivity in 2025. From content creation to automation, these tools will give you a competitive edge in the digital age. 

🔥 Tools covered:
• ChatGPT for content creation
• Notion AI for organization  
• Canva AI for design
• Calendly AI for scheduling
• Zapier AI for automation

💡 Timestamps:
0:00 Introduction
0:10 ChatGPT Content Creation
0:20 Notion AI Organization
0:30 Canva AI Design
0:40 Calendly AI Scheduling  
0:50 Zapier AI Automation

Subscribe for more AI and productivity tips!',
 '["AI tools", "productivity", "automation", "2025", "ChatGPT", "Notion", "Canva", "business", "entrepreneur"]',
 'scheduled');