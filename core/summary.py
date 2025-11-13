"""Daily aggregation and data retention management."""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional
from core.db import DatabaseManager

logger = logging.getLogger(__name__)


class SummaryManager:
    """Manages daily aggregation and data retention."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize summary manager.
        
        Args:
            db_manager: DatabaseManager instance (creates new if None)
        """
        self.db_manager = db_manager or DatabaseManager()
        self._running = False
        self._thread = None
        self._last_aggregation_date = None
        
    def start(self):
        """Start the summary management background task."""
        if self._running:
            logger.warning("Summary manager already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._management_loop, daemon=True)
        self._thread.start()
        logger.info("Summary manager started")
        
        # Run initial aggregation and cleanup
        self._check_and_aggregate()
        self._cleanup_old_data()
        
    def stop(self):
        """Stop the summary management task."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Summary manager stopped")
    
    def _management_loop(self):
        """Background loop for daily aggregation checks."""
        logger.info("Summary management loop started")
        
        while self._running:
            try:
                # Check every hour
                time.sleep(3600)
                
                # Check if we need to aggregate
                self._check_and_aggregate()
                
                # Run cleanup once per day (at 2 AM)
                current_hour = datetime.now().hour
                if current_hour == 2:
                    self._cleanup_old_data()
                    # Sleep for an hour to avoid running multiple times
                    time.sleep(3600)
                    
            except Exception as e:
                logger.error(f"Error in summary management loop: {e}")
                time.sleep(300)  # Sleep 5 minutes on error
    
    def _check_and_aggregate(self):
        """Check if daily aggregation is needed and perform it."""
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        
        # Check if we've already aggregated today
        if self._last_aggregation_date == today_str:
            return
        
        # Aggregate yesterday's data
        yesterday = today - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        try:
            logger.info(f"Aggregating data for {yesterday_str}")
            self.db_manager.aggregate_daily(yesterday_str)
            self._last_aggregation_date = today_str
            logger.info(f"Successfully aggregated data for {yesterday_str}")
            
        except Exception as e:
            logger.error(f"Error aggregating daily data: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old sample data based on retention policy."""
        try:
            logger.info("Running data retention cleanup")
            self.db_manager.cleanup_old_data()
            logger.info("Data retention cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
    
    def aggregate_date(self, date_str: str):
        """Manually aggregate data for a specific date.
        
        Args:
            date_str: Date string in 'YYYY-MM-DD' format
        """
        try:
            logger.info(f"Manually aggregating data for {date_str}")
            self.db_manager.aggregate_daily(date_str)
            logger.info(f"Successfully aggregated data for {date_str}")
            
        except Exception as e:
            logger.error(f"Error aggregating data for {date_str}: {e}")
            raise
    
    def aggregate_date_range(self, start_date: str, end_date: str):
        """Aggregate data for a range of dates.
        
        Args:
            start_date: Start date string in 'YYYY-MM-DD' format
            end_date: End date string in 'YYYY-MM-DD' format
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            try:
                self.aggregate_date(date_str)
            except Exception as e:
                logger.error(f"Failed to aggregate {date_str}: {e}")
            
            current += timedelta(days=1)
    
    def force_cleanup(self, retention_days: int = 90):
        """Force immediate cleanup of old data.
        
        Args:
            retention_days: Number of days to retain
        """
        try:
            logger.info(f"Force cleanup with {retention_days} days retention")
            self.db_manager.cleanup_old_data(retention_days)
            logger.info("Force cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during force cleanup: {e}")
            raise


class DataPersister:
    """Handles periodic persistence of network samples to database."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, 
                 persist_interval: int = 5):
        """Initialize data persister.
        
        Args:
            db_manager: DatabaseManager instance
            persist_interval: Interval in seconds to persist accumulated samples
        """
        self.db_manager = db_manager or DatabaseManager()
        self.persist_interval = persist_interval
        self._running = False
        self._thread = None
        self._sample_queue = []
        self._queue_lock = threading.Lock()
        
    def start(self):
        """Start the data persistence background task."""
        if self._running:
            logger.warning("Data persister already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._persistence_loop, daemon=True)
        self._thread.start()
        logger.info("Data persister started")
        
    def stop(self):
        """Stop the data persistence task and flush remaining samples."""
        if not self._running:
            return
        
        self._running = False
        
        # Flush remaining samples
        self._flush_samples()
        
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Data persister stopped")
    
    def add_sample(self, timestamp: int, pid: int, process_name: str,
                   app_name: Optional[str], bytes_sent: int, bytes_recv: int):
        """Add a sample to the persistence queue.
        
        Args:
            timestamp: Unix epoch timestamp
            pid: Process ID
            process_name: Process executable name
            app_name: Human-friendly application name
            bytes_sent: Bytes sent in this sample period
            bytes_recv: Bytes received in this sample period
        """
        with self._queue_lock:
            self._sample_queue.append((
                timestamp, pid, process_name, app_name, bytes_sent, bytes_recv
            ))
    
    def add_snapshot(self, snapshot: dict, timestamp: Optional[int] = None):
        """Add a complete snapshot to the persistence queue.
        
        Args:
            snapshot: Network usage snapshot from NetworkMonitor
            timestamp: Unix epoch timestamp (uses current time if None)
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        for pid, data in snapshot.items():
            # Only persist samples with actual activity
            if data.get('bytes_sent', 0) > 0 or data.get('bytes_recv', 0) > 0:
                self.add_sample(
                    timestamp=timestamp,
                    pid=pid,
                    process_name=data.get('process_name', 'Unknown'),
                    app_name=data.get('app_name'),
                    bytes_sent=data.get('bytes_sent', 0),
                    bytes_recv=data.get('bytes_recv', 0)
                )
    
    def _persistence_loop(self):
        """Background loop for periodic sample persistence."""
        logger.info("Data persistence loop started")
        
        while self._running:
            try:
                time.sleep(self.persist_interval)
                self._flush_samples()
                
            except Exception as e:
                logger.error(f"Error in persistence loop: {e}")
                time.sleep(self.persist_interval)
    
    def _flush_samples(self):
        """Flush accumulated samples to database."""
        with self._queue_lock:
            if not self._sample_queue:
                return
            
            samples_to_write = self._sample_queue.copy()
            self._sample_queue.clear()
        
        try:
            self.db_manager.insert_samples_batch(samples_to_write)
            logger.debug(f"Persisted {len(samples_to_write)} samples to database")
            
        except Exception as e:
            logger.error(f"Error persisting samples: {e}")
            # Re-add samples to queue on error (but limit queue size)
            with self._queue_lock:
                self._sample_queue.extend(samples_to_write[-1000:])  # Keep last 1000
