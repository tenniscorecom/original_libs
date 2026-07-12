"""
credentials/gui.py — 認証情報の管理ツール（GUI 版）

tkinter（Python 標準ライブラリ）による認証情報の登録・削除画面。
機能は対話式ツール（python -m comken.credentials）と同じで、
ターミナル操作に慣れていない人向けに GUI にしたもの。

起動方法:
    python -m comken.credentials --gui

    # bat ファイルにしておくとダブルクリックで起動できる:
    #   @echo off
    #   python -m comken.credentials --gui

対話式ツールと同様、プロジェクトのフォルダ（main.py がある場所）で起動すると
コード内の REQUIRED_CREDENTIALS 宣言を読み取り、未登録の項目を一覧表示する。
"""

import tkinter as tk
from tkinter import messagebox, ttk

from ..exceptions import CredentialNotFoundError
from .__main__ import _read_declared_credentials
from .store import (
    CREDENTIAL_NAME_PATTERN,
    CREDENTIALS_PATH,
    delete_credential,
    list_names,
    save_credential,
)


def validate_and_build_name(prefix: str, item: str) -> tuple[str | None, str | None]:
    """システム名と項目名からキー名を組み立てる。

    Returns:
        (キー名, None): 入力が正しい場合。
        (None, エラーメッセージ): 入力に問題がある場合。
    """
    prefix = prefix.strip()
    item = item.strip()
    if not prefix:
        return None, "システム名を入力してください（例: salesforce）。"
    if not CREDENTIAL_NAME_PATTERN.fullmatch(prefix):
        return None, (
            "システム名に使えるのは半角英数字とアンダースコアだけです（例: salesforce, oju_sys）。"
        )
    if not item:
        return None, "項目名を入力してください（例: username / password / token）。"
    if not CREDENTIAL_NAME_PATTERN.fullmatch(item):
        return None, "項目名に使えるのは半角英数字とアンダースコアだけです（例: username）。"
    return f"{prefix}_{item}", None


def split_name(name: str) -> tuple[str, str]:
    """キー名を（システム名, 項目名）に分解する。

    区切りが複数ある場合は最後のアンダースコアで分ける
    （oju_sys_password → ("oju_sys", "password")）。
    """
    prefix, _, item = name.rpartition("_")
    if not prefix:
        return name, ""
    return prefix, item


