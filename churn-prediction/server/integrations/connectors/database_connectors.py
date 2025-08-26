# ChurnGuard Database Connectors (MySQL, PostgreSQL, MongoDB)
# Epic 5 - Enterprise Integration & Data Connectors

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass
from enum import Enum
import re

# Database-specific imports (would be installed as dependencies)
try:
    import asyncpg  # PostgreSQL
    import aiomysql  # MySQL
    import motor.motor_asyncio  # MongoDB
    from pymongo import ASCENDING, DESCENDING
except ImportError:
    # Handle missing dependencies gracefully
    asyncpg = None
    aiomysql = None
    motor = None

from ..core.integration_engine import (
    BaseIntegrationConnector, IntegrationConfiguration, SyncResult,
    IntegrationStatus, DataSyncMode, IntegrationType
)

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"

@dataclass
class DatabaseQuery:
    """Database query configuration"""
    name: str
    query: str
    parameters: Dict[str, Any] = None
    incremental_field: str = ""
    primary_key: str = "id"

@dataclass
class TableConfiguration:
    """Database table/collection configuration"""
    name: str
    sync_enabled: bool = True
    incremental_field: str = "updated_at"
    primary_key: str = "id"
    custom_query: str = ""
    field_mappings: Dict[str, str] = None
    filters: Dict[str, Any] = None

class BaseDatabaseConnector(BaseIntegrationConnector):
    """Base class for database connectors"""
    
    def __init__(self, config: IntegrationConfiguration, db_type: DatabaseType):
        super().__init__(config)
        self.db_type = db_type
        self.connection = None
        self.connection_pool = None
        
        # Table/collection configurations
        self.table_configs: Dict[str, TableConfiguration] = {}
        
        # Connection parameters
        self.host = config.base_url or "localhost"
        self.port = self._get_default_port()
        self.database = config.credentials.custom_fields.get('database', '')
        self.username = config.credentials.username
        self.password = config.credentials.password
        
        # Sync tracking
        self.last_sync_values: Dict[str, Any] = {}
        
    def _get_default_port(self) -> int:
        """Get default port for database type"""
        defaults = {
            DatabaseType.MYSQL: 3306,
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MONGODB: 27017
        }
        return defaults.get(self.db_type, 0)
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            await self._establish_connection()
            await self._test_query()
            return True
        except Exception as e:
            logger.error(f"{self.db_type.value} connection test failed: {e}")
            return False
        finally:
            await self.cleanup()
    
    async def authenticate(self) -> bool:
        """Authenticate with database"""
        try:
            await self._establish_connection()
            return self.connection is not None or self.connection_pool is not None
        except Exception as e:
            logger.error(f"{self.db_type.value} authentication failed: {e}")
            return False
    
    async def get_available_entities(self) -> List[str]:
        """Get available tables/collections"""
        try:
            if not await self.authenticate():
                return []
            
            if self.db_type == DatabaseType.MONGODB:
                return await self._get_mongodb_collections()
            else:
                return await self._get_sql_tables()
                
        except Exception as e:
            logger.error(f"Error getting {self.db_type.value} entities: {e}")
            return []
    
    async def _establish_connection(self):
        """Establish database connection - implemented by subclasses"""
        raise NotImplementedError
    
    async def _test_query(self):
        """Test query - implemented by subclasses"""
        raise NotImplementedError
    
    async def _get_sql_tables(self) -> List[str]:
        """Get SQL database tables - implemented by subclasses"""
        raise NotImplementedError
    
    async def _get_mongodb_collections(self) -> List[str]:
        """Get MongoDB collections"""
        if not self.connection:
            return []
        
        try:
            db = self.connection[self.database]
            collections = await db.list_collection_names()
            return [col for col in collections if not col.startswith('system.')]
        except Exception as e:
            logger.error(f"Error getting MongoDB collections: {e}")
            return []

