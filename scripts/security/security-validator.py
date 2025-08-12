#!/usr/bin/env python3
"""
Security Configuration Validator
安全配置驗證器 - 檢查系統安全配置的完整性和合規性
"""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class SecurityValidator:
    """Comprehensive security configuration validator"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.warnings = []
        self.recommendations = []
        
    def add_issue(self, severity: str, category: str, message: str, file_path: Optional[str] = None):
        """Add a security issue"""
        issue = {
            'severity': severity,  # critical, high, medium, low
            'category': category,
            'message': message,
            'file': file_path,
        }
        
        if severity in ['critical', 'high']:
            self.issues.append(issue)
        elif severity == 'medium':
            self.warnings.append(issue)
        else:
            self.recommendations.append(issue)
            
    def validate_jwt_configuration(self, env_files: List[Path]) -> None:
        """Validate JWT configuration"""
        print("🔍 Validating JWT Configuration...")
        
        for env_file in env_files:
            if not env_file.exists():
                continue
                
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Check JWT secret key
            jwt_secret_match = re.search(r'JWT_SECRET_KEY=(.+)', content)
            if jwt_secret_match:
                secret = jwt_secret_match.group(1).strip()
                
                # Check for weak secrets
                weak_secrets = [
                    'secret', 'password', 'test', 'dev', 'debug',
                    'your_secret_key_here', 'change_me', '123456'
                ]
                
                if any(weak in secret.lower() for weak in weak_secrets):
                    self.add_issue(
                        'critical',
                        'jwt',
                        f"Weak JWT secret detected in {env_file}",
                        str(env_file)
                    )
                    
                if len(secret) < 32:
                    self.add_issue(
                        'high',
                        'jwt',
                        f"JWT secret too short (< 32 chars) in {env_file}",
                        str(env_file)
                    )
                    
            # Check JWT algorithm
            algorithm_match = re.search(r'JWT_ALGORITHM=(.+)', content)
            if algorithm_match:
                algorithm = algorithm_match.group(1).strip()
                if algorithm not in ['HS256', 'RS256']:
                    self.add_issue(
                        'medium',
                        'jwt',
                        f"Potentially insecure JWT algorithm: {algorithm}",
                        str(env_file)
                    )
                    
            # Check token expiration
            access_expire_match = re.search(r'JWT_ACCESS_TOKEN_EXPIRE_MINUTES=(\d+)', content)
            if access_expire_match:
                expire_minutes = int(access_expire_match.group(1))
                if expire_minutes > 60:
                    self.add_issue(
                        'medium',
                        'jwt',
                        f"JWT access token expiration too long: {expire_minutes} minutes",
                        str(env_file)
                    )
                    
    def validate_database_security(self, env_files: List[Path]) -> None:
        """Validate database security configuration"""
        print("🔍 Validating Database Security...")
        
        for env_file in env_files:
            if not env_file.exists():
                continue
                
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Check for default database passwords
            db_password_patterns = [
                r'POSTGRES_PASSWORD=(.+)',
                r'DATABASE_PASSWORD=(.+)',
                r'DB_PASSWORD=(.+)',
            ]
            
            for pattern in db_password_patterns:
                match = re.search(pattern, content)
                if match:
                    password = match.group(1).strip()
                    
                    weak_passwords = [
                        'password', 'admin', 'root', 'test', '123456',
                        'postgres', 'database', 'your_password_here'
                    ]
                    
                    if any(weak in password.lower() for weak in weak_passwords):
                        self.add_issue(
                            'critical',
                            'database',
                            f"Weak database password detected in {env_file}",
                            str(env_file)
                        )
                        
                    if len(password) < 12:
                        self.add_issue(
                            'high',
                            'database',
                            f"Database password too short (< 12 chars) in {env_file}",
                            str(env_file)
                        )
                        
            # Check for plaintext database URLs in production
            if 'production' in str(env_file).lower():
                db_url_match = re.search(r'DATABASE_URL=(.+)', content)
                if db_url_match:
                    db_url = db_url_match.group(1).strip()
                    if not db_url.startswith('postgresql://') or 'localhost' in db_url:
                        self.add_issue(
                            'medium',
                            'database',
                            f"Production database configuration may be insecure in {env_file}",
                            str(env_file)
                        )
                        
    def validate_api_keys(self, env_files: List[Path]) -> None:
        """Validate API key configuration"""
        print("🔍 Validating API Keys...")
        
        sensitive_patterns = [
            r'OPENAI_API_KEY=(.+)',
            r'GOOGLE_API_KEY=(.+)',
            r'STRIPE_SECRET_KEY=(.+)',
            r'AWS_SECRET_ACCESS_KEY=(.+)',
            r'AZURE_CLIENT_SECRET=(.+)',
        ]
        
        for env_file in env_files:
            if not env_file.exists():
                continue
                
            with open(env_file, 'r') as f:
                content = f.read()
                
            for pattern in sensitive_patterns:
                match = re.search(pattern, content)
                if match:
                    api_key = match.group(1).strip()
                    
                    # Check for placeholder values
                    placeholders = [
                        'your_', 'replace_', 'change_', 'todo_',
                        'test_', 'example_', 'dummy_', 'fake_'
                    ]
                    
                    if any(placeholder in api_key.lower() for placeholder in placeholders):
                        self.add_issue(
                            'high',
                            'api_keys',
                            f"Placeholder API key detected: {pattern.split('=')[0]} in {env_file}",
                            str(env_file)
                        )
                        
    def validate_cors_configuration(self) -> None:
        """Validate CORS configuration"""
        print("🔍 Validating CORS Configuration...")
        
        # Check FastAPI CORS configuration
        fastapi_files = list(self.project_root.glob("src/services/*/app/main.py"))
        
        for file_path in fastapi_files:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check for overly permissive CORS
            if 'allow_origins=["*"]' in content:
                self.add_issue(
                    'high',
                    'cors',
                    f"Overly permissive CORS configuration (allow_origins=['*']) in {file_path}",
                    str(file_path)
                )
                
            if 'allow_credentials=True' in content and 'allow_origins=["*"]' in content:
                self.add_issue(
                    'critical',
                    'cors',
                    f"Dangerous CORS configuration: credentials with wildcard origins in {file_path}",
                    str(file_path)
                )
                
    def validate_docker_security(self) -> None:
        """Validate Docker security configuration"""
        print("🔍 Validating Docker Security...")
        
        dockerfile_paths = list(self.project_root.glob("**/Dockerfile"))
        
        for dockerfile_path in dockerfile_paths:
            with open(dockerfile_path, 'r') as f:
                content = f.read()
                
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check for running as root
                if line.startswith('USER root'):
                    self.add_issue(
                        'high',
                        'docker',
                        f"Running as root user in Dockerfile at line {i}",
                        str(dockerfile_path)
                    )
                    
                # Check for ADD instead of COPY
                if line.startswith('ADD ') and not line.startswith('ADD --'):
                    self.add_issue(
                        'medium',
                        'docker',
                        f"Use COPY instead of ADD for security at line {i}",
                        str(dockerfile_path)
                    )
                    
                # Check for latest tag usage
                if ':latest' in line and line.startswith('FROM'):
                    self.add_issue(
                        'medium',
                        'docker',
                        f"Using 'latest' tag is not recommended at line {i}",
                        str(dockerfile_path)
                    )
                    
    def validate_dependency_security(self) -> None:
        """Validate dependency security"""
        print("🔍 Validating Dependency Security...")
        
        # Check Python dependencies
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomli
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomli.load(f)
                    
                dependencies = pyproject_data.get('project', {}).get('dependencies', [])
                
                # Check for vulnerable packages (basic check)
                vulnerable_patterns = [
                    'django<3.',
                    'flask<2.',
                    'requests<2.20',
                    'urllib3<1.24',
                ]
                
                for dep in dependencies:
                    for pattern in vulnerable_patterns:
                        if pattern in dep.lower():
                            self.add_issue(
                                'high',
                                'dependencies',
                                f"Potentially vulnerable dependency: {dep}",
                                str(pyproject_path)
                            )
                            
            except ImportError:
                self.add_issue(
                    'low',
                    'dependencies',
                    "tomli not available for pyproject.toml parsing",
                    str(pyproject_path)
                )
                
        # Check Node.js dependencies
        package_json_path = self.project_root / "src/frontend/package.json"
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                
            dependencies = {
                **package_data.get('dependencies', {}),
                **package_data.get('devDependencies', {})
            }
            
            # Check for audit
            try:
                result = subprocess.run(
                    ['npm', 'audit', '--json'],
                    cwd=package_json_path.parent,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    audit_data = json.loads(result.stdout)
                    vulnerabilities = audit_data.get('vulnerabilities', {})
                    
                    for vuln_name, vuln_data in vulnerabilities.items():
                        severity = vuln_data.get('severity', 'unknown')
                        if severity in ['critical', 'high']:
                            self.add_issue(
                                severity,
                                'dependencies',
                                f"Vulnerable Node.js dependency: {vuln_name} ({severity})",
                                str(package_json_path)
                            )
                            
            except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
                self.add_issue(
                    'low',
                    'dependencies',
                    "Could not run npm audit for security check",
                    str(package_json_path)
                )
                
    def validate_ssl_configuration(self) -> None:
        """Validate SSL/TLS configuration"""
        print("🔍 Validating SSL Configuration...")
        
        # Check for SSL settings in environment files
        env_files = list(self.project_root.glob("config/environments/*.env"))
        
        for env_file in env_files:
            if 'production' in str(env_file).lower():
                with open(env_file, 'r') as f:
                    content = f.read()
                    
                if 'SSL_ENABLED=false' in content or 'FORCE_HTTPS=false' in content:
                    self.add_issue(
                        'high',
                        'ssl',
                        f"SSL disabled in production environment: {env_file}",
                        str(env_file)
                    )
                    
    def validate_logging_security(self) -> None:
        """Validate logging configuration for security"""
        print("🔍 Validating Logging Security...")
        
        python_files = list(self.project_root.glob("src/**/*.py"))
        
        sensitive_patterns = [
            r'log.*password',
            r'log.*secret',
            r'log.*token',
            r'log.*key',
            r'print.*password',
            r'print.*secret',
        ]
        
        for py_file in python_files:
            with open(py_file, 'r') as f:
                content = f.read()
                
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line_lower = line.lower()
                
                for pattern in sensitive_patterns:
                    if re.search(pattern, line_lower):
                        self.add_issue(
                            'high',
                            'logging',
                            f"Potential sensitive data logging at line {i}: {line.strip()[:50]}...",
                            str(py_file)
                        )
                        break
                        
    def check_file_permissions(self) -> None:
        """Check file permissions for sensitive files"""
        print("🔍 Checking File Permissions...")
        
        sensitive_files = [
            "config/environments/*.env",
            "config/keys/*.json",
            ".env*",
            "secrets/*",
        ]
        
        for pattern in sensitive_files:
            files = list(self.project_root.glob(pattern))
            
            for file_path in files:
                if file_path.is_file():
                    stat_info = file_path.stat()
                    permissions = oct(stat_info.st_mode)[-3:]
                    
                    # Check if file is readable by others
                    if permissions[2] in ['4', '5', '6', '7']:  # Others have read permission
                        self.add_issue(
                            'high',
                            'permissions',
                            f"Sensitive file readable by others: {file_path} ({permissions})",
                            str(file_path)
                        )
                        
    def run_all_validations(self) -> Dict[str, any]:
        """Run all security validations"""
        print("🛡️  Starting Security Validation...")
        
        # Find environment files
        env_files = list(self.project_root.glob("config/environments/*.env"))
        env_files.extend(list(self.project_root.glob(".env*")))
        
        # Run validations
        self.validate_jwt_configuration(env_files)
        self.validate_database_security(env_files)
        self.validate_api_keys(env_files)
        self.validate_cors_configuration()
        self.validate_docker_security()
        self.validate_dependency_security()
        self.validate_ssl_configuration()
        self.validate_logging_security()
        self.check_file_permissions()
        
        # Compile results
        results = {
            'summary': {
                'critical_issues': len([i for i in self.issues if i['severity'] == 'critical']),
                'high_issues': len([i for i in self.issues if i['severity'] == 'high']),
                'medium_issues': len(self.warnings),
                'low_issues': len(self.recommendations),
                'total_issues': len(self.issues) + len(self.warnings) + len(self.recommendations),
            },
            'issues': self.issues,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
        }
        
        return results
        
    def generate_report(self, results: Dict[str, any], output_format: str = 'text') -> str:
        """Generate security report"""
        if output_format == 'json':
            return json.dumps(results, indent=2)
            
        # Text format
        report_lines = [
            "🛡️  Security Validation Report",
            "=" * 50,
            "",
            f"📊 Summary:",
            f"  Critical Issues: {results['summary']['critical_issues']}",
            f"  High Issues: {results['summary']['high_issues']}",
            f"  Medium Issues: {results['summary']['medium_issues']}",
            f"  Low Issues: {results['summary']['low_issues']}",
            f"  Total Issues: {results['summary']['total_issues']}",
            "",
        ]
        
        # Critical and High Issues
        if results['issues']:
            report_lines.extend([
                "🚨 Critical & High Issues:",
                "-" * 30,
            ])
            
            for issue in results['issues']:
                severity_icon = "🔴" if issue['severity'] == 'critical' else "🟠"
                report_lines.extend([
                    f"{severity_icon} [{issue['severity'].upper()}] {issue['category']}",
                    f"   {issue['message']}",
                    f"   File: {issue.get('file', 'N/A')}",
                    "",
                ])
                
        # Warnings
        if results['warnings']:
            report_lines.extend([
                "⚠️  Warnings:",
                "-" * 15,
            ])
            
            for warning in results['warnings']:
                report_lines.extend([
                    f"🟡 [{warning['severity'].upper()}] {warning['category']}",
                    f"   {warning['message']}",
                    f"   File: {warning.get('file', 'N/A')}",
                    "",
                ])
                
        # Recommendations
        if results['recommendations']:
            report_lines.extend([
                "💡 Recommendations:",
                "-" * 20,
            ])
            
            for rec in results['recommendations']:
                report_lines.extend([
                    f"🔵 [{rec['severity'].upper()}] {rec['category']}",
                    f"   {rec['message']}",
                    f"   File: {rec.get('file', 'N/A')}",
                    "",
                ])
                
        return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(description="Security Configuration Validator")
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path.cwd(),
        help='Project root directory'
    )
    parser.add_argument(
        '--output-format',
        choices=['text', 'json'],
        default='text',
        help='Output format'
    )
    parser.add_argument(
        '--output-file',
        type=Path,
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '--fail-on-critical',
        action='store_true',
        help='Exit with error code if critical issues found'
    )
    
    args = parser.parse_args()
    
    validator = SecurityValidator(args.project_root)
    results = validator.run_all_validations()
    
    # Generate report
    report = validator.generate_report(results, args.output_format)
    
    # Output report
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(report)
        print(f"✅ Security report saved to: {args.output_file}")
    else:
        print(report)
        
    # Exit with appropriate code
    if args.fail_on_critical and results['summary']['critical_issues'] > 0:
        print(f"❌ Found {results['summary']['critical_issues']} critical security issues")
        return 1
    elif results['summary']['total_issues'] == 0:
        print("✅ No security issues found!")
        return 0
    else:
        print(f"⚠️  Found {results['summary']['total_issues']} security issues")
        return 0


if __name__ == "__main__":
    exit(main())