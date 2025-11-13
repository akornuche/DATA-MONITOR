"""Unit tests for database operations."""
import pytest
import os
import tempfile
from datetime import datetime, timedelta
from core.db import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = DatabaseManager(path)
    yield db
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


def test_schema_creation(temp_db):
    """Test that schema is created correctly."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    
    # Check sample table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sample'")
    assert cursor.fetchone() is not None
    
    # Check daily_summary table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_summary'")
    assert cursor.fetchone() is not None
    
    conn.close()


def test_insert_sample(temp_db):
    """Test inserting a sample record."""
    timestamp = int(datetime.now().timestamp())
    
    temp_db.insert_sample(
        timestamp=timestamp,
        pid=1234,
        process_name='test.exe',
        app_name='Test App',
        bytes_sent=1024,
        bytes_recv=2048
    )
    
    # Verify insertion
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sample")
    count = cursor.fetchone()[0]
    assert count == 1
    
    cursor.execute("SELECT * FROM sample WHERE pid=1234")
    row = cursor.fetchone()
    assert row['process_name'] == 'test.exe'
    assert row['app_name'] == 'Test App'
    assert row['bytes_sent'] == 1024
    assert row['bytes_recv'] == 2048
    
    conn.close()


def test_insert_samples_batch(temp_db):
    """Test batch insertion of samples."""
    timestamp = int(datetime.now().timestamp())
    
    samples = [
        (timestamp, 1, 'app1.exe', 'App 1', 100, 200),
        (timestamp, 2, 'app2.exe', 'App 2', 300, 400),
        (timestamp, 3, 'app3.exe', 'App 3', 500, 600),
    ]
    
    temp_db.insert_samples_batch(samples)
    
    # Verify
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sample")
    count = cursor.fetchone()[0]
    assert count == 3
    conn.close()


def test_get_samples_for_range(temp_db):
    """Test retrieving samples for a time range."""
    base_time = int(datetime.now().timestamp())
    
    # Insert samples at different times
    for i in range(10):
        temp_db.insert_sample(
            timestamp=base_time + i,
            pid=1000 + i,
            process_name=f'app{i}.exe',
            app_name=f'App {i}',
            bytes_sent=100 * i,
            bytes_recv=200 * i
        )
    
    # Get samples for middle range
    samples = temp_db.get_samples_for_range(base_time + 3, base_time + 7)
    
    assert len(samples) == 5
    assert samples[0]['pid'] == 1003
    assert samples[4]['pid'] == 1007


def test_aggregate_daily(temp_db):
    """Test daily aggregation."""
    # Create a specific date
    test_date = datetime(2024, 1, 15)
    base_timestamp = int(test_date.timestamp())
    
    # Insert samples for that day with same app name
    for i in range(10):
        temp_db.insert_sample(
            timestamp=base_timestamp + i * 3600,  # Each hour
            pid=1000,
            process_name='chrome.exe',
            app_name='Chrome',
            bytes_sent=1024,
            bytes_recv=2048
        )
    
    # Aggregate
    date_str = test_date.strftime('%Y-%m-%d')
    temp_db.aggregate_daily(date_str)
    
    # Verify
    summary = temp_db.get_daily_summary(date_str)
    assert len(summary) == 1
    assert summary[0]['app_name'] == 'Chrome'
    assert summary[0]['bytes_sent'] == 10240  # 1024 * 10
    assert summary[0]['bytes_recv'] == 20480  # 2048 * 10


def test_get_daily_summary(temp_db):
    """Test retrieving daily summary."""
    date_str = '2024-01-15'
    
    # Insert summary data directly
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO daily_summary (date, app_name, bytes_sent, bytes_recv)
        VALUES (?, ?, ?, ?)
    """, (date_str, 'App1', 1000, 2000))
    cursor.execute("""
        INSERT INTO daily_summary (date, app_name, bytes_sent, bytes_recv)
        VALUES (?, ?, ?, ?)
    """, (date_str, 'App2', 3000, 4000))
    conn.commit()
    conn.close()
    
    # Retrieve
    summary = temp_db.get_daily_summary(date_str)
    assert len(summary) == 2
    
    # Should be sorted by total (desc)
    assert summary[0]['app_name'] == 'App2'
    assert summary[0]['total_bytes'] == 7000
    assert summary[1]['app_name'] == 'App1'
    assert summary[1]['total_bytes'] == 3000


def test_cleanup_old_data(temp_db):
    """Test data retention cleanup."""
    now = datetime.now()
    
    # Insert old samples (100 days ago)
    old_timestamp = int((now - timedelta(days=100)).timestamp())
    for i in range(5):
        temp_db.insert_sample(
            timestamp=old_timestamp + i,
            pid=1000,
            process_name='old.exe',
            app_name='Old App',
            bytes_sent=100,
            bytes_recv=200
        )
    
    # Insert recent samples (10 days ago)
    recent_timestamp = int((now - timedelta(days=10)).timestamp())
    for i in range(5):
        temp_db.insert_sample(
            timestamp=recent_timestamp + i,
            pid=2000,
            process_name='new.exe',
            app_name='New App',
            bytes_sent=300,
            bytes_recv=400
        )
    
    # Cleanup with 90 day retention
    temp_db.cleanup_old_data(retention_days=90)
    
    # Verify old data removed, recent data retained
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sample")
    count = cursor.fetchone()[0]
    assert count == 5  # Only recent samples remain
    
    cursor.execute("SELECT process_name FROM sample LIMIT 1")
    row = cursor.fetchone()
    assert row['process_name'] == 'new.exe'
    
    conn.close()


def test_get_available_dates(temp_db):
    """Test retrieving available dates."""
    # Insert summaries for different dates
    dates = ['2024-01-15', '2024-01-16', '2024-01-17']
    
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    for date in dates:
        cursor.execute("""
            INSERT INTO daily_summary (date, app_name, bytes_sent, bytes_recv)
            VALUES (?, ?, ?, ?)
        """, (date, 'TestApp', 1000, 2000))
    conn.commit()
    conn.close()
    
    # Get available dates
    available = temp_db.get_available_dates()
    assert len(available) == 3
    assert '2024-01-15' in available
    assert '2024-01-16' in available
    assert '2024-01-17' in available