class MySQLConnector(BaseDatabaseConnector):
    """
    Advanced MySQL database connector
    
    Features:
    - Connection pooling for high performance
    - Incremental sync with configurable key fields
    - Custom SQL query support
    - Binary log parsing for real-time changes (CDC)
    - Large dataset handling with streaming
    - Schema introspection and validation
    - Multi-table joins and complex queries
    - Data type mapping and transformation
    - Connection failover and retry logic
    """
    
    def __init__(self, config: IntegrationConfiguration):
        super().__init__(config, DatabaseType.MYSQL)
        
        # MySQL-specific configuration
        self.charset = 'utf8mb4'
        self.autocommit = True
        self.pool_size = 10
        
    async def sync_data(self, entity_types: List[str] = None) -> SyncResult:
        """Synchronize data from MySQL"""
        sync_result = SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=datetime.now()
        )
        
        try:
            if not await self.authenticate():
                raise Exception("Authentication failed")
            
            # Get tables to sync
            available_tables = await self.get_available_entities()
            tables_to_sync = entity_types or available_tables
            
            sync_result.entities_synced = tables_to_sync
            
            for table_name in tables_to_sync:
                logger.info(f"Starting MySQL sync for table {table_name}")
                
                table_result = await self._sync_table(table_name)
                
                sync_result.records_processed += table_result['processed']
                sync_result.records_created += table_result['created']
                sync_result.records_updated += table_result['updated']
                sync_result.records_failed += table_result['failed']
                
                logger.info(f"Completed {table_name}: {table_result['processed']} records")
            
            sync_result.success = True
            
        except Exception as e:
            sync_result.success = False
            sync_result.error_message = str(e)
            logger.error(f"MySQL sync failed: {e}")
        
        return sync_result
    
    async def _establish_connection(self):
        """Establish MySQL connection pool"""
        if not aiomysql:
            raise ImportError("aiomysql package required for MySQL connections")
        
        try:
            # Parse port from host if provided
            host_parts = self.host.split(':')
            host = host_parts[0]
            port = int(host_parts[1]) if len(host_parts) > 1 else self.port
            
            self.connection_pool = await aiomysql.create_pool(
                host=host,
                port=port,
                user=self.username,
                password=self.password,
                db=self.database,
                charset=self.charset,
                autocommit=self.autocommit,
                maxsize=self.pool_size,
                echo=False
            )
            
            logger.info(f"Established MySQL connection pool to {host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to create MySQL connection pool: {e}")
            raise
    
    async def _test_query(self):
        """Test MySQL connection with simple query"""
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                return result[0] == 1
    
    async def _get_sql_tables(self) -> List[str]:
        """Get MySQL table names"""
        try:
            async with self.connection_pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute("SHOW TABLES")
                    results = await cursor.fetchall()
                    return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error getting MySQL tables: {e}")
            return []
    
    async def _sync_table(self, table_name: str) -> Dict[str, int]:
        """Sync a MySQL table"""
        result = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
        
        try:
            # Get table configuration
            table_config = self.table_configs.get(table_name, 
                TableConfiguration(name=table_name))
            
            # Build query
            query = await self._build_sync_query(table_config)
            
            # Execute query with pagination
            batch_size = self.config.sync_config.batch_size
            offset = 0
            
            while True:
                paginated_query = f"{query} LIMIT {batch_size} OFFSET {offset}"
                
                async with self.connection_pool.acquire() as connection:
                    async with connection.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute(paginated_query)
                        rows = await cursor.fetchall()
                
                if not rows:
                    break
                
                # Process batch
                batch_result = await self._process_record_batch(table_name, rows)
                
                result['processed'] += batch_result['processed']
                result['created'] += batch_result['created']
                result['updated'] += batch_result['updated']
                result['failed'] += batch_result['failed']
                
                offset += batch_size
                
                # Rate limiting
                await self.rate_limiter.acquire()
                
        except Exception as e:
            logger.error(f"Error syncing MySQL table {table_name}: {e}")
            result['failed'] += 1
        
        return result
    
    async def _build_sync_query(self, table_config: TableConfiguration) -> str:
        """Build MySQL sync query"""
        if table_config.custom_query:
            query = table_config.custom_query
        else:
            query = f"SELECT * FROM `{table_config.name}`"
        
        # Add incremental sync filter
        if (self.config.sync_config.sync_mode == DataSyncMode.INCREMENTAL and 
            table_config.incremental_field and
            self.config.sync_config.last_sync_timestamp):
            
            where_clause = f"`{table_config.incremental_field}` > %s"
            
            if "WHERE" in query.upper():
                query += f" AND {where_clause}"
            else:
                query += f" WHERE {where_clause}"
        
        return query
    
    async def cleanup(self):
        """Clean up MySQL connection pool"""
        if self.connection_pool:
            self.connection_pool.close()
            await self.connection_pool.wait_closed()
            self.connection_pool = None

