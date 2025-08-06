#!/usr/bin/env python3
"""
OpenAPI 規範驗證腳本
驗證所有微服務的 OpenAPI 規範一致性
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import aiohttp
import yaml

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAPIValidator:
    """OpenAPI 規範驗證器"""

    def __init__(self):
        self.services = {
            "api-gateway": "http://localhost:8000",
            "auth-service": "http://localhost:8001",
            "data-service": "http://localhost:8002",
            "inference-service": "http://localhost:8003",
            "video-service": "http://localhost:8004",
            "ai-service": "http://localhost:8005",
            "social-service": "http://localhost:8006",
            "trend-service": "http://localhost:8007",
            "scheduler-service": "http://localhost:8008",
            "storage-service": "http://localhost:8009",
        }
        self.errors = []
        self.warnings = []

    async def fetch_openapi_spec(
        self, session: aiohttp.ClientSession, service_name: str, base_url: str
    ) -> Optional[Dict]:
        """獲取服務的 OpenAPI 規範"""
        openapi_urls = [
            f"{base_url}/openapi.json",
            f"{base_url}/docs/openapi.json",
            f"{base_url}/api/openapi.json",
        ]

        for url in openapi_urls:
            try:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        spec = await response.json()
                        logger.info(f"✅ Retrieved OpenAPI spec for {service_name}")
                        return spec
            except Exception:
                continue

        self.warnings.append(f"Could not retrieve OpenAPI spec for {service_name}")
        return None

    def validate_openapi_structure(self, service_name: str, spec: Dict) -> None:
        """驗證 OpenAPI 規範結構"""
        required_fields = ["openapi", "info", "paths"]

        for field in required_fields:
            if field not in spec:
                self.errors.append(f"{service_name}: Missing required field '{field}'")

        # 檢查版本
        if "openapi" in spec:
            version = spec["openapi"]
            if not version.startswith("3."):
                self.warnings.append(
                    f"{service_name}: Using OpenAPI version {version}, recommend 3.x"
                )

        # 檢查 info 部分
        if "info" in spec:
            info = spec["info"]
            required_info_fields = ["title", "version"]
            for field in required_info_fields:
                if field not in info:
                    self.errors.append(f"{service_name}: Missing info.{field}")

        # 檢查路徑
        if "paths" in spec and not spec["paths"]:
            self.warnings.append(f"{service_name}: No API paths defined")

    def validate_security_schemes(self, service_name: str, spec: Dict) -> None:
        """驗證安全方案"""
        if "components" not in spec:
            self.warnings.append(f"{service_name}: No security components defined")
            return

        components = spec["components"]
        if "securitySchemes" not in components:
            self.warnings.append(f"{service_name}: No security schemes defined")
            return

        security_schemes = components["securitySchemes"]

        # 檢查是否有 JWT 認證
        has_jwt = any(
            scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
            for scheme in security_schemes.values()
        )

        if not has_jwt:
            self.warnings.append(f"{service_name}: No JWT Bearer authentication scheme found")

    def validate_response_schemas(self, service_name: str, spec: Dict) -> None:
        """驗證回應結構"""
        if "paths" not in spec:
            return

        paths = spec["paths"]
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() not in [
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "PATCH",
                ]:
                    continue

                if "responses" not in operation:
                    self.errors.append(
                        f"{service_name}: No responses defined for {method.upper()} {path}"
                    )
                    continue

                responses = operation["responses"]

                # 檢查是否有成功回應
                success_codes = [code for code in responses.keys() if code.startswith("2")]
                if not success_codes:
                    self.warnings.append(
                        f"{service_name}: No success response for {method.upper()} {path}"
                    )

                # 檢查是否有錯誤處理
                error_codes = [code for code in responses.keys() if code.startswith(("4", "5"))]
                if not error_codes:
                    self.warnings.append(
                        f"{service_name}: No error responses for {method.upper()} {path}"
                    )

    def check_api_consistency(self, specs: Dict[str, Dict]) -> None:
        """檢查 API 一致性"""
        # 檢查版本一致性
        versions = {}
        for service_name, spec in specs.items():
            if "info" in spec and "version" in spec["info"]:
                version = spec["info"]["version"]
                if version in versions:
                    versions[version].append(service_name)
                else:
                    versions[version] = [service_name]

        if len(versions) > 1:
            self.warnings.append(f"Inconsistent API versions across services: {versions}")

        # 檢查安全方案一致性
        security_schemes = {}
        for service_name, spec in specs.items():
            if "components" in spec and "securitySchemes" in spec["components"]:
                schemes = spec["components"]["securitySchemes"]
                for scheme_name, scheme_def in schemes.items():
                    key = (
                        scheme_name,
                        scheme_def.get("type"),
                        scheme_def.get("scheme"),
                    )
                    if key in security_schemes:
                        security_schemes[key].append(service_name)
                    else:
                        security_schemes[key] = [service_name]

        # 檢查是否所有服務都使用相同的安全方案
        if security_schemes:
            scheme_counts = {k: len(v) for k, v in security_schemes.items()}
            max_count = max(scheme_counts.values())
            if max_count < len(specs):
                self.warnings.append("Not all services use the same security schemes")

    async def validate_all_services(self) -> None:
        """驗證所有服務的 OpenAPI 規範"""
        logger.info("🔍 Starting OpenAPI validation...")

        async with aiohttp.ClientSession() as session:
            # 獲取所有規範
            specs = {}
            tasks = []

            for service_name, base_url in self.services.items():
                task = self.fetch_openapi_spec(session, service_name, base_url)
                tasks.append((service_name, task))

            # 等待所有請求完成
            for service_name, task in tasks:
                try:
                    spec = await task
                    if spec:
                        specs[service_name] = spec
                except Exception as e:
                    self.warnings.append(f"Error fetching spec for {service_name}: {str(e)}")

            # 驗證每個規範
            for service_name, spec in specs.items():
                logger.info(f"🔍 Validating {service_name}...")
                self.validate_openapi_structure(service_name, spec)
                self.validate_security_schemes(service_name, spec)
                self.validate_response_schemas(service_name, spec)

            # 檢查一致性
            if specs:
                self.check_api_consistency(specs)

    def validate_static_schemas(self) -> None:
        """驗證靜態 OpenAPI 檔案"""
        schema_files = [
            Path("docs/api/openapi.yaml"),
            Path("docs/api/openapi.json"),
            Path("api-docs/openapi.yaml"),
        ]

        for schema_file in schema_files:
            if schema_file.exists():
                try:
                    if schema_file.suffix == ".yaml":
                        with open(schema_file, "r") as f:
                            spec = yaml.safe_load(f)
                    else:
                        with open(schema_file, "r") as f:
                            spec = json.load(f)

                    service_name = f"static:{schema_file.name}"
                    self.validate_openapi_structure(service_name, spec)
                    logger.info(f"✅ Validated static schema: {schema_file}")

                except Exception as e:
                    self.errors.append(f"Error validating {schema_file}: {str(e)}")

    def generate_report(self) -> int:
        """生成驗證報告"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 OPENAPI VALIDATION SUMMARY")
        logger.info("=" * 50)

        if self.errors:
            logger.error(f"❌ {len(self.errors)} ERRORS found:")
            for error in self.errors:
                logger.error(f"  • {error}")

        if self.warnings:
            logger.warning(f"⚠️  {len(self.warnings)} WARNINGS found:")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")

        if not self.errors and not self.warnings:
            logger.info("✅ All OpenAPI schemas are valid!")
        elif not self.errors:
            logger.info("✅ No critical errors found")

        logger.info("=" * 50)

        return 1 if self.errors else 0


async def main():
    """主要驗證流程"""
    validator = OpenAPIValidator()

    # 驗證靜態檔案
    validator.validate_static_schemas()

    # 驗證運行中的服務（如果可用）
    try:
        await validator.validate_all_services()
    except Exception as e:
        validator.warnings.append(f"Could not validate running services: {str(e)}")

    return validator.generate_report()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
