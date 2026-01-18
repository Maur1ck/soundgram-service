import re
import httpx
from typing import Optional, Tuple
from pydantic import HttpUrl

from app.schemas import PlaylistResponse, TrackInfo
from app.exceptions import (
    InvalidURLFormatException,
    CaptchaRequiredException,
    PlaylistNotFoundException,
    ServiceUnavailableException,
    ExternalServiceException,
    SoundgramHTTPException
)


class YandexMusicService:
    """
    Сервис для работы с Яндекс.Музыкой.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://music.yandex.ru/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Retpath-Y": "https://music.yandex.ru/",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Language": "ru"
    }

    OLD_FORMAT_REGEX = r"users/([^/]+)/playlists/(\d+)"
    NEW_FORMAT_REGEX = r"playlists/([0-9a-fA-F\-]+)"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_playlist(self, url: HttpUrl) -> PlaylistResponse:
        """
        Получает информацию о плейлисте по ссылке.

        Args:
            url: Ссылка на плейлист (music.yandex.ru или yandex.by)

        Returns:
            PlaylistResponse: Объект с названием, автором и списком треков.

        Raises:
            SoundgramHTTPException:
                - 400: Неверный формат ссылки.
                - 403: Требуется капча.
                - 404: Плейлист не найден/приватный.
                - 503: Ошибка сети.
        """
        format_type, params = self._parse_url(url)

        if not format_type:
            raise InvalidURLFormatException()

        api_url = self._get_api_url(format_type, params)
        data = await self._fetch_data(api_url)

        if isinstance(data, dict) and "result" in data:
            data = data["result"]

        title, owner_name = self._parse_metadata(data)
        tracks = self._parse_tracks(data)

        return PlaylistResponse(
            title=str(title),
            owner=str(owner_name),
            tracks=tracks
        )

    def _get_api_url(self, format_type: str, params: dict) -> str:
        if format_type == 'old':
            return f"https://music.yandex.ru/handlers/playlist.jsx?owner={params['owner']}&kinds={params['kind']}&light=true&lang=ru&external-domain=music.yandex.ru"
        elif format_type == 'new':
            return f"https://api.music.yandex.by/playlist/{params['playlist_id']}?resumestream=false&richtracks=true"
        return ""

    async def _fetch_data(self, api_url: str) -> dict:
        try:
            response = await self.client.get(api_url, headers=self.HEADERS, follow_redirects=True)
            response.raise_for_status()

            try:
                return response.json()
            except Exception:
                raise CaptchaRequiredException()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PlaylistNotFoundException()
            raise ExternalServiceException(status_code=e.response.status_code)
        except SoundgramHTTPException:
            raise
        except Exception:
            raise ServiceUnavailableException()

    def _parse_metadata(self, data: dict) -> tuple[str, str]:
        title = "Unknown"
        owner_name = "Unknown"

        if "playlist" in data:
            playlist_obj = data["playlist"]
            title = playlist_obj.get("title", "Unknown")
            owner_obj = playlist_obj.get("owner") or data.get("owner", {})
            owner_name = owner_obj.get("name", owner_obj.get("login", "Unknown"))
        else:
            title = data.get("title", "Unknown")
            owner_obj = data.get("owner", {})
            owner_name = owner_obj.get("name", owner_obj.get("login", "Unknown"))

        return title, owner_name

    def _parse_tracks(self, data: dict) -> list[TrackInfo]:
        raw_tracks = []

        if "tracks" in data:
            raw_tracks = data["tracks"]
        elif "playlist" in data and "tracks" in data["playlist"]:
            raw_tracks = data["playlist"]["tracks"]

        return [self._parse_single_track(item) for item in raw_tracks]

    def _parse_single_track(self, item: dict) -> TrackInfo:
        track = item.get("track", item) if isinstance(item, dict) else item

        track_title = str(track.get("title", "Unknown Track"))

        artists = track.get("artists", [])
        author_names = [a["name"] for a in artists if isinstance(a, dict) and "name" in a] if isinstance(artists,
                                                                                                         list) else []
        if not author_names:
            author_names = ["Unknown Artist"]

        cover_uri = track.get("coverUri")
        cover_url = f"https://{cover_uri.replace('%%', '400x400')}" if cover_uri else ""

        track_id = str(track.get("id"))
        albums = track.get("albums", [])
        album_id = str(albums[0].get("id")) if isinstance(albums, list) and albums else None

        iframe_html = self._generate_iframe_code(album_id, track_id) if album_id and track_id else ""

        return TrackInfo(
            title=track_title,
            authors=author_names,
            cover_url=cover_url,
            iframe_html=iframe_html
        )

    @classmethod
    def _parse_url(cls, url: HttpUrl) -> Tuple[Optional[str], Optional[dict]]:
        url_str = str(url)

        match_old = re.search(cls.OLD_FORMAT_REGEX, url_str)
        if match_old:
            return 'old', {
                'owner': match_old.group(1),
                'kind': match_old.group(2)
            }

        match_new = re.search(cls.NEW_FORMAT_REGEX, url_str)
        if match_new:
            return 'new', {
                'playlist_id': match_new.group(1)
            }

        return None, None

    @staticmethod
    def _generate_iframe_code(album_id: str, track_id: str) -> str:
        return (
            f'<iframe frameborder="0" style="border:none;width:100%;height:180px;" '
            f'width="100%" height="180" '
            f'src="https://music.yandex.ru/iframe/album/{album_id}/track/{track_id}">'
            f'</iframe>'
        )
