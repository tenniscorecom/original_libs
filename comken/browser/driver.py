import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

from ..utils.file import DownloadDir
from .options import BrowserOptions


def _resolve_download_dir(
    download_dir: "str | os.PathLike | DownloadDir | None",
    default_path: str | Path,
) -> DownloadDir:
    """download_dir 引数を DownloadDir に揃える。

    - DownloadDir ならそのまま使う（一時フォルダの自動削除などの性質を保つ）
    - パス（str / Path）なら固定フォルダの DownloadDir に包む
    - 未指定なら BrowserOptions.DOWNLOAD_DIR を固定フォルダの DownloadDir に包む

    これにより、どの指定方法でも EdgeDriver.download_dir.wait() が使える。
    """
    if isinstance(download_dir, DownloadDir):
        return download_dir
    if download_dir:
        return DownloadDir(path=download_dir)
    return DownloadDir(path=default_path)


class EdgeDriver:
    """Edge WebDriver のラッパー。with 文で確実に終了できる。

    ダウンロード先は常に DownloadDir として self.download_dir に持つため、
    どの指定方法でも d.download_dir.wait() で完了待ちができる。

    Args:
        browser_options: BrowserOptions のインスタンス。省略時はデフォルト設定で起動。
                         DRIVER_PATH / WAIT_SECONDS もここで設定する。
        download_dir: ダウンロード先。以下のいずれか:
                      - DownloadDir（使い捨ての一時フォルダなら with で自動削除される）
                      - パス（str / Path）→ 固定フォルダとして使う
                      - 省略 → BrowserOptions.DOWNLOAD_DIR（固定フォルダ）を使う

    使い方（デフォルトのダウンロードフォルダを使う場合）:
        from comken.utils import move_file

        with EdgeDriver() as d:
            d.driver.get("https://example.com")
            # ... ダウンロード操作 ...
            files = d.download_dir.wait()  # 完了まで待機
            move_file(files[0], r"C:\作業\output")

    使い方（使い捨ての一時フォルダを使う場合）:
        from comken.utils import DownloadDir, move_file

        with DownloadDir() as dl, EdgeDriver(download_dir=dl) as d:
            d.driver.get("https://example.com")
            # ... ダウンロード操作 ...
            files = dl.wait()  # d.download_dir.wait() と同じもの
            move_file(files[0], r"C:\作業\output")  # with 内で移動する
        # ← with を抜けると一時フォルダは自動削除される
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

        service = Service(executable_path=opts.DRIVER_PATH)
        self._driver = webdriver.Edge(service=service, options=options)
        self._driver.implicitly_wait(opts.WAIT_SECONDS)

    def __enter__(self) -> "EdgeDriver":
        return self

    def __exit__(self, *args) -> None:
        self.quit()

    @property
    def driver(self) -> webdriver.Edge:
        return self._driver

    def quit(self) -> None:
        self._driver.quit()
