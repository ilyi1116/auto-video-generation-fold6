async function globalSetup() {
  console.log("🚀 開始 E2E 測試環境設定...");

  // 等待後端服務啟動
  const maxRetries = 30;
  let retries = 0;

  while (retries < maxRetries) {
    try {
      const response = await fetch("http://localhost:8000/health");
      if (response.ok) {
        console.log("✅ 後端服務已就緒");
        break;
      }
    } catch (error) {
      console.log(`⏳ 等待後端服務啟動... (${retries + 1}/${maxRetries})`);
      await new Promise((resolve) => setTimeout(resolve, 2000));
      retries++;
    }
  }

  if (retries === maxRetries) {
    throw new Error("❌ 後端服務啟動失敗，無法進行測試");
  }

  // 設置測試資料庫
  try {
    await fetch("http://localhost:8000/api/test/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resetDatabase: true,
        seedTestData: true,
      }),
    });
    console.log("✅ 測試資料庫設定完成");
  } catch (error) {
    console.error("❌ 測試資料庫設定失敗:", error);
  }

  console.log("🎯 E2E 測試環境設定完成！");
}

module.exports = globalSetup;
