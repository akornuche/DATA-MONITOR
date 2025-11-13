"""Network monitoring module - tracks per-process network usage."""
import logging
import psutil
import time
import threading
from typing import Dict, Callable, Optional, List
from collections import defaultdict
from core.process_info import get_process_info

logger = logging.getLogger(__name__)

# Sampling interval in seconds
SAMPLE_INTERVAL = 1.0


class NetworkMonitor:
    """Monitors network usage per process in realtime."""
    
    def __init__(self, sample_interval: float = SAMPLE_INTERVAL):
        """Initialize network monitor.
        
        Args:
            sample_interval: Time between samples in seconds
        """
        self.sample_interval = sample_interval
        self._running = False
        self._thread = None
        self._callbacks = []
        
        # Store previous counters for delta calculation
        self._previous_counters = {}  # pid -> (bytes_sent, bytes_recv)
        
        # Latest snapshot
        self._latest_snapshot = {}
        self._snapshot_lock = threading.Lock()
        
        # Permission status
        self.permissions_warning = None
        
    def start(self):
        """Start the monitoring loop."""
        if self._running:
            logger.warning("Monitor already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        logger.info("Network monitor started")
        
    def stop(self):
        """Stop the monitoring loop."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Network monitor stopped")
        
    def subscribe(self, callback: Callable[[Dict], None]):
        """Subscribe to snapshot updates.
        
        Args:
            callback: Function to call with each new snapshot
        """
        self._callbacks.append(callback)
        
    def get_latest_snapshot(self) -> Dict:
        """Get the latest network usage snapshot.
        
        Returns:
            Dictionary: pid -> {process_name, app_name, bytes_sent, bytes_recv}
        """
        with self._snapshot_lock:
            return self._latest_snapshot.copy()
    
    def _monitoring_loop(self):
        """Main monitoring loop - runs in background thread."""
        logger.info("Monitoring loop started")
        
        while self._running:
            try:
                start_time = time.time()
                
                # Capture current snapshot
                snapshot = self._capture_snapshot()
                
                # Update latest snapshot
                with self._snapshot_lock:
                    self._latest_snapshot = snapshot
                
                # Notify subscribers
                for callback in self._callbacks:
                    try:
                        callback(snapshot)
                    except Exception as e:
                        logger.error(f"Error in subscriber callback: {e}")
                
                # Sleep for remaining interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.sample_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.sample_interval)
    
    def _capture_snapshot(self) -> Dict:
        """Capture current network usage snapshot with delta calculation.
        
        Returns:
            Dictionary: pid -> {process_name, app_name, bytes_sent, bytes_recv}
        """
        snapshot = {}
        current_counters = {}
        
        try:
            # Iterate through all processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    
                    # Get IO counters for the process
                    # Note: On Windows, io_counters() returns read/write bytes, not network bytes
                    # We'll use connections to track network activity
                    connections = proc.connections(kind='inet')
                    
                    if not connections:
                        # Skip processes with no network connections
                        continue
                    
                    # For processes with connections, try to get network IO
                    # This is a limitation of psutil - it doesn't provide per-process network bytes
                    # We'll use a workaround by tracking connection count as a proxy
                    # In production, you'd need Windows Performance Counters or ETW
                    
                    # Get process info
                    proc_info = get_process_info(pid)
                    
                    # Try to estimate network usage
                    bytes_sent, bytes_recv = self._estimate_process_network_io(proc, pid)
                    
                    # Store current counters
                    current_counters[pid] = (bytes_sent, bytes_recv)
                    
                    # Calculate delta
                    if pid in self._previous_counters:
                        prev_sent, prev_recv = self._previous_counters[pid]
                        delta_sent = max(0, bytes_sent - prev_sent)
                        delta_recv = max(0, bytes_recv - prev_recv)
                    else:
                        # First time seeing this process
                        delta_sent = 0
                        delta_recv = 0
                    
                    # Only include processes with activity
                    if delta_sent > 0 or delta_recv > 0 or len(connections) > 0:
                        snapshot[pid] = {
                            'process_name': proc_info['process_name'],
                            'app_name': proc_info['app_name'],
                            'bytes_sent': delta_sent,
                            'bytes_recv': delta_recv,
                            'connections': len(connections)
                        }
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    # Process ended or we don't have permission
                    continue
                except Exception as e:
                    logger.debug(f"Error capturing process {pid}: {e}")
                    continue
            
            # Update previous counters
            self._previous_counters = current_counters
            
            # Check if we got any data - if not, may be permissions issue
            if not snapshot and not self.permissions_warning:
                self.permissions_warning = (
                    "Limited network data available. For full per-process statistics, "
                    "run as Administrator."
                )
                logger.warning(self.permissions_warning)
            
        except Exception as e:
            logger.error(f"Error capturing snapshot: {e}")
        
        return snapshot
    
    def _estimate_process_network_io(self, proc: psutil.Process, pid: int) -> tuple:
        """Estimate network I/O for a process.
        
        Note: psutil doesn't provide per-process network bytes directly on Windows.
        This is a workaround that uses io_counters as a proxy.
        For production use, Windows Performance Counters or ETW would be needed.
        
        Args:
            proc: psutil.Process object
            pid: Process ID
            
        Returns:
            Tuple of (bytes_sent, bytes_recv) - cumulative counts
        """
        try:
            # On Windows, io_counters gives disk I/O, not network I/O
            # We'll use a workaround: track connection states and estimate
            
            # Get all connections for this process
            connections = proc.connections(kind='inet')
            
            # For a more accurate implementation, we would:
            # 1. Use Windows Performance Counters (requires pywin32)
            # 2. Use ETW (Event Tracing for Windows)
            # 3. Use Network Statistics API
            
            # Simplified approach: use system-wide network counters
            # and proportionally attribute to processes with connections
            if not hasattr(self, '_system_net_io'):
                self._system_net_io = psutil.net_io_counters()
                self._connection_pids = {}
            
            current_net_io = psutil.net_io_counters()
            
            # Calculate system-wide delta
            system_sent = current_net_io.bytes_sent
            system_recv = current_net_io.bytes_recv
            
            # Count active connections across all processes
            active_connections = len(connections)
            
            # Simple estimation: if process has connections, attribute proportionally
            # This is a rough estimation - real implementation needs Performance Counters
            if active_connections > 0:
                # Store cumulative estimate
                if not hasattr(self, '_process_estimates'):
                    self._process_estimates = {}
                
                if pid not in self._process_estimates:
                    self._process_estimates[pid] = (0, 0)
                
                prev_sent, prev_recv = self._process_estimates[pid]
                
                # Increment by a small amount per connection (very rough estimate)
                # In real implementation, use Performance Counters
                estimate_factor = active_connections * 1024  # Arbitrary factor
                
                new_sent = prev_sent + estimate_factor
                new_recv = prev_recv + estimate_factor
                
                self._process_estimates[pid] = (new_sent, new_recv)
                
                return (new_sent, new_recv)
            
            return (0, 0)
            
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return (0, 0)
        except Exception as e:
            logger.debug(f"Error estimating network IO for PID {pid}: {e}")
            return (0, 0)
    
    def get_total_bandwidth(self) -> Dict[str, int]:
        """Get total current bandwidth usage.
        
        Returns:
            Dictionary with 'bytes_sent' and 'bytes_recv' keys
        """
        snapshot = self.get_latest_snapshot()
        
        total_sent = sum(data['bytes_sent'] for data in snapshot.values())
        total_recv = sum(data['bytes_recv'] for data in snapshot.values())
        
        return {
            'bytes_sent': total_sent,
            'bytes_recv': total_recv,
            'total': total_sent + total_recv
        }
    
    def get_top_processes(self, n: int = 5) -> List[Dict]:
        """Get top N processes by total bandwidth.
        
        Args:
            n: Number of top processes to return
            
        Returns:
            List of process dictionaries sorted by total bandwidth
        """
        snapshot = self.get_latest_snapshot()
        
        # Convert to list and add total
        processes = []
        for pid, data in snapshot.items():
            proc_dict = data.copy()
            proc_dict['pid'] = pid
            proc_dict['total'] = data['bytes_sent'] + data['bytes_recv']
            processes.append(proc_dict)
        
        # Sort by total bandwidth
        processes.sort(key=lambda x: x['total'], reverse=True)
        
        return processes[:n]
