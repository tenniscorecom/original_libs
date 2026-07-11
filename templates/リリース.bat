@echo off
rem =====================================================
rem comken リリース用バッチ（管理者用）
rem 開発フォルダの内容を配布フォルダへ反映する。
rem 実行すると、各 PC は次回起動時から新しいバージョンで動く。
rem ※開発フォルダは main ブランチをチェックアウトした状態で実行すること
rem   （git はチェックアウト中のブランチの中身がフォルダの実体になるため）
rem =====================================================

rem 管理者が環境に合わせてここだけ書き換える
set COMKEN_DEV=\\server\share\tools\comken-dev
set COMKEN_SHARE=\\server\share\tools\comken

echo 開発フォルダの内容を配布フォルダに反映します。
echo   %COMKEN_DEV%
echo   → %COMKEN_SHARE%
set /p CONFIRM=よろしいですか？（y で実行）:
if /i not "%CONFIRM%"=="y" (
    echo 中止しました。
    pause
    exit /b 0
)

robocopy "%COMKEN_DEV%" "%COMKEN_SHARE%" /MIR /XD .git __pycache__ .venv /NJH /NJS /NP /NFL /NDL >nul

echo.
echo 反映しました。各 PC は次回起動時から新しいバージョンで動きます。
pause
