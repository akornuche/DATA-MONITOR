"""Main application window."""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QTabWidget, QSplitter, QMessageBox,
                             QStatusBar)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
import logging

from ui.widgets.usage_table import UsageTableWidget
from ui.widgets.summary_view import SummaryViewWidget
from ui.widgets.recommendation_widget import RecommendationWidget
from ui.charts import RealtimeBandwidthChart, TopProcessesChart, DailyBarChart
from core.monitor import NetworkMonitor
from core.recommender import UsageRecommender
from core.summary import SummaryManager, DataPersister
from core.db import DatabaseManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        # Core components
        self.monitor = NetworkMonitor()
        self.recommender = UsageRecommender()
        self.db_manager = DatabaseManager()
        self.summary_manager = SummaryManager(self.db_manager)
        self.data_persister = DataPersister(self.db_manager)
        
        # UI timers
        self.ui_update_timer = None
        self.recommendation_timer = None
        
        # Setup UI
        self._setup_ui()
        
        # Start monitoring
        self._start_monitoring()
        
    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Data Monitor - Network Usage Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Top stats bar
        stats_widget = self._create_stats_widget()
        main_layout.addWidget(stats_widget)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Realtime monitoring tab
        realtime_tab = self._create_realtime_tab()
        tab_widget.addTab(realtime_tab, "Realtime Monitor")
        
        # Historical summary tab
        summary_tab = self._create_summary_tab()
        tab_widget.addTab(summary_tab, "Daily Summary")
        
        main_layout.addWidget(tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def _create_stats_widget(self) -> QWidget:
        """Create top stats display widget.
        
        Returns:
            Stats widget
        """
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-bottom: 2px solid #ccc;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        
        # Total bandwidth label
        self.total_bandwidth_label = QLabel("Total: 0.00 KB/s")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.total_bandwidth_label.setFont(font)
        layout.addWidget(self.total_bandwidth_label)
        
        layout.addSpacing(20)
        
        # Upload label
        self.upload_label = QLabel("↑ Upload: 0.00 KB/s")
        self.upload_label.setFont(font)
        self.upload_label.setStyleSheet("color: #d32f2f;")
        layout.addWidget(self.upload_label)
        
        layout.addSpacing(20)
        
        # Download label
        self.download_label = QLabel("↓ Download: 0.00 KB/s")
        self.download_label.setFont(font)
        self.download_label.setStyleSheet("color: #1976d2;")
        layout.addWidget(self.download_label)
        
        layout.addStretch()
        
        return widget
        
    def _create_realtime_tab(self) -> QWidget:
        """Create realtime monitoring tab.
        
        Returns:
            Realtime tab widget
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left side - table and recommendations
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Usage table
        self.usage_table = UsageTableWidget()
        left_splitter.addWidget(self.usage_table)
        
        # Recommendations
        self.recommendation_widget = RecommendationWidget()
        left_splitter.addWidget(self.recommendation_widget)
        
        # Set initial sizes (table 70%, recommendations 30%)
        left_splitter.setSizes([700, 300])
        
        # Right side - charts
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Realtime bandwidth chart
        self.realtime_chart = RealtimeBandwidthChart()
        right_splitter.addWidget(self.realtime_chart)
        
        # Top processes chart
        self.top_processes_chart = TopProcessesChart()
        right_splitter.addWidget(self.top_processes_chart)
        
        # Set initial sizes (equal)
        right_splitter.setSizes([500, 500])
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)
        
        # Set initial sizes (left 40%, right 60%)
        main_splitter.setSizes([400, 600])
        
        layout.addWidget(main_splitter)
        
        return widget
        
    def _create_summary_tab(self) -> QWidget:
        """Create historical summary tab.
        
        Returns:
            Summary tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Summary view (top)
        self.summary_view = SummaryViewWidget()
        self.summary_view.date_changed.connect(self._on_summary_date_changed)
        
        # Daily bar chart (bottom)
        self.daily_chart = DailyBarChart()
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.summary_view)
        splitter.addWidget(self.daily_chart)
        
        # Set initial sizes (table 60%, chart 40%)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        return widget
        
    def _start_monitoring(self):
        """Start network monitoring and UI updates."""
        try:
            # Start monitor
            self.monitor.start()
            logger.info("Network monitor started")
            
            # Start summary manager
            self.summary_manager.start()
            logger.info("Summary manager started")
            
            # Start data persister
            self.data_persister.start()
            logger.info("Data persister started")
            
            # Setup UI update timer (1 second)
            self.ui_update_timer = QTimer()
            self.ui_update_timer.timeout.connect(self._update_ui)
            self.ui_update_timer.start(1000)
            
            # Setup recommendation timer (5 seconds)
            self.recommendation_timer = QTimer()
            self.recommendation_timer.timeout.connect(self._update_recommendations)
            self.recommendation_timer.start(5000)
            
            # Check for permissions warning
            if self.monitor.permissions_warning:
                QMessageBox.warning(
                    self,
                    "Limited Permissions",
                    self.monitor.permissions_warning
                )
            
            self.status_bar.showMessage("Monitoring active")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to start monitoring: {e}"
            )
            
    def _update_ui(self):
        """Update UI with latest data."""
        try:
            # Get latest snapshot
            snapshot = self.monitor.get_latest_snapshot()
            
            # Update table
            self.usage_table.update_data(snapshot)
            
            # Get total bandwidth
            total_usage = self.monitor.get_total_bandwidth()
            
            # Update stats labels
            total_kbps = total_usage['total'] / 1024
            upload_kbps = total_usage['bytes_sent'] / 1024
            download_kbps = total_usage['bytes_recv'] / 1024
            
            # Format with appropriate units
            if total_kbps >= 1024:
                self.total_bandwidth_label.setText(f"Total: {total_kbps/1024:.2f} MB/s")
            else:
                self.total_bandwidth_label.setText(f"Total: {total_kbps:.2f} KB/s")
            
            if upload_kbps >= 1024:
                self.upload_label.setText(f"↑ Upload: {upload_kbps/1024:.2f} MB/s")
            else:
                self.upload_label.setText(f"↑ Upload: {upload_kbps:.2f} KB/s")
            
            if download_kbps >= 1024:
                self.download_label.setText(f"↓ Download: {download_kbps/1024:.2f} MB/s")
            else:
                self.download_label.setText(f"↓ Download: {download_kbps:.2f} KB/s")
            
            # Update charts
            self.realtime_chart.add_data_point(
                total_usage['bytes_sent'],
                total_usage['bytes_recv']
            )
            self.top_processes_chart.add_snapshot(snapshot)
            
            # Persist snapshot to database
            self.data_persister.add_snapshot(snapshot)
            
        except Exception as e:
            logger.error(f"Error updating UI: {e}")
            
    def _update_recommendations(self):
        """Update recommendations based on current usage."""
        try:
            snapshot = self.monitor.get_latest_snapshot()
            total_usage = self.monitor.get_total_bandwidth()
            
            recommendations = self.recommender.get_recommendations(snapshot, total_usage)
            self.recommendation_widget.update_recommendations(recommendations)
            
        except Exception as e:
            logger.error(f"Error updating recommendations: {e}")
            
    def _on_summary_date_changed(self, date: str):
        """Handle summary date change.
        
        Args:
            date: Date string in 'YYYY-MM-DD' format
        """
        try:
            # Get daily summary
            summary_data = self.db_manager.get_daily_summary(date)
            
            # Update summary view
            self.summary_view.set_summary_data(summary_data)
            
            # Update daily chart
            self.daily_chart.set_data(summary_data, date)
            
            if not summary_data:
                self.status_bar.showMessage(f"No data available for {date}")
            else:
                self.status_bar.showMessage(f"Showing data for {date}")
                
        except Exception as e:
            logger.error(f"Error loading summary for {date}: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load summary: {e}"
            )
            
    def closeEvent(self, event):
        """Handle window close event.
        
        Args:
            event: Close event
        """
        try:
            # Stop timers
            if self.ui_update_timer:
                self.ui_update_timer.stop()
            if self.recommendation_timer:
                self.recommendation_timer.stop()
            
            # Stop monitoring
            self.monitor.stop()
            self.summary_manager.stop()
            self.data_persister.stop()
            
            logger.info("Application closed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        event.accept()
