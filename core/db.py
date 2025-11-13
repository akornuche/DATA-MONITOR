"""Database operations for network usage monitoring."""
import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'usage.db')
RETENTION_DAYS = 90


class DatabaseManager:
    """Manages SQLite database operations for network usage tracking."""
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.ensure_schema()
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def ensure_schema(self):
        """Create database schema if it doesn't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create sample table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sample (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    pid INTEGER NOT NULL,
                    process_name TEXT NOT NULL,
                    app_name TEXT,
                    bytes_sent INTEGER NOT NULL,
                    bytes_recv INTEGER NOT NULL
                )
            """)
            
            # Create indexes on sample table
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sample_timestamp 
                ON sample(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sample_pid 
                ON sample(pid)
            """)
            
            # Create daily summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    app_name TEXT NOT NULL,
                    bytes_sent INTEGER NOT NULL,
                    bytes_recv INTEGER NOT NULL
                )
            """)
            
            # Create unique index on daily summary
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_app 
                ON daily_summary(date, app_name)
            """)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error creating schema: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def insert_sample(self, timestamp: int, pid: int, process_name: str, 
                     app_name: Optional[str], bytes_sent: int, bytes_recv: int):
        """Insert a sample record.
        
        Args:
            timestamp: Unix epoch timestamp
            pid: Process ID
            process_name: Process executable name
            app_name: Human-friendly application name
            bytes_sent: Bytes sent in this sample period
            bytes_recv: Bytes received in this sample period
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO sample (timestamp, pid, process_name, app_name, 
                                  bytes_sent, bytes_recv)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, pid, process_name, app_name, bytes_sent, bytes_recv))
            
            conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Error inserting sample: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def insert_samples_batch(self, samples: List[Tuple]):
        """Insert multiple samples in a batch.
        
        Args:
            samples: List of tuples (timestamp, pid, process_name, app_name, 
                                    bytes_sent, bytes_recv)
        """
        if not samples:
            return
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.executemany("""
                INSERT INTO sample (timestamp, pid, process_name, app_name, 
                                  bytes_sent, bytes_recv)
                VALUES (?, ?, ?, ?, ?, ?)
            """, samples)
            
            conn.commit()
            logger.debug(f"Inserted {len(samples)} samples")
            
        except sqlite3.Error as e:
            logger.error(f"Error inserting batch samples: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_samples_for_range(self, start_ts: int, end_ts: int) -> List[Dict]:
        """Get samples within a time range.
        
        Args:
            start_ts: Start timestamp (Unix epoch)
            end_ts: End timestamp (Unix epoch)
            
        Returns:
            List of sample dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, timestamp, pid, process_name, app_name, 
                       bytes_sent, bytes_recv
                FROM sample
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            """, (start_ts, end_ts))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching samples: {e}")
            raise
        finally:
            conn.close()
    
    def aggregate_daily(self, date: str):
        """Aggregate samples for a specific date into daily summary.
        
        Args:
            date: Date string in 'YYYY-MM-DD' format
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Parse date to get timestamp range
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            start_ts = int(date_obj.timestamp())
            end_ts = start_ts + 86400  # +24 hours
            
            # Delete existing summary for this date
            cursor.execute("""
                DELETE FROM daily_summary WHERE date = ?
            """, (date,))
            
            # Aggregate by app_name
            cursor.execute("""
                INSERT INTO daily_summary (date, app_name, bytes_sent, bytes_recv)
                SELECT 
                    ? as date,
                    COALESCE(app_name, process_name) as app_name,
                    SUM(bytes_sent) as bytes_sent,
                    SUM(bytes_recv) as bytes_recv
                FROM sample
                WHERE timestamp >= ? AND timestamp < ?
                GROUP BY COALESCE(app_name, process_name)
            """, (date, start_ts, end_ts))
            
            conn.commit()
            logger.info(f"Aggregated daily summary for {date}")
            
        except sqlite3.Error as e:
            logger.error(f"Error aggregating daily summary: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_daily_summary(self, date: str) -> List[Dict]:
        """Get daily summary for a specific date.
        
        Args:
            date: Date string in 'YYYY-MM-DD' format
            
        Returns:
            List of summary dictionaries with app_name and byte totals
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT app_name, bytes_sent, bytes_recv,
                       (bytes_sent + bytes_recv) as total_bytes
                FROM daily_summary
                WHERE date = ?
                ORDER BY total_bytes DESC
            """, (date,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching daily summary: {e}")
            raise
        finally:
            conn.close()
    
    def cleanup_old_data(self, retention_days: int = RETENTION_DAYS):
        """Remove samples older than retention period.
        
        Args:
            retention_days: Number of days to retain data
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_ts = int(cutoff_date.timestamp())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM sample WHERE timestamp < ?
            """, (cutoff_ts,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old sample records")
                
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old data: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_available_dates(self) -> List[str]:
        """Get list of dates that have data in daily_summary.
        
        Returns:
            List of date strings in 'YYYY-MM-DD' format
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT date
                FROM daily_summary
                ORDER BY date DESC
            """)
            
            rows = cursor.fetchall()
            return [row['date'] for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching available dates: {e}")
            raise
        finally:
            conn.close()
