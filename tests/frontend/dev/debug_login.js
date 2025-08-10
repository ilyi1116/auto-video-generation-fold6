// 在瀏覽器控制台運行此腳本來測試登入
console.log('🔍 開始診斷登入問題...');

// 測試 1: 檢查當前頁面環境
console.log('當前 URL:', window.location.href);
console.log('User Agent:', navigator.userAgent);

// 測試 2: 直接測試 API 連接
async function testLogin() {
    console.log('📡 測試登入 API...');
    
    try {
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: 'demo@example.com',
                password: 'demo123'
            })
        });
        
        console.log('✅ 請求成功!');
        console.log('響應狀態:', response.status);
        console.log('響應頭:', [...response.headers.entries()]);
        
        const result = await response.json();
        console.log('響應內容:', result);
        
        return result;
    } catch (error) {
        console.error('❌ 請求失敗:', error);
        console.error('錯誤類型:', error.constructor.name);
        console.error('錯誤訊息:', error.message);
        console.error('完整錯誤:', error);
        
        return { error: error.message };
    }
}

// 測試 3: 檢查網路狀態
console.log('🌐 網路狀態:', navigator.onLine ? '線上' : '離線');

// 測試 4: 檢查 localStorage
console.log('💾 當前 localStorage auth_token:', localStorage.getItem('auth_token'));

// 執行測試
testLogin().then(result => {
    if (result.success) {
        console.log('🎉 登入測試成功!');
        console.log('Token:', result.data.token);
    } else {
        console.log('💔 登入測試失敗');
    }
});

// 提供清理函數
window.clearAuthStorage = () => {
    localStorage.removeItem('auth_token');
    console.log('✨ Auth storage 已清除');
};

console.log('💡 提示: 運行 clearAuthStorage() 可清除認證存儲');