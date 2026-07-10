from comken.config import Config


class AppConfig(Config):
    """プロジェクト固有の設定クラス。

    config.ini の値は config.SECTION.KEY で参照する（例: config.REPORT.OUTPUT_FOLDER）。
    リスト変換などプロジェクト固有の加工が必要な場合はプロパティを追加する。
    """


config = AppConfig()
