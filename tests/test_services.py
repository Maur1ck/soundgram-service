import pytest
import respx
from httpx import Response
from app.services import YandexMusicService
from app.exceptions import (
    InvalidURLFormatException,
    PlaylistNotFoundException,
    CaptchaRequiredException,
)

# Sample Data
MOCK_PLAYLIST_DATA = {
    "result": {
        "title": "Super Playlist",
        "owner": {"name": "DJ Python"},
        "tracks": [
            {
                "id": "111",
                "title": "Cool Track",
                "artists": [{"name": "Best Artist"}],
                "albums": [{"id": "222"}],
                "coverUri": "example.com/cover/%%",
            }
        ],
    }
}


@pytest.mark.asyncio
async def test_get_playlist_old_format_success(http_client):
    url = "https://music.yandex.ru/users/someuser/playlists/100500"

    async with respx.mock:
        respx.route(host="music.yandex.ru").mock(
            return_value=Response(200, json=MOCK_PLAYLIST_DATA)
        )

        service = YandexMusicService(http_client)
        result = await service.get_playlist(url)

        assert result.title == "Super Playlist"


@pytest.mark.asyncio
async def test_get_playlist_new_format_success(http_client):
    url = "https://music.yandex.ru/playlists/abcd-1234"

    async with respx.mock:
        respx.route(host="api.music.yandex.by").mock(
            return_value=Response(200, json=MOCK_PLAYLIST_DATA)
        )

        service = YandexMusicService(http_client)
        result = await service.get_playlist(url)

        assert result.title == "Super Playlist"


@pytest.mark.asyncio
async def test_get_playlist_not_found(http_client):
    url = "https://music.yandex.ru/users/unknown/playlists/999"

    async with respx.mock:
        respx.route(host="music.yandex.ru").mock(return_value=Response(404))

        service = YandexMusicService(http_client)
        with pytest.raises(PlaylistNotFoundException):
            await service.get_playlist(url)


@pytest.mark.asyncio
async def test_invalid_url_format(http_client):
    url = "https://google.com"

    service = YandexMusicService(http_client)
    with pytest.raises(InvalidURLFormatException):
        await service.get_playlist(url)


@pytest.mark.asyncio
async def test_captcha_required(http_client):
    url = "https://music.yandex.ru/users/bot/playlists/1"

    async with respx.mock:
        respx.route(host="music.yandex.ru").mock(
            return_value=Response(200, text="<!DOCTYPE html>...captcha...")
        )

        service = YandexMusicService(http_client)
        with pytest.raises(CaptchaRequiredException):
            await service.get_playlist(url)
