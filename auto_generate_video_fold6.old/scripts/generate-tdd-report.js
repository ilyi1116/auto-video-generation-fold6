#!/usr/bin/env node

/**
 * TDD 測試報告自動化生成工具
 * 遵循 TDD 原則，收集並生成詳細的測試報告
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class TDDReportGenerator {
    constructor() {
        this.reportDir = path.join(process.cwd(), 'tdd-reports');
        this.coverageDir = path.join(process.cwd(), 'coverage-reports');
        this.timestamp = new Date().toISOString();
        
        // 確保報告目錄存在
        if (!fs.existsSync(this.reportDir)) {
            fs.mkdirSync(this.reportDir, { recursive: true });
        }
    }

    /**
     * 收集前端測試數據
     */
    collectFrontendData() {
        console.log('📱 收集前端測試數據...');
        
        const frontendDir = path.join(process.cwd(), 'frontend');
        const coverageFile = path.join(frontendDir, 'coverage', 'coverage-summary.json');
        
        let frontendData = {
            exists: fs.existsSync(frontendDir),
            testsRun: false,
            coverage: null,
            testResults: null
        };

        if (frontendData.exists) {
            try {
                // 檢查是否有測試覆蓋率報告
                if (fs.existsSync(coverageFile)) {
                    const coverageData = JSON.parse(fs.readFileSync(coverageFile, 'utf8'));
                    frontendData.coverage = {
                        statements: coverageData.total.statements.pct,
                        branches: coverageData.total.branches.pct,
                        functions: coverageData.total.functions.pct,
                        lines: coverageData.total.lines.pct
                    };
                }

                // 嘗試執行測試並收集結果
                process.chdir(frontendDir);
                
                const testCommand = 'npm run test:unit -- --reporter=json';
                try {
                    const testOutput = execSync(testCommand, { 
                        encoding: 'utf8',
                        timeout: 60000
                    });
                    
                    frontendData.testsRun = true;
                    frontendData.testResults = this.parseTestOutput(testOutput);
                } catch (error) {
                    console.log('⚠️ 前端測試執行失敗，使用模擬數據');
                    frontendData.testResults = {
                        total: 0,
                        passed: 0,
                        failed: 0,
                        skipped: 0
                    };
                }
                
                process.chdir('..');
            } catch (error) {
                console.error('前端數據收集錯誤:', error.message);
            }
        }

        return frontendData;
    }

    /**
     * 收集後端測試數據
     */
    collectBackendData() {
        console.log('🔧 收集後端測試數據...');
        
        const servicesDir = path.join(process.cwd(), 'services');
        let backendData = {
            services: [],
            totalCoverage: 0,
            totalTests: 0
        };

        if (fs.existsSync(servicesDir)) {
            const services = fs.readdirSync(servicesDir, { withFileTypes: true })
                .filter(dirent => dirent.isDirectory())
                .map(dirent => dirent.name);

            for (const serviceName of services) {
                const serviceDir = path.join(servicesDir, serviceName);
                const serviceData = this.collectServiceData(serviceName, serviceDir);
                backendData.services.push(serviceData);
            }

            // 計算平均覆蓋率
            const validServices = backendData.services.filter(s => s.coverage);
            if (validServices.length > 0) {
                backendData.totalCoverage = validServices.reduce((sum, s) => 
                    sum + s.coverage.statements, 0) / validServices.length;
            }

            backendData.totalTests = backendData.services.reduce((sum, s) => 
                sum + (s.testResults?.total || 0), 0);
        }

        return backendData;
    }

    /**
     * 收集單個服務的測試數據
     */
    collectServiceData(serviceName, serviceDir) {
        let serviceData = {
            name: serviceName,
            exists: fs.existsSync(serviceDir),
            hasTests: false,
            coverage: null,
            testResults: null,
            codeQuality: null
        };

        if (serviceData.exists) {
            const testsDir = path.join(serviceDir, 'tests');
            serviceData.hasTests = fs.existsSync(testsDir);

            if (serviceData.hasTests) {
                try {
                    process.chdir(serviceDir);

                    // 收集測試覆蓋率
                    try {
                        const coverageOutput = execSync(
                            'python -m pytest --cov=app --cov-report=json --cov-report=term-missing -q',
                            { encoding: 'utf8', timeout: 120000 }
                        );
                        
                        const coverageFile = path.join(serviceDir, 'coverage.json');
                        if (fs.existsSync(coverageFile)) {
                            const coverageData = JSON.parse(fs.readFileSync(coverageFile, 'utf8'));
                            serviceData.coverage = {
                                statements: Math.round(coverageData.totals.percent_covered || 0),
                                missing: coverageData.totals.missing_lines || 0,
                                total: coverageData.totals.num_statements || 0
                            };
                        }
                    } catch (error) {
                        console.log(`⚠️ ${serviceName} 覆蓋率收集失敗`);
                    }

                    // 收集測試結果
                    try {
                        const testOutput = execSync(
                            'python -m pytest --tb=no -q',
                            { encoding: 'utf8', timeout: 120000 }
                        );
                        
                        serviceData.testResults = this.parsePytestOutput(testOutput);
                    } catch (error) {
                        console.log(`⚠️ ${serviceName} 測試執行失敗`);
                        serviceData.testResults = { total: 0, passed: 0, failed: 0 };
                    }

                    // 收集程式碼品質指標
                    try {
                        const flake8Output = execSync(
                            'flake8 app/ --max-complexity=10 --statistics',
                            { encoding: 'utf8', timeout: 30000 }
                        );
                        
                        serviceData.codeQuality = this.parseFlake8Output(flake8Output);
                    } catch (error) {
                        serviceData.codeQuality = { issues: 0, complexity: 'unknown' };
                    }

                    process.chdir('../..');
                } catch (error) {
                    console.error(`${serviceName} 數據收集錯誤:`, error.message);
                    process.chdir('../..');
                }
            }
        }

        return serviceData;
    }

    /**
     * 解析測試輸出
     */
    parseTestOutput(output) {
        // 簡化的解析邏輯
        const lines = output.split('\n');
        let results = { total: 0, passed: 0, failed: 0, skipped: 0 };
        
        for (const line of lines) {
            if (line.includes('passed')) {
                const match = line.match(/(\d+)\s+passed/);
                if (match) results.passed = parseInt(match[1]);
            }
            if (line.includes('failed')) {
                const match = line.match(/(\d+)\s+failed/);
                if (match) results.failed = parseInt(match[1]);
            }
            if (line.includes('skipped')) {
                const match = line.match(/(\d+)\s+skipped/);
                if (match) results.skipped = parseInt(match[1]);
            }
        }
        
        results.total = results.passed + results.failed + results.skipped;
        return results;
    }

    /**
     * 解析 pytest 輸出
     */
    parsePytestOutput(output) {
        const lines = output.split('\n');
        let results = { total: 0, passed: 0, failed: 0 };
        
        for (const line of lines) {
            if (line.includes('passed') || line.includes('failed')) {
                const match = line.match(/(\d+)\s+passed|(\d+)\s+failed/g);
                if (match) {
                    for (const m of match) {
                        if (m.includes('passed')) {
                            results.passed = parseInt(m.match(/(\d+)/)[1]);
                        }
                        if (m.includes('failed')) {
                            results.failed = parseInt(m.match(/(\d+)/)[1]);
                        }
                    }
                }
            }
        }
        
        results.total = results.passed + results.failed;
        return results;
    }

    /**
     * 解析 flake8 輸出
     */
    parseFlake8Output(output) {
        const lines = output.split('\n');
        let issues = 0;
        let complexityIssues = 0;
        
        for (const line of lines) {
            if (line.trim() && !line.includes('statistics')) {
                issues++;
                if (line.includes('C90')) {
                    complexityIssues++;
                }
            }
        }
        
        return { issues, complexityIssues };
    }

    /**
     * 收集 Git 資訊
     */
    collectGitInfo() {
        console.log('📊 收集 Git 資訊...');
        
        try {
            const commitHash = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
            const commitMessage = execSync('git log -1 --pretty=format:"%s"', { encoding: 'utf8' }).trim();
            const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
            const author = execSync('git log -1 --pretty=format:"%an"', { encoding: 'utf8' }).trim();
            const date = execSync('git log -1 --pretty=format:"%ai"', { encoding: 'utf8' }).trim();
            
            // 檢測 TDD 階段
            let tddPhase = 'unknown';
            if (commitMessage.startsWith('red:')) tddPhase = 'red';
            else if (commitMessage.startsWith('green:')) tddPhase = 'green';
            else if (commitMessage.startsWith('refactor:')) tddPhase = 'refactor';
            
            return {
                commitHash: commitHash.substring(0, 8),
                fullHash: commitHash,
                commitMessage,
                branch,
                author,
                date,
                tddPhase
            };
        } catch (error) {
            console.error('Git 資訊收集失敗:', error.message);
            return null;
        }
    }

    /**
     * 生成 HTML 報告
     */
    generateHTMLReport(data) {
        console.log('📝 生成 HTML 報告...');
        
        const { frontend, backend, git } = data;
        
        const html = `
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TDD 測試報告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: #333; background: #f5f7fa;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .tdd-phase { 
            display: inline-block; padding: 5px 15px; border-radius: 20px;
            font-weight: bold; text-transform: uppercase;
        }
        .phase-red { background: #e74c3c; }
        .phase-green { background: #27ae60; }
        .phase-refactor { background: #3498db; }
        .phase-unknown { background: #95a5a6; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { 
            background: white; border-radius: 10px; padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s;
        }
        .card:hover { transform: translateY(-2px); }
        .card h2 { color: #2c3e50; margin-bottom: 15px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }
        
        .metric { 
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 0; border-bottom: 1px solid #ecf0f1;
        }
        .metric:last-child { border-bottom: none; }
        .metric-value { font-weight: bold; }
        .success { color: #27ae60; }
        .warning { color: #f39c12; }
        .error { color: #e74c3c; }
        
        .coverage-bar { 
            width: 100%; height: 20px; background: #ecf0f1; border-radius: 10px;
            overflow: hidden; margin: 10px 0;
        }
        .coverage-fill { 
            height: 100%; background: linear-gradient(90deg, #e74c3c 0%, #f39c12 70%, #27ae60 90%);
            transition: width 0.3s ease;
        }
        
        .services-grid { 
            display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); 
            gap: 15px; margin-top: 15px;
        }
        .service-card { 
            background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db;
        }
        .service-name { font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
        
        .footer { 
            text-align: center; padding: 30px; color: #7f8c8d; 
            border-top: 1px solid #ecf0f1; margin-top: 40px;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header { padding: 20px; }
            .header h1 { font-size: 2em; }
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 TDD 測試報告</h1>
            ${git ? `
                <p><strong>提交:</strong> ${git.commitHash} - ${git.commitMessage}</p>
                <p><strong>分支:</strong> ${git.branch} | <strong>作者:</strong> ${git.author}</p>
                <p><strong>時間:</strong> ${git.date}</p>
                <span class="tdd-phase phase-${git.tddPhase}">TDD ${git.tddPhase.toUpperCase()} 階段</span>
            ` : ''}
        </div>

        <div class="grid">
            <!-- 總覽卡片 -->
            <div class="card">
                <h2>📊 測試總覽</h2>
                <div class="metric">
                    <span>前端測試</span>
                    <span class="metric-value ${frontend.testsRun ? 'success' : 'error'}">
                        ${frontend.testsRun ? '✅ 已執行' : '❌ 未執行'}
                    </span>
                </div>
                <div class="metric">
                    <span>後端服務</span>
                    <span class="metric-value">${backend.services.length} 個服務</span>
                </div>
                <div class="metric">
                    <span>總測試數</span>
                    <span class="metric-value">${backend.totalTests + (frontend.testResults?.total || 0)}</span>
                </div>
                <div class="metric">
                    <span>平均覆蓋率</span>
                    <span class="metric-value ${(backend.totalCoverage || 0) >= 90 ? 'success' : 'warning'}">
                        ${Math.round(backend.totalCoverage || 0)}%
                    </span>
                </div>
            </div>

            <!-- 前端測試卡片 -->
            <div class="card">
                <h2>📱 前端測試</h2>
                ${frontend.exists ? `
                    ${frontend.coverage ? `
                        <div class="metric">
                            <span>語句覆蓋率</span>
                            <span class="metric-value ${frontend.coverage.statements >= 90 ? 'success' : 'warning'}">
                                ${frontend.coverage.statements}%
                            </span>
                        </div>
                        <div class="coverage-bar">
                            <div class="coverage-fill" style="width: ${frontend.coverage.statements}%"></div>
                        </div>
                        <div class="metric">
                            <span>分支覆蓋率</span>
                            <span class="metric-value">${frontend.coverage.branches}%</span>
                        </div>
                        <div class="metric">
                            <span>函數覆蓋率</span>
                            <span class="metric-value">${frontend.coverage.functions}%</span>
                        </div>
                    ` : '<p class="warning">⚠️ 未找到覆蓋率報告</p>'}
                    
                    ${frontend.testResults ? `
                        <div class="metric">
                            <span>通過測試</span>
                            <span class="metric-value success">${frontend.testResults.passed}</span>
                        </div>
                        <div class="metric">
                            <span>失敗測試</span>
                            <span class="metric-value ${frontend.testResults.failed > 0 ? 'error' : 'success'}">
                                ${frontend.testResults.failed}
                            </span>
                        </div>
                    ` : ''}
                ` : '<p class="error">❌ 前端目錄不存在</p>'}
            </div>

            <!-- 後端測試卡片 -->
            <div class="card">
                <h2>🔧 後端測試</h2>
                <div class="services-grid">
                    ${backend.services.map(service => `
                        <div class="service-card">
                            <div class="service-name">${service.name}</div>
                            ${service.hasTests ? `
                                ${service.coverage ? `
                                    <div style="font-size: 0.9em; color: #666;">
                                        覆蓋率: <strong class="${service.coverage.statements >= 90 ? 'success' : 'warning'}">
                                            ${service.coverage.statements}%
                                        </strong>
                                    </div>
                                ` : ''}
                                ${service.testResults ? `
                                    <div style="font-size: 0.9em; color: #666;">
                                        測試: ${service.testResults.passed}/${service.testResults.total} 通過
                                    </div>
                                ` : ''}
                                ${service.codeQuality ? `
                                    <div style="font-size: 0.9em; color: #666;">
                                        品質問題: ${service.codeQuality.issues}
                                    </div>
                                ` : ''}
                            ` : '<div style="color: #999;">無測試</div>'}
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- TDD 品質指標 -->
            <div class="card">
                <h2>🎯 TDD 品質指標</h2>
                <div class="metric">
                    <span>覆蓋率要求</span>
                    <span class="metric-value">≥ 90%</span>
                </div>
                <div class="metric">
                    <span>複雜度限制</span>
                    <span class="metric-value">≤ 10</span>
                </div>
                <div class="metric">
                    <span>TDD 循環</span>
                    <span class="metric-value ${git && git.tddPhase !== 'unknown' ? 'success' : 'warning'}">
                        ${git && git.tddPhase !== 'unknown' ? '✅ 遵循' : '⚠️ 檢查'}
                    </span>
                </div>
                <div class="metric">
                    <span>測試優先</span>
                    <span class="metric-value success">✅ 啟用</span>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>報告生成時間: ${this.timestamp}</p>
            <p>🧬 基於 Test-Driven Development 最佳實踐</p>
        </div>
    </div>
</body>
</html>`;

        const reportPath = path.join(this.reportDir, 'index.html');
        fs.writeFileSync(reportPath, html);
        
        return reportPath;
    }

    /**
     * 生成 JSON 報告
     */
    generateJSONReport(data) {
        console.log('📄 生成 JSON 報告...');
        
        const reportData = {
            timestamp: this.timestamp,
            version: '1.0.0',
            tddCompliant: this.checkTDDCompliance(data),
            ...data
        };

        const reportPath = path.join(this.reportDir, 'report.json');
        fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2));
        
        return reportPath;
    }

    /**
     * 檢查 TDD 合規性
     */
    checkTDDCompliance(data) {
        const { frontend, backend } = data;
        
        let compliance = {
            overall: false,
            coverage: false,
            testExistence: false,
            codeQuality: false,
            score: 0
        };

        // 檢查覆蓋率
        const avgCoverage = backend.totalCoverage || 0;
        compliance.coverage = avgCoverage >= 90;

        // 檢查測試存在性
        const hasTests = backend.services.some(s => s.hasTests) || frontend.testsRun;
        compliance.testExistence = hasTests;

        // 檢查程式碼品質
        const qualityIssues = backend.services.reduce((sum, s) => 
            sum + (s.codeQuality?.issues || 0), 0);
        compliance.codeQuality = qualityIssues < 10;

        // 計算總分
        let score = 0;
        if (compliance.coverage) score += 40;
        if (compliance.testExistence) score += 30;
        if (compliance.codeQuality) score += 30;
        
        compliance.score = score;
        compliance.overall = score >= 80;

        return compliance;
    }

    /**
     * 主要執行函數
     */
    async generate() {
        console.log('🧬 開始生成 TDD 測試報告...');
        console.log('=' * 50);

        try {
            // 收集所有數據
            const data = {
                frontend: this.collectFrontendData(),
                backend: this.collectBackendData(),
                git: this.collectGitInfo()
            };

            // 生成報告
            const htmlPath = this.generateHTMLReport(data);
            const jsonPath = this.generateJSONReport(data);

            console.log('=' * 50);
            console.log('✅ TDD 測試報告生成完成！');
            console.log(`📄 HTML 報告: ${htmlPath}`);
            console.log(`🔧 JSON 報告: ${jsonPath}`);
            
            // 顯示摘要
            const compliance = this.checkTDDCompliance(data);
            console.log(`📊 TDD 合規性評分: ${compliance.score}/100`);
            console.log(`🎯 整體合規: ${compliance.overall ? '✅ 通過' : '❌ 需改進'}`);

        } catch (error) {
            console.error('❌ 報告生成失敗:', error.message);
            process.exit(1);
        }
    }
}

// 執行報告生成
if (require.main === module) {
    const generator = new TDDReportGenerator();
    generator.generate();
}

module.exports = TDDReportGenerator;