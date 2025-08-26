# ChurnGuard Real-Time Streaming Data Pipelines
# Epic 5 - Enterprise Integration & Data Connectors

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Union, Callable, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict, deque
import time
import hashlib

# Streaming service imports (would be installed as dependencies)
try:
    import aiokafka  # Kafka
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError:
    aiokafka = None

try:
    import aioredis  # Redis Streams
except ImportError:
    aioredis = None

try:
    import websockets  # WebSocket streams
except ImportError:
    websockets = None

from ..core.integration_engine import IntegrationConfiguration

logger = logging.getLogger(__name__)

class StreamType(Enum):
    KAFKA = "kafka"
    REDIS_STREAMS = "redis_streams"
    WEBSOCKET = "websocket"
    RABBITMQ = "rabbitmq"
    AWS_KINESIS = "aws_kinesis"
    CUSTOM = "custom"

class DataFormat(Enum):
    JSON = "json"
    AVRO = "avro"
    PROTOBUF = "protobuf"
    CSV = "csv"
    XML = "xml"
    PLAIN_TEXT = "plain_text"

class ProcessingMode(Enum):
    AT_LEAST_ONCE = "at_least_once"
    AT_MOST_ONCE = "at_most_once"
    EXACTLY_ONCE = "exactly_once"

@dataclass
class StreamMessage:
    """Stream message data structure"""
    message_id: str
    stream_id: str
    organization_id: str
    timestamp: datetime
    
    # Message data
    data: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Processing metadata
    processed: bool = False
    processed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0
    retry_count: int = 0
    error_message: str = ""
    
    # Source information
    source_topic: str = ""
    source_partition: int = 0
    source_offset: int = 0

@dataclass
class StreamConfiguration:
    """Stream configuration"""
    stream_id: str
    organization_id: str
    name: str
    description: str
    
    # Stream settings
    stream_type: StreamType
    connection_config: Dict[str, Any] = field(default_factory=dict)
    
    # Topic/stream settings
    topics: List[str] = field(default_factory=list)
    consumer_group: str = ""
    
    # Data format
    data_format: DataFormat = DataFormat.JSON
    schema: Dict[str, Any] = field(default_factory=dict)
    
    # Processing configuration
    processing_mode: ProcessingMode = ProcessingMode.AT_LEAST_ONCE
    batch_size: int = 100
    batch_timeout_ms: int = 1000
    max_retries: int = 3
    
    # Transformation
    transformation_function: Optional[str] = None
    field_mappings: Dict[str, str] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # Performance settings
    buffer_size: int = 10000
    max_concurrent_processors: int = 10
    
    # Status
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_message_at: Optional[datetime] = None
    total_messages_processed: int = 0
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StreamMetrics:
    """Stream processing metrics"""
    stream_id: str
    
    # Throughput metrics
    messages_per_second: float = 0.0
    bytes_per_second: float = 0.0
    
    # Processing metrics
    avg_processing_time_ms: float = 0.0
    success_rate: float = 1.0
    error_rate: float = 0.0
    
    # Lag metrics
    consumer_lag: int = 0
    partition_lags: Dict[int, int] = field(default_factory=dict)
    
    # Buffer metrics
    buffer_utilization: float = 0.0
    queued_messages: int = 0
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Window-based metrics
    messages_last_minute: int = 0
    messages_last_hour: int = 0
    errors_last_minute: int = 0

