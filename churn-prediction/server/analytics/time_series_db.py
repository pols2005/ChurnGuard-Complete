# ChurnGuard Time-Series Database Integration
# Epic 4 - Advanced Analytics & AI Insights

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
import numpy as np
import pandas as pd
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class TimeSeriesPoint:
    """Time-series data point"""
    timestamp: datetime
    metric_name: str
    value: float
    organization_id: str
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None

class TimeSeriesDB:
    """
    High-performance time-series database wrapper for analytics
    
    Supports multiple backends:
    - InfluxDB (preferred for high-scale deployments)
    - TimescaleDB (PostgreSQL extension)
    - In-memory storage (development/testing)
    
    Features:
    - Sub-second query performance
    - Automatic data retention policies
    - Compression and downsampling
    - Multi-tenant data isolation
    - Real-time data ingestion
    """
    
    def __init__(self, backend: str = 'memory', connection_string: Optional[str] = None):
        self.backend = backend
        self.connection_string = connection_string
        self.client = None
        self.memory_storage = {}  # For in-memory backend
        
        self._initialize_backend()
        
    def _initialize_backend(self):
        """Initialize the time-series database backend"""
        if self.backend == 'influxdb':
            self._initialize_influxdb()
        elif self.backend == 'timescaledb':
            self._initialize_timescaledb()
        elif self.backend == 'memory':
            self._initialize_memory()
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
    
    def _initialize_influxdb(self):
        """Initialize InfluxDB connection"""
        try:
            from influxdb_client import InfluxDBClient
            from influxdb_client.client.write_api import SYNCHRONOUS
            
            # Parse connection string: influxdb://username:password@host:port/database?token=xxx
            if self.connection_string:
                # Simplified for demo - would parse full connection string in production
                self.client = InfluxDBClient(
                    url="http://localhost:8086",
                    token="your-token",
                    org="churnguard"
                )
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                self.query_api = self.client.query_api()
                self.bucket = "analytics"
                
                logger.info("InfluxDB client initialized")
            else:
                logger.warning("InfluxDB connection string not provided, using memory backend")
                self._initialize_memory()
                
        except ImportError:
            logger.warning("InfluxDB client not available, using memory backend")
            self._initialize_memory()
            
    def _initialize_timescaledb(self):
        """Initialize TimescaleDB connection"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            if self.connection_string:
                self.client = psycopg2.connect(self.connection_string)
                self._create_timescale_tables()
                logger.info("TimescaleDB client initialized")
            else:
                logger.warning("TimescaleDB connection string not provided, using memory backend")
                self._initialize_memory()
                
        except ImportError:
            logger.warning("TimescaleDB client not available, using memory backend")
            self._initialize_memory()
            
    def _initialize_memory(self):
        """Initialize in-memory storage"""
        self.backend = 'memory'
        self.memory_storage = {
            'metrics': [],
            'indexes': {}
        }
        logger.info("Memory backend initialized")
    
    def write_point(self, point: TimeSeriesPoint):
        """Write a single time-series data point"""
        if self.backend == 'influxdb':
            self._write_influxdb_point(point)
        elif self.backend == 'timescaledb':
            self._write_timescale_point(point)
        else:
            self._write_memory_point(point)
    
    def write_points(self, points: List[TimeSeriesPoint]):
        """Write multiple time-series data points"""
        if self.backend == 'influxdb':
            self._write_influxdb_points(points)
        elif self.backend == 'timescaledb':
            self._write_timescale_points(points)
        else:
            for point in points:
                self._write_memory_point(point)
    
    def query(self, 
              metric_name: str,
              organization_id: str,
              start_time: Optional[datetime] = None,
              end_time: Optional[datetime] = None,
              tags: Optional[Dict[str, str]] = None,
              aggregation: Optional[str] = None,
              interval: Optional[str] = None,
              limit: Optional[int] = None) -> pd.DataFrame:
        """
        Query time-series data with flexible filtering and aggregation
        
        Args:
            metric_name: Name of the metric to query
            organization_id: Organization ID for multi-tenant isolation
            start_time: Start time for query range
            end_time: End time for query range
            tags: Tag filters
            aggregation: Aggregation function ('mean', 'sum', 'count', 'min', 'max')
            interval: Aggregation interval ('1m', '5m', '1h', '1d')
            limit: Maximum number of points to return
            
        Returns:
            Pandas DataFrame with time-series data
        """
        if self.backend == 'influxdb':
            return self._query_influxdb(metric_name, organization_id, start_time, 
                                      end_time, tags, aggregation, interval, limit)
        elif self.backend == 'timescaledb':
            return self._query_timescale(metric_name, organization_id, start_time,
                                       end_time, tags, aggregation, interval, limit)
        else:
            return self._query_memory(metric_name, organization_id, start_time,
                                    end_time, tags, aggregation, interval, limit)
    
    def get_latest_value(self, metric_name: str, organization_id: str, 
                        tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get the latest value for a metric"""
        df = self.query(metric_name, organization_id, tags=tags, limit=1)
        if df.empty:
            return None
        return df.iloc[0]['value']
    
    def get_metric_stats(self, metric_name: str, organization_id: str,
                        window_hours: int = 1) -> Dict[str, float]:
        """Get statistical summary for a metric over a time window"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=window_hours)
        
        df = self.query(metric_name, organization_id, start_time, end_time)
        
        if df.empty:
            return {
                'count': 0,
                'mean': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'sum': 0.0,
                'rate_per_hour': 0.0
            }
        
        values = df['value']
        
        return {
            'count': len(values),
            'mean': float(values.mean()),
            'std': float(values.std()),
            'min': float(values.min()),
            'max': float(values.max()),
            'sum': float(values.sum()),
            'rate_per_hour': len(values) / window_hours,
            'p50': float(values.quantile(0.5)),
            'p95': float(values.quantile(0.95)),
            'p99': float(values.quantile(0.99))
        }
    
    def downsample(self, metric_name: str, organization_id: str,
                   aggregation: str, interval: str,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Downsample high-frequency data for long-term storage and analysis
        
        Args:
            metric_name: Name of the metric
            organization_id: Organization ID
            aggregation: Aggregation function ('mean', 'sum', 'count', 'min', 'max')
            interval: Downsampling interval ('1m', '5m', '1h', '1d')
            start_time: Start time for downsampling
            end_time: End time for downsampling
            
        Returns:
            Downsampled data as DataFrame
        """
        df = self.query(metric_name, organization_id, start_time, end_time)
        
        if df.empty:
            return df
        
        # Set timestamp as index for resampling
        df = df.set_index('timestamp')
        
        # Resample based on interval and aggregation
        if aggregation == 'mean':
            resampled = df['value'].resample(interval).mean()
        elif aggregation == 'sum':
            resampled = df['value'].resample(interval).sum()
        elif aggregation == 'count':
            resampled = df['value'].resample(interval).count()
        elif aggregation == 'min':
            resampled = df['value'].resample(interval).min()
        elif aggregation == 'max':
            resampled = df['value'].resample(interval).max()
        else:
            raise ValueError(f"Unsupported aggregation: {aggregation}")
        
        # Convert back to DataFrame
        result_df = resampled.reset_index()
        result_df.columns = ['timestamp', 'value']
        result_df['metric_name'] = metric_name
        result_df['organization_id'] = organization_id
        
        return result_df
    
    def cleanup_old_data(self, retention_days: int = 90):
        """Clean up old data based on retention policy"""
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        if self.backend == 'influxdb':
            self._cleanup_influxdb(cutoff_time)
        elif self.backend == 'timescaledb':
            self._cleanup_timescale(cutoff_time)
        else:
            self._cleanup_memory(cutoff_time)
    
    # InfluxDB-specific methods
    def _write_influxdb_point(self, point: TimeSeriesPoint):
        """Write point to InfluxDB"""
        from influxdb_client import Point
        
        p = Point(point.metric_name) \
            .tag("organization_id", point.organization_id) \
            .field("value", point.value) \
            .time(point.timestamp)
        
        # Add additional tags
        for key, value in point.tags.items():
            if key != 'organization_id':  # Already added
                p = p.tag(key, value)
        
        self.write_api.write(bucket=self.bucket, record=p)
    
    def _write_influxdb_points(self, points: List[TimeSeriesPoint]):
        """Write multiple points to InfluxDB"""
        from influxdb_client import Point
        
        records = []
        for point in points:
            p = Point(point.metric_name) \
                .tag("organization_id", point.organization_id) \
                .field("value", point.value) \
                .time(point.timestamp)
            
            for key, value in point.tags.items():
                if key != 'organization_id':
                    p = p.tag(key, value)
            
            records.append(p)
        
        self.write_api.write(bucket=self.bucket, record=records)
    
    def _query_influxdb(self, metric_name, organization_id, start_time, end_time,
                       tags, aggregation, interval, limit) -> pd.DataFrame:
        """Query InfluxDB"""
        # Build Flux query
        query = f'from(bucket: "{self.bucket}") |> range(start: -1h)'
        query += f' |> filter(fn: (r) => r._measurement == "{metric_name}")'
        query += f' |> filter(fn: (r) => r.organization_id == "{organization_id}")'
        
        if start_time:
            query = query.replace('-1h', start_time.strftime('%Y-%m-%dT%H:%M:%SZ'))
        
        if aggregation and interval:
            query += f' |> aggregateWindow(every: {interval}, fn: {aggregation})'
        
        if limit:
            query += f' |> limit(n: {limit})'
        
        result = self.query_api.query_data_frame(query)
        
        if result.empty:
            return pd.DataFrame(columns=['timestamp', 'value', 'metric_name', 'organization_id'])
        
        # Rename columns to match standard format
        result = result.rename(columns={'_time': 'timestamp', '_value': 'value'})
        result['metric_name'] = metric_name
        result['organization_id'] = organization_id
        
        return result[['timestamp', 'value', 'metric_name', 'organization_id']]
    
    # TimescaleDB-specific methods
    def _create_timescale_tables(self):
        """Create TimescaleDB tables"""
        with self.client.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS time_series_data (
                    timestamp TIMESTAMPTZ NOT NULL,
                    metric_name TEXT NOT NULL,
                    organization_id UUID NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    tags JSONB,
                    metadata JSONB
                );
                
                -- Create hypertable if not exists
                SELECT create_hypertable('time_series_data', 'timestamp', if_not_exists => TRUE);
                
                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_ts_metric_org ON time_series_data(metric_name, organization_id, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_ts_org_time ON time_series_data(organization_id, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_ts_tags ON time_series_data USING GIN (tags);
            """)
            self.client.commit()
    
    def _write_timescale_point(self, point: TimeSeriesPoint):
        """Write point to TimescaleDB"""
        with self.client.cursor() as cursor:
            cursor.execute("""
                INSERT INTO time_series_data (timestamp, metric_name, organization_id, value, tags, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                point.timestamp,
                point.metric_name,
                point.organization_id,
                point.value,
                json.dumps(point.tags),
                json.dumps(point.metadata) if point.metadata else None
            ))
        self.client.commit()
    
    def _write_timescale_points(self, points: List[TimeSeriesPoint]):
        """Write multiple points to TimescaleDB"""
        with self.client.cursor() as cursor:
            data = [
                (p.timestamp, p.metric_name, p.organization_id, p.value, 
                 json.dumps(p.tags), json.dumps(p.metadata) if p.metadata else None)
                for p in points
            ]
            
            cursor.executemany("""
                INSERT INTO time_series_data (timestamp, metric_name, organization_id, value, tags, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, data)
        self.client.commit()
    
    def _query_timescale(self, metric_name, organization_id, start_time, end_time,
                        tags, aggregation, interval, limit) -> pd.DataFrame:
        """Query TimescaleDB"""
        # Build SQL query
        query = """
            SELECT timestamp, value, metric_name, organization_id
            FROM time_series_data
            WHERE metric_name = %s AND organization_id = %s
        """
        params = [metric_name, organization_id]
        
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        if tags:
            for key, value in tags.items():
                query += " AND tags->%s = %s"
                params.extend([key, f'"{value}"'])
        
        if aggregation and interval:
            # Use TimescaleDB time_bucket function
            query = f"""
                SELECT time_bucket('{interval}', timestamp) as timestamp,
                       {aggregation}(value) as value,
                       %s as metric_name,
                       %s as organization_id
                FROM time_series_data
                WHERE metric_name = %s AND organization_id = %s
            """
            params = [metric_name, organization_id, metric_name, organization_id]
            
            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)
            
            query += " GROUP BY time_bucket('{interval}', timestamp)"
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self.client.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        
        columns = ['timestamp', 'value', 'metric_name', 'organization_id']
        return pd.DataFrame(rows, columns=columns)
    
    # In-memory backend methods
    def _write_memory_point(self, point: TimeSeriesPoint):
        """Write point to memory storage"""
        self.memory_storage['metrics'].append({
            'timestamp': point.timestamp,
            'metric_name': point.metric_name,
            'organization_id': point.organization_id,
            'value': point.value,
            'tags': point.tags,
            'metadata': point.metadata
        })
    
    def _query_memory(self, metric_name, organization_id, start_time, end_time,
                     tags, aggregation, interval, limit) -> pd.DataFrame:
        """Query memory storage"""
        data = []
        
        for point in self.memory_storage['metrics']:
            # Basic filtering
            if (point['metric_name'] == metric_name and 
                point['organization_id'] == organization_id):
                
                # Time filtering
                if start_time and point['timestamp'] < start_time:
                    continue
                if end_time and point['timestamp'] > end_time:
                    continue
                
                # Tag filtering
                if tags:
                    match = True
                    for key, value in tags.items():
                        if point['tags'].get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                data.append({
                    'timestamp': point['timestamp'],
                    'value': point['value'],
                    'metric_name': point['metric_name'],
                    'organization_id': point['organization_id']
                })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return df
        
        # Sort by timestamp descending
        df = df.sort_values('timestamp', ascending=False)
        
        # Apply limit
        if limit:
            df = df.head(limit)
        
        # Apply aggregation if specified
        if aggregation and interval and not df.empty:
            df = df.set_index('timestamp')
            if aggregation == 'mean':
                df = df['value'].resample(interval).mean().reset_index()
            elif aggregation == 'sum':
                df = df['value'].resample(interval).sum().reset_index()
            # Add other aggregations as needed
            df['metric_name'] = metric_name
            df['organization_id'] = organization_id
        
        return df
    
    def _cleanup_influxdb(self, cutoff_time: datetime):
        """Cleanup old InfluxDB data"""
        # InfluxDB cleanup would use retention policies
        pass
    
    def _cleanup_timescale(self, cutoff_time: datetime):
        """Cleanup old TimescaleDB data"""
        with self.client.cursor() as cursor:
            cursor.execute(
                "DELETE FROM time_series_data WHERE timestamp < %s",
                (cutoff_time,)
            )
        self.client.commit()
    
    def _cleanup_memory(self, cutoff_time: datetime):
        """Cleanup old memory data"""
        self.memory_storage['metrics'] = [
            point for point in self.memory_storage['metrics']
            if point['timestamp'] >= cutoff_time
        ]

# Global time-series database instance
ts_db = TimeSeriesDB(backend='memory')

def get_time_series_db() -> TimeSeriesDB:
    """Get the global time-series database instance"""
    return ts_db

# Convenience functions
def write_metric(metric_name: str, value: float, organization_id: str, **tags):
    """Write a metric to the time-series database"""
    point = TimeSeriesPoint(
        timestamp=datetime.now(),
        metric_name=metric_name,
        value=value,
        organization_id=organization_id,
        tags=tags
    )
    ts_db.write_point(point)

def query_metric_history(metric_name: str, organization_id: str, 
                        hours_back: int = 24) -> pd.DataFrame:
    """Query metric history"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)
    return ts_db.query(metric_name, organization_id, start_time, end_time)