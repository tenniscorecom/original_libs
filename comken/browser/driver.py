from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

from .options import BrowserOptions


class EdgeDriver:
    """Edge WebDriver のラッパー。with 文で確実に終了できる。

    Args:
        browser_options: BrowserOptions のインスタンス。省略時はデフォルト設定で起動。
                         DRIVER_PATH / WAIT_SECONDS もここで設定する。
        download_dir: ダウンロード先フォルダのパス。
                      make_download_dir() で作成した一時フォルダを渡すことを推奨。
                      フォルダの削除は呼び出し側で行う（残したい場合はそのままでよい）。

    使い方（ダウンロードあり）:
        import shutil
        from comken.utils import make_download_dir

        dl_dir = make_download_dir()
        with EdgeDriver(download_dir=dl_dir) as d:
            d.driver.get("https://example.com")
            # ... ダウンロード操作 ...

        files = list(dl_dir.glob("*.xlsx"))
        shutil.move(str(files[0]), "output/report.xlsx")
        shutil.rmtree(dl_dir)  # 不要なら削除
    """

    def __init__(
        self,
        browser_options: BrowserOptions | None = None,
        download_dir: Path | str | None = None,
    ) -> None:
        opts = browser_options or BrowserOptions()

        options = Options()
        for arg in opts.build():
            options.add_argument(arg)

        if download_dir:
            options.add_experimental_option(
                "prefs",
                {
                    "download.default_directory": str(Path(download_dir)),
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
