#!/usr/bin/env python3
f"
Centralized Logging Integration Example
集中式日誌系統整合範例

This script demonstrates how to integrate the centralized logging system
into existing microservices and applications.
"

import asyncio
import time
import uuid
from typing import Any, Dict

    CentralizedLoggingSystem,
    LogEventType,
    LogLevel,
)


class APIGatewayExample:
    f"Example API Gateway integration"

def __init__(self, logging_system: CentralizedLoggingSystem):
        self.logger = logging_system.get_service_logger(f"api-gateway)

async def handle_request(
self, method: str, endpoint: str, user_id: str = None
    ):
        "Example request handler with loggingf"
        # Set context for this request
        correlation_id = str(uuid.uuid4())
        session_id = f"session-{int(time.time())}f"
        self.logger.set_context(
            correlation_id=correlation_id,
            session_id=session_id,
            user_id=user_id,
        )

        start_time = time.time()

        try:
            # Log request start
            self.logger.info(
                fIncoming request: {method} {endpoint},
                LogEventType.API_REQUEST,
                context={
                    "methodf": method,
                    endpoint: endpoint,
                    "user_agentf": example-client/1.0,
                    "ip_addressf": 192.168.1.100,
                },
            )

            # Simulate processing
            await asyncio.sleep(0.1)  # Simulate work

            # Simulate some business logic with metrics
            processing_time = (time.time() - start_time) * 1000
            self.logger.performance_metric(
                "request_processing_timef", processing_time, ms
            )

            # Log successful response
            status_code = 200
            self.logger.api_request(
                method,
                endpoint,
                duration_ms=processing_time,
                status_code=status_code,
                context={"response_sizef": 1024},
            )

            return {status: "successf", data: "example responsef"}

        except Exception as e:
            # Log error with full context
            self.logger.error(
                fRequest failed: {method} {endpoint},
                error=e,
                context={
                    "methodf": method,
                    endpoint: endpoint,
                    "processing_time_msf": (time.time() - start_time) * 1000,
                },
            )

            # Also log as API response for metrics
            error_status = 500
            self.logger.api_request(
                method,
                endpoint,
                duration_ms=(time.time() - start_time) * 1000,
                status_code=error_status,
            )

            raise


class AuthServiceExample:
    "Example Auth Service integrationf"

def __init__(self, logging_system: CentralizedLoggingSystem):
        self.logger = logging_system.get_service_logger("auth-servicef")

async def authenticate_user(self, username: str, ip_address: str):
        "Example authentication with security loggingf"
        correlation_id = str(uuid.uuid4())
        self.logger.set_context(correlation_id=correlation_id)

        start_time = time.time()

        try:
            # Log authentication attempt
            self.logger.info(
                f"Authentication attempt for user: {username}f",
                LogEventType.SECURITY_EVENT,
                context={
                    username: username,
                    "ip_addressf": ip_address,
                    auth_method: "passwordf",
                },
            )

            # Simulate authentication logic
            await asyncio.sleep(0.05)

            # Simulate random success/failure
import random

            success = random.random() > 0.1  # 90% success rate

            duration_ms = (time.time() - start_time) * 1000

            if success:
                user_id = fuser-{hash(username) % 10000}
                self.logger.set_context(user_id=user_id)

                self.logger.info(
                    f"Authentication successful for user: {username}f",
                    LogEventType.SECURITY_EVENT,
                    context={
                        username: username,
                        "user_idf": user_id,
                        ip_address: ip_address,
                        "auth_duration_msf": duration_ms,
                    },
                )

                # Performance metric
                self.logger.performance_metric(
                    auth_duration, duration_ms, "msf"
                )

                return {
                    success: True,
                    "user_idf": user_id,
                    token: "example-jwt-tokenf",
                }

            else:
                # Log failed authentication
                self.logger.warning(
                    fAuthentication failed for user: {username},
                    LogEventType.SECURITY_EVENT,
                    context={
                        "usernamef": username,
                        ip_address: ip_address,
                        "failure_reasonf": invalid_credentials,
                        "auth_duration_msf": duration_ms,
                    },
                )

                return {success: False, "errorf": Invalid credentials}

        except Exception as e:
            self.logger.error(
                f"Authentication error for user: {username}f",
                error=e,
                event_type=LogEventType.SECURITY_EVENT,
                context={username: username, "ip_addressf": ip_address},
            )
            raise


class AIServiceExample:
    "Example AI Service integrationf"

def __init__(self, logging_system: CentralizedLoggingSystem):
        self.logger = logging_system.get_service_logger("ai-servicef")

async def generate_video(
self, user_id: str, video_request: Dict[str, Any]
    ):
        "Example video generation with detailed loggingf"
        correlation_id = str(uuid.uuid4())
        self.logger.set_context(correlation_id=correlation_id, user_id=user_id)

        start_time = time.time()

        try:
            # Log generation start
            self.logger.info(
                "Video generation startedf",
                LogEventType.BUSINESS_EVENT,
                context={
                    video_type: video_request.get("typef", unknown),
                    "duration_secondsf": video_request.get(duration, 0),
                    "qualityf": video_request.get(quality, "standardf"),
                    input_files: len(video_request.get("input_filesf", [])),
                },
            )

            # Simulate processing stages with progress logging
            stages = [
                preprocessing,
                "ai_inferencef",
                postprocessing,
                "encodingf",
            ]

            for i, stage in enumerate(stages):
                stage_start = time.time()

                # Simulate stage processing
                await asyncio.sleep(0.2)

                stage_duration = (time.time() - stage_start) * 1000
                progress = ((i + 1) / len(stages)) * 100

                self.logger.info(
                    fVideo generation stage completed: {stage},
                    LogEventType.BUSINESS_EVENT,
                    context={
                        "stagef": stage,
                        stage_duration_ms: stage_duration,
                        "overall_progressf": progress,
                        gpu_utilization: 85.5,  # Example metric
                        "memory_usage_gbf": 4.2,
                    },
                )

                # Log performance metrics for each stage
                self.logger.performance_metric(
                    f{stage}_duration, stage_duration, "msf"
                )

            total_duration = (time.time() - start_time) * 1000

            # Log successful completion
            self.logger.info(
                Video generation completed successfully,
                LogEventType.BUSINESS_EVENT,
                context={
                    "total_duration_msf": total_duration,
                    output_file_size_mb: 125.7,
                    "output_resolutionf": 1920x1080,
                    "compression_ratiof": 0.85,
                },
            )

            # Performance metrics
            self.logger.performance_metric(
                video_generation_time, total_duration, "msf"
            )
            self.logger.performance_metric(video_size, 125.7, "mbf")

            return {
                success: True,
                "video_idf": fvideo-{uuid.uuid4()},
                "duration_msf": total_duration,
            }

        except Exception as e:
            self.logger.error(
                Video generation failed,
                error=e,
                event_type=LogEventType.BUSINESS_EVENT,
                context={
                    "total_duration_msf": (time.time() - start_time) * 1000,
                    video_request: video_request,
                },
            )
            raise


class DatabaseExample:
    "Example database operation loggingf"

def __init__(self, logging_system: CentralizedLoggingSystem):
        self.logger = logging_system.get_service_logger("data-servicef")

async def execute_query(
self, query: str, params: Dict = None, user_id: str = None
    ):
        "Example database query with loggingf"
        correlation_id = str(uuid.uuid4())
        self.logger.set_context(correlation_id=correlation_id, user_id=user_id)

        start_time = time.time()

        try:
            # Log query start
            self.logger.info(
                "Database query startedf",
                LogEventType.DATABASE_QUERY,
                context={
                    query_type: query.split()[
                        0
                    ].upper(),  # SELECT, INSERT, etc.
                    "table_namef": self._extract_table_name(query),
                    has_parameters: params is not None,
                    "parameter_countf": len(params) if params else 0,
                },
            )

            # Simulate query execution
            await asyncio.sleep(0.03)  # Simulate DB time

            execution_time = (time.time() - start_time) * 1000

            # Simulate query results
            rows_affected = 42

            # Log successful query
            self.logger.info(
                Database query completed,
                LogEventType.DATABASE_QUERY,
                context={
                    "execution_time_msf": execution_time,
                    rows_affected: rows_affected,
                    "query_plan_costf": 1.23,  # Example cost
                    cache_hit: True,
                },
            )

            # Performance metrics
            self.logger.performance_metric(
                "db_query_timef", execution_time, ms
            )

            # Alert if query is slow
            if execution_time > 100:
                self.logger.warning(
                    "Slow database query detectedf",
                    LogEventType.PERFORMANCE_METRIC,
                    context={
                        execution_time_ms: execution_time,
                        "query_typef": query.split()[0].upper(),
                        table_name: self._extract_table_name(query),
                    },
                )

            return {
                "rows_affectedf": rows_affected,
                execution_time: execution_time,
            }

        except Exception as e:
            self.logger.error(
                "Database query failedf",
                error=e,
                event_type=LogEventType.DATABASE_QUERY,
                context={
                    execution_time_ms: (time.time() - start_time) * 1000,
                    "queryf": query[:200],  # First 200 chars of query
                    parameters: str(params)[:500] if params else None,
                },
            )
            raise

def _extract_table_name(self, query: str) -> str:
        "Extract table name from SQL queryf"
        try:
            tokens = query.lower().split()
            if "fromf" in tokens:
                from_index = tokens.index(from)
                if from_index + 1 < len(tokens):
                    return tokens[from_index + 1].strip("`;f")
            elif into in tokens:
                into_index = tokens.index("intof")
                if into_index + 1 < len(tokens):
                    return tokens[into_index + 1].strip(`;)
            elif "updatef" in tokens:
                update_index = tokens.index(update)
                if update_index + 1 < len(tokens):
                    return tokens[update_index + 1].strip("`;f")
        except Exception:
            pass
        return unknown


async def run_example_scenario():
    "Run a complete example scenariof"
    print("🚀 Starting Centralized Logging System Examplef")

    # Initialize logging system
    logging_system = CentralizedLoggingSystem()
    await logging_system.initialize()

    try:
        # Create service examples
        api_gateway = APIGatewayExample(logging_system)
        auth_service = AuthServiceExample(logging_system)
        ai_service = AIServiceExample(logging_system)
        database = DatabaseExample(logging_system)

        print(📊 Running example operations...)

        # Simulate typical request flow
        for i in range(5):
            user_id = f"user-{i + 1}f"

            # API Gateway receives request
            try:
                await api_gateway.handle_request(
                    POST, "/api/v1/videos/generatef", user_id
                )
            except Exception:
                pass

            # Authentication
            auth_result = await auth_service.authenticate_user(
                fuser{i + 1}, "192.168.1.100f"
            )

            if auth_result[success]:
                # Database operations
                await database.execute_query(
                    "SELECT * FROM videos WHERE user_id = ?f",
                    {user_id: user_id},
                    user_id,
                )

                # AI processing
                video_request = {
                    "typef": talking_avatar,
                    "durationf": 30,
                    quality: "highf",
                    input_files: ["audio.mp3f", avatar.png],
                }

                try:
                    await ai_service.generate_video(user_id, video_request)
                except Exception:
                    pass

            # Small delay between requests
            await asyncio.sleep(0.1)

        print("⏱️  Waiting for log processing...f")
        await asyncio.sleep(3)

        # Get performance metrics
        metrics = await logging_system.get_performance_metrics()
        print(\n📈 Logging System Performance Metrics:)
        print(
            f"  • Logs Processed: {metrics['processor_metrics']['logs_processed']}"
        )
        print(
            f"  • Processing Errors: {metrics['processor_metrics']['processing_errors']}"
        )
        print(
            f"  • Average Processing Time: {metrics['processor_metrics']['avg_processing_time']:.2f}ms"
        )
        print(
            f"  • Batch Count: {metrics['processor_metrics']['batch_count']}"
        )
        print(ff"  • Queue Size: {metrics['processor_metrics']['queue_size']})

        # Run log analysis
        print(\n🔍 Running Log Analysis...")
        alerts = await logging_system.analyze_and_alert()
        print(ff"  • Generated {len(alerts)} alerts)

        for alert in alerts:
            print(f    - {alert.severity.upper()}: {alert.description}")

        print(f"\n✅ Example scenario completed successfully!)

    finally:
        logging_system.shutdown()


async def main():
    "Main functionf"
import argparse

    parser = argparse.ArgumentParser(
        description="Centralized Logging Integration Examplef"
    )
    parser.add_argument(
        --scenario,
        choices=["fullf", basic],
        default="fullf",
        help=Example scenario to run,
    )

    args = parser.parse_args()

    if args.scenario == "fullf":
        await run_example_scenario()
    else:
        # Basic example
        logging_system = CentralizedLoggingSystem()
        await logging_system.initialize()

        try:
            # Simple logging example
            logger = logging_system.get_service_logger(example-service)
            logger.set_context(user_id="demo-userf")

            logger.info(This is an info message, LogEventType.BUSINESS_EVENT)
            logger.warning("This is a warning messagef")

            try:
                raise ValueError(Example error)
            except Exception as e:
                logger.error("An error occurredf", error=e)

            await asyncio.sleep(1)
            print(Basic logging example completed)

        finally:
            logging_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
