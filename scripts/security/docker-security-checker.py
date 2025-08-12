#!/usr/bin/env python3
"""
Docker 安全配置檢查器
檢查 Docker 配置和容器的安全設定
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import yaml


class DockerSecurityChecker:
    """Docker 安全檢查器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.issues: List[Dict] = []

    def check_all_security(self) -> Dict[str, Any]:
        """檢查所有 Docker 安全配置"""
        print("🐳 檢查 Docker 安全配置...")
        print(f"專案根目錄: {self.project_root}")
        print("-" * 50)

        # 檢查 Docker Compose 配置
        self._check_docker_compose_files()

        # 檢查 Dockerfile 安全性
        self._check_dockerfile_security()

        # 檢查運行中的容器
        self._check_running_containers()

        # 檢查 Docker 守護程序配置
        self._check_docker_daemon()

        return self._generate_report()

    def _check_docker_compose_files(self):
        """檢查 Docker Compose 檔案安全性"""
        print("\n📋 檢查 Docker Compose 檔案...")

        compose_files = list(self.project_root.glob("docker-compose*.yml"))
        compose_files.extend(list(self.project_root.glob("docker-compose*.yaml")))

        for compose_file in compose_files:
            self._analyze_compose_file(compose_file)

    def _analyze_compose_file(self, compose_file: Path):
        """分析單個 Docker Compose 檔案"""
        try:
            with open(compose_file, "r", encoding="utf-8") as f:
                compose_config = yaml.safe_load(f)

            print(f"🔍 分析: {compose_file.name}")

            if "services" not in compose_config:
                return

            for service_name, service_config in compose_config["services"].items():
                self._check_service_security(service_name, service_config, compose_file)

        except Exception as e:
            self.issues.append(
                {
                    "type": "compose_file_error",
                    "file": str(compose_file),
                    "severity": "medium",
                    "message": f"無法解析 Docker Compose 檔案: {e}",
                }
            )

    def _check_service_security(self, service_name: str, config: Dict, compose_file: Path):
        """檢查服務安全配置"""
        # 檢查特權模式
        if config.get("privileged", False):
            self.issues.append(
                {
                    "type": "privileged_container",
                    "service": service_name,
                    "file": str(compose_file),
                    "severity": "critical",
                    "message": f"服務 {service_name} 使用特權模式運行",
                }
            )

        # 檢查用戶配置
        if "user" not in config:
            self.issues.append(
                {
                    "type": "no_user_specified",
                    "service": service_name,
                    "file": str(compose_file),
                    "severity": "high",
                    "message": f"服務 {service_name} 未指定非 root 用戶",
                }
            )
        elif config["user"] in ["root", "0", "0:0"]:
            self.issues.append(
                {
                    "type": "root_user",
                    "service": service_name,
                    "file": str(compose_file),
                    "severity": "high",
                    "message": f"服務 {service_name} 使用 root 用戶運行",
                }
            )

        # 檢查 capabilities
        if "cap_add" in config:
            dangerous_caps = ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "SYS_MODULE"]
            for cap in config["cap_add"]:
                if cap in dangerous_caps:
                    self.issues.append(
                        {
                            "type": "dangerous_capability",
                            "service": service_name,
                            "capability": cap,
                            "file": str(compose_file),
                            "severity": "high",
                            "message": f"服務 {service_name} 添加了危險的 capability: {cap}",
                        }
                    )

        if "cap_drop" not in config or "ALL" not in config.get("cap_drop", []):
            self.issues.append(
                {
                    "type": "no_cap_drop_all",
                    "service": service_name,
                    "file": str(compose_file),
                    "severity": "medium",
                    "message": f"服務 {service_name} 未移除所有 capabilities",
                }
            )

        # 檢查只讀檔案系統
        if not config.get("read_only", False):
            self.issues.append(
                {
                    "type": "no_readonly_filesystem",
                    "service": service_name,
                    "file": str(compose_file),
                    "severity": "medium",
                    "message": f"服務 {service_name} 未啟用只讀檔案系統",
                }
            )

        # 檢查 security_opt
        security_opts = config.get("security_opt", [])
        if "no-new-privileges:true" not in security_opts:
            self.issues.append(
                {
                    "type": "no_new_privileges_missing",
                    "service": service_name,
                    "file": str(compose_file),
                    "severity": "medium",
                    "message": f"服務 {service_name} 未設定 no-new-privileges",
                }
            )

        # 檢查網路配置
        if "network_mode" in config and config["network_mode"] == "host":
            self.issues.append(
                {
                    "type": "host_network",
                    "service": service_name,
                    "file": str(compose_file),
                    "severity": "high",
                    "message": f"服務 {service_name} 使用主機網路模式",
                }
            )

        # 檢查端口綁定
        if "ports" in config:
            for port in config["ports"]:
                if isinstance(port, str) and not port.startswith("127.0.0.1:"):
                    self.issues.append(
                        {
                            "type": "public_port_binding",
                            "service": service_name,
                            "port": port,
                            "file": str(compose_file),
                            "severity": "medium",
                            "message": f"服務 {service_name} 端口 {port} 綁定到所有介面",
                        }
                    )

        # 檢查環境變數
        if "environment" in config:
            for env_var in config["environment"]:
                if isinstance(env_var, str):
                    if any(
                        keyword in env_var.lower()
                        for keyword in ["password", "secret", "key", "token"]
                    ):
                        if "=" in env_var and not env_var.split("=")[1].startswith("${"):
                            self.issues.append(
                                {
                                    "type": "hardcoded_secret",
                                    "service": service_name,
                                    "file": str(compose_file),
                                    "severity": "critical",
                                    "message": f"服務 {service_name} 環境變數包含硬編碼機密信息",
                                }
                            )

        print(f"  ✅ 服務 {service_name}: 已檢查")

    def _check_dockerfile_security(self):
        """檢查 Dockerfile 安全性"""
        print("\n🐋 檢查 Dockerfile 安全性...")

        dockerfiles = list(self.project_root.rglob("Dockerfile*"))

        for dockerfile in dockerfiles:
            if dockerfile.is_file():
                self._analyze_dockerfile(dockerfile)

    def _analyze_dockerfile(self, dockerfile: Path):
        """分析 Dockerfile 安全性"""
        try:
            with open(dockerfile, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"🔍 分析: {dockerfile.relative_to(self.project_root)}")

            # 檢查基礎映像
            base_images = re.findall(r"^FROM\s+(.+)", content, re.MULTILINE)
            for base_image in base_images:
                if ":latest" in base_image or ":" not in base_image:
                    self.issues.append(
                        {
                            "type": "latest_tag",
                            "file": str(dockerfile),
                            "base_image": base_image,
                            "severity": "medium",
                            "message": f"Dockerfile 使用 latest 標籤: {base_image}",
                        }
                    )

            # 檢查 USER 指令
            user_instructions = re.findall(r"^USER\s+(.+)", content, re.MULTILINE)
            if not user_instructions:
                self.issues.append(
                    {
                        "type": "no_user_instruction",
                        "file": str(dockerfile),
                        "severity": "high",
                        "message": "Dockerfile 未指定非 root 用戶",
                    }
                )
            elif any(user in ["root", "0"] for user in user_instructions):
                self.issues.append(
                    {
                        "type": "root_user_dockerfile",
                        "file": str(dockerfile),
                        "severity": "high",
                        "message": "Dockerfile 明確指定 root 用戶",
                    }
                )

            # 檢查 COPY/ADD 權限
            copy_instructions = re.findall(
                r"^(COPY|ADD)\s+.*--chown=([^\s]+)", content, re.MULTILINE
            )
            for cmd, chown in copy_instructions:
                if chown in ["root", "0", "0:0"]:
                    self.issues.append(
                        {
                            "type": "root_chown",
                            "file": str(dockerfile),
                            "severity": "medium",
                            "message": f"{cmd} 指令使用 root 所有權",
                        }
                    )

            # 檢查套件更新
            if "apt-get update" in content and "apt-get upgrade" not in content:
                self.issues.append(
                    {
                        "type": "no_package_upgrade",
                        "file": str(dockerfile),
                        "severity": "low",
                        "message": "Dockerfile 更新套件列表但未升級套件",
                    }
                )

            # 檢查快取清理
            if "apt-get install" in content and "rm -rf /var/lib/apt/lists/*" not in content:
                self.issues.append(
                    {
                        "type": "no_cache_cleanup",
                        "file": str(dockerfile),
                        "severity": "low",
                        "message": "Dockerfile 未清理 apt 快取",
                    }
                )

            print(f"  ✅ {dockerfile.name}: 已檢查")

        except Exception as e:
            self.issues.append(
                {
                    "type": "dockerfile_error",
                    "file": str(dockerfile),
                    "severity": "medium",
                    "message": f"無法解析 Dockerfile: {e}",
                }
            )

    def _check_running_containers(self):
        """檢查運行中的容器安全性"""
        print("\n🔄 檢查運行中的容器...")

        try:
            # 獲取運行中的容器
            result = subprocess.run(
                ["docker", "ps", "--format", "json"], capture_output=True, text=True, check=True
            )

            if result.stdout.strip():
                containers = [json.loads(line) for line in result.stdout.strip().split("\n")]

                for container in containers:
                    self._check_container_security(container)
            else:
                print("  📋 沒有運行中的容器")

        except subprocess.CalledProcessError:
            print("  ❌ 無法獲取容器信息 (Docker 可能未運行)")
        except FileNotFoundError:
            print("  ❌ Docker 命令未找到")

    def _check_container_security(self, container: Dict):
        """檢查單個容器的安全性"""
        container_id = container["ID"]
        container_name = container["Names"]

        try:
            # 檢查容器詳細信息
            result = subprocess.run(
                ["docker", "inspect", container_id], capture_output=True, text=True, check=True
            )

            inspect_data = json.loads(result.stdout)[0]

            # 檢查特權模式
            if inspect_data["HostConfig"]["Privileged"]:
                self.issues.append(
                    {
                        "type": "running_privileged",
                        "container": container_name,
                        "severity": "critical",
                        "message": f"容器 {container_name} 以特權模式運行",
                    }
                )

            # 檢查用戶
            user = inspect_data["Config"].get("User", "root")
            if user in ["", "root", "0"]:
                self.issues.append(
                    {
                        "type": "running_as_root",
                        "container": container_name,
                        "severity": "high",
                        "message": f"容器 {container_name} 以 root 用戶運行",
                    }
                )

            # 檢查只讀檔案系統
            if not inspect_data["HostConfig"]["ReadonlyRootfs"]:
                self.issues.append(
                    {
                        "type": "running_not_readonly",
                        "container": container_name,
                        "severity": "medium",
                        "message": f"容器 {container_name} 未使用只讀檔案系統",
                    }
                )

            print(f"  ✅ 容器 {container_name}: 已檢查")

        except Exception as e:
            print(f"  ❌ 檢查容器 {container_name} 失敗: {e}")

    def _check_docker_daemon(self):
        """檢查 Docker 守護程序配置"""
        print("\n⚙️  檢查 Docker 守護程序配置...")

        try:
            # 檢查 Docker 版本
            result = subprocess.run(
                ["docker", "version", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )

            version_info = json.loads(result.stdout)
            docker_version = version_info["Server"]["Version"]

            print(f"  📋 Docker 版本: {docker_version}")

            # 檢查是否為最新版本 (簡單檢查)
            major_version = int(docker_version.split(".")[0])
            if major_version < 20:
                self.issues.append(
                    {
                        "type": "old_docker_version",
                        "version": docker_version,
                        "severity": "medium",
                        "message": f"Docker 版本過舊: {docker_version}",
                    }
                )

        except Exception as e:
            print(f"  ❌ 無法檢查 Docker 守護程序: {e}")

    def _generate_report(self) -> Dict[str, Any]:
        """生成安全檢查報告"""
        print("\n" + "=" * 50)
        print("📊 Docker 安全檢查報告")
        print("=" * 50)

        # 統計問題數量
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in self.issues:
            severity_counts[issue["severity"]] += 1

        print(f"總問題數: {len(self.issues)}")
        print(f"嚴重: {severity_counts['critical']}")
        print(f"高: {severity_counts['high']}")
        print(f"中: {severity_counts['medium']}")
        print(f"低: {severity_counts['low']}")

        if self.issues:
            print("\n⚠️  發現的問題:")
            for issue in sorted(
                self.issues,
                key=lambda x: ["critical", "high", "medium", "low"].index(x["severity"]),
            ):
                icon = {"critical": "🚨", "high": "⚠️", "medium": "🔸", "low": "💡"}[
                    issue["severity"]
                ]
                print(f"{icon} [{issue['severity'].upper()}] {issue['message']}")

        else:
            print("\n✅ 所有 Docker 配置安全設定正確！")

        # 安全建議
        print("\n📋 安全建議:")
        print("1. 使用非 root 用戶運行容器")
        print("2. 啟用只讀檔案系統")
        print("3. 移除不必要的 capabilities")
        print("4. 使用特定版本標籤而非 latest")
        print("5. 限制端口綁定到本地介面")
        print("6. 使用多階段構建減少攻擊面")
        print("7. 定期更新基礎映像")
        print("8. 掃描映像安全漏洞")

        return {
            "total_issues": len(self.issues),
            "severity_counts": severity_counts,
            "issues": self.issues,
            "status": "pass" if len(self.issues) == 0 else "fail",
        }


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="Docker 安全配置檢查器")
    parser.add_argument("--output", help="輸出報告到 JSON 檔案")

    args = parser.parse_args()

    checker = DockerSecurityChecker()
    report = checker.check_all_security()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 報告已儲存到: {args.output}")

    # 返回適當的退出碼
    exit_code = 0 if report["status"] == "pass" else 1
    exit(exit_code)


if __name__ == "__main__":
    main()
