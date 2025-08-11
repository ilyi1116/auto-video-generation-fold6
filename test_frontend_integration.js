#!/usr/bin/env node

/**
 * 前端整合測試腳本
 * 測試前端與後端API的整合
 */

const http = require('http');

// 測試配置
const config = {
    apiGateway: 'http://localhost:8000',
    aiService: 'http://localhost:8005', 
    frontend: 'http://localhost:5173'
};

// HTTP請求工具函數
function makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const requestOptions = {
            hostname: urlObj.hostname,
            port: urlObj.port,
            path: urlObj.pathname + urlObj.search,
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        const req = http.request(requestOptions, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const parsed = res.headers['content-type']?.includes('application/json') 
                        ? JSON.parse(data) 
                        : data;
                    resolve({ status: res.statusCode, data: parsed, headers: res.headers });
                } catch (e) {
                    resolve({ status: res.statusCode, data, headers: res.headers });
                }
            });
        });

        req.on('error', reject);

        if (options.body) {
            req.write(JSON.stringify(options.body));
        }

        req.end();
    });
}

// 測試函數集
const tests = {
    // 測試服務健康狀況
    async testHealthChecks() {
        console.log('🏥 Testing Service Health...');
        
        try {
            const apiHealth = await makeRequest(`${config.apiGateway}/health`);
            console.log(`  API Gateway: ${apiHealth.status === 200 ? '✅' : '❌'} (${apiHealth.status})`);
            
            const aiHealth = await makeRequest(`${config.aiService}/health`);
            console.log(`  AI Service: ${aiHealth.status === 200 ? '✅' : '❌'} (${aiHealth.status})`);
            
            const frontendHealth = await makeRequest(config.frontend);
            console.log(`  Frontend: ${frontendHealth.status === 200 ? '✅' : '❌'} (${frontendHealth.status})`);
            
            return true;
        } catch (error) {
            console.log(`  ❌ Health check failed: ${error.message}`);
            return false;
        }
    },

    // 測試用戶認證流程
    async testAuthentication() {
        console.log('🔐 Testing Authentication Flow...');
        
        try {
            // 1. 註冊新用戶
            const registerData = {
                email: `test-${Date.now()}@example.com`,
                password: 'testpass123',
                first_name: 'Frontend',
                last_name: 'Test'
            };

            const registerRes = await makeRequest(`${config.apiGateway}/api/v1/auth/register`, {
                method: 'POST',
                body: registerData
            });

            if (registerRes.status !== 200) {
                console.log(`  ❌ Registration failed: ${registerRes.status}`);
                return false;
            }

            console.log(`  ✅ Registration successful`);
            const token = registerRes.data.data.access_token;

            // 2. 驗證令牌
            const verifyRes = await makeRequest(`${config.apiGateway}/api/v1/auth/verify`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (verifyRes.status !== 200) {
                console.log(`  ❌ Token verification failed: ${verifyRes.status}`);
                return false;
            }

            console.log(`  ✅ Token verification successful`);
            return { token, userId: registerRes.data.data.user.id };

        } catch (error) {
            console.log(`  ❌ Authentication test failed: ${error.message}`);
            return false;
        }
    },

    // 測試AI服務整合
    async testAIIntegration() {
        console.log('🤖 Testing AI Service Integration...');
        
        try {
            // 測試腳本生成
            const scriptReq = {
                topic: '前端測試AI腳本生成',
                platform: 'youtube',
                style: 'educational',
                duration: 30
            };

            const scriptRes = await makeRequest(`${config.aiService}/api/v1/generate/script`, {
                method: 'POST',
                body: scriptReq
            });

            if (scriptRes.status !== 200) {
                console.log(`  ❌ Script generation failed: ${scriptRes.status}`);
                return false;
            }

            console.log(`  ✅ Script generation successful`);
            console.log(`    Script length: ${scriptRes.data.data.script.length} chars`);

            // 測試圖片生成
            const imageReq = {
                prompt: '美麗的風景',
                style: 'realistic',
                resolution: '1080x1920',
                quantity: 2
            };

            const imageRes = await makeRequest(`${config.aiService}/api/v1/generate/image`, {
                method: 'POST',
                body: imageReq
            });

            if (imageRes.status !== 200) {
                console.log(`  ❌ Image generation failed: ${imageRes.status}`);
                return false;
            }

            console.log(`  ✅ Image generation successful`);
            console.log(`    Generated ${imageRes.data.data.images.length} images`);

            return {
                script: scriptRes.data.data.script,
                images: imageRes.data.data.images
            };

        } catch (error) {
            console.log(`  ❌ AI integration test failed: ${error.message}`);
            return false;
        }
    },

    // 測試影片創建流程
    async testVideoCreation(authData, aiData) {
        console.log('🎬 Testing Video Creation Flow...');
        
        if (!authData || !aiData) {
            console.log(`  ⏭️  Skipping video creation (missing dependencies)`);
            return false;
        }

        try {
            const videoReq = {
                title: '前端整合測試影片',
                description: '這是前端整合測試創建的影片',
                topic: 'AI測試',
                style: 'modern',
                duration: 15,
                platform: 'tiktok'
            };

            const videoRes = await makeRequest(`${config.apiGateway}/api/v1/videos`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${authData.token}` },
                body: videoReq
            });

            if (videoRes.status !== 200) {
                console.log(`  ❌ Video creation failed: ${videoRes.status}`);
                return false;
            }

            console.log(`  ✅ Video creation successful`);
            const videoId = videoRes.data.data.id;

            // 等待影片處理完成
            console.log(`  ⏳ Waiting for video processing...`);
            await new Promise(resolve => setTimeout(resolve, 3000));

            // 檢查影片狀態
            const statusRes = await makeRequest(`${config.apiGateway}/api/v1/videos`, {
                headers: { Authorization: `Bearer ${authData.token}` }
            });

            if (statusRes.status !== 200) {
                console.log(`  ❌ Video status check failed: ${statusRes.status}`);
                return false;
            }

            const video = statusRes.data.data.videos.find(v => v.id === videoId);
            console.log(`  ✅ Video status: ${video ? video.status : 'not found'}`);
            
            return video;

        } catch (error) {
            console.log(`  ❌ Video creation test failed: ${error.message}`);
            return false;
        }
    },

    // 測試分析功能
    async testAnalytics(authData) {
        console.log('📊 Testing Analytics Dashboard...');
        
        if (!authData) {
            console.log(`  ⏭️  Skipping analytics test (no auth)`);
            return false;
        }

        try {
            const analyticsRes = await makeRequest(`${config.apiGateway}/api/v1/analytics/dashboard`, {
                headers: { Authorization: `Bearer ${authData.token}` }
            });

            if (analyticsRes.status !== 200) {
                console.log(`  ❌ Analytics request failed: ${analyticsRes.status}`);
                return false;
            }

            const data = analyticsRes.data.data;
            console.log(`  ✅ Analytics data retrieved`);
            console.log(`    Total videos: ${data.totalVideos}`);
            console.log(`    Completed: ${data.completedVideos}`);
            console.log(`    Total views: ${data.totalViews}`);
            console.log(`    Total likes: ${data.totalLikes}`);

            return data;

        } catch (error) {
            console.log(`  ❌ Analytics test failed: ${error.message}`);
            return false;
        }
    }
};

// 主測試函數
async function runIntegrationTests() {
    console.log('🧪 Starting Frontend Integration Tests...\n');
    
    const results = {
        health: false,
        auth: false,
        ai: false,
        video: false,
        analytics: false
    };

    // 1. 健康檢查
    results.health = await tests.testHealthChecks();
    console.log('');

    // 2. 認證測試
    const authData = await tests.testAuthentication();
    results.auth = !!authData;
    console.log('');

    // 3. AI服務測試
    const aiData = await tests.testAIIntegration();
    results.ai = !!aiData;
    console.log('');

    // 4. 影片創建測試
    const videoData = await tests.testVideoCreation(authData, aiData);
    results.video = !!videoData;
    console.log('');

    // 5. 分析功能測試
    const analyticsData = await tests.testAnalytics(authData);
    results.analytics = !!analyticsData;
    console.log('');

    // 測試結果總結
    console.log('📈 Integration Test Results:');
    console.log('================================');
    console.log(`  🏥 Service Health: ${results.health ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`  🔐 Authentication: ${results.auth ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`  🤖 AI Services: ${results.ai ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`  🎬 Video Creation: ${results.video ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`  📊 Analytics: ${results.analytics ? '✅ PASS' : '❌ FAIL'}`);
    console.log('================================');

    const passedTests = Object.values(results).filter(Boolean).length;
    const totalTests = Object.keys(results).length;
    
    console.log(`\n🎯 Overall Result: ${passedTests}/${totalTests} tests passed`);
    
    if (passedTests === totalTests) {
        console.log('🎉 All integration tests PASSED! 🎉');
        console.log('\n📱 Ready for frontend testing at:', config.frontend);
    } else {
        console.log(`⚠️  ${totalTests - passedTests} tests failed. Please check the issues above.`);
    }

    console.log('\n🚀 Next Steps:');
    console.log('  1. Open browser and visit:', config.frontend);
    console.log('  2. Test user registration and login');
    console.log('  3. Try creating videos with AI-generated content');
    console.log('  4. Configure real API keys for enhanced AI features');
}

// 執行測試
if (require.main === module) {
    runIntegrationTests().catch(console.error);
}

module.exports = { tests, makeRequest, config };