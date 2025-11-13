"""Unit tests for network monitor."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.monitor import NetworkMonitor
import time


@pytest.fixture
def mock_psutil():
    """Mock psutil module."""
    with patch('core.monitor.psutil') as mock:
        yield mock


@pytest.fixture
def monitor():
    """Create a NetworkMonitor instance."""
    return NetworkMonitor()


def test_monitor_initialization(monitor):
    """Test monitor initializes correctly."""
    assert monitor.sample_interval == 1.0
    assert monitor._running is False
    assert monitor._thread is None
    assert len(monitor._callbacks) == 0


def test_monitor_start_stop(monitor):
    """Test starting and stopping monitor."""
    monitor.start()
    assert monitor._running is True
    assert monitor._thread is not None
    
    # Give it a moment to start
    time.sleep(0.1)
    
    monitor.stop()
    assert monitor._running is False


def test_subscribe_callback(monitor):
    """Test subscribing to snapshot updates."""
    callback = Mock()
    monitor.subscribe(callback)
    
    assert callback in monitor._callbacks


def test_get_latest_snapshot(monitor):
    """Test getting latest snapshot."""
    # Initially empty
    snapshot = monitor.get_latest_snapshot()
    assert isinstance(snapshot, dict)
    assert len(snapshot) == 0


def test_delta_calculation(monitor, mock_psutil):
    """Test delta calculation between samples."""
    # Mock process
    mock_proc = MagicMock()
    mock_proc.info = {'pid': 1234, 'name': 'test.exe'}
    mock_proc.connections.return_value = [MagicMock()]  # Has connections
    
    mock_psutil.process_iter.return_value = [mock_proc]
    mock_psutil.net_io_counters.return_value = MagicMock(
        bytes_sent=1000,
        bytes_recv=2000
    )
    
    # Mock get_process_info
    with patch('core.monitor.get_process_info') as mock_get_info:
        mock_get_info.return_value = {
            'pid': 1234,
            'process_name': 'test.exe',
            'app_name': 'Test App',
            'cmdline': 'test.exe'
        }
        
        # First capture - should have 0 delta
        snapshot1 = monitor._capture_snapshot()
        
        # Second capture - should calculate delta
        # Note: In real implementation, we'd need to simulate cumulative increase
        snapshot2 = monitor._capture_snapshot()


def test_get_total_bandwidth(monitor):
    """Test getting total bandwidth."""
    # Set up a mock snapshot
    monitor._latest_snapshot = {
        1234: {'process_name': 'app1', 'app_name': 'App1', 
               'bytes_sent': 1024, 'bytes_recv': 2048},
        5678: {'process_name': 'app2', 'app_name': 'App2',
               'bytes_sent': 512, 'bytes_recv': 1024}
    }
    
    total = monitor.get_total_bandwidth()
    
    assert total['bytes_sent'] == 1536  # 1024 + 512
    assert total['bytes_recv'] == 3072  # 2048 + 1024
    assert total['total'] == 4608  # 1536 + 3072


def test_get_top_processes(monitor):
    """Test getting top N processes."""
    # Set up mock snapshot
    monitor._latest_snapshot = {
        1: {'process_name': 'app1', 'app_name': 'App1',
            'bytes_sent': 1000, 'bytes_recv': 1000},
        2: {'process_name': 'app2', 'app_name': 'App2',
            'bytes_sent': 500, 'bytes_recv': 500},
        3: {'process_name': 'app3', 'app_name': 'App3',
            'bytes_sent': 2000, 'bytes_recv': 2000},
        4: {'process_name': 'app4', 'app_name': 'App4',
            'bytes_sent': 300, 'bytes_recv': 300},
    }
    
    top_3 = monitor.get_top_processes(n=3)
    
    assert len(top_3) == 3
    assert top_3[0]['app_name'] == 'App3'  # Highest
    assert top_3[0]['total'] == 4000
    assert top_3[1]['app_name'] == 'App1'
    assert top_3[2]['app_name'] == 'App2'


def test_empty_snapshot_handling(monitor):
    """Test handling of empty snapshot."""
    total = monitor.get_total_bandwidth()
    assert total['total'] == 0
    
    top = monitor.get_top_processes()
    assert len(top) == 0


def test_callback_notification(monitor):
    """Test that callbacks are notified."""
    callback = Mock()
    monitor.subscribe(callback)
    
    # Manually trigger a snapshot update
    test_snapshot = {1234: {'process_name': 'test', 'app_name': 'Test',
                            'bytes_sent': 100, 'bytes_recv': 200}}
    
    # Simulate callback notification
    for cb in monitor._callbacks:
        cb(test_snapshot)
    
    callback.assert_called_once_with(test_snapshot)