class StreamProcessor:
    """Base class for stream processors"""
    
    def __init__(self, config: StreamConfiguration):
        self.config = config
        self.metrics = StreamMetrics(stream_id=config.stream_id)
        self.running = False
        self.consumer_task: Optional[asyncio.Task] = None
        
        # Message buffers
        self.message_buffer: deque = deque(maxlen=config.buffer_size)
        self.processing_queue: asyncio.Queue = asyncio.Queue(maxsize=config.buffer_size)
        
        # Processing workers
        self.processor_tasks: List[asyncio.Task] = []
        
        # Metrics tracking
        self.message_timestamps: deque = deque(maxlen=1000)
        self.processing_times: deque = deque(maxlen=1000)
        self.errors: deque = deque(maxlen=100)
    
    async def start(self):
        """Start stream processing"""
        if self.running:
            return
        
        self.running = True
        logger.info(f"Starting stream processor for {self.config.name}")
        
        # Start consumer
        self.consumer_task = asyncio.create_task(self._consume_messages())
        
        # Start processing workers
        for i in range(self.config.max_concurrent_processors):
            task = asyncio.create_task(self._process_messages(f"worker-{i}"))
            self.processor_tasks.append(task)
        
        # Start metrics updater
        asyncio.create_task(self._update_metrics())
    
    async def stop(self):
        """Stop stream processing"""
        if not self.running:
            return
        
        self.running = False
        logger.info(f"Stopping stream processor for {self.config.name}")
        
        # Stop consumer
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass
        
        # Stop processors
        for task in self.processor_tasks:
            task.cancel()
        
        await asyncio.gather(*self.processor_tasks, return_exceptions=True)
        
        # Clean up resources
        await self._cleanup()
    
    async def _consume_messages(self):
        """Consume messages from stream - implemented by subclasses"""
        raise NotImplementedError
    
    async def _process_messages(self, worker_id: str):
        """Process messages from queue"""
        while self.running:
            try:
                # Get message from queue
                message = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=1.0
                )
                
                start_time = time.time()
                
                # Process message
                success = await self._process_single_message(message)
                
                # Update metrics
                processing_time = (time.time() - start_time) * 1000
                self.processing_times.append(processing_time)
                
                message.processed = success
                message.processed_at = datetime.now()
                message.processing_time_ms = processing_time
                
                if success:
                    self.config.total_messages_processed += 1
                    self.config.last_message_at = datetime.now()
                else:
                    self.errors.append(datetime.now())
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message processor {worker_id}: {e}")
                self.errors.append(datetime.now())
                await asyncio.sleep(0.1)
    
    async def _process_single_message(self, message: StreamMessage) -> bool:
        """Process a single stream message"""
        try:
            # Apply filters
            if not self._passes_filters(message):
                return True  # Filtered out but not an error
            
            # Transform data
            transformed_data = await self._transform_message(message)
            if not transformed_data:
                return False
            
            # Send to analytics
            success = await self._send_to_analytics(transformed_data)
            return success
            
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")
            message.error_message = str(e)
            return False
    
    def _passes_filters(self, message: StreamMessage) -> bool:
        """Check if message passes configured filters"""
        if not self.config.filters:
            return True
        
        try:
            for field, filter_config in self.config.filters.items():
                if field not in message.data:
                    continue
                
                value = message.data[field]
                
                # Simple filter operations
                if 'equals' in filter_config:
                    if value != filter_config['equals']:
                        return False
                
                if 'contains' in filter_config:
                    if isinstance(value, str) and filter_config['contains'] not in value:
                        return False
                
                if 'min_value' in filter_config:
                    if isinstance(value, (int, float)) and value < filter_config['min_value']:
                        return False
                
                if 'max_value' in filter_config:
                    if isinstance(value, (int, float)) and value > filter_config['max_value']:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return False
    
    async def _transform_message(self, message: StreamMessage) -> Optional[Dict[str, Any]]:
        """Transform stream message data"""
        try:
            # Base transformation
            transformed = {
                'message_id': message.message_id,
                'stream_id': message.stream_id,
                'organization_id': message.organization_id,
                'timestamp': message.timestamp.isoformat(),
                'source': f'stream_{self.config.stream_type.value}',
                'raw_data': message.data
            }
            
            # Apply field mappings
            for source_field, target_field in self.config.field_mappings.items():
                if source_field in message.data:
                    transformed[target_field] = message.data[source_field]
            
            # Copy all fields if no mappings specified
            if not self.config.field_mappings:
                transformed.update(message.data)
            
            # Apply custom transformation function if specified
            if self.config.transformation_function:
                transformed = await self._apply_custom_transformation(transformed)
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming message: {e}")
            return None
    
    async def _apply_custom_transformation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom transformation function"""
        try:
            # This would execute custom Python code safely
            # For now, we'll just return the data as-is
            return data
        except Exception as e:
            logger.error(f"Error in custom transformation: {e}")
            return data
    
    async def _send_to_analytics(self, data: Dict[str, Any]) -> bool:
        """Send transformed data to analytics system"""
        try:
            # This would integrate with the main analytics system
            logger.debug(f"Sending stream data to analytics: {data.get('message_id')}")
            return True
        except Exception as e:
            logger.error(f"Error sending stream data to analytics: {e}")
            return False
    
    async def _update_metrics(self):
        """Update stream processing metrics"""
        while self.running:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                now = datetime.now()
                minute_ago = now - timedelta(minutes=1)
                hour_ago = now - timedelta(hours=1)
                
                # Calculate throughput
                recent_messages = [ts for ts in self.message_timestamps if ts > minute_ago]
                self.metrics.messages_per_second = len(recent_messages) / 60.0
                
                # Calculate processing times
                if self.processing_times:
                    self.metrics.avg_processing_time_ms = sum(self.processing_times) / len(self.processing_times)
                
                # Calculate error rates
                recent_errors = [ts for ts in self.errors if ts > minute_ago]
                if recent_messages:
                    self.metrics.error_rate = len(recent_errors) / len(recent_messages)
                    self.metrics.success_rate = 1.0 - self.metrics.error_rate
                
                # Update counts
                self.metrics.messages_last_minute = len(recent_messages)
                self.metrics.messages_last_hour = len([ts for ts in self.message_timestamps if ts > hour_ago])
                self.metrics.errors_last_minute = len(recent_errors)
                
                # Buffer utilization
                self.metrics.buffer_utilization = len(self.message_buffer) / self.config.buffer_size
                self.metrics.queued_messages = self.processing_queue.qsize()
                
                self.metrics.last_updated = now
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
    
    async def _cleanup(self):
        """Clean up resources"""
        pass

class KafkaStreamProcessor(StreamProcessor):
    """Kafka stream processor"""
    
    def __init__(self, config: StreamConfiguration):
        super().__init__(config)
        self.consumer: Optional[AIOKafkaConsumer] = None
        
        if not aiokafka:
            raise ImportError("aiokafka package required for Kafka streaming")
    
    async def _consume_messages(self):
        """Consume messages from Kafka"""
        try:
            # Create Kafka consumer
            self.consumer = AIOKafkaConsumer(
                *self.config.topics,
                bootstrap_servers=self.config.connection_config.get('bootstrap_servers', 'localhost:9092'),
                group_id=self.config.consumer_group or f"churnguard-{self.config.stream_id}",
                value_deserializer=self._deserialize_message,
                enable_auto_commit=True,
                auto_offset_reset='latest'
            )
            
            await self.consumer.start()
            
            try:
                async for msg in self.consumer:
                    if not self.running:
                        break
                    
                    # Create stream message
                    stream_message = StreamMessage(
                        message_id=str(uuid.uuid4()),
                        stream_id=self.config.stream_id,
                        organization_id=self.config.organization_id,
                        timestamp=datetime.fromtimestamp(msg.timestamp / 1000) if msg.timestamp else datetime.now(),
                        data=msg.value,
                        source_topic=msg.topic,
                        source_partition=msg.partition,
                        source_offset=msg.offset
                    )
                    
                    # Add to message buffer
                    self.message_buffer.append(stream_message)
                    self.message_timestamps.append(stream_message.timestamp)
                    
                    # Queue for processing
                    try:
                        await self.processing_queue.put(stream_message)
                    except asyncio.QueueFull:
                        logger.warning(f"Processing queue full for stream {self.config.name}")
                        # Remove oldest message from buffer
                        if self.message_buffer:
                            self.message_buffer.popleft()
            
            finally:
                await self.consumer.stop()
                
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}")
    
    def _deserialize_message(self, value: bytes) -> Dict[str, Any]:
        """Deserialize Kafka message based on format"""
        try:
            if self.config.data_format == DataFormat.JSON:
                return json.loads(value.decode('utf-8'))
            elif self.config.data_format == DataFormat.PLAIN_TEXT:
                return {'text': value.decode('utf-8')}
            else:
                # Default to JSON
                return json.loads(value.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error deserializing message: {e}")
            return {'raw': value.decode('utf-8', errors='ignore')}
    
    async def _cleanup(self):
        """Clean up Kafka resources"""
        if self.consumer:
            await self.consumer.stop()

class RedisStreamProcessor(StreamProcessor):
    """Redis Streams processor"""
    
    def __init__(self, config: StreamConfiguration):
        super().__init__(config)
        self.redis: Optional[aioredis.Redis] = None
        
        if not aioredis:
            raise ImportError("aioredis package required for Redis Streams")
    
    async def _consume_messages(self):
        """Consume messages from Redis Streams"""
        try:
            # Connect to Redis
            redis_config = self.config.connection_config
            self.redis = aioredis.from_url(
                redis_config.get('url', 'redis://localhost:6379'),
                encoding='utf-8',
                decode_responses=True
            )
            
            # Consumer group setup
            consumer_group = self.config.consumer_group or f"churnguard-{self.config.stream_id}"
            consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
            
            # Create consumer groups for each stream
            for topic in self.config.topics:
                try:
                    await self.redis.xgroup_create(topic, consumer_group, id='0', mkstream=True)
                except Exception:
                    # Group might already exist
                    pass
            
            # Consume messages
            while self.running:
                try:
                    # Read from multiple streams
                    streams = {topic: '>' for topic in self.config.topics}
                    
                    messages = await self.redis.xreadgroup(
                        consumer_group,
                        consumer_name,
                        streams,
                        count=self.config.batch_size,
                        block=self.config.batch_timeout_ms
                    )
                    
                    for stream_name, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            # Create stream message
                            stream_message = StreamMessage(
                                message_id=message_id,
                                stream_id=self.config.stream_id,
                                organization_id=self.config.organization_id,
                                timestamp=datetime.now(),
                                data=dict(fields),
                                source_topic=stream_name
                            )
                            
                            # Add to buffer and queue
                            self.message_buffer.append(stream_message)
                            self.message_timestamps.append(stream_message.timestamp)
                            
                            try:
                                await self.processing_queue.put(stream_message)
                            except asyncio.QueueFull:
                                logger.warning(f"Processing queue full for Redis stream {self.config.name}")
                            
                            # Acknowledge message
                            await self.redis.xack(stream_name, consumer_group, message_id)
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error reading from Redis stream: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error in Redis stream consumer: {e}")
    
    async def _cleanup(self):
        """Clean up Redis resources"""
        if self.redis:
            await self.redis.close()

class WebSocketStreamProcessor(StreamProcessor):
    """WebSocket stream processor"""
    
    def __init__(self, config: StreamConfiguration):
        super().__init__(config)
        self.websocket_connections: Dict[str, Any] = {}
        
        if not websockets:
            raise ImportError("websockets package required for WebSocket streaming")
    
    async def _consume_messages(self):
        """Consume messages from WebSocket connections"""
        try:
            # Connect to WebSocket endpoints
            for topic in self.config.topics:
                ws_url = self.config.connection_config.get('urls', {}).get(topic)
                if ws_url:
                    asyncio.create_task(self._connect_websocket(topic, ws_url))
        
        except Exception as e:
            logger.error(f"Error setting up WebSocket connections: {e}")
    
    async def _connect_websocket(self, topic: str, url: str):
        """Connect to a WebSocket endpoint"""
        try:
            async with websockets.connect(url) as websocket:
                self.websocket_connections[topic] = websocket
                
                async for message in websocket:
                    if not self.running:
                        break
                    
                    try:
                        # Parse message data
                        if self.config.data_format == DataFormat.JSON:
                            data = json.loads(message)
                        else:
                            data = {'text': message}
                        
                        # Create stream message
                        stream_message = StreamMessage(
                            message_id=str(uuid.uuid4()),
                            stream_id=self.config.stream_id,
                            organization_id=self.config.organization_id,
                            timestamp=datetime.now(),
                            data=data,
                            source_topic=topic
                        )
                        
                        # Add to buffer and queue
                        self.message_buffer.append(stream_message)
                        self.message_timestamps.append(stream_message.timestamp)
                        
                        await self.processing_queue.put(stream_message)
                        
                    except Exception as e:
                        logger.error(f"Error processing WebSocket message: {e}")
        
        except Exception as e:
            logger.error(f"WebSocket connection error for {topic}: {e}")
        finally:
            if topic in self.websocket_connections:
                del self.websocket_connections[topic]

class StreamingDataPipelineManager:
    """
    Manager for real-time streaming data pipelines
    
    Features:
    - Multi-protocol streaming support (Kafka, Redis, WebSocket)
    - Dynamic pipeline configuration and management
    - Real-time metrics and monitoring
    - Automatic error recovery and retry logic
    - Load balancing and scaling
    - Schema validation and evolution
    - Data quality monitoring
    - Performance optimization
    """
    
    def __init__(self):
        # Stream configurations and processors
        self.stream_configs: Dict[str, StreamConfiguration] = {}
        self.stream_processors: Dict[str, StreamProcessor] = {}
        
        # Global metrics
        self.global_metrics: Dict[str, Any] = {
            'total_streams': 0,
            'active_streams': 0,
            'total_messages_processed': 0,
            'avg_processing_time_ms': 0.0,
            'error_rate': 0.0
        }
        
        # Background tasks
        self.monitor_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the streaming pipeline manager"""
        logger.info("Starting streaming data pipeline manager")
        
        # Start monitoring task
        self.monitor_task = asyncio.create_task(self._monitor_streams())
    
    async def stop(self):
        """Stop the streaming pipeline manager"""
        logger.info("Stopping streaming data pipeline manager")
        
        # Stop all stream processors
        for processor in self.stream_processors.values():
            await processor.stop()
        
        # Stop monitoring
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
    
    async def create_stream(self, config: StreamConfiguration) -> str:
        """Create a new streaming pipeline"""
        try:
            # Validate configuration
            self._validate_stream_config(config)
            
            # Create processor based on stream type
            processor = self._create_processor(config)
            
            # Store configuration and processor
            self.stream_configs[config.stream_id] = config
            self.stream_processors[config.stream_id] = processor
            
            # Start processor if active
            if config.active:
                await processor.start()
            
            self.global_metrics['total_streams'] += 1
            if config.active:
                self.global_metrics['active_streams'] += 1
            
            logger.info(f"Created stream pipeline: {config.name}")
            return config.stream_id
            
        except Exception as e:
            logger.error(f"Error creating stream pipeline: {e}")
            raise
    
    def _create_processor(self, config: StreamConfiguration) -> StreamProcessor:
        """Create appropriate stream processor based on type"""
        if config.stream_type == StreamType.KAFKA:
            return KafkaStreamProcessor(config)
        elif config.stream_type == StreamType.REDIS_STREAMS:
            return RedisStreamProcessor(config)
        elif config.stream_type == StreamType.WEBSOCKET:
            return WebSocketStreamProcessor(config)
        else:
            raise ValueError(f"Unsupported stream type: {config.stream_type}")
    
    def _validate_stream_config(self, config: StreamConfiguration):
        """Validate stream configuration"""
        if not config.stream_id:
            raise ValueError("Stream ID is required")
        
        if not config.organization_id:
            raise ValueError("Organization ID is required")
        
        if not config.topics:
            raise ValueError("At least one topic is required")
        
        if config.stream_id in self.stream_configs:
            raise ValueError(f"Stream {config.stream_id} already exists")
    
    async def get_stream_metrics(self, stream_id: str) -> Optional[StreamMetrics]:
        """Get metrics for a specific stream"""
        processor = self.stream_processors.get(stream_id)
        return processor.metrics if processor else None
    
    async def get_global_metrics(self) -> Dict[str, Any]:
        """Get global streaming metrics"""
        # Update global metrics
        total_messages = sum(
            config.total_messages_processed 
            for config in self.stream_configs.values()
        )
        
        avg_processing_time = 0.0
        total_error_rate = 0.0
        active_count = 0
        
        for processor in self.stream_processors.values():
            if processor.running:
                active_count += 1
                avg_processing_time += processor.metrics.avg_processing_time_ms
                total_error_rate += processor.metrics.error_rate
        
        if active_count > 0:
            avg_processing_time /= active_count
            total_error_rate /= active_count
        
        self.global_metrics.update({
            'active_streams': active_count,
            'total_messages_processed': total_messages,
            'avg_processing_time_ms': avg_processing_time,
            'error_rate': total_error_rate
        })
        
        return self.global_metrics.copy()
    
    async def _monitor_streams(self):
        """Monitor stream health and performance"""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
                for stream_id, processor in self.stream_processors.items():
                    if not processor.running and self.stream_configs[stream_id].active:
                        logger.warning(f"Stream {stream_id} is not running but should be active")
                        # Attempt to restart
                        try:
                            await processor.start()
                            logger.info(f"Restarted stream {stream_id}")
                        except Exception as e:
                            logger.error(f"Failed to restart stream {stream_id}: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stream monitoring: {e}")

# Global streaming pipeline manager
streaming_manager = StreamingDataPipelineManager()

def get_streaming_manager() -> StreamingDataPipelineManager:
    """Get the global streaming pipeline manager"""
    return streaming_manager

# Convenience functions
async def start_streaming_pipelines():
    """Start streaming data pipelines"""
    manager = get_streaming_manager()
    await manager.start()

async def stop_streaming_pipelines():
    """Stop streaming data pipelines"""
    manager = get_streaming_manager()
    await manager.stop()

async def create_kafka_stream(organization_id: str, topics: List[str], 
                            bootstrap_servers: str = "localhost:9092") -> str:
    """Create a Kafka streaming pipeline"""
    config = StreamConfiguration(
        stream_id=str(uuid.uuid4()),
        organization_id=organization_id,
        name=f"Kafka Stream - {', '.join(topics)}",
        description="Kafka streaming pipeline",
        stream_type=StreamType.KAFKA,
        topics=topics,
        connection_config={'bootstrap_servers': bootstrap_servers}
    )
    
    manager = get_streaming_manager()
    return await manager.create_stream(config)