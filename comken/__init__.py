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


def version() -> str:
    """ライブラリのバージョンを返す（例: "0.2.0"）。"""
    return __version__


__all__ = [
    "Config",
    "setup_logger",
    "version",
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
