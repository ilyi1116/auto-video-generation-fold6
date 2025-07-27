#!/usr/bin/env python3
"""
安全報告生成器
整合多個安全掃描工具的結果，生成統一的安全報告
"""

import os
import json
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityReportGenerator:
    """安全報告生成器"""
    
    def __init__(self):
        self.findings = []
        self.summary = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0
        }
        self.scanner_results = {}
    
    def process_bandit_report(self, file_path: str):
        """處理 Bandit 報告"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for result in data.get('results', []):
                finding = {
                    "id": f"bandit_{result.get('test_id')}_{result.get('line_number')}",
                    "scanner": "bandit",
                    "severity": result.get('issue_severity', 'UNKNOWN').upper(),
                    "confidence": result.get('issue_confidence', 'UNKNOWN'),
                    "title": result.get('issue_text', ''),
                    "description": result.get('issue_text', ''),
                    "file_path": result.get('filename', ''),
                    "line_number": result.get('line_number', 0),
                    "rule_id": result.get('test_id', ''),
                    "remediation": result.get('more_info', ''),
                    "created_at": datetime.now().isoformat()
                }
                self.findings.append(finding)
                self._update_summary(finding['severity'])
            
            self.scanner_results['bandit'] = {
                "total_findings": len(data.get('results', [])),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to process Bandit report {file_path}: {e}")
    
    def process_semgrep_report(self, file_path: str):
        """處理 Semgrep 報告"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for result in data.get('results', []):
                severity = self._map_semgrep_severity(result.get('extra', {}).get('severity', 'INFO'))
                
                finding = {
                    "id": f"semgrep_{result.get('check_id')}_{result.get('start', {}).get('line', 0)}",
                    "scanner": "semgrep",
                    "severity": severity,
                    "confidence": "HIGH",
                    "title": result.get('extra', {}).get('message', ''),
                    "description": result.get('extra', {}).get('message', ''),
                    "file_path": result.get('path', ''),
                    "line_number": result.get('start', {}).get('line', 0),
                    "rule_id": result.get('check_id', ''),
                    "remediation": result.get('extra', {}).get('fix', ''),
                    "created_at": datetime.now().isoformat()
                }
                self.findings.append(finding)
                self._update_summary(finding['severity'])
            
            self.scanner_results['semgrep'] = {
                "total_findings": len(data.get('results', [])),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to process Semgrep report {file_path}: {e}")
    
    def process_safety_report(self, file_path: str):
        """處理 Safety 報告"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Safety 報告可能是列表格式
            vulnerabilities = data if isinstance(data, list) else data.get('vulnerabilities', [])
            
            for vuln in vulnerabilities:
                finding = {
                    "id": f"safety_{vuln.get('id')}",
                    "scanner": "safety",
                    "severity": "HIGH",  # Safety 通常報告高風險漏洞
                    "confidence": "HIGH",
                    "title": f"Vulnerable package: {vuln.get('package_name')}",
                    "description": vuln.get('advisory', ''),
                    "file_path": "requirements.txt",
                    "line_number": 0,
                    "rule_id": str(vuln.get('id', '')),
                    "remediation": f"Upgrade to version {vuln.get('vulnerable_spec', '')}",
                    "cve_id": vuln.get('cve'),
                    "created_at": datetime.now().isoformat()
                }
                self.findings.append(finding)
                self._update_summary(finding['severity'])
            
            self.scanner_results['safety'] = {
                "total_findings": len(vulnerabilities),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to process Safety report {file_path}: {e}")
    
    def process_npm_audit_report(self, file_path: str):
        """處理 npm audit 報告"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            vulnerabilities = data.get('vulnerabilities', {})
            
            for vuln_id, vuln in vulnerabilities.items():
                severity = vuln.get('severity', 'unknown').upper()
                
                finding = {
                    "id": f"npm_{vuln_id}",
                    "scanner": "npm_audit",
                    "severity": severity,
                    "confidence": "HIGH",
                    "title": f"Vulnerable npm package: {vuln.get('name')}",
                    "description": vuln.get('title', ''),
                    "file_path": "package.json",
                    "line_number": 0,
                    "rule_id": vuln_id,
                    "remediation": f"Update to version {vuln.get('fixAvailable', {}).get('version', 'latest')}",
                    "cve_id": vuln.get('cves', [None])[0] if vuln.get('cves') else None,
                    "created_at": datetime.now().isoformat()
                }
                self.findings.append(finding)
                self._update_summary(finding['severity'])
            
            self.scanner_results['npm_audit'] = {
                "total_findings": len(vulnerabilities),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to process npm audit report {file_path}: {e}")
    
    def process_trivy_report(self, file_path: str):
        """處理 Trivy 報告"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            results = data.get('Results', [])
            
            for result in results:
                # 處理漏洞
                for vuln in result.get('Vulnerabilities', []):
                    finding = {
                        "id": f"trivy_{vuln.get('VulnerabilityID')}",
                        "scanner": "trivy",
                        "severity": vuln.get('Severity', 'UNKNOWN').upper(),
                        "confidence": "HIGH",
                        "title": f"Container vulnerability: {vuln.get('Title', '')}",
                        "description": vuln.get('Description', ''),
                        "file_path": result.get('Target', ''),
                        "line_number": 0,
                        "rule_id": vuln.get('VulnerabilityID', ''),
                        "remediation": f"Update package {vuln.get('PkgName', '')} to {vuln.get('FixedVersion', 'latest')}",
                        "cve_id": vuln.get('VulnerabilityID'),
                        "cvss_score": vuln.get('CVSS', {}).get('V3Score'),
                        "created_at": datetime.now().isoformat()
                    }
                    self.findings.append(finding)
                    self._update_summary(finding['severity'])
                
                # 處理密鑰
                for secret in result.get('Secrets', []):
                    finding = {
                        "id": f"trivy_secret_{secret.get('RuleID')}_{secret.get('StartLine', 0)}",
                        "scanner": "trivy_secrets",
                        "severity": secret.get('Severity', 'UNKNOWN').upper(),
                        "confidence": "HIGH",
                        "title": f"Secret detected: {secret.get('Title', '')}",
                        "description": secret.get('Match', ''),
                        "file_path": result.get('Target', ''),
                        "line_number": secret.get('StartLine', 0),
                        "rule_id": secret.get('RuleID', ''),
                        "remediation": "Remove or encrypt the detected secret",
                        "created_at": datetime.now().isoformat()
                    }
                    self.findings.append(finding)
                    self._update_summary(finding['severity'])
                
                # 處理配置錯誤
                for misconfig in result.get('Misconfigurations', []):
                    finding = {
                        "id": f"trivy_config_{misconfig.get('ID')}_{misconfig.get('CauseMetadata', {}).get('StartLine', 0)}",
                        "scanner": "trivy_config",
                        "severity": misconfig.get('Severity', 'UNKNOWN').upper(),
                        "confidence": "HIGH",
                        "title": f"Configuration issue: {misconfig.get('Title', '')}",
                        "description": misconfig.get('Description', ''),
                        "file_path": result.get('Target', ''),
                        "line_number": misconfig.get('CauseMetadata', {}).get('StartLine', 0),
                        "rule_id": misconfig.get('ID', ''),
                        "remediation": misconfig.get('Resolution', ''),
                        "created_at": datetime.now().isoformat()
                    }
                    self.findings.append(finding)
                    self._update_summary(finding['severity'])
            
            self.scanner_results['trivy'] = {
                "total_findings": sum(len(r.get('Vulnerabilities', [])) + len(r.get('Secrets', [])) + len(r.get('Misconfigurations', [])) for r in results),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to process Trivy report {file_path}: {e}")
    
    def process_sarif_report(self, file_path: str, scanner_name: str):
        """處理 SARIF 格式報告"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            runs = data.get('runs', [])
            
            for run in runs:
                results = run.get('results', [])
                
                for result in results:
                    rule_id = result.get('ruleId', '')
                    message = result.get('message', {}).get('text', '')
                    
                    # 獲取位置資訊
                    locations = result.get('locations', [])
                    file_path = ''
                    line_number = 0
                    
                    if locations:
                        physical_location = locations[0].get('physicalLocation', {})
                        artifact_location = physical_location.get('artifactLocation', {})
                        file_path = artifact_location.get('uri', '')
                        
                        region = physical_location.get('region', {})
                        line_number = region.get('startLine', 0)
                    
                    # 獲取嚴重程度
                    level = result.get('level', 'note')
                    severity = self._map_sarif_severity(level)
                    
                    finding = {
                        "id": f"{scanner_name}_{rule_id}_{line_number}_{hash(message) % 10000}",
                        "scanner": scanner_name,
                        "severity": severity,
                        "confidence": "HIGH",
                        "title": message,
                        "description": message,
                        "file_path": file_path,
                        "line_number": line_number,
                        "rule_id": rule_id,
                        "remediation": "",
                        "created_at": datetime.now().isoformat()
                    }
                    self.findings.append(finding)
                    self._update_summary(finding['severity'])
            
            self.scanner_results[scanner_name] = {
                "total_findings": sum(len(run.get('results', [])) for run in runs),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to process SARIF report {file_path}: {e}")
    
    def process_reports_directory(self, reports_dir: str):
        """處理報告目錄中的所有報告"""
        reports_path = Path(reports_dir)
        
        if not reports_path.exists():
            logger.warning(f"Reports directory {reports_dir} does not exist")
            return
        
        # 遞迴搜尋所有報告檔案
        for file_path in reports_path.rglob('*'):
            if file_path.is_file():
                file_name = file_path.name.lower()
                
                try:
                    if 'bandit' in file_name and file_name.endswith('.json'):
                        logger.info(f"Processing Bandit report: {file_path}")
                        self.process_bandit_report(str(file_path))
                    
                    elif 'semgrep' in file_name and file_name.endswith('.json'):
                        logger.info(f"Processing Semgrep report: {file_path}")
                        self.process_semgrep_report(str(file_path))
                    
                    elif 'safety' in file_name and file_name.endswith('.json'):
                        logger.info(f"Processing Safety report: {file_path}")
                        self.process_safety_report(str(file_path))
                    
                    elif 'npm-audit' in file_name and file_name.endswith('.json'):
                        logger.info(f"Processing npm audit report: {file_path}")
                        self.process_npm_audit_report(str(file_path))
                    
                    elif 'trivy' in file_name and file_name.endswith('.json'):
                        logger.info(f"Processing Trivy report: {file_path}")
                        self.process_trivy_report(str(file_path))
                    
                    elif file_name.endswith('.sarif'):
                        scanner_name = self._extract_scanner_name_from_sarif(file_name)
                        logger.info(f"Processing SARIF report: {file_path} (scanner: {scanner_name})")
                        self.process_sarif_report(str(file_path), scanner_name)
                
                except Exception as e:
                    logger.error(f"Failed to process file {file_path}: {e}")
    
    def generate_report(self, output_format: str = 'json') -> Dict[str, Any]:
        """生成綜合安全報告"""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_scanners": len(self.scanner_results),
                "total_findings": len(self.findings)
            },
            "summary": self.summary,
            "scanner_results": self.scanner_results,
            "findings": self.findings,
            "recommendations": self._generate_recommendations(),
            "risk_assessment": self._assess_risk()
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str, format_type: str = 'json'):
        """儲存報告到檔案"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == 'json':
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        
        elif format_type == 'yaml':
            with open(output_file, 'w') as f:
                yaml.dump(report, f, default_flow_style=False)
        
        elif format_type == 'markdown':
            markdown_content = self._generate_markdown_report(report)
            with open(output_file, 'w') as f:
                f.write(markdown_content)
        
        logger.info(f"Report saved to {output_file}")
    
    def _update_summary(self, severity: str):
        """更新嚴重程度統計"""
        severity = severity.upper()
        if severity in self.summary:
            self.summary[severity] += 1
        else:
            self.summary["UNKNOWN"] += 1
    
    def _map_semgrep_severity(self, severity: str) -> str:
        """映射 Semgrep 嚴重程度"""
        mapping = {
            "ERROR": "HIGH",
            "WARNING": "MEDIUM",
            "INFO": "LOW"
        }
        return mapping.get(severity.upper(), "UNKNOWN")
    
    def _map_sarif_severity(self, level: str) -> str:
        """映射 SARIF 嚴重程度"""
        mapping = {
            "error": "HIGH",
            "warning": "MEDIUM",
            "note": "LOW",
            "info": "LOW"
        }
        return mapping.get(level.lower(), "UNKNOWN")
    
    def _extract_scanner_name_from_sarif(self, file_name: str) -> str:
        """從 SARIF 檔案名稱提取掃描器名稱"""
        if 'trivy' in file_name:
            return 'trivy'
        elif 'checkov' in file_name:
            return 'checkov'
        elif 'hadolint' in file_name:
            return 'hadolint'
        elif 'gitleaks' in file_name:
            return 'gitleaks'
        else:
            return 'unknown'
    
    def _generate_recommendations(self) -> List[str]:
        """生成安全建議"""
        recommendations = []
        
        critical_count = self.summary.get("CRITICAL", 0)
        high_count = self.summary.get("HIGH", 0)
        
        if critical_count > 0:
            recommendations.append(f"🚨 立即修復 {critical_count} 個關鍵安全問題")
        
        if high_count > 0:
            recommendations.append(f"⚠️ 優先修復 {high_count} 個高風險安全問題")
        
        # 分析不同掃描器的發現
        scanner_counts = {}
        for finding in self.findings:
            scanner = finding['scanner']
            scanner_counts[scanner] = scanner_counts.get(scanner, 0) + 1
        
        if scanner_counts.get('trivy_secrets', 0) > 0 or scanner_counts.get('gitleaks', 0) > 0:
            recommendations.append("🔑 檢查並移除程式碼中的硬編碼密鑰")
        
        if scanner_counts.get('bandit', 0) > 0:
            recommendations.append("🐍 修復 Python 程式碼中的安全漏洞")
        
        if scanner_counts.get('safety', 0) > 0:
            recommendations.append("📦 更新存在安全漏洞的 Python 依賴套件")
        
        if scanner_counts.get('npm_audit', 0) > 0:
            recommendations.append("📦 更新存在安全漏洞的 Node.js 依賴套件")
        
        if scanner_counts.get('trivy', 0) > 0:
            recommendations.append("🐳 修復容器映像中的安全漏洞")
        
        if scanner_counts.get('trivy_config', 0) > 0:
            recommendations.append("⚙️ 修復基礎設施配置中的安全問題")
        
        return recommendations
    
    def _assess_risk(self) -> Dict[str, Any]:
        """評估整體風險"""
        total_findings = len(self.findings)
        critical_count = self.summary.get("CRITICAL", 0)
        high_count = self.summary.get("HIGH", 0)
        
        # 風險等級評估
        if critical_count > 0:
            risk_level = "CRITICAL"
            risk_score = 10
        elif high_count > 5:
            risk_level = "HIGH"
            risk_score = 8
        elif high_count > 0:
            risk_level = "MEDIUM"
            risk_score = 6
        elif total_findings > 10:
            risk_level = "LOW"
            risk_score = 4
        else:
            risk_level = "MINIMAL"
            risk_score = 2
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "total_findings": total_findings,
            "critical_findings": critical_count,
            "high_findings": high_count,
            "remediation_priority": "immediate" if critical_count > 0 else "high" if high_count > 0 else "normal"
        }
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """生成 Markdown 格式報告"""
        markdown = f"""# Security Scan Report

**Generated:** {report['metadata']['generated_at']}  
**Total Scanners:** {report['metadata']['total_scanners']}  
**Total Findings:** {report['metadata']['total_findings']}

## Summary

| Severity | Count |
|----------|-------|
| Critical | {report['summary']['CRITICAL']} |
| High     | {report['summary']['HIGH']} |
| Medium   | {report['summary']['MEDIUM']} |
| Low      | {report['summary']['LOW']} |

## Risk Assessment

**Risk Level:** {report['risk_assessment']['risk_level']}  
**Risk Score:** {report['risk_assessment']['risk_score']}/10  
**Remediation Priority:** {report['risk_assessment']['remediation_priority']}

## Recommendations

"""
        
        for recommendation in report['recommendations']:
            markdown += f"- {recommendation}\n"
        
        markdown += "\n## Scanner Results\n\n"
        
        for scanner, result in report['scanner_results'].items():
            markdown += f"- **{scanner}**: {result['total_findings']} findings ({result['status']})\n"
        
        if report['summary']['CRITICAL'] > 0 or report['summary']['HIGH'] > 0:
            markdown += "\n## Critical and High Severity Findings\n\n"
            
            for finding in report['findings']:
                if finding['severity'] in ['CRITICAL', 'HIGH']:
                    markdown += f"### {finding['severity']}: {finding['title']}\n\n"
                    markdown += f"**File:** `{finding['file_path']}`  \n"
                    markdown += f"**Line:** {finding['line_number']}  \n"
                    markdown += f"**Scanner:** {finding['scanner']}  \n"
                    markdown += f"**Rule:** {finding['rule_id']}  \n"
                    markdown += f"**Description:** {finding['description']}  \n"
                    
                    if finding['remediation']:
                        markdown += f"**Remediation:** {finding['remediation']}  \n"
                    
                    markdown += "\n---\n\n"
        
        return markdown


def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive security report')
    parser.add_argument('--input-dir', required=True, help='Directory containing security scan reports')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--format', choices=['json', 'yaml', 'markdown'], default='json', help='Output format')
    
    args = parser.parse_args()
    
    generator = SecurityReportGenerator()
    generator.process_reports_directory(args.input_dir)
    
    report = generator.generate_report()
    generator.save_report(report, args.output, args.format)
    
    # 輸出摘要到 stdout
    print(f"Security scan completed:")
    print(f"  Total findings: {report['metadata']['total_findings']}")
    print(f"  Critical: {report['summary']['CRITICAL']}")
    print(f"  High: {report['summary']['HIGH']}")
    print(f"  Medium: {report['summary']['MEDIUM']}")
    print(f"  Low: {report['summary']['LOW']}")
    print(f"  Risk level: {report['risk_assessment']['risk_level']}")


if __name__ == '__main__':
    main()