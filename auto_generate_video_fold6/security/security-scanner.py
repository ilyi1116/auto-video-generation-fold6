"""
綜合安全掃描器
整合多種安全掃描工具，提供統一的安全評估
"""

import os
import json
import asyncio
import subprocess
import tempfile
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import requests
from concurrent.futures import ThreadPoolExecutor
import docker


@dataclass
class SecurityFinding:
    """安全發現"""

    id: str
    severity: str
    title: str
    description: str
    file_path: str
    line_number: int
    scanner: str
    rule_id: str
    confidence: str
    remediation: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    created_at: Optional[str] = None


@dataclass
class ScanResult:
    """掃描結果"""

    scanner: str
    target: str
    scan_type: str
    start_time: datetime
    end_time: datetime
    status: str
    findings: List[SecurityFinding]
    metadata: Dict[str, Any]
    summary: Dict[str, int]


class SecurityScanner:
    """安全掃描器主類"""

    def __init__(
        self,
        config_dir: str = "./security",
        reports_dir: str = "./reports/security",
        docker_client: docker.DockerClient = None,
    ):
        self.config_dir = Path(config_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.docker_client = docker_client or docker.from_env()
        self.logger = logging.getLogger(__name__)

        # 掃描器配置
        self.scanners = {
            "trivy": {
                "image": "aquasec/trivy:latest",
                "config": self.config_dir / "trivy-config.yaml",
            },
            "bandit": {
                "image": "securityanalysis/bandit:latest",
                "config": self.config_dir / "bandit-config.yaml",
            },
            "safety": {"image": "pyupio/safety:latest", "config": None},
            "semgrep": {"image": "returntocorp/semgrep:latest", "config": None},
            "gitleaks": {"image": "zricethezav/gitleaks:latest", "config": None},
        }

        # 掃描歷史
        self.scan_history = []

    async def run_comprehensive_scan(
        self, target_path: str, scan_types: List[str] = None, docker_images: List[str] = None
    ) -> Dict[str, ScanResult]:
        """執行綜合安全掃描"""
        if scan_types is None:
            scan_types = ["code", "dependencies", "secrets", "containers"]

        results = {}

        self.logger.info(f"Starting comprehensive security scan for {target_path}")

        # 並行執行不同類型的掃描
        tasks = []

        if "code" in scan_types:
            tasks.append(self._scan_code_vulnerabilities(target_path))

        if "dependencies" in scan_types:
            tasks.append(self._scan_dependencies(target_path))

        if "secrets" in scan_types:
            tasks.append(self._scan_secrets(target_path))

        if "containers" in scan_types and docker_images:
            for image in docker_images:
                tasks.append(self._scan_container_image(image))

        if "infrastructure" in scan_types:
            tasks.append(self._scan_infrastructure(target_path))

        # 等待所有掃描完成
        scan_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 處理結果
        for i, result in enumerate(scan_results):
            if isinstance(result, Exception):
                self.logger.error(f"Scan task {i} failed: {result}")
            elif isinstance(result, ScanResult):
                results[result.scanner] = result
            elif isinstance(result, list):
                for scan_result in result:
                    if isinstance(scan_result, ScanResult):
                        results[scan_result.scanner] = scan_result

        # 生成綜合報告
        comprehensive_report = await self._generate_comprehensive_report(results)

        # 發送告警
        await self._send_security_alerts(results)

        return results

    async def _scan_code_vulnerabilities(self, target_path: str) -> ScanResult:
        """掃描程式碼漏洞"""
        start_time = datetime.now()
        findings = []

        try:
            # Bandit 掃描 Python 程式碼
            bandit_result = await self._run_bandit_scan(target_path)
            findings.extend(bandit_result)

            # Semgrep 掃描多語言程式碼
            semgrep_result = await self._run_semgrep_scan(target_path)
            findings.extend(semgrep_result)

            status = "completed"

        except Exception as e:
            self.logger.error(f"Code vulnerability scan failed: {e}")
            status = "failed"

        end_time = datetime.now()

        return ScanResult(
            scanner="code_vulnerabilities",
            target=target_path,
            scan_type="code",
            start_time=start_time,
            end_time=end_time,
            status=status,
            findings=findings,
            metadata={"scan_duration": (end_time - start_time).total_seconds()},
            summary=self._summarize_findings(findings),
        )

    async def _run_bandit_scan(self, target_path: str) -> List[SecurityFinding]:
        """執行 Bandit 掃描"""
        findings = []

        try:
            # 準備 Bandit 命令
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{os.path.abspath(target_path)}:/code",
                "-v",
                f"{self.config_dir}:/config",
                "securityanalysis/bandit",
                "-r",
                "/code",
                "-f",
                "json",
                "-c",
                "/config/bandit-config.yaml",
            ]

            # 執行掃描
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode in [0, 1]:  # 0=無問題, 1=發現問題
                if result.stdout:
                    bandit_data = json.loads(result.stdout)

                    for result_item in bandit_data.get("results", []):
                        finding = SecurityFinding(
                            id=f"bandit_{result_item.get('test_id')}_{int(time.time())}",
                            severity=result_item.get("issue_severity", "UNKNOWN").upper(),
                            title=result_item.get("issue_text", ""),
                            description=result_item.get("issue_text", ""),
                            file_path=result_item.get("filename", ""),
                            line_number=result_item.get("line_number", 0),
                            scanner="bandit",
                            rule_id=result_item.get("test_id", ""),
                            confidence=result_item.get("issue_confidence", "UNKNOWN"),
                            remediation=result_item.get("more_info", ""),
                            created_at=datetime.now().isoformat(),
                        )
                        findings.append(finding)

        except Exception as e:
            self.logger.error(f"Bandit scan failed: {e}")

        return findings

    async def _run_semgrep_scan(self, target_path: str) -> List[SecurityFinding]:
        """執行 Semgrep 掃描"""
        findings = []

        try:
            # 準備 Semgrep 命令
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{os.path.abspath(target_path)}:/code",
                "returntocorp/semgrep",
                "--config=auto",
                "--json",
                "/code",
            ]

            # 執行掃描
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode in [0, 1]:
                if result.stdout:
                    semgrep_data = json.loads(result.stdout)

                    for result_item in semgrep_data.get("results", []):
                        severity = self._map_semgrep_severity(
                            result_item.get("extra", {}).get("severity", "INFO")
                        )

                        finding = SecurityFinding(
                            id=f"semgrep_{result_item.get('check_id')}_{int(time.time())}",
                            severity=severity,
                            title=result_item.get("extra", {}).get("message", ""),
                            description=result_item.get("extra", {}).get("message", ""),
                            file_path=result_item.get("path", ""),
                            line_number=result_item.get("start", {}).get("line", 0),
                            scanner="semgrep",
                            rule_id=result_item.get("check_id", ""),
                            confidence="HIGH",
                            remediation=result_item.get("extra", {}).get("fix", ""),
                            created_at=datetime.now().isoformat(),
                        )
                        findings.append(finding)

        except Exception as e:
            self.logger.error(f"Semgrep scan failed: {e}")

        return findings

    async def _scan_dependencies(self, target_path: str) -> ScanResult:
        """掃描依賴套件漏洞"""
        start_time = datetime.now()
        findings = []

        try:
            # Safety 掃描 Python 依賴
            safety_result = await self._run_safety_scan(target_path)
            findings.extend(safety_result)

            # npm audit 掃描 Node.js 依賴
            npm_result = await self._run_npm_audit(target_path)
            findings.extend(npm_result)

            status = "completed"

        except Exception as e:
            self.logger.error(f"Dependencies scan failed: {e}")
            status = "failed"

        end_time = datetime.now()

        return ScanResult(
            scanner="dependencies",
            target=target_path,
            scan_type="dependencies",
            start_time=start_time,
            end_time=end_time,
            status=status,
            findings=findings,
            metadata={"scan_duration": (end_time - start_time).total_seconds()},
            summary=self._summarize_findings(findings),
        )

    async def _run_safety_scan(self, target_path: str) -> List[SecurityFinding]:
        """執行 Safety 掃描"""
        findings = []

        # 查找 requirements.txt 檔案
        req_files = list(Path(target_path).rglob("requirements*.txt"))

        for req_file in req_files:
            try:
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{req_file.parent}:/code",
                    "pyupio/safety",
                    "check",
                    "--json",
                    "-r",
                    f"/code/{req_file.name}",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

                if result.stdout:
                    safety_data = json.loads(result.stdout)

                    for vuln in safety_data:
                        finding = SecurityFinding(
                            id=f"safety_{vuln.get('id')}_{int(time.time())}",
                            severity="HIGH",  # Safety 通常報告高風險漏洞
                            title=f"Vulnerable package: {vuln.get('package_name')}",
                            description=vuln.get("advisory", ""),
                            file_path=str(req_file),
                            line_number=0,
                            scanner="safety",
                            rule_id=str(vuln.get("id", "")),
                            confidence="HIGH",
                            remediation=f"Upgrade to version {vuln.get('vulnerable_spec', '')}",
                            cve_id=vuln.get("cve"),
                            created_at=datetime.now().isoformat(),
                        )
                        findings.append(finding)

            except Exception as e:
                self.logger.error(f"Safety scan failed for {req_file}: {e}")

        return findings

    async def _run_npm_audit(self, target_path: str) -> List[SecurityFinding]:
        """執行 npm audit 掃描"""
        findings = []

        # 查找 package.json 檔案
        package_files = list(Path(target_path).rglob("package.json"))

        for package_file in package_files:
            try:
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{package_file.parent}:/code",
                    "-w",
                    "/code",
                    "node:18-alpine",
                    "npm",
                    "audit",
                    "--audit-level=moderate",
                    "--json",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

                if result.stdout:
                    audit_data = json.loads(result.stdout)

                    for vuln_id, vuln in audit_data.get("vulnerabilities", {}).items():
                        severity = vuln.get("severity", "unknown").upper()

                        finding = SecurityFinding(
                            id=f"npm_{vuln_id}_{int(time.time())}",
                            severity=severity,
                            title=f"Vulnerable npm package: {vuln.get('name')}",
                            description=vuln.get("title", ""),
                            file_path=str(package_file),
                            line_number=0,
                            scanner="npm_audit",
                            rule_id=vuln_id,
                            confidence="HIGH",
                            remediation=f"Update to version {vuln.get('fixAvailable', {}).get('version', 'latest')}",
                            cve_id=vuln.get("cves", [None])[0] if vuln.get("cves") else None,
                            created_at=datetime.now().isoformat(),
                        )
                        findings.append(finding)

            except Exception as e:
                self.logger.error(f"npm audit failed for {package_file}: {e}")

        return findings

    async def _scan_secrets(self, target_path: str) -> ScanResult:
        """掃描密鑰洩露"""
        start_time = datetime.now()
        findings = []

        try:
            # Trivy 密鑰掃描
            trivy_result = await self._run_trivy_secret_scan(target_path)
            findings.extend(trivy_result)

            # Gitleaks 掃描
            gitleaks_result = await self._run_gitleaks_scan(target_path)
            findings.extend(gitleaks_result)

            status = "completed"

        except Exception as e:
            self.logger.error(f"Secrets scan failed: {e}")
            status = "failed"

        end_time = datetime.now()

        return ScanResult(
            scanner="secrets",
            target=target_path,
            scan_type="secrets",
            start_time=start_time,
            end_time=end_time,
            status=status,
            findings=findings,
            metadata={"scan_duration": (end_time - start_time).total_seconds()},
            summary=self._summarize_findings(findings),
        )

    async def _run_trivy_secret_scan(self, target_path: str) -> List[SecurityFinding]:
        """執行 Trivy 密鑰掃描"""
        findings = []

        try:
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{os.path.abspath(target_path)}:/code",
                "-v",
                f"{self.config_dir}:/config",
                "aquasec/trivy",
                "fs",
                "--scanners",
                "secret",
                "--config",
                "/config/trivy-secret.yaml",
                "--format",
                "json",
                "/code",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0 and result.stdout:
                trivy_data = json.loads(result.stdout)

                for result_item in trivy_data.get("Results", []):
                    for secret in result_item.get("Secrets", []):
                        finding = SecurityFinding(
                            id=f"trivy_secret_{secret.get('RuleID')}_{int(time.time())}",
                            severity=secret.get("Severity", "UNKNOWN").upper(),
                            title=f"Secret detected: {secret.get('Title', '')}",
                            description=secret.get("Match", ""),
                            file_path=result_item.get("Target", ""),
                            line_number=secret.get("StartLine", 0),
                            scanner="trivy_secrets",
                            rule_id=secret.get("RuleID", ""),
                            confidence="HIGH",
                            remediation="Remove or encrypt the detected secret",
                            created_at=datetime.now().isoformat(),
                        )
                        findings.append(finding)

        except Exception as e:
            self.logger.error(f"Trivy secret scan failed: {e}")

        return findings

    async def _run_gitleaks_scan(self, target_path: str) -> List[SecurityFinding]:
        """執行 Gitleaks 掃描"""
        findings = []

        try:
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{os.path.abspath(target_path)}:/code",
                "zricethezav/gitleaks:latest",
                "detect",
                "--source=/code",
                "--report-format=json",
                "--report-path=/tmp/gitleaks.json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

            # Gitleaks 在找到密鑰時返回非零狀態碼
            if result.stdout:
                try:
                    gitleaks_data = json.loads(result.stdout)

                    for secret in gitleaks_data:
                        finding = SecurityFinding(
                            id=f"gitleaks_{secret.get('RuleID')}_{int(time.time())}",
                            severity="HIGH",
                            title=f"Secret detected: {secret.get('Description', '')}",
                            description=secret.get("Match", ""),
                            file_path=secret.get("File", ""),
                            line_number=secret.get("StartLine", 0),
                            scanner="gitleaks",
                            rule_id=secret.get("RuleID", ""),
                            confidence="HIGH",
                            remediation="Remove or encrypt the detected secret",
                            created_at=datetime.now().isoformat(),
                        )
                        findings.append(finding)

                except json.JSONDecodeError:
                    pass  # 沒有發現密鑰

        except Exception as e:
            self.logger.error(f"Gitleaks scan failed: {e}")

        return findings

    async def _scan_container_image(self, image_name: str) -> ScanResult:
        """掃描容器映像"""
        start_time = datetime.now()
        findings = []

        try:
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                "/var/run/docker.sock:/var/run/docker.sock",
                "-v",
                f"{self.config_dir}:/config",
                "aquasec/trivy",
                "image",
                "--config",
                "/config/trivy-config.yaml",
                "--format",
                "json",
                image_name,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0 and result.stdout:
                trivy_data = json.loads(result.stdout)

                for result_item in trivy_data.get("Results", []):
                    for vuln in result_item.get("Vulnerabilities", []):
                        finding = SecurityFinding(
                            id=f"trivy_container_{vuln.get('VulnerabilityID')}_{int(time.time())}",
                            severity=vuln.get("Severity", "UNKNOWN").upper(),
                            title=f"Container vulnerability: {vuln.get('Title', '')}",
                            description=vuln.get("Description", ""),
                            file_path=f"Container: {image_name}",
                            line_number=0,
                            scanner="trivy_container",
                            rule_id=vuln.get("VulnerabilityID", ""),
                            confidence="HIGH",
                            remediation=f"Update package {vuln.get('PkgName', '')} to {vuln.get('FixedVersion', 'latest')}",
                            cve_id=vuln.get("VulnerabilityID"),
                            cvss_score=vuln.get("CVSS", {}).get("V3Score"),
                            created_at=datetime.now().isoformat(),
                        )
                        findings.append(finding)

            status = "completed"

        except Exception as e:
            self.logger.error(f"Container scan failed for {image_name}: {e}")
            status = "failed"

        end_time = datetime.now()

        return ScanResult(
            scanner="container",
            target=image_name,
            scan_type="container",
            start_time=start_time,
            end_time=end_time,
            status=status,
            findings=findings,
            metadata={"scan_duration": (end_time - start_time).total_seconds()},
            summary=self._summarize_findings(findings),
        )

    async def _scan_infrastructure(self, target_path: str) -> ScanResult:
        """掃描基礎設施配置"""
        start_time = datetime.now()
        findings = []

        try:
            # 掃描 Dockerfile
            dockerfile_findings = await self._scan_dockerfiles(target_path)
            findings.extend(dockerfile_findings)

            # 掃描 Kubernetes 配置
            k8s_findings = await self._scan_kubernetes_configs(target_path)
            findings.extend(k8s_findings)

            # 掃描 Docker Compose 配置
            compose_findings = await self._scan_docker_compose_configs(target_path)
            findings.extend(compose_findings)

            status = "completed"

        except Exception as e:
            self.logger.error(f"Infrastructure scan failed: {e}")
            status = "failed"

        end_time = datetime.now()

        return ScanResult(
            scanner="infrastructure",
            target=target_path,
            scan_type="infrastructure",
            start_time=start_time,
            end_time=end_time,
            status=status,
            findings=findings,
            metadata={"scan_duration": (end_time - start_time).total_seconds()},
            summary=self._summarize_findings(findings),
        )

    async def _scan_dockerfiles(self, target_path: str) -> List[SecurityFinding]:
        """掃描 Dockerfile 安全問題"""
        findings = []

        dockerfiles = list(Path(target_path).rglob("Dockerfile*"))

        for dockerfile in dockerfiles:
            try:
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{dockerfile.parent}:/code",
                    "aquasec/trivy",
                    "config",
                    "--format",
                    "json",
                    f"/code/{dockerfile.name}",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode == 0 and result.stdout:
                    trivy_data = json.loads(result.stdout)

                    for result_item in trivy_data.get("Results", []):
                        for misconfig in result_item.get("Misconfigurations", []):
                            finding = SecurityFinding(
                                id=f"dockerfile_{misconfig.get('ID')}_{int(time.time())}",
                                severity=misconfig.get("Severity", "UNKNOWN").upper(),
                                title=f"Dockerfile issue: {misconfig.get('Title', '')}",
                                description=misconfig.get("Description", ""),
                                file_path=str(dockerfile),
                                line_number=misconfig.get("CauseMetadata", {}).get("StartLine", 0),
                                scanner="trivy_dockerfile",
                                rule_id=misconfig.get("ID", ""),
                                confidence="HIGH",
                                remediation=misconfig.get("Resolution", ""),
                                created_at=datetime.now().isoformat(),
                            )
                            findings.append(finding)

            except Exception as e:
                self.logger.error(f"Dockerfile scan failed for {dockerfile}: {e}")

        return findings

    async def _scan_kubernetes_configs(self, target_path: str) -> List[SecurityFinding]:
        """掃描 Kubernetes 配置安全問題"""
        findings = []

        # 查找 K8s 配置檔案
        k8s_files = []
        k8s_files.extend(list(Path(target_path).rglob("*.yaml")))
        k8s_files.extend(list(Path(target_path).rglob("*.yml")))

        for k8s_file in k8s_files:
            # 簡單檢查是否為 K8s 配置
            try:
                with open(k8s_file, "r") as f:
                    content = f.read()
                    if "apiVersion:" in content and "kind:" in content:
                        # 這很可能是 K8s 配置檔案
                        cmd = [
                            "docker",
                            "run",
                            "--rm",
                            "-v",
                            f"{k8s_file.parent}:/code",
                            "aquasec/trivy",
                            "config",
                            "--format",
                            "json",
                            f"/code/{k8s_file.name}",
                        ]

                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                        if result.returncode == 0 and result.stdout:
                            trivy_data = json.loads(result.stdout)

                            for result_item in trivy_data.get("Results", []):
                                for misconfig in result_item.get("Misconfigurations", []):
                                    finding = SecurityFinding(
                                        id=f"k8s_{misconfig.get('ID')}_{int(time.time())}",
                                        severity=misconfig.get("Severity", "UNKNOWN").upper(),
                                        title=f"K8s config issue: {misconfig.get('Title', '')}",
                                        description=misconfig.get("Description", ""),
                                        file_path=str(k8s_file),
                                        line_number=misconfig.get("CauseMetadata", {}).get(
                                            "StartLine", 0
                                        ),
                                        scanner="trivy_k8s",
                                        rule_id=misconfig.get("ID", ""),
                                        confidence="HIGH",
                                        remediation=misconfig.get("Resolution", ""),
                                        created_at=datetime.now().isoformat(),
                                    )
                                    findings.append(finding)

            except Exception as e:
                self.logger.debug(f"K8s config scan failed for {k8s_file}: {e}")

        return findings

    async def _scan_docker_compose_configs(self, target_path: str) -> List[SecurityFinding]:
        """掃描 Docker Compose 配置安全問題"""
        findings = []

        compose_files = list(Path(target_path).rglob("docker-compose*.yml"))
        compose_files.extend(list(Path(target_path).rglob("docker-compose*.yaml")))

        for compose_file in compose_files:
            try:
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{compose_file.parent}:/code",
                    "aquasec/trivy",
                    "config",
                    "--format",
                    "json",
                    f"/code/{compose_file.name}",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode == 0 and result.stdout:
                    trivy_data = json.loads(result.stdout)

                    for result_item in trivy_data.get("Results", []):
                        for misconfig in result_item.get("Misconfigurations", []):
                            finding = SecurityFinding(
                                id=f"compose_{misconfig.get('ID')}_{int(time.time())}",
                                severity=misconfig.get("Severity", "UNKNOWN").upper(),
                                title=f"Docker Compose issue: {misconfig.get('Title', '')}",
                                description=misconfig.get("Description", ""),
                                file_path=str(compose_file),
                                line_number=misconfig.get("CauseMetadata", {}).get("StartLine", 0),
                                scanner="trivy_compose",
                                rule_id=misconfig.get("ID", ""),
                                confidence="HIGH",
                                remediation=misconfig.get("Resolution", ""),
                                created_at=datetime.now().isoformat(),
                            )
                            findings.append(finding)

            except Exception as e:
                self.logger.error(f"Docker Compose scan failed for {compose_file}: {e}")

        return findings

    def _summarize_findings(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """統計發現摘要"""
        summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}

        for finding in findings:
            severity = finding.severity.upper()
            if severity in summary:
                summary[severity] += 1
            else:
                summary["UNKNOWN"] += 1

        return summary

    def _map_semgrep_severity(self, severity: str) -> str:
        """映射 Semgrep 嚴重程度"""
        mapping = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}
        return mapping.get(severity.upper(), "UNKNOWN")

    async def _generate_comprehensive_report(
        self, results: Dict[str, ScanResult]
    ) -> Dict[str, Any]:
        """生成綜合報告"""
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_scanners": len(results),
            "summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0},
            "scanner_results": {},
            "recommendations": [],
        }

        all_findings = []

        for scanner_name, scan_result in results.items():
            report["scanner_results"][scanner_name] = {
                "status": scan_result.status,
                "findings_count": len(scan_result.findings),
                "summary": scan_result.summary,
                "duration": scan_result.metadata.get("scan_duration", 0),
            }

            # 累計統計
            for severity, count in scan_result.summary.items():
                report["summary"][severity] += count

            all_findings.extend(scan_result.findings)

        # 生成建議
        report["recommendations"] = self._generate_recommendations(all_findings)

        # 儲存報告
        report_file = self.reports_dir / f"comprehensive_security_report_{int(time.time())}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return report

    def _generate_recommendations(self, findings: List[SecurityFinding]) -> List[str]:
        """生成安全建議"""
        recommendations = []

        # 統計嚴重問題
        critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in findings if f.severity == "HIGH")

        if critical_count > 0:
            recommendations.append(f"立即修復 {critical_count} 個關鍵安全問題")

        if high_count > 0:
            recommendations.append(f"優先修復 {high_count} 個高風險安全問題")

        # 檢查常見問題類型
        scanner_counts = {}
        for finding in findings:
            scanner_counts[finding.scanner] = scanner_counts.get(finding.scanner, 0) + 1

        if scanner_counts.get("trivy_secrets", 0) > 0:
            recommendations.append("檢查並移除程式碼中的硬編碼密鑰")

        if scanner_counts.get("bandit", 0) > 0:
            recommendations.append("修復 Python 程式碼中的安全漏洞")

        if scanner_counts.get("safety", 0) > 0:
            recommendations.append("更新存在安全漏洞的 Python 依賴套件")

        if scanner_counts.get("npm_audit", 0) > 0:
            recommendations.append("更新存在安全漏洞的 Node.js 依賴套件")

        return recommendations

    async def _send_security_alerts(self, results: Dict[str, ScanResult]):
        """發送安全告警"""
        total_critical = sum(r.summary.get("CRITICAL", 0) for r in results.values())
        total_high = sum(r.summary.get("HIGH", 0) for r in results.values())

        if total_critical > 0 or total_high > 5:
            # 發送高優先級告警
            alert_data = {
                "alert": "SecurityScanAlert",
                "severity": "high" if total_critical > 0 else "medium",
                "message": f"Security scan found {total_critical} critical and {total_high} high severity issues",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "critical_issues": total_critical,
                    "high_issues": total_high,
                    "scanners_run": list(results.keys()),
                },
            }

            # 這裡可以整合到 Alertmanager 或其他告警系統
            self.logger.warning(f"Security Alert: {alert_data['message']}")


async def main():
    """主函數 - 示例用法"""
    scanner = SecurityScanner()

    # 執行綜合掃描
    results = await scanner.run_comprehensive_scan(
        target_path="./",
        scan_types=["code", "dependencies", "secrets"],
        docker_images=["auto-video/api-gateway:latest", "auto-video/auth-service:latest"],
    )

    # 輸出結果摘要
    for scanner_name, result in results.items():
        print(f"\n{scanner_name} scan:")
        print(f"  Status: {result.status}")
        print(f"  Findings: {len(result.findings)}")
        print(f"  Summary: {result.summary}")


if __name__ == "__main__":
    asyncio.run(main())
