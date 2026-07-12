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

rem どのバージョンをいつ配布したか後から追えるように、日時タグを打つ
rem （バージョン管理は robocopy のタイムスタンプ差分で行うため、タグは記録用）
for /f "tokens=1-3 delims=/ " %%a in ("%DATE%") do set TAG_DATE=%%a%%b%%c
set TAG_TIME=%TIME: =0%
set TAG=release-%TAG_DATE%-%TAG_TIME:~0,2%%TAG_TIME:~3,2%
pushd "%COMKEN_DEV%"
git tag %TAG% 2>nul && git push origin %TAG% 2>nul
popd

robocopy "%COMKEN_DEV%" "%COMKEN_SHARE%" /MIR /XD .git __pycache__ .venv /NJH /NJS /NP /NFL /NDL >nul

echo.
echo 反映しました。各 PC は次回起動時から新しいバージョンで動きます。
pause
