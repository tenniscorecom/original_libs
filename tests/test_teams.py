"""
teams モジュールのテスト。

実行方法:
    リポジトリのルートで python -m pytest tests/ -v
"""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from comken.exceptions import TeamsError
from comken.teams import CardColor, TeamsNotifier


DUMMY_URL = "https://prod-xx.japaneast.logic.azure.com/workflows/xxx"


@pytest.fixture
def notifier():
    return TeamsNotifier(DUMMY_URL)


def _mock_urlopen(status=200, body=b""):
    """urllib.request.urlopen のモックを返す。"""
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch("urllib.request.urlopen", return_value=mock_resp)


def _sent_payload(mock_open) -> dict:
    """モックに渡されたリクエストから JSON ペイロードを取り出す。"""
    req = mock_open.call_args[0][0]
    return json.loads(req.data.decode("utf-8"))


def _card_body(payload: dict) -> list[dict]:
    """ペイロードから Adaptive Card の body（TextBlock のリスト）を取り出す。"""
    return payload["attachments"][0]["content"]["body"]


class TestTeamsNotifierSend:
    """send() のテスト。"""

    def test_posts_adaptive_card_with_text(self, notifier):
        """send() が Adaptive Card 形式でテキストを送ることを確認する。

        Power Automate の「Webhook 要求を受信したらチャネルに投稿する」テンプレートは
        Adaptive Card 形式（type: message + attachments）を期待するため。
        """
        with _mock_urlopen() as mock_open:
            notifier.send("処理が完了しました")

        payload = _sent_payload(mock_open)
        assert payload["type"] == "message"
        attachment = payload["attachments"][0]
        assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"
        assert attachment["content"]["type"] == "AdaptiveCard"
        assert _card_body(payload)[0]["text"] == "処理が完了しました"

    def test_text_block_wraps(self, notifier):
        """長文が折り返されるよう wrap が有効なことを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send("テスト")

        assert _card_body(_sent_payload(mock_open))[0]["wrap"] is True

    def test_posts_to_correct_url(self, notifier):
        """正しい URL に POST することを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send("テスト")

        req = mock_open.call_args[0][0]
        assert req.full_url == DUMMY_URL
        assert req.method == "POST"


class TestTeamsNotifierSendCard:
    """send_card() のテスト。"""

    def test_title_is_bold_and_medium(self, notifier):
        """タイトルが太字・大きめの TextBlock になることを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send_card("完了", body="3,421 件を処理しました")

        blocks = _card_body(_sent_payload(mock_open))
        assert blocks[0]["text"] == "完了"
        assert blocks[0]["weight"] == "Bolder"
        assert blocks[0]["size"] == "Medium"
        assert blocks[1]["text"] == "3,421 件を処理しました"

    def test_default_color(self, notifier):
        """デフォルトのタイトル色が Default であることを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send_card("タイトル")

        assert _card_body(_sent_payload(mock_open))[0]["color"] == CardColor.DEFAULT

    def test_red_color_for_errors(self, notifier):
        """CardColor.RED で Adaptive Card の Attention 色になることを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send_card("エラー", color=CardColor.RED)

        assert _card_body(_sent_payload(mock_open))[0]["color"] == "Attention"

    def test_body_can_be_omitted(self, notifier):
        """body を省略するとタイトルの TextBlock だけになることを確認する。"""
        with _mock_urlopen() as mock_open:
            notifier.send_card("タイトルだけ")

        assert len(_card_body(_sent_payload(mock_open))) == 1


class TestTeamsNotifierErrors:
    """通知失敗時のエラーハンドリングのテスト。

    生の urllib のエラーではなく、日本語メッセージ付きの TeamsError になることを確認する。
    """

    def test_http_error_raises_teams_error(self, notifier):
        """HTTP エラー（不正な Webhook URL 等）は TeamsError になる。"""
        import io

        http_error = urllib.error.HTTPError(
            DUMMY_URL, 400, "Bad Request", {}, io.BytesIO(b"Invalid payload")
        )
        with patch("urllib.request.urlopen", side_effect=http_error):
            with pytest.raises(TeamsError, match="HTTP 400"):
                notifier.send("テスト")

    def test_connection_error_raises_teams_error(self, notifier):
        """接続エラー（オフライン等）は TeamsError になる。"""
        url_error = urllib.error.URLError("Name or service not known")
        with patch("urllib.request.urlopen", side_effect=url_error):
            with pytest.raises(TeamsError, match="接続できませんでした"):
                notifier.send("テスト")
