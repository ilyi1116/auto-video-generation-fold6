"""
AI 文本生成服務測試
測試腳本生成和文本處理功能
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.services.text_generator import TextGenerator


@pytest.mark.unit
class TestTextGeneration:
    """文本生成服務單元測試"""

    @pytest.fixture
    async def client(self) -> AsyncClient:
        """創建測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def text_generator(self):
        """創建文本生成器實例"""
        return TextGenerator()

    @pytest.mark.asyncio
    async def test_generate_script_success(self, client: AsyncClient):
        """測試腳本生成成功"""
        request_data = {
            "topic": "科技趨勢分析",
            "platform": "youtube",
            "duration": "short",
            "tone": "professional",
            "target_audience": "技術愛好者",
            "keywords": ["人工智慧", "機器學習", "未來科技"]
        }
        
        mock_response = {
            "script": {
                "title": "2024年人工智慧發展趨勢",
                "content": "歡迎來到今天的科技趨勢分析。在這個快速發展的數位時代...",
                "scenes": [
                    {
                        "id": 1,
                        "text": "歡迎來到今天的科技趨勢分析",
                        "duration": 3,
                        "type": "intro"
                    },
                    {
                        "id": 2,
                        "text": "在這個快速發展的數位時代，人工智慧正在改變我們的世界",
                        "duration": 8,
                        "type": "content"
                    },
                    {
                        "id": 3,
                        "text": "感謝收看，我們下次見",
                        "duration": 2,
                        "type": "outro"
                    }
                ],
                "metadata": {
                    "duration": 13,
                    "word_count": 156,
                    "reading_time": "13秒",
                    "difficulty": "intermediate",
                    "engagement_score": 8.5
                }
            }
        }
        
        with patch("app.services.text_generator.TextGenerator.generate_script") as mock_generate:
            mock_generate.return_value = mock_response["script"]

            response = await client.post("/ai/text/generate-script", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["script"]["title"] == mock_response["script"]["title"]
            assert len(data["script"]["scenes"]) == 3
            assert data["script"]["metadata"]["duration"] == 13

    @pytest.mark.asyncio
    async def test_generate_script_with_invalid_platform(self, client: AsyncClient):
        """測試腳本生成 - 無效平台"""
        request_data = {
            "topic": "測試主題",
            "platform": "invalid_platform",
            "duration": "short",
            "tone": "professional"
        }

        response = await client.post("/ai/text/generate-script", json=request_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_improve_script_success(self, client: AsyncClient):
        """測試腳本改進成功"""
        request_data = {
            "original_script": "這是原始腳本內容",
            "improvement_type": "engagement",
            "target_metrics": {
                "engagement_score": 9.0,
                "readability": "easy"
            }
        }
        
        mock_response = {
            "improved_script": {
                "title": "改進後的腳本標題",
                "content": "這是改進後的腳本內容，更具吸引力和互動性",
                "improvements": [
                    "增加了引人入勝的開場白",
                    "添加了互動元素",
                    "優化了語言表達"
                ],
                "metrics": {
                    "engagement_score": 9.2,
                    "readability": "easy",
                    "improvement_percentage": 15.3
                }
            }
        }
        
        with patch("app.services.text_generator.TextGenerator.improve_script") as mock_improve:
            mock_improve.return_value = mock_response["improved_script"]

            response = await client.post("/ai/text/improve-script", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["improved_script"]["metrics"]["engagement_score"] == 9.2
            assert len(data["improved_script"]["improvements"]) == 3

    @pytest.mark.asyncio
    async def test_analyze_text_sentiment(self, client: AsyncClient):
        """測試文本情感分析"""
        request_data = {
            "text": "這是一個非常好的產品，我很滿意這次的購買體驗！",
            "language": "zh-TW"
        }
        
        mock_response = {
            "sentiment": {
                "label": "positive",
                "score": 0.92,
                "confidence": 0.87,
                "emotions": {
                    "joy": 0.8,
                    "satisfaction": 0.9,
                    "excitement": 0.6
                }
            }
        }
        
        with patch("app.services.text_generator.TextGenerator.analyze_sentiment") as mock_analyze:
            mock_analyze.return_value = mock_response["sentiment"]

            response = await client.post("/ai/text/analyze-sentiment", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["sentiment"]["label"] == "positive"
            assert data["sentiment"]["score"] == 0.92

    @pytest.mark.asyncio
    async def test_generate_keywords_success(self, client: AsyncClient):
        """測試關鍵字生成成功"""
        request_data = {
            "content": "人工智慧和機器學習正在改變我們的世界",
            "count": 5,
            "language": "zh-TW"
        }
        
        mock_response = {
            "keywords": [
                {"keyword": "人工智慧", "relevance": 0.95, "frequency": 3},
                {"keyword": "機器學習", "relevance": 0.90, "frequency": 2},
                {"keyword": "科技創新", "relevance": 0.85, "frequency": 1},
                {"keyword": "數位轉型", "relevance": 0.80, "frequency": 1},
                {"keyword": "未來發展", "relevance": 0.75, "frequency": 1}
            ]
        }
        
        with patch("app.services.text_generator.TextGenerator.extract_keywords") as mock_extract:
            mock_extract.return_value = mock_response["keywords"]

            response = await client.post("/ai/text/generate-keywords", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["keywords"]) == 5
            assert data["keywords"][0]["keyword"] == "人工智慧"

    @pytest.mark.asyncio
    async def test_summarize_text_success(self, client: AsyncClient):
        """測試文本摘要成功"""
        request_data = {
            "text": "這是一段很長的文本內容..." * 100,  # 模擬長文本
            "max_length": 100,
            "style": "bullet_points"
        }
        
        mock_response = {
            "summary": {
                "content": "• 主要重點一\n• 主要重點二\n• 主要重點三",
                "original_length": 2500,
                "summary_length": 45,
                "compression_ratio": 0.018,
                "key_topics": ["主題一", "主題二", "主題三"]
            }
        }
        
        with patch("app.services.text_generator.TextGenerator.summarize_text") as mock_summarize:
            mock_summarize.return_value = mock_response["summary"]

            response = await client.post("/ai/text/summarize", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["summary"]["compression_ratio"] == 0.018
            assert len(data["summary"]["key_topics"]) == 3

    def test_text_generator_initialization(self, text_generator):
        """測試文本生成器初始化"""
        assert text_generator is not None
        assert hasattr(text_generator, 'generate_script')
        assert hasattr(text_generator, 'improve_script')
        assert hasattr(text_generator, 'analyze_sentiment')

    @pytest.mark.asyncio
    async def test_text_generator_error_handling(self, text_generator):
        """測試文本生成器錯誤處理"""
        with patch("app.services.text_generator.TextGenerator._call_ai_model") as mock_call:
            mock_call.side_effect = Exception("AI service unavailable")
            
            with pytest.raises(Exception) as exc_info:
                await text_generator.generate_script({
                    "topic": "測試主題",
                    "platform": "youtube"
                })
            
            assert "AI service unavailable" in str(exc_info.value)


@pytest.mark.integration
class TestTextGenerationIntegration:
    """文本生成服務整合測試"""

    @pytest.fixture
    async def client(self) -> AsyncClient:
        """創建測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_script_generation_pipeline(self, client: AsyncClient):
        """測試完整的腳本生成流程"""
        # 第一步：生成初始腳本
        initial_request = {
            "topic": "環保科技",
            "platform": "youtube",
            "duration": "medium",
            "tone": "educational"
        }
        
        with patch("app.services.text_generator.TextGenerator.generate_script") as mock_generate:
            mock_generate.return_value = {
                "title": "環保科技的未來",
                "content": "初始腳本內容",
                "scenes": [
                    {"id": 1, "text": "開場", "duration": 3, "type": "intro"}
                ]
            }
            
            initial_response = await client.post("/ai/text/generate-script", 
                                               json=initial_request)
            assert initial_response.status_code == status.HTTP_200_OK
            initial_script = initial_response.json()["script"]

        # 第二步：改進腳本
        improve_request = {
            "original_script": initial_script["content"],
            "improvement_type": "engagement"
        }
        
        with patch("app.services.text_generator.TextGenerator.improve_script") as mock_improve:
            mock_improve.return_value = {
                "title": "環保科技的未來 - 改進版",
                "content": "改進後的腳本內容",
                "improvements": ["增加互動性"]
            }
            
            improve_response = await client.post("/ai/text/improve-script", 
                                               json=improve_request)
            assert improve_response.status_code == status.HTTP_200_OK

        # 第三步：生成關鍵字
        keyword_request = {
            "content": initial_script["content"],
            "count": 5
        }
        
        with patch("app.services.text_generator.TextGenerator.extract_keywords") as mock_keywords:
            mock_keywords.return_value = [
                {"keyword": "環保", "relevance": 0.9}
            ]
            
            keyword_response = await client.post("/ai/text/generate-keywords", 
                                                json=keyword_request)
            assert keyword_response.status_code == status.HTTP_200_OK

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_text_generation(self, client: AsyncClient):
        """測試並發文本生成請求"""
        import asyncio
        
        requests = [
            {
                "topic": f"主題 {i}",
                "platform": "youtube",
                "duration": "short",
                "tone": "casual"
            }
            for i in range(5)
        ]
        
        with patch("app.services.text_generator.TextGenerator.generate_script") as mock_generate:
            mock_generate.return_value = {
                "title": "測試腳本",
                "content": "測試內容",
                "scenes": []
            }
            
            # 並發執行多個請求
            tasks = [
                client.post("/ai/text/generate-script", json=req)
                for req in requests
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # 驗證所有請求都成功
            for response in responses:
                assert response.status_code == status.HTTP_200_OK