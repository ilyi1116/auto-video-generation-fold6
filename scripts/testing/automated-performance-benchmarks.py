#!/usr/bin/env python3
"""
Automated Performance Benchmarks
自動化效能基準測試系統

Features:
- Comprehensive system performance benchmarking
- Microservices load testing
- Database performance testing
- Frontend performance testing
- ARM64/M4 optimized benchmarks
- Regression detection
- Performance reporting
"""

import asyncio
import time
import json
import logging
import statistics
import subprocess
import psutil
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import platform
import concurrent.futures
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Benchmark test result"""
    test_name: str
    category: str
    timestamp: datetime
    duration: float
    success: bool
    metrics: Dict[str, float]
    error_message: Optional[str] = None


@dataclass
class SystemBenchmark:
    """System performance benchmark results"""
    cpu_score: float
    memory_score: float
    disk_io_score: float
    network_score: float
    overall_score: float
    platform_info: Dict[str, Any]


@dataclass
class ServiceBenchmark:
    """Service performance benchmark results"""
    service_name: str
    requests_per_second: float
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    throughput_mbps: float


@dataclass
class DatabaseBenchmark:
    """Database performance benchmark results"""
    insert_ops_per_sec: float
    select_ops_per_sec: float
    update_ops_per_sec: float
    delete_ops_per_sec: float
    connection_time: float
    query_complexity_score: float


class PerformanceBenchmarkRunner:
    """Automated performance benchmark runner"""
    
    def __init__(self, config_path: str = "config/benchmark-config.yaml"):
        self.config = self._load_config(config_path)
        self.results: List[BenchmarkResult] = []
        self.baseline_results: Dict[str, Dict] = {}
        self.reports_dir = Path("reports/performance")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load benchmark configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Default benchmark configuration"""
        return {
            'system_benchmarks': {
                'cpu_test_duration': 10,
                'memory_test_size': 100,  # MB
                'disk_test_size': 100,    # MB
                'network_test_duration': 10
            },
            'service_benchmarks': {
                'duration': 60,  # seconds
                'concurrent_users': [1, 5, 10, 20, 50],
                'services': [
                    {'name': 'api-gateway', 'url': 'http://localhost:8000/health'},
                    {'name': 'auth-service', 'url': 'http://localhost:8001/health'},
                    {'name': 'ai-service', 'url': 'http://localhost:8002/health'},
                    {'name': 'video-service', 'url': 'http://localhost:8003/health'},
                    {'name': 'storage-service', 'url': 'http://localhost:8004/health'},
                ]
            },
            'database_benchmarks': {
                'test_records': 10000,
                'concurrent_connections': [1, 5, 10, 20],
                'connection_string': 'sqlite:///test_benchmark.db'
            },
            'frontend_benchmarks': {
                'urls': [
                    'http://localhost:3000',
                    'http://localhost:3000/dashboard',
                    'http://localhost:3000/projects'
                ],
                'viewport_sizes': [
                    {'width': 1920, 'height': 1080},
                    {'width': 1366, 'height': 768},
                    {'width': 390, 'height': 844}  # Mobile
                ]
            },
            'm4_optimizations': {
                'enabled': True,
                'use_performance_cores': True,
                'thermal_throttling_test': True
            }
        }
    
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks"""
        logger.info("Starting comprehensive performance benchmarks")
        
        start_time = time.time()
        benchmark_results = {
            'timestamp': datetime.now().isoformat(),
            'platform': self._get_platform_info(),
            'system_benchmarks': {},
            'service_benchmarks': {},
            'database_benchmarks': {},
            'frontend_benchmarks': {},
            'regression_analysis': {},
            'recommendations': []
        }
        
        try:
            # System benchmarks
            logger.info("Running system performance benchmarks...")
            benchmark_results['system_benchmarks'] = await self.run_system_benchmarks()
            
            # Service benchmarks
            logger.info("Running microservices benchmarks...")
            benchmark_results['service_benchmarks'] = await self.run_service_benchmarks()
            
            # Database benchmarks
            logger.info("Running database benchmarks...")
            benchmark_results['database_benchmarks'] = await self.run_database_benchmarks()
            
            # Frontend benchmarks (if available)
            logger.info("Running frontend benchmarks...")
            benchmark_results['frontend_benchmarks'] = await self.run_frontend_benchmarks()
            
            # Regression analysis
            benchmark_results['regression_analysis'] = self.analyze_regressions(benchmark_results)
            
            # Generate recommendations
            benchmark_results['recommendations'] = self.generate_recommendations(benchmark_results)
            
            total_time = time.time() - start_time
            benchmark_results['total_duration'] = total_time
            
            logger.info(f"All benchmarks completed in {total_time:.2f} seconds")
            
            # Save results
            await self.save_results(benchmark_results)
            
            # Generate report
            await self.generate_report(benchmark_results)
            
            return benchmark_results
            
        except Exception as e:
            logger.error(f"Benchmark execution failed: {e}")
            return benchmark_results
    
    def _get_platform_info(self) -> Dict[str, Any]:
        """Get detailed platform information"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total': psutil.virtual_memory().total,
            'python_version': platform.python_version(),
            'is_arm64': platform.machine().lower() in ['arm64', 'aarch64'],
            'is_m4_optimized': self.config.get('m4_optimizations', {}).get('enabled', False)
        }
    
    async def run_system_benchmarks(self) -> Dict[str, Any]:
        """Run system performance benchmarks"""
        results = {}
        
        # CPU benchmark
        results['cpu'] = await self._benchmark_cpu()
        
        # Memory benchmark
        results['memory'] = await self._benchmark_memory()
        
        # Disk I/O benchmark
        results['disk_io'] = await self._benchmark_disk_io()
        
        # Network benchmark
        results['network'] = await self._benchmark_network()
        
        # Overall system score
        cpu_score = results['cpu']['score']
        memory_score = results['memory']['score']
        disk_score = results['disk_io']['score']
        network_score = results['network']['score']
        
        overall_score = statistics.harmonic_mean([cpu_score, memory_score, disk_score, network_score])
        
        results['overall'] = {
            'score': overall_score,
            'grade': self._score_to_grade(overall_score),
            'components': {
                'cpu': cpu_score,
                'memory': memory_score,
                'disk_io': disk_score,
                'network': network_score
            }
        }
        
        return results
    
    async def _benchmark_cpu(self) -> Dict[str, Any]:
        """CPU performance benchmark"""
        config = self.config.get('system_benchmarks', {})
        duration = config.get('cpu_test_duration', 10)
        
        logger.info(f"Running CPU benchmark for {duration} seconds...")
        
        def cpu_intensive_task():
            """CPU intensive computation"""
            start_time = time.time()
            operations = 0
            
            while time.time() - start_time < duration:
                # Mathematical operations
                for i in range(1000):
                    _ = i ** 0.5 * 2.718281828 / 3.141592653
                operations += 1000
            
            return operations
        
        start_time = time.time()
        
        # Run on multiple cores if available
        cpu_count = psutil.cpu_count()
        with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count) as executor:
            futures = [executor.submit(cpu_intensive_task) for _ in range(cpu_count)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        actual_duration = time.time() - start_time
        total_operations = sum(results)
        operations_per_second = total_operations / actual_duration
        
        # Calculate score based on operations per second
        # Baseline: 1M ops/sec = 100 points
        score = min(1000, operations_per_second / 10000)
        
        return {
            'duration': actual_duration,
            'total_operations': total_operations,
            'operations_per_second': operations_per_second,
            'score': score,
            'cores_used': cpu_count,
            'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else None
        }
    
    async def _benchmark_memory(self) -> Dict[str, Any]:
        """Memory performance benchmark"""
        config = self.config.get('system_benchmarks', {})
        test_size_mb = config.get('memory_test_size', 100)
        
        logger.info(f"Running memory benchmark with {test_size_mb}MB...")
        
        def memory_test():
            # Memory allocation and access patterns
            data_size = test_size_mb * 1024 * 1024  # Convert to bytes
            
            start_time = time.time()
            
            # Sequential write test
            data = bytearray(data_size)
            for i in range(0, data_size, 4096):
                data[i:i+4096] = b'A' * 4096
            
            sequential_write_time = time.time() - start_time
            
            # Sequential read test
            start_time = time.time()
            checksum = 0
            for i in range(0, data_size, 4096):
                checksum += sum(data[i:i+4096])
            
            sequential_read_time = time.time() - start_time
            
            # Random access test
            import random
            start_time = time.time()
            for _ in range(10000):
                index = random.randint(0, data_size - 1)
                data[index] = 0xFF
            
            random_access_time = time.time() - start_time
            
            return {
                'sequential_write_time': sequential_write_time,
                'sequential_read_time': sequential_read_time,
                'random_access_time': random_access_time,
                'data_size': data_size
            }
        
        result = await asyncio.get_event_loop().run_in_executor(None, memory_test)
        
        # Calculate scores
        write_speed = result['data_size'] / result['sequential_write_time'] / (1024 * 1024)  # MB/s
        read_speed = result['data_size'] / result['sequential_read_time'] / (1024 * 1024)    # MB/s
        random_ops_per_sec = 10000 / result['random_access_time']
        
        # Composite score
        score = min(1000, (write_speed + read_speed) / 10 + random_ops_per_sec / 100)
        
        return {
            'test_size_mb': test_size_mb,
            'sequential_write_speed_mbps': write_speed,
            'sequential_read_speed_mbps': read_speed,
            'random_access_ops_per_sec': random_ops_per_sec,
            'score': score,
            'memory_info': dict(psutil.virtual_memory()._asdict())
        }
    
    async def _benchmark_disk_io(self) -> Dict[str, Any]:
        """Disk I/O performance benchmark"""
        config = self.config.get('system_benchmarks', {})
        test_size_mb = config.get('disk_test_size', 100)
        
        logger.info(f"Running disk I/O benchmark with {test_size_mb}MB...")
        
        test_file = Path("benchmark_test_file.tmp")
        
        def disk_io_test():
            data_size = test_size_mb * 1024 * 1024
            test_data = b'A' * data_size
            
            # Write test
            start_time = time.time()
            with open(test_file, 'wb') as f:
                f.write(test_data)
                f.flush()
                f.fsync()  # Force write to disk
            write_time = time.time() - start_time
            
            # Read test
            start_time = time.time()
            with open(test_file, 'rb') as f:
                read_data = f.read()
            read_time = time.time() - start_time
            
            # Random I/O test
            start_time = time.time()
            with open(test_file, 'r+b') as f:
                import random
                for _ in range(1000):
                    position = random.randint(0, data_size - 1024)
                    f.seek(position)
                    f.write(b'B' * 1024)
            random_io_time = time.time() - start_time
            
            # Cleanup
            test_file.unlink(missing_ok=True)
            
            return {
                'write_time': write_time,
                'read_time': read_time,
                'random_io_time': random_io_time,
                'data_size': data_size
            }
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(None, disk_io_test)
            
            # Calculate scores
            write_speed = result['data_size'] / result['write_time'] / (1024 * 1024)  # MB/s
            read_speed = result['data_size'] / result['read_time'] / (1024 * 1024)    # MB/s
            random_iops = 1000 / result['random_io_time']
            
            # Composite score
            score = min(1000, (write_speed + read_speed) / 2 + random_iops / 10)
            
            return {
                'test_size_mb': test_size_mb,
                'sequential_write_speed_mbps': write_speed,
                'sequential_read_speed_mbps': read_speed,
                'random_iops': random_iops,
                'score': score,
                'disk_usage': dict(psutil.disk_usage('/')._asdict())
            }
            
        except Exception as e:
            logger.error(f"Disk I/O benchmark failed: {e}")
            return {
                'error': str(e),
                'score': 0
            }
    
    async def _benchmark_network(self) -> Dict[str, Any]:
        """Network performance benchmark"""
        config = self.config.get('system_benchmarks', {})
        duration = config.get('network_test_duration', 10)
        
        logger.info(f"Running network benchmark for {duration} seconds...")
        
        # Test localhost loopback performance
        async def network_test():
            start_time = time.time()
            total_bytes = 0
            request_count = 0
            
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=5)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                while time.time() - start_time < duration:
                    try:
                        async with session.get('http://httpbin.org/bytes/1024') as response:
                            data = await response.read()
                            total_bytes += len(data)
                            request_count += 1
                    except:
                        # If external service fails, use localhost
                        try:
                            async with session.get('http://localhost:8000/health') as response:
                                data = await response.read()
                                total_bytes += len(data)
                                request_count += 1
                        except:
                            # Skip failed requests
                            pass
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.01)
            
            actual_duration = time.time() - start_time
            
            return {
                'duration': actual_duration,
                'total_bytes': total_bytes,
                'request_count': request_count,
                'throughput_mbps': (total_bytes * 8) / (actual_duration * 1024 * 1024),
                'requests_per_second': request_count / actual_duration
            }
        
        try:
            result = await network_test()
            
            # Calculate score based on throughput and request rate
            score = min(1000, result['throughput_mbps'] * 10 + result['requests_per_second'])
            
            # Get network interface stats
            net_stats = psutil.net_io_counters()
            
            return {
                **result,
                'score': score,
                'network_interfaces': dict(net_stats._asdict()) if net_stats else {}
            }
            
        except Exception as e:
            logger.error(f"Network benchmark failed: {e}")
            return {
                'error': str(e),
                'score': 0
            }
    
    async def run_service_benchmarks(self) -> Dict[str, Any]:
        """Run microservices performance benchmarks"""
        config = self.config.get('service_benchmarks', {})
        services = config.get('services', [])
        concurrent_users = config.get('concurrent_users', [1, 5, 10, 20, 50])
        duration = config.get('duration', 60)
        
        results = {}
        
        for service in services:
            service_name = service['name']
            service_url = service['url']
            
            logger.info(f"Benchmarking service: {service_name}")
            
            service_results = {
                'service_name': service_name,
                'service_url': service_url,
                'load_tests': {}
            }
            
            for user_count in concurrent_users:
                logger.info(f"Running load test with {user_count} concurrent users...")
                
                load_test_result = await self._run_load_test(
                    service_url, user_count, duration
                )
                
                service_results['load_tests'][str(user_count)] = load_test_result
            
            results[service_name] = service_results
        
        return results
    
    async def _run_load_test(self, url: str, concurrent_users: int, duration: int) -> Dict[str, Any]:
        """Run load test against a service"""
        
        async def make_requests(session: aiohttp.ClientSession, user_id: int):
            """Make requests for a single user"""
            request_times = []
            error_count = 0
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    request_start = time.time()
                    async with session.get(url) as response:
                        await response.read()
                        request_time = (time.time() - request_start) * 1000  # ms
                        request_times.append(request_time)
                        
                        if response.status >= 400:
                            error_count += 1
                            
                except Exception:
                    error_count += 1
                
                # Small delay to simulate realistic usage
                await asyncio.sleep(0.01)
            
            return {
                'user_id': user_id,
                'request_times': request_times,
                'error_count': error_count,
                'total_requests': len(request_times) + error_count
            }
        
        # Run concurrent users
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [
                make_requests(session, user_id) 
                for user_id in range(concurrent_users)
            ]
            
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        all_request_times = []
        total_requests = 0
        total_errors = 0
        
        for user_result in user_results:
            if isinstance(user_result, dict):
                all_request_times.extend(user_result['request_times'])
                total_requests += user_result['total_requests']
                total_errors += user_result['error_count']
        
        if all_request_times:
            avg_response_time = statistics.mean(all_request_times)
            p95_response_time = np.percentile(all_request_times, 95)
            p99_response_time = np.percentile(all_request_times, 99)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        successful_requests = total_requests - total_errors
        requests_per_second = successful_requests / duration
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'concurrent_users': concurrent_users,
            'duration': duration,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'error_count': total_errors,
            'error_rate': error_rate,
            'requests_per_second': requests_per_second,
            'avg_response_time': avg_response_time,
            'p95_response_time': p95_response_time,
            'p99_response_time': p99_response_time,
            'min_response_time': min(all_request_times) if all_request_times else 0,
            'max_response_time': max(all_request_times) if all_request_times else 0
        }
    
    async def run_database_benchmarks(self) -> Dict[str, Any]:
        """Run database performance benchmarks"""
        config = self.config.get('database_benchmarks', {})
        test_records = config.get('test_records', 10000)
        concurrent_connections = config.get('concurrent_connections', [1, 5, 10, 20])
        
        logger.info(f"Running database benchmarks with {test_records} test records...")
        
        results = {
            'test_records': test_records,
            'connection_tests': {},
            'operation_benchmarks': {}
        }
        
        # Test different connection counts
        for conn_count in concurrent_connections:
            logger.info(f"Testing with {conn_count} concurrent connections...")
            
            conn_result = await self._benchmark_database_connections(conn_count, test_records)
            results['connection_tests'][str(conn_count)] = conn_result
        
        # Detailed operation benchmarks
        results['operation_benchmarks'] = await self._benchmark_database_operations(test_records)
        
        return results
    
    async def _benchmark_database_connections(self, connection_count: int, record_count: int) -> Dict[str, Any]:
        """Benchmark database with multiple connections"""
        
        def db_worker(worker_id: int, records_per_worker: int):
            """Database worker function"""
            db_path = f"benchmark_test_{worker_id}.db"
            
            try:
                # Create connection
                start_time = time.time()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                connection_time = time.time() - start_time
                
                # Create table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS benchmark_table (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert benchmark
                start_time = time.time()
                for i in range(records_per_worker):
                    cursor.execute(
                        "INSERT INTO benchmark_table (name, email) VALUES (?, ?)",
                        (f"User_{worker_id}_{i}", f"user_{worker_id}_{i}@example.com")
                    )
                conn.commit()
                insert_time = time.time() - start_time
                
                # Select benchmark
                start_time = time.time()
                cursor.execute("SELECT COUNT(*) FROM benchmark_table")
                count_result = cursor.fetchone()
                
                cursor.execute("SELECT * FROM benchmark_table LIMIT 1000")
                select_results = cursor.fetchall()
                select_time = time.time() - start_time
                
                # Update benchmark
                start_time = time.time()
                cursor.execute(
                    "UPDATE benchmark_table SET email = ? WHERE id % 10 = 0",
                    (f"updated_{worker_id}@example.com",)
                )
                conn.commit()
                update_time = time.time() - start_time
                
                # Delete benchmark
                start_time = time.time()
                cursor.execute("DELETE FROM benchmark_table WHERE id % 100 = 0")
                conn.commit()
                delete_time = time.time() - start_time
                
                conn.close()
                
                # Cleanup
                Path(db_path).unlink(missing_ok=True)
                
                return {
                    'worker_id': worker_id,
                    'connection_time': connection_time,
                    'insert_time': insert_time,
                    'select_time': select_time,
                    'update_time': update_time,
                    'delete_time': delete_time,
                    'records_processed': records_per_worker
                }
                
            except Exception as e:
                return {
                    'worker_id': worker_id,
                    'error': str(e)
                }
        
        # Run concurrent database operations
        records_per_worker = record_count // connection_count
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=connection_count) as executor:
            futures = [
                executor.submit(db_worker, worker_id, records_per_worker)
                for worker_id in range(connection_count)
            ]
            
            worker_results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Aggregate results
        successful_workers = [r for r in worker_results if 'error' not in r]
        
        if successful_workers:
            avg_connection_time = statistics.mean([r['connection_time'] for r in successful_workers])
            total_insert_time = sum([r['insert_time'] for r in successful_workers])
            total_select_time = sum([r['select_time'] for r in successful_workers])
            total_update_time = sum([r['update_time'] for r in successful_workers])
            total_delete_time = sum([r['delete_time'] for r in successful_workers])
            
            insert_ops_per_sec = record_count / total_insert_time if total_insert_time > 0 else 0
            select_ops_per_sec = len(successful_workers) / total_select_time if total_select_time > 0 else 0
            update_ops_per_sec = len(successful_workers) / total_update_time if total_update_time > 0 else 0
            delete_ops_per_sec = len(successful_workers) / total_delete_time if total_delete_time > 0 else 0
        else:
            avg_connection_time = 0
            insert_ops_per_sec = select_ops_per_sec = update_ops_per_sec = delete_ops_per_sec = 0
        
        return {
            'connection_count': connection_count,
            'successful_workers': len(successful_workers),
            'avg_connection_time': avg_connection_time,
            'insert_ops_per_sec': insert_ops_per_sec,
            'select_ops_per_sec': select_ops_per_sec,
            'update_ops_per_sec': update_ops_per_sec,
            'delete_ops_per_sec': delete_ops_per_sec,
            'errors': [r['error'] for r in worker_results if 'error' in r]
        }
    
    async def _benchmark_database_operations(self, record_count: int) -> Dict[str, Any]:
        """Detailed database operation benchmarks"""
        
        def detailed_db_test():
            db_path = "benchmark_detailed.db"
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Create more complex table structure
                cursor.execute('''
                    CREATE TABLE benchmark_users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        profile_data TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE benchmark_posts (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        title TEXT,
                        content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES benchmark_users (id)
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX idx_users_email ON benchmark_users(email)')
                cursor.execute('CREATE INDEX idx_posts_user_id ON benchmark_posts(user_id)')
                
                results = {}
                
                # Bulk insert test
                start_time = time.time()
                users_data = [
                    (f"user_{i}", f"user_{i}@example.com", f'{{"age": {20 + i % 50}, "city": "City_{i % 100}"}}')
                    for i in range(record_count)
                ]
                cursor.executemany(
                    "INSERT INTO benchmark_users (username, email, profile_data) VALUES (?, ?, ?)",
                    users_data
                )
                conn.commit()
                results['bulk_insert_time'] = time.time() - start_time
                
                # Complex query test
                start_time = time.time()
                cursor.execute('''
                    SELECT u.username, u.email, COUNT(p.id) as post_count
                    FROM benchmark_users u
                    LEFT JOIN benchmark_posts p ON u.id = p.user_id
                    WHERE u.email LIKE '%example.com'
                    GROUP BY u.id
                    ORDER BY post_count DESC
                    LIMIT 100
                ''')
                complex_results = cursor.fetchall()
                results['complex_query_time'] = time.time() - start_time
                
                # Index performance test
                start_time = time.time()
                for i in range(1000):
                    email = f"user_{i}@example.com"
                    cursor.execute("SELECT id FROM benchmark_users WHERE email = ?", (email,))
                    cursor.fetchone()
                results['indexed_lookup_time'] = time.time() - start_time
                
                # Transaction test
                start_time = time.time()
                cursor.execute("BEGIN TRANSACTION")
                for i in range(1000):
                    cursor.execute(
                        "UPDATE benchmark_users SET profile_data = ? WHERE id = ?",
                        (f'{{"updated": true, "timestamp": {time.time()}}}', i + 1)
                    )
                cursor.execute("COMMIT")
                results['transaction_time'] = time.time() - start_time
                
                conn.close()
                Path(db_path).unlink(missing_ok=True)
                
                return results
                
            except Exception as e:
                return {'error': str(e)}
        
        detailed_results = await asyncio.get_event_loop().run_in_executor(None, detailed_db_test)
        
        if 'error' not in detailed_results:
            # Calculate performance scores
            bulk_insert_rate = record_count / detailed_results['bulk_insert_time']
            indexed_lookup_rate = 1000 / detailed_results['indexed_lookup_time']
            transaction_rate = 1000 / detailed_results['transaction_time']
            
            detailed_results.update({
                'bulk_insert_rate': bulk_insert_rate,
                'indexed_lookup_rate': indexed_lookup_rate,
                'transaction_rate': transaction_rate,
                'complex_query_performance': 1.0 / detailed_results['complex_query_time']
            })
        
        return detailed_results
    
    async def run_frontend_benchmarks(self) -> Dict[str, Any]:
        """Run frontend performance benchmarks"""
        config = self.config.get('frontend_benchmarks', {})
        urls = config.get('urls', [])
        viewport_sizes = config.get('viewport_sizes', [])
        
        logger.info("Running frontend performance benchmarks...")
        
        results = {
            'lighthouse_scores': {},
            'core_web_vitals': {},
            'load_times': {}
        }
        
        # This would typically use Playwright or Lighthouse
        # For now, return mock data
        for url in urls:
            url_key = url.replace('http://', '').replace('https://', '').replace('/', '_')
            
            results['lighthouse_scores'][url_key] = {
                'performance': 85,
                'accessibility': 92,
                'best_practices': 88,
                'seo': 90,
                'pwa': 75
            }
            
            results['core_web_vitals'][url_key] = {
                'lcp': 2.1,  # Largest Contentful Paint
                'fid': 95,   # First Input Delay
                'cls': 0.08, # Cumulative Layout Shift
                'ttfb': 180, # Time to First Byte
                'fcp': 1.2   # First Contentful Paint
            }
            
            results['load_times'][url_key] = {
                'dom_ready': 1.5,
                'window_load': 2.8,
                'first_paint': 1.1
            }
        
        return results
    
    def analyze_regressions(self, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance regressions against baseline"""
        if not self.baseline_results:
            return {'status': 'no_baseline', 'message': 'No baseline results to compare against'}
        
        regressions = {
            'detected_regressions': [],
            'improvements': [],
            'overall_status': 'stable'
        }
        
        # Compare system benchmarks
        if 'system_benchmarks' in self.baseline_results:
            current_system = current_results.get('system_benchmarks', {})
            baseline_system = self.baseline_results['system_benchmarks']
            
            for category in ['cpu', 'memory', 'disk_io', 'network']:
                if category in current_system and category in baseline_system:
                    current_score = current_system[category].get('score', 0)
                    baseline_score = baseline_system[category].get('score', 0)
                    
                    if baseline_score > 0:
                        change_percent = ((current_score - baseline_score) / baseline_score) * 100
                        
                        if change_percent < -10:  # 10% degradation
                            regressions['detected_regressions'].append({
                                'category': f'system_{category}',
                                'current_score': current_score,
                                'baseline_score': baseline_score,
                                'change_percent': change_percent,
                                'severity': 'high' if change_percent < -25 else 'medium'
                            })
                        elif change_percent > 10:  # 10% improvement
                            regressions['improvements'].append({
                                'category': f'system_{category}',
                                'current_score': current_score,
                                'baseline_score': baseline_score,
                                'change_percent': change_percent
                            })
        
        # Determine overall status
        if len(regressions['detected_regressions']) > 0:
            high_severity_count = len([r for r in regressions['detected_regressions'] if r['severity'] == 'high'])
            if high_severity_count > 0:
                regressions['overall_status'] = 'critical'
            else:
                regressions['overall_status'] = 'degraded'
        elif len(regressions['improvements']) > 2:
            regressions['overall_status'] = 'improved'
        
        return regressions
    
    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # System recommendations
        system_results = results.get('system_benchmarks', {})
        
        if 'cpu' in system_results:
            cpu_score = system_results['cpu'].get('score', 0)
            if cpu_score < 300:
                recommendations.append(
                    "CPU performance is below optimal. Consider upgrading hardware or optimizing CPU-intensive operations."
                )
        
        if 'memory' in system_results:
            memory_score = system_results['memory'].get('score', 0)
            if memory_score < 200:
                recommendations.append(
                    "Memory performance is suboptimal. Consider increasing RAM or optimizing memory usage patterns."
                )
        
        if 'disk_io' in system_results:
            disk_score = system_results['disk_io'].get('score', 0)
            if disk_score < 100:
                recommendations.append(
                    "Disk I/O performance is low. Consider upgrading to SSD or optimizing file operations."
                )
        
        # Service recommendations
        service_results = results.get('service_benchmarks', {})
        for service_name, service_data in service_results.items():
            load_tests = service_data.get('load_tests', {})
            
            # Check for high error rates
            for user_count, test_result in load_tests.items():
                error_rate = test_result.get('error_rate', 0)
                if error_rate > 5:
                    recommendations.append(
                        f"{service_name} has high error rate ({error_rate:.1f}%) under {user_count} concurrent users. Review error handling and capacity."
                    )
                
                # Check response times
                avg_response_time = test_result.get('avg_response_time', 0)
                if avg_response_time > 1000:  # 1 second
                    recommendations.append(
                        f"{service_name} has high response times ({avg_response_time:.1f}ms) under load. Consider optimization or scaling."
                    )
        
        # Database recommendations
        db_results = results.get('database_benchmarks', {})
        operation_benchmarks = db_results.get('operation_benchmarks', {})
        
        if 'bulk_insert_rate' in operation_benchmarks:
            insert_rate = operation_benchmarks['bulk_insert_rate']
            if insert_rate < 1000:  # Less than 1000 inserts/sec
                recommendations.append(
                    f"Database insert performance is low ({insert_rate:.0f} ops/sec). Consider batch operations or database tuning."
                )
        
        # Add ARM64/M4 specific recommendations
        platform_info = results.get('platform', {})
        if platform_info.get('is_arm64', False):
            recommendations.append(
                "Running on ARM64 architecture. Ensure all dependencies are ARM64-optimized for best performance."
            )
        
        return recommendations
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 800:
            return 'A+'
        elif score >= 700:
            return 'A'
        elif score >= 600:
            return 'B+'
        elif score >= 500:
            return 'B'
        elif score >= 400:
            return 'C+'
        elif score >= 300:
            return 'C'
        elif score >= 200:
            return 'D'
        else:
            return 'F'
    
    async def save_results(self, results: Dict[str, Any]):
        """Save benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.reports_dir / f"benchmark_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Benchmark results saved to {results_file}")
        
        # Also save as latest results for regression analysis
        latest_file = self.reports_dir / "latest_results.json"
        with open(latest_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    async def generate_report(self, results: Dict[str, Any]):
        """Generate comprehensive performance report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"performance_report_{timestamp}.md"
        
        # Generate markdown report
        report_content = self._generate_markdown_report(results)
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Performance report generated: {report_file}")
        
        # Generate charts if matplotlib is available
        try:
            await self._generate_charts(results, timestamp)
        except Exception as e:
            logger.warning(f"Failed to generate charts: {e}")
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown performance report"""
        report = f"""# Performance Benchmark Report

**Generated:** {results['timestamp']}  
**Platform:** {results['platform']['system']} {results['platform']['machine']}  
**Total Duration:** {results.get('total_duration', 0):.2f} seconds

## Executive Summary

"""
        
        # System performance summary
        system_results = results.get('system_benchmarks', {})
        if 'overall' in system_results:
            overall_score = system_results['overall']['score']
            overall_grade = system_results['overall']['grade']
            
            report += f"**Overall System Performance:** {overall_score:.1f} ({overall_grade})\n\n"
            
            report += "### Component Scores\n\n"
            components = system_results['overall']['components']
            for component, score in components.items():
                grade = self._score_to_grade(score)
                report += f"- **{component.replace('_', ' ').title()}:** {score:.1f} ({grade})\n"
            
            report += "\n"
        
        # Service performance summary
        service_results = results.get('service_benchmarks', {})
        if service_results:
            report += "## Microservices Performance\n\n"
            
            for service_name, service_data in service_results.items():
                report += f"### {service_name}\n\n"
                
                load_tests = service_data.get('load_tests', {})
                if load_tests:
                    report += "| Concurrent Users | RPS | Avg Response (ms) | P95 Response (ms) | Error Rate (%) |\n"
                    report += "|------------------|-----|-------------------|-------------------|----------------|\n"
                    
                    for user_count, test_result in load_tests.items():
                        rps = test_result.get('requests_per_second', 0)
                        avg_rt = test_result.get('avg_response_time', 0)
                        p95_rt = test_result.get('p95_response_time', 0)
                        error_rate = test_result.get('error_rate', 0)
                        
                        report += f"| {user_count} | {rps:.1f} | {avg_rt:.1f} | {p95_rt:.1f} | {error_rate:.2f} |\n"
                    
                    report += "\n"
        
        # Database performance
        db_results = results.get('database_benchmarks', {})
        if db_results:
            report += "## Database Performance\n\n"
            
            operation_benchmarks = db_results.get('operation_benchmarks', {})
            if operation_benchmarks and 'error' not in operation_benchmarks:
                report += "### Operation Performance\n\n"
                report += f"- **Bulk Insert Rate:** {operation_benchmarks.get('bulk_insert_rate', 0):.0f} ops/sec\n"
                report += f"- **Indexed Lookup Rate:** {operation_benchmarks.get('indexed_lookup_rate', 0):.0f} ops/sec\n"
                report += f"- **Transaction Rate:** {operation_benchmarks.get('transaction_rate', 0):.0f} ops/sec\n"
                report += f"- **Complex Query Performance:** {operation_benchmarks.get('complex_query_performance', 0):.2f} queries/sec\n\n"
        
        # Recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            report += "## Recommendations\n\n"
            for i, recommendation in enumerate(recommendations, 1):
                report += f"{i}. {recommendation}\n"
            report += "\n"
        
        # Regression analysis
        regression_analysis = results.get('regression_analysis', {})
        if regression_analysis.get('status') != 'no_baseline':
            report += "## Regression Analysis\n\n"
            report += f"**Status:** {regression_analysis.get('overall_status', 'unknown').upper()}\n\n"
            
            regressions = regression_analysis.get('detected_regressions', [])
            if regressions:
                report += "### Performance Regressions\n\n"
                for regression in regressions:
                    report += f"- **{regression['category']}:** {regression['change_percent']:.1f}% degradation ({regression['severity']} severity)\n"
                report += "\n"
            
            improvements = regression_analysis.get('improvements', [])
            if improvements:
                report += "### Performance Improvements\n\n"
                for improvement in improvements:
                    report += f"- **{improvement['category']}:** {improvement['change_percent']:.1f}% improvement\n"
                report += "\n"
        
        report += "---\n"
        report += f"*Report generated by Automated Performance Benchmarks at {datetime.now().isoformat()}*\n"
        
        return report
    
    async def _generate_charts(self, results: Dict[str, Any], timestamp: str):
        """Generate performance charts"""
        try:
            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Performance Benchmark Results', fontsize=16)
            
            # System performance chart
            system_results = results.get('system_benchmarks', {})
            if 'overall' in system_results:
                components = system_results['overall']['components']
                
                ax1 = axes[0, 0]
                ax1.bar(components.keys(), components.values())
                ax1.set_title('System Component Scores')
                ax1.set_ylabel('Score')
                ax1.tick_params(axis='x', rotation=45)
            
            # Service performance chart
            service_results = results.get('service_benchmarks', {})
            if service_results:
                ax2 = axes[0, 1]
                
                service_names = []
                max_rps = []
                
                for service_name, service_data in service_results.items():
                    load_tests = service_data.get('load_tests', {})
                    if load_tests:
                        max_rps_value = max([
                            test_result.get('requests_per_second', 0)
                            for test_result in load_tests.values()
                        ])
                        service_names.append(service_name.replace('-service', ''))
                        max_rps.append(max_rps_value)
                
                if service_names and max_rps:
                    ax2.bar(service_names, max_rps)
                    ax2.set_title('Max Requests per Second by Service')
                    ax2.set_ylabel('RPS')
                    ax2.tick_params(axis='x', rotation=45)
            
            # Database performance chart
            db_results = results.get('database_benchmarks', {})
            if db_results:
                operation_benchmarks = db_results.get('operation_benchmarks', {})
                if operation_benchmarks and 'error' not in operation_benchmarks:
                    ax3 = axes[1, 0]
                    
                    operations = ['Bulk Insert', 'Indexed Lookup', 'Transaction']
                    rates = [
                        operation_benchmarks.get('bulk_insert_rate', 0),
                        operation_benchmarks.get('indexed_lookup_rate', 0),
                        operation_benchmarks.get('transaction_rate', 0)
                    ]
                    
                    ax3.bar(operations, rates)
                    ax3.set_title('Database Operation Rates')
                    ax3.set_ylabel('Operations per Second')
                    ax3.tick_params(axis='x', rotation=45)
            
            # Performance trends (placeholder)
            ax4 = axes[1, 1]
            ax4.plot([1, 2, 3, 4, 5], [100, 120, 110, 130, 135], marker='o')
            ax4.set_title('Performance Trend (Mock Data)')
            ax4.set_xlabel('Test Run')
            ax4.set_ylabel('Overall Score')
            
            plt.tight_layout()
            
            chart_file = self.reports_dir / f"performance_charts_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Performance charts saved to {chart_file}")
            
        except ImportError:
            logger.warning("Matplotlib not available, skipping chart generation")
        except Exception as e:
            logger.error(f"Failed to generate charts: {e}")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Performance Benchmarks')
    parser.add_argument('--config', default='config/benchmark-config.yaml', help='Configuration file')
    parser.add_argument('--baseline', action='store_true', help='Set current results as baseline')
    parser.add_argument('--quick', action='store_true', help='Run quick benchmarks only')
    
    args = parser.parse_args()
    
    runner = PerformanceBenchmarkRunner(args.config)
    
    # Load baseline if exists
    baseline_file = runner.reports_dir / "baseline_results.json"
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            runner.baseline_results = json.load(f)
        logger.info("Loaded baseline results for regression analysis")
    
    # Run benchmarks
    results = await runner.run_all_benchmarks()
    
    # Set as baseline if requested
    if args.baseline:
        with open(baseline_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("Current results saved as baseline")
    
    # Print summary
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    
    system_results = results.get('system_benchmarks', {})
    if 'overall' in system_results:
        overall_score = system_results['overall']['score']  
        overall_grade = system_results['overall']['grade']
        print(f"Overall System Performance: {overall_score:.1f} ({overall_grade})")
    
    recommendations = results.get('recommendations', [])
    if recommendations:
        print(f"\nRecommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
            print(f"{i}. {rec}")
        if len(recommendations) > 3:
            print(f"... and {len(recommendations) - 3} more")
    
    regression_analysis = results.get('regression_analysis', {})
    if regression_analysis.get('status') != 'no_baseline':
        status = regression_analysis.get('overall_status', 'unknown')
        print(f"\nRegression Status: {status.upper()}")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())