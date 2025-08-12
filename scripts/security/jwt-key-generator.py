#!/usr/bin/env python3
"""
Enterprise JWT Key Management System
企業級JWT密鑰管理系統 - 生成和管理安全密鑰
"""

import argparse
import base64
import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class JWTKeyManager:
    """Enterprise-grade JWT key management"""
    
    def __init__(self, key_store_path: str = "config/keys"):
        self.key_store_path = Path(key_store_path)
        self.key_store_path.mkdir(parents=True, exist_ok=True)
        
    def generate_symmetric_key(self, key_size: int = 32) -> str:
        """Generate a cryptographically secure symmetric key"""
        return base64.urlsafe_b64encode(secrets.token_bytes(key_size)).decode('utf-8')
        
    def generate_rsa_keypair(self, key_size: int = 2048) -> Dict[str, str]:
        """Generate RSA asymmetric key pair"""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return {
            'private_key': private_pem.decode('utf-8'),
            'public_key': public_pem.decode('utf-8'),
        }
        
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        """Derive a key from password using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(32)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode())).decode('utf-8')
        salt_b64 = base64.urlsafe_b64encode(salt).decode('utf-8')
        
        return {
            'key': key,
            'salt': salt_b64,
            'iterations': 100000,
            'algorithm': 'SHA256'
        }
        
    def generate_key_set(self, environment: str = 'development') -> Dict[str, any]:
        """Generate a complete set of keys for an environment"""
        keyset = {
            'environment': environment,
            'generated_at': datetime.utcnow().isoformat(),
            'key_id': secrets.token_urlsafe(16),
            'keys': {}
        }
        
        # JWT signing keys
        if environment == 'production':
            # Use RSA for production (more secure)
            rsa_keys = self.generate_rsa_keypair(2048)
            keyset['keys']['jwt_algorithm'] = 'RS256'
            keyset['keys']['jwt_private_key'] = rsa_keys['private_key']
            keyset['keys']['jwt_public_key'] = rsa_keys['public_key']
        else:
            # Use HMAC for development (simpler)
            keyset['keys']['jwt_algorithm'] = 'HS256'
            keyset['keys']['jwt_secret_key'] = self.generate_symmetric_key(32)
            
        # Session encryption key
        keyset['keys']['session_key'] = self.generate_symmetric_key(32)
        
        # Database encryption key
        keyset['keys']['db_encryption_key'] = self.generate_symmetric_key(32)
        
        # API keys encryption
        keyset['keys']['api_key_encryption'] = self.generate_symmetric_key(32)
        
        # CSRF token key
        keyset['keys']['csrf_key'] = self.generate_symmetric_key(16)
        
        # Password reset token key
        keyset['keys']['password_reset_key'] = self.generate_symmetric_key(32)
        
        # Email verification key
        keyset['keys']['email_verification_key'] = self.generate_symmetric_key(32)
        
        # File upload security
        keyset['keys']['file_upload_key'] = self.generate_symmetric_key(32)
        
        return keyset
        
    def save_keyset(self, keyset: Dict[str, any], filename: Optional[str] = None) -> Path:
        """Save keyset to file with secure permissions"""
        if filename is None:
            filename = f"keyset_{keyset['environment']}_{keyset['key_id']}.json"
            
        filepath = self.key_store_path / filename
        
        # Save with restricted permissions (owner read/write only)
        with open(filepath, 'w') as f:
            json.dump(keyset, f, indent=2)
            
        # Set secure file permissions
        os.chmod(filepath, 0o600)
        
        return filepath
        
    def load_keyset(self, filepath: Path) -> Dict[str, any]:
        """Load keyset from file"""
        with open(filepath, 'r') as f:
            return json.load(f)
            
    def rotate_keys(self, current_keyset_path: Path, keep_old: bool = True) -> Dict[str, Path]:
        """Rotate keys by generating new ones and optionally keeping old ones"""
        # Load current keyset
        current_keyset = self.load_keyset(current_keyset_path)
        environment = current_keyset['environment']
        
        # Generate new keyset
        new_keyset = self.generate_key_set(environment)
        
        # Save new keyset
        new_keyset_path = self.save_keyset(new_keyset)
        
        result = {'new_keyset': new_keyset_path}
        
        if keep_old:
            # Archive old keyset
            archive_name = f"archived_{current_keyset['key_id']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            archive_path = self.key_store_path / 'archive' / archive_name
            archive_path.parent.mkdir(exist_ok=True)
            
            # Copy old keyset to archive
            import shutil
            shutil.copy2(current_keyset_path, archive_path)
            result['archived_keyset'] = archive_path
            
        return result
        
    def generate_env_file(self, keyset: Dict[str, any], template_path: Optional[Path] = None) -> str:
        """Generate .env file content from keyset"""
        keys = keyset['keys']
        
        env_content = [
            "# JWT Security Configuration",
            f"# Generated on: {keyset['generated_at']}",
            f"# Key ID: {keyset['key_id']}",
            f"# Environment: {keyset['environment']}",
            "",
        ]
        
        # JWT configuration
        env_content.extend([
            "# JWT Configuration",
            f"JWT_ALGORITHM={keys['jwt_algorithm']}",
        ])
        
        if keys['jwt_algorithm'] == 'HS256':
            env_content.append(f"JWT_SECRET_KEY={keys['jwt_secret_key']}")
        else:
            newline = '\\n'
            private_key_escaped = keys['jwt_private_key'].replace('\n', newline)
            public_key_escaped = keys['jwt_public_key'].replace('\n', newline)
            env_content.extend([
                f"JWT_PRIVATE_KEY=\"{private_key_escaped}\"",
                f"JWT_PUBLIC_KEY=\"{public_key_escaped}\"",
            ])
            
        # Other security keys
        env_content.extend([
            "",
            "# Security Keys",
            f"SESSION_SECRET_KEY={keys['session_key']}",
            f"DB_ENCRYPTION_KEY={keys['db_encryption_key']}",
            f"API_KEY_ENCRYPTION={keys['api_key_encryption']}",
            f"CSRF_SECRET_KEY={keys['csrf_key']}",
            f"PASSWORD_RESET_KEY={keys['password_reset_key']}",
            f"EMAIL_VERIFICATION_KEY={keys['email_verification_key']}",
            f"FILE_UPLOAD_KEY={keys['file_upload_key']}",
            "",
            "# Security Settings",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30",
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS=7",
            "SESSION_EXPIRE_HOURS=24",
            "PASSWORD_RESET_EXPIRE_HOURS=1",
            "EMAIL_VERIFICATION_EXPIRE_HOURS=24",
            "",
            "# Production Security Flags",
            "SECURE_COOKIES=true",
            "CSRF_PROTECTION=true",
            "RATE_LIMITING_ENABLED=true",
            "SECURITY_HEADERS_ENABLED=true",
            "",
        ])
        
        return "\n".join(env_content)
        
    def validate_keyset(self, keyset: Dict[str, any]) -> List[str]:
        """Validate keyset for security compliance"""
        issues = []
        
        # Check required fields
        required_fields = ['environment', 'generated_at', 'key_id', 'keys']
        for field in required_fields:
            if field not in keyset:
                issues.append(f"Missing required field: {field}")
                
        if 'keys' not in keyset:
            return issues
            
        keys = keyset['keys']
        
        # Validate JWT configuration
        if 'jwt_algorithm' not in keys:
            issues.append("Missing JWT algorithm specification")
        elif keys['jwt_algorithm'] not in ['HS256', 'RS256']:
            issues.append(f"Unsupported JWT algorithm: {keys['jwt_algorithm']}")
            
        # Check key presence based on algorithm
        if keys.get('jwt_algorithm') == 'HS256':
            if 'jwt_secret_key' not in keys:
                issues.append("Missing JWT secret key for HS256")
            elif len(keys['jwt_secret_key']) < 32:
                issues.append("JWT secret key too short (minimum 32 characters)")
        elif keys.get('jwt_algorithm') == 'RS256':
            if 'jwt_private_key' not in keys:
                issues.append("Missing JWT private key for RS256")
            if 'jwt_public_key' not in keys:
                issues.append("Missing JWT public key for RS256")
                
        # Check other required keys
        required_keys = [
            'session_key', 'db_encryption_key', 'api_key_encryption',
            'csrf_key', 'password_reset_key', 'email_verification_key'
        ]
        
        for key_name in required_keys:
            if key_name not in keys:
                issues.append(f"Missing security key: {key_name}")
                
        return issues
        
    def list_keysets(self) -> List[Dict[str, any]]:
        """List all keysets in the key store"""
        keysets = []
        
        for filepath in self.key_store_path.glob("keyset_*.json"):
            try:
                keyset = self.load_keyset(filepath)
                keyset['filepath'] = str(filepath)
                keysets.append(keyset)
            except Exception as e:
                print(f"Error loading keyset {filepath}: {e}")
                
        return sorted(keysets, key=lambda x: x.get('generated_at', ''))


def main():
    parser = argparse.ArgumentParser(description="JWT Key Management System")
    parser.add_argument(
        'action',
        choices=['generate', 'rotate', 'validate', 'list', 'env'],
        help='Action to perform'
    )
    parser.add_argument(
        '--environment',
        default='development',
        choices=['development', 'staging', 'production'],
        help='Environment for key generation'
    )
    parser.add_argument(
        '--keyset-file',
        type=Path,
        help='Path to keyset file'
    )
    parser.add_argument(
        '--output-file',
        type=Path,
        help='Output file path'
    )
    parser.add_argument(
        '--key-store',
        default='config/keys',
        help='Key store directory'
    )
    
    args = parser.parse_args()
    
    manager = JWTKeyManager(args.key_store)
    
    if args.action == 'generate':
        print(f"Generating keyset for {args.environment} environment...")
        keyset = manager.generate_key_set(args.environment)
        
        # Validate the generated keyset
        issues = manager.validate_keyset(keyset)
        if issues:
            print("⚠️  Validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
            
        # Save keyset
        filepath = manager.save_keyset(keyset)
        print(f"✅ Keyset generated and saved to: {filepath}")
        
        # Generate .env content
        env_content = manager.generate_env_file(keyset)
        env_filepath = filepath.parent / f".env.{args.environment}"
        
        with open(env_filepath, 'w') as f:
            f.write(env_content)
        os.chmod(env_filepath, 0o600)
        
        print(f"✅ Environment file generated: {env_filepath}")
        print(f"🔑 Key ID: {keyset['key_id']}")
        
    elif args.action == 'rotate':
        if not args.keyset_file:
            print("❌ --keyset-file required for rotation")
            return 1
            
        if not args.keyset_file.exists():
            print(f"❌ Keyset file not found: {args.keyset_file}")
            return 1
            
        print("Rotating keys...")
        result = manager.rotate_keys(args.keyset_file)
        
        print(f"✅ New keyset generated: {result['new_keyset']}")
        if 'archived_keyset' in result:
            print(f"📦 Old keyset archived: {result['archived_keyset']}")
            
    elif args.action == 'validate':
        if not args.keyset_file:
            print("❌ --keyset-file required for validation")
            return 1
            
        if not args.keyset_file.exists():
            print(f"❌ Keyset file not found: {args.keyset_file}")
            return 1
            
        keyset = manager.load_keyset(args.keyset_file)
        issues = manager.validate_keyset(keyset)
        
        if not issues:
            print("✅ Keyset validation passed")
            return 0
        else:
            print("❌ Keyset validation failed:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
            
    elif args.action == 'list':
        keysets = manager.list_keysets()
        
        if not keysets:
            print("No keysets found")
            return 0
            
        print(f"Found {len(keysets)} keysets:")
        print()
        
        for keyset in keysets:
            print(f"🔑 Key ID: {keyset['key_id']}")
            print(f"   Environment: {keyset['environment']}")
            print(f"   Generated: {keyset['generated_at']}")
            print(f"   Algorithm: {keyset['keys'].get('jwt_algorithm', 'Unknown')}")
            print(f"   File: {keyset['filepath']}")
            print()
            
    elif args.action == 'env':
        if not args.keyset_file:
            print("❌ --keyset-file required for env generation")
            return 1
            
        if not args.keyset_file.exists():
            print(f"❌ Keyset file not found: {args.keyset_file}")
            return 1
            
        keyset = manager.load_keyset(args.keyset_file)
        env_content = manager.generate_env_file(keyset)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(env_content)
            os.chmod(args.output_file, 0o600)
            print(f"✅ Environment file generated: {args.output_file}")
        else:
            print(env_content)
            
    return 0


if __name__ == "__main__":
    exit(main())