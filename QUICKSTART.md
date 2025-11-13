# Data Monitor - Quick Start Guide

## For End Users

### Download and Run (Once Executable is Built)

1. **Download** `data_monitor.exe`
2. **Double-click** to run
3. **Optional**: Right-click → "Run as administrator" for full features
4. **Done!** The app starts monitoring immediately

### First Time Setup

The app automatically creates:
- `data/` folder - Contains usage database
- `logs/` folder - Contains application logs

No configuration needed - just run and monitor!

---

## For Developers

### 1. Setup Environment (First Time Only)

```powershell
# Clone/download the project
cd "C:\Git\DATA MONITOR"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run from Source

```powershell
# Activate virtual environment (if not already active)
.venv\Scripts\activate

# Run the application
python main.py
```

### 3. Run Tests

```powershell
# Option A: Use the test runner script
.\run_tests.bat

# Option B: Run pytest directly
.venv\Scripts\activate
pytest tests\ -v
```

### 4. Build Executable

```powershell
# Use the build script
.\packaging\build_exe.bat

# Result: dist\data_monitor.exe
```

### 5. Test the Executable

```powershell
# Run the built executable
.\dist\data_monitor.exe
```

---

## Common Tasks

### View Database Contents
```powershell
# Install sqlite3 or use DB Browser for SQLite
sqlite3 data\usage.db

# Example queries
SELECT * FROM sample ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM daily_summary ORDER BY date DESC;
```

### View Logs
```powershell
# Open log file
notepad logs\app.log

# Or tail in PowerShell
Get-Content logs\app.log -Wait
```

### Clean Build
```powershell
# Remove build artifacts
Remove-Item -Recurse -Force dist, build

# Rebuild
.\packaging\build_exe.bat
```

### Reset Database
```powershell
# Stop application first!
# Delete database file
Remove-Item data\usage.db

# Restart application - new database will be created
```

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Import errors | Activate virtual environment: `.venv\Scripts\activate` |
| Missing dependencies | `pip install -r requirements.txt` |
| Tests fail | Check logs, ensure database not in use |
| Build fails | Install PyInstaller: `pip install pyinstaller` |
| Exe won't run | Check `logs\app.log`, try as Administrator |
| Limited data | Run as Administrator for full per-process stats |

---

## File Locations Reference

```
DATA MONITOR/
├── main.py                     # Run this: python main.py
├── requirements.txt            # Dependencies
├── run_tests.bat              # Run this: .\run_tests.bat
├── README.md                  # Full documentation
├── PROJECT_SUMMARY.md         # Project overview
├── DEPLOYMENT_CHECKLIST.md    # Deployment guide
│
├── packaging/
│   └── build_exe.bat          # Run this: .\packaging\build_exe.bat
│
├── dist/
│   └── data_monitor.exe       # Built executable (after build)
│
├── data/
│   └── usage.db               # Database (created at runtime)
│
└── logs/
    └── app.log                # Application logs (created at runtime)
```

---

## What's Next?

1. ✅ **Source code complete** - All modules implemented
2. ✅ **Tests passing** - Run `.\run_tests.bat` to verify
3. ⏭️ **Build executable** - Run `.\packaging\build_exe.bat`
4. ⏭️ **Test on clean system** - Copy .exe to test machine
5. ⏭️ **Distribute** - Share with users!

---

## Support

- 📖 **Full Documentation**: See `README.md`
- 🔍 **Troubleshooting**: See `README.md` → Troubleshooting section
- 📝 **Logs**: Check `logs\app.log` for diagnostic info
- ✅ **Deployment**: See `DEPLOYMENT_CHECKLIST.md`

---

**Ready to build?** Run: `.\packaging\build_exe.bat`
