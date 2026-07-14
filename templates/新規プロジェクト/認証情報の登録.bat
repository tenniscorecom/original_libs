@echo off
rem ============================================================
rem  comken 認証情報の登録 GUI ランチャー
rem  このファイルをダブルクリックすると、パスワード・トークン等を
rem  登録・更新する画面（GUI）が開きます。
rem
rem  前提: 共有サーバーの comken を PYTHONPATH で参照済みであること
rem        （各 PC で初回1回。詳細は 仕様書.md「参照・運用」）
rem  このファイルは各プロジェクトのルートにコピーして使ってください。
rem ============================================================
python -m comken.credentials --gui
if errorlevel 1 (
  echo.
  echo [!] GUI の起動に失敗しました。
  echo     - Python が入っているか
  echo     - PYTHONPATH が共有サーバーの comken を指しているか
  echo     を確認してください。
  pause
)