class CredentialsApp:
    """認証情報の管理画面。

    左: 登録済みキー名の一覧（ダブルクリックでフォームに読み込み・上書き用）
    右: 登録フォーム（システム名・項目名・値）
    下: このプロジェクトに必要な項目（REQUIRED_CREDENTIALS 宣言の未登録分）
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("comken 認証情報の管理")
        root.geometry("640x480")
        root.minsize(560, 400)

        self._build_widgets()
        self._refresh()

    # ------------------------------------------------------------- 画面の組み立て
    def _build_widgets(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # ── 左: 登録済み一覧 ──
        left = ttk.LabelFrame(main, text="登録済みのキー名", padding=8)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(left, exportselection=False)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<Double-Button-1>", self._on_listbox_double_click)

        ttk.Label(left, text="ダブルクリックでフォームに読み込み（上書き用）").pack(
            anchor=tk.W, pady=(4, 0)
        )
        ttk.Button(left, text="選択したキーを削除", command=self._on_delete).pack(
            anchor=tk.W, pady=(8, 0)
        )

        # ── 右: 登録フォーム ──
        right = ttk.Frame(main, padding=(12, 0, 0, 0))
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        form = ttk.LabelFrame(right, text="登録（新規追加・上書き）", padding=8)
        form.pack(fill=tk.X)

        ttk.Label(form, text="システム名（例: salesforce）").pack(anchor=tk.W)
        self.prefix_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.prefix_var).pack(fill=tk.X, pady=(0, 6))

        ttk.Label(form, text="項目名（例: username / password / token）").pack(anchor=tk.W)
        self.item_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.item_var).pack(fill=tk.X, pady=(0, 6))

        ttk.Label(form, text="値").pack(anchor=tk.W)
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(form, textvariable=self.value_var, show="●")
        self.value_entry.pack(fill=tk.X)

        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            form, text="値を表示する", variable=self.show_var, command=self._on_toggle_show
        ).pack(anchor=tk.W, pady=(2, 6))

        ttk.Button(form, text="登録する", command=self._on_save).pack(anchor=tk.E)

        # ── 右下: プロジェクトの必要項目 ──
        self.required_frame = ttk.LabelFrame(
            right, text="このプロジェクトに必要な項目（未登録のみ）", padding=8
        )
        self.required_listbox = tk.Listbox(self.required_frame, height=5, exportselection=False)
        self.required_listbox.pack(fill=tk.BOTH, expand=True)
        self.required_listbox.bind("<Double-Button-1>", self._on_required_double_click)
        ttk.Label(self.required_frame, text="ダブルクリックでフォームに入力").pack(anchor=tk.W)

        # ── ステータスバー ──
        self.status_var = tk.StringVar(value=f"保存先: {CREDENTIALS_PATH}")
        ttk.Label(self.root, textvariable=self.status_var, padding=(12, 4)).pack(
            side=tk.BOTTOM, anchor=tk.W
        )

    # ------------------------------------------------------------------ 表示更新
    def _refresh(self) -> None:
        """登録済み一覧と必要項目一覧を最新の状態にする。"""
        registered = list_names()
        self.listbox.delete(0, tk.END)
        for name in registered:
            self.listbox.insert(tk.END, name)

        missing = [n for n in _read_declared_credentials() if n not in set(registered)]
        self.required_listbox.delete(0, tk.END)
        for name in missing:
            self.required_listbox.insert(tk.END, name)
        if missing:
            self.required_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        else:
            self.required_frame.pack_forget()

    # -------------------------------------------------------------- イベント処理
    def _on_toggle_show(self) -> None:
        self.value_entry.config(show="" if self.show_var.get() else "●")

    def _on_listbox_double_click(self, _event=None) -> None:
        """登録済みキーをフォームに読み込む（値は復号せず空のまま）。"""
        selection = self.listbox.curselection()
        if not selection:
            return
        prefix, item = split_name(self.listbox.get(selection[0]))
        self.prefix_var.set(prefix)
        self.item_var.set(item)
        self.value_var.set("")
        self.status_var.set("値を入力して「登録する」を押すと上書きされます。")

    def _on_required_double_click(self, _event=None) -> None:
        selection = self.required_listbox.curselection()
        if not selection:
            return
        prefix, item = split_name(self.required_listbox.get(selection[0]))
        self.prefix_var.set(prefix)
        self.item_var.set(item)
        self.value_var.set("")
        self.value_entry.focus_set()

    def _on_save(self) -> None:
        name, error = validate_and_build_name(self.prefix_var.get(), self.item_var.get())
        if error:
            messagebox.showwarning("入力エラー", error, parent=self.root)
            return

        value = self.value_var.get()
        if not value:
            messagebox.showwarning("入力エラー", "値が空です。", parent=self.root)
            return

        is_overwrite = name in list_names()
        if is_overwrite:
            ok = messagebox.askyesno(
                "上書きの確認", f"{name} は登録済みです。上書きしますか？", parent=self.root
            )
            if not ok:
                return

        save_credential(name, value)
        self.value_var.set("")
        self._refresh()
        self.status_var.set(f"保存しました: {name}")

    def _on_delete(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo(
                "削除", "左の一覧から削除するキーを選択してください。", parent=self.root
            )
            return
        name = self.listbox.get(selection[0])

        ok = messagebox.askyesno(
            "削除の確認", f"{name} を削除します。よろしいですか？", parent=self.root
        )
        if not ok:
            return

        try:
            delete_credential(name)
        except CredentialNotFoundError:
            pass  # 一覧の更新漏れで既に消えていた場合。refresh で直る
        self._refresh()
        self.status_var.set(f"削除しました: {name}")


def main() -> None:
    root = tk.Tk()
    CredentialsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
