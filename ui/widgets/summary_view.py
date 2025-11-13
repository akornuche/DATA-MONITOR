"""Summary view widget - displays daily usage summaries."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QDateEdit,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SummaryViewWidget(QWidget):
    """Widget for viewing daily usage summaries."""
    
    date_changed = pyqtSignal(str)  # Emits date string when selection changes
    
    def __init__(self, parent=None):
        """Initialize summary view widget."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Date selector
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("View Date:"))
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(-1))  # Default to yesterday
        self.date_edit.dateChanged.connect(self._on_date_changed)
        date_layout.addWidget(self.date_edit)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        date_layout.addWidget(self.refresh_btn)
        
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Summary stats
        self.stats_label = QLabel("No data available")
        self.stats_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(self.stats_label)
        
        # Summary table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            'Application', 'Upload (MB)', 'Download (MB)', 'Total (MB)'
        ])
        
        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        
        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
        
    def set_summary_data(self, summary_data: list):
        """Set summary data for display.
        
        Args:
            summary_data: List of dicts with app_name, bytes_sent, bytes_recv
        """
        # Disable sorting while updating
        self.table.setSortingEnabled(False)
        
        # Clear existing rows
        self.table.setRowCount(0)
        
        if not summary_data:
            self.stats_label.setText("No data available for selected date")
            self.table.setSortingEnabled(True)
            return
        
        # Calculate totals
        total_sent = sum(item['bytes_sent'] for item in summary_data)
        total_recv = sum(item['bytes_recv'] for item in summary_data)
        total_all = total_sent + total_recv
        
        # Update stats label
        self.stats_label.setText(
            f"Total: {total_all / (1024**2):.2f} MB  |  "
            f"Upload: {total_sent / (1024**2):.2f} MB  |  "
            f"Download: {total_recv / (1024**2):.2f} MB"
        )
        
        # Add rows
        for row_idx, item in enumerate(summary_data):
            self.table.insertRow(row_idx)
            
            app_name = item.get('app_name', 'Unknown')
            sent_mb = item.get('bytes_sent', 0) / (1024 ** 2)
            recv_mb = item.get('bytes_recv', 0) / (1024 ** 2)
            total_mb = sent_mb + recv_mb
            
            # Create items
            app_item = QTableWidgetItem(app_name)
            sent_item = QTableWidgetItem(f"{sent_mb:.2f}")
            recv_item = QTableWidgetItem(f"{recv_mb:.2f}")
            total_item = QTableWidgetItem(f"{total_mb:.2f}")
            
            # Set items non-editable
            for item in [app_item, sent_item, recv_item, total_item]:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Align numbers to right
            for item in [sent_item, recv_item, total_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Add items to table
            self.table.setItem(row_idx, 0, app_item)
            self.table.setItem(row_idx, 1, sent_item)
            self.table.setItem(row_idx, 2, recv_item)
            self.table.setItem(row_idx, 3, total_item)
        
        # Re-enable sorting
        self.table.setSortingEnabled(True)
        
    def get_selected_date(self) -> str:
        """Get the currently selected date.
        
        Returns:
            Date string in 'YYYY-MM-DD' format
        """
        date = self.date_edit.date()
        return date.toString("yyyy-MM-dd")
    
    def set_available_dates(self, dates: list):
        """Update available dates (for future enhancement).
        
        Args:
            dates: List of date strings
        """
        # Could be used to highlight available dates in calendar
        pass
    
    def _on_date_changed(self, date: QDate):
        """Handle date selection change."""
        date_str = date.toString("yyyy-MM-dd")
        self.date_changed.emit(date_str)
        
    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        date_str = self.get_selected_date()
        self.date_changed.emit(date_str)
    
    def clear(self):
        """Clear all summary data."""
        self.table.setRowCount(0)
        self.stats_label.setText("No data available")
