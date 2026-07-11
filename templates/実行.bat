@echo off
rem =====================================================
rem ツール起動用バッチ（この雛形をプロジェクトのルートにコピーして使う）
rem 1. comken を共有フォルダからローカルに差分同期（自動更新）
rem 2. main.py を実行
rem 共有フォルダに繋がらない場合は、前回同期したローカル版で動く。
rem =====================================================

rem 管理者が環境に合わせてここだけ書き換える
set COMKEN_SHARE=\\server\share\tools\comken
set COMKEN_LOCAL=%LOCALAPPDATA%\comken

if exist "%COMKEN_SHARE%" (
    robocopy "%COMKEN_SHARE%" "%COMKEN_LOCAL%" /MIR /XD .git __pycache__ .venv /NJH /NJS /NP /NFL /NDL >nul
)

cd /d "%~dp0"
python main.py

pause
