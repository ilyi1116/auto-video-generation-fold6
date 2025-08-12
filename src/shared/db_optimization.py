"""
Database Query Optimization System
數據庫查詢優化系統 - 智能查詢優化和性能監控
"""

import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

logger = structlog.get_logger()


class QueryStats:
    """Query performance statistics"""
    
    def __init__(self):
        self.queries: List[Dict] = []
        self.slow_query_threshold = 1.0  # seconds
        
    def add_query(self, query: str, duration: float, params: Optional[Dict] = None):
        """Add query execution record"""
        self.queries.append({
            "query": query,
            "duration": duration,
            "params": params,
            "timestamp": time.time(),
            "is_slow": duration > self.slow_query_threshold
        })
        
        # Log slow queries
        if duration > self.slow_query_threshold:
            logger.warning(
                "Slow query detected",
                query=query[:200] + "..." if len(query) > 200 else query,
                duration=duration,
                params=params
            )
            
    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics"""
        if not self.queries:
            return {}
            
        durations = [q["duration"] for q in self.queries]
        slow_queries = [q for q in self.queries if q["is_slow"]]
        
        return {
            "total_queries": len(self.queries),
            "slow_queries": len(slow_queries),
            "avg_duration": sum(durations) / len(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "slow_query_rate": len(slow_queries) / len(self.queries) * 100
        }
        
    def get_slow_queries(self) -> List[Dict]:
        """Get list of slow queries"""
        return [q for q in self.queries if q["is_slow"]]


# Global query stats instance
query_stats = QueryStats()


@asynccontextmanager
async def query_monitor(session: AsyncSession, query_name: str = "unknown"):
    """Context manager for monitoring query performance"""
    start_time = time.time()
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        query_stats.add_query(query_name, duration)
        
        if duration > query_stats.slow_query_threshold:
            logger.warning(
                "Slow query completed",
                name=query_name,
                duration=duration
            )


def monitor_query(func):
    """Decorator for monitoring query performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            query_stats.add_query(func.__name__, duration)
            
    return wrapper


