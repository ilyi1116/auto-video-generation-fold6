#!/usr/bin/env python3
"""
假資料管理模組
Mock Data Management Module
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class MockDataManager:
    """假資料管理器"""
    
    def __init__(self, fixtures_dir: Optional[Path] = None):
        self.fixtures_dir = fixtures_dir or Path(__file__).parent
        self._cache = {}
    
    def load_fixture(self, fixture_name: str) -> Dict[str, Any]:
        """載入假資料檔案"""
        if fixture_name in self._cache:
            return self._cache[fixture_name]
        
        fixture_path = self.fixtures_dir / f"{fixture_name}.json"
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture file {fixture_path} not found")
        
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._cache[fixture_name] = data
        return data
    
    def get_test_users(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """獲取測試用戶資料"""
        users_data = self.load_fixture('users')
        users = users_data['test_users']
        
        if count:
            return random.sample(users, min(count, len(users)))
        return users
    
    def get_video_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """獲取影片模板"""
        videos_data = self.load_fixture('videos')
        templates = videos_data['video_templates']
        
        if category:
            return [t for t in templates if t.get('category') == category]
        return templates
    
    def get_sample_videos(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """獲取範例影片"""
        videos_data = self.load_fixture('videos')
        videos = videos_data['sample_videos']
        
        if status:
            return [v for v in videos if v.get('status') == status]
        return videos
    
    def get_script_template(self, style: str) -> Dict[str, Any]:
        """獲取腳本模板"""
        ai_data = self.load_fixture('ai_responses')
        return ai_data['script_templates'].get(style, {})
    
    def get_voice_options(self, gender: Optional[str] = None) -> List[Dict[str, Any]]:
        """獲取語音選項"""
        ai_data = self.load_fixture('ai_responses')
        voice_data = ai_data['voice_options']
        
        if gender == 'male':
            return voice_data['male_voices']
        elif gender == 'female':
            return voice_data['female_voices']
        else:
            return voice_data['male_voices'] + voice_data['female_voices']
    
    def get_image_prompts(self, category: str) -> List[str]:
        """獲取圖像生成提示詞"""
        ai_data = self.load_fixture('ai_responses')
        return ai_data['image_prompts'].get(category, [])
    
    def generate_mock_script(self, topic: str, style: str = 'educational', 
                           host_name: str = '主持人', channel_name: str = '頻道') -> str:
        """生成模擬腳本"""
        template_data = self.get_script_template(style)
        if not template_data:
            return f"關於{topic}的內容腳本"
        
        # 隨機選擇模板
        intro = random.choice(template_data.get('intro_templates', ['']))
        main_content = random.choice(template_data.get('main_content_templates', ['']))
        conclusion = random.choice(template_data.get('conclusion_templates', ['']))
        
        # 變數替換
        variables = {
            'topic': topic,
            'host_name': host_name,
            'channel_name': channel_name,
            'skill': topic,  # 教學類型用
            'materials': '相關工具和材料',  # 教學類型用
            'step1': '第一個步驟',  # 教學類型用
        }
        
        script_parts = []
        for part in [intro, main_content, conclusion]:
            for var, value in variables.items():
                part = part.replace(f'{{{{{var}}}}}', value)
            if part.strip():
                script_parts.append(part.strip())
        
        return '\n\n'.join(script_parts)
    
    def generate_mock_response(self, response_type: str, **kwargs) -> Dict[str, Any]:
        """生成模擬API回應"""
        ai_data = self.load_fixture('ai_responses')
        sample_responses = ai_data['sample_responses']
        
        if response_type not in sample_responses:
            return {"success": False, "error": f"Unknown response type: {response_type}"}
        
        # 複製基礎回應
        response = sample_responses[response_type]['success_response'].copy()
        
        # 根據回應類型進行客製化
        if response_type == 'script_generation':
            topic = kwargs.get('topic', 'AI技術')
            style = kwargs.get('style', 'educational')
            script = self.generate_mock_script(topic, style)
            response['data']['script'] = script
            response['data']['word_count'] = len(script.split())
            response['data']['estimated_duration'] = f"{len(script.split()) * 0.5:.0f}-{len(script.split()) * 0.7:.0f}秒"
        
        elif response_type == 'image_generation':
            # 生成隨機圖像URL
            response['data']['images'] = [
                {
                    "url": f"https://picsum.photos/1280/720?random={random.randint(1, 1000)}",
                    "prompt": kwargs.get('prompt', 'Generated image'),
                    "style": kwargs.get('style', 'realistic'),
                    "resolution": "1280x720"
                }
                for _ in range(kwargs.get('count', 1))
            ]
        
        elif response_type == 'voice_synthesis':
            text_length = len(kwargs.get('text', '測試文字'))
            duration = text_length * 0.4  # 假設每個字0.4秒
            response['data'].update({
                'duration': duration,
                'text_length': text_length,
                'file_size': f"{duration * 0.02:.1f}MB"  # 假設每秒0.02MB
            })
        
        # 更新時間戳
        response['data']['generated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        return response
    
    def save_custom_data(self, fixture_name: str, data: Dict[str, Any]):
        """儲存自定義資料"""
        fixture_path = self.fixtures_dir / f"{fixture_name}.json"
        with open(fixture_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 清除快取
        if fixture_name in self._cache:
            del self._cache[fixture_name]
    
    def clear_cache(self):
        """清除快取"""
        self._cache.clear()

# 全域實例
mock_data_manager = MockDataManager()

# 便利函數
def get_test_users(count: Optional[int] = None) -> List[Dict[str, Any]]:
    """獲取測試用戶"""
    return mock_data_manager.get_test_users(count)

def get_video_templates(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """獲取影片模板"""
    return mock_data_manager.get_video_templates(category)

def generate_mock_script(topic: str, style: str = 'educational') -> str:
    """生成模擬腳本"""
    return mock_data_manager.generate_mock_script(topic, style)

def generate_mock_response(response_type: str, **kwargs) -> Dict[str, Any]:
    """生成模擬回應"""
    return mock_data_manager.generate_mock_response(response_type, **kwargs)