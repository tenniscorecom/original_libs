# バージョンの定義はここ1箇所だけ（pyproject.toml は dynamic version でここを参照する）
__version__ = "0.2.0"

from .config import Config
from .exceptions import (
    ColumnNotFoundError,
    ConfigError,
    CredentialError,
    CredentialNotFoundError,
    CsvError,
    ExcelError,
    InvalidCredentialNameError,
    MacroError,
    OriginalLibsError,
    SalesforceError,
    SheetNotFoundError,
    TeamsError,
)
from .logger import setup_logger
from .runtime import is_debug, is_dry_run, set_debug, set_dry_run

__all__ = [
    "Config",
    "setup_logger",
    "set_debug",
    "is_debug",
    "set_dry_run",
    "is_dry_run",
    "OriginalLibsError",
    "ExcelError",
    "SheetNotFoundError",
    "MacroError",
    "ColumnNotFoundError",
    "CsvError",
    "ConfigError",
    "SalesforceError",
    "TeamsError",
    "CredentialError",
    "CredentialNotFoundError",
    "InvalidCredentialNameError",
]
