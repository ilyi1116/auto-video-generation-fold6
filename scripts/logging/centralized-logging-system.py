#!/usr/bin/env python3
"""
Centralized Logging System
集中式日誌管理系統

Features:
- Multi-level structured logging
- Log aggregation from all microservices
- Real-time log streaming and analysis
- Log correlation and tracing
- Performance-optimized log processing
- Intelligent log filtering and alerting
- ARM64/M4 Max optimizations
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
import gzip
import threading
from queue import Queue, Empty
from collections import defaultdict, deque
import redis
import yaml
from enum import Enum
import traceback
import inspect
import psutil
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEventType(Enum):
    """Log event types"""
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    DATABASE_QUERY = "database_query"
    CACHE_OPERATION = "cache_operation"
    SERVICE_COMMUNICATION = "service_communication"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"
    SECURITY_EVENT = "security_event"
    BUSINESS_EVENT = "business_event"


@dataclass
class LogEntry:
    """Structured log entry"""
    id: str
    timestamp: datetime
    level: LogLevel
    service_name: str
    event_type: LogEventType
    message: str
    context: Dict[str, Any]
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[float] = None
    error_details: Optional[Dict] = None
    stack_trace: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class LogAggregation:
    """Log aggregation result"""
    service_name: str
    time_window: str
    start_time: datetime
    end_time: datetime
    total_logs: int
    log_level_counts: Dict[str, int]
    event_type_counts: Dict[str, int]
    error_count: int
    avg_response_time: Optional[float]
    unique_users: int
    unique_sessions: int


@dataclass
class LogAlert:
    """Log-based alert"""
    id: str
    timestamp: datetime
    severity: str
    alert_type: str
    service_name: str
    description: str
    conditions: Dict[str, Any]
    affected_logs: List[str]
    correlation_ids: List[str]


class LogProcessor:
    """High-performance log processor"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.processing_queue = Queue(maxsize=10000)
        self.batch_queue = Queue(maxsize=1000)
        self.redis_client = None
        self.processing_threads = []
        self.batch_size = config.get('batch_size', 100)
        self.batch_timeout = config.get('batch_timeout', 5)  # seconds
        self.is_running = False
        
        # Performance metrics
        self.metrics = {
            'logs_processed': 0,
            'logs_dropped': 0,
            'processing_errors': 0,
            'avg_processing_time': 0.0,
            'batch_count': 0
        }
        
        # ARM64/M4 optimizations
        self.m4_optimizations = config.get('m4_optimizations', {})
        if self.m4_optimizations.get('enabled', False):
            self._setup_m4_optimizations()
    
    def _setup_m4_optimizations(self):
        """Setup M4 Max specific optimizations"""
        try:
            # Use efficiency cores for log processing
            cpu_affinity = self.m4_optimizations.get('cpu_affinity', [4, 5, 6, 7])
            current_process = psutil.Process()
            current_process.cpu_affinity(cpu_affinity)
            logger.info(f"Set CPU affinity to E-cores: {cpu_affinity}")
            
            # Optimize batch sizes for unified memory architecture
            unified_memory = self.m4_optimizations.get('unified_memory_optimization', {})
            if unified_memory.get('enabled', False):
                self.batch_size = min(self.batch_size, unified_memory.get('max_batch_size', 50))
                logger.info(f"Optimized batch size for unified memory: {self.batch_size}")
                
        except Exception as e:
            logger.warning(f"Failed to apply M4 optimizations: {e}")
    
    async def initialize(self):
        """Initialize log processor"""
        try:
            # Initialize Redis connection
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 2),
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test Redis connection
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.ping
            )
            
            logger.info("Log processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize log processor: {e}")
            raise
    
    def start_processing(self):
        """Start log processing threads"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start processing threads
        num_threads = self.config.get('processing_threads', 4)
        for i in range(num_threads):
            thread = threading.Thread(
                target=self._processing_worker,
                name=f"LogProcessor-{i}",
                daemon=True
            )
            thread.start()
            self.processing_threads.append(thread)
        
        # Start batch processing thread
        batch_thread = threading.Thread(
            target=self._batch_processor,
            name="LogBatchProcessor",
            daemon=True
        )
        batch_thread.start()
        self.processing_threads.append(batch_thread)
        
        logger.info(f"Started {len(self.processing_threads)} log processing threads")
    
    def stop_processing(self):
        """Stop log processing"""
        self.is_running = False
        
        # Wait for threads to finish
        for thread in self.processing_threads:
            thread.join(timeout=5)
        
        logger.info("Log processing stopped")
    
    def add_log(self, log_entry: LogEntry) -> bool:
        """Add log entry for processing"""
        try:
            self.processing_queue.put_nowait(log_entry)
            return True
        except:
            self.metrics['logs_dropped'] += 1
            return False
    
    def _processing_worker(self):
        """Log processing worker thread"""
        while self.is_running:
            try:
                # Get log entry with timeout
                try:
                    log_entry = self.processing_queue.get(timeout=1)
                except Empty:
                    continue
                
                start_time = time.time()
                
                # Process log entry
                processed_entry = self._process_log_entry(log_entry)
                
                # Add to batch queue
                try:
                    self.batch_queue.put_nowait(processed_entry)
                except:
                    self.metrics['logs_dropped'] += 1
                
                # Update metrics
                processing_time = (time.time() - start_time) * 1000
                self.metrics['logs_processed'] += 1
                self.metrics['avg_processing_time'] = (
                    (self.metrics['avg_processing_time'] * (self.metrics['logs_processed'] - 1) + processing_time) /
                    self.metrics['logs_processed']
                )
                
                self.processing_queue.task_done()
                
            except Exception as e:
                self.metrics['processing_errors'] += 1
                logger.error(f"Error in log processing worker: {e}")
    
    def _process_log_entry(self, log_entry: LogEntry) -> Dict:
        """Process individual log entry"""
        try:
            # Convert to dictionary
            processed = asdict(log_entry)
            
            # Add processing metadata
            processed['processed_at'] = datetime.now().isoformat()
            processed['processor_id'] = socket.gethostname()
            
            # Convert timestamp to ISO format
            if isinstance(processed['timestamp'], datetime):
                processed['timestamp'] = processed['timestamp'].isoformat()
            
            # Extract additional context from error details
            if log_entry.error_details:
                processed['error_category'] = self._categorize_error(log_entry.error_details)
            
            # Add performance context
            if log_entry.duration_ms is not None:
                processed['performance_bucket'] = self._categorize_performance(log_entry.duration_ms)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing log entry: {e}")
            return asdict(log_entry)
    
    def _categorize_error(self, error_details: Dict) -> str:
        """Categorize error based on details"""
        error_type = error_details.get('type', '').lower()
        
        if 'timeout' in error_type or 'connectiontimeout' in error_type:
            return 'timeout'
        elif 'connection' in error_type:
            return 'connection'
        elif 'authentication' in error_type or 'authorization' in error_type:
            return 'auth'
        elif 'validation' in error_type:
            return 'validation'
        elif 'database' in error_type or 'sql' in error_type:
            return 'database'
        else:
            return 'unknown'
    
    def _categorize_performance(self, duration_ms: float) -> str:
        """Categorize performance based on duration"""
        if duration_ms < 100:
            return 'fast'
        elif duration_ms < 500:
            return 'normal'
        elif duration_ms < 1000:
            return 'slow'
        else:
            return 'very_slow'
    
    def _batch_processor(self):
        """Batch processor for efficient storage"""
        batch = []
        last_flush = time.time()
        
        while self.is_running:
            try:
                # Get log entries for batch
                try:
                    entry = self.batch_queue.get(timeout=1)
                    batch.append(entry)
                    
                    # Check if batch is ready
                    if (len(batch) >= self.batch_size or 
                        time.time() - last_flush >= self.batch_timeout):
                        
                        if batch:
                            self._flush_batch(batch)
                            batch = []
                            last_flush = time.time()
                            self.metrics['batch_count'] += 1
                    
                except Empty:
                    # Timeout - flush if we have entries
                    if batch and time.time() - last_flush >= self.batch_timeout:
                        self._flush_batch(batch)
                        batch = []
                        last_flush = time.time()
                        self.metrics['batch_count'] += 1
                
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
        
        # Flush remaining entries
        if batch:
            self._flush_batch(batch)
    
    def _flush_batch(self, batch: List[Dict]):
        """Flush batch to storage"""
        try:
            if not self.redis_client:
                return
            
            # Prepare batch for storage
            timestamp = datetime.now().isoformat()
            
            # Store in Redis streams for real-time processing
            for entry in batch:
                stream_key = f"logs:{entry['service_name']}:{entry['level']}"
                self.redis_client.xadd(stream_key, entry, maxlen=10000)
            
            # Store batch summary for analytics
            batch_summary = {
                'timestamp': timestamp,
                'batch_size': len(batch),
                'services': list(set(entry['service_name'] for entry in batch)),
                'log_levels': list(set(entry['level'] for entry in batch)),
                'error_count': len([e for e in batch if e['level'] in ['error', 'critical']])
            }
            
            self.redis_client.lpush('log_batches', json.dumps(batch_summary))
            self.redis_client.ltrim('log_batches', 0, 1000)  # Keep last 1000 batches
            
        except Exception as e:
            logger.error(f"Error flushing log batch: {e}")
    
    def get_metrics(self) -> Dict:
        """Get processing metrics"""
        return {
            **self.metrics,
            'queue_size': self.processing_queue.qsize(),
            'batch_queue_size': self.batch_queue.qsize(),
            'is_running': self.is_running
        }


class LogAnalyzer:
    """Advanced log analysis and correlation"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.alert_rules = []
        
    def add_alert_rule(self, rule: Dict):
        """Add log alert rule"""
        self.alert_rules.append(rule)
    
    async def analyze_logs(self, time_window_minutes: int = 5) -> List[LogAlert]:
        """Analyze logs for patterns and alerts"""
        alerts = []
        
        try:
            # Get recent logs from all streams
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            
            # Check each alert rule
            for rule in self.alert_rules:
                rule_alerts = await self._check_alert_rule(rule, cutoff_time)
                alerts.extend(rule_alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return []
    
    async def _check_alert_rule(self, rule: Dict, cutoff_time: datetime) -> List[LogAlert]:
        """Check specific alert rule"""
        alerts = []
        
        try:
            rule_type = rule.get('type')
            
            if rule_type == 'error_rate':
                alerts.extend(await self._check_error_rate_rule(rule, cutoff_time))
            elif rule_type == 'response_time':
                alerts.extend(await self._check_response_time_rule(rule, cutoff_time))
            elif rule_type == 'log_volume':
                alerts.extend(await self._check_log_volume_rule(rule, cutoff_time))
            elif rule_type == 'correlation':
                alerts.extend(await self._check_correlation_rule(rule, cutoff_time))
            
        except Exception as e:
            logger.error(f"Error checking alert rule {rule.get('name')}: {e}")
        
        return alerts
    
    async def _check_error_rate_rule(self, rule: Dict, cutoff_time: datetime) -> List[LogAlert]:
        """Check error rate alert rule"""
        try:
            service_name = rule.get('service_name', '*')
            threshold = rule.get('threshold', 0.1)  # 10% error rate
            
            # Get error and total log counts
            error_streams = await self._get_matching_streams(f"logs:{service_name}:error")
            total_streams = await self._get_matching_streams(f"logs:{service_name}:*")
            
            error_count = 0
            total_count = 0
            
            for stream in error_streams:
                error_count += await self._count_recent_entries(stream, cutoff_time)
            
            for stream in total_streams:
                total_count += await self._count_recent_entries(stream, cutoff_time)
            
            if total_count > 0:
                error_rate = error_count / total_count
                
                if error_rate > threshold:
                    alert = LogAlert(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        severity='warning' if error_rate < threshold * 2 else 'critical',
                        alert_type='error_rate',
                        service_name=service_name,
                        description=f"High error rate detected: {error_rate:.2%} (threshold: {threshold:.2%})",
                        conditions={'error_rate': error_rate, 'threshold': threshold},
                        affected_logs=[],
                        correlation_ids=[]
                    )
                    return [alert]
            
        except Exception as e:
            logger.error(f"Error checking error rate rule: {e}")
        
        return []
    
    async def _check_response_time_rule(self, rule: Dict, cutoff_time: datetime) -> List[LogAlert]:
        """Check response time alert rule"""
        # Implementation for response time analysis
        return []
    
    async def _check_log_volume_rule(self, rule: Dict, cutoff_time: datetime) -> List[LogAlert]:
        """Check log volume alert rule"""
        # Implementation for log volume analysis
        return []
    
    async def _check_correlation_rule(self, rule: Dict, cutoff_time: datetime) -> List[LogAlert]:
        """Check correlation alert rule"""
        # Implementation for log correlation analysis
        return []
    
    async def _get_matching_streams(self, pattern: str) -> List[str]:
        """Get streams matching pattern"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.redis_client.keys(pattern)
            )
        except:
            return []
    
    async def _count_recent_entries(self, stream: str, cutoff_time: datetime) -> int:
        """Count recent entries in stream"""
        try:
            # Convert cutoff time to Redis stream timestamp
            cutoff_timestamp = int(cutoff_time.timestamp() * 1000)
            
            entries = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.redis_client.xrange(stream, min=cutoff_timestamp)
            )
            
            return len(entries)
            
        except:
            return 0


class CentralizedLoggingSystem:
    """Main centralized logging system"""
    
    def __init__(self, config_path: str = "config/logging-config.yaml"):
        self.config = self._load_config(config_path)
        self.log_processor = LogProcessor(self.config)
        self.log_analyzer = None
        self.service_loggers: Dict[str, logging.Logger] = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load logging configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Default logging configuration"""
        return {
            'processing_threads': 4,
            'batch_size': 100,
            'batch_timeout': 5,
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 2
            },
            'm4_optimizations': {
                'enabled': True,
                'cpu_affinity': [4, 5, 6, 7],
                'unified_memory_optimization': {
                    'enabled': True,
                    'max_batch_size': 50
                }
            },
            'services': [
                'api-gateway',
                'auth-service', 
                'ai-service',
                'video-service',
                'storage-service'
            ],
            'alert_rules': [
                {
                    'name': 'High Error Rate',
                    'type': 'error_rate',
                    'service_name': '*',
                    'threshold': 0.1,
                    'severity': 'warning'
                }
            ]
        }
    
    async def initialize(self):
        """Initialize centralized logging system"""
        try:
            await self.log_processor.initialize()
            
            # Initialize log analyzer
            self.log_analyzer = LogAnalyzer(self.log_processor.redis_client)
            
            # Add alert rules
            for rule in self.config.get('alert_rules', []):
                self.log_analyzer.add_alert_rule(rule)
            
            # Start processing
            self.log_processor.start_processing()
            
            logger.info("Centralized logging system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize centralized logging system: {e}")
            raise
    
    def get_service_logger(self, service_name: str) -> 'ServiceLogger':
        """Get logger for specific service"""
        if service_name not in self.service_loggers:
            service_logger = ServiceLogger(service_name, self)
            self.service_loggers[service_name] = service_logger
        
        return self.service_loggers[service_name]
    
    def log(self, service_name: str, level: LogLevel, event_type: LogEventType, 
            message: str, context: Dict[str, Any] = None, **kwargs) -> bool:
        """Log entry through centralized system"""
        try:
            log_entry = LogEntry(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                level=level,
                service_name=service_name,
                event_type=event_type,
                message=message,
                context=context or {},
                **kwargs
            )
            
            return self.log_processor.add_log(log_entry)
            
        except Exception as e:
            logger.error(f"Error creating log entry: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict:
        """Get logging system performance metrics"""
        processor_metrics = self.log_processor.get_metrics()
        
        # Add system metrics
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'active_threads': threading.active_count()
        }
        
        return {
            'processor_metrics': processor_metrics,
            'system_metrics': system_metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    async def analyze_and_alert(self):
        """Run log analysis and alerting"""
        if not self.log_analyzer:
            return []
        
        alerts = await self.log_analyzer.analyze_logs()
        
        # Process alerts
        for alert in alerts:
            logger.warning(f"LOG ALERT [{alert.severity.upper()}] {alert.service_name}: {alert.description}")
        
        return alerts
    
    def shutdown(self):
        """Shutdown logging system"""
        self.log_processor.stop_processing()
        logger.info("Centralized logging system shutdown")


class ServiceLogger:
    """Service-specific logger wrapper"""
    
    def __init__(self, service_name: str, logging_system: CentralizedLoggingSystem):
        self.service_name = service_name
        self.logging_system = logging_system
        self.correlation_id = None
        self.session_id = None
        self.user_id = None
    
    def set_context(self, correlation_id: str = None, session_id: str = None, user_id: str = None):
        """Set logging context"""
        if correlation_id:
            self.correlation_id = correlation_id
        if session_id:
            self.session_id = session_id
        if user_id:
            self.user_id = user_id
    
    def info(self, message: str, event_type: LogEventType = LogEventType.BUSINESS_EVENT, 
             context: Dict = None, **kwargs):
        """Log info message"""
        return self.logging_system.log(
            self.service_name, LogLevel.INFO, event_type, message, context,
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            user_id=self.user_id,
            **kwargs
        )
    
    def warning(self, message: str, event_type: LogEventType = LogEventType.ERROR_OCCURRED,
                context: Dict = None, **kwargs):
        """Log warning message"""
        return self.logging_system.log(
            self.service_name, LogLevel.WARNING, event_type, message, context,
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            user_id=self.user_id,
            **kwargs
        )
    
    def error(self, message: str, error: Exception = None, 
              event_type: LogEventType = LogEventType.ERROR_OCCURRED,
              context: Dict = None, **kwargs):
        """Log error message"""
        error_details = None
        stack_trace = None
        
        if error:
            error_details = {
                'type': type(error).__name__,
                'message': str(error),
                'args': error.args
            }
            stack_trace = traceback.format_exc()
        
        return self.logging_system.log(
            self.service_name, LogLevel.ERROR, event_type, message, context,
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            user_id=self.user_id,
            error_details=error_details,
            stack_trace=stack_trace,
            **kwargs
        )
    
    def api_request(self, method: str, endpoint: str, duration_ms: float = None,
                    status_code: int = None, context: Dict = None):
        """Log API request"""
        message = f"{method} {endpoint}"
        if status_code:
            message += f" -> {status_code}"
        if duration_ms:
            message += f" ({duration_ms:.1f}ms)"
        
        return self.logging_system.log(
            self.service_name, LogLevel.INFO, LogEventType.API_REQUEST, message,
            context or {}, 
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            user_id=self.user_id,
            duration_ms=duration_ms,
            metadata={'method': method, 'endpoint': endpoint, 'status_code': status_code}
        )
    
    def performance_metric(self, metric_name: str, value: float, unit: str = None,
                          context: Dict = None):
        """Log performance metric"""
        message = f"Performance metric: {metric_name} = {value}"
        if unit:
            message += f" {unit}"
        
        return self.logging_system.log(
            self.service_name, LogLevel.INFO, LogEventType.PERFORMANCE_METRIC, message,
            context or {},
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            user_id=self.user_id,
            metadata={'metric_name': metric_name, 'value': value, 'unit': unit}
        )


async def main():
    """Main function for testing"""
    logging_system = CentralizedLoggingSystem()
    
    try:
        await logging_system.initialize()
        
        # Get service logger
        api_logger = logging_system.get_service_logger('api-gateway')
        api_logger.set_context(correlation_id='test-123', user_id='user-456')
        
        # Test logging
        api_logger.info("API Gateway started", LogEventType.BUSINESS_EVENT)
        api_logger.api_request('GET', '/api/v1/health', duration_ms=45.2, status_code=200)
        api_logger.performance_metric('response_time', 45.2, 'ms')
        
        # Simulate error
        try:
            raise ValueError("Test error")
        except Exception as e:
            api_logger.error("Test error occurred", error=e)
        
        # Wait and get metrics
        await asyncio.sleep(2)
        metrics = await logging_system.get_performance_metrics()
        print(json.dumps(metrics, indent=2, default=str))
        
        # Run analysis
        alerts = await logging_system.analyze_and_alert()
        print(f"Generated {len(alerts)} alerts")
        
    finally:
        logging_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())