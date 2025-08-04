async function globalTeardown() {
  console.log('🧹 開始清理 E2E 測試環境...');
  
  try {
    // 清理測試資料
    await fetch('http://localhost:8000/api/test/cleanup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cleanupTestData: true,
        resetToInitialState: true
      })
    });
    console.log('✅ 測試資料清理完成');
  } catch (error) {
    console.error('⚠️ 測試資料清理失敗:', error);
  }
  
  console.log('✨ E2E 測試環境清理完成！');
}

module.exports = globalTeardown;