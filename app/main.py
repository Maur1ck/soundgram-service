from fastapi import FastAPI

from app.schemas import PlaylistRequest
from app.services import YandexMusicService

app = FastAPI(title="Soundgram Playlists Service")


@app.post("/playlist")
async def get_playlist_info(data: PlaylistRequest):
    return await YandexMusicService().get_playlist(data.url)
