"""Charts module - realtime and historical data visualization."""
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from collections import deque
import time
import logging

logger = logging.getLogger(__name__)

# Configure pyqtgraph
pg.setConfigOptions(antialias=True)


class RealtimeBandwidthChart(QWidget):
    """Realtime line chart showing total bandwidth usage."""
    
    def __init__(self, parent=None, history_seconds: int = 60):
        """Initialize realtime bandwidth chart.
        
        Args:
            parent: Parent widget
            history_seconds: Number of seconds of history to display
        """
        super().__init__(parent)
        self.history_seconds = history_seconds
        self.max_points = history_seconds  # 1 point per second
        
        # Data storage
        self.timestamps = deque(maxlen=self.max_points)
        self.upload_data = deque(maxlen=self.max_points)
        self.download_data = deque(maxlen=self.max_points)
        self.total_data = deque(maxlen=self.max_points)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Realtime Bandwidth (Last 60 seconds)")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Bandwidth', units='KB/s')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        
        # Add legend
        self.plot_widget.addLegend()
        
        # Create plot curves
        self.upload_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='r', width=2),
            name='Upload'
        )
        self.download_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='b', width=2),
            name='Download'
        )
        self.total_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='g', width=2),
            name='Total'
        )
        
        layout.addWidget(self.plot_widget)
        
    def add_data_point(self, bytes_sent: int, bytes_recv: int):
        """Add a new data point to the chart.
        
        Args:
            bytes_sent: Bytes sent in the last second
            bytes_recv: Bytes received in the last second
        """
        current_time = time.time()
        
        # Add timestamp (relative to oldest point)
        if not self.timestamps:
            self.timestamps.append(0)
        else:
            # Calculate relative time
            time_offset = current_time - (self.timestamps[0] + 
                                         (time.time() - len(self.timestamps)))
            self.timestamps.append(len(self.timestamps))
        
        # Convert to KB/s
        upload_kbps = bytes_sent / 1024
        download_kbps = bytes_recv / 1024
        total_kbps = upload_kbps + download_kbps
        
        self.upload_data.append(upload_kbps)
        self.download_data.append(download_kbps)
        self.total_data.append(total_kbps)
        
        # Update curves
        self._update_curves()
        
    def _update_curves(self):
        """Update plot curves with current data."""
        if not self.timestamps:
            return
        
        # Convert deques to lists for plotting
        x = list(range(len(self.timestamps)))
        
        self.upload_curve.setData(x, list(self.upload_data))
        self.download_curve.setData(x, list(self.download_data))
        self.total_curve.setData(x, list(self.total_data))
        
        # Auto-range Y axis
        self.plot_widget.enableAutoRange(axis='y')
        
    def clear(self):
        """Clear all chart data."""
        self.timestamps.clear()
        self.upload_data.clear()
        self.download_data.clear()
        self.total_data.clear()
        self._update_curves()


