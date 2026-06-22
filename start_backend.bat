@echo off
cd /d %~dp0backend
echo Starting backend on http://127.0.0.1:8080
python run.py
