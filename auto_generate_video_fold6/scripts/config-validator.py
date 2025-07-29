#!/usr/bin/env python3
"""
配置驗證和同步工具
確保所有配置文件的一致性和完整性
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError


class ConfigValidator:
    """配置驗證器"""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or "config")
        self.schemas = {}
        self.validation_results = {}
        self.load_schemas()
    
    def load_schemas(self):
        """載入配置模式定義"""
        self.schemas = {
            "base": {
                "type": "object",
                "required": ["generation", "ai_services", "cost_control", "resources"],
                "properties": {
                    "generation": {
                        "type": "object",
                        "required": ["daily_video_limit", "platforms"],
                        "properties": {
                            "daily_video_limit": {"type": "integer", "minimum": 1},
                            "platforms": {"type": "array", "items": {"type": "string"}},
                            "max_duration_seconds": {"type": "integer", "minimum": 10}
                        }
                    },
                    "ai_services": {
                        "type": "object",
                        "required": ["text_generation", "image_generation"],
                        "properties": {
                            "text_generation": {
                                "type": "object", 
                                "required": ["provider"],
                                "properties": {
                                    "provider": {"type": "string", "enum": ["openai", "gemini", "claude"]},
                                    "model": {"type": "string"},
                                    "max_tokens": {"type": "integer", "minimum": 100}
                                }
                            },
                            "image_generation": {
                                "type": "object",
                                "required": ["provider"],
                                "properties": {
                                    "provider": {"type": "string", "enum": ["dalle", "midjourney", "stable-diffusion"]},
                                    "resolution": {"type": "string"},
                                    "quality": {"type": "string", "enum": ["standard", "high", "premium"]}
                                }
                            }
                        }
                    },
                    "cost_control": {
                        "type": "object",
                        "required": ["daily_budget_usd"],
                        "properties": {
                            "daily_budget_usd": {"type": "number", "minimum": 0},
                            "api_rate_limits": {"type": "object"}
                        }
                    },
                    "resources": {
                        "type": "object",
                        "properties": {
                            "max_memory_usage": {"type": "string"},
                            "max_cpu_cores": {"type": "integer", "minimum": 1},
                            "disk_space_limit": {"type": "string"}
                        }
                    }
                }
            },
            "auth": {
                "type": "object",
                "required": ["jwt", "oauth", "security"],
                "properties": {
                    "jwt": {
                        "type": "object",
                        "required": ["secret_key", "algorithm", "expire_minutes"],
                        "properties": {
                            "secret_key": {"type": "string", "minLength": 32},
                            "algorithm": {"type": "string", "enum": ["HS256", "RS256"]},
                            "expire_minutes": {"type": "integer", "minimum": 15}
                        }
                    },
                    "oauth": {
                        "type": "object",
                        "properties": {
                            "google": {"type": "object"},
                            "github": {"type": "object"},
                            "discord": {"type": "object"}
                        }
                    },
                    "security": {
                        "type": "object",
                        "properties": {
                            "password_min_length": {"type": "integer", "minimum": 8},
                            "max_login_attempts": {"type": "integer", "minimum": 3},
                            "lockout_duration_minutes": {"type": "integer", "minimum": 5}
                        }
                    }
                }
            }
        }
    
    def validate_config_file(self, config_file: Path) -> Tuple[bool, List[str]]:
        """驗證單個配置文件"""
        errors = []
        
        if not config_file.exists():
            return False, [f"配置文件不存在: {config_file}"]
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"JSON 格式錯誤: {e}"]
        except Exception as e:
            return False, [f"讀取文件失敗: {e}"]
        
        # 根據文件名選擇模式
        config_type = config_file.stem.replace('-config', '')
        schema = self.schemas.get(config_type)
        
        if schema:
            try:
                validate(instance=config_data, schema=schema)
            except ValidationError as e:
                errors.append(f"模式驗證失敗: {e.message}")
            except Exception as e:
                errors.append(f"驗證過程錯誤: {e}")
        
        # 自定義驗證規則
        custom_errors = self._custom_validation(config_data, config_type)
        errors.extend(custom_errors)
        
        return len(errors) == 0, errors
    
    def _custom_validation(self, config_data: Dict, config_type: str) -> List[str]:
        """自定義驗證規則"""
        errors = []
        
        if config_type == "base":
            # 檢查平台配置
            platforms = config_data.get("generation", {}).get("platforms", [])
            valid_platforms = ["tiktok", "youtube", "instagram", "twitter"]
            
            for platform in platforms:
                if platform not in valid_platforms:
                    errors.append(f"不支援的平台: {platform}")
            
            # 檢查預算和限制的合理性
            daily_limit = config_data.get("generation", {}).get("daily_video_limit", 0)
            daily_budget = config_data.get("cost_control", {}).get("daily_budget_usd", 0)
            
            estimated_cost_per_video = 0.50  # 假設每個影片成本
            if daily_budget > 0 and daily_limit * estimated_cost_per_video > daily_budget:
                errors.append(f"每日影片限制({daily_limit})可能超出預算({daily_budget} USD)")
        
        elif config_type == "auth":
            # 檢查 JWT 密鑰強度
            jwt_secret = config_data.get("jwt", {}).get("secret_key", "")
            if len(jwt_secret) < 32:
                errors.append("JWT 密鑰長度應至少 32 字符")
            
            # 檢查安全設置
            security = config_data.get("security", {})
            password_min_length = security.get("password_min_length", 0)
            if password_min_length < 8:
                errors.append("密碼最小長度應至少 8 字符")
        
        return errors
    
    def validate_all_configs(self) -> Dict[str, Any]:
        """驗證所有配置文件"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "files": {}
        }
        
        config_files = list(self.config_dir.glob("*-config.json"))
        results["total_files"] = len(config_files)
        
        for config_file in config_files:
            is_valid, errors = self.validate_config_file(config_file)
            
            results["files"][config_file.name] = {
                "valid": is_valid,
                "errors": errors,
                "size": config_file.stat().st_size,
                "modified": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            }
            
            if is_valid:
                results["valid_files"] += 1
            else:
                results["invalid_files"] += 1
        
        self.validation_results = results
        return results
    
    def check_config_consistency(self) -> Dict[str, Any]:
        """檢查配置間的一致性"""
        consistency_issues = []
        
        # 載入主要配置文件
        base_config = self._load_config("base-config.json")
        auth_config = self._load_config("auth-config.json")
        enterprise_config = self._load_config("enterprise-config.json")
        
        if not all([base_config, auth_config]):
            return {"issues": ["無法載入必要的配置文件"]}
        
        # 檢查服務端口是否衝突
        ports_used = set()
        for config_name, config_data in [
            ("base", base_config), 
            ("auth", auth_config), 
            ("enterprise", enterprise_config)
        ]:
            if config_data and "services" in config_data:
                for service, service_config in config_data["services"].items():
                    if "port" in service_config:
                        port = service_config["port"]
                        if port in ports_used:
                            consistency_issues.append(f"端口衝突: {port} 在多個服務中使用")
                        else:
                            ports_used.add(port)
        
        # 檢查資源限制的一致性
        if base_config and enterprise_config:
            base_memory = base_config.get("resources", {}).get("max_memory_usage")
            enterprise_memory = enterprise_config.get("resources", {}).get("max_memory_usage")
            
            if base_memory and enterprise_memory and base_memory != enterprise_memory:
                consistency_issues.append(f"記憶體限制不一致: base({base_memory}) vs enterprise({enterprise_memory})")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "issues_count": len(consistency_issues),
            "issues": consistency_issues
        }
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """載入配置文件"""
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def generate_config_template(self, config_type: str, output_file: str = None) -> str:
        """生成配置模板"""
        templates = {
            "base": {
                "generation": {
                    "daily_video_limit": 50,
                    "platforms": ["tiktok", "youtube", "instagram"],
                    "max_duration_seconds": 300,
                    "quality": "high"
                },
                "ai_services": {
                    "text_generation": {
                        "provider": "gemini",
                        "model": "gemini-pro",
                        "max_tokens": 2000
                    },
                    "image_generation": {
                        "provider": "stable-diffusion",
                        "resolution": "1024x1024",
                        "quality": "high"
                    },
                    "voice_cloning": {
                        "provider": "elevenlabs",
                        "voice_stability": 0.8,
                        "voice_similarity": 0.8
                    }
                },
                "cost_control": {
                    "daily_budget_usd": 25.0,
                    "api_rate_limits": {
                        "gemini_requests_per_hour": 100,
                        "dalle_requests_per_hour": 50,
                        "elevenlabs_requests_per_hour": 200
                    }
                },
                "resources": {
                    "max_memory_usage": "4GB",
                    "max_cpu_cores": 4,
                    "disk_space_limit": "100GB"
                },
                "scheduling": {
                    "enabled": True,
                    "work_hours": {
                        "start": "09:00",
                        "end": "18:00"
                    },
                    "auto_publish": False
                }
            },
            "auth": {
                "jwt": {
                    "secret_key": "your-super-secret-jwt-key-32chars-min",
                    "algorithm": "HS256",
                    "expire_minutes": 60
                },
                "oauth": {
                    "google": {
                        "client_id": "your-google-client-id",
                        "client_secret": "your-google-client-secret"
                    },
                    "github": {
                        "client_id": "your-github-client-id",
                        "client_secret": "your-github-client-secret"
                    }
                },
                "security": {
                    "password_min_length": 8,
                    "max_login_attempts": 5,
                    "lockout_duration_minutes": 15,
                    "require_email_verification": True
                }
            }
        }
        
        template = templates.get(config_type)
        if not template:
            raise ValueError(f"不支援的配置類型: {config_type}")
        
        if output_file is None:
            output_file = self.config_dir / f"{config_type}-config.template.json"
        else:
            output_file = Path(output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        return str(output_file)
    
    def sync_configs_with_environment(self) -> Dict[str, Any]:
        """同步配置與環境變數"""
        env_mappings = {
            "JWT_SECRET_KEY": "auth.jwt.secret_key",
            "DAILY_VIDEO_LIMIT": "base.generation.daily_video_limit",
            "DAILY_BUDGET": "base.cost_control.daily_budget_usd",
            "AI_TEXT_PROVIDER": "base.ai_services.text_generation.provider",
            "AI_IMAGE_PROVIDER": "base.ai_services.image_generation.provider"
        }
        
        sync_results = {
            "timestamp": datetime.now().isoformat(),
            "synced_vars": [],
            "missing_vars": [],
            "conflicts": []
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            
            if env_value:
                config_file, config_key = config_path.split('.', 1)
                config_data = self._load_config(f"{config_file}-config.json")
                
                if config_data:
                    # 獲取配置中的當前值
                    current_value = self._get_nested_value(config_data, config_key)
                    
                    if str(current_value) != env_value:
                        sync_results["conflicts"].append({
                            "env_var": env_var,
                            "env_value": env_value,
                            "config_value": current_value,
                            "config_path": config_path
                        })
                    else:
                        sync_results["synced_vars"].append(env_var)
                else:
                    sync_results["missing_vars"].append(f"配置文件 {config_file}-config.json 不存在")
            else:
                sync_results["missing_vars"].append(env_var)
        
        return sync_results
    
    def _get_nested_value(self, data: Dict, key_path: str):
        """獲取嵌套字典值"""
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    def generate_report(self, output_file: str = None) -> str:
        """生成完整的配置驗證報告"""
        validation_results = self.validate_all_configs()
        consistency_results = self.check_config_consistency()
        sync_results = self.sync_configs_with_environment()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_config_files": validation_results["total_files"],
                "valid_files": validation_results["valid_files"],
                "invalid_files": validation_results["invalid_files"],
                "consistency_issues": consistency_results["issues_count"],
                "sync_conflicts": len(sync_results.get("conflicts", []))
            },
            "validation": validation_results,
            "consistency": consistency_results,
            "environment_sync": sync_results,
            "recommendations": self._generate_recommendations(
                validation_results, consistency_results, sync_results
            )
        }
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"config_validation_report_{timestamp}.json"
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _generate_recommendations(self, validation_results: Dict, 
                                consistency_results: Dict, sync_results: Dict) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        if validation_results["invalid_files"] > 0:
            recommendations.append("修復配置文件驗證錯誤，確保所有配置文件格式正確")
        
        if consistency_results["issues_count"] > 0:
            recommendations.append("解決配置間的一致性問題，避免服務衝突")
        
        if len(sync_results.get("conflicts", [])) > 0:
            recommendations.append("同步環境變數與配置文件，確保部署一致性")
        
        if len(sync_results.get("missing_vars", [])) > 0:
            recommendations.append("設置缺失的環境變數，完善部署配置")
        
        if not recommendations:
            recommendations.append("配置系統運行良好，建議定期執行驗證檢查")
        
        return recommendations
    
    def print_summary(self):
        """打印配置驗證摘要"""
        if not self.validation_results:
            self.validate_all_configs()
        
        results = self.validation_results
        
        print("\n" + "="*60)
        print("⚙️  配置驗證摘要報告")
        print("="*60)
        print(f"📄 總配置文件: {results['total_files']}")
        print(f"✅ 有效文件: {results['valid_files']}")
        print(f"❌ 無效文件: {results['invalid_files']}")
        
        if results['invalid_files'] > 0:
            print("\n🚨 配置錯誤:")
            for filename, file_info in results['files'].items():
                if not file_info['valid']:
                    print(f"  ❌ {filename}:")
                    for error in file_info['errors']:
                        print(f"     - {error}")
        
        consistency = self.check_config_consistency()
        if consistency['issues_count'] > 0:
            print(f"\n⚠️  一致性問題 ({consistency['issues_count']} 個):")
            for issue in consistency['issues']:
                print(f"  - {issue}")
        
        sync = self.sync_configs_with_environment()
        if sync.get('conflicts'):
            print(f"\n🔄 環境同步衝突 ({len(sync['conflicts'])} 個):")
            for conflict in sync['conflicts']:
                print(f"  - {conflict['env_var']}: 環境({conflict['env_value']}) ≠ 配置({conflict['config_value']})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="配置驗證和同步工具")
    parser.add_argument("--config-dir", default="config", help="配置文件目錄")
    parser.add_argument("--report", help="生成報告文件路徑")
    parser.add_argument("--template", help="生成配置模板 (base|auth)")
    
    args = parser.parse_args()
    
    validator = ConfigValidator(args.config_dir)
    
    if args.template:
        try:
            template_file = validator.generate_config_template(args.template)
            print(f"✅ 配置模板已生成: {template_file}")
        except ValueError as e:
            print(f"❌ 錯誤: {e}")
            sys.exit(1)
    else:
        validator.print_summary()
        
        if args.report:
            report_file = validator.generate_report(args.report)
            print(f"\n📊 詳細報告已保存: {report_file}")