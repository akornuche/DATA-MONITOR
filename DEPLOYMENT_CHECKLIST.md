# Data Monitor - Deployment Checklist

## Pre-Build Verification

- [ ] All source files created and saved
- [ ] No syntax errors in Python files
- [ ] requirements.txt includes all dependencies
- [ ] Database schema verified (core/db.py)
- [ ] Logging configured (main.py)
- [ ] Unit tests written and passing

## Build Process

### 1. Environment Setup
```powershell
# Check Python version
python --version  # Should be 3.11+

# Navigate to project directory
cd "C:\Git\DATA MONITOR"

# Verify all files present
dir
```

### 2. Install Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Tests
```powershell
# Run all tests
pytest tests/ -v

# Expected: All tests pass
```

### 4. Test Application (Source)
```powershell
# Run from source
python main.py

# Verify:
# - Application window opens
# - Network monitoring starts
# - Data appears in tables
# - Charts update
# - Database file created at data/usage.db
# - Log file created at logs/app.log
```

### 5. Build Executable
```powershell
# Run build script
.\packaging\build_exe.bat

# Or manually:
pyinstaller packaging\pyinstaller.spec

# Expected output:
# - dist\data_monitor.exe created
# - File size: ~50-100 MB (single-file bundle)
```

## Post-Build Testing

### Test 1: Clean System Test
- [ ] Copy data_monitor.exe to clean folder
- [ ] Run data_monitor.exe
- [ ] Verify application starts
- [ ] Verify monitoring works
- [ ] Verify data/ folder created
- [ ] Verify logs/ folder created
- [ ] Verify database created

### Test 2: Functionality Test
- [ ] Realtime table updates every second
- [ ] Charts update in real-time
- [ ] Recommendations appear
- [ ] Daily summary tab accessible
- [ ] Date picker works
- [ ] Close and reopen - data persists

### Test 3: Permission Test (No Admin)
- [ ] Run without admin rights
- [ ] Check for permission warning
- [ ] Verify app continues to run
- [ ] Verify basic functionality works

### Test 4: Permission Test (Admin)
- [ ] Right-click → Run as administrator
- [ ] Verify enhanced data collection
- [ ] Check logs for permission status

### Test 5: Performance Test
- [ ] Monitor CPU usage (<5% typical)
- [ ] Monitor RAM usage (<100 MB typical)
- [ ] Let run for 5+ minutes
- [ ] Verify no memory leaks
- [ ] Verify database size reasonable

### Test 6: Error Handling
- [ ] Delete data/usage.db while running
- [ ] Force close and restart
- [ ] Verify graceful recovery

## Windows VM Test (Recommended)

### Setup Clean Windows 10/11 VM
```
1. Fresh Windows 10/11 installation
2. No Python installed
3. No development tools
4. Standard user account
```

### Copy and Test
```
1. Copy data_monitor.exe to VM
2. Double-click to run
3. Verify everything works
4. Test as admin and non-admin
```

## Deployment Package

### Files to Include
```
dist/
  └── data_monitor.exe       # Main executable

README.md                     # User documentation
LICENSE                       # License file (if applicable)
```

### Optional Source Package
```
source/
  ├── main.py
  ├── requirements.txt
  ├── README.md
  ├── core/
  ├── ui/
  ├── tests/
  ├── packaging/
  └── assets/
```

## Distribution Checklist

- [ ] Executable tested on clean system
- [ ] README.md complete and accurate
- [ ] Version number correct
- [ ] File size reasonable (<150 MB)
- [ ] No debug output in release build
- [ ] Antivirus false positive check
- [ ] Digital signature (optional, recommended)

## User Instructions Summary

### Quick Start
1. Download data_monitor.exe
2. Run the executable
3. (Optional) Run as Administrator for full features
4. Monitor your network usage!

### What Users Should Know
- First run creates data/ and logs/ folders
- Data retained for 90 days by default
- Logs rotated at 10 MB
- No internet connection required
- No data sent externally
- Portable - no installation needed

## Troubleshooting Guide for Users

### Application won't start
- Check logs/app.log for errors
- Ensure Windows 10/11
- Try running as Administrator

### Limited data shown
- Run as Administrator for full features
- Check permission warning message

### High memory usage
- Normal for real-time monitoring
- Typical: 50-100 MB RAM

### Database too large
- Default 90-day retention
- Can manually delete data/usage.db to reset

## Support Resources

### For Users
- README.md - Complete documentation
- logs/app.log - Diagnostic information
- GitHub Issues - Report problems

### For Developers
- Source code with comments
- Unit tests for examples
- requirements.txt for dependencies

## Version Information

**Version**: 1.0.0
**Build Date**: November 2025
**Python Version**: 3.11+
**Target OS**: Windows 10/11 (64-bit)

## Sign-off

- [ ] All tests passed
- [ ] Documentation complete
- [ ] Executable built successfully
- [ ] Clean system test passed
- [ ] Ready for distribution

---

**Built By**: Data Monitor Team
**Contact**: See README.md for support information
