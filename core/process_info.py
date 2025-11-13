"""Process information resolver - maps PIDs to process and application names."""
import logging
import psutil
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Windows-specific imports for product name extraction
try:
    import win32api
    import win32con
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False
    logger.warning("win32api not available - app names will be limited to process names")


class ProcessInfoResolver:
    """Resolves process information from PIDs."""
    
    def __init__(self):
        """Initialize process info resolver."""
        self._cache = {}  # Cache: pid -> info dict
        
    def get_process_info(self, pid: int) -> Dict:
        """Get process information for a given PID.
        
        Args:
            pid: Process ID
            
        Returns:
            Dictionary with keys: pid, process_name, app_name, cmdline
        """
        # Check cache first
        if pid in self._cache:
            return self._cache[pid]
        
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            
            # Try to get executable path for app name resolution
            try:
                exe_path = process.exe()
                app_name = self._resolve_app_name(exe_path, process_name)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                app_name = process_name
                exe_path = None
            
            # Get command line
            try:
                cmdline = ' '.join(process.cmdline())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                cmdline = ''
            
            info = {
                'pid': pid,
                'process_name': process_name,
                'app_name': app_name,
                'cmdline': cmdline
            }
            
            # Cache the result
            self._cache[pid] = info
            return info
            
        except psutil.NoSuchProcess:
            # Process no longer exists
            return {
                'pid': pid,
                'process_name': 'Unknown',
                'app_name': 'Unknown',
                'cmdline': ''
            }
        except Exception as e:
            logger.error(f"Error getting process info for PID {pid}: {e}")
            return {
                'pid': pid,
                'process_name': 'Error',
                'app_name': 'Error',
                'cmdline': ''
            }
    
    def _resolve_app_name(self, exe_path: Optional[str], process_name: str) -> str:
        """Resolve friendly application name from executable path.
        
        Args:
            exe_path: Full path to executable
            process_name: Process name from psutil
            
        Returns:
            Friendly application name
        """
        if not exe_path:
            return process_name
        
        # Try to get product name on Windows
        if WINDOWS_API_AVAILABLE and os.path.exists(exe_path):
            try:
                # Get file version info
                info = win32api.GetFileVersionInfo(exe_path, '\\')
                
                # Get language and codepage
                ms = info['StringFileInfo']
                
                # Try to extract product name or file description
                for key in ms.keys():
                    if 'ProductName' in ms[key]:
                        product_name = ms[key]['ProductName']
                        if product_name:
                            return product_name
                    if 'FileDescription' in ms[key]:
                        file_desc = ms[key]['FileDescription']
                        if file_desc:
                            return file_desc
                            
            except Exception as e:
                logger.debug(f"Could not extract version info from {exe_path}: {e}")
        
        # Fallback: use process name with some cleanup
        return self._clean_process_name(process_name)
    
    def _clean_process_name(self, process_name: str) -> str:
        """Clean up process name to make it more readable.
        
        Args:
            process_name: Raw process name
            
        Returns:
            Cleaned process name
        """
        # Remove .exe extension
        if process_name.lower().endswith('.exe'):
            process_name = process_name[:-4]
        
        # Capitalize first letter
        if process_name:
            process_name = process_name[0].upper() + process_name[1:]
        
        return process_name
    
    def clear_cache(self):
        """Clear the process info cache."""
        self._cache.clear()
    
    def remove_from_cache(self, pid: int):
        """Remove a specific PID from cache.
        
        Args:
            pid: Process ID to remove
        """
        if pid in self._cache:
            del self._cache[pid]


# Global instance
_resolver = None


def get_resolver() -> ProcessInfoResolver:
    """Get global ProcessInfoResolver instance.
    
    Returns:
        ProcessInfoResolver instance
    """
    global _resolver
    if _resolver is None:
        _resolver = ProcessInfoResolver()
    return _resolver


def get_process_info(pid: int) -> Dict:
    """Convenience function to get process info.
    
    Args:
        pid: Process ID
        
    Returns:
        Process info dictionary
    """
    return get_resolver().get_process_info(pid)
