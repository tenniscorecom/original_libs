"""credentials モジュールのテスト。

DPAPI はログオン中の Windows アカウントで暗号化・復号するため、
テストも実際に暗号化・復号を行う（モックしない）。
"""

import pytest

from comken.credentials import (
    Credentials,
    delete_credential,
    list_names,
    load_credential,
    save_credential,
)
from comken.exceptions import CredentialNotFoundError, InvalidCredentialNameError


@pytest.fixture
def cred_path(tmp_path):
    """テスト用の保存先ファイルパスを返す。"""
    return tmp_path / "credentials.dat"


class TestSaveAndLoad:
    def test_saves_and_loads_credential(self, cred_path):
        """保存した値をそのまま取り出せることを確認する。"""
        save_credential("salesforce_password", "pass123", cred_path)

        assert load_credential("salesforce_password", cred_path) == "pass123"

    def test_overwrites_same_name(self, cred_path):
        """同じキー名で保存すると上書きされることを確認する。"""
        save_credential("salesforce_password", "old_pass", cred_path)
        save_credential("salesforce_password", "new_pass", cred_path)

        assert load_credential("salesforce_password", cred_path) == "new_pass"

    def test_keeps_multiple_names(self, cred_path):
        """複数のキーを別々に保存できることを確認する。"""
        save_credential("salesforce_username", "sf_user", cred_path)
        save_credential("salesforce_password", "sf_pass", cred_path)
        save_credential("oju_sys_password", "oju_pass", cred_path)

        assert load_credential("salesforce_username", cred_path) == "sf_user"
        assert load_credential("salesforce_password", cred_path) == "sf_pass"
        assert load_credential("oju_sys_password", cred_path) == "oju_pass"

    def test_load_missing_name_raises(self, cred_path):
        """未登録のキー名を指定すると CredentialNotFoundError になることを確認する。"""
        save_credential("salesforce_password", "pass", cred_path)

        with pytest.raises(CredentialNotFoundError):
            load_credential("unknown_key", cred_path)

    def test_load_from_missing_file_raises(self, cred_path):
        """ファイル自体が存在しない場合も CredentialNotFoundError になることを確認する。"""
        with pytest.raises(CredentialNotFoundError):
            load_credential("salesforce_password", cred_path)

    @pytest.mark.parametrize("bad_name", ["応需sys_password", "sales force", "sf-test", "sf.test", ""])
    def test_rejects_invalid_name(self, cred_path, bad_name):
        """半角英数字とアンダースコア以外を含むキー名は登録できないことを確認する。"""
        with pytest.raises(InvalidCredentialNameError):
            save_credential(bad_name, "pass", cred_path)

    def test_japanese_value_is_allowed(self, cred_path):
        """キー名は英数字のみだが、値には日本語を保存できることを確認する。"""
        save_credential("app_secret", "秘密の合言葉", cred_path)

        assert load_credential("app_secret", cred_path) == "秘密の合言葉"


class TestCredentials:
    def test_accesses_values_by_attribute(self, cred_path):
        """プレフィックス + 属性名でキーの値を取り出せることを確認する。"""
        save_credential("salesforce_username", "sf_user", cred_path)
        save_credential("salesforce_password", "sf_pass", cred_path)

        sf = Credentials("salesforce", cred_path)
        assert sf.username == "sf_user"
        assert sf.password == "sf_pass"

    def test_prefix_switches_all_values(self, cred_path):
        """プレフィックスを変えるだけで本番用・テスト用が切り替わることを確認する。"""
        save_credential("salesforce_password", "honban_pass", cred_path)
        save_credential("salesforce_test_password", "test_pass", cred_path)

        assert Credentials("salesforce", cred_path).password == "honban_pass"
        assert Credentials("salesforce_test", cred_path).password == "test_pass"

    def test_missing_key_raises_with_full_name(self, cred_path):
        """未登録の属性はフルのキー名入りのエラーになることを確認する。"""
        save_credential("salesforce_username", "user", cred_path)

        with pytest.raises(CredentialNotFoundError, match="salesforce_token"):
            Credentials("salesforce", cred_path).token

    def test_invalid_prefix_raises(self, cred_path):
        """使えない文字を含むプレフィックスは生成時にエラーになることを確認する。"""
        with pytest.raises(InvalidCredentialNameError):
            Credentials("応需sys", cred_path)


class TestDelete:
    def test_deletes_credential(self, cred_path):
        """削除した値は取り出せなくなることを確認する。"""
        save_credential("salesforce_password", "pass", cred_path)
        delete_credential("salesforce_password", cred_path)

        with pytest.raises(CredentialNotFoundError):
            load_credential("salesforce_password", cred_path)

    def test_delete_missing_name_raises(self, cred_path):
        """未登録のキー名を削除しようとするとエラーになることを確認する。"""
        with pytest.raises(CredentialNotFoundError):
            delete_credential("unknown_key", cred_path)


class TestListNames:
    def test_lists_registered_names(self, cred_path):
        """登録済みのキー名がソートされて返ることを確認する。"""
        save_credential("salesforce_password", "p", cred_path)
        save_credential("oju_sys_password", "p", cred_path)

        assert list_names(cred_path) == ["oju_sys_password", "salesforce_password"]

    def test_returns_empty_list_when_no_file(self, cred_path):
        """ファイルが存在しない場合は空リストを返すことを確認する。"""
        assert list_names(cred_path) == []


class TestEncryption:
    def test_file_does_not_contain_plaintext(self, cred_path):
        """保存ファイルに値が平文で含まれていないことを確認する。"""
        save_credential("salesforce_password", "secret_pass_value", cred_path)

        raw = cred_path.read_bytes()
        assert b"secret_pass_value" not in raw
