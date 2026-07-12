"""
teams モジュールのテスト。

実行方法:
    リポジトリのルートで python -m pytest tests/ -v
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from comken.teams import TeamsNotifier


DUMMY_URL = "https://dummy.webhook.office.com/webhookb2/xxx"


@pytest.fixture
def notifier():
    return TeamsNotifier(DUMMY_URL)


def _mock_urlopen(status=200, body=b"1"):
    """urllib.request.urlopen のモックを返す。"""
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch("urllib.request.urlopen", return_value=mock_resp)


class TestTeamsNotifierSend:
    """send() のテスト。"""

    def test_posts_text_payload(self, notifier):
        """send() が {"text": ...} のペイロードを POST することを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send("処理が完了しました")

        req = mock_open.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload == {"text": "処理が完了しました"}

    def test_posts_to_correct_url(self, notifier):
        """正しい URL に POST することを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send("テスト")

        req = mock_open.call_args[0][0]
        assert req.full_url == DUMMY_URL

    def test_uses_post_method(self, notifier):
        """HTTP メソッドが POST であることを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send("テスト")

        req = mock_open.call_args[0][0]
        assert req.method == "POST"


class TestTeamsNotifierSendCard:
    """send_card() のテスト。"""

    def test_posts_messagecard_payload(self, notifier):
        """send_card() が MessageCard 形式のペイロードを送ることを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send_card("完了", body="3,421 件を処理しました")

        req = mock_open.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["@type"] == "MessageCard"
        assert payload["summary"] == "完了"
        assert payload["sections"][0]["activityTitle"] == "完了"
        assert payload["sections"][0]["activityText"] == "3,421 件を処理しました"

    def test_default_color_is_blue(self, notifier):
        """デフォルトのカラーが青（0076D7）であることを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send_card("タイトル")

        req = mock_open.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["themeColor"] == "0076D7"

    def test_custom_color(self, notifier):
        """color 引数でカラーを変更できることを確認する（エラー通知用の赤など）。"""
        with _mock_urlopen() as mock_open:
            notifier.send_card("エラー", color="FF0000")

        req = mock_open.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["themeColor"] == "FF0000"

    def test_body_can_be_omitted(self, notifier):
        """body を省略しても送れることを確認する。"""
        with _mock_urlopen():
            notifier.send_card("タイトルだけ")
