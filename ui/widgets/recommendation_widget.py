"""Recommendation widget - displays usage recommendations."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea,
                             QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class RecommendationWidget(QWidget):
    """Widget displaying network usage recommendations."""
    
    def __init__(self, parent=None):
        """Initialize recommendation widget."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("💡 Recommendations")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Scroll area for recommendations
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container widget for recommendations
        self.recommendations_container = QWidget()
        self.recommendations_layout = QVBoxLayout(self.recommendations_container)
        self.recommendations_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.recommendations_container)
        layout.addWidget(scroll)
        
        # Initial empty state
        self._show_empty_state()
        
    def update_recommendations(self, recommendations: list):
        """Update displayed recommendations.
        
        Args:
            recommendations: List of recommendation strings
        """
        # Clear existing recommendations
        while self.recommendations_layout.count():
            item = self.recommendations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not recommendations:
            self._show_empty_state()
            return
        
        # Add new recommendations
        for rec in recommendations[:5]:  # Show max 5 recommendations
            rec_widget = self._create_recommendation_widget(rec)
            self.recommendations_layout.addWidget(rec_widget)
        
        # Add stretch at the end
        self.recommendations_layout.addStretch()
        
    def _show_empty_state(self):
        """Show message when no recommendations available."""
        empty_label = QLabel("✓ No recommendations at this time.\nYour network usage looks good!")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("""
            color: #666;
            padding: 20px;
            font-size: 11pt;
        """)
        self.recommendations_layout.addWidget(empty_label)
        self.recommendations_layout.addStretch()
        
    def _create_recommendation_widget(self, recommendation: str) -> QFrame:
        """Create a single recommendation widget.
        
        Args:
            recommendation: Recommendation text
            
        Returns:
            QFrame containing the recommendation
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #fffacd;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                margin: 4px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Recommendation text
        text_label = QLabel(recommendation)
        text_label.setWordWrap(True)
        text_label.setTextFormat(Qt.TextFormat.PlainText)
        text_label.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(text_label)
        
        return frame
    
    def clear(self):
        """Clear all recommendations."""
        while self.recommendations_layout.count():
            item = self.recommendations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._show_empty_state()
