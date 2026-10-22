
"""Telegram Bot API client. Webhook mode only."""
from __future__ import annotations

from io import BytesIO

import httpx

from app.render.telegram import (
    CAPTION_LIMIT,
    chunk_caption,
    render_message,
    strip_all_tags,
)


class TelegramClient:
    def __init__(
        self,
        bot_token: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        bot_token = bot_token.strip()
        self._base = f"https://api.telegram.org/bot{bot_token}"
        self._file_base = f"https://api.telegram.org/file/bot{bot_token}"
        self._http = http_client or httpx.Client(timeout=15.0)

    def _post(self, method: str, **kwargs) -> dict:
        response = self._http.post(f"{self._base}/{method}", **kwargs)
        response.raise_for_status()
        return response.json()

    def download_file(
        self,
        file_id: str,
        max_bytes: int = 5 * 1024 * 1024,
    ) -> bytes:
        """Download a Telegram file with a size limit."""
        if not file_id:
            raise ValueError("Missing Telegram file ID.")

        result = self._post("getFile", json={"file_id": file_id})

        if not result.get("ok"):
            raise ValueError("Telegram could not locate that file.")

        file_path = result.get("result", {}).get("file_path")
        if not file_path:
            raise ValueError("Telegram did not return a file path.")

        # Telegram returns a relative file path.
        url = f"{self._file_base}/{file_path}"

        chunks = []
        total = 0

        with self._http.stream("GET", url) as response:
            response.raise_for_status()

            length = response.headers.get("content-length")
            if length:
                try:
                    if int(length) > max_bytes:
                        raise ValueError("Files must be 5 MB or smaller.")
                except ValueError as exc:
                    if str(exc) == "Files must be 5 MB or smaller.":
                        raise
                    # Ignore a malformed Content-Length header.

            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("Files must be 5 MB or smaller.")
                chunks.append(chunk)

        return b"".join(chunks)

    def send_chat_action(
        self,
        chat_id: int,
        action: str = "typing",
    ) -> None:
        self._post(
            "sendChatAction",
            json={"chat_id": chat_id, "action": action},
        )

    def send_message(
        self,
        chat_id: int,
        html_text: str,
        reply_markup: dict | None = None,
    ) -> dict:
        payload: dict = {
            "chat_id": chat_id,
            "text": html_text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        data = self._post("sendMessage", json=payload)

        if not data.get("ok") and data.get("error_code") == 400:
            fallback_payload: dict = {
                "chat_id": chat_id,
                "text": strip_all_tags(html_text),
            }
            if reply_markup:
                fallback_payload["reply_markup"] = reply_markup
            data = self._post("sendMessage", json=fallback_payload)

        return data

    def send_rendered(
        self,
        chat_id: int,
        chunks: list[str],
        reply_markup: dict | None = None,
    ) -> list[dict]:
        """Send pre-rendered HTML chunks; attach buttons to the final chunk."""
        results = []

        for i, chunk in enumerate(chunks):
            is_last = i == len(chunks) - 1
            results.append(
                self.send_message(
                    chat_id,
                    chunk,
                    reply_markup=reply_markup if is_last else None,
                )
            )

        return results

    def send_markdown(
        self,
        chat_id: int,
        markdown: str,
        reply_markup: dict | None = None,
    ) -> list[dict]:
        return self.send_rendered(
            chat_id,
            render_message(markdown),
            reply_markup=reply_markup,
        )

    def send_photo(
        self,
        chat_id: int,
        photo: BytesIO,
        caption_html: str | None = None,
    ) -> dict:
        data: dict = {"chat_id": str(chat_id)}

        if caption_html:
            capped = (
                chunk_caption(caption_html, limit=CAPTION_LIMIT)[0]
                if len(caption_html) > CAPTION_LIMIT
                else caption_html
            )
            data["caption"] = capped
            data["parse_mode"] = "HTML"

        photo.seek(0)
        files = {"photo": ("chart.png", photo, "image/png")}

        return self._post("sendPhoto", data=data, files=files)

    def set_webhook(
        self,
        url: str,
        secret_token: str,
        allowed_updates: list[str],
        drop_pending_updates: bool = True,
    ) -> dict:
        return self._post(
            "setWebhook",
            json={
                "url": url,
                "secret_token": secret_token,
                "allowed_updates": allowed_updates,
                "drop_pending_updates": drop_pending_updates,
            },
        )

    def delete_webhook(self) -> dict:
        return self._post("deleteWebhook", json={})

    def get_webhook_info(self) -> dict:
        return self._post("getWebhookInfo", json={})

    def get_me(self) -> dict:
        """Check whether the configured Telegram bot token is valid."""
        return self._post("getMe", json={})