class TopProcessesChart(QWidget):
    """Chart showing top N processes' bandwidth over time."""
    
    def __init__(self, parent=None, top_n: int = 3, history_seconds: int = 60):
        """Initialize top processes chart.
        
        Args:
            parent: Parent widget
            top_n: Number of top processes to track
            history_seconds: Number of seconds of history
        """
        super().__init__(parent)
        self.top_n = top_n
        self.history_seconds = history_seconds
        self.max_points = history_seconds
        
        # Data storage: app_name -> deque of bandwidth values
        self.process_data = {}
        self.timestamps = deque(maxlen=self.max_points)
        
        # Plot curves: app_name -> curve object
        self.curves = {}
        
        # Color palette
        self.colors = [
            (255, 100, 100),  # Red
            (100, 100, 255),  # Blue
            (100, 255, 100),  # Green
            (255, 255, 100),  # Yellow
            (255, 100, 255),  # Magenta
        ]
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel(f"Top {self.top_n} Processes")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Bandwidth', units='KB/s')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        
        # Add legend
        self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)
        
    def add_snapshot(self, snapshot: dict):
        """Add snapshot and update top processes.
        
        Args:
            snapshot: Network usage snapshot
        """
        current_time = time.time()
        
        # Add timestamp
        if not self.timestamps:
            self.timestamps.append(0)
        else:
            self.timestamps.append(len(self.timestamps))
        
        # Calculate bandwidth per app
        app_bandwidth = {}
        for pid, data in snapshot.items():
            app_name = data.get('app_name', 'Unknown')
            total_bytes = data.get('bytes_sent', 0) + data.get('bytes_recv', 0)
            
            if app_name not in app_bandwidth:
                app_bandwidth[app_name] = 0
            app_bandwidth[app_name] += total_bytes
        
        # Get top N apps
        top_apps = sorted(app_bandwidth.items(), key=lambda x: x[1], reverse=True)[:self.top_n]
        top_app_names = [name for name, _ in top_apps]
        
        # Update data for all tracked apps
        # For apps no longer in top N, add 0
        # For new apps, initialize with zeros for history
        all_apps = set(self.process_data.keys()) | set(top_app_names)
        
        for app_name in all_apps:
            if app_name not in self.process_data:
                # New app - initialize with zeros
                self.process_data[app_name] = deque([0] * len(self.timestamps), 
                                                    maxlen=self.max_points)
            
            # Add current value
            if app_name in app_bandwidth:
                kbps = app_bandwidth[app_name] / 1024
                self.process_data[app_name].append(kbps)
            else:
                self.process_data[app_name].append(0)
            
            # Ensure deque is same length as timestamps
            while len(self.process_data[app_name]) < len(self.timestamps):
                self.process_data[app_name].appendleft(0)
        
        # Update curves
        self._update_curves(top_app_names)
        
    def _update_curves(self, top_apps: list):
        """Update plot curves.
        
        Args:
            top_apps: List of app names to display
        """
        # Remove curves for apps no longer in top N
        for app_name in list(self.curves.keys()):
            if app_name not in top_apps:
                self.plot_widget.removeItem(self.curves[app_name])
                del self.curves[app_name]
        
        # Add/update curves for top apps
        x = list(range(len(self.timestamps)))
        
        for idx, app_name in enumerate(top_apps):
            if app_name not in self.curves:
                # Create new curve
                color_idx = idx % len(self.colors)
                color = self.colors[color_idx]
                pen = pg.mkPen(color=color, width=2)
                self.curves[app_name] = self.plot_widget.plot(
                    pen=pen,
                    name=app_name
                )
            
            # Update curve data
            if app_name in self.process_data:
                y = list(self.process_data[app_name])
                self.curves[app_name].setData(x, y)
        
        # Auto-range Y axis
        self.plot_widget.enableAutoRange(axis='y')
        
    def clear(self):
        """Clear all chart data."""
        self.timestamps.clear()
        self.process_data.clear()
        for curve in self.curves.values():
            self.plot_widget.removeItem(curve)
        self.curves.clear()


class DailyBarChart(QWidget):
    """Bar chart for daily summary data."""
    
    def __init__(self, parent=None):
        """Initialize daily bar chart."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self.title = QLabel("Daily Usage by Application")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        self.title.setFont(title_font)
        layout.addWidget(self.title)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Data Usage', units='MB')
        self.plot_widget.setLabel('bottom', 'Application')
        self.plot_widget.showGrid(y=True, alpha=0.3)
        
        layout.addWidget(self.plot_widget)
        
    def set_data(self, summary_data: list, date: str = None):
        """Set daily summary data for display.
        
        Args:
            summary_data: List of dicts with app_name, bytes_sent, bytes_recv
            date: Date string for title
        """
        self.plot_widget.clear()
        
        if not summary_data:
            return
        
        # Update title if date provided
        if date:
            self.title.setText(f"Daily Usage by Application - {date}")
        
        # Sort by total usage
        summary_data = sorted(summary_data, 
                            key=lambda x: x.get('total_bytes', 0), 
                            reverse=True)
        
        # Limit to top 10 for readability
        summary_data = summary_data[:10]
        
        # Prepare data
        app_names = [item['app_name'] for item in summary_data]
        upload_mb = [item['bytes_sent'] / (1024**2) for item in summary_data]
        download_mb = [item['bytes_recv'] / (1024**2) for item in summary_data]
        
        # Create bar chart
        x = list(range(len(app_names)))
        width = 0.35
        
        # Upload bars
        upload_bars = pg.BarGraphItem(
            x=[i - width/2 for i in x],
            height=upload_mb,
            width=width,
            brush='r',
            name='Upload'
        )
        self.plot_widget.addItem(upload_bars)
        
        # Download bars
        download_bars = pg.BarGraphItem(
            x=[i + width/2 for i in x],
            height=download_mb,
            width=width,
            brush='b',
            name='Download'
        )
        self.plot_widget.addItem(download_bars)
        
        # Set X axis labels
        x_dict = {i: name[:20] for i, name in enumerate(app_names)}  # Truncate long names
        x_axis = self.plot_widget.getAxis('bottom')
        x_axis.setTicks([list(x_dict.items())])
        
        # Add legend
        self.plot_widget.addLegend()
        
    def clear(self):
        """Clear chart data."""
        self.plot_widget.clear()
        self.title.setText("Daily Usage by Application")
