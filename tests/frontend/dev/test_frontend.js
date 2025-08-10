import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('🚀 正在測試前端服務器啟動...');

const frontendPath = join(__dirname, 'src', 'frontend');
const child = spawn('npm', ['run', 'dev'], {
  cwd: frontendPath,
  stdio: 'pipe'
});

let serverStarted = false;
let output = '';

child.stdout.on('data', (data) => {
  const text = data.toString();
  output += text;
  console.log('STDOUT:', text);
  
  if (text.includes('Local:') && text.includes('http://')) {
    serverStarted = true;
    console.log('✅ 前端服務器成功啟動！');
    console.log('🌐 服務器地址:', text.match(/http:\/\/[^\s]+/)?.[0] || 'http://localhost:5173');
    
    // 等待一秒後關閉
    setTimeout(() => {
      child.kill('SIGTERM');
      process.exit(0);
    }, 1000);
  }
});

child.stderr.on('data', (data) => {
  const text = data.toString();
  console.log('STDERR:', text);
  
  if (text.includes('ENOENT') || text.includes('Error:')) {
    console.log('❌ 前端服務器啟動失敗');
    console.log('錯誤信息:', text);
    child.kill('SIGTERM');
    process.exit(1);
  }
});

child.on('close', (code) => {
  if (!serverStarted) {
    console.log(`❌ 前端服務器進程結束，退出碼: ${code}`);
    console.log('完整輸出:', output);
    process.exit(1);
  } else {
    console.log('✅ 測試完成，前端服務器可以正常啟動');
    process.exit(0);
  }
});

// 10秒超時
setTimeout(() => {
  if (!serverStarted) {
    console.log('⏰ 測試超時，前端服務器可能啟動較慢');
    child.kill('SIGTERM');
    process.exit(1);
  }
}, 10000);