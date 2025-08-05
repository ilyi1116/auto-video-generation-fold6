#!/usr/bin/env python3
"""
Centralized Logging Integration Example
集中式日誌系統整合範例

This script demonstrates how to integrate the centralized logging system
into existing microservices and applications.
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, Any
from centralized_logging_system import (
    CentralizedLoggingSystem, 
    LogLevel, 
    LogEventType
)

class APIGatewayExample:
    """Example API Gateway integration"""
    
    def __init__(self, logging_system: CentralizedLoggingSystem):
        self.logger = logging_system.get_service_logger('api-gateway')        
        
    async def handle_request(self, method: str, endpoint: str, user_id: str = None):
        """Example request handler with logging"""
        # Set context for this request
        correlation_id = str(uuid.uuid4())
        session_id = f"session-{int(time.time())}"
        self.logger.set_context(
            correlation_id=correlation_id,
            session_id=session_id,
            user_id=user_id
        )
        
        start_time = time.time()
        
        try:
            # Log request start
            self.logger.info(
                f"Incoming request: {method} {endpoint}",
                LogEventType.API_REQUEST,
                context={
                    'method': method,
                    'endpoint': endpoint,
                    'user_agent': 'example-client/1.0',
                    'ip_address': '192.168.1.100'
                }
            )
            
            # Simulate processing
            await asyncio.sleep(0.1)  # Simulate work
            
            # Simulate some business logic with metrics
            processing_time = (time.time() - start_time) * 1000
            self.logger.performance_metric('request_processing_time', processing_time, 'ms')
            
            # Log successful response
            status_code = 200
            self.logger.api_request(
                method, endpoint,
                duration_ms=processing_time,
                status_code=status_code,
                context={'response_size': 1024}
            )
            
            return {"status": "success", "data": "example response"}
            
        except Exception as e:
            # Log error with full context
            self.logger.error(
                f"Request failed: {method} {endpoint}",
                error=e,
                context={
                    'method': method,
                    'endpoint': endpoint,
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
            )
            
            # Also log as API response for metrics
            error_status = 500
            self.logger.api_request(
                method, endpoint,
                duration_ms=(time.time() - start_time) * 1000,
                status_code=error_status
            )
            
            raise


class AuthServiceExample:
    """Example Auth Service integration"""
    
    def __init__(self, logging_system: CentralizedLoggingSystem):
        self.logger = logging_system.get_service_logger('auth-service')
        
    async def authenticate_user(self, username: str, ip_address: str):
        """Example authentication with security logging"""
        correlation_id = str(uuid.uuid4())
        self.logger.set_context(correlation_id=correlation_id)
        
        start_time = time.time()
        
        try:
            # Log authentication attempt
            self.logger.info(
                f"Authentication attempt for user: {username}",
                LogEventType.SECURITY_EVENT,
                context={
                    'username': username,
                    'ip_address': ip_address,
                    'auth_method': 'password'
                }
            )
            
            # Simulate authentication logic
            await asyncio.sleep(0.05)
            
            # Simulate random success/failure
            import random
            success = random.random() > 0.1  # 90% success rate
            
            duration_ms = (time.time() - start_time) * 1000
            
            if success:
                user_id = f"user-{hash(username) % 10000}"
                self.logger.set_context(user_id=user_id)
                
                self.logger.info(
                    f"Authentication successful for user: {username}",
                    LogEventType.SECURITY_EVENT,
                    context={
                        'username': username,
                        'user_id': user_id,
                        'ip_address': ip_address,
                        'auth_duration_ms': duration_ms
                    }
                )
                
                # Performance metric
                self.logger.performance_metric('auth_duration', duration_ms, 'ms')
                
                return {"success": True, "user_id": user_id, "token": "example-jwt-token"}
                
            else:
                # Log failed authentication
                self.logger.warning(
                    f"Authentication failed for user: {username}",
                    LogEventType.SECURITY_EVENT,
                    context={
                        'username': username,
                        'ip_address': ip_address,
                        'failure_reason': 'invalid_credentials',
                        'auth_duration_ms': duration_ms
                    }
                )
                
                return {"success": False, "error": "Invalid credentials"}
                
        except Exception as e:
            self.logger.error(
                f"Authentication error for user: {username}",
                error=e,
                event_type=LogEventType.SECURITY_EVENT,
                context={
                    'username': username,
                    'ip_address': ip_address
                }
            )
            raise


class AIServiceExample:
    """Example AI Service integration"""
    
    def __init__(self, logging_system: CentralizedLoggingSystem):
        self.logger = logging_system.get_service_logger('ai-service')
        
    async def generate_video(self, user_id: str, video_request: Dict[str, Any]):
        """Example video generation with detailed logging"""
        correlation_id = str(uuid.uuid4())
        self.logger.set_context(
            correlation_id=correlation_id,
            user_id=user_id
        )
        
        start_time = time.time()
        
        try:
            # Log generation start
            self.logger.info(
                "Video generation started",
                LogEventType.BUSINESS_EVENT,
                context={
                    'video_type': video_request.get('type', 'unknown'),
                    'duration_seconds': video_request.get('duration', 0),
                    'quality': video_request.get('quality', 'standard'),
                    'input_files': len(video_request.get('input_files', []))
                }
            )
            
            # Simulate processing stages with progress logging
            stages = ['preprocessing', 'ai_inference', 'postprocessing', 'encoding']
            
            for i, stage in enumerate(stages):
                stage_start = time.time()
                
                # Simulate stage processing
                await asyncio.sleep(0.2)
                
                stage_duration = (time.time() - stage_start) * 1000
                progress = ((i + 1) / len(stages)) * 100
                
                self.logger.info(
                    f"Video generation stage completed: {stage}",
                    LogEventType.BUSINESS_EVENT,
                    context={
                        'stage': stage,
                        'stage_duration_ms': stage_duration,
                        'overall_progress': progress,
                        'gpu_utilization': 85.5,  # Example metric
                        'memory_usage_gb': 4.2
                    }
                )
                
                # Log performance metrics for each stage
                self.logger.performance_metric(f'{stage}_duration', stage_duration, 'ms')
            
            total_duration = (time.time() - start_time) * 1000
            
            # Log successful completion
            self.logger.info(
                "Video generation completed successfully",
                LogEventType.BUSINESS_EVENT,
                context={
                    'total_duration_ms': total_duration,
                    'output_file_size_mb': 125.7,
                    'output_resolution': '1920x1080',
                    'compression_ratio': 0.85
                }
            )
            
            # Performance metrics
            self.logger.performance_metric('video_generation_time', total_duration, 'ms')
            self.logger.performance_metric('video_size', 125.7, 'mb')
            
            return {
                "success": True,
                "video_id": f"video-{uuid.uuid4()}",
                "duration_ms": total_duration
            }
            
        except Exception as e:
            self.logger.error(
                "Video generation failed",
                error=e,
                event_type=LogEventType.BUSINESS_EVENT,
                context={
                    'total_duration_ms': (time.time() - start_time) * 1000,
                    'video_request': video_request
                }
            )
            raise


class DatabaseExample:
    """Example database operation logging"""
    
    def __init__(self, logging_system: CentralizedLoggingSystem):
        self.logger = logging_system.get_service_logger('data-service')
        
    async def execute_query(self, query: str, params: Dict = None, user_id: str = None):
        """Example database query with logging"""
        correlation_id = str(uuid.uuid4())
        self.logger.set_context(
            correlation_id=correlation_id,
            user_id=user_id
        )
        
        start_time = time.time()
        
        try:
            # Log query start
            self.logger.info(
                "Database query started",
                LogEventType.DATABASE_QUERY,
                context={
                    'query_type': query.split()[0].upper(),  # SELECT, INSERT, etc.
                    'table_name': self._extract_table_name(query),
                    'has_parameters': params is not None,
                    'parameter_count': len(params) if params else 0
                }
            )
            
            # Simulate query execution
            await asyncio.sleep(0.03)  # Simulate DB time
            
            execution_time = (time.time() - start_time) * 1000
            
            # Simulate query results
            rows_affected = 42
            
            # Log successful query
            self.logger.info(
                "Database query completed",
                LogEventType.DATABASE_QUERY,
                context={
                    'execution_time_ms': execution_time,
                    'rows_affected': rows_affected,
                    'query_plan_cost': 1.23,  # Example cost
                    'cache_hit': True
                }
            )
            
            # Performance metrics
            self.logger.performance_metric('db_query_time', execution_time, 'ms')
            
            # Alert if query is slow
            if execution_time > 100:
                self.logger.warning(
                    "Slow database query detected",
                    LogEventType.PERFORMANCE_METRIC,
                    context={
                        'execution_time_ms': execution_time,
                        'query_type': query.split()[0].upper(),
                        'table_name': self._extract_table_name(query)
                    }
                )
            
            return {"rows_affected": rows_affected, "execution_time": execution_time}
            
        except Exception as e:
            self.logger.error(
                "Database query failed",
                error=e,
                event_type=LogEventType.DATABASE_QUERY,
                context={
                    'execution_time_ms': (time.time() - start_time) * 1000,
                    'query': query[:200],  # First 200 chars of query
                    'parameters': str(params)[:500] if params else None
                }
            )
            raise
    
    def _extract_table_name(self, query: str) -> str:
        """Extract table name from SQL query"""
        try:
            tokens = query.lower().split()
            if 'from' in tokens:
                from_index = tokens.index('from')
                if from_index + 1 < len(tokens):
                    return tokens[from_index + 1].strip('`;')
            elif 'into' in tokens:
                into_index = tokens.index('into')
                if into_index + 1 < len(tokens):
                    return tokens[into_index + 1].strip('`;')
            elif 'update' in tokens:
                update_index = tokens.index('update')
                if update_index + 1 < len(tokens):
                    return tokens[update_index + 1].strip('`;')
        except:
            pass
        return 'unknown'


async def run_example_scenario():
    """Run a complete example scenario"""
    print("🚀 Starting Centralized Logging System Example")
    
    # Initialize logging system
    logging_system = CentralizedLoggingSystem()
    await logging_system.initialize()
    
    try:
        # Create service examples
        api_gateway = APIGatewayExample(logging_system)
        auth_service = AuthServiceExample(logging_system)
        ai_service = AIServiceExample(logging_system)
        database = DatabaseExample(logging_system)
        
        print("📊 Running example operations...")
        
        # Simulate typical request flow
        for i in range(5):
            user_id = f"user-{i + 1}"
            
            # API Gateway receives request
            try:
                await api_gateway.handle_request('POST', '/api/v1/videos/generate', user_id)
            except:
                pass
            
            # Authentication
            auth_result = await auth_service.authenticate_user(f'user{i + 1}', '192.168.1.100')
            
            if auth_result['success']:
                # Database operations
                await database.execute_query(
                    'SELECT * FROM videos WHERE user_id = ?',
                    {'user_id': user_id},
                    user_id
                )
                
                # AI processing
                video_request = {
                    'type': 'talking_avatar',
                    'duration': 30,
                    'quality': 'high',
                    'input_files': ['audio.mp3', 'avatar.png']
                }
                
                try:
                    await ai_service.generate_video(user_id, video_request)
                except:
                    pass
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        print("⏱️  Waiting for log processing...")
        await asyncio.sleep(3)
        
        # Get performance metrics
        metrics = await logging_system.get_performance_metrics()
        print("\n📈 Logging System Performance Metrics:")
        print(f"  • Logs Processed: {metrics['processor_metrics']['logs_processed']}")
        print(f"  • Processing Errors: {metrics['processor_metrics']['processing_errors']}")
        print(f"  • Average Processing Time: {metrics['processor_metrics']['avg_processing_time']:.2f}ms")
        print(f"  • Batch Count: {metrics['processor_metrics']['batch_count']}")
        print(f"  • Queue Size: {metrics['processor_metrics']['queue_size']}")
        
        # Run log analysis
        print("\n🔍 Running Log Analysis...")
        alerts = await logging_system.analyze_and_alert()
        print(f"  • Generated {len(alerts)} alerts")
        
        for alert in alerts:
            print(f"    - {alert.severity.upper()}: {alert.description}")
        
        print("\n✅ Example scenario completed successfully!")
        
    finally:
        logging_system.shutdown()


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Centralized Logging Integration Example')
    parser.add_argument('--scenario', choices=['full', 'basic'], default='full',
                       help='Example scenario to run')
    
    args = parser.parse_args()
    
    if args.scenario == 'full':
        await run_example_scenario()
    else:
        # Basic example
        logging_system = CentralizedLoggingSystem()
        await logging_system.initialize()
        
        try:
            # Simple logging example
            logger = logging_system.get_service_logger('example-service')
            logger.set_context(user_id='demo-user')
            
            logger.info("This is an info message", LogEventType.BUSINESS_EVENT)
            logger.warning("This is a warning message")
            
            try:
                raise ValueError("Example error")
            except Exception as e:
                logger.error("An error occurred", error=e)
            
            await asyncio.sleep(1)
            print("Basic logging example completed")
            
        finally:
            logging_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())