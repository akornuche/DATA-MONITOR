# Data Monitor

A Windows desktop application for real-time network usage monitoring with per-process tracking, historical analysis, and intelligent recommendations.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## Features

- **Real-time Monitoring**: Track network usage per process with 1-second granularity
- **Per-Process Tracking**: See which applications are using your bandwidth
- **Historical Analysis**: View daily summaries with detailed breakdown by application
- **Smart Recommendations**: Get actionable tips to reduce data consumption
- **Visual Analytics**: Real-time charts and historical bar graphs
- **Data Persistence**: SQLite database with 90-day retention (configurable)
- **Single-File Executable**: Portable .exe with no installation required

## Screenshots

### Realtime Monitor Tab
- Live table showing per-process upload/download speeds
- Real-time bandwidth chart (last 60 seconds)
- Top 3 processes chart
- Smart recommendations panel

### Daily Summary Tab
- Date picker for historical data
- Per-application breakdown
- Bar chart visualization
- Total usage statistics

## System Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **RAM**: 100 MB minimum
- **Disk Space**: 50 MB for application + database storage
- **Permissions**: Can run without admin rights (limited data) or as Administrator (full per-process statistics)

## Installation

### Option 1: Use Pre-built Executable (Recommended)

1. Download `data_monitor.exe` from the releases page
2. Run `data_monitor.exe`
3. (Optional) Run as Administrator for full per-process network statistics

### Option 2: Build from Source

#### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (optional)

#### Build Steps

1. **Clone or download the repository:**
   ```powershell
   git clone <repository-url>
   cd "DATA MONITOR"
   ```

2. **Run the build script:**
   ```powershell
   .\packaging\build_exe.bat
   ```

3. **The executable will be created at:**
   ```
   dist\data_monitor.exe
   ```

#### Manual Build (Alternative)

```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build with PyInstaller
pyinstaller packaging\pyinstaller.spec

# Executable will be in dist\data_monitor.exe
```

## Usage

### Running the Application

**Standard Mode (No Admin Rights):**
```powershell
data_monitor.exe
```

**Administrator Mode (Recommended for full features):**
1. Right-click `data_monitor.exe`
2. Select "Run as administrator"

### Permission Notes

- **Without Admin Rights**: The app will run but may show limited per-process network data. System-wide statistics will still be available.
- **With Admin Rights**: Full per-process network tracking with accurate byte counts per application.

The application will automatically detect permission limitations and display a warning if enhanced privileges are recommended.

### First Run

On first launch:
1. The app creates a `data/` folder for the database
2. The app creates a `logs/` folder for application logs
3. Network monitoring begins immediately
4. Data is persisted to the database every 5 seconds

### Interface Overview

#### Top Stats Bar
- **Total**: Combined upload + download speed
- **Upload**: Current upload speed (red)
- **Download**: Current download speed (blue)

#### Realtime Monitor Tab
- **Usage Table**: Sortable table of all active processes
  - Click column headers to sort
  - Color-coded: Red background for high usage (>1 MB/s)
- **Bandwidth Chart**: 60-second rolling chart
- **Top Processes**: Chart showing top 3 bandwidth consumers
- **Recommendations**: Smart tips updated every 5 seconds

#### Daily Summary Tab
- **Date Picker**: Select any past date with data
- **Summary Table**: Applications sorted by total usage
- **Bar Chart**: Visual comparison of upload vs download
- **Statistics**: Daily totals displayed at top

## Data Management

### Database Location
```
data/usage.db
```

### Data Retention
- **Default**: 90 days
- **Location**: Configured in `core/db.py` (`RETENTION_DAYS`)
- **Automatic Cleanup**: Runs daily at 2 AM

### Changing Retention Period

Edit `core/db.py`:
```python
RETENTION_DAYS = 90  # Change to desired number of days
```

Rebuild the application after changes.

### Manual Database Operations

The database is standard SQLite. You can query it directly:

```powershell
sqlite3 data/usage.db
```

**Example queries:**
```sql
-- View recent samples
SELECT * FROM sample ORDER BY timestamp DESC LIMIT 10;

-- View daily summaries
SELECT * FROM daily_summary ORDER BY date DESC;

-- Total data by app (last 24 hours)
SELECT 
    COALESCE(app_name, process_name) as app,
    SUM(bytes_sent + bytes_recv) / 1024.0 / 1024.0 as mb_total
FROM sample
WHERE timestamp > (strftime('%s', 'now') - 86400)
GROUP BY app
ORDER BY mb_total DESC;
```

## Logging

