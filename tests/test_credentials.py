"""credentials モジュールのテスト。

DPAPI はログオン中の Windows アカウントで暗号化・復号するため、
テストも実際に暗号化・復号を行う（モックしない）。
"""

import pytest

from comken.credentials import (
    Credential,
    delete_credential,
    list_services,
    load_credential,
    save_credential,
)
from comken.exceptions import CredentialNotFoundError, InvalidServiceNameError


@pytest.fixture
def cred_path(tmp_path):
    """テスト用の保存先ファイルパスを返す。"""
    return tmp_path / "credentials.dat"


class TestSaveAndLoad:
    def test_saves_and_loads_credential(self, cred_path):
        """保存した認証情報をそのまま取り出せることを確認する。"""
        cred = Credential("user@example.com", "pass123", "token456")
        save_credential("salesforce", cred, cred_path)

        cred = load_credential("salesforce", cred_path)
        assert cred.username == "user@example.com"
        assert cred.password == "pass123"
        assert cred.token == "token456"

    def test_token_defaults_to_empty(self, cred_path):
        """トークンを省略した場合は空文字になることを確認する。"""
        save_credential("app", Credential("user", "pass"), cred_path)

        assert load_credential("app", cred_path).token == ""

    def test_overwrites_same_service(self, cred_path):
        """同じサービス名で保存すると上書きされることを確認する。"""
        save_credential("app", Credential("old_user", "old_pass"), cred_path)
        save_credential("app", Credential("new_user", "new_pass"), cred_path)

        cred = load_credential("app", cred_path)
        assert cred.username == "new_user"
        assert cred.password == "new_pass"

    def test_keeps_multiple_services(self, cred_path):
        """複数のサービスを別々に保存できることを確認する。"""
        save_credential("salesforce", Credential("sf_user", "sf_pass"), cred_path)
        save_credential("oju_sys", Credential("oju_user", "oju_pass"), cred_path)

        assert load_credential("salesforce", cred_path).username == "sf_user"
        assert load_credential("oju_sys", cred_path).username == "oju_user"

    @pytest.mark.parametrize("bad_name", ["応需sys", "sales force", "sf-test", "sf.test", ""])
    def test_rejects_invalid_service_name(self, cred_path, bad_name):
        """半角英数字とアンダースコア以外を含むサービス名は登録できないことを確認する。"""
        with pytest.raises(InvalidServiceNameError):
            save_credential(bad_name, Credential("user", "pass"), cred_path)

    def test_accepts_underscore_service_name(self, cred_path):
        """アンダースコア入りのサービス名は登録できることを確認する。"""
        save_credential("salesforce_test", Credential("user", "pass"), cred_path)

        assert load_credential("salesforce_test", cred_path).username == "user"

    def test_load_missing_service_raises(self, cred_path):
        """未登録のサービス名を指定すると CredentialNotFoundError になることを確認する。"""
        save_credential("app", Credential("user", "pass"), cred_path)

        with pytest.raises(CredentialNotFoundError):
            load_credential("unknown", cred_path)

    def test_load_from_missing_file_raises(self, cred_path):
        """ファイル自体が存在しない場合も CredentialNotFoundError になることを確認する。"""
        with pytest.raises(CredentialNotFoundError):
            load_credential("app", cred_path)


class TestDelete:
    def test_deletes_credential(self, cred_path):
        """削除した認証情報は取り出せなくなることを確認する。"""
        save_credential("app", Credential("user", "pass"), cred_path)
        delete_credential("app", cred_path)

        with pytest.raises(CredentialNotFoundError):
            load_credential("app", cred_path)

    def test_delete_missing_service_raises(self, cred_path):
        """未登録のサービス名を削除しようとするとエラーになることを確認する。"""
        with pytest.raises(CredentialNotFoundError):
            delete_credential("unknown", cred_path)


class TestListServices:
    def test_lists_registered_services(self, cred_path):
        """登録済みのサービス名がソートされて返ることを確認する。"""
        save_credential("salesforce", Credential("u", "p"), cred_path)
        save_credential("oju_sys", Credential("u", "p"), cred_path)

        assert list_services(cred_path) == ["oju_sys", "salesforce"]

    def test_returns_empty_list_when_no_file(self, cred_path):
        """ファイルが存在しない場合は空リストを返すことを確認する。"""
        assert list_services(cred_path) == []


class TestEncryption:
    def test_file_does_not_contain_plaintext(self, cred_path):
        """保存ファイルにパスワードが平文で含まれていないことを確認する。"""
        save_credential("app", Credential("secret_user", "secret_pass"), cred_path)

        raw = cred_path.read_bytes()
        assert b"secret_user" not in raw
        assert b"secret_pass" not in raw
