import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

from .download import DownloadDir
from .options import BrowserOptions


def _resolve_download_dir(
    download_dir: "str | os.PathLike | DownloadDir | None",
    options_download_dir: "str | None",
) -> DownloadDir:
    """download_dir 引数を DownloadDir に揃える。

    - DownloadDir ならそのまま使う
    - パス（str / Path）なら固定フォルダの DownloadDir に包む
    - 未指定かつ BrowserOptions.DOWNLOAD_DIR が設定済み → 固定フォルダ
    - 未指定かつ BrowserOptions.DOWNLOAD_DIR が None → 一時フォルダを自動作成

    どの指定方法でも d.download_dir.wait() が使える。
    """
    if isinstance(download_dir, DownloadDir):
        return download_dir
    if download_dir:
        return DownloadDir(path=download_dir)
    if options_download_dir:
        return DownloadDir(path=options_download_dir)
    return DownloadDir()  # 一時フォルダ（EdgeDriver の with 終了時に自動削除）


class EdgeDriver:
    """Edge WebDriver のラッパー。with 文で確実に終了できる。

    デフォルトでは内部に一時ダウンロードフォルダを自動作成し、
    with を抜けると自動削除する。ファイルを残したい場合は
    BrowserOptions.DOWNLOAD_DIR またはコンストラクタの download_dir にパスを指定する。

    Args:
        browser_options: BrowserOptions のインスタンス。省略時はデフォルト設定で起動。
                         DRIVER_PATH / WAIT_SECONDS / DOWNLOAD_DIR もここで設定する。
        download_dir: ダウンロード先（BrowserOptions.DOWNLOAD_DIR より優先）。
                      - パス（str / Path）→ 固定フォルダとして使う（削除しない）
                      - DownloadDir → そのまま使う
                      - 省略 → BrowserOptions.DOWNLOAD_DIR を使う（None なら一時フォルダ）

    使い方（デフォルト：一時フォルダ、with 終了で自動削除）:
        from comken.utils import move_file

        with EdgeDriver() as d:
            d.driver.get("https://example.com")
            # ... ダウンロード操作 ...
            files = d.download_dir.wait()        # 完了まで待機
            move_file(files[0], r"C:\\作業\\output")  # with 内で移動する
        # ← ここで一時フォルダは自動削除される

    使い方（ファイルを残す場合）:
        # BrowserOptions で指定
        opts = BrowserOptions()
        opts.DOWNLOAD_DIR = r"C:\\作業\\downloads"
        with EdgeDriver(opts) as d:
            files = d.download_dir.wait()
        # ← C:\\作業\\downloads のファイルはそのまま残る

        # または EdgeDriver に直接指定
        with EdgeDriver(download_dir=r"C:\\作業\\downloads") as d:
            files = d.download_dir.wait()
    """

    def __init__(
        self,
        browser_options: BrowserOptions | None = None,
        download_dir: "str | os.PathLike | DownloadDir | None" = None,
    ) -> None:
        opts = browser_options or BrowserOptions()

        options = Options()
        for arg in opts.build():
            options.add_argument(arg)

        self.download_dir = _resolve_download_dir(download_dir, opts.DOWNLOAD_DIR)
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": str(self.download_dir.path),
                "download.prompt_for_download": False,
            },
        )

        # ドライバー起動に失敗すると with に入る前に例外で抜けるため、
        # ここで片付けないと作成済みの一時フォルダが残り続ける
        try:
            service = Service(executable_path=opts.DRIVER_PATH)
            self._driver = webdriver.Edge(service=service, options=options)
            self._driver.implicitly_wait(opts.WAIT_SECONDS)
        except Exception:
            self.download_dir.__exit__(None, None, None)
            raise

    def __enter__(self) -> "EdgeDriver":
        return self

    def __exit__(self, *args) -> None:
        self.quit()
        self.download_dir.__exit__(*args)  # 一時フォルダなら自動削除

    @property
    def driver(self) -> webdriver.Edge:
        return self._driver

    def quit(self) -> None:
        self._driver.quit()