class QueryOptimizer:
    """Database query optimization utilities"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def optimize_select_query(
        self,
        select_query: Select,
        eager_load_relations: List[str] = None,
        join_relations: List[str] = None
    ) -> Select:
        """Optimize SELECT query with eager loading"""
        optimized_query = select_query
        
        # Add eager loading for specified relations
        if eager_load_relations:
            for relation in eager_load_relations:
                optimized_query = optimized_query.options(selectinload(relation))
                
        # Add joined loading for specified relations
        if join_relations:
            for relation in join_relations:
                optimized_query = optimized_query.options(joinedload(relation))
                
        return optimized_query
        
    async def analyze_query_plan(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Analyze query execution plan"""
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        
        try:
            result = await self.session.execute(text(explain_query), params or {})
            plan = result.fetchone()[0]
            
            return {
                "execution_time": self._extract_execution_time(plan),
                "planning_time": plan[0]["Planning Time"],
                "total_cost": plan[0]["Plan"]["Total Cost"],
                "rows": plan[0]["Plan"]["Actual Rows"],
                "plan": plan
            }
            
        except Exception as e:
            logger.error("Failed to analyze query plan", error=str(e))
            return {}
            
    def _extract_execution_time(self, plan: List[Dict]) -> float:
        """Extract execution time from query plan"""
        return plan[0]["Execution Time"]
        
    async def suggest_indexes(self, table_name: str) -> List[str]:
        """Suggest indexes for better query performance"""
        # Analyze table usage patterns
        usage_query = """
        SELECT schemaname, tablename, attname, n_distinct, correlation
        FROM pg_stats
        WHERE tablename = :table_name
        ORDER BY n_distinct DESC
        """
        
        try:
            result = await self.session.execute(
                text(usage_query),
                {"table_name": table_name}
            )
            
            stats = result.fetchall()
            suggestions = []
            
            for stat in stats:
                if stat.n_distinct > 100:  # High cardinality columns
                    suggestions.append(f"CREATE INDEX idx_{table_name}_{stat.attname} ON {table_name} ({stat.attname});")
                    
            return suggestions
            
        except Exception as e:
            logger.error("Failed to suggest indexes", error=str(e))
            return []
            
    async def find_missing_indexes(self) -> List[Dict[str, Any]]:
        """Find potentially missing indexes"""
        missing_indexes_query = """
        SELECT
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation,
            null_frac
        FROM pg_stats
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            AND n_distinct > 100
            AND null_frac < 0.1
        ORDER BY n_distinct DESC
        LIMIT 20
        """
        
        try:
            result = await self.session.execute(text(missing_indexes_query))
            return [
                {
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "column": row.attname,
                    "distinct_values": row.n_distinct,
                    "correlation": row.correlation,
                    "null_fraction": row.null_frac,
                    "suggested_index": f"CREATE INDEX idx_{row.tablename}_{row.attname} ON {row.tablename} ({row.attname});"
                }
                for row in result.fetchall()
            ]
            
        except Exception as e:
            logger.error("Failed to find missing indexes", error=str(e))
            return []
            
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get table statistics for optimization"""
        stats_query = """
        SELECT
            schemaname,
            tablename,
            n_tup_ins,
            n_tup_upd,
            n_tup_del,
            n_live_tup,
            n_dead_tup,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        WHERE tablename = :table_name
        """
        
        try:
            result = await self.session.execute(
                text(stats_query),
                {"table_name": table_name}
            )
            
            row = result.fetchone()
            if row:
                return {
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "inserts": row.n_tup_ins,
                    "updates": row.n_tup_upd,
                    "deletes": row.n_tup_del,
                    "live_tuples": row.n_live_tup,
                    "dead_tuples": row.n_dead_tup,
                    "last_vacuum": row.last_vacuum,
                    "last_autovacuum": row.last_autovacuum,
                    "last_analyze": row.last_analyze,
                    "last_autoanalyze": row.last_autoanalyze,
                    "dead_tuple_ratio": (row.n_dead_tup / max(row.n_live_tup, 1)) * 100
                }
                
            return {}
            
        except Exception as e:
            logger.error("Failed to get table stats", error=str(e))
            return {}


class DatabaseOptimizationManager:
    """Comprehensive database optimization manager"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.optimizer = QueryOptimizer(session)
        
    async def run_optimization_analysis(self) -> Dict[str, Any]:
        """Run comprehensive optimization analysis"""
        logger.info("Starting database optimization analysis")
        
        analysis_results = {
            "query_stats": query_stats.get_stats(),
            "slow_queries": query_stats.get_slow_queries(),
            "missing_indexes": await self.optimizer.find_missing_indexes(),
            "table_recommendations": [],
            "maintenance_recommendations": []
        }
        
        # Analyze key tables
        key_tables = ["users", "video_projects", "ai_requests", "trending_keywords"]
        
        for table_name in key_tables:
            try:
                table_stats = await self.optimizer.get_table_stats(table_name)
                if table_stats:
                    analysis_results["table_recommendations"].append({
                        "table": table_name,
                        "stats": table_stats,
                        "recommendations": self._generate_table_recommendations(table_stats)
                    })
            except Exception as e:
                logger.warning(f"Failed to analyze table {table_name}", error=str(e))
                
        # Generate maintenance recommendations
        analysis_results["maintenance_recommendations"] = await self._generate_maintenance_recommendations()
        
        logger.info("Database optimization analysis completed")
        return analysis_results
        
    def _generate_table_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations for table optimization"""
        recommendations = []
        
        # Check dead tuple ratio
        dead_ratio = stats.get("dead_tuple_ratio", 0)
        if dead_ratio > 20:
            recommendations.append(f"Consider VACUUM for {stats['table']} (dead tuple ratio: {dead_ratio:.1f}%)")
            
        # Check if analyze is needed
        if not stats.get("last_autoanalyze"):
            recommendations.append(f"Run ANALYZE on {stats['table']} for better query planning")
            
        # Check table size
        live_tuples = stats.get("live_tuples", 0)
        if live_tuples > 1000000:  # Large table
            recommendations.append(f"Consider partitioning {stats['table']} (size: {live_tuples:,} rows)")
            
        return recommendations
        
    async def _generate_maintenance_recommendations(self) -> List[str]:
        """Generate database maintenance recommendations"""
        recommendations = []
        
        # Check database size
        try:
            size_query = """
            SELECT
                pg_size_pretty(pg_database_size(current_database())) as size,
                pg_database_size(current_database()) as size_bytes
            """
            
            result = await self.session.execute(text(size_query))
            row = result.fetchone()
            
            size_bytes = row.size_bytes
            size_human = row.size
            
            recommendations.append(f"Database size: {size_human}")
            
            if size_bytes > 10 * 1024 * 1024 * 1024:  # > 10GB
                recommendations.append("Consider database maintenance for large database")
                
        except Exception as e:
            logger.error("Failed to check database size", error=str(e))
            
        # Check connection statistics
        try:
            connections_query = """
            SELECT
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
            """
            
            result = await self.session.execute(text(connections_query))
            row = result.fetchone()
            
            if row.total_connections > 50:
                recommendations.append(f"High connection count: {row.total_connections} (consider connection pooling)")
                
        except Exception as e:
            logger.error("Failed to check connections", error=str(e))
            
        return recommendations
        
    async def optimize_common_queries(self) -> Dict[str, str]:
        """Generate optimized versions of common queries"""
        optimizations = {}
        
        # User lookup optimization
        optimizations["user_lookup"] = """
        -- Original: SELECT * FROM users WHERE email = ?
        -- Optimized: Add index and select specific columns
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users (email);
        SELECT id, email, full_name, subscription_tier FROM users WHERE email = ?;
        """
        
        # Video project listing optimization
        optimizations["video_projects_list"] = """
        -- Original: SELECT * FROM video_projects WHERE user_id = ? ORDER BY created_at DESC
        -- Optimized: Add composite index and pagination
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_video_projects_user_created 
        ON video_projects (user_id, created_at DESC);
        
        SELECT id, title, status, created_at 
        FROM video_projects 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?;
        """
        
        # Trending data optimization
        optimizations["trending_data"] = """
        -- Original: SELECT * FROM trending_keywords WHERE platform = ? AND created_at > ?
        -- Optimized: Add composite index and materialized view
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trending_platform_created 
        ON trending_keywords (platform, created_at DESC);
        
        -- Consider materialized view for frequently accessed trending data
        CREATE MATERIALIZED VIEW IF NOT EXISTS trending_summary AS
        SELECT platform, keyword, count(*) as frequency, max(created_at) as last_seen
        FROM trending_keywords
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY platform, keyword
        ORDER BY frequency DESC;
        """
        
        return optimizations


# Utility functions for common optimization patterns
async def execute_with_monitoring(
    session: AsyncSession,
    query: str,
    params: Dict = None,
    query_name: str = "custom"
) -> Any:
    """Execute query with performance monitoring"""
    async with query_monitor(session, query_name):
        return await session.execute(text(query), params or {})


def batch_insert_optimization(items: List[Dict], batch_size: int = 1000):
    """Decorator for optimizing batch inserts"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Process items in batches
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                await func(batch, *args, **kwargs)
                
        return wrapper
    return decorator


async def get_query_stats() -> Dict[str, Any]:
    """Get global query statistics"""
    return query_stats.get_stats()


async def reset_query_stats():
    """Reset global query statistics"""
    global query_stats
    query_stats = QueryStats()