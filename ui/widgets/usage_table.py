"""Usage table widget - displays realtime per-process network usage."""
from PyQt6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import logging

logger = logging.getLogger(__name__)


class UsageTableWidget(QWidget):
    """Widget displaying realtime network usage in a sortable table."""
    
    process_selected = pyqtSignal(int)  # Emits PID when row selected
    
    def __init__(self, parent=None):
        """Initialize usage table widget."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'Application', 'PID', 'Upload (KB/s)', 'Download (KB/s)', 
            'Total (KB/s)', 'Connections'
        ])
        
        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        
        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Application
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # PID
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Upload
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Download
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Total
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Connections
        
        # Connect selection signal
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table)
        
    def update_data(self, snapshot: dict):
        """Update table with new snapshot data.
        
        Args:
            snapshot: Network usage snapshot from NetworkMonitor
        """
        # Disable sorting while updating
        self.table.setSortingEnabled(False)
        
        # Get current selection
        current_selection = self._get_selected_pid()
        
        # Clear existing rows
        self.table.setRowCount(0)
        
        # Convert snapshot to list and sort by total bandwidth
        processes = []
        for pid, data in snapshot.items():
            total_bytes = data.get('bytes_sent', 0) + data.get('bytes_recv', 0)
            processes.append((pid, data, total_bytes))
        
        processes.sort(key=lambda x: x[2], reverse=True)
        
        # Add rows
        for row_idx, (pid, data, total_bytes) in enumerate(processes):
            self.table.insertRow(row_idx)
            
            app_name = data.get('app_name', 'Unknown')
            bytes_sent = data.get('bytes_sent', 0)
            bytes_recv = data.get('bytes_recv', 0)
            connections = data.get('connections', 0)
            
            # Convert to KB/s
            upload_kbps = bytes_sent / 1024
            download_kbps = bytes_recv / 1024
            total_kbps = total_bytes / 1024
            
            # Create items
            app_item = QTableWidgetItem(app_name)
            pid_item = QTableWidgetItem(str(pid))
            upload_item = QTableWidgetItem(f"{upload_kbps:.2f}")
            download_item = QTableWidgetItem(f"{download_kbps:.2f}")
            total_item = QTableWidgetItem(f"{total_kbps:.2f}")
            conn_item = QTableWidgetItem(str(connections))
            
            # Set items non-editable
            for item in [app_item, pid_item, upload_item, download_item, total_item, conn_item]:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Align numbers to right
            for item in [pid_item, upload_item, download_item, total_item, conn_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Color code high usage (> 1 MB/s = 1024 KB/s)
            if total_kbps > 1024:
                color = QColor(255, 200, 200)  # Light red
                for item in [app_item, pid_item, upload_item, download_item, total_item, conn_item]:
                    item.setBackground(color)
            
            # Store PID in first column for selection tracking
            app_item.setData(Qt.ItemDataRole.UserRole, pid)
            
            # Add items to table
            self.table.setItem(row_idx, 0, app_item)
            self.table.setItem(row_idx, 1, pid_item)
            self.table.setItem(row_idx, 2, upload_item)
            self.table.setItem(row_idx, 3, download_item)
            self.table.setItem(row_idx, 4, total_item)
            self.table.setItem(row_idx, 5, conn_item)
            
            # Restore selection if this was the selected PID
            if current_selection == pid:
                self.table.selectRow(row_idx)
        
        # Re-enable sorting
        self.table.setSortingEnabled(True)
        
    def _get_selected_pid(self) -> int:
        """Get the PID of the currently selected row.
        
        Returns:
            Selected PID or -1 if none selected
        """
        selected_rows = self.table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            item = self.table.item(row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return -1
    
    def _on_selection_changed(self):
        """Handle selection change in table."""
        pid = self._get_selected_pid()
        if pid != -1:
            self.process_selected.emit(pid)
    
    def clear(self):
        """Clear all table data."""
        self.table.setRowCount(0)
