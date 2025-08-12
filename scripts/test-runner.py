#!/usr/bin/env python3
"""
Intelligent Test Runner for Auto Video Generation System
智能測試運行器 - 提供不同級別的測試執行策略
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Intelligent test runner with different strategies"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_dirs = [
            "src/services/*/tests",
            "tests",
        ]
    
    def run_unit_tests(self, parallel: bool = True, coverage: bool = True) -> int:
        """Run only unit tests - fastest execution"""
        print("🧪 Running Unit Tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Test selection
        cmd.extend(["-m", "unit"])
        
        # Parallel execution
        if parallel:
            cmd.extend(["-n", "auto"])
        
        # Coverage
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing:skip-covered",
                "--cov-report=html:htmlcov",
            ])
        
        # Fast mode settings
        cmd.extend([
            "--tb=short",
            "--maxfail=5",  # Stop after 5 failures
            "-q",  # Quiet mode
        ])
        
        return self._run_command(cmd)
    
    def run_smoke_tests(self) -> int:
        """Run critical smoke tests only"""
        print("💨 Running Smoke Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "-m", "smoke",
            "--tb=short",
            "-v",
        ]
        
        return self._run_command(cmd)
    
    def run_integration_tests(self, parallel: bool = True) -> int:
        """Run integration tests"""
        print("🔗 Running Integration Tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Test selection
        cmd.extend(["-m", "integration"])
        
        # Parallel execution (limited for integration tests)
        if parallel:
            cmd.extend(["-n", "2"])  # Limited parallelism for integration
        
        cmd.extend([
            "--tb=short",
            "--maxfail=3",
        ])
        
        return self._run_command(cmd)
    
    def run_full_test_suite(self, parallel: bool = True, coverage: bool = True) -> int:
        """Run complete test suite"""
        print("🚀 Running Full Test Suite...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Parallel execution
        if parallel:
            cmd.extend(["-n", "auto"])
        
        # Coverage
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml",
                "--cov-fail-under=80",
            ])
        
        # Performance monitoring
        cmd.extend([
            "--durations=10",
            "--durations-min=1.0",
        ])
        
        return self._run_command(cmd)
    
    def run_changed_tests(self) -> int:
        """Run tests for changed files only"""
        print("📝 Running Tests for Changed Files...")
        
        # Get changed files
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            changed_files = result.stdout.strip().split('\n')
            
            if not changed_files or changed_files == ['']:
                print("No changed files detected, running smoke tests instead...")
                return self.run_smoke_tests()
            
            # Filter Python files
            py_files = [f for f in changed_files if f.endswith('.py')]
            
            if not py_files:
                print("No Python files changed, running smoke tests...")
                return self.run_smoke_tests()
            
            # Run tests for changed modules
            cmd = [
                "python", "-m", "pytest",
                "--lf",  # Last failed
                "--ff",  # Failed first
                "-n", "auto",
                "--tb=short",
            ]
            
            # Add specific test files if they exist
            for py_file in py_files:
                test_file = self._find_test_file(py_file)
                if test_file:
                    cmd.append(str(test_file))
            
            return self._run_command(cmd)
            
        except subprocess.CalledProcessError:
            print("Git not available, running smoke tests...")
            return self.run_smoke_tests()
    
    def run_performance_tests(self) -> int:
        """Run performance benchmark tests"""
        print("⚡ Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "-m", "performance",
            "--benchmark-only",
            "--benchmark-sort=mean",
            "--benchmark-min-rounds=5",
            "-v",
        ]
        
        return self._run_command(cmd)
    
    def run_security_tests(self) -> int:
        """Run security-related tests"""
        print("🔒 Running Security Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "-m", "security",
            "-v",
            "--tb=short",
        ]
        
        return self._run_command(cmd)
    
    def _find_test_file(self, source_file: str) -> Optional[Path]:
        """Find corresponding test file for a source file"""
        source_path = Path(source_file)
        
        # Try different test file patterns
        possible_patterns = [
            f"test_{source_path.stem}.py",
            f"{source_path.stem}_test.py",
            f"test_{source_path.stem}_*.py",
        ]
        
        # Look in test directories
        for test_dir in ["tests", "src/services/*/tests"]:
            test_dir_path = self.project_root / test_dir
            if "*" in test_dir:
                # Handle glob patterns
                import glob
                for expanded_dir in glob.glob(str(test_dir_path)):
                    expanded_path = Path(expanded_dir)
                    for pattern in possible_patterns:
                        test_files = list(expanded_path.glob(pattern))
                        if test_files:
                            return test_files[0]
            else:
                if test_dir_path.exists():
                    for pattern in possible_patterns:
                        test_files = list(test_dir_path.glob(pattern))
                        if test_files:
                            return test_files[0]
        
        return None
    
    def _run_command(self, cmd: List[str]) -> int:
        """Run command and return exit code"""
        print(f"Executing: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱️  Tests completed in {duration:.2f} seconds")
        
        return result.returncode
    
    def check_test_environment(self) -> bool:
        """Check if test environment is properly set up"""
        print("🔍 Checking test environment...")
        
        # Check if pytest is available
        try:
            subprocess.run(["python", "-m", "pytest", "--version"], 
                         capture_output=True, check=True)
            print("✅ pytest is available")
        except subprocess.CalledProcessError:
            print("❌ pytest is not available")
            return False
        
        # Check if test directories exist
        test_dirs_exist = False
        for test_dir in self.test_dirs:
            if "*" in test_dir:
                import glob
                if glob.glob(str(self.project_root / test_dir)):
                    test_dirs_exist = True
                    break
            else:
                if (self.project_root / test_dir).exists():
                    test_dirs_exist = True
                    break
        
        if test_dirs_exist:
            print("✅ Test directories found")
        else:
            print("❌ No test directories found")
            return False
        
        print("✅ Test environment ready")
        return True


def main():
    parser = argparse.ArgumentParser(description="Intelligent Test Runner")
    parser.add_argument(
        "strategy",
        choices=["unit", "smoke", "integration", "full", "changed", "performance", "security"],
        help="Test execution strategy"
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel test execution"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true", 
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check test environment setup"
    )
    
    args = parser.parse_args()
    
    # Find project root
    current_dir = Path.cwd()
    project_root = current_dir
    
    # Look for pyproject.toml to identify project root
    while project_root.parent != project_root:
        if (project_root / "pyproject.toml").exists():
            break
        project_root = project_root.parent
    else:
        project_root = current_dir
    
    runner = TestRunner(project_root)
    
    if args.check_env:
        if not runner.check_test_environment():
            sys.exit(1)
        return
    
    # Determine strategy
    parallel = not args.no_parallel
    coverage = not args.no_coverage
    
    strategy_map = {
        "unit": lambda: runner.run_unit_tests(parallel, coverage),
        "smoke": runner.run_smoke_tests,
        "integration": lambda: runner.run_integration_tests(parallel),
        "full": lambda: runner.run_full_test_suite(parallel, coverage),
        "changed": runner.run_changed_tests,
        "performance": runner.run_performance_tests,
        "security": runner.run_security_tests,
    }
    
    print(f"🎯 Test Strategy: {args.strategy}")
    print(f"🔧 Parallel: {parallel}, Coverage: {coverage}")
    print("-" * 50)
    
    exit_code = strategy_map[args.strategy]()
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()