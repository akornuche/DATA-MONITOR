"""Data Monitor - Network Usage Tracking Application.

Main entry point for the application.
"""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow


def setup_logging():
    """Setup application logging with rotation."""
    # Ensure logs directory exists
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, 'app.log')
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (10 MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup
    logging.info("=" * 60)
    logging.info("Data Monitor Application Started")
    logging.info("=" * 60)


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    
    try:
        # Enable High DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Data Monitor")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Data Monitor")
        
        # Load stylesheet if available
        stylesheet_path = os.path.join(os.path.dirname(__file__), 'assets', 'styles.qss')
        if os.path.exists(stylesheet_path):
            try:
                with open(stylesheet_path, 'r') as f:
                    app.setStyleSheet(f.read())
                logging.info("Loaded custom stylesheet")
            except Exception as e:
                logging.warning(f"Could not load stylesheet: {e}")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logging.info("Main window displayed")
        
        # Run application
        exit_code = app.exec()
        
        logging.info(f"Application exited with code {exit_code}")
        return exit_code
        
    except Exception as e:
        logging.critical(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
