@echo off
rem =====================================================
rem comken 初回セットアップ（各 PC で1回だけ実行する）
rem 1. 共有フォルダのパスを環境変数 COMKEN_SHARE に登録
rem    （各ツールの 実行.bat はこの環境変数を参照するので書き換え不要になる）
rem 2. 共有フォルダからローカルに comken をコピー
rem 3. pip install -e でローカルの comken を Python に登録
rem =====================================================

rem 管理者が環境に合わせてここだけ書き換える（パスを書くのはこのファイルだけ）
set COMKEN_SHARE=\\server\share\tools\comken
set COMKEN_LOCAL=%LOCALAPPDATA%\comken

if not exist "%COMKEN_SHARE%" (
    echo 共有フォルダにアクセスできません: %COMKEN_SHARE%
    echo ネットワーク接続を確認してから、もう一度実行してください。
    pause
    exit /b 1
)

echo 共有フォルダのパスを環境変数に登録しています...
setx COMKEN_SHARE "%COMKEN_SHARE%" >nul

echo comken をローカルにコピーしています...
robocopy "%COMKEN_SHARE%" "%COMKEN_LOCAL%" /MIR /XD .git __pycache__ .venv /NJH /NJS /NP /NFL /NDL >nul

echo Python に登録しています...
pip install -e "%COMKEN_LOCAL%" --no-deps

echo.
echo セットアップ完了。以後は各ツールの 実行.bat から起動してください。
pause
