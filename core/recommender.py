"""Rules-based recommendations engine for reducing data consumption."""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Default threshold for high bandwidth (5 MB/s)
DEFAULT_HIGH_BANDWIDTH_THRESHOLD = 5 * 1024 * 1024  # bytes/s

# Background sync services to monitor
SYNC_SERVICES = [
    'onedrive', 'dropbox', 'googledrivesync', 'google drive',
    'icloud', 'sync', 'backup', 'megasync', 'pcloud'
]

# System processes that may consume bandwidth
SYSTEM_PROCESSES = [
    'svchost', 'system', 'windows update', 'wuauclt',
    'trustedinstaller', 'tiworker'
]


class UsageRecommender:
    """Generates recommendations for reducing network data consumption."""
    
    def __init__(self, high_bandwidth_threshold: int = DEFAULT_HIGH_BANDWIDTH_THRESHOLD):
        """Initialize recommender.
        
        Args:
            high_bandwidth_threshold: Threshold in bytes/s for high bandwidth alert
        """
        self.high_bandwidth_threshold = high_bandwidth_threshold
        
    def get_recommendations(self, snapshot: Dict, total_usage: Dict[str, int]) -> List[str]:
        """Generate recommendations based on current usage.
        
        Args:
            snapshot: Current network usage snapshot from NetworkMonitor
            total_usage: Total bandwidth usage (bytes_sent, bytes_recv, total)
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not snapshot or total_usage.get('total', 0) == 0:
            return recommendations
        
        total_bandwidth = total_usage['total']
        
        # Calculate per-app usage and percentages
        app_usage = self._aggregate_by_app(snapshot)
        
        # Rule 1: Single app using > 50% of bandwidth
        high_usage_apps = self._check_high_usage_apps(app_usage, total_bandwidth)
        recommendations.extend(high_usage_apps)
        
        # Rule 2: Background sync services using > 20%
        sync_recommendations = self._check_sync_services(app_usage, total_bandwidth)
        recommendations.extend(sync_recommendations)
        
        # Rule 3: System processes using high bandwidth
        system_recommendations = self._check_system_processes(app_usage, total_bandwidth)
        recommendations.extend(system_recommendations)
        
        # Rule 4: Total bandwidth exceeds threshold
        threshold_recommendations = self._check_bandwidth_threshold(total_bandwidth)
        recommendations.extend(threshold_recommendations)
        
        # Rule 5: Multiple high-bandwidth processes
        multi_app_recommendations = self._check_multiple_apps(app_usage, total_bandwidth)
        recommendations.extend(multi_app_recommendations)
        
        return recommendations
    
    def _aggregate_by_app(self, snapshot: Dict) -> Dict[str, Dict]:
        """Aggregate usage by application name.
        
        Args:
            snapshot: Process snapshot dictionary
            
        Returns:
            Dictionary: app_name -> {bytes_sent, bytes_recv, total, pids}
        """
        app_usage = {}
        
        for pid, data in snapshot.items():
            app_name = data.get('app_name', 'Unknown')
            
            if app_name not in app_usage:
                app_usage[app_name] = {
                    'bytes_sent': 0,
                    'bytes_recv': 0,
                    'total': 0,
                    'pids': []
                }
            
            app_usage[app_name]['bytes_sent'] += data.get('bytes_sent', 0)
            app_usage[app_name]['bytes_recv'] += data.get('bytes_recv', 0)
            app_usage[app_name]['total'] += (data.get('bytes_sent', 0) + 
                                            data.get('bytes_recv', 0))
            app_usage[app_name]['pids'].append(pid)
        
        return app_usage
    
    def _check_high_usage_apps(self, app_usage: Dict, total_bandwidth: int) -> List[str]:
        """Check for apps using > 50% of bandwidth.
        
        Args:
            app_usage: Aggregated app usage
            total_bandwidth: Total bandwidth usage
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if total_bandwidth == 0:
            return recommendations
        
        for app_name, usage in app_usage.items():
            percentage = (usage['total'] / total_bandwidth) * 100
            
            if percentage > 50:
                mb_per_sec = usage['total'] / (1024 * 1024)
                
                recommendation = (
                    f"⚠️ {app_name} is using {percentage:.0f}% of bandwidth "
                    f"({mb_per_sec:.2f} MB/s). "
                )
                
                # Add specific action based on app type
                app_lower = app_name.lower()
                if 'chrome' in app_lower or 'firefox' in app_lower or 'edge' in app_lower:
                    recommendation += "Consider pausing video playback or closing unused tabs."
                elif 'steam' in app_lower or 'epic' in app_lower or 'origin' in app_lower:
                    recommendation += "Pause game downloads or updates."
                elif 'torrent' in app_lower or 'utorrent' in app_lower or 'bittorrent' in app_lower:
                    recommendation += "Pause or limit torrent downloads."
                else:
                    recommendation += "Consider closing or limiting this application."
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def _check_sync_services(self, app_usage: Dict, total_bandwidth: int) -> List[str]:
        """Check for background sync services using > 20%.
        
        Args:
            app_usage: Aggregated app usage
            total_bandwidth: Total bandwidth usage
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if total_bandwidth == 0:
            return recommendations
        
        sync_total = 0
        sync_apps = []
        
        for app_name, usage in app_usage.items():
            app_lower = app_name.lower()
            if any(service in app_lower for service in SYNC_SERVICES):
                sync_total += usage['total']
                sync_apps.append(app_name)
        
        if sync_total > 0:
            percentage = (sync_total / total_bandwidth) * 100
            
            if percentage > 20:
                mb_per_sec = sync_total / (1024 * 1024)
                apps_str = ', '.join(sync_apps)
                
                recommendation = (
                    f"💾 Background sync services ({apps_str}) are using "
                    f"{percentage:.0f}% of bandwidth ({mb_per_sec:.2f} MB/s). "
                    f"Consider pausing cloud sync temporarily."
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _check_system_processes(self, app_usage: Dict, total_bandwidth: int) -> List[str]:
        """Check for system processes using significant bandwidth.
        
        Args:
            app_usage: Aggregated app usage
            total_bandwidth: Total bandwidth usage
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if total_bandwidth == 0:
            return recommendations
        
        for app_name, usage in app_usage.items():
            app_lower = app_name.lower()
            
            if any(proc in app_lower for proc in SYSTEM_PROCESSES):
                percentage = (usage['total'] / total_bandwidth) * 100
                
                if percentage > 15:
                    mb_per_sec = usage['total'] / (1024 * 1024)
                    
                    recommendation = (
                        f"🖥️ System process ({app_name}) is using {percentage:.0f}% "
                        f"of bandwidth ({mb_per_sec:.2f} MB/s). "
                        f"This may be Windows Update or system maintenance. "
                        f"Check Windows Update settings to defer updates."
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _check_bandwidth_threshold(self, total_bandwidth: int) -> List[str]:
        """Check if total bandwidth exceeds user threshold.
        
        Args:
            total_bandwidth: Total bandwidth usage
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if total_bandwidth > self.high_bandwidth_threshold:
            mb_per_sec = total_bandwidth / (1024 * 1024)
            threshold_mb = self.high_bandwidth_threshold / (1024 * 1024)
            
            recommendation = (
                f"📊 High bandwidth usage detected: {mb_per_sec:.2f} MB/s "
                f"(threshold: {threshold_mb:.2f} MB/s). "
                f"Consider enabling data saver mode in browsers and streaming apps."
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _check_multiple_apps(self, app_usage: Dict, total_bandwidth: int) -> List[str]:
        """Check for multiple apps each using moderate bandwidth.
        
        Args:
            app_usage: Aggregated app usage
            total_bandwidth: Total bandwidth usage
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if total_bandwidth == 0:
            return recommendations
        
        # Find apps using 10-50% each
        moderate_apps = []
        for app_name, usage in app_usage.items():
            percentage = (usage['total'] / total_bandwidth) * 100
            if 10 <= percentage <= 50:
                moderate_apps.append((app_name, percentage, usage['total']))
        
        if len(moderate_apps) >= 3:
            mb_per_sec_total = sum(u[2] for u in moderate_apps) / (1024 * 1024)
            apps_str = ', '.join(f"{name} ({pct:.0f}%)" for name, pct, _ in moderate_apps[:3])
            
            recommendation = (
                f"📱 Multiple applications are actively using bandwidth: {apps_str}. "
                f"Combined usage: {mb_per_sec_total:.2f} MB/s. "
                f"Consider closing non-essential applications."
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def set_threshold(self, threshold: int):
        """Update the high bandwidth threshold.
        
        Args:
            threshold: New threshold in bytes/s
        """
        self.high_bandwidth_threshold = threshold
        logger.info(f"Updated bandwidth threshold to {threshold / (1024 * 1024):.2f} MB/s")
