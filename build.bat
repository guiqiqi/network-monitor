pip install uv
uv sync
uv run pyinstaller --onefile --hiddenimport win32timezone --name monitor .\main.py
copy install.bat .\dist