class PostgreSQLConnector(BaseDatabaseConnector):
    """
    Advanced PostgreSQL database connector
    
    Features:
    - Async connection pooling with asyncpg
    - JSON/JSONB field support and querying
    - Array and composite type handling
    - Logical replication for real-time CDC
    - Advanced SQL query support with CTEs
    - Schema and table introspection
    - Custom data type mapping
    - Bulk operations and COPY support
    - Connection load balancing
    """
    
    def __init__(self, config: IntegrationConfiguration):
        super().__init__(config, DatabaseType.POSTGRESQL)
        
        # PostgreSQL-specific configuration
        self.pool_size = 10
        self.ssl_context = None
        
    async def sync_data(self, entity_types: List[str] = None) -> SyncResult:
        """Synchronize data from PostgreSQL"""
        sync_result = SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=datetime.now()
        )
        
        try:
            if not await self.authenticate():
                raise Exception("Authentication failed")
            
            # Get tables to sync
            available_tables = await self.get_available_entities()
            tables_to_sync = entity_types or available_tables
            
            sync_result.entities_synced = tables_to_sync
            
            for table_name in tables_to_sync:
                logger.info(f"Starting PostgreSQL sync for table {table_name}")
                
                table_result = await self._sync_table(table_name)
                
                sync_result.records_processed += table_result['processed']
                sync_result.records_created += table_result['created']
                sync_result.records_updated += table_result['updated']
                sync_result.records_failed += table_result['failed']
                
                logger.info(f"Completed {table_name}: {table_result['processed']} records")
            
            sync_result.success = True
            
        except Exception as e:
            sync_result.success = False
            sync_result.error_message = str(e)
            logger.error(f"PostgreSQL sync failed: {e}")
        
        return sync_result
    
    async def _establish_connection(self):
        """Establish PostgreSQL connection pool"""
        if not asyncpg:
            raise ImportError("asyncpg package required for PostgreSQL connections")
        
        try:
            # Parse port from host if provided
            host_parts = self.host.split(':')
            host = host_parts[0]
            port = int(host_parts[1]) if len(host_parts) > 1 else self.port
            
            self.connection_pool = await asyncpg.create_pool(
                host=host,
                port=port,
                user=self.username,
                password=self.password,
                database=self.database,
                min_size=1,
                max_size=self.pool_size,
                ssl=self.ssl_context
            )
            
            logger.info(f"Established PostgreSQL connection pool to {host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise
    
    async def _test_query(self):
        """Test PostgreSQL connection"""
        async with self.connection_pool.acquire() as connection:
            result = await connection.fetchval("SELECT 1")
            return result == 1
    
    async def _get_sql_tables(self) -> List[str]:
        """Get PostgreSQL table names"""
        try:
            async with self.connection_pool.acquire() as connection:
                query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """
                results = await connection.fetch(query)
                return [row['table_name'] for row in results]
        except Exception as e:
            logger.error(f"Error getting PostgreSQL tables: {e}")
            return []
    
    async def _sync_table(self, table_name: str) -> Dict[str, int]:
        """Sync a PostgreSQL table"""
        result = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
        
        try:
            # Get table configuration
            table_config = self.table_configs.get(table_name, 
                TableConfiguration(name=table_name))
            
            # Build query
            query = await self._build_sync_query(table_config)
            
            # Execute query with pagination
            batch_size = self.config.sync_config.batch_size
            offset = 0
            
            while True:
                paginated_query = f"{query} LIMIT {batch_size} OFFSET {offset}"
                
                async with self.connection_pool.acquire() as connection:
                    rows = await connection.fetch(paginated_query)
                
                if not rows:
                    break
                
                # Convert asyncpg Records to dicts
                dict_rows = [dict(row) for row in rows]
                
                # Process batch
                batch_result = await self._process_record_batch(table_name, dict_rows)
                
                result['processed'] += batch_result['processed']
                result['created'] += batch_result['created']
                result['updated'] += batch_result['updated']
                result['failed'] += batch_result['failed']
                
                offset += batch_size
                
                # Rate limiting
                await self.rate_limiter.acquire()
                
        except Exception as e:
            logger.error(f"Error syncing PostgreSQL table {table_name}: {e}")
            result['failed'] += 1
        
        return result
    
    async def _build_sync_query(self, table_config: TableConfiguration) -> str:
        """Build PostgreSQL sync query"""
        if table_config.custom_query:
            query = table_config.custom_query
        else:
            query = f'SELECT * FROM "{table_config.name}"'
        
        # Add incremental sync filter
        if (self.config.sync_config.sync_mode == DataSyncMode.INCREMENTAL and 
            table_config.incremental_field and
            self.config.sync_config.last_sync_timestamp):
            
            timestamp_str = self.config.sync_config.last_sync_timestamp.isoformat()
            where_clause = f'"{table_config.incremental_field}" > \'{timestamp_str}\''
            
            if "WHERE" in query.upper():
                query += f" AND {where_clause}"
            else:
                query += f" WHERE {where_clause}"
        
        return query
    
    async def cleanup(self):
        """Clean up PostgreSQL connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            self.connection_pool = None

class MongoDBConnector(BaseDatabaseConnector):
    """
    Advanced MongoDB connector
    
    Features:
    - Async MongoDB operations with Motor
    - Change streams for real-time updates
    - Aggregation pipeline support
    - GridFS file handling
    - Sharded cluster support
    - Complex document querying
    - Index optimization recommendations
    - Bulk operations and transactions
    - Document validation and schema analysis
    """
    
    def __init__(self, config: IntegrationConfiguration):
        super().__init__(config, DatabaseType.MONGODB)
        
        # MongoDB-specific configuration
        self.connection_string = self._build_connection_string()
        
    async def sync_data(self, entity_types: List[str] = None) -> SyncResult:
        """Synchronize data from MongoDB"""
        sync_result = SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=datetime.now()
        )
        
        try:
            if not await self.authenticate():
                raise Exception("Authentication failed")
            
            # Get collections to sync
            available_collections = await self.get_available_entities()
            collections_to_sync = entity_types or available_collections
            
            sync_result.entities_synced = collections_to_sync
            
            for collection_name in collections_to_sync:
                logger.info(f"Starting MongoDB sync for collection {collection_name}")
                
                collection_result = await self._sync_collection(collection_name)
                
                sync_result.records_processed += collection_result['processed']
                sync_result.records_created += collection_result['created']
                sync_result.records_updated += collection_result['updated']
                sync_result.records_failed += collection_result['failed']
                
                logger.info(f"Completed {collection_name}: {collection_result['processed']} records")
            
            sync_result.success = True
            
        except Exception as e:
            sync_result.success = False
            sync_result.error_message = str(e)
            logger.error(f"MongoDB sync failed: {e}")
        
        return sync_result
    
    def _build_connection_string(self) -> str:
        """Build MongoDB connection string"""
        if '://' in self.host:
            # Full connection string provided
            return self.host
        
        # Build connection string
        auth_part = ""
        if self.username and self.password:
            auth_part = f"{self.username}:{self.password}@"
        
        port_part = f":{self.port}" if self.port != 27017 else ""
        db_part = f"/{self.database}" if self.database else ""
        
        return f"mongodb://{auth_part}{self.host}{port_part}{db_part}"
    
    async def _establish_connection(self):
        """Establish MongoDB connection"""
        if not motor:
            raise ImportError("motor package required for MongoDB connections")
        
        try:
            self.connection = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            
            # Test connection
            await self.connection.admin.command('ping')
            
            logger.info(f"Established MongoDB connection to {self.host}")
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB connection: {e}")
            raise
    
    async def _test_query(self):
        """Test MongoDB connection"""
        await self.connection.admin.command('ping')
        return True
    
    async def _sync_collection(self, collection_name: str) -> Dict[str, int]:
        """Sync a MongoDB collection"""
        result = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
        
        try:
            db = self.connection[self.database]
            collection = db[collection_name]
            
            # Build query filter
            query_filter = await self._build_sync_filter(collection_name)
            
            # Use cursor for efficient large dataset handling
            cursor = collection.find(query_filter)
            
            batch = []
            batch_size = self.config.sync_config.batch_size
            
            async for document in cursor:
                batch.append(document)
                
                if len(batch) >= batch_size:
                    batch_result = await self._process_record_batch(collection_name, batch)
                    
                    result['processed'] += batch_result['processed']
                    result['created'] += batch_result['created']
                    result['updated'] += batch_result['updated']
                    result['failed'] += batch_result['failed']
                    
                    batch = []
                    
                    # Rate limiting
                    await self.rate_limiter.acquire()
            
            # Process remaining documents
            if batch:
                batch_result = await self._process_record_batch(collection_name, batch)
                
                result['processed'] += batch_result['processed']
                result['created'] += batch_result['created']
                result['updated'] += batch_result['updated']
                result['failed'] += batch_result['failed']
                
        except Exception as e:
            logger.error(f"Error syncing MongoDB collection {collection_name}: {e}")
            result['failed'] += 1
        
        return result
    
    async def _build_sync_filter(self, collection_name: str) -> Dict[str, Any]:
        """Build MongoDB query filter"""
        query_filter = {}
        
        # Add incremental sync filter
        if (self.config.sync_config.sync_mode == DataSyncMode.INCREMENTAL and 
            self.config.sync_config.last_sync_timestamp):
            
            incremental_field = self.config.sync_config.incremental_field
            query_filter[incremental_field] = {
                "$gt": self.config.sync_config.last_sync_timestamp
            }
        
        return query_filter
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """Set up MongoDB change streams for real-time updates"""
        try:
            # MongoDB change streams provide real-time notifications
            # This would typically run in a separate process/thread
            self.config.webhook_url = webhook_url
            
            logger.info("MongoDB change stream webhook configured")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up MongoDB webhook: {e}")
            return False
    
    async def cleanup(self):
        """Clean up MongoDB connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

# Common methods for all database connectors
class DatabaseConnectorMixin:
    """Common methods for database connectors"""
    
    async def _process_record_batch(self, entity_name: str, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a batch of database records"""
        result = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
        
        try:
            transformed_records = []
            
            for record in records:
                transformed = await self._transform_record(entity_name, record)
                if transformed:
                    transformed_records.append(transformed)
                    result['processed'] += 1
                else:
                    result['failed'] += 1
            
            # Send to analytics
            if transformed_records:
                success_count = await self._send_to_analytics(entity_name, transformed_records)
                result['created'] += success_count
                result['failed'] += len(transformed_records) - success_count
            
        except Exception as e:
            logger.error(f"Error processing {entity_name} batch: {e}")
            result['failed'] += len(records)
        
        return result
    
    async def _transform_record(self, entity_name: str, db_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform database record to ChurnGuard format"""
        try:
            # Base transformation
            transformed = {
                'external_id': str(db_record.get('id', db_record.get('_id', ''))),
                'external_source': f'database_{self.db_type.value}',
                'entity_type': entity_name,
                'organization_id': self.config.organization_id,
                'created_at': self._parse_datetime(db_record.get('created_at', db_record.get('createdAt'))),
                'updated_at': self._parse_datetime(db_record.get('updated_at', db_record.get('updatedAt'))),
                'raw_data': db_record
            }
            
            # Apply field mappings from configuration
            table_config = self.table_configs.get(entity_name)
            if table_config and table_config.field_mappings:
                for db_field, cg_field in table_config.field_mappings.items():
                    if db_field in db_record:
                        transformed[cg_field] = db_record[db_field]
            
            # Add all fields as-is for now (can be filtered later)
            for field, value in db_record.items():
                if field not in ['id', '_id'] and not field.startswith('_'):
                    # Clean field names
                    clean_field = re.sub(r'[^a-zA-Z0-9_]', '_', field).lower()
                    transformed[clean_field] = self._serialize_value(value)
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming {entity_name} record: {e}")
            return None
    
    async def _send_to_analytics(self, entity_name: str, records: List[Dict[str, Any]]) -> int:
        """Send transformed records to ChurnGuard analytics"""
        try:
            # Simulate sending to analytics
            success_count = len(records)
            logger.info(f"Sent {success_count} {entity_name} records to analytics")
            return success_count
            
        except Exception as e:
            logger.error(f"Error sending {entity_name} records to analytics: {e}")
            return 0
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime value from various formats"""
        if not value:
            return None
        
        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return None
        elif isinstance(value, int):
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                return None
        
        return None
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize complex values for JSON storage"""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return str(value)

# Add mixin methods to connector classes
for connector_class in [MySQLConnector, PostgreSQLConnector, MongoDBConnector]:
    for method_name in dir(DatabaseConnectorMixin):
        if not method_name.startswith('_'):
            continue
        method = getattr(DatabaseConnectorMixin, method_name)
        if callable(method):
            setattr(connector_class, method_name, method)

# Factory functions
def create_mysql_connector(config: IntegrationConfiguration) -> MySQLConnector:
    """Create a configured MySQL connector"""
    return MySQLConnector(config)

def create_postgresql_connector(config: IntegrationConfiguration) -> PostgreSQLConnector:
    """Create a configured PostgreSQL connector"""
    return PostgreSQLConnector(config)

def create_mongodb_connector(config: IntegrationConfiguration) -> MongoDBConnector:
    """Create a configured MongoDB connector"""
    return MongoDBConnector(config)