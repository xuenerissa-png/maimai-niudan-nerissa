@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo 请先从 https://www.python.org/downloads/ 安装 Python 3.10 或更新版本，再重新打开此文件。
) else (
  py -3 local_setup.py --configure
)
pause