### Log Location
```
logs/app.log
```

### Log Rotation
- **Max Size**: 10 MB per file
- **Backups**: 5 files retained
- **Format**: `YYYY-MM-DD HH:MM:SS - module - LEVEL - message`

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Non-critical issues
- **ERROR**: Errors that don't stop the app
- **CRITICAL**: Severe errors

## Troubleshooting

### Issue: "Limited network data available" warning

**Cause**: Application lacks permissions for per-process network tracking.

**Solution**: Run as Administrator (right-click → "Run as administrator")

### Issue: No data appearing in tables

**Possible Causes:**
1. No network activity detected
2. Processes have no active connections
3. Permission issues

**Solutions:**
1. Generate network activity (browse web, download file)
2. Check logs at `logs/app.log`
3. Run as Administrator

### Issue: Database errors

**Solution**: Delete `data/usage.db` and restart. A new database will be created.

### Issue: Application won't start

1. Check `logs/app.log` for error messages
2. Ensure no other instance is running
3. Try running from command prompt to see error output:
   ```powershell
   .\data_monitor.exe
   ```

### Issue: High CPU usage

**Cause**: Monitoring overhead on systems with many processes.

**Solution**: This is normal for real-time monitoring. Typical usage is <5% CPU.

## Development

### Project Structure

```
data_monitor/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── core/                        # Core monitoring logic
│   ├── __init__.py
│   ├── monitor.py              # NetworkMonitor class
│   ├── process_info.py         # Process information resolver
│   ├── db.py                   # Database operations
│   ├── summary.py              # Daily aggregation
│   └── recommender.py          # Recommendations engine
├── ui/                         # User interface
│   ├── __init__.py
│   ├── main_window.py          # Main application window
│   ├── charts.py               # pyqtgraph charts
│   └── widgets/                # UI components
│       ├── usage_table.py
│       ├── summary_view.py
│       └── recommendation_widget.py
├── assets/                     # Resources
│   └── styles.qss              # Qt stylesheet
├── tests/                      # Unit tests
│   ├── test_monitor.py
│   ├── test_db.py
│   └── test_recommender.py
├── packaging/                  # Build scripts
│   ├── pyinstaller.spec
│   └── build_exe.bat
├── data/                       # Created at runtime
│   └── usage.db
└── logs/                       # Created at runtime
    └── app.log
```

### Running Tests

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_db.py -v

# Run with coverage
pytest tests/ --cov=core --cov=ui
```

### Dependencies

- **PyQt6**: GUI framework
- **pyqtgraph**: Real-time plotting
- **psutil**: System and process utilities
- **pytest**: Testing framework
- **pyinstaller**: Executable packaging

### Adding Features

1. Core monitoring logic → `core/`
2. UI components → `ui/` or `ui/widgets/`
3. Tests → `tests/`
4. Rebuild executable after changes

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Document functions with docstrings
- Keep functions focused and small

## Technical Notes

### Per-Process Network Tracking on Windows

**Challenge**: Windows doesn't provide direct per-process network byte counters via standard APIs.

**Current Implementation**: 
- Uses `psutil` to enumerate processes and connections
- Estimates bandwidth based on connection states
- For production accuracy, would need:
  - Windows Performance Counters (via `pywin32`)
  - Event Tracing for Windows (ETW)
  - Network Statistics API

**Why This Matters**: The current implementation provides a best-effort estimate. Running as Administrator improves accuracy but still has limitations due to Windows API constraints.

**Future Enhancement**: Integrate Windows Performance Counters for true per-process byte tracking.

### Database Performance

- **Sample Insertion**: Batched every 5 seconds to reduce I/O
- **Indexes**: Timestamp and PID indexed for fast queries
- **Daily Aggregation**: Runs asynchronously to avoid UI blocking

### UI Update Strategy

- **Realtime Data**: Updated every 1 second
- **Recommendations**: Updated every 5 seconds (less frequent to reduce overhead)
- **Charts**: 60-second rolling window for real-time view

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with PyQt6
- Charts powered by pyqtgraph
- System monitoring via psutil

## Support

For issues, questions, or contributions:
1. Check the logs: `logs/app.log`
2. Review this README's troubleshooting section
3. Open an issue on the project repository

## Changelog

### Version 1.0.0 (November 2025)
- Initial release
- Real-time per-process network monitoring
- Historical daily summaries
- Smart recommendations engine
- Single-file executable for Windows
- 90-day data retention
- Comprehensive logging

---

**Note**: This application monitors network usage locally only. No data is transmitted externally. All information stays on your machine in the local database.
