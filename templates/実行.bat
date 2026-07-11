@echo off
rem =====================================================
rem ツール起動用バッチ（この雛形をプロジェクトのルートにコピーして使う。書き換え不要）
rem 1. comken を共有フォルダからローカルに差分同期（自動更新）
rem 2. main.py を実行
rem 共有フォルダのパスは環境変数 COMKEN_SHARE から読む（初回セットアップ.bat が登録する）。
rem 共有フォルダに繋がらない場合は、前回同期したローカル版で動く。
rem =====================================================

set COMKEN_LOCAL=%LOCALAPPDATA%\comken

if defined COMKEN_SHARE (
    if exist "%COMKEN_SHARE%" (
        robocopy "%COMKEN_SHARE%" "%COMKEN_LOCAL%" /MIR /XD .git __pycache__ .venv /NJH /NJS /NP /NFL /NDL >nul
    )
)

cd /d "%~dp0"
python main.py

pause